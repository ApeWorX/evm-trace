from evm_trace import CallTreeNode
from evm_trace.gas import GasReport, combine_gas_reports, extract_gas_report

report1: GasReport = {
    "address1": {b"willcombine": [1]},
    "address2": {b"different": [2]},
}

report2: GasReport = {
    "address1": {b"willcombine": [1]},
    "address2": {b"willNOTcombine": [2]},
    "address3": {b"notincludedinreport1": [3]},
}


def test_builds_gas_report(call_tree_data):
    tree = CallTreeNode(**call_tree_data)
    report = extract_gas_report(tree)
    assert report


def test_combine_gas_reports():
    combined = combine_gas_reports(report1=report1, report2=report2)
    assert combined == {
        "address1": {b"willcombine": [1, 1]},
        "address2": {b"different": [2], b"willNOTcombine": [2]},
        "address3": {b"notincludedinreport1": [3]},
    }
