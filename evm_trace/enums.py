from enum import Enum


class CallType(Enum):
    CALL = "CALL"
    CALLCODE = "CALLCODE"
    CREATE = "CREATE"
    CREATE2 = "CREATE2"
    DELEGATECALL = "DELEGATECALL"
    EVENT = "EVENT"
    INTERNAL = "INTERNAL"  # Non-opcode internal call
    SELFDESTRUCT = "SELFDESTRUCT"
    STATICCALL = "STATICCALL"

    def __eq__(self, other):
        return self.value == getattr(other, "value", other)

    def __hash__(self) -> int:
        return hash(self.value)


CALL_OPCODES = (
    CallType.CALL,
    CallType.CALLCODE,
    CallType.CREATE,
    CallType.CREATE2,
    CallType.DELEGATECALL,
    CallType.STATICCALL,
)
