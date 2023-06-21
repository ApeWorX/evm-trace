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
        "0x00000000000000000000000000000000000000000000000000000000000"
        "00000000000000000000000000000bcf7fffd8b256ec51a36782a52d0c34f"
        "6474d95100000000000000000000000000000000000000000000000000000"
        "0000000000000000000000000000000000000000000000000000000000000"
        "0000000000000300000000000000000000000000000000000000000000000"
        "000000000000000033461013b576020610140600039600051600055610116"
        "61002461000039610116610000f36003361161000c576100fe565b6000356"
        "0e01c346101045763425ace52811861003957600436106101045760036040"
        "526001606052610077565b6350144002811861005c5760243610610104576"
        "004356040526001606052610077565b6318b30cb781186100a15760443610"
        "61010457604060046040375b6040511561010457604051606051808201828"
        "1106101045790509050600055600160805260206080f35b63c7dd9abe8118"
        "6100bf576004361061010457600160405260206040f35b6327871d9981186"
        "100dd576004361061010457600160405260206040f35b63f9bd55cc811861"
        "00fc57600436106101045760005460405260206040f35b505b60006000fd5"
        "b600080fda165767970657283000307000b005b600080fd00000000000000"
        "00000000000000000000000000000000000000000000000003"
    )
    create_node = node.calls[0]
    assert create_node.value == expected_value
    assert create_node.calldata.startswith(expected_calldata)
