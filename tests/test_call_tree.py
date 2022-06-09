import pytest

from evm_trace import CallTreeNode
from evm_trace.base import CallType

MUTABLE_REPR = """
CALL: 0xF2Df0b975c0C9eFa2f8CA0491C2d1685104d2488 [194827 gas]
├── CALL: 0xBcF7FFFD8B256Ec51a36782a52D0c34f6474D951.<0x61d22ffe> [168423 gas]
│   └── CALL: 0x274b028b03A250cA03644E6c578D81f019eE1323.<0x8f27163e> [160842 gas]
├── CALL: 0xBcF7FFFD8B256Ec51a36782a52D0c34f6474D951.<0x61d22ffe> [116942 gas]
│   └── CALL: 0x274b028b03A250cA03644E6c578D81f019eE1323.<0x8f27163e> [114595 gas]
└── CALL: 0xBcF7FFFD8B256Ec51a36782a52D0c34f6474D951.<0xb9e5b20a> [93421 gas]
    ├── CALL: 0x274b028b03A250cA03644E6c578D81f019eE1323.<0x8f27163e> [91277 gas]
    ├── CALL: 0x274b028b03A250cA03644E6c578D81f019eE1323.<0x90bb7141> [46476 gas]
    └── CALL: 0x274b028b03A250cA03644E6c578D81f019eE1323.<0x90bb7141> [23491 gas]
"""
STATIC_REPR = "STATICCALL: 0x274b028b03A250cA03644E6c578D81f019eE1323.<0x7007cbe8> [369688 gas]"
DELEGATECALL_REPR = (
    "DELEGATECALL: 0xaa1A02671440Be41545D83BDDfF2bf2488628C10.<0x70a08231> [161021 gas]"
)
REPR_MAP = {
    CallType.MUTABLE: MUTABLE_REPR,
    CallType.STATIC: STATIC_REPR,
    CallType.DELEGATE: DELEGATECALL_REPR,
}


@pytest.fixture(scope="session")
def call_tree(call_tree_data):
    return CallTreeNode(**call_tree_data)


def test_call_tree_validation_passes(call_tree_data):
    tree = CallTreeNode(**call_tree_data)
    assert tree


def test_call_tree_mutable_representation(call_tree):
    expected = REPR_MAP[call_tree.call_type].strip()
    assert repr(call_tree) == expected
