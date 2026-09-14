from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from eth.vm import opcode_values
from eth.vm.memory import Memory
from eth.vm.stack import Stack
from eth_pydantic_types import Address, HexBytes
from eth_utils import to_int
from msgspec import Struct
from msgspec.json import Decoder

# opcodes grouped by the number of items they pop from the stack
# fmt: off
POP_OPCODES = {
    1: ["EXTCODEHASH", "ISZERO", "NOT", "BALANCE", "CALLDATALOAD", "EXTCODESIZE", "BLOCKHASH", "POP", "MLOAD", "SLOAD", "JUMP", "SELFDESTRUCT"],  # noqa: E501
    2: ["SHL", "SHR", "SAR", "REVERT", "ADD", "MUL", "SUB", "DIV", "SDIV", "MOD", "SMOD", "EXP", "SIGNEXTEND", "LT", "GT", "SLT", "SGT", "EQ", "AND", "XOR", "OR", "BYTE", "SHA3", "KECCAK256", "MSTORE", "MSTORE8", "SSTORE", "JUMPI", "RETURN"],  # noqa: E501
    3: ["RETURNDATACOPY", "ADDMOD", "MULMOD", "CALLDATACOPY", "CODECOPY", "CREATE"],
    4: ["CREATE2", "EXTCODECOPY"],
    6: ["STATICCALL", "DELEGATECALL"],
    7: ["CALL", "CALLCODE"]
}
# fmt: on
POPCODES = {op: n for n, opcodes in POP_OPCODES.items() for op in opcodes}
POPCODES.update({f"LOG{n}": n + 2 for n in range(0, 5)})
POPCODES.update(TLOAD=1, TSTORE=2, MCOPY=3, BLOBHASH=1)
OPCODE_NAMES = {value: name for name, value in vars(opcode_values).items() if name.isupper()}
# Match Geth's opcode spelling. vmTrace has no fork context to distinguish 0x44's meaning.
# Explicit client names (including SHA3 and PREVRANDAO) are preserved.
OPCODE_NAMES.update({0x20: "KECCAK256", 0x44: "DIFFICULTY", 0xFE: "INVALID"})


class IncompleteTraceError(ValueError):
    """The trace omits information required to reconstruct execution state."""


class uint256(int):
    pass


class VMTrace(Struct):
    code: HexBytes
    """The code to be executed."""
    ops: list[VMOperation]
    """The operations executed."""


class VMOperation(Struct):
    pc: int
    """The program counter."""
    cost: int
    """The gas cost for this instruction."""
    ex: VMExecutedOperation | None
    """Information concerning the execution of the operation."""
    sub: VMTrace | None
    """Subordinate trace of the CALL/CREATE if applicable."""
    op: str | None = None
    """Opcode name, recovered from code when absent."""
    idx: str | None = None
    """Optional Erigon index in the tree."""


class VMExecutedOperation(Struct):
    used: int
    """The amount of remaining gas."""
    push: list[HexBytes] | None
    """The stack item placed, if any."""
    mem: MemoryDiff | None
    """If altered, the memory delta."""
    store: StorageDiff | None
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
    stack: list[int]
    memory: bytes | memoryview
    storage: dict[int, int]


def to_trace_frames(
    trace: VMTrace | None,
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
    if trace is None:
        return

    memory = Memory()
    stack = Stack()
    storage: dict[int, int] = {}
    read_memory = memory.read_bytes if copy_memory else memory.read

    for op in trace.ops:
        opcode = op.op
        if opcode is None:
            if not trace.code:
                raise IncompleteTraceError(f"Incomplete vmTrace: missing bytecode at pc {op.pc}")
            if op.pc < 0:
                raise ValueError(f"Invalid vmTrace: negative program counter {op.pc}")
            # EVM execution falls through to STOP beyond the end of known bytecode,
            # including when a final PUSH advances past truncated immediate bytes.
            byte = trace.code[op.pc] if op.pc < len(trace.code) else 0
            opcode = OPCODE_NAMES.get(byte, "INVALID")

        # Modern structLogs expose memory before this instruction expands or writes it.
        yield VMTraceFrame(
            address=address,
            pc=op.pc,
            op=opcode,
            depth=depth,
            stack=[to_int(val) for val in stack.values],
            memory=read_memory(0, len(memory)),
            storage=storage.copy(),
        )

        call_address = ""
        if op.sub and opcode in ("CALL", "STATICCALL"):
            call_address_from_stack = stack.values[-2]
            # Evm natively discards dirty upper bits during CALL
            # NOTE: `isinstance` check to satisfy mypy
            if isinstance(call_address_from_stack, bytes) and len(call_address_from_stack) > 20:
                call_address_from_stack = call_address_from_stack[-20:]
            call_address = Address.__eth_pydantic_validate__(call_address_from_stack)
        elif op.sub and opcode in ("DELEGATECALL", "CALLCODE"):
            call_address = address
        elif op.sub and opcode in ("CREATE", "CREATE2") and op.ex and op.ex.push:
            # A failed creation only reports zero: its attempted address is not recoverable.
            created = to_int(op.ex.push[-1])
            if created:
                call_address = Address.__eth_pydantic_validate__(created)

        if op.sub:
            yield from to_trace_frames(
                op.sub, depth=depth + 1, address=call_address, copy_memory=copy_memory
            )

        if op.ex:
            if (
                opcode in ("CALL", "CALLCODE", "STATICCALL", "DELEGATECALL", "CREATE", "CREATE2")
                and not op.ex.push
            ):
                raise IncompleteTraceError(
                    f"Incomplete vmTrace: missing {opcode} result push at pc {op.pc}"
                )
            _expand_memory(memory, opcode, stack)
            if opcode == "MCOPY":
                destination, source, size = (to_int(value) for value in stack.values[-3:][::-1])
                # This can be reconstructed even when a client omits MCOPY's memory delta.
                memory.copy(destination, source, size)

            if op.ex.mem:
                memory.extend(op.ex.mem.off, len(op.ex.mem.data))
                memory.write(op.ex.mem.off, len(op.ex.mem.data), op.ex.mem.data)

            if opcode.startswith("DUP"):
                # Clients disagree about whether push includes the duplicate itself.
                stack.dup(int(opcode[3:]))
            elif opcode.startswith("SWAP"):
                stack.swap(int(opcode[4:]))
            else:
                num_pop = POPCODES.get(opcode)
                if num_pop:
                    stack.pop_any(num_pop)

                for item in op.ex.push or []:
                    stack.push_bytes(item)

            # erigon bug: https://github.com/ledgerwatch/erigon/pull/7970
            if opcode == "PUSH0" and not op.ex.push:
                stack.push_int(0)

            if op.ex.store:
                storage[op.ex.store.key] = op.ex.store.val


def _expand_memory(memory: Memory, opcode: str, stack: Stack) -> None:
    """Expand memory for opcode operands."""

    def peek_stack(index: int) -> int:
        return to_int(stack.values[-index])

    if opcode in ("MLOAD", "MSTORE", "MSTORE8"):
        memory.extend(peek_stack(1), 1 if opcode == "MSTORE8" else 32)
    elif opcode in ("SHA3", "KECCAK256", "RETURN", "REVERT") or opcode.startswith("LOG"):
        memory.extend(peek_stack(1), peek_stack(2))
    elif opcode in ("CALLDATACOPY", "CODECOPY", "RETURNDATACOPY"):
        memory.extend(peek_stack(1), peek_stack(3))
    elif opcode == "EXTCODECOPY":
        memory.extend(peek_stack(2), peek_stack(4))
    elif opcode == "MCOPY":
        memory.extend(max(peek_stack(1), peek_stack(2)), peek_stack(3))
    elif opcode in ("CREATE", "CREATE2"):
        memory.extend(peek_stack(2), peek_stack(3))
    elif opcode in ("CALL", "CALLCODE"):
        memory.extend(peek_stack(4), peek_stack(5))
        memory.extend(peek_stack(6), peek_stack(7))
    elif opcode in ("DELEGATECALL", "STATICCALL"):
        memory.extend(peek_stack(3), peek_stack(4))
        memory.extend(peek_stack(5), peek_stack(6))


class RPCResponse(Struct):
    result: RPCTraceResult | list[RPCTraceResult]


class RPCTraceResult(Struct):
    trace: list | None
    vmTrace: VMTrace | None
    stateDiff: dict | None


def dec_hook(type: type, obj: Any) -> Any:
    if type is uint256:
        return uint256(obj, 16)
    elif type is HexBytes:
        return HexBytes(obj)


def from_rpc_response(buffer: bytes) -> VMTrace | None | list[VMTrace | None]:
    """
    Decode structured data from a raw `trace_replayTransaction` or `trace_replayBlockTransactions`.
    """
    response = Decoder(RPCResponse, dec_hook=dec_hook).decode(buffer)
    result: list[RPCTraceResult] | RPCTraceResult = response.result
    return [i.vmTrace for i in result] if isinstance(result, list) else result.vmTrace
