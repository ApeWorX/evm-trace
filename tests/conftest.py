import json
from pathlib import Path

import pytest

from evm_trace import ParityTrace, ParityTraceList, TraceFrame
from evm_trace.enums import CallType

DATA_PATH = Path(__file__).parent / "data"
GETH_DATA = DATA_PATH / "geth"
EVM_TRACE_DATA = DATA_PATH / "evm_trace"
PARITY_DATA = DATA_PATH / "parity"
TRACE_FRAME_DATA = json.loads((EVM_TRACE_DATA / "frame.json").read_text())
CALL_FRAME_DATA = json.loads((EVM_TRACE_DATA / "call.json").read_text())
MUTABLE_CALL_TREE_DATA = json.loads((EVM_TRACE_DATA / "mutable_call.json").read_text())
STATIC_CALL_TREE_DATA = json.loads((EVM_TRACE_DATA / "static_call.json").read_text())
DELEGATE_CALL_TREE_DATA = json.loads((EVM_TRACE_DATA / "delegate_call.json").read_text())
CALL_TRACE_DATA = json.loads((GETH_DATA / "call.json").read_text())
CREATE_CALL_TRACE_DATA = json.loads((GETH_DATA / "create_call.json").read_text())
GETH_CREATE2_TRACE = json.loads((GETH_DATA / "create2_structlogs.json").read_text())
PARITY_CREATE2_TRACE = json.loads((PARITY_DATA / "create2.json").read_text())
CALL_TREE_DATA_MAP = {
    CallType.CALL.value: MUTABLE_CALL_TREE_DATA,
    CallType.STATICCALL.value: STATIC_CALL_TREE_DATA,
    CallType.DELEGATECALL.value: DELEGATE_CALL_TREE_DATA,
}


@pytest.fixture(scope="session")
def trace_frame_data():
    """
    One frame of data from `debug_traceTransaction` using the
    `structLog` tracer (default).
    """
    return TRACE_FRAME_DATA


@pytest.fixture(scope="session")
def call_frame_data():
    """
    One frame of data from `debug_traceTransaction` using the
    `structLog` tracer (default) for a CALL frame.
    """
    return CALL_FRAME_DATA


@pytest.fixture(scope="session")
def call_trace_data():
    """
    The data you get from `debug_traceTransaction` using the
    `callTracer` tracer.
    """
    return CALL_TRACE_DATA


@pytest.fixture(scope="session")
def deploy_call_trace_data():
    """
    The data you get from `debug_traceTransaction` using the
    `callTracer` tracer from a deploy transaction.
    """
    return CREATE_CALL_TRACE_DATA


@pytest.fixture(
    scope="session",
    params=(CallType.CALL.value, CallType.DELEGATECALL.value, CallType.STATICCALL.value),
)
def call_tree_data(request):
    yield CALL_TREE_DATA_MAP[request.param]


@pytest.fixture
def parity_create2_trace_list():
    trace_list = [ParityTrace.parse_obj(x) for x in PARITY_CREATE2_TRACE]
    return ParityTraceList(__root__=trace_list)


@pytest.fixture
def geth_create2_trace_frames():
    return [TraceFrame(**x) for x in GETH_CREATE2_TRACE]
