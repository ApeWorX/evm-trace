from typing import Dict, List

from evm_trace.base import CallTreeNode

Address = str
Calldata = bytes
GasUsage = int

GasReport = Dict[Address, Dict[Calldata, List[GasUsage]]]


def extract_gas_report(calltree: CallTreeNode) -> GasReport:
    report = {
        calltree.address: {calltree.calldata: [calltree.gas_cost] if calltree.gas_cost else []}
    }

    for call in calltree.calls:
        report = combine_gas_reports(report, extract_gas_report(call))

    return report


def combine_gas_reports(report1: GasReport, report2: GasReport) -> GasReport:

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
