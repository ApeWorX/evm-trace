"""Save bounded transaction and block replay comparisons from the local archive node."""

import gzip
import json
import sys
from pathlib import Path

from collect_trace_cases import rpc


def main():
    output = Path(sys.argv[1])
    result = {"client": rpc("web3_clientVersion", []), "transactions": {}, "blocks": {}}
    # Before and after Cancun. Select two modest contract executions per block.
    for number in (17_000_000, 22_000_000):
        block = rpc("eth_getBlockByNumber", [hex(number), False])
        receipts = rpc("eth_getBlockReceipts", [hex(number)])
        selected = [r for r in receipts if 21_000 < int(r["gasUsed"], 16) <= 100_000][:2]
        for receipt in selected:
            tx_hash = receipt["transactionHash"]
            result["transactions"][tx_hash] = {
                "transaction": rpc("eth_getTransactionByHash", [tx_hash]),
                "receipt": receipt,
                "block_hash": block["hash"],
                "parity": rpc("trace_replayTransaction", [tx_hash, ["vmTrace", "trace"]]),
                "trace_transaction": rpc("trace_transaction", [tx_hash]),
                "geth": rpc(
                    "debug_traceTransaction",
                    [tx_hash, {"enableMemory": True, "enableReturnData": True}],
                ),
                "call_tracer": rpc("debug_traceTransaction", [tx_hash, {"tracer": "callTracer"}]),
            }
            print(
                number,
                tx_hash,
                len(result["transactions"][tx_hash]["geth"]["structLogs"]),
                flush=True,
            )

    # Early, small blocks cover both single- and multi-transaction responses.
    for number in (1_000_000, 1_000_001):
        block = rpc("eth_getBlockByNumber", [hex(number), False])
        assert int(block["gasUsed"], 16) < 300_000
        replay = rpc("trace_replayBlockTransactions", [hex(number), ["trace", "vmTrace"]])
        individual = {
            tx: rpc("trace_replayTransaction", [tx, ["trace", "vmTrace"]])
            for tx in block["transactions"]
        }
        result["blocks"][str(number)] = {
            "hash": block["hash"],
            "replay": replay,
            "individual": individual,
        }
        print("block", number, len(replay), flush=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(result, separators=(",", ":")) + "\n").encode()
    output.write_bytes(gzip.compress(data, mtime=0) if output.suffix == ".gz" else data)


if __name__ == "__main__":
    main()
