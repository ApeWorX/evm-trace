# evm-trace

Ethereum Virtual Machine transaction tracing tool

## Dependencies

* [python3](https://www.python.org/downloads) version 3.7.2 or greater, python3-dev

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
struct_logs = web3.manager.request_blocking("debug_traceTransaction", [txn_hash]).structLogs
for item in struct_logs:
    yield TraceFrame(**item)
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

### Call Tree Node Customization

You can also customize the output by making your own display class:

```python
from evm_trace.display import DisplayableCallTreeNode, get_calltree_from_trace


class CustomDisplay(DisplayableCallTreeNode):
    def title(self) -> str:
        call_type = self.call.call_type.value.lower().capitalize()
        address = self.call.address.hex()
        cost = self.call.gas_cost
        return f"{call_type} call @ {address} gas_cost={cost}"


calltree = get_calltree_from_geth_trace(trace, display_cls=CustomDisplay)
```

## Development

This project is in development and should be considered a beta.
Things might not be in their final state and breaking changes may occur.
Comments, questions, criticisms and pull requests are welcomed.

## License

This project is licensed under the [Apache 2.0](LICENSE).
