from enum import Enum


class CallType(Enum):
    INTERNAL = "INTERNAL"  # Non-opcode internal call
    CREATE = "CREATE"
    CREATE2 = "CREATE2"
    CALL = "CALL"
    DELEGATECALL = "DELEGATECALL"
    STATICCALL = "STATICCALL"
    CALLCODE = "CALLCODE"
    SELFDESTRUCT = "SELFDESTRUCT"

    def __eq__(self, other):
        return self.value == getattr(other, "value", other)

    def __hash__(self) -> int:
        return hash(self.value)


CALL_OPCODES = (CallType.CALL, CallType.CALLCODE, CallType.DELEGATECALL, CallType.STATICCALL)
