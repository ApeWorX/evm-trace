import pytest
from pydantic import ValidationError

from evm_trace import CallTreeNode
from evm_trace.gas import GasReport, GasReportValidation, _merge_reports, get_gas_report

report1: GasReport = {
    "address1": {"willcombine": [1]},
    "address2": {"different": [2]},
}

report2: GasReport = {
    "address1": {"willcombine": [1]},
    "address2": {"willNOTcombine": [2]},
    "address3": {"notincludedinreport1": [3]},
}


def test_builds_gas_report(call_tree_data):
    tree = CallTreeNode(**call_tree_data)
    gas_report = get_gas_report(tree)

    for call in tree.calls:
        assert call.address in gas_report


def test_merged_reports():
    merged = _merge_reports(report1=report1, report2=report2)

    assert merged == {
        "address1": {"willcombine": [1, 1]},
        "address2": {"different": [2], "willNOTcombine": [2]},
        "address3": {"notincludedinreport1": [3]},
    }


@pytest.mark.parametrize(
    "test_data",
    (
        {"address": "d8dA6BF269"},
        {"address": "0x71c7656ec7ab88b098defb751b7401b5f6d8976f"},
    ),
)
def test_gas_report_validation_fail(test_data):
    with pytest.raises(ValidationError):
        GasReportValidation(**test_data)


def test_gas_report_validation_pass():
    valid = GasReportValidation(
        address="71c7656ec7ab88b098defb751b7401b5f6d8976f",
        method_id=b"88888888",
    )

    assert valid.address.hex() == "0x71c7656ec7ab88b098defb751b7401b5f6d8976f"
    assert valid.method_id.hex() == "0x38383838"
    assert valid.gas_cost is None
