from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from evm_trace.base import CallTreeNode

ContractID = TypeVar("ContractID")
MethodID = TypeVar("MethodID")
GasReport = dict[ContractID, dict[MethodID, list[int]]]


def get_gas_report(calltree: "CallTreeNode") -> GasReport:
    """
    Extracts a gas report object from a :class:`~evm_trace.base.CallTreeNode`.

    Args:
        calltree (:class:`~evm_trace.base.CallTreeNode`): call tree used for gas report.

    Returns:
        :class:`~evm_trace.gas.GasReport`: Gas report structure from a call tree.
    """
    report = {
        calltree.address: {
            calltree.calldata[:4]: [calltree.gas_cost] if calltree.gas_cost is not None else []
        }
    }
    return merge_reports(report, *map(get_gas_report, calltree.calls))


def merge_reports(*reports: GasReport) -> GasReport:
    """
    Merge method for merging a list of gas reports and combining a list of gas costs.
    """
    merged_report: GasReport = {}
    for report in reports:
        for contract_id, methods in report.items():
            merged_methods = merged_report.setdefault(contract_id, {})
            for method_id, gas_costs in methods.items():
                merged_methods.setdefault(method_id, []).extend(gas_costs)

    return merged_report
