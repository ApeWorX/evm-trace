from typing import Any, Dict, List

from hexbytes import HexBytes
from pydantic import BaseModel, Field, validator


class TraceFrame(BaseModel):
    pc: int
    op: str
    gas: int
    gas_cost: int = Field(alias="gasCost")
    depth: int
    stack: List[Any]
    memory: List[Any]
    storage: Dict[Any, Any]


@validator("stack", "memory", pre=True, each_item=True)
def validate_hexbytes(value: Any) -> HexBytes:
    if value and not isinstance(value, HexBytes):
        raise ValueError(f"Hash `{value}` is not a valid Hexbyte.")
    return value


@validator("storage")
def validate_hexbytes_dict(value: Any) -> Dict[HexBytes, HexBytes]:
    for k, v in value:
        if k and not isinstance(k, HexBytes):
            raise ValueError(f"Key `{value}` is not a valid Hexbyte.")
        if v and not isinstance(v, HexBytes):
            raise ValueError(f"Value `{value}` is not a valid Hexbyte.")
    return value
