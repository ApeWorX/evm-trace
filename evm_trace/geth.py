import math
from typing import Dict, Iterator, List, Optional

from eth_utils import to_int
from ethpm_types import BaseModel, HexBytes
from pydantic import Field, validator

from evm_trace.base import CallTreeNode
from evm_trace.enums import CALL_OPCODES, CallType


class TraceFrame(BaseModel):
    """
    A low-level data structure modeling a transaction trace frame
    from the Geth RPC ``debug_traceTransaction``.
    """

    pc: int
    """Program counter."""

    op: str
    """Opcode."""

    gas: int
    """Remaining gas."""

    gas_cost: int = Field(alias="gasCost")
    """The cost to execute this opcode."""

    depth: int
    """
    The number of external jumps away the initially called contract (starts at 0).
    """

    stack: List[HexBytes] = []
    """Execution stack."""

    memory: List[HexBytes] = []
    """Execution memory."""

    storage: Dict[HexBytes, HexBytes] = {}
    """Contract storage."""

    @validator("pc", "gas", "gas_cost", "depth", pre=True)
    def validate_ints(cls, value):
        return int(value, 16) if isinstance(value, str) else value

    @property
    def address(self) -> Optional[HexBytes]:
        """
        The address of this CALL frame.
        Only returns a value if this frame's opcode is a call-based opcode.
        """

        if self.op not in CALL_OPCODES:
            return None

        return HexBytes(self.stack[-2][-20:])


def get_calltree_from_geth_call_trace(data: Dict) -> CallTreeNode:
    """
    Creates a CallTreeNode from a given transaction call trace.

    Args:
        data (Dict): The response from ``debug_traceTransaction`` when using
          ``tracer=callTracer``.

    Returns:
        :class:`~evm_trace.base.CallTreeNode`: Call tree of transaction trace.
    """

    data = _validate_data_from_call_tracer(data)
    root = CallTreeNode(**data)

    def fix_depth(r: CallTreeNode):
        for c in r.calls:
            c.depth = r.depth + 1
            fix_depth(c)

    fix_depth(root)
    return root


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

    return _create_node(
        trace=trace,
        show_internal=show_internal,
        **root_node_kwargs,
    )


def create_call_node_data(frame: TraceFrame) -> Dict:
    """
    Parse a CALL-opcode frame into an address and calldata.

    Args:
        frame (:class:`~evm_trace.geth.TraceFrame`): The call frame to parse.

    Returns:
        Tuple[str, HexBytes]: A tuple of the address str and the calldata.
    """

    data: Dict = {"address": frame.address, "depth": frame.depth}
    if frame.op == CallType.CALL.value:
        data["call_type"] = CallType.CALL
        data["value"] = int(frame.stack[-3].hex(), 16)
        data["calldata"] = extract_memory(
            offset=frame.stack[-4], size=frame.stack[-5], memory=frame.memory
        )
    elif frame.op == CallType.DELEGATECALL.value:
        data["call_type"] = CallType.DELEGATECALL
        data["calldata"] = extract_memory(
            offset=frame.stack[-3], size=frame.stack[-4], memory=frame.memory
        )
    else:
        data["call_type"] = CallType.STATICCALL
        data["calldata"] = extract_memory(
            offset=frame.stack[-3], size=frame.stack[-4], memory=frame.memory
        )

    return data


def extract_memory(offset: HexBytes, size: HexBytes, memory: List[HexBytes]) -> HexBytes:
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


def _create_node(
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
        if frame.op in [x.value for x in CALL_OPCODES]:
            # NOTE: Because of the different meanings in structLog style gas values,
            # gas is not set for nodes created this way.
            data = create_call_node_data(frame)
            child = _create_node(trace=trace, show_internal=show_internal, **data)
            node.calls.append(child)

        # TODO: Handle internal nodes using JUMP and JUMPI

        elif frame.op == CallType.SELFDESTRUCT.value:
            # TODO: Handle the internal value transfer
            node.selfdestruct = True
            break

        elif frame.op == "STOP":
            # TODO: Handle "execution halted" vs. gas limit reached
            break

        elif frame.op in ("RETURN", "REVERT") and not node.returndata:
            node.returndata = extract_memory(
                offset=frame.stack[-1], size=frame.stack[-2], memory=frame.memory
            )
            # TODO: Handle "execution halted" vs. gas limit reached
            node.failed = frame.op == "REVERT"
            break

        # TODO: Handle invalid opcodes (`node.failed = True`)
        # NOTE: ignore other opcodes

    # TODO: Handle "execution halted" vs. gas limit reached

    return node


def _validate_data_from_call_tracer(data: Dict) -> Dict:
    # Handle renames
    if "receiver" in data:
        data["address"] = data.pop("receiver")
    elif "to" in data:
        data["address"] = data.pop("to")
    if "input" in data:
        data["calldata"] = data.pop("input")
    if "output" in data:
        data["returndata"] = data.pop("output")
    if "gasUsed" in data:
        data["gas_cost"] = data.pop("gasUsed")
    if "gas" in data:
        data["gas_limit"] = data.pop("gas")
    if "type" in data:
        data["call_type"] = data.pop("type")

    # Remove unneeded keys
    unneeded_keys = ("sender", "from")
    for key in unneeded_keys:
        if key in data:
            del data[key]

    # Handle sub calls
    def fix_call_calls(r):
        r["calls"] = [
            _validate_data_from_call_tracer(x) for x in r.get("calls", []) if isinstance(x, dict)
        ]

    fix_call_calls(data)
    return data
