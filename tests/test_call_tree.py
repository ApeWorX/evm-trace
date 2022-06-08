import pytest

from evm_trace import CallTreeNode

EXPECTED_TREE_REPR = """
CALL: 0xF2Df0b975c0C9eFa2f8CA0491C2d1685104d2488 [194827 gas]
├── CALL: 0xBcF7FFFD8B256Ec51a36782a52D0c34f6474D951.<0x61d22ffe> [168423 gas]
│   └── CALL: 0x274b028b03A250cA03644E6c578D81f019eE1323.<0x8f27163e> [160842 gas]
├── CALL: 0xBcF7FFFD8B256Ec51a36782a52D0c34f6474D951.<0x61d22ffe> [116942 gas]
│   └── CALL: 0x274b028b03A250cA03644E6c578D81f019eE1323.<0x8f27163e> [114595 gas]
└── CALL: 0xBcF7FFFD8B256Ec51a36782a52D0c34f6474D951.<0xb9e5b20a> [93421 gas]
    ├── CALL: 0x274b028b03A250cA03644E6c578D81f019eE1323.<0x8f27163e> [91277 gas]
    ├── CALL: 0x274b028b03A250cA03644E6c578D81f019eE1323.<0x90bb7141> [46476 gas]
    └── CALL: 0x274b028b03A250cA03644E6c578D81f019eE1323.<0x90bb7141> [23491 gas]
""".strip()


@pytest.fixture(scope="session")
def call_tree(call_tree_data):
    return CallTreeNode(**call_tree_data)


def test_call_tree_validation_passes(call_tree_data):
    tree = CallTreeNode(**call_tree_data)
    assert tree


def test_call_tree_representation(call_tree):
    actual = repr(call_tree)
    assert actual == EXPECTED_TREE_REPR
