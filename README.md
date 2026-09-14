# Quick Start

Ethereum Virtual Machine transaction tracing tool

## Dependencies

- [python3](https://www.python.org/downloads) version 3.9 to 3.12.

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
    frame = TraceFrame.model_validate(item)
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
trace_list = ParityTraceList.model_validate(raw_trace_list)
```

And to make call-tree nodes, you can do:

```python
from evm_trace import get_calltree_from_parity_trace

tree = get_calltree_from_parity_trace(trace_list)
```

### Compressed VM Traces

Some clients support `trace_replayTransaction` with `["vmTrace"]`. This is an opcode trace containing stack and memory deltas, distinct from the Parity call tree above:

```python
from evm_trace.vmtrace import from_rpc_response, to_trace_frames

# response_bytes is the complete JSON-RPC response, encoded as bytes.
vm_trace = from_rpc_response(response_bytes)
for frame in to_trace_frames(vm_trace, address=transaction_to):
    print(frame.pc, frame.op, frame.stack)
```

`op` and `idx` are optional client extensions. The converter can recover opcode names from `code` and `pc`, reconstruct Cancun stack effects and memory expansion, and replay `DUP`, `SWAP`, and `MCOPY` directly. Memory snapshots are taken **before** the current instruction expands or writes memory, matching modern Geth struct logs. This changes the older converter's expansion timing.

Recovered opcode names use Geth spelling (`KECCAK256` for `0x20`, `DIFFICULTY` for `0x44`). The trace does not identify the fork, so `0x44` cannot distinguish pre-Merge difficulty from post-Merge randomness. Explicit names supplied by the client are preserved.

`frame.address` identifies the execution context: `DELEGATECALL` and `CALLCODE` retain their caller's context, while successful CREATE operations use the returned address. Failed creation addresses are unavailable. `copy_memory=False` yields a mutable `memoryview`; consume it immediately.

These synthetic frames do not expose gas/refund/error fields, and `storage` contains only the storage deltas reported so far in that call. They are not a complete Geth `TraceFrame` substitute. Client output can also be incomplete; see the [upstream Reth fixes](https://github.com/paradigmxyz/reth/pull/27213). Missing bytecode (when opcode names are absent) and missing CALL/CREATE result pushes raise `evm_trace.vmtrace.IncompleteTraceError`, a `ValueError` subclass. Other missing or incorrect client data may still produce incorrect frames.

For call-tree reconstruction, struct logs need memory enabled to recover calldata, initcode, events, and return values. If a call has no opcode frames (for example a precompile), enable return-data capture as well; without it the full returned bytes cannot be recovered from the truncated output-memory copy. `LOG0` events have no topics and their `selector` is `None`.

### Events and call order

Struct-log call trees include `LOG0`–`LOG4` events. For `callTracer`, request
`{"tracer": "callTracer", "tracerConfig": {"withLog": true}}` to include logs;
`get_calltree_from_geth_call_trace` imports them into each node's `events` list.
The emitting `event.address` is retained when the client supplies it, including
logs emitted through DELEGATECALL.

`event.position` is the number of child calls preceding that event in its parent.
The text renderer uses it to interleave events and calls in execution order,
while `events` and `calls` remain separate lists. Older traces without positions
use `None` and retain the previous events-first display order. If callers filter
out child calls, they should update event positions; positions beyond the remaining
calls render at the end.

Struct logs include attempted emissions even when execution later reverts.
A client's `callTracer` may discard reverted logs, so event lists across these
formats are not necessarily equivalent for failed calls.

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
