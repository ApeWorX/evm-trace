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
