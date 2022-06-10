import pytest
from hexbytes import HexBytes

from evm_trace.base import CallType

TRACE_FRAME_DATA = {
    "pc": 1564,
    "op": "RETURN",
    "gas": 0,
    "gasCost": 0,
    "depth": 1,
    "callType": CallType.CALL.value,
    "stack": [
        "0000000000000000000000000000000000000000000000000000000040c10f19",
        "0000000000000000000000000000000000000000000000000000000000000020",
        "0000000000000000000000000000000000000000000000000000000000000140",
    ],
    "memory": [
        "0000000000000000000000001e59ce931b4cfea3fe4b875411e280e173cb7a9c",
        "0000000000000000000000000000000000000000000000000000000000000001",
    ],
    "storage": {
        "0000000000000000000000000000000000000000000000000000000000000004": "0000000000000000000000001e59ce931b4cfea3fe4b875411e280e173cb7a9c",  # noqa: E501
        "ad3228b676f7d3cd4284a5443f17f1962b36e491b30a40b2405849e597ba5fb5": "0000000000000000000000001e59ce931b4cfea3fe4b875411e280e173cb7a9c",  # noqa: E501
        "aadb61a4b4c5d48b7a5669391b7c73852a3ab7795f24721b9a439220b54b591b": "0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
    },
}
MUTABLE_CALL_TREE_DATA = {
    "call_type": CallType.CALL,
    "address": HexBytes("0xf2df0b975c0c9efa2f8ca0491c2d1685104d2488"),
    "value": 0,
    "depth": 0,
    "gas_limit": 197110,
    "gas_cost": 194827,
    "calldata": HexBytes("0x"),
    "returndata": HexBytes("0x"),
    "calls": [
        {
            "call_type": CallType.CALL,
            "address": HexBytes("0xbcf7fffd8b256ec51a36782a52d0c34f6474d951"),
            "value": 0,
            "depth": 1,
            "gas_limit": 171094,
            "gas_cost": 168423,
            "calldata": HexBytes("0x61d22ffe"),
            "returndata": HexBytes("0x"),
            "calls": [
                {
                    "call_type": CallType.CALL,
                    "address": HexBytes("0x274b028b03a250ca03644e6c578d81f019ee1323"),
                    "value": 0,
                    "depth": 2,
                    "gas_limit": 163393,
                    "gas_cost": 160842,
                    "calldata": HexBytes("0x8f27163e"),
                    "returndata": HexBytes("0x"),
                    "calls": [],
                    "selfdestruct": False,
                    "failed": False,
                    "displays_last": True,
                }
            ],
            "selfdestruct": False,
            "failed": False,
            "displays_last": False,
        },
        {
            "call_type": CallType.CALL,
            "address": HexBytes("0xbcf7fffd8b256ec51a36782a52d0c34f6474d951"),
            "value": 0,
            "depth": 1,
            "gas_limit": 118796,
            "gas_cost": 116942,
            "calldata": HexBytes("0x61d22ffe"),
            "returndata": HexBytes("0x"),
            "calls": [
                {
                    "call_type": CallType.CALL,
                    "address": HexBytes("0x274b028b03a250ca03644e6c578d81f019ee1323"),
                    "value": 0,
                    "depth": 2,
                    "gas_limit": 116412,
                    "gas_cost": 114595,
                    "calldata": HexBytes("0x8f27163e"),
                    "returndata": HexBytes("0x"),
                    "calls": [],
                    "selfdestruct": False,
                    "failed": False,
                    "displays_last": True,
                }
            ],
            "selfdestruct": False,
            "failed": False,
            "displays_last": False,
        },
        {
            "call_type": CallType.CALL,
            "address": HexBytes("0xbcf7fffd8b256ec51a36782a52d0c34f6474d951"),
            "value": 0,
            "depth": 1,
            "gas_limit": 94902,
            "gas_cost": 93421,
            "calldata": HexBytes(
                "0xb9e5b20a0000000000000000000000001e59ce931b4cfea3fe4b875411e280e173cb7a9c"
            ),
            "returndata": HexBytes("0x"),
            "calls": [
                {
                    "call_type": CallType.CALL,
                    "address": HexBytes("0x274b028b03a250ca03644e6c578d81f019ee1323"),
                    "value": 0,
                    "depth": 2,
                    "gas_limit": 92724,
                    "gas_cost": 91277,
                    "calldata": HexBytes("0x8f27163e"),
                    "returndata": HexBytes("0x"),
                    "calls": [],
                    "selfdestruct": False,
                    "failed": False,
                    "displays_last": False,
                },
                {
                    "call_type": CallType.CALL,
                    "address": HexBytes("0x274b028b03a250ca03644e6c578d81f019ee1323"),
                    "value": 0,
                    "depth": 2,
                    "gas_limit": 47212,
                    "gas_cost": 46476,
                    "calldata": HexBytes("0x90bb7141"),
                    "returndata": HexBytes("0x"),
                    "calls": [],
                    "selfdestruct": False,
                    "failed": False,
                    "displays_last": False,
                },
                {
                    "call_type": CallType.CALL,
                    "address": HexBytes("0x274b028b03a250ca03644e6c578d81f019ee1323"),
                    "value": 0,
                    "depth": 2,
                    "gas_limit": 23862,
                    "gas_cost": 23491,
                    "calldata": HexBytes("0x90bb7141"),
                    "returndata": HexBytes("0x"),
                    "calls": [],
                    "selfdestruct": False,
                    "failed": False,
                    "displays_last": True,
                },
            ],
            "selfdestruct": False,
            "failed": False,
            "displays_last": True,
        },
    ],
    "selfdestruct": False,
    "failed": False,
    "displays_last": True,
}
STATIC_CALL_TREE_DATA = {
    "call_type": CallType.STATICCALL,
    "address": HexBytes("0x274b028b03a250ca03644e6c578d81f019ee1323"),
    "value": 0,
    "depth": 2,
    "gas_limit": 375554,
    "gas_cost": 369688,
    "calldata": HexBytes("0x7007cbe8"),
    "returndata": HexBytes(
        "0x000000000000000000000000000000000293b0e3558d33b8a4c483e40e2b8db9000000000000000000000000000000000000000000000000018b932eebcc7eb90000000000000000000000000000000000bf550935e92f79f09e3530df8660c5"  # noqa: E501
    ),
    "calls": [],
    "selfdestruct": False,
    "failed": False,
}
DELEGATE_CALL_TREE_DATA = {
    "call_type": CallType.DELEGATECALL,
    "address": HexBytes("0xaa1a02671440be41545d83bddff2bf2488628c10"),
    "value": 0,
    "depth": 3,
    "gas_limit": 163575,
    "gas_cost": 161021,
    "calldata": HexBytes(
        "0x70a0823100000000000000000000000077924185cf0cbb2ae0b746a0086a065d6875b0a5"
    ),
    "returndata": HexBytes("0x00000000000000000000000000000000000000000001136eac81315861fd80a7"),
    "calls": [],
    "selfdestruct": False,
    "failed": False,
}
CALL_TREE_DATA_MAP = {
    CallType.CALL.value: MUTABLE_CALL_TREE_DATA,
    CallType.STATICCALL.value: STATIC_CALL_TREE_DATA,
    CallType.DELEGATECALL.value: DELEGATE_CALL_TREE_DATA,
}


@pytest.fixture(scope="session")
def trace_frame_data():
    return TRACE_FRAME_DATA


@pytest.fixture(
    scope="session",
    params=(CallType.CALL.value, CallType.DELEGATECALL.value, CallType.STATICCALL.value),
)
def call_tree_data(request):
    yield CALL_TREE_DATA_MAP[request.param]
