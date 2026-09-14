# Historical DELEGATECALL fixtures

`historical_delegatecalls.json.gz` records the two Ethereum mainnet transactions requested in [issue #2](https://github.com/ApeWorX/evm-trace/issues/2):

| Transaction                                                          | Original opcode frames | Retained frames | Calls including root | DELEGATECALLs |
| -------------------------------------------------------------------- | ---------------------: | --------------: | -------------------: | ------------: |
| `0xb7d7f1d5ce7743e821d3026647df486f517946ef1342a1ae93c96e4a8016eab7` |                 64,771 |             522 |                  131 |            16 |
| `0x0537316f37627655b7fe5e50e23f71cd835b377d1cde4226443c94723d036e32` |                 88,952 |             510 |                  129 |            25 |

Recorded on 2026-09-14 using `reth/v2.5.2-5a6940e/x86_64-unknown-linux-gnu`. Transaction hashes, block hashes and block numbers are also included in the fixture. The RPC inputs were:

- `eth_getTransactionByHash` with each transaction hash.
- `debug_traceTransaction` with `{"enableMemory": false, "enableReturnData": false, "disableStorage": true, "timeout": "60s"}`.
- `debug_traceTransaction` with `{"tracer": "callTracer", "timeout": "60s"}`.
- `trace_transaction` with each transaction hash.

The opcode fixtures retain the first and last frames, every CALL-family/CREATE-family/terminal/error frame and its successor, and both sides of every depth decrease. Only `pc`, `op`, `gas`, `gasCost`, `depth`, `stack` and `error` fields are retained when present. Their reconstructed call shapes were checked against both the full original traces and `callTracer` before committing the compact fixtures. They are sufficient for these call-tree regressions, not for replaying every opcode.

Memory and return-data capture were disabled to keep the large RPC responses manageable. Struct-log comparisons therefore check call types, addresses, depths, values and failures. The unabridged `callTracer` and Parity call traces additionally check calldata and return values. Gas accounting and log availability differ by format and are excluded from these comparisons.

For the second transaction, Reth's Parity tracer omits one zero-value ECRECOVER `STATICCALL` present in `callTracer`. The test removes only that specific call after checking its type, address, value and lack of children. All DELEGATECALLs remain in the comparison.
