import pytest
from eth_pydantic_types import HexBytes

from evm_trace import CallTreeNode
from evm_trace.gas import GasReport, get_gas_report, merge_reports

# Simplified version of gas reports only for testing purposes
CONTRACT_A = HexBytes("0x0000000000000000000000000000000000000001")
CONTRACT_B = HexBytes("0x0000000000000000000000000000000000000002")
CONTRACT_C = HexBytes("0x0000000000000000000000000000000000000003")
METHOD_A = HexBytes("0x181d60da")
METHOD_B = HexBytes("0xc7cee1b7")
METHOD_C = HexBytes("0xd76d0659")

reports: list[GasReport] = [
    {
        CONTRACT_A: {METHOD_A: [100, 101, 100, 102]},
        CONTRACT_B: {METHOD_B: [200, 202, 202, 200, 200]},
    },
    {
        CONTRACT_A: {METHOD_A: [105, 106]},
        CONTRACT_B: {METHOD_A: [200, 201]},
        CONTRACT_C: {METHOD_C: [300]},
    },
]


def test_get_gas_report(call_tree_data):
    tree = CallTreeNode(**call_tree_data)
    gas_report = get_gas_report(tree)

    def assert_all(t):
        assert t.address in gas_report
        for c in t.calls:
            assert_all(c)

    assert_all(tree)


def test_merge_reports():
    merged = merge_reports(*reports)
    assert merged == {
        CONTRACT_A: {METHOD_A: [100, 101, 100, 102, 105, 106]},
        CONTRACT_B: {METHOD_A: [200, 201], METHOD_B: [200, 202, 202, 200, 200]},
        CONTRACT_C: {METHOD_C: [300]},
    }


def test_merge_single_report():
    actual = merge_reports(reports[0])
    expected = reports[0]
    assert actual == expected


def test_merge_no_reports():
    assert merge_reports() == {}


@pytest.mark.parametrize("cost,expected", [(None, []), (0, [0]), (7, [7])])
def test_gas_samples_distinguish_zero_from_unknown(cost, expected):
    tree = CallTreeNode(call_type="CALL", address=CONTRACT_A, calldata=METHOD_A, gas_cost=cost)
    assert get_gas_report(tree)[CONTRACT_A][METHOD_A] == expected


def test_zero_gas_samples_survive_nested_report_merging():
    tree = CallTreeNode(
        call_type="CALL",
        address=CONTRACT_A,
        calldata=METHOD_A,
        gas_cost=10,
        calls=[
            CallTreeNode(call_type="CALL", address=CONTRACT_A, calldata=METHOD_A, gas_cost=cost)
            for cost in (0, None, 5)
        ],
    )
    assert get_gas_report(tree)[CONTRACT_A][METHOD_A] == [10, 0, 5]
