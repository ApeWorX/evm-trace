from typing import List, Optional, Union

from pydantic import BaseModel, Field, validator

from evm_trace.base import CallTreeNode, CallType


class CallAction(BaseModel):
    gas: int
    input: Optional[str] = None
    receiver: Optional[str] = Field(alias="to", default=None)
    sender: str = Field(alias="from")
    value: int

    @validator("value", "gas", pre=True)
    def convert_integer(cls, v):
        return int(v, 16)


class CreateAction(BaseModel):
    gas: int
    init: str
    value: int

    @validator("value", "gas", pre=True)
    def convert_integer(cls, v):
        return int(v, 16)


class SelfDestructAction(BaseModel):
    address: str


class ActionResult(BaseModel):
    gas_used: str = Field(alias="gasUsed")

    @validator("gas_used", pre=True)
    def convert_integer(cls, v):
        return int(v, 16)


class CallResult(ActionResult):
    output: str


class CreateResult(ActionResult):
    address: str
    code: str


ParityTraceAction = Union[CreateAction, CallAction, SelfDestructAction]
ParityTraceResult = Union[CallResult, CreateResult]


class ParityTrace(BaseModel):
    error: Optional[str] = None
    action: ParityTraceAction
    block_hash: str = Field(alias="blockHash")
    call_type: CallType = Field(alias="type")
    result: Optional[ParityTraceResult] = None
    subtraces: int
    trace_address: List[int] = Field(alias="traceAddress")
    transaction_hash: str = Field(alias="transactionHash")

    @validator("call_type", pre=True)
    def convert_call_type(cls, v) -> CallType:
        value = v.upper()
        if value == "SUICIDE":
            value = "SELFDESTRUCT"

        return CallType(value)


def get_calltree_from_parity_trace(root: ParityTrace, traces: List[ParityTrace]) -> CallTreeNode:
    """
    Create a :class:`~evm_trace.base.CallTreeNode` from output models from the Parity approach
    (e.g. from the ``trace_transaction`` RPC).

    Args:
        root (:class:`~evm_trace.parity.ParityTrace`): The root parity trace node.
        traces (List[:class:~evm_trace.parity.ParityTrace]): The list of parity trace nodes,
          likely parsed from the response data from the ``trace_transaction`` RPC response.

    Returns:
        :class:`~evm_trace.base.CallTreeNode`
    """

    node_kwargs = {"call_type": root.call_type, "error": root.error is not None}

    if root.call_type == CallType.CREATE:
        # Init code = action.init
        # Runtime code = result.code
        # Created contract = result.address
        create_action: CreateAction = root.action  # type: ignore
        create_result: CreateResult = root.result  # type: ignore

        node_kwargs = {
            **node_kwargs,
            "address": create_result.address,
            "value": create_action.value,
            "gas_cost": create_result.gas_used,
            "gas_limit": create_action.gas,
            "gas_used": create_result.gas_used,
        }

    elif root.call_type in (CallType.CALL, CallType.DELEGATECALL):
        call_action: CallAction = root.action  # type: ignore
        call_result: CallResult = root.result  # type: ignore

        node_kwargs = {
            **node_kwargs,
            "address": call_action.receiver,
            "value": call_action.value,
            "gas_limit": call_action.gas,
            "gas_cost": call_result.gas_used,
            "calldata": call_action.input,
            "returndata": call_result.output,
        }

    elif root.call_type == CallType.SELFDESTRUCT:
        # Refund address = action.refundAddress
        # Sent value = action.balance
        selfdestruct_action: SelfDestructAction = root.action  # type: ignore
        node_kwargs = {
            **node_kwargs,
            "address": selfdestruct_action.address,
            "gas_limit": 0,  # No field
            "gas_cost": 0,  # No field
        }

    node_kwargs["calls"] = []
    sub_trees = [
        sub
        for sub in traces
        if len(sub.trace_address) == len(root.trace_address) + 1
        and sub.trace_address[:-1] == root.trace_address
    ]
    node_kwargs["calls"] = [get_calltree_from_parity_trace(sub, traces) for sub in sub_trees]
    node = CallTreeNode.parse_obj(node_kwargs)
    return node
