import math
from enum import Enum
from typing import Any, Dict, Iterator, List

from eth_utils import to_int
from hexbytes import HexBytes
from pydantic import BaseModel, Field, ValidationError, validator


def _convert_hexbytes(cls, v: Any) -> HexBytes:
    try:
        return HexBytes(v)
    except ValueError:
        raise ValidationError(f"Value '{v}' could not be converted to Hexbytes.", cls)


class TraceFrame(BaseModel):
    pc: int
    op: str
    gas: int
    gas_cost: int = Field(alias="gasCost")
    depth: int
    stack: List[Any]
    memory: List[Any]
    storage: Dict[Any, Any] = {}

    @validator("stack", "memory", pre=True, each_item=True)
    def convert_hexbytes(cls, v) -> HexBytes:
        return _convert_hexbytes(cls, v)

    @validator("storage", pre=True)
    def convert_hexbytes_dict(cls, v) -> Dict[HexBytes, HexBytes]:
        return {_convert_hexbytes(cls, k): _convert_hexbytes(cls, val) for k, val in v.items()}


class CallType(Enum):
    INTERNAL = "INTERNAL"  # Non-opcode internal call
    STATIC = "STATIC"  # STATICCALL opcode
    MUTABLE = "MUTABLE"  # CALL opcode
    DELEGATE = "DELEGATE"  # DELEGATECALL opcode
    SELFDESTRUCT = "SELFDESTRUCT"  # SELFDESTRUCT opcode


class CallTreeNode(BaseModel):
    call_type: CallType
    address: Any
    value: int = 0
    depth: int = 0
    gas_limit: int
    gas_cost: int  # calculated from call starting and return
    calldata: Any = HexBytes(b"")
    returndata: Any = HexBytes(b"")
    calls: List["CallTreeNode"] = []
    selfdestruct: bool = False
    failed: bool = False

    @validator("address", "calldata", "returndata", pre=True)
    def validate_hexbytes(cls, v) -> HexBytes:
        return _convert_hexbytes(cls, v)


def get_calltree_from_trace(
    trace: Iterator[TraceFrame], show_internal=False, **root_node_kwargs
) -> CallTreeNode:
    """
    Creates a CallTreeNode from a given transaction trace.

    Args:
        trace (Iterator[TraceFrame]): Iterator of transaction trace frames.
        show_internal (bool): Boolean whether to display internal calls. Defaulted to False.
        root_node_kwargs (dict): Keyword argments passed to the root ``CallTreeNode``.

    Returns:
        :class:`~evm_trace.base.CallTreeNode: Call tree of transaction trace.
    """

    return _create_node_from_call(
        trace=trace,
        show_internal=show_internal,
        **root_node_kwargs,
    )


def _extract_memory(offset: HexBytes, size: HexBytes, memory: List[HexBytes]) -> HexBytes:
    """
    Extracts memory from the EVM stack.

    Args:
        offset (HexBytes): Offset byte location in memory.
        size (HexBytes): Number of bytes to return.
        memory (List[HexBytes]): Memory stack.

    Returns:
        HexBytes: Byte value from memory stack.
    """

    size_int = to_int(size)

    if size_int == 0:
        return HexBytes(b"")

    offset_int = to_int(offset)

    # Compute the word that contains the first byte
    start_word = math.floor(offset_int / 32)
    # Compute the word that contains the last byte
    stop_word = math.ceil((offset_int + size_int) / 32)

    byte_slice = b""

    for word in memory[start_word:stop_word]:
        byte_slice += word

    offset_index = offset_int % 32
    return HexBytes(byte_slice[offset_index:size_int])


def _create_node_from_call(
    trace: Iterator[TraceFrame], show_internal: bool = False, **node_kwargs
) -> CallTreeNode:
    """
    Use specified opcodes to create a branching callnode
    https://www.evm.codes/
    """

    if show_internal:
        raise NotImplementedError()

    node = CallTreeNode(**node_kwargs)

    for frame in trace:
        if frame.op in ("CALL", "DELEGATECALL", "STATICCALL"):
            child_node_kwargs = {}

            child_node_kwargs["address"] = frame.stack[-2][-20:]  # address is 20 bytes in EVM
            child_node_kwargs["depth"] = frame.depth
            # TODO: Validate gas values
            child_node_kwargs["gas_limit"] = int(frame.stack[-1].hex(), 16)
            child_node_kwargs["gas_cost"] = frame.gas_cost

            if frame.op == "CALL":
                child_node_kwargs["call_type"] = CallType.MUTABLE
                child_node_kwargs["value"] = int(frame.stack[-3].hex(), 16)
                child_node_kwargs["calldata"] = _extract_memory(
                    offset=frame.stack[-4], size=frame.stack[-5], memory=frame.memory
                )
            elif frame.op == "DELEGATECALL":
                child_node_kwargs["call_type"] = CallType.DELEGATE
                child_node_kwargs["calldata"] = _extract_memory(
                    offset=frame.stack[-3], size=frame.stack[-4], memory=frame.memory
                )
            else:
                child_node_kwargs["call_type"] = CallType.STATIC
                child_node_kwargs["calldata"] = _extract_memory(
                    offset=frame.stack[-3], size=frame.stack[-4], memory=frame.memory
                )

            child_node = _create_node_from_call(trace=trace, **child_node_kwargs)
            node.calls.append(child_node)

        # TODO: Handle internal nodes using JUMP and JUMPI

        elif frame.op in ("SELFDESTRUCT", "STOP"):
            # TODO: Handle the internal value transfer in SELFDESTRUCT
            # TODO: Handle "execution halted" vs. gas limit reached
            node.selfdestruct = frame.op == "SELFDESTRUCT"
            break

        elif frame.op in ("RETURN", "REVERT"):
            node.returndata = _extract_memory(
                offset=frame.stack[-1], size=frame.stack[-2], memory=frame.memory
            )
            # TODO: Handle "execution halted" vs. gas limit reached
            node.failed = frame.op == "REVERT"
            break

        # TODO: Handle invalid opcodes (`node.failed = True`)
        # NOTE: ignore other opcodes

    # TODO: Handle "execution halted" vs. gas limit reached
    return node
