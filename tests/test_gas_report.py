from evm_trace import CallTreeNode
from evm_trace.gas import Report, _merge_reports, get_gas_report

report1: Report = {
    "address1": {"willcombine": [1]},
    "address2": {"different": [2]},
}

report2: Report = {
    "address1": {"willcombine": [1]},
    "address2": {"willNOTcombine": [2]},
    "address3": {"notincludedinreport1": [3]},
}


def test_builds_gas_report(call_tree_data):
    tree = CallTreeNode(**call_tree_data)
    gas_report = get_gas_report(tree)

    assert gas_report


def test_merged_reports():
    merged = _merge_reports(report1=report1, report2=report2)

    assert merged == {
        "address1": {"willcombine": [1, 1]},
        "address2": {"different": [2], "willNOTcombine": [2]},
        "address3": {"notincludedinreport1": [3]},
    }
