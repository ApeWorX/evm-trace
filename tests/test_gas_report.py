from typing import List

from ethpm_types import HexBytes

from evm_trace import CallTreeNode
from evm_trace.gas import GasReport, get_gas_report, merge_reports

# Simplified version of gas reports only for testing purposes
reports: List[GasReport] = [
    {
        HexBytes("1"): {HexBytes("10"): [1]},
        HexBytes("2"): {HexBytes("20"): [2]},
    },
    {
        HexBytes("1"): {HexBytes("10"): [1]},
        HexBytes("2"): {HexBytes("21"): [2]},
        HexBytes("3"): {HexBytes("30"): [3]},
    },
]


def test_builds_gas_report(call_tree_data):
    tree = CallTreeNode(**call_tree_data)
    gas_report = get_gas_report(tree)

    for call in tree.calls:
        assert call.address in gas_report


def test_merged_reports():
    merged = merge_reports(*reports)

    assert merged == {
        HexBytes("0x01"): {HexBytes("0x10"): [1, 1]},
        HexBytes("0x02"): {HexBytes("0x20"): [2], HexBytes("0x21"): [2]},
        HexBytes("0x03"): {HexBytes("0x30"): [3]},
    }
