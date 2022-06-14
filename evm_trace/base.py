import math
from typing import Any, Dict, Iterator, List, Optional, Type

from eth_utils import to_int
from hexbytes import HexBytes
from pydantic import BaseModel, Field, ValidationError, validator

from evm_trace.display import DisplayableCallTreeNode
from evm_trace.enums import CallType


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


class CallTreeNode(BaseModel):
    call_type: CallType
    address: Any
    value: int = 0
    depth: int = 0
    gas_limit: Optional[int]
    gas_cost: Optional[int]  # calculated from call starting and return
    calldata: Any = HexBytes(b"")
    returndata: Any = HexBytes(b"")
    calls: List["CallTreeNode"] = []
    selfdestruct: bool = False
    failed: bool = False
    display_cls: Type[DisplayableCallTreeNode] = DisplayableCallTreeNode

    @property
    def display_nodes(self) -> Iterator[DisplayableCallTreeNode]:
        return self.display_cls.make_tree(self)

    @validator("address", "calldata", "returndata", pre=True)
    def validate_hexbytes(cls, v) -> HexBytes:
        return _convert_hexbytes(cls, v)

    def __str__(self) -> str:
        return "\n".join([str(t) for t in self.display_nodes])

    def __repr__(self) -> str:
        return str(self)

    def __getitem__(self, index: int) -> "CallTreeNode":
        return self.calls[index]


def get_calltree_from_geth_trace(
    trace: Iterator[TraceFrame], show_internal=False, **root_node_kwargs
) -> CallTreeNode:
    """
    Creates a CallTreeNode from a given transaction trace.

    Args:
        trace (Iterator[TraceFrame]): Iterator of transaction trace frames.
        show_internal (bool): Boolean whether to display internal calls. Defaulted to False.
        root_node_kwargs (dict): Keyword arguments passed to the root ``CallTreeNode``.

    Returns:
        :class:`~evm_trace.base.CallTreeNode`: Call tree of transaction trace.
    """

    node = _create_node_from_call(
        trace=trace,
        show_internal=show_internal,
        **root_node_kwargs,
    )
    return node


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

    end_index = stop_word + 1
    byte_slice = b"".join(memory[start_word:end_index])
    offset_index = offset_int % 32

    # NOTE: Add 4 for the selector.

    end_bytes_index = offset_index + size_int
    return_bytes = byte_slice[offset_index:end_bytes_index]
    return HexBytes(return_bytes)


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
            child_node_kwargs = {
                "address": frame.stack[-2][-20:],
                "depth": frame.depth,
                "gas_limit": int(frame.stack[-1].hex(), 16),
                "gas_cost": frame.gas_cost,
            }

            # TODO: Validate gas values

            if frame.op == "CALL":
                child_node_kwargs["call_type"] = CallType.CALL
                child_node_kwargs["value"] = int(frame.stack[-3].hex(), 16)
                child_node_kwargs["calldata"] = _extract_memory(
                    offset=frame.stack[-4], size=frame.stack[-5], memory=frame.memory
                )
            elif frame.op == "DELEGATECALL":
                child_node_kwargs["call_type"] = CallType.DELEGATECALL
                child_node_kwargs["calldata"] = _extract_memory(
                    offset=frame.stack[-3], size=frame.stack[-4], memory=frame.memory
                )
            else:
                child_node_kwargs["call_type"] = CallType.STATICCALL
                child_node_kwargs["calldata"] = _extract_memory(
                    offset=frame.stack[-3], size=frame.stack[-4], memory=frame.memory
                )

            child_node = _create_node_from_call(trace=trace, **child_node_kwargs)
            node.calls.append(child_node)

        # TODO: Handle internal nodes using JUMP and JUMPI

        elif frame.op == "SELFDESTRUCT":
            # TODO: Handle the internal value transfer
            node.selfdestruct = True
            break

        elif frame.op == "STOP":
            # TODO: Handle "execution halted" vs. gas limit reached
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
