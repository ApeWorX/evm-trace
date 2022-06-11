import json
from pathlib import Path
from typing import Dict, List

import pytest

from evm_trace.parity import ParityTrace, get_calltree_from_parity_trace

from .expected_traces import (
    PARITY_CALL_TRACE_EXPECTED_OUTPUT,
    PARITY_CREATE_TRACE_EXPECTED_OUTPUT,
    PARITY_SELFDESTRUCT_TRACE_EXPECTED_OUTPUT,
    PARITY_REVERT_TRACE_EXPECTED_OUTPUT,
)

DATA_PATH = Path(__file__).parent / "data" / "parity"
EXPECTED_OUTPUT_MAP = {
    "call": PARITY_CALL_TRACE_EXPECTED_OUTPUT,
    "create": PARITY_CREATE_TRACE_EXPECTED_OUTPUT,
    "selfdestruct": PARITY_SELFDESTRUCT_TRACE_EXPECTED_OUTPUT,
    "revert": PARITY_REVERT_TRACE_EXPECTED_OUTPUT,
}


@pytest.mark.parametrize("name", ("call", "create", "selfdestruct", "revert"))
def test_parity(name):
    raw_data: List[Dict] = json.loads((DATA_PATH / f"{name}.json").read_text())
    traces = [ParityTrace.parse_obj(d) for d in raw_data]
    actual = get_calltree_from_parity_trace(traces[0], traces)
    expected = EXPECTED_OUTPUT_MAP[name].strip()
    assert repr(actual) == expected
