import copy
from typing import Dict, List

from ethpm_types import BaseModel, HexBytes
from pydantic import validator

from evm_trace.base import CallTreeNode

GasReport = Dict[HexBytes, Dict[HexBytes, List[int]]]


class GasReportValidation(BaseModel):
    address: HexBytes
    method_id: HexBytes
    gas_cost: int

    @validator("address")
    def validate_address(cls, v) -> HexBytes:
        """
        A valid address is 20 bytes.
        """
        if len(v) != 20:
            raise ValueError("`address` should be 20 bytes.")

        return v

    @validator("method_id")
    def validate_method_id(cls, v) -> HexBytes:
        """
        Method ids are 4 bytes at the beginning of calldata.
        """
        if len(v) > 4:
            v = v[:4]

        return v


def get_gas_report(calltree: CallTreeNode) -> GasReport:
    """
    Extracts a gas report object from a :class:`~evm_trace.base.CallTreeNode`.

    Args:
        calltree (:class:`~evm_trace.base.CallTreeNode`): call tree used for gas report.

    Returns:
        :class:`~evm_trace.gas.Report`: Gas report structure from a call tree.
    """
    valid = GasReportValidation(
        address=calltree.address, method_id=calltree.calldata, gas_cost=calltree.gas_cost
    )

    report = {valid.address: {valid.method_id: [valid.gas_cost]}}

    report = _merge_reports([report, *map(get_gas_report, calltree.calls)])

    return report


def _merge_reports(reports: List[GasReport]) -> GasReport:
    """
    Private helper method for merging two reports.
    """
    merged_report: GasReport = copy.deepcopy(reports.pop(0))

    if len(reports) < 1:
        return merged_report

    for report in reports:
        for outer_key, inner_dict in report.items():
            if outer_key in merged_report:
                for inner_key, inner_list in report[outer_key].items():
                    if inner_key in merged_report[outer_key]:
                        merged_report[outer_key][inner_key].extend(inner_list)
                    else:
                        merged_report[outer_key][inner_key] = inner_list
            else:
                merged_report[outer_key] = inner_dict

    return merged_report
