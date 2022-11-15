import pytest
from hexbytes import HexBytes
from pydantic import ValidationError

from evm_trace import CallType
from evm_trace.base import TraceFrame, get_calltree_from_geth_trace


def test_trace_frame_validation_passes(trace_frame_data):
    frame = TraceFrame(**trace_frame_data)
    assert frame


def test_trace_no_memory():
    pc = 0
    op = "REVERT"
    gas = 4732305
    gas_cost = 3
    depth = 1
    stack = []
    trace_frame = TraceFrame(pc=pc, op=op, gas=gas, gasCost=gas_cost, depth=depth, stack=stack)
    assert trace_frame.pc == pc
    assert trace_frame.op == op
    assert trace_frame.gas == gas
    assert trace_frame.gas_cost == gas_cost
    assert trace_frame.depth == depth
    assert trace_frame.stack == []


@pytest.mark.parametrize(
    "test_data",
    (
        {"stack": ["potato"]},
        {"memory": ["potato"]},
        {"storage": {"piggy": "dippin"}},
    ),
)
def test_trace_frame_validation_fails(test_data, trace_frame_data):
    data = {**trace_frame_data, **test_data}
    with pytest.raises(ValidationError):
        TraceFrame(**data)


def test_get_calltree_from_geth_trace(trace_frame_data):
    trace_frame_data["op"] = "RETURN"
    returndata = HexBytes("0x0000000000000000000000004d4d2c55eae97a04acafb66011df29463b665732")
    root_node_kwargs = {
        "gas_cost": 123,
        "gas_limit": 1234,
        "address": "0x56764a0000000000000000000000000000000031",
        "calldata": HexBytes("0x21325"),
        "value": 34,
        "call_type": CallType.CALL,
        "failed": False,
        "returndata": returndata,
    }
    frames = (TraceFrame(**d) for d in (trace_frame_data,))
    actual = get_calltree_from_geth_trace(frames, **root_node_kwargs)

    # Tests against a bug where we could not set the return data.
    assert actual.returndata == returndata
