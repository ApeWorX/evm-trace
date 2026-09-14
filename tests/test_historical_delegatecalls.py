import gzip
import json
from pathlib import Path

import pytest

from evm_trace.geth import (
    create_trace_frames,
    get_calltree_from_geth_call_trace,
    get_calltree_from_geth_trace,
)
from evm_trace.parity import ParityTraceList, get_calltree_from_parity_trace

from .trace_helpers import semantic_tree


@pytest.fixture(params=[(0, 131, 16), (1, 129, 25)], ids=["b7d7f1d5", "0537316f"])
def historical_case(request):
    path = Path(__file__).parent / "data/geth/historical_delegatecalls.json.gz"
    index, calls, delegatecalls = request.param
    case = json.loads(gzip.decompress(path.read_bytes()))["cases"][index]
    return case, calls, delegatecalls


def call_shape(node):
    return {
        key: [call_shape(child) for child in value] if key == "calls" else value
        for key, value in node.items()
        if key not in ("input", "output")
    }


def walk(node):
    yield node
    for child in node.calls:
        yield from walk(child)


def test_historical_structlog_delegatecalls(historical_case):
    case, expected_calls, expected_delegatecalls = historical_case
    transaction = case["transaction"]
    struct_tree = get_calltree_from_geth_trace(
        create_trace_frames(case["struct_logs"]),
        address=transaction["to"],
        calldata=transaction["input"],
        value=transaction["value"],
    )
    call_tree = get_calltree_from_geth_call_trace(case["call_tracer"])
    # Memory was disabled when recording these large traces; compare call structure,
    # addresses, values, depths and failures, not the unavailable calldata/return bytes.
    assert call_shape(semantic_tree(struct_tree)) == call_shape(semantic_tree(call_tree))
    nodes = list(walk(struct_tree))
    assert len(nodes) == expected_calls
    assert sum(node.call_type == "DELEGATECALL" for node in nodes) == expected_delegatecalls


def test_historical_parity_delegatecalls(historical_case):
    case, _, _ = historical_case
    call_tree = get_calltree_from_geth_call_trace(case["call_tracer"])
    parity_tree = get_calltree_from_parity_trace(ParityTraceList.model_validate(case["parity"]))
    if case["transaction"]["hash"].startswith("0x0537316f"):
        # Reth's Parity tracer omits this zero-value ECRECOVER precompile call.
        # Normalize only that exact call, leaving all DELEGATECALLs in the comparison.
        omitted = call_tree.calls[0].calls[22].calls[0].calls.pop(0)
        assert omitted.call_type == "STATICCALL"
        assert omitted.address == bytes.fromhex("00" * 19 + "01")
        assert omitted.value == 0
        assert not omitted.calls
    assert semantic_tree(parity_tree) == semantic_tree(call_tree)
