import json
from glob import glob

import pytest

from evm_trace.base import create_node_from_parity_trace


@pytest.mark.parametrize("name", glob("tests/parity/trace*.json"))
def test_parity_trace(name):
    traces = json.load(open(name))
    print(len(traces))
    tree = create_node_from_parity_trace(traces[0], traces)
    print(tree)
