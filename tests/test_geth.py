import re

import pytest
from ethpm_types import HexBytes

from evm_trace._pydantic_compat import ValidationError
from evm_trace.enums import CallType
from evm_trace.geth import (
    TraceFrame,
    create_trace_frames,
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


def test_get_calltree_from_geth_trace_when_given_list(trace_frame_data):
    """
    Ensure we don't get recursion error!
    """
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
    frames = [TraceFrame(**trace_frame_data)]
    actual = get_calltree_from_geth_trace(frames, **root_node_kwargs)

    # Tests against a bug where we could not set the return data.
    assert actual.returndata == returndata


def test_get_calltree_from_geth_call_trace(call_trace_data):
    node = get_calltree_from_geth_call_trace(call_trace_data)
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


def test_get_call_tree_from_call_deploy_call_trace(deploy_call_trace_data):
    node = get_calltree_from_geth_call_trace(deploy_call_trace_data)
    expected = "CREATE: 0x274b028b03A250cA03644E6c578D81f019eE1323 [70148 gas]"
    assert repr(node) == expected.strip()


def test_get_call_tree_from_create2_struct_logs(geth_create2_trace_frames):
    address = "0x274b028b03A250cA03644E6c578D81f019eE1323"
    calldata = "0x88ab52d4000000000000000000000000274b028b03a250ca03644e6c578d81f019ee1323"
    node = get_calltree_from_geth_trace(
        (x for x in geth_create2_trace_frames),
        call_type=CallType.CALL,
        address=address,
        gas_limit=30000000,
        calldata=HexBytes(calldata),
    )
    assert len(node.calls) == 2
    actual = repr(node)[:120]
    pattern = re.compile(
        rf".*\s*CALL: {address}\."
        rf"<{calldata[:10]}>\s*├── CREATE2: 0x[a-fA-F0-9]{{40}}[\s└─├\w:.<?>]*"
    )
    assert pattern.match(actual), f"actual: {actual}, pattern: {str(pattern)}"


def test_create_trace_frames_from_geth_create2_struct_logs(
    geth_create2_struct_logs, geth_create2_trace_frames
):
    frames = list(create_trace_frames(geth_create2_struct_logs))
    assert len(frames) == len(geth_create2_trace_frames)
    assert frames != geth_create2_trace_frames

    create2_found = False
    for frame in frames:
        if frame.op.startswith("CREATE"):
            assert frame.address
            address = frame.address.hex()
            assert address.startswith("0x")
            assert len(address) == 42
            create2_found = create2_found or frame.op == "CREATE2"

    assert create2_found
