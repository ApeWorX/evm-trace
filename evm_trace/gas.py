from typing import Any, Dict, List

from hexbytes import HexBytes
from pydantic import BaseModel, ValidationError, validator

from evm_trace.base import CallTreeNode
from evm_trace.utils import _convert_hexbytes

Report = Dict[str, Dict[str, List[int]]]


class Address(BaseModel):
    address: Any

    @validator("address", pre=True)
    def validate_hexbytes(cls, v) -> HexBytes:
        """
        A valid address is 20 bytes.
        """
        value = _convert_hexbytes(cls, v)

        if len(v) != 20:
            raise ValidationError

        return value


class MethodId(BaseModel):
    method_id: Any

    @validator("method_id", pre=True)
    def validate_hexbytes(cls, v) -> HexBytes:
        """
        Method ids are 4 bytes at the beginning of calldata.
        """
        value = _convert_hexbytes(cls, v)

        if len(value) > 4:
            value = value[:4]

        return value


def get_gas_report(calltree: CallTreeNode) -> Report:
    """
    Extracts a gas report object from a :class:`~evm_trace.base.CallTreeNode`.

    Args:
        calltree (:class:`~evm_trace.base.CallTreeNode`): extractable call tree

    Returns:
        :class:`~evm_trace.gas.Report`: Gas report structure from a call tree.
    """
    address = Address(address=calltree.address)
    method_id = MethodId(method_id=calltree.calldata)

    report = {str(address): {str(method_id): [calltree.gas_cost] if calltree.gas_cost else []}}

    for node in calltree.calls:
        report = _merge_reports(report, get_gas_report(node))

    return report


def _merge_reports(report1: Report, report2: Report) -> Report:
    """
    Private helper method for merging two reports.
    """
    merged_report: Report = report1.copy()

    for outer_key, inner_dict in report2.items():
        if outer_key in merged_report:
            for inner_key, inner_list in report2[outer_key].items():
                if inner_key in merged_report[outer_key]:
                    merged_report[outer_key][inner_key].extend(inner_list)
                else:
                    merged_report[outer_key][inner_key] = inner_list
        else:
            merged_report[outer_key] = inner_dict

    return merged_report
