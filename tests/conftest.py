import pytest
from hexbytes import HexBytes

from evm_trace.enums import CallType

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
CALL_FRAME_DATA = {
    "pc": 359,
    "op": "CALL",
    "gas": 29971782,
    "gasCost": 22369,
    "depth": 1,
    "stack": [
        "0xf552a8b8",
        "0x274b028b03a250ca03644e6c578d81f019ee1323",
        "0x00",
        "0x60",
        "0x24",
        "0x7c",
        "0x00",
        "0x274b028b03a250ca03644e6c578d81f019ee1323",
        "0x01c95546",
    ],
    "memory": [
        "0x0000000000000000000000000000000000000000000000000000000000000000",
        "0x0000000000000000000000000000000000000000000000000000000000000000",
        "0x0000000000000000000000000000000000000000000000000000000000000000",
        "0x000000000000000000000000000000000000000000000000000000004420e486",
        "0x0000000000000000000000001e59ce931b4cfea3fe4b875411e280e173cb7a9c",
    ],
    "storage": {},
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
GETH_CALL_TRACE_DATA = {
    "type": "CALL",
    "from": "0x1e59ce931b4cfea3fe4b875411e280e173cb7a9c",
    "to": "0xf2df0b975c0c9efa2f8ca0491c2d1685104d2488",
    "value": "0x7b",
    "gas": "0x47cb6e",
    "gasUsed": "0x445e6",
    "input": "0x372dca07",
    "output": "0x000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000200000000000000000000000001e59ce931b4cfea3fe4b875411e280e173cb7a9c",  # noqa: E501
    "calls": [
        {
            "type": "CALL",
            "from": "0xf2df0b975c0c9efa2f8ca0491c2d1685104d2488",
            "to": "0xbcf7fffd8b256ec51a36782a52d0c34f6474d951",
            "value": "0x0",
            "gas": "0x4697e7",
            "gasUsed": "0x84d4",
            "input": "0x045856de00000000000000000000000000000000000000000000000000000000000393cc",
            "output": "0x00000000000000000000000000000000000000000000000000001564ff3f0da300000000000000000000000000000000000000000000000000000002964619c700000000000000000000000000000000000000000000000000000000000393cc00000000000000000000000000000000000000000000000004cae9c39bdb4f7700000000000000000000000000000000000000000000000000005af310694bb20000000000000000000000000000000000000000011dc18b6f8f1601b7b1b33100000000000000000000000000000000000000000000000000000000000393cc000000000000000000000000000000000000000000000004ffd72d92184e6bb20000000000000000000000000000000000000000000000000000000000000d7e000000000000000000000000000000000000000000000006067396b875234f7700000000000000000000000000000000000000000000000000012f39bc807bb20000000000000000000000000000000000000002f5db749b3db467538fb1b331",  # noqa: E501
        },
        {
            "type": "CALL",
            "from": "0xf2df0b975c0c9efa2f8ca0491c2d1685104d2488",
            "to": "0xbcf7fffd8b256ec51a36782a52d0c34f6474d951",
            "value": "0x0",
            "gas": "0x45fb34",
            "gasUsed": "0xf3eb",
            "input": "0xbeed0f8500000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000011dc18b6f8f1601b7b1b33100000000000000000000000000000000000000000000000000000000000000096963652d637265616d0000000000000000000000000000000000000000000000",  # noqa: E501
            "output": "0x",
            "calls": [
                {
                    "type": "STATICCALL",
                    "from": "0xbcf7fffd8b256ec51a36782a52d0c34f6474d951",
                    "to": "0x274b028b03a250ca03644e6c578d81f019ee1323",
                    "gas": "0x44b63f",
                    "gasUsed": "0x5d9",
                    "input": "0x7007cbe8",
                    "output": "0x000000000000000000000000000000000293b0e3558d33b8a4c483e40e2b8db9000000000000000000000000000000000000000000000000018b932eebcc7eb90000000000000000000000000000000000bf550935e92f79f09e3530df8660c5",  # noqa: E501
                },
                {
                    "type": "CALL",
                    "from": "0xbcf7fffd8b256ec51a36782a52d0c34f6474d951",
                    "to": "0x274b028b03a250ca03644e6c578d81f019ee1323",
                    "value": "0x0",
                    "gas": "0x44a772",
                    "gasUsed": "0xa1f2",
                    "input": "0x878fb70100000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000011dc18b6f8f1601b7b1b331000000000000000000000000f2df0b975c0c9efa2f8ca0491c2d1685104d2488000000000000000000000000000000000000000000000000000000000000000773696d706c657200000000000000000000000000000000000000000000000000",  # noqa: E501
                    "output": "0x",
                },
            ],
        },
        {
            "type": "CALL",
            "from": "0xf2df0b975c0c9efa2f8ca0491c2d1685104d2488",
            "to": "0xbcf7fffd8b256ec51a36782a52d0c34f6474d951",
            "value": "0x0",
            "gas": "0x4506ef",
            "gasUsed": "0x2d3",
            "input": "0xb27b88040000000000000000000000001e59ce931b4cfea3fe4b875411e280e173cb7a9c",
            "output": "0x0000000000000000000000001e59ce931b4cfea3fe4b875411e280e173cb7a9c",
        },
        {
            "type": "CALL",
            "from": "0xf2df0b975c0c9efa2f8ca0491c2d1685104d2488",
            "to": "0xbcf7fffd8b256ec51a36782a52d0c34f6474d951",
            "value": "0x0",
            "gas": "0x450126",
            "gasUsed": "0x165ab",
            "input": "0xb9e5b20a0000000000000000000000001e59ce931b4cfea3fe4b875411e280e173cb7a9c",
            "output": "0x",
            "calls": [
                {
                    "type": "STATICCALL",
                    "from": "0xbcf7fffd8b256ec51a36782a52d0c34f6474d951",
                    "to": "0x274b028b03a250ca03644e6c578d81f019ee1323",
                    "gas": "0x43e944",
                    "gasUsed": "0x947",
                    "input": "0xe5e1d93f000000000000000000000000f2df0b975c0c9efa2f8ca0491c2d1685104d2488",  # noqa: E501
                    "output": "0x00000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000011dc18b6f8f1601b7b1b331000000000000000000000000f2df0b975c0c9efa2f8ca0491c2d1685104d2488000000000000000000000000000000000000000000000000000000000000000773696d706c657200000000000000000000000000000000000000000000000000",  # noqa: E501
                },
                {
                    "type": "CALL",
                    "from": "0xbcf7fffd8b256ec51a36782a52d0c34f6474d951",
                    "to": "0x274b028b03a250ca03644e6c578d81f019ee1323",
                    "value": "0x0",
                    "gas": "0x43d5bd",
                    "gasUsed": "0x8442",
                    "input": "0x878fb70100000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000274b028b03a250ca03644e6c578d81f019ee1323000000000000000000000000000000000000000000000000000000000000000773696d706c657200000000000000000000000000000000000000000000000000",  # noqa: E501
                    "output": "0x",
                },
                {
                    "type": "CALL",
                    "from": "0xbcf7fffd8b256ec51a36782a52d0c34f6474d951",
                    "to": "0x274b028b03a250ca03644e6c578d81f019ee1323",
                    "value": "0x0",
                    "gas": "0x4348e6",
                    "gasUsed": "0x6253",
                    "input": "0x90bb7141",
                    "output": "0x",
                },
                {
                    "type": "CALL",
                    "from": "0xbcf7fffd8b256ec51a36782a52d0c34f6474d951",
                    "to": "0x274b028b03a250ca03644e6c578d81f019ee1323",
                    "value": "0x0",
                    "gas": "0x42e652",
                    "gasUsed": "0x5a83",
                    "input": "0x90bb7141",
                    "output": "0x",
                },
            ],
        },
        {
            "type": "STATICCALL",
            "from": "0xf2df0b975c0c9efa2f8ca0491c2d1685104d2488",
            "to": "0x274b028b03a250ca03644e6c578d81f019ee1323",
            "gas": "0x439750",
            "gasUsed": "0xafe",
            "input": "0xbff2e0950000000000000000000000001e59ce931b4cfea3fe4b875411e280e173cb7a9c",
            "output": "0x0000000000000000000000000000000000000000000000000000000000000000",
        },
        {
            "type": "STATICCALL",
            "from": "0xf2df0b975c0c9efa2f8ca0491c2d1685104d2488",
            "to": "0xbcf7fffd8b256ec51a36782a52d0c34f6474d951",
            "gas": "0x437fe8",
            "gasUsed": "0x35b",
            "input": "0x9155fd570000000000000000000000001e59ce931b4cfea3fe4b875411e280e173cb7a9c",
            "output": "0x0000000000000000000000000000000000000000000000000000000000000000",
        },
        {
            "type": "CALL",
            "from": "0xf2df0b975c0c9efa2f8ca0491c2d1685104d2488",
            "to": "0xbcf7fffd8b256ec51a36782a52d0c34f6474d951",
            "value": "0x0",
            "gas": "0x43784b",
            "gasUsed": "0x7f83",
            "input": "0xbeed0f850000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000096c656d6f6e64726f700000000000000000000000000000000000000000000000",  # noqa: E501
            "output": "0x",
            "calls": [
                {
                    "type": "STATICCALL",
                    "from": "0xbcf7fffd8b256ec51a36782a52d0c34f6474d951",
                    "to": "0x274b028b03a250ca03644e6c578d81f019ee1323",
                    "gas": "0x426124",
                    "gasUsed": "0x5d9",
                    "input": "0x7007cbe8",
                    "output": "0x000000000000000000000000000000000293b0e3558d33b8a4c483e40e2b8db9000000000000000000000000000000000000000000000000018b932eebcc7eb90000000000000000000000000000000000bf550935e92f79f09e3530df8660c5",  # noqa: E501
                },
                {
                    "type": "CALL",
                    "from": "0xbcf7fffd8b256ec51a36782a52d0c34f6474d951",
                    "to": "0x274b028b03a250ca03644e6c578d81f019ee1323",
                    "value": "0x0",
                    "gas": "0x425257",
                    "gasUsed": "0x649e",
                    "input": "0x878fb70100000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000f2df0b975c0c9efa2f8ca0491c2d1685104d2488000000000000000000000000000000000000000000000000000000000000000773696d706c657200000000000000000000000000000000000000000000000000",  # noqa: E501
                    "output": "0x",
                },
            ],
        },
        {
            "type": "CALL",
            "from": "0xf2df0b975c0c9efa2f8ca0491c2d1685104d2488",
            "to": "0xbcf7fffd8b256ec51a36782a52d0c34f6474d951",
            "value": "0x0",
            "gas": "0x42f728",
            "gasUsed": "0x7f83",
            "input": "0xbeed0f850000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000006f0000000000000000000000000000000000000000000000000000000000000014736e6974636865735f6765745f73746963686573000000000000000000000000",  # noqa: E501
            "output": "0x",
            "calls": [
                {
                    "type": "STATICCALL",
                    "from": "0xbcf7fffd8b256ec51a36782a52d0c34f6474d951",
                    "to": "0x274b028b03a250ca03644e6c578d81f019ee1323",
                    "gas": "0x41e206",
                    "gasUsed": "0x5d9",
                    "input": "0x7007cbe8",
                    "output": "0x000000000000000000000000000000000293b0e3558d33b8a4c483e40e2b8db9000000000000000000000000000000000000000000000000018b932eebcc7eb90000000000000000000000000000000000bf550935e92f79f09e3530df8660c5",  # noqa: E501
                },
                {
                    "type": "CALL",
                    "from": "0xbcf7fffd8b256ec51a36782a52d0c34f6474d951",
                    "to": "0x274b028b03a250ca03644e6c578d81f019ee1323",
                    "value": "0x0",
                    "gas": "0x41d339",
                    "gasUsed": "0x649e",
                    "input": "0x878fb7010000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000006f000000000000000000000000f2df0b975c0c9efa2f8ca0491c2d1685104d2488000000000000000000000000000000000000000000000000000000000000000773696d706c657200000000000000000000000000000000000000000000000000",  # noqa: E501
                    "output": "0x",
                },
            ],
        },
    ],
}
CALL_TREE_DATA_MAP = {
    CallType.CALL.value: MUTABLE_CALL_TREE_DATA,
    CallType.STATICCALL.value: STATIC_CALL_TREE_DATA,
    CallType.DELEGATECALL.value: DELEGATE_CALL_TREE_DATA,
}


@pytest.fixture(scope="session")
def trace_frame_data():
    return TRACE_FRAME_DATA


@pytest.fixture(scope="session")
def call_frame_data():
    return CALL_FRAME_DATA


@pytest.fixture(scope="session")
def geth_call_trace_data():
    return GETH_CALL_TRACE_DATA


@pytest.fixture(
    scope="session",
    params=(CallType.CALL.value, CallType.DELEGATECALL.value, CallType.STATICCALL.value),
)
def call_tree_data(request):
    yield CALL_TREE_DATA_MAP[request.param]
