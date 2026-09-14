import pytest

from evm_trace.base import CallTreeNode
from evm_trace.enums import CallType

from .expected_traces import (
    CALL_TRACE_EXPECTED_OUTPUT,
    DELEGATECALL_TRACE_EXPECTED_OUTPUT,
    STATIC_TRACE_EXPECTED_OUTPUT,
)

EXPECTED_OUTPUT_MAP = {
    CallType.CALL: CALL_TRACE_EXPECTED_OUTPUT,
    CallType.STATICCALL: STATIC_TRACE_EXPECTED_OUTPUT,
    CallType.DELEGATECALL: DELEGATECALL_TRACE_EXPECTED_OUTPUT,
}


@pytest.fixture(scope="session")
def call_tree(call_tree_data):
    return CallTreeNode(**call_tree_data)


class TestCallTreeNode:
    def test_call_tree_validation_passes(self, call_tree_data):
        tree = CallTreeNode(**call_tree_data)
        assert tree

    def test_call_tree_mutable_representation(self, call_tree):
        expected = EXPECTED_OUTPUT_MAP[call_tree.call_type].strip()
        assert repr(call_tree) == expected


@pytest.mark.parametrize("positions", [[0, 0, 1, 2], [2, 0, 1, 0]])
def test_event_positions_interleave_with_calls(positions):
    from evm_trace.base import EventNode

    events = [
        EventNode(depth=1, position=position, topics=[bytes([index]) * 32])
        for index, position in enumerate(positions, start=1)
    ]
    tree = CallTreeNode(
        call_type="CALL",
        events=events,
        calls=[CallTreeNode(call_type="STATICCALL"), CallTreeNode(call_type="DELEGATECALL")],
    )
    expected = []
    for position, call_type in enumerate(["STATICCALL", "DELEGATECALL", None]):
        expected.extend(
            f"EVENT: 0x{event.topics[0].hex()}" for event in events if event.position == position
        )
        if call_type:
            expected.append(call_type)
    lines = str(tree).splitlines()[1:]
    assert [line[4:] for line in lines] == expected
    assert all(line.startswith("├── ") for line in lines[:-1])
    assert lines[-1].startswith("└── ")


def test_legacy_and_filtered_event_positions():
    from evm_trace.base import EventNode

    tree = CallTreeNode(
        call_type="CALL",
        events=[EventNode(depth=1), EventNode(depth=1, position=4)],
        calls=[CallTreeNode(call_type="STATICCALL")],
    )
    assert str(tree).splitlines() == [
        "CALL",
        "├── EVENT: None",
        "├── STATICCALL",
        "└── EVENT: None",
    ]
