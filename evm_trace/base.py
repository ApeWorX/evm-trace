import math
from typing import Dict, Iterator, List, Optional

from eth_utils import to_int
from ethpm_types import BaseModel, HexBytes
from pydantic import Field, validator

from evm_trace.display import get_tree_display
from evm_trace.enums import CallType


class TraceFrame(BaseModel):
    pc: int
    op: str
    gas: int
    gas_cost: int = Field(alias="gasCost")
    depth: int
    stack: List[HexBytes] = []
    memory: List[HexBytes] = []
    storage: Dict[HexBytes, HexBytes] = {}

    @validator("pc", "gas", "gas_cost", "depth", pre=True)
    def validate_ints(cls, value):
        return int(value, 16) if isinstance(value, str) else value


class CallTreeNode(BaseModel):
    call_type: CallType
    address: HexBytes = HexBytes("")
    value: int = 0
    depth: int = 0
    gas_limit: Optional[int] = None
    gas_cost: Optional[int] = None  # calculated from call starting and return
    calldata: HexBytes = HexBytes("")
    returndata: HexBytes = HexBytes("")
    calls: List["CallTreeNode"] = []
    selfdestruct: bool = False
    failed: bool = False

    def __str__(self) -> str:
        return get_tree_display(self)

    def __repr__(self) -> str:
        return str(self)

    def __getitem__(self, index: int) -> "CallTreeNode":
        return self.calls[index]


def get_calltree_from_geth_trace(
    trace: Iterator[TraceFrame], show_internal: bool = False, **root_node_kwargs
) -> CallTreeNode:
    """
    Creates a CallTreeNode from a given transaction trace.

    Args:
        trace (Iterator[TraceFrame]): Iterator of transaction trace frames.
        show_internal (bool): Boolean whether to display internal calls.
          Defaults to ``False``.
        root_node_kwargs (dict): Keyword arguments passed to the root ``CallTreeNode``.

    Returns:
        :class:`~evm_trace.base.CallTreeNode`: Call tree of transaction trace.
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
        return HexBytes("")

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

            child_node = _create_node_from_call(
                trace=trace, show_internal=show_internal, **child_node_kwargs
            )
            node.calls.append(child_node)

        # TODO: Handle internal nodes using JUMP and JUMPI

        elif frame.op == "SELFDESTRUCT":
            # TODO: Handle the internal value transfer
            node.selfdestruct = True
            break

        elif frame.op == "STOP":
            # TODO: Handle "execution halted" vs. gas limit reached
            break

        elif frame.op in ("RETURN", "REVERT") and not node.returndata:
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
