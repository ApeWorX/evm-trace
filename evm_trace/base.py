from functools import cached_property, singledispatchmethod
from typing import List, Optional

from eth_pydantic_types import HexBytes
from pydantic import BaseModel as _BaseModel
from pydantic import ConfigDict, field_validator

from evm_trace.display import get_tree_display
from evm_trace.enums import CallType


class BaseModel(_BaseModel):
    model_config = ConfigDict(
        ignored_types=(cached_property, singledispatchmethod),
        arbitrary_types_allowed=True,
    )


class CallTreeNode(BaseModel):
    """
    A higher-level object modeling a node in an execution call tree.
    Used by both Geth-style and Parity-style low-level data structures.
    """

    call_type: CallType
    """The type of call."""

    address: HexBytes = HexBytes("")
    """The contract address of the call."""

    value: int = 0
    """The amount of value sent on the call."""

    depth: int = 0
    """
    The number of external jumps away the initially called contract (starts at 0).
    """

    gas_limit: Optional[int] = None
    """
    The total amount of gas available.
    """

    gas_cost: Optional[int] = None  # calculated from call starting and return
    """The cost to execute this opcode."""

    calldata: HexBytes = HexBytes("")
    """Transaction calldata (inputs)."""

    returndata: HexBytes = HexBytes("")
    """Transaction returndata (outputs)."""

    calls: List["CallTreeNode"] = []
    """The list of external sub-calls this call makes."""

    selfdestruct: bool = False
    """Whether this is a SELFDESTRUCT opcode or not."""

    failed: bool = False
    """Whether the call failed or not."""

    def __str__(self) -> str:
        try:
            return get_tree_display(self)
        except Exception as err:
            return f"CallTreeNode (display_err={err})"

    def __repr__(self) -> str:
        return str(self)

    def __getitem__(self, index: int) -> "CallTreeNode":
        return self.calls[index]

    @field_validator("calldata", "returndata", "address", mode="before")
    def validate_bytes(cls, value):
        return HexBytes(value) if isinstance(value, str) else value

    @field_validator("value", "depth", mode="before")
    def validate_ints(cls, value):
        return (int(value, 16) if isinstance(value, str) else value) if value else 0

    @field_validator("gas_limit", "gas_cost", mode="before")
    def validate_optional_ints(cls, value):
        return int(value, 16) if isinstance(value, str) else value
