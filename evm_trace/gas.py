import copy
from typing import Dict, List, TypeVar

from evm_trace.base import CallTreeNode

ContractID = TypeVar("ContractID")
MethodID = TypeVar("MethodID")
GasReport = Dict[ContractID, Dict[MethodID, List[int]]]


def get_gas_report(calltree: CallTreeNode) -> GasReport:
    """
    Extracts a gas report object from a :class:`~evm_trace.base.CallTreeNode`.

    Args:
        calltree (:class:`~evm_trace.base.CallTreeNode`): call tree used for gas report.

    Returns:
        :class:`~evm_trace.gas.GasReport`: Gas report structure from a call tree.
    """
    report = {
        calltree.address: {calltree.calldata[:4]: [calltree.gas_cost] if calltree.gas_cost else []}
    }
    return merge_reports(report, *map(get_gas_report, calltree.calls))


def merge_reports(*reports: GasReport) -> GasReport:
    """
    Merge method for merging a list of gas reports and combining a list of gas costs.
    If given a single report, it only returns it.
    """
    reports_ls = list(reports)
    num_reports = len(reports_ls)
    if num_reports == 0:
        return {}

    elif num_reports == 1:
        return reports_ls[0]

    merged_report: GasReport = copy.deepcopy(reports_ls.pop(0))
    for report in reports_ls:
        for outer_key, inner_dict in report.items():
            if outer_key not in merged_report:
                merged_report[outer_key] = inner_dict
                continue

            for inner_key, inner_list in report[outer_key].items():
                if inner_key in merged_report[outer_key]:
                    merged_report[outer_key][inner_key].extend(inner_list)
                else:
                    merged_report[outer_key][inner_key] = inner_list

    return merged_report
