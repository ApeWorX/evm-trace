"""Collect bounded, read-only differential traces from a local archive node.

Run with ``uv run scripts/collect_trace_cases.py OUTPUT.json``.
No transactions are signed or broadcast; code is supplied through state overrides.
"""

import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

RPC = "http://127.0.0.1:8545"
SENDER = "0x0000000000000000000000000000000000001000"
ROOT = "0x0000000000000000000000000000000000001001"
CHILD = "0x0000000000000000000000000000000000001002"
GRANDCHILD = "0x0000000000000000000000000000000000001003"


def rpc(method, params):
    payload = json.dumps(dict(jsonrpc="2.0", id=1, method=method, params=params)).encode()
    request = Request(RPC, payload, {"Content-Type": "application/json"})
    with urlopen(request, timeout=30) as response:  # noqa: S310 - fixed localhost HTTP URL
        data = json.load(response)
    if "error" in data:
        raise RuntimeError(data["error"])
    return data["result"]


def call(op="f1", to=CHILD, out_size="20", out_offset="00"):
    value = "6000" if op in ("f1", "f2") else ""
    return f"60{out_size}60{out_offset}60006000{value}73{to[2:]}61ffff{op}"


def cases():
    programs = {
        "mstore": "60016000525f00",
        "mload_expansion": "6040515900",
        "sha3_expansion": "60206040205900",
        "return_expansion": "60206040f3",
        "revert_expansion": "60206040fd",
        "log0": "60206040a000",
        "log2": "6002600160006000a200",
        "mcopy": "60aa6000536001600060205e5900",
        "transient": "602a60005d60005c60010100",
        "blobhash": "60004960010100",
        "push0_dup_swap": "5f600180600290915000",
        "storage": "602a6000556000545000",
        "sload_existing": "6000545000",
        "invalid": "fe",
        "underflow_call": "f1",
        "underflow_add": "01",
        "out_of_gas_memory": "630100000051",
        "call": call() + "5000",
        "delegatecall": call("f4") + "5000",
        "delegatecall_value": call("f4") + "5000",
        "callcode": call("f2") + "5000",
        "staticcall": call("fa") + "5000",
        "eoa_then_contract": call(to=GRANDCHILD) + "50" + call() + "5000",
        "precompile_then_contract": call(to="0x" + "04".zfill(40)) + "50" + call() + "5000",
        "failed_child_then_contract": call() + "50" + call(to=GRANDCHILD) + "5000",
        "invalid_child_then_contract": call() + "50" + call(to=GRANDCHILD) + "5000",
        "nested_siblings": call() + "50" + call(to=GRANDCHILD) + "5000",
        "create": "6001600053600160006000f05000",
        "create2": "60016000536000600160006000f55000",
        "create_success": "6000600053600160006000f05000",
        "consecutive_create": "6000600053600160006000f0600160006000f000",
        "create_return_code": "69605f60005360016000f3600052600a60166000f05000",
        "create2_return_code": "69605f60005360016000f36000526001600a60166000f55000",
    }
    for name, code in programs.items():
        overrides = {
            ROOT: {"code": "0x" + code, "stateDiff": {"0x" + "00" * 32: "0x" + "07".zfill(64)}},
            CHILD: {"code": "0x602a60005260206000f3"},
        }
        if name in ("failed_child_then_contract", "invalid_child_then_contract"):
            overrides[CHILD]["code"] = "0xfe" if name.startswith("invalid") else "0x60006000fd"
            overrides[GRANDCHILD] = {"code": "0x602b60005260206000f3"}
        elif name == "nested_siblings":
            overrides[CHILD]["code"] = "0x" + call(to=GRANDCHILD) + "5000"
            overrides[GRANDCHILD] = {"code": "0x602b60005260206000f3"}
        request = {"from": SENDER, "to": ROOT, "gas": "0x100000"}
        if name == "delegatecall_value":
            request["value"] = "0x7"
            overrides[SENDER] = {"balance": "0x1000000000000000000"}
        yield name, request, overrides


def main():
    output = Path(sys.argv[1])
    version = rpc("web3_clientVersion", [])
    block = rpc("eth_getBlockByNumber", ["latest", False])
    result = {
        "client": version,
        "block_number": block["number"],
        "block_hash": block["hash"],
        "cases": {},
    }
    for name, request, overrides in cases():
        result["cases"][name] = {
            "call": request,
            "overrides": overrides,
            "parity": rpc(
                "trace_call", [request, ["vmTrace", "trace"], block["number"], overrides]
            ),
            "geth": rpc(
                "debug_traceCall",
                [request, block["number"], {"enableMemory": True, "stateOverrides": overrides}],
            ),
            "call_tracer": rpc(
                "debug_traceCall",
                [request, block["number"], {"tracer": "callTracer", "stateOverrides": overrides}],
            ),
        }
        print(name, len(result["cases"][name]["geth"]["structLogs"]), flush=True)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
