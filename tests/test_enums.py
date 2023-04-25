import pytest

from evm_trace import CallType


class TestCallType:
    @pytest.mark.parametrize("val", (CallType.CALL, "CALL"))
    def test_eq(self, val):
        call_type = CallType.CALL
        assert call_type == val
