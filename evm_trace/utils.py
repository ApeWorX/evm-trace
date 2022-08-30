from typing import Any

from hexbytes import HexBytes
from pydantic import ValidationError


def _convert_hexbytes(cls, v: Any) -> HexBytes:
    try:
        return HexBytes(v)
    except ValueError:
        raise ValidationError(f"Value '{v}' could not be converted to Hexbytes.", cls)
