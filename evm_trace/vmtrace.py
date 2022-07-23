from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional, Type

from eth.vm.memory import Memory  # type: ignore
from eth.vm.stack import Stack  # type: ignore
from eth_abi import decode_single, encode_single  # type: ignore
from eth_utils import decode_hex, to_checksum_address
from hexbytes import HexBytes
from msgspec import Struct  # type: ignore
from msgspec.json import Decoder  # type: ignore

# opcodes grouped by the number of items they pop from the stack
# fmt: off
POP_OPCODES = {
    1: ["EXTCODEHASH", "ISZERO", "NOT", "BALANCE", "CALLDATALOAD", "EXTCODESIZE", "BLOCKHASH", "POP", "MLOAD", "SLOAD", "JUMP", "SELFDESTRUCT"],  # noqa: E501
    2: ["SHL", "SHR", "SAR", "REVERT", "ADD", "MUL", "SUB", "DIV", "SDIV", "MOD", "SMOD", "EXP", "SIGNEXTEND", "LT", "GT", "SLT", "SGT", "EQ", "AND", "XOR", "OR", "BYTE", "SHA3", "MSTORE", "MSTORE8", "SSTORE", "JUMPI", "LOG0", "RETURN"],  # noqa: E501
    3: ["RETURNDATACOPY", "ADDMOD", "MULMOD", "CALLDATACOPY", "CODECOPY", "CREATE"],
    4: ["CREATE2", "EXTCODECOPY"],
    6: ["STATICCALL", "DELEGATECALL"],
    7: ["CALL", "CALLCODE"]
}
# fmt: on
POPCODES = {op: n for n, opcodes in POP_OPCODES.items() for op in opcodes}
POPCODES.update({f"LOG{n}": n + 2 for n in range(1, 5)})
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
    ex: VMExecutedOperation
    """Information concerning the execution of the operation."""
    sub: Optional[VMTrace]
    """Subordinate trace of the CALL/CREATE if applicable."""
    op: str
    """Opcode that is being called."""
    idx: str
    """Index in the tree."""


class VMExecutedOperation(Struct):
    used: int
    """The total gas used."""
    push: List[uint256]
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


class RPCResponse(Struct):
    result: RPCTraceResult


class RPCTraceResult(Struct):
    trace: Optional[List]
    vmTrace: VMTrace
    stateDiff: Optional[Dict]


class VMTraceFrame(Struct):
    address: str
    pc: int
    op: str
    depth: int
    stack: List[int]
    memory: List[int]
    storage: Dict[int, int]


def dec_hook(type: Type, obj: Any) -> Any:
    if type is uint256:
        return uint256(obj, 16)
    if type is HexBytes:
        return HexBytes(decode_hex(obj))


def to_address(value):
    return to_checksum_address(decode_single("address", encode_single("uint256", value)))


def to_trace_frames(
    trace: VMTrace,
    depth: int = 0,
    address: str = None,
) -> Iterator[VMTraceFrame]:
    memory = Memory()
    stack = Stack()
    storage = {}

    for op in trace.ops:
        if op.op in ["CALL", "DELEGATECALL", "STATICCALL"]:
            call_address = to_address(stack.values[-2][1])

        if num_pop := POPCODES.get(op.op):
            stack.pop_ints(num_pop)

        for item in op.ex.push:
            stack.push_int(item)

        if op.ex.mem:
            memory.extend(op.ex.mem.off, len(op.ex.mem.data))
            memory.write(op.ex.mem.off, len(op.ex.mem.data), op.ex.mem.data)

        if op.ex.store:
            storage[op.ex.store.key] = op.ex.store.val

        yield VMTraceFrame(
            address=address,
            pc=op.pc,
            op=op.op,
            depth=depth,
            stack=[val for typ, val in stack.values],
            memory=HexBytes(memory._bytes),
            storage=storage.copy(),
        )

        if op.sub:
            yield from to_trace_frames(op.sub, depth=depth + 1, address=call_address)


def from_rpc_response(buffer: bytes) -> VMTrace:
    return Decoder(RPCResponse, dec_hook=dec_hook).decode(buffer).result.vmTrace
