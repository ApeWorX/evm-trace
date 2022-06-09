import pytest
from pydantic import ValidationError

from evm_trace.base import TraceFrame


def test_trace_frame_validation_passes(trace_frame_data):
    frame = TraceFrame(**trace_frame_data)
    assert frame


@pytest.mark.parametrize(
    "test_data",
    (
        {"stack": ["potato"]},
        {"memory": ["potato"]},
        {"storage": {"piggy": "dippin"}},
    ),
)
def test_trace_frame_validation_fails(test_data, trace_frame_data):
    data = {**trace_frame_data, **test_data}
    with pytest.raises(ValidationError):
        TraceFrame(**data)
