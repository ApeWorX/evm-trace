from enum import Enum


class CallType(Enum):
    INTERNAL = "INTERNAL"  # Non-opcode internal call
    CREATE = "CREATE"
    CALL = "CALL"
    DELEGATECALL = "DELEGATECALL"
    STATICCALL = "STATICCALL"
    CALLCODE = "CALLCODE"
    SELFDESTRUCT = "SELFDESTRUCT"
