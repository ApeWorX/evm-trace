from copy import deepcopy

import pytest
from pydantic import ValidationError

from evm_trace.base import TraceFrame

TRACE_FRAME_STRUCTURE = {
    "pc": 1564,
    "op": "RETURN",
    "gas": 0,
    "gasCost": 0,
    "depth": 1,
    "stack": [
        "0000000000000000000000000000000000000000000000000000000040c10f19",
        "0000000000000000000000000000000000000000000000000000000000000020",
        "0000000000000000000000000000000000000000000000000000000000000140",
    ],
    "memory": [
        "0000000000000000000000001e59ce931b4cfea3fe4b875411e280e173cb7a9c",
        "0000000000000000000000000000000000000000000000000000000000000001",
    ],
    "storage": {
        "0000000000000000000000000000000000000000000000000000000000000004": "0000000000000000000000001e59ce931b4cfea3fe4b875411e280e173cb7a9c",  # noqa: E501
        "ad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5": "0000000000000000000000001e59ce931b4cfea3fe4b875411e280e173cb7a9c",  # noqa: E501
        "aadb61a4b4c5d48b7a5669391b7c73852a3ab7795f24721b9a439220b54b591b": "0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    },
}


def test_trace_frame_validation_passes():
    frame = TraceFrame(**TRACE_FRAME_STRUCTURE)
    assert frame


trace_frame_test_cases = (
    {"stack": ["potato"]},
    {"memory": ["potato"]},
    {"storage": {"piggy": "dippin"}},
)


@pytest.mark.parametrize("test_value", trace_frame_test_cases)
def test_trace_frame_validation_fails(test_value):
    trace_frame_structure = deepcopy(TRACE_FRAME_STRUCTURE)
    trace_frame_structure.update(test_value)

    with pytest.raises(ValidationError):
        TraceFrame(**trace_frame_structure)
