from pathlib import Path

import pytest

from evm_trace.parity import ParityTraceList, get_calltree_from_parity_trace

from .expected_traces import (
    PARITY_CALL_TRACE_EXPECTED_OUTPUT,
    PARITY_CREATE_REVERT_TRACE_EXPECTED_OUTPUT,
    PARITY_CREATE_TRACE_EXPECTED_OUTPUT,
    PARITY_OUT_OF_GAS_TRACE_EXPECTED_OUTPUT,
    PARITY_REVERT_TRACE_EXPECTED_OUTPUT,
    PARITY_SELFDESTRUCT_TRACE_EXPECTED_OUTPUT,
)

DATA_PATH = Path(__file__).parent / "data" / "parity"
EXPECTED_OUTPUT_MAP = {
    "call": PARITY_CALL_TRACE_EXPECTED_OUTPUT,
    "create": PARITY_CREATE_TRACE_EXPECTED_OUTPUT,
    "selfdestruct": PARITY_SELFDESTRUCT_TRACE_EXPECTED_OUTPUT,
    "revert": PARITY_REVERT_TRACE_EXPECTED_OUTPUT,
    "error": PARITY_OUT_OF_GAS_TRACE_EXPECTED_OUTPUT,
    "create_revert": PARITY_CREATE_REVERT_TRACE_EXPECTED_OUTPUT,
}


@pytest.mark.parametrize(
    "name", ("call", "create", "selfdestruct", "revert", "error", "create_revert")
)
def test_parity(name):
    path = DATA_PATH / f"{name}.json"
    traces = ParityTraceList.parse_file(path)
    actual = get_calltree_from_parity_trace(traces)
    expected = EXPECTED_OUTPUT_MAP[name].strip()
    assert repr(actual) == expected
