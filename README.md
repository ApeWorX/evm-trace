# Quick Start

Ethereum Virtual Machine transaction tracing tool

## Dependencies

- [python3](https://www.python.org/downloads) version 3.8 to 3.11.

## Installation

### via `pip`

You can install the latest release via [`pip`](https://pypi.org/project/pip/):

```bash
pip install evm-trace
```

### via `setuptools`

You can clone the repository and use [`setuptools`](https://github.com/pypa/setuptools) for the most up-to-date version:

```bash
git clone https://github.com/ApeWorX/evm-trace.git
cd evm-trace
python3 setup.py install
```

## Quick Usage

### Geth Style Traces

If you are using a node that supports the `debug_traceTransaction` RPC, you can use `web3.py` to get trace frames:

```python
from web3 import HTTPProvider, Web3
from evm_trace import TraceFrame

web3 = Web3(HTTPProvider("https://path.to.my.node"))
txn_hash = "0x..."
struct_logs = web3.manager.request_blocking("debug_traceTransaction", [txn_hash]).structLogs
for item in struct_logs:
    frame = TraceFrame.parse_obj(item)
```

If you want to get the call-tree node, you can do:

```python
from evm_trace import CallType, get_calltree_from_geth_trace

root_node_kwargs = {
    "gas_cost": 10000000,
    "gas_limit": 10000000000,
    "address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    "calldata": "0x00",
    "value": 1000,
    "call_type": CallType.CALL,
}

# Where `trace` is a `TraceFrame` (see example above)
calltree = get_calltree_from_geth_trace(trace, **root_node_kwargs)
```

### Parity Style Traces

If you are using a node that supports the `trace_transaction` RPC, you can use `web3.py` to get trace objects:

```python
from evm_trace import CallType, ParityTraceList

raw_trace_list = web3.manager.request_blocking("trace_transaction", [txn_hash])
trace_list = ParityTraceList.parse_obj(raw_trace_list)
```

And to make call-tree nodes, you can do:

```python
from evm_trace import get_calltree_from_parity_trace

tree = get_calltree_from_parity_trace(trace_list)
```

### Gas Reports

If you are using a node that supports creating traces, you can get a gas report.

```python
from evm_trace.gas import get_gas_report

# see examples above for creating a calltree
calltree = get_calltree_from_geth_trace(trace, **root_node_kwargs)

gas_report = get_gas_report(calltree)
```

For a more custom report, use the `merge_reports` method to combine a list of reports into a single report.
Pass two or more `Dict[Any, Dict[Any, List[int]]]` to combine reports where `List[int]` is the gas used.

Customize the values of `Any` accordingly:

1. The first `Any` represents the bytes from the address.
2. The second `Any` represents the method selector.

For example, you may replace addresses with token names or selector bytes with signature call strings.

Import the method like so:

```python
from evm_trace.gas import merge_reports
```

## Development

This project is in development and should be considered a beta.
Things might not be in their final state and breaking changes may occur.
Comments, questions, criticisms and pull requests are welcomed.

## License

This project is licensed under the [Apache 2.0](LICENSE).
