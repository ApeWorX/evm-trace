import re

import pytest
from eth_pydantic_types import HexBytes
from eth_utils import to_checksum_address
from pydantic import ValidationError

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


def test_get_calltree_from_geth_trace_handles_events(geth_structlogs):
    frames = [TraceFrame.model_validate(f) for f in geth_structlogs]
    actual = get_calltree_from_geth_trace(frames)
    contract_a = "e7f1725e7734ce288f8367e1bb143e90bb3f0512"
    contract_a_checksum = to_checksum_address(contract_a)
    expected_selector_0 = "0x7289bf584c70dbd1e1a9f47d4d86498048378245f23434470bbda959f708d0ff"
    expected_selector_1 = "0x61fb72029c258791b830903dd8de307390e49a1673acb59083b1d0e26ce73e33"
    expected_selector_2 = "0x5fc4e95e3c9b74ccfcc1edd97348437b79c0596201a3d5b11ffa63c3fb80cd69"
    expected_repr = f"""
CALL
├── CALL: {contract_a_checksum}.<0x045856de>
├── CALL: {contract_a_checksum}.<0xbeed0f85>
│   ├── STATICCALL: 0x5FbDB2315678afecb367f032d93F642f64180aa3.<0x7007cbe8>
│   └── CALL: 0x5FbDB2315678afecb367f032d93F642f64180aa3.<0x878fb701>
│       ├── EVENT: {expected_selector_0}
│       ├── EVENT: {expected_selector_1}
│       └── EVENT: {expected_selector_2}
├── CALL: {contract_a_checksum}.<0xb27b8804>
├── CALL: {contract_a_checksum}.<0xb9e5b20a>
│   ├── STATICCALL: 0x5FbDB2315678afecb367f032d93F642f64180aa3.<0xe5e1d93f>
│   ├── CALL: 0x5FbDB2315678afecb367f032d93F642f64180aa3.<0x878fb701>
│   │   ├── EVENT: {expected_selector_0}
│   │   ├── EVENT: {expected_selector_1}
│   │   └── EVENT: {expected_selector_2}
│   ├── CALL: 0x5FbDB2315678afecb367f032d93F642f64180aa3.<0x90bb7141>
│   └── CALL: 0x5FbDB2315678afecb367f032d93F642f64180aa3.<0x90bb7141>
├── STATICCALL: 0x5FbDB2315678afecb367f032d93F642f64180aa3.<0xbff2e095>
├── STATICCALL: 0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512.<0x9155fd57>
├── CALL: {contract_a_checksum}.<0xbeed0f85>
│   ├── STATICCALL: 0x5FbDB2315678afecb367f032d93F642f64180aa3.<0x7007cbe8>
│   └── CALL: 0x5FbDB2315678afecb367f032d93F642f64180aa3.<0x878fb701>
│       ├── EVENT: {expected_selector_0}
│       ├── EVENT: {expected_selector_1}
│       └── EVENT: {expected_selector_2}
└── CALL: {contract_a_checksum}.<0xbeed0f85>
    ├── STATICCALL: 0x5FbDB2315678afecb367f032d93F642f64180aa3.<0x7007cbe8>
    └── CALL: 0x5FbDB2315678afecb367f032d93F642f64180aa3.<0x878fb701>
        ├── EVENT: {expected_selector_0}
        ├── EVENT: {expected_selector_1}
        └── EVENT: {expected_selector_2}
""".strip()
    actual_repr = repr(actual)
    assert actual_repr == expected_repr

    # Assertions related to direct event data.
    actual_events = actual.calls[-1].calls[-1].events
    assert len(actual_events) == 3

    # Assert `.selector` is correct.
    assert actual_events[0].selector == HexBytes(expected_selector_0)
    assert actual_events[1].selector == HexBytes(expected_selector_1)
    assert actual_events[2].selector == HexBytes(expected_selector_2)

    # Assert `.topics` is correct.
    assert actual_events[0].topics == [
        HexBytes(expected_selector_0),
        HexBytes(f"0x000000000000000000000000{contract_a}"),
        HexBytes("0x0000000000000000000000000000000000000000000000000000000000000001"),
    ]
    assert actual_events[1].topics == [
        HexBytes(expected_selector_1),
        HexBytes(f"0x000000000000000000000000{contract_a}"),
    ]
    assert actual_events[2].topics == [
        HexBytes(expected_selector_2),
        HexBytes("0x0000000000000000000000000000000000000000000000000000000000000005"),
        HexBytes("0x0000000000000000000000000000000000000000000000000000000000000006"),
        HexBytes("0x0000000000000000000000000000000000000000000000000000000000000007"),
    ]

    # Assert `.data` is correct.
    assert actual_events[0].data == HexBytes(
        "0x0000000000000000000000000000000000000000000000000000000000000002"
        "0000000000000000000000000000000000000000000000000000000000000003"
    )
    assert actual_events[1].data == HexBytes(f"0x000000000000000000000000{contract_a}")
    assert actual_events[2].data == HexBytes(
        "0x0000000000000000000000000000000000000000000000000000000000000008"
        "0000000000000000000000000000000000000000000000000000000000000009"
        "000000000000000000000000000000000000000000000000000000000000000a"
    )


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
