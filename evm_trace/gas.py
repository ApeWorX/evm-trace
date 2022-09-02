import copy
from typing import Any, Dict, List

from evm_trace.base import CallTreeNode

GasReport = Dict[Any, Dict[Any, List[int]]]


def get_gas_report(calltree: CallTreeNode) -> GasReport:
    """
    Extracts a gas report object from a :class:`~evm_trace.base.CallTreeNode`.

    Args:
        calltree (:class:`~evm_trace.base.CallTreeNode`): call tree used for gas report.

    Returns:
        :class:`~evm_trace.gas.Report`: Gas report structure from a call tree.
    """
    report = {
        calltree.address: {calltree.calldata[:4]: [calltree.gas_cost] if calltree.gas_cost else []}
    }

    report = merge_reports([report, *map(get_gas_report, calltree.calls)])

    return report


def merge_reports(reports: List[GasReport]) -> GasReport:
    """
    Merge method for merging a list of gas reports and combining a list of gas costs.
    """
    merged_report: GasReport = copy.deepcopy(reports.pop(0))

    if len(reports) < 1:
        return merged_report

    for report in reports:
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
