from typing import Dict, List

from evm_trace.base import CallTreeNode

Address = str
Calldata = bytes
GasUsage = int

GasReport = Dict[Address, Dict[Calldata, List[GasUsage]]]


def extract_gas_report(calltree: CallTreeNode) -> GasReport:
    """
    Extracts a gas report object from a :class:`~evm_trace.base.CallTreeNode`

    Args:
        calltree (:class:`~evm_trace.base.CallTreeNode`): extractable call tree

    Returns:
        :class:`~evm_trace.gas.GasReport`: Gas report structure from a call tree.
    """
    report = {
        calltree.address: {calltree.calldata: [calltree.gas_cost] if calltree.gas_cost else []}
    }

    for call in calltree.calls:
        report = combine_gas_reports(report, extract_gas_report(call))

    return report


def combine_gas_reports(report1: GasReport, report2: GasReport) -> GasReport:
    """
    Combines two gas report objects into a single gas report. :class:`~evm_trace.base.CallTreeNode`

    Args:
        report1 (:class:`~evm_trace.gas.GasReport`): the first instance of GasReport
        report2 (:class:`~evm_trace.gas.GasReport`): the second instance of GasReport

    Returns:
        :class:`~evm_trace.gas.GasReport`: A combined gas report structure.
    """

    for address, calldata_dict in report2.items():
        if address in report1:
            for calldata, gas_cost_list in report2[address].items():
                if calldata in report1[address]:
                    report1[address][calldata].extend(gas_cost_list)
                else:
                    report1[address][calldata] = gas_cost_list
        else:
            report1[address] = calldata_dict

    return report1
