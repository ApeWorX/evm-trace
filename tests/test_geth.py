import pytest
from ethpm_types import HexBytes
from pydantic import ValidationError

from evm_trace.enums import CallType
from evm_trace.geth import (
    TraceFrame,
    get_calltree_from_geth_call_trace,
    get_calltree_from_geth_trace,
)


class TestTraceFrame:
    def test_validation_passes(self, trace_frame_data):
        frame = TraceFrame(**trace_frame_data)
        assert frame

    def test_no_memory(self):
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
    def test_validation_fails(self, test_data, trace_frame_data):
        data = {**trace_frame_data, **test_data}
        with pytest.raises(ValidationError):
            TraceFrame(**data)

    def test_address(self, call_frame_data):
        frame = TraceFrame(**call_frame_data)
        assert frame.address == HexBytes("0x274b028b03a250ca03644e6c578d81f019ee1323")


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


def test_get_calltree_from_geth_call_trace(geth_call_trace_data):
    node = get_calltree_from_geth_call_trace(geth_call_trace_data)
    expected = """
    CALL: 0xF2Df0b975c0C9eFa2f8CA0491C2d1685104d2488.<0x372dca07> [280038 gas]
├── CALL: 0xBcF7FFFD8B256Ec51a36782a52D0c34f6474D951.<0x045856de> [34004 gas]
├── CALL: 0xBcF7FFFD8B256Ec51a36782a52D0c34f6474D951.<0xbeed0f85> [62443 gas]
│   ├── STATICCALL: 0x274b028b03A250cA03644E6c578D81f019eE1323.<0x7007cbe8> [1497 gas]
│   └── CALL: 0x274b028b03A250cA03644E6c578D81f019eE1323.<0x878fb701> [41458 gas]
├── CALL: 0xBcF7FFFD8B256Ec51a36782a52D0c34f6474D951.<0xb27b8804> [723 gas]
├── CALL: 0xBcF7FFFD8B256Ec51a36782a52D0c34f6474D951.<0xb9e5b20a> [91563 gas]
│   ├── STATICCALL: 0x274b028b03A250cA03644E6c578D81f019eE1323.<0xe5e1d93f> [2375 gas]
│   ├── CALL: 0x274b028b03A250cA03644E6c578D81f019eE1323.<0x878fb701> [33858 gas]
│   ├── CALL: 0x274b028b03A250cA03644E6c578D81f019eE1323.<0x90bb7141> [25171 gas]
│   └── CALL: 0x274b028b03A250cA03644E6c578D81f019eE1323.<0x90bb7141> [23171 gas]
├── STATICCALL: 0x274b028b03A250cA03644E6c578D81f019eE1323.<0xbff2e095> [2814 gas]
├── STATICCALL: 0xBcF7FFFD8B256Ec51a36782a52D0c34f6474D951.<0x9155fd57> [859 gas]
├── CALL: 0xBcF7FFFD8B256Ec51a36782a52D0c34f6474D951.<0xbeed0f85> [32643 gas]
│   ├── STATICCALL: 0x274b028b03A250cA03644E6c578D81f019eE1323.<0x7007cbe8> [1497 gas]
│   └── CALL: 0x274b028b03A250cA03644E6c578D81f019eE1323.<0x878fb701> [25758 gas]
└── CALL: 0xBcF7FFFD8B256Ec51a36782a52D0c34f6474D951.<0xbeed0f85> [32643 gas]
    ├── STATICCALL: 0x274b028b03A250cA03644E6c578D81f019eE1323.<0x7007cbe8> [1497 gas]
    └── CALL: 0x274b028b03A250cA03644E6c578D81f019eE1323.<0x878fb701> [25758 gas]
    """
    assert repr(node) == expected.strip()
