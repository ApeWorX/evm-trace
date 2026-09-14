from collections.abc import Iterator

from eth_pydantic_types import HexBytes, HexBytes20
from eth_utils import to_hex, to_int
from pydantic import Field, RootModel, field_validator

from evm_trace.base import BaseModel, CallTreeNode, EventNode
from evm_trace.enums import CALL_OPCODES, CallType

# Geth's OpCode.String() formats unknown opcodes as "opcode 0xXX not defined".
UNKNOWN_OPCODE_PREFIX = "opcode 0x"


def _stack_address(value: HexBytes) -> HexBytes20:
    return HexBytes20.__eth_pydantic_validate__(value[-20:].rjust(20, b"\x00"))


class TraceMemory(RootModel[list[HexBytes]]):
    root: list[HexBytes] = []

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

    stack: list[HexBytes] = []
    """Execution stack."""

    memory: TraceMemory = TraceMemory()
    """Execution memory."""

    storage: dict[HexBytes, HexBytes] = {}
    """Contract storage."""

    error: str | None = None
    """Execution error reported on this instruction, if any."""

    return_data: HexBytes | None = Field(alias="returnData", default=None)
    """The return-data buffer, when the client was configured to include it."""

    contract_address: HexBytes20 | None = None
    """The address producing the frame."""

    @field_validator("pc", "gas", "gas_cost", "depth", mode="before")
    def validate_ints(cls, value):
        return int(value, 16) if isinstance(value, str) else value

    @property
    def address(self) -> HexBytes20 | None:
        """
        The address of this CALL frame.
        Only returns a value if this frame's opcode is a call-based opcode.
        """

        if not self.contract_address and (
            self.op in CALL_OPCODES and CallType.CREATE.value not in self.op
        ):
            self.contract_address = _stack_address(self.stack[-2])

        return self.contract_address


def create_trace_frames(data: Iterator[dict]) -> Iterator[TraceFrame]:
    """
    Get trace frames from ``debug_traceTransaction`` response items.
    Sets the ``contract_address`` for CREATE and CREATE2 frames by
    looking ahead and finding it.

    Args:
        data (Iterator[dict]): An iterator of response struct logs.

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
            yield frame_obj


def _get_create_frames(frame: TraceFrame, frames: Iterator[dict]) -> list[TraceFrame]:
    create_frames = [frame]
    pending_creates = [frame]
    for next_frame in frames:
        next_frame_obj = TraceFrame.model_validate(next_frame)
        # Resolve the previous CREATE before handling a consecutive CREATE at the same depth.
        while pending_creates and next_frame_obj.depth <= pending_creates[-1].depth:
            previous = pending_creates.pop()
            if next_frame_obj.depth == previous.depth and next_frame_obj.stack:
                previous.contract_address = _stack_address(next_frame_obj.stack[-1])
        create_frames.append(next_frame_obj)
        if next_frame_obj.op in (CallType.CREATE, CallType.CREATE2):
            pending_creates.append(next_frame_obj)
        if not pending_creates:
            break

    return create_frames


def get_calltree_from_geth_call_trace(data: dict) -> CallTreeNode:
    """
    Creates a CallTreeNode from a given transaction call trace.

    Args:
        data (dict): The response from ``debug_traceTransaction`` when using
          ``tracer=callTracer``.

    Returns:
        :class:`~evm_trace.base.CallTreeNode`: Call tree of transaction trace.
    """

    data = _validate_data_from_call_tracer(data)
    root = CallTreeNode(**data)

    def fix_depth(node: CallTreeNode):
        for event in node.events:
            event.depth = node.depth + 1
        for child in node.calls:
            child.depth = node.depth + 1
            fix_depth(child)

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
          The legacy ``callType`` alias is accepted for ``call_type``.

    Returns:
        :class:`~evm_trace.base.CallTreeNode`: Call tree of transaction trace.
    """

    # Preserve the public alias without passing it into recursive node construction.
    if "callType" in root_node_kwargs:
        root_node_kwargs["call_type"] = root_node_kwargs.pop("callType")

    return _create_node(
        trace=trace,
        show_internal=show_internal,
        **root_node_kwargs,
    )


def create_call_node_data(frame: TraceFrame) -> dict:
    """
    Parse a CALL-opcode frame into an address and calldata.

    Args:
        frame (:class:`~evm_trace.geth.TraceFrame`): The call frame to parse.

    Returns:
        Tuple[str, HexBytes]: A tuple of the address str and the calldata.
    """

    data: dict = {"address": frame.address, "depth": frame.depth}
    if frame.op in (CallType.CALL.value, CallType.CALLCODE.value):
        data["call_type"] = CallType(frame.op)
        data["value"] = int(to_hex(frame.stack[-3]), 16)
        data["calldata"] = frame.memory.get(frame.stack[-4], frame.stack[-5])
    elif frame.op == CallType.DELEGATECALL.value:
        data["call_type"] = CallType.DELEGATECALL
        data["calldata"] = frame.memory.get(frame.stack[-3], frame.stack[-4])

    # Initcode is in the CREATE frame; the new address is learned after returning.
    elif frame.op == CallType.CREATE.value:
        data["call_type"] = CallType.CREATE
        data["value"] = int(to_hex(frame.stack[-1]), 16)
        data["calldata"] = frame.memory.get(frame.stack[-2], frame.stack[-3])
    elif frame.op == CallType.CREATE2.value:
        data["call_type"] = CallType.CREATE2
        data["value"] = int(to_hex(frame.stack[-1]), 16)
        data["calldata"] = frame.memory.get(frame.stack[-2], frame.stack[-3])

    else:
        data["call_type"] = CallType.STATICCALL
        data["calldata"] = frame.memory.get(frame.stack[-3], frame.stack[-4])

    return data


def extract_memory(offset: HexBytes, size: HexBytes, memory: list[HexBytes]) -> HexBytes:
    """
    Extracts memory from the EVM stack.

    Args:
        offset (HexBytes): Offset byte location in memory.
        size (HexBytes): Number of bytes to return.
        memory (list[HexBytes]): Memory stack.

    Returns:
        HexBytes: Byte value from memory stack.
    """

    size_int = to_int(size)

    if size_int == 0:
        return HexBytes("")

    offset_int = to_int(offset)

    # Compute the word that contains the first byte
    start_word = offset_int // 32
    # Compute the word that contains the last byte
    stop_word = (offset_int + size_int + 31) // 32

    byte_slice = b"".join(memory[start_word:stop_word])
    offset_index = offset_int % 32

    end_bytes_index = offset_index + size_int
    return_bytes = byte_slice[offset_index:end_bytes_index].ljust(size_int, b"\x00")
    return HexBytes(return_bytes)


class _FrameIterator:
    """Iterator with one-frame lookahead."""

    def __init__(self, frames: Iterator[TraceFrame]):
        self.frames = iter(frames)
        self.next_frame = next(self.frames, None)

    def pop(self) -> TraceFrame:
        frame = self.next_frame
        if frame is None:
            raise StopIteration
        self.next_frame = next(self.frames, None)
        return frame


def _create_node(
    trace: Iterator[TraceFrame] | _FrameIterator, show_internal: bool = False, **node_kwargs
) -> CallTreeNode:
    """Build a branching call tree using the opcodes documented at https://www.evm.codes/."""
    if show_internal:
        raise NotImplementedError()

    frames = trace if isinstance(trace, _FrameIterator) else _FrameIterator(trace)
    node_kwargs.setdefault("call_type", CallType.CALL)
    # Normalize model-supported hex depths before computing child depths.
    node_kwargs["depth"] = CallTreeNode.validate_ints(node_kwargs.get("depth", 0))
    evm_depth = frames.next_frame.depth if frames.next_frame else 0

    while frames.next_frame is not None and frames.next_frame.depth == evm_depth:
        frame = frames.pop()
        if frame.error or frame.op == "INVALID" or frame.op.startswith(UNKNOWN_OPCODE_PREFIX):
            node_kwargs["failed"] = True
            break

        if frame.op in CALL_OPCODES:
            data = create_call_node_data(frame)
            data["depth"] = node_kwargs["depth"] + 1
            if frame.op == "DELEGATECALL":
                data["value"] = node_kwargs.get("value", 0)
            is_create = frame.op in (CallType.CREATE, CallType.CREATE2)
            if is_create and data["address"] is None:
                data["address"] = b""
            entered = frames.next_frame is not None and frames.next_frame.depth > evm_depth
            subcall = _create_node(frames, **data) if entered else CallTreeNode(**data)

            resumed = frames.next_frame
            if resumed is not None and resumed.depth == evm_depth and resumed.stack:
                result = to_int(resumed.stack[-1])
                if is_create and result == 0 and not subcall.failed:
                    # Initcode can RETURN successfully but fail code validation/deposit.
                    # Those bytes are not returned to the caller; REVERT data is retained.
                    subcall.returndata = HexBytes(b"")
                subcall.failed = subcall.failed or result == 0
                if is_create:
                    # Zero reports failure, not the attempted contract's address.
                    # Keep the default empty address when the address is unknown.
                    subcall.address = _stack_address(resumed.stack[-1]) if result else HexBytes(b"")
                elif not entered:
                    # Memory only exposes a possibly truncated copy, not the output's length.
                    if resumed.return_data is not None:
                        subcall.returndata = resumed.return_data
            node_kwargs.setdefault("calls", []).append(subcall)

        elif frame.op.startswith("LOG"):
            event = _create_event_node(frame)
            event.depth = node_kwargs["depth"] + 1
            event.position = len(node_kwargs.get("calls", []))
            node_kwargs.setdefault("events", []).append(event)
        elif frame.op == "SELFDESTRUCT":
            node_kwargs["selfdestruct"] = True
            break
        elif frame.op == "STOP":
            break
        elif frame.op in ("RETURN", "REVERT"):
            if not node_kwargs.get("returndata"):
                node_kwargs["returndata"] = frame.memory.get(frame.stack[-1], frame.stack[-2])
            if frame.op == "REVERT":
                node_kwargs["failed"] = True
            break

    return CallTreeNode(**node_kwargs)


def _create_event_node(frame: TraceFrame) -> EventNode:
    # The number of topics is derived from the opcode,
    # e.g. LOG2 means two topics, including the selector for non-anonymous events.
    num_topics = int(frame.op[3])

    topics = [frame.stack[-3 - index].rjust(32, b"\x00") for index in range(num_topics)]

    # Figure out data.
    data = frame.memory.get(frame.stack[-1], frame.stack[-2])

    return EventNode(data=data, depth=frame.depth, topics=topics)


def _validate_data_from_call_tracer(data: dict) -> dict:
    data = dict(data)
    if data.get("error"):
        data["failed"] = True
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

    if "logs" in data:
        # Depth is assigned after constructing the tree. Copy each log to leave
        # the RPC response untouched, including when parsing it more than once.
        data["events"] = [
            *data.get("events", []),
            *({**log, "depth": 0} for log in data.pop("logs") or []),
        ]

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
