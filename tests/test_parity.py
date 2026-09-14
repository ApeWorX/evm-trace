from pathlib import Path

import pytest

from evm_trace.geth import (
    create_trace_frames,
    get_calltree_from_geth_call_trace,
    get_calltree_from_geth_trace,
)
from evm_trace.parity import ParityTraceList, get_calltree_from_parity_trace

from .expected_traces import (
    PARITY_CALL_TRACE_EXPECTED_OUTPUT,
    PARITY_CREATE2_EXPECTED_OUTPUT,
    PARITY_CREATE_REVERT_TRACE_EXPECTED_OUTPUT,
    PARITY_CREATE_TRACE_EXPECTED_OUTPUT,
    PARITY_OUT_OF_GAS_TRACE_EXPECTED_OUTPUT,
    PARITY_REVERT_TRACE_EXPECTED_OUTPUT,
    PARITY_REVERT_TRACE_WITH_MESSAGE_EXPECTED_OUTPUT,
    PARITY_SELFDESTRUCT_TRACE_EXPECTED_OUTPUT,
)
from .trace_helpers import semantic_tree

DATA_PATH = Path(__file__).parent / "data" / "parity"
EXPECTED_OUTPUT_MAP = {
    "call": PARITY_CALL_TRACE_EXPECTED_OUTPUT,
    "create": PARITY_CREATE_TRACE_EXPECTED_OUTPUT,
    "selfdestruct": PARITY_SELFDESTRUCT_TRACE_EXPECTED_OUTPUT,
    "revert": PARITY_REVERT_TRACE_EXPECTED_OUTPUT,
    "error": PARITY_OUT_OF_GAS_TRACE_EXPECTED_OUTPUT,
    "create_revert": PARITY_CREATE_REVERT_TRACE_EXPECTED_OUTPUT,
    "revert_with_message": PARITY_REVERT_TRACE_WITH_MESSAGE_EXPECTED_OUTPUT,
}


@pytest.mark.parametrize(
    "name",
    ("call", "create", "selfdestruct", "revert", "error", "create_revert", "revert_with_message"),
)
def test_parity(name):
    assert name in EXPECTED_OUTPUT_MAP, f"Missing expected output set for '{name}'."
    path = DATA_PATH / f"{name}.json"
    traces = ParityTraceList.model_validate_json(path.read_text())
    actual = repr(get_calltree_from_parity_trace(traces))

    expected = EXPECTED_OUTPUT_MAP[name].strip()
    assert actual == expected


def test_create2(parity_create2_trace_list):
    call_tree = get_calltree_from_parity_trace(parity_create2_trace_list)
    actual = repr(call_tree)
    expected = PARITY_CREATE2_EXPECTED_OUTPUT.strip()
    assert actual == expected


def test_parity_call_tree_matches_call_tracer(trace_case):
    name, case = trace_case
    actual = semantic_tree(
        get_calltree_from_parity_trace(ParityTraceList.model_validate(case["parity"]["trace"]))
    )
    expected = semantic_tree(get_calltree_from_geth_call_trace(case["call_tracer"]))
    if name == "precompile_then_contract":
        # Reth's Parity call trace deliberately omits the zero-value precompile.
        expected["calls"].pop(0)
    if name in ("create2", "create2_return_code"):
        # The Parity action only says "create"; it does not identify CREATE2.
        expected["calls"][0]["type"] = "CREATE"
    assert actual == expected


def test_mainnet_tracing_methods_match(mainnet_trace_case):
    case = mainnet_trace_case
    transaction = case["transaction"]
    struct_tree = get_calltree_from_geth_trace(
        create_trace_frames(case["geth"]["structLogs"]),
        address=transaction["to"],
        calldata=transaction["input"],
        value=transaction["value"],
    )
    call_tree = get_calltree_from_geth_call_trace(case["call_tracer"])
    parity_tree = get_calltree_from_parity_trace(
        ParityTraceList.model_validate(case["parity"]["trace"])
    )
    transaction_tree = get_calltree_from_parity_trace(
        ParityTraceList.model_validate(case["trace_transaction"])
    )
    assert semantic_tree(struct_tree) == semantic_tree(call_tree) == semantic_tree(parity_tree)
    assert parity_tree == transaction_tree
