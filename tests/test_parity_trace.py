import json
from glob import glob
from pathlib import Path

import pytest

from evm_trace.parity import ParityTrace, get_calltree_from_parity_trace

DATA_PATH = Path(__file__).parent / "data" / "parity"
PARITY_TRACE_FILE_NAMES = [Path(p).name for p in glob(str(DATA_PATH / "trace*.json"))]


@pytest.mark.parametrize("name", PARITY_TRACE_FILE_NAMES)
def test_parity_trace_frame_models(name):
    file_path = DATA_PATH / name
    trace_data = json.loads(file_path.read_text())
    models = [ParityTrace.parse_obj(d) for d in trace_data]
    assert len(models) == len(trace_data)


@pytest.mark.parametrize("name", glob("tests/data/parity/trace*.json"))
def test_parity_trace(name):
    traces = json.load(open(name))
    print(len(traces))
    tree = get_calltree_from_parity_trace(traces[0], traces)
    print(tree)
