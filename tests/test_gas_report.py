import pytest
from ethpm_types import HexBytes
from pydantic import ValidationError

from evm_trace import CallTreeNode
from evm_trace.gas import GasReport, GasReportValidation, _merge_reports, get_gas_report

# Simplified version of gas reports only for testing purposes
report1: GasReport = {
    HexBytes("1"): {HexBytes("10"): [1]},
    HexBytes("2"): {HexBytes("20"): [2]},
}

report2: GasReport = {
    HexBytes("1"): {HexBytes("10"): [1]},
    HexBytes("2"): {HexBytes("21"): [2]},
    HexBytes("3"): {HexBytes("30"): [3]},
}


def test_builds_gas_report(call_tree_data):
    tree = CallTreeNode(**call_tree_data)
    gas_report = get_gas_report(tree)

    for call in tree.calls:
        assert call.address in gas_report


def test_merged_reports():
    merged = _merge_reports(report1=report1, report2=report2)

    assert merged == {
        HexBytes("0x01"): {HexBytes("0x10"): [1, 1]},
        HexBytes("0x02"): {HexBytes("0x20"): [2], HexBytes("0x21"): [2]},
        HexBytes("0x03"): {HexBytes("0x30"): [3]},
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
