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
    expected = f"""
CALL: {address}.<{calldata[:10]}>
└── CREATE2: 0x7c23b43594428A657718713FF246C609EeDDfAFf
    """.strip()
    assert len(node.calls) == 1
    assert repr(node) == expected.strip()

    expected_value = 123
    expected_calldata = HexBytes(
        "0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
        "bcf7fffd8b256ec51a36782a52d0c34f6474d95100000000000000000000000000000000000000000000000000"
        "000000000000000000000000000000000000000000000000000000000000000000000000000003000000000000"
        "000000000000000000000000000000000000000000000000000360206101356000396000516000556101166100"
        "1f61000039610116610000f36003361161000c576100fe565b60003560e01c346101045763425ace5281186100"
        "3957600436106101045760036040526001606052610077565b6350144002811861005c57602436106101045760"
        "04356040526001606052610077565b6318b30cb781186100a1576044361061010457604060046040375b604051"
        "15610104576040516060518082018281106101045790509050600055600160805260206080f35b63c7dd9abe81"
        "186100bf576004361061010457600160405260206040f35b6327871d9981186100dd5760043610610104576001"
        "60405260206040f35b63f9bd55cc81186100fc57600436106101045760005460405260206040f35b505b600060"
        "00fd5b600080fda165767970657283000307000b00000000000000000000000000000000000000000000000000"
        "00000000000003"
    )
    create_node = node.calls[0]
    assert create_node.value == expected_value
    assert create_node.calldata.startswith(expected_calldata)
