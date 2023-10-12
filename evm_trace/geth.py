import math
from typing import Dict, Iterator, List, Optional

from eth_pydantic_types import HashBytes20, HexBytes
from eth_utils import to_int
from pydantic import Field, RootModel, field_validator

from evm_trace.base import BaseModel, CallTreeNode
from evm_trace.enums import CALL_OPCODES, CallType


class TraceMemory(RootModel[List[HexBytes]]):
    root: List[HexBytes] = []

    def get(self, offset: HexBytes, size: HexBytes):
        return extract_memory(offset, size, self.root)


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

    memory: TraceMemory = TraceMemory()
    """Execution memory."""

    storage: Dict[HexBytes, HexBytes] = {}
    """Contract storage."""

    contract_address: Optional[HashBytes20] = None
    """The address producing the frame."""

    @field_validator("pc", "gas", "gas_cost", "depth", mode="before")
    def validate_ints(cls, value):
        return int(value, 16) if isinstance(value, str) else value

    @property
    def address(self) -> Optional[HashBytes20]:
        """
        The address of this CALL frame.
        Only returns a value if this frame's opcode is a call-based opcode.
        """

        if not self.contract_address and (
            self.op in CALL_OPCODES and CallType.CREATE.value not in self.op
        ):
            self.contract_address = HashBytes20.__eth_pydantic_validate__(self.stack[-2][-20:])

        return self.contract_address


def create_trace_frames(data: Iterator[Dict]) -> Iterator[TraceFrame]:
    """
    Get trace frames from ``debug_traceTransaction`` response items.
    Sets the ``contract_address`` for CREATE and CREATE2 frames by
    looking ahead and finding it.

    Args:
        data (Iterator[Dict]): An iterator of response struct logs.

    Returns:
        Iterator[:class:`~evm_trace.geth.TraceFrame`]
    """

    # NOTE: Use a new iter in case a list or something is passed in.
    # This logic requires an iterator.
    frames = iter(data)

    for frame in frames:
        frame_obj = TraceFrame(**frame)

        if CallType.CREATE.value in frame_obj.op:
            # Look ahead to find the address.
            create_frames = _get_create_frames(frame_obj, frames)
            yield from create_frames

        else:
            yield TraceFrame(**frame)


def _get_create_frames(frame: TraceFrame, frames: Iterator[Dict]) -> List[TraceFrame]:
    create_frames = [frame]
    start_depth = frame.depth
    for next_frame in frames:
        next_frame_obj = TraceFrame.model_validate(next_frame)
        depth = next_frame_obj.depth

        if CallType.CREATE.value in next_frame_obj.op:
            # Handle CREATE within a CREATE.
            create_frames.extend(_get_create_frames(next_frame_obj, frames))

        elif depth <= start_depth:
            # Extract the address for the original CREATE using
            # the first frame after the CREATE with an equal depth.
            if len(next_frame_obj.stack) > 0:
                raw_addr = HexBytes(next_frame_obj.stack[-1][-40:])
                frame.contract_address = HashBytes20.__eth_pydantic_validate__(raw_addr)

            create_frames.append(next_frame_obj)
            break

        elif depth > start_depth:
            create_frames.append(next_frame_obj)

    return create_frames


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
        data["calldata"] = frame.memory.get(frame.stack[-4], frame.stack[-5])
    elif frame.op == CallType.DELEGATECALL.value:
        data["call_type"] = CallType.DELEGATECALL
        data["calldata"] = frame.memory.get(frame.stack[-3], frame.stack[-4])

    # `calldata` and `address` are handle in later frames for CREATE and CREATE2.
    elif frame.op == CallType.CREATE.value:
        data["call_type"] = CallType.CREATE
        data["value"] = int(frame.stack[-1].hex(), 16)
    elif frame.op == CallType.CREATE2.value:
        data["call_type"] = CallType.CREATE2
        data["value"] = int(frame.stack[-1].hex(), 16)

    else:
        data["call_type"] = CallType.STATICCALL
        data["calldata"] = frame.memory.get(frame.stack[-3], frame.stack[-4])

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

    if isinstance(trace, list):
        # NOTE: We don't officially support lists here,
        # but if we don't do this, the user gets a recursion error
        # and it is confusing as to why.
        trace = iter(trace)

    if show_internal:
        raise NotImplementedError()

    # Store node details and do all validation at the end.
    # This allow us to wild-hold required properties until they are known.
    for frame in trace:
        if (
            node_kwargs.get("last_create_depth")
            and frame.depth == node_kwargs["last_create_depth"][-1]
        ):
            # If we get here, we are in the process of completing the attributes from
            # a CREATE or CREATE2 node. The data is located at the first frame with the same depth
            # after the CREATE or CREATE2 opcode was found. This idea is copied from Brownie.
            node_kwargs["last_create_depth"].pop()
            for subcall in node_kwargs.get("calls", [])[::-1]:
                if subcall.call_type in (CallType.CREATE, CallType.CREATE2):
                    subcall.address = HashBytes20.__eth_pydantic_validate__(frame.stack[-1][-40:])
                    if len(frame.stack) >= 5:
                        subcall.calldata = frame.memory.get(frame.stack[-4], frame.stack[-5])

                    break

        if frame.op in [x.value for x in CALL_OPCODES]:
            # NOTE: Because of the different meanings in structLog style gas values,
            # gas is not set for nodes created this way.
            data = create_call_node_data(frame)
            if data.get("call_type") in (CallType.CREATE, CallType.CREATE2):
                data["last_create_depth"] = [frame.depth]
                if "last_create_depth" in node_kwargs:
                    node_kwargs["last_create_depth"].append(frame.depth)
                else:
                    node_kwargs["last_create_depth"] = [frame.depth]

            subcall = _create_node(trace=trace, show_internal=show_internal, **data)
            if "calls" in node_kwargs:
                node_kwargs["calls"].append(subcall)
            else:
                node_kwargs["calls"] = [subcall]

        # TODO: Handle internal nodes using JUMP and JUMPI

        elif frame.op == CallType.SELFDESTRUCT.value:
            # TODO: Handle the internal value transfer
            node_kwargs["selfdestruct"] = True
            break

        elif frame.op == "STOP":
            # TODO: Handle "execution halted" vs. gas limit reached
            break

        elif frame.op in ("RETURN", "REVERT") and not node_kwargs.get("returndata"):
            node_kwargs["returndata"] = frame.memory.get(frame.stack[-1], frame.stack[-2])

            # TODO: Handle "execution halted" vs. gas limit reached
            node_kwargs["failed"] = frame.op == "REVERT"
            break

        # TODO: Handle invalid opcodes (`node.failed = True`)
        # NOTE: ignore other opcodes

    # TODO: Handle "execution halted" vs. gas limit reached

    if "last_create_depth" in node_kwargs:
        del node_kwargs["last_create_depth"]

    if node_kwargs["call_type"] in (CallType.CREATE, CallType.CREATE2) and not node_kwargs.get(
        "address"
    ):
        # Set temporary address so validation succeeds.
        node_kwargs["address"] = 20 * b"\x00"

    node = CallTreeNode(**node_kwargs)
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
