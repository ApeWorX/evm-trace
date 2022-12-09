from typing import List, Optional

from ethpm_types import BaseModel, HexBytes
from pydantic import validator

from evm_trace.display import get_tree_display
from evm_trace.enums import CallType


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

    @validator("calldata", "returndata", "address", pre=True)
    def validate_bytes(cls, value):
        return HexBytes(value) if isinstance(value, str) else value

    @validator("value", "depth", pre=True)
    def validate_ints(cls, value):
        if not value:
            return 0

        return int(value, 16) if isinstance(value, str) else value

    @validator("gas_limit", "gas_cost", pre=True)
    def validate_optional_ints(cls, value):
        return int(value, 16) if isinstance(value, str) else value
