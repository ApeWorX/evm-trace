from enum import Enum
from typing import Any, Dict, List

from hexbytes import HexBytes
from pydantic import BaseModel, Field, ValidationError, validator


def _convert_hexbytes(cls, v: Any) -> HexBytes:
    try:
        return HexBytes(v)
    except ValueError:
        raise ValidationError(f"Value '{v}' could not be converted to Hexbytes.", cls)


class TraceFrame(BaseModel):
    pc: int
    op: str
    gas: int
    gas_cost: int = Field(alias="gasCost")
    depth: int
    stack: List[Any]
    memory: List[Any]
    storage: Dict[Any, Any] = {}

    @validator("stack", "memory", pre=True, each_item=True)
    def convert_hexbytes(cls, v) -> HexBytes:
        return _convert_hexbytes(cls, v)

    @validator("storage", pre=True)
    def convert_hexbytes_dict(cls, v) -> Dict[HexBytes, HexBytes]:
        return {_convert_hexbytes(cls, k): _convert_hexbytes(cls, val) for k, val in v.items()}


class CallType(Enum):
    INTERNAL = "INTERNAL"  # Non-opcode internal call
    STATIC = "STATIC"  # STATICCALL opcode
    MUTABLE = "MUTABLE"  # CALL opcode
    DELEGATE = "DELEGATE"  # DELEGATECALL opcode
    SELFDESTRUCT = "SELFDESTRUCT"  # SELFDESTRUCT opcode


class CallTreeNode(BaseModel):
    call_type: CallType
    address: Any
    value: int = 0
    gas_limit: int
    gas_cost: int  # calculated from call starting and return
    calldata: Any = HexBytes(b"")
    returndata: Any = HexBytes(b"")
    calls: List["CallTreeNode"] = []
    selfdestruct: bool = False
    failed: bool = False

    @validator("address", "calldata", "returndata", pre=True)
    def validate_hexbytes(cls, v) -> HexBytes:
        return _convert_hexbytes(cls, v)
