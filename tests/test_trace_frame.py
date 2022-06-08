import pytest
from pydantic import ValidationError

from evm_trace.base import TraceFrame


def test_trace_frame_validation_passes(trace_frame_structure):
    frame = TraceFrame(**trace_frame_structure)
    assert frame


@pytest.mark.parametrize(
    "test_data",
    (
        {"stack": ["potato"]},
        {"memory": ["potato"]},
        {"storage": {"piggy": "dippin"}},
    ),
)
def test_trace_frame_validation_fails(test_data, trace_frame_structure):
    data = {**trace_frame_structure, **test_data}
    with pytest.raises(ValidationError):
        TraceFrame(**data)
