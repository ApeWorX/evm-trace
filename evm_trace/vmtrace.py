from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional, Type, Union

from eth.vm.memory import Memory
from eth.vm.stack import Stack
from eth_utils import to_checksum_address
from ethpm_types import HexBytes
from msgspec import Struct
from msgspec.json import Decoder

# opcodes grouped by the number of items they pop from the stack
# fmt: off
POP_OPCODES = {
    1: ["EXTCODEHASH", "ISZERO", "NOT", "BALANCE", "CALLDATALOAD", "EXTCODESIZE", "BLOCKHASH", "POP", "MLOAD", "SLOAD", "JUMP", "SELFDESTRUCT"],  # noqa: E501
    2: ["SHL", "SHR", "SAR", "REVERT", "ADD", "MUL", "SUB", "DIV", "SDIV", "MOD", "SMOD", "EXP", "SIGNEXTEND", "LT", "GT", "SLT", "SGT", "EQ", "AND", "XOR", "OR", "BYTE", "SHA3", "MSTORE", "MSTORE8", "SSTORE", "JUMPI", "RETURN"],  # noqa: E501
    3: ["RETURNDATACOPY", "ADDMOD", "MULMOD", "CALLDATACOPY", "CODECOPY", "CREATE"],
    4: ["CREATE2", "EXTCODECOPY"],
    6: ["STATICCALL", "DELEGATECALL"],
    7: ["CALL", "CALLCODE"]
}
# fmt: on
POPCODES = {op: n for n, opcodes in POP_OPCODES.items() for op in opcodes}
POPCODES.update({f"LOG{n}": n + 2 for n in range(0, 5)})
POPCODES.update({f"SWAP{i}": i + 1 for i in range(1, 17)})
POPCODES.update({f"DUP{i}": i for i in range(1, 17)})


class uint256(int):
    pass


class VMTrace(Struct):
    code: HexBytes
    """The code to be executed."""
    ops: List[VMOperation]
    """The operations executed."""


class VMOperation(Struct):
    pc: int
    """The program counter."""
    cost: int
    """The gas cost for this instruction."""
    ex: Optional[VMExecutedOperation]
    """Information concerning the execution of the operation."""
    sub: Optional[VMTrace]
    """Subordinate trace of the CALL/CREATE if applicable."""
    op: str
    """Opcode that is being called."""
    idx: str
    """Index in the tree."""


class VMExecutedOperation(Struct):
    used: int
    """The amount of remaining gas."""
    push: List[HexBytes]
    """The stack item placed, if any."""
    mem: Optional[MemoryDiff]
    """If altered, the memory delta."""
    store: Optional[StorageDiff]
    """The altered storage value, if any."""


class MemoryDiff(Struct):
    off: int
    """Offset into memory the change begins."""
    data: HexBytes
    """The changed data."""


class StorageDiff(Struct):
    key: uint256
    """Which key in storage is changed."""
    val: uint256
    """What the value has been changed to."""


class VMTraceFrame(Struct):
    """
    A synthetic trace frame representing the state at a step of execution.
    """

    address: str
    pc: int
    op: str
    depth: int
    stack: List[int]
    memory: Union[bytes, memoryview]
    storage: Dict[int, int]


def to_address(value):
    # clear the padding and expand to 32 bytes
    return to_checksum_address(value[-20:].rjust(20, b"\x00"))


def to_trace_frames(
    trace: VMTrace,
    depth: int = 1,
    address: str = "",
    copy_memory: bool = True,
) -> Iterator[VMTraceFrame]:
    """
    Replays a VMTrace and yields trace frames at each step of the execution.
    Can be used as a much faster drop-in replacement for Geth-style traces.

    Args:
        trace (VMTrace): A decoded trace from a `trace_` rpc.
        depth (int): A depth of the call being processed. automatically populated.
        address (str): The address of the contract being executed. auto populated
            except the root call.
        copy_memory (bool): Whether to copy memory when returning trace frames.
            Disable for a speedup when dealing with traces using a large amount of memory.
            when disabled, `VMTraceFrame.memory` becomes `memoryview` instead of `bytes`, which
            works like a pointer at the memory `bytearray`. this means you must process the
            frames immediately, otherwise you risk memory value mutating further into execution.

    Returns:
        Iterator[VMTraceFrame]: An iterator of synthetic traces which can be used as a drop-in
        replacement for Geth-style traces. also contains the address of the current contract
        context.
    """
    memory = Memory()
    stack = Stack()
    storage: Dict[int, int] = {}
    call_address = ""
    read_memory = memory.read_bytes if copy_memory else memory.read

    for op in trace.ops:
        if op.ex and op.ex.mem:
            memory.extend(op.ex.mem.off, len(op.ex.mem.data))

        # geth convention is to return after memory expansion, but before the operation is applied
        yield VMTraceFrame(
            address=address,
            pc=op.pc,
            op=op.op,
            depth=depth,
            stack=[val for _, val in stack.values],
            memory=read_memory(0, len(memory)),
            storage=storage.copy(),
        )

        if op.op in ["CALL", "DELEGATECALL", "STATICCALL"]:
            call_address = to_address(stack.values[-2][1])

        if op.ex:
            if op.ex.mem:
                memory.write(op.ex.mem.off, len(op.ex.mem.data), op.ex.mem.data)

            num_pop = POPCODES.get(op.op)
            if num_pop:
                stack.pop_any(num_pop)

            for item in op.ex.push:
                stack.push_bytes(item)

            if op.ex.store:
                storage[op.ex.store.key] = op.ex.store.val

        if op.sub:
            yield from to_trace_frames(
                op.sub, depth=depth + 1, address=call_address, copy_memory=copy_memory
            )


class RPCResponse(Struct):
    result: Union[RPCTraceResult, List[RPCTraceResult]]


class RPCTraceResult(Struct):
    trace: Optional[List]
    vmTrace: VMTrace
    stateDiff: Optional[Dict]


def dec_hook(type: Type, obj: Any) -> Any:
    if type is uint256:
        return uint256(obj, 16)
    elif type is HexBytes:
        return HexBytes(obj)


def from_rpc_response(buffer: bytes) -> Union[VMTrace, List[VMTrace]]:
    """
    Decode structured data from a raw `trace_replayTransaction` or `trace_replayBlockTransactions`.
    """
    resp = Decoder(RPCResponse, dec_hook=dec_hook).decode(buffer)

    if isinstance(resp.result, list):
        return [i.vmTrace for i in resp.result]

    return resp.result.vmTrace
