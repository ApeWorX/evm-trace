from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field, validator

from evm_trace.base import CallTreeNode, CallType
from evm_trace.display import DisplayableCallTreeNode


class CallAction(BaseModel):
    gas: int
    input: Optional[str] = None
    receiver: Optional[str] = Field(alias="to", default=None)
    sender: str = Field(alias="from")
    value: int
    # only used to recover the specific call type
    call_type: str = Field(alias="callType", repr=False)

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
    balance: int

    @validator("balance", pre=True)
    def convert_integer(cls, v):
        return int(v, 16)


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
    def convert_call_type(cls, v, values) -> CallType:
        if isinstance(values["action"], CallAction):
            v = values["action"].call_type
        value = v.upper()
        if value == "SUICIDE":
            value = "SELFDESTRUCT"

        return CallType(value)


class ParityTraceList(BaseModel):
    __root__: List[ParityTrace]

    # pydantic models with custom root don't have this by default
    def __iter__(self):
        return iter(self.__root__)

    def __getitem__(self, item):
        return self.__root__[item]


def get_calltree_from_parity_trace(
    traces: ParityTraceList,
    root: Optional[ParityTrace] = None,
    display_cls: Type[DisplayableCallTreeNode] = DisplayableCallTreeNode,
    **root_kwargs,
) -> CallTreeNode:
    """
    Create a :class:`~evm_trace.base.CallTreeNode` from output models using the Parity approach
    (e.g. from the ``trace_transaction`` RPC).

    Args:
        traces (List[:class:~evm_trace.parity.ParityTraceList]): The list of parity trace nodes,
          likely loaded from the response data from the ``trace_transaction`` RPC response.
        root (:class:`~evm_trace.parity.ParityTrace`): The root parity trace node. Optional, uses
          the first item by default.
        display_cls (Type[DisplayableCallTreeNode]]: A custom class to use for representing
          the call tree. Defaults to :class:`~evm_trace.display.DisplayableCallTreeNode`.
        **root_kwargs: Additional kwargs to append to the root node. Useful for adding gas for
          reverted calls.

    Returns:
        :class:`~evm_trace.base.CallTreeNode`
    """
    root = root or traces[0]
    failed = root.error is not None
    node_kwargs: Dict[Any, Any] = dict(
        call_type=root.call_type,
        failed=failed,
        display_cls=display_cls,
        **root_kwargs,
    )

    if root.call_type == CallType.CREATE:
        create_action: CreateAction = root.action  # type: ignore
        create_result: CreateResult = root.result  # type: ignore

        node_kwargs.update(
            value=create_action.value,
            gas_limit=create_action.gas,
        )
        if create_result:
            node_kwargs.update(gas_used=create_result.gas_used, address=create_result.address)

    elif root.call_type in (
        CallType.CALL,
        CallType.DELEGATECALL,
        CallType.STATICCALL,
        CallType.CALLCODE,
    ):
        call_action: CallAction = root.action  # type: ignore
        call_result: CallResult = root.result  # type: ignore

        node_kwargs.update(
            address=call_action.receiver,
            value=call_action.value,
            gas_limit=call_action.gas,
            calldata=call_action.input,
        )
        # no result if the call has an error
        if call_result:
            node_kwargs.update(
                gas_cost=call_result.gas_used,
                returndata=call_result.output,
            )

    elif root.call_type == CallType.SELFDESTRUCT:
        selfdestruct_action: SelfDestructAction = root.action  # type: ignore
        node_kwargs.update(
            address=selfdestruct_action.address,
        )

    subtraces = [
        sub
        for sub in traces
        if len(sub.trace_address) == len(root.trace_address) + 1
        and sub.trace_address[:-1] == root.trace_address
    ]
    node_kwargs["calls"] = [get_calltree_from_parity_trace(traces, root=sub) for sub in subtraces]
    node = CallTreeNode.parse_obj(node_kwargs)
    return node
