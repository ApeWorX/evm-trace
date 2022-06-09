from enum import Enum


class CallType(Enum):
    INTERNAL = "INTERNAL"  # Non-opcode internal call
    STATIC = "STATIC"  # STATICCALL opcode
    MUTABLE = "MUTABLE"  # CALL opcode
    DELEGATE = "DELEGATE"  # DELEGATECALL opcode
    SELFDESTRUCT = "SELFDESTRUCT"  # SELFDESTRUCT opcode
