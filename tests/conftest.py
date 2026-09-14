import gzip
import json
from pathlib import Path

import pytest

from evm_trace import ParityTrace, ParityTraceList, TraceFrame
from evm_trace.enums import CallType

DATA_PATH = Path(__file__).parent / "data"
GETH_DATA = DATA_PATH / "geth"
EVM_TRACE_DATA = DATA_PATH / "evm_trace"
PARITY_DATA = DATA_PATH / "parity"
TRACE_FRAME_DATA = json.loads((EVM_TRACE_DATA / "frame.json").read_text(encoding="utf8"))
CALL_FRAME_DATA = json.loads((EVM_TRACE_DATA / "call.json").read_text(encoding="utf8"))
MUTABLE_CALL_TREE_DATA = json.loads(
    (EVM_TRACE_DATA / "mutable_call.json").read_text(encoding="utf8")
)
STATIC_CALL_TREE_DATA = json.loads((EVM_TRACE_DATA / "static_call.json").read_text(encoding="utf8"))
DELEGATE_CALL_TREE_DATA = json.loads(
    (EVM_TRACE_DATA / "delegate_call.json").read_text(encoding="utf8")
)
CALL_TRACE_DATA = json.loads((GETH_DATA / "call.json").read_text())
CREATE_CALL_TRACE_DATA = json.loads((GETH_DATA / "create_call.json").read_text(encoding="utf8"))
GETH_TRACE = json.loads((GETH_DATA / "structlogs.json").read_text(encoding="utf8"))
GETH_CREATE2_TRACE = json.loads((GETH_DATA / "create2_structlogs.json").read_text(encoding="utf8"))
PARITY_CREATE2_TRACE = json.loads((PARITY_DATA / "create2.json").read_text(encoding="utf8"))
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


@pytest.fixture(scope="session")
def parity_create2_trace_list():
    trace_list = [ParityTrace.model_validate(x) for x in PARITY_CREATE2_TRACE]
    return ParityTraceList(root=trace_list)


@pytest.fixture(scope="session")
def geth_structlogs():
    return GETH_TRACE


@pytest.fixture(scope="session")
def geth_create2_struct_logs():
    return GETH_CREATE2_TRACE


@pytest.fixture(scope="session")
def geth_create2_trace_frames(geth_create2_struct_logs):
    # NOTE: These frames won't have the CREATE address set.
    return [TraceFrame(**x) for x in geth_create2_struct_logs]


# Recorded trace cases are loaded only when a test requests them.
@pytest.fixture(scope="session")
def reth_trace_cases():
    return json.loads((DATA_PATH / "vmtrace/reth.json").read_text())["cases"]


@pytest.fixture(
    params=[
        "mstore",
        "mload_expansion",
        "sha3_expansion",
        "return_expansion",
        "revert_expansion",
        "log0",
        "log2",
        "mcopy",
        "transient",
        "blobhash",
        "push0_dup_swap",
        "storage",
        "sload_existing",
        "invalid",
        "underflow_call",
        "underflow_add",
        "out_of_gas_memory",
        "call",
        "delegatecall",
        "delegatecall_value",
        "callcode",
        "staticcall",
        "eoa_then_contract",
        "precompile_then_contract",
        "failed_child_then_contract",
        "invalid_child_then_contract",
        "nested_siblings",
        "create",
        "create2",
        "create_success",
        "consecutive_create",
        "create_return_code",
        "create2_return_code",
    ]
)
def trace_case(request, reth_trace_cases):
    return request.param, reth_trace_cases[request.param]


@pytest.fixture(scope="session")
def mainnet_trace_cases():
    return json.loads(gzip.decompress((DATA_PATH / "vmtrace/mainnet.json.gz").read_bytes()))[
        "transactions"
    ]


@pytest.fixture(
    params=[
        "0x4893b62e0fc82f4487feb18e6c75d0eebae8dfb3a2e4c64abf7c80b3667c6935",
        "0x6e5839ccc3d278edc1e4bef2f829e89957855973cb9804e6e2e2166ea6583094",
        "0xe004f5ae399484baafc18e52ad119667bef7998e7d5a7711b7ec28856f1d4365",
        "0x8adc58bf2cac357bee014c5099860824796dd92d44efdc3fd0753b88665e1fb1",
    ]
)
def mainnet_trace_case(request, mainnet_trace_cases):
    return mainnet_trace_cases[request.param]
