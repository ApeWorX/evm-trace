import copy
import gzip
import json
from pathlib import Path

import pytest
from eth_pydantic_types import HexBytes
from msgspec.json import Decoder

from evm_trace.geth import (
    TraceFrame,
    create_trace_frames,
    extract_memory,
    get_calltree_from_geth_call_trace,
    get_calltree_from_geth_trace,
)
from evm_trace.parity import ParityTraceList, get_calltree_from_parity_trace
from evm_trace.vmtrace import VMTrace, dec_hook, from_rpc_response, to_trace_frames

RETH = json.loads((Path(__file__).parent / "data/vmtrace/reth.json").read_text())
CASES = RETH["cases"]
MAINNET = json.loads(
    gzip.decompress((Path(__file__).parent / "data/vmtrace/mainnet.json.gz").read_bytes())
)


def decode(code, ops):
    return Decoder(VMTrace, dec_hook=dec_hook).decode(json.dumps({"code": code, "ops": ops}))


def operation(pc, push=(), *, mem=None, sub=None, executed=True):
    return {
        "pc": pc,
        "cost": 3,
        "ex": {"used": 100, "push": list(push), "mem": mem, "store": None} if executed else None,
        "sub": sub,
    }


def semantic_tree(node):
    """Compare fields shared by the formats, excluding gas accounting and log availability."""
    return {
        "type": node.call_type.value,
        "address": node.address.hex(),
        "depth": node.depth,
        "value": node.value,
        "failed": node.failed,
        "input": node.calldata.hex(),
        "output": node.returndata.hex(),
        "calls": [semantic_tree(child) for child in node.calls],
    }


@pytest.mark.parametrize("name", CASES)
def test_structlogs_match_call_tracer(name):
    case = CASES[name]
    actual = get_calltree_from_geth_trace(
        create_trace_frames(case["geth"]["structLogs"]),
        address=case["call"]["to"],
        value=case["call"].get("value", 0),
    )
    expected = get_calltree_from_geth_call_trace(case["call_tracer"])
    assert semantic_tree(actual) == semantic_tree(expected)


@pytest.mark.parametrize("name", CASES)
def test_parity_call_tree_matches_call_tracer(name):
    case = CASES[name]
    actual = semantic_tree(
        get_calltree_from_parity_trace(ParityTraceList.model_validate(case["parity"]["trace"]))
    )
    expected = semantic_tree(get_calltree_from_geth_call_trace(case["call_tracer"]))
    if name == "precompile_then_contract":
        # Reth's Parity call trace deliberately omits the zero-value precompile.
        expected["calls"].pop(0)
    if name in ("create2", "create2_return_code"):
        # The Parity action only says "create"; it does not identify CREATE2.
        expected["calls"][0]["type"] = "CREATE"
    assert actual == expected


def test_call_tracer_input_is_not_mutated():
    raw = copy.deepcopy(CASES["failed_child_then_contract"]["call_tracer"])
    original = copy.deepcopy(raw)
    first = get_calltree_from_geth_call_trace(raw)
    second = get_calltree_from_geth_call_trace(raw)
    assert raw == original
    assert first == second
    assert first.calls[0].failed


def test_log0_has_no_selector():
    node = get_calltree_from_geth_trace(create_trace_frames(CASES["log0"]["geth"]["structLogs"]))
    event = node.events[0]
    assert event.topics == []
    assert event.selector is None
    assert event.data == bytes(32)
    assert "display_err" not in str(node)


def test_short_address_is_left_padded():
    frame = next(
        f for f in create_trace_frames(CASES["call"]["geth"]["structLogs"]) if f.op == "CALL"
    )
    assert frame.address == bytes.fromhex("0000000000000000000000000000000000001002")


def test_consecutive_create_addresses_resolve_at_first_resumed_frame():
    case = CASES["consecutive_create"]
    frames = list(create_trace_frames(case["geth"]["structLogs"]))
    creates = [f for f in frames if f.op == "CREATE"]
    assert [f.address.hex() for f in creates] == [c["to"][2:] for c in case["call_tracer"]["calls"]]
    assert len(frames) == len(case["geth"]["structLogs"])


def test_memory_reads_use_integer_offsets_and_zero_fill():
    assert extract_memory(HexBytes(2**255), HexBytes(0), []) == b""
    assert extract_memory(HexBytes(2**255), HexBytes(3), []) == bytes(3)
    assert extract_memory(HexBytes(31), HexBytes(3), [HexBytes(b"a" * 32)]) == b"a\x00\x00"


def test_vmtrace_decodes_without_erigon_extensions():
    trace = decode(
        "0x600160020100",
        [operation(0, ["0x1"]), operation(2, ["0x2"]), operation(4, ["0x3"]), operation(5)],
    )
    frames = list(to_trace_frames(trace))
    assert [f.op for f in frames] == ["PUSH1", "PUSH1", "ADD", "STOP"]
    assert [f.stack for f in frames] == [[], [1], [1, 2], [3]]


@pytest.mark.parametrize(
    "opcode,arguments,push,expected",
    [
        ("5c", [0], ["0x2a"], [7, 42]),
        ("5d", [42, 0], [], [7]),
        ("49", [0], ["0x0"], [7, 0]),
        ("5e", [1, 0, 32], [], [7]),
    ],
)
def test_cancun_stack_effects(opcode, arguments, push, expected):
    values = [7, *arguments]
    code = "".join(f"60{value:02x}" for value in values) + opcode + "00"
    ops = [operation(2 * i, [hex(value)]) for i, value in enumerate(values)]
    ops.extend([operation(2 * len(values), push), operation(2 * len(values) + 1)])
    assert list(to_trace_frames(decode("0x" + code, ops)))[-1].stack == expected


@pytest.mark.parametrize("copy_memory", [True, False])
def test_vmtrace_memory_reads_and_mcopy_without_deltas(copy_memory):
    # MSTORE8(0, 0xaa); MLOAD(64); POP; MCOPY(32, 0, 1); STOP.
    ops = [
        operation(0, ["0xaa"]),
        operation(2, ["0x0"]),
        operation(4, mem={"off": 0, "data": "0xaa"}),
        operation(5, ["0x40"]),
        operation(7, ["0x0"]),
        operation(8),
        operation(9, ["0x1"]),
        operation(11, ["0x0"]),
        operation(13, ["0x20"]),
        operation(15),
        operation(16),
    ]
    trace = decode("0x60aa600053604051506001600060205e00", ops)
    # Snapshot immediately: memoryview mode intentionally exposes mutable memory.
    frames = [
        (f.op, f.stack, bytes(f.memory)) for f in to_trace_frames(trace, copy_memory=copy_memory)
    ]
    assert frames[2][2] == b""  # Before MSTORE8's expansion.
    assert frames[4][2] == b"\xaa" + bytes(31)  # Before MLOAD expands it again.
    assert frames[5][2] == b"\xaa" + bytes(95)
    assert frames[-1][2] == b"\xaa" + bytes(31) + b"\xaa" + bytes(63)
    assert frames[-1][1] == []


@pytest.mark.parametrize("opcode", ["f1", "f2", "f4", "fa"])
def test_vmtrace_call_context(opcode):
    # Empty calldata/output; dirty upper address bits are discarded.
    target = "0xff" + "00" * 29 + "1002"
    values = ["0x0"] * (5 if opcode in ("f1", "f2") else 4) + [target, "0xff"]
    ops = [dict(operation(i, [value]), op="PUSH32") for i, value in enumerate(values)]
    child = {"code": "0x00", "ops": [operation(0)]}
    ops.append(
        dict(
            operation(len(values), ["0x1"], sub=child),
            op={"f1": "CALL", "f2": "CALLCODE", "f4": "DELEGATECALL", "fa": "STATICCALL"}[opcode],
        )
    )
    root = "0x0000000000000000000000000000000000001001"
    frames = list(to_trace_frames(decode("0x", ops), address=root))
    assert frames[-1].depth == 2
    assert frames[-1].address.lower() == (
        root if opcode in ("f2", "f4") else "0x0000000000000000000000000000000000001002"
    )


def test_vmtrace_failed_opcode_does_not_read_missing_stack():
    assert [f.op for f in to_trace_frames(decode("0xf1", [operation(0, executed=False)]))] == [
        "CALL"
    ]


def test_vmtrace_null_and_block_results():
    raw = {
        "result": [
            {"trace": [], "vmTrace": None, "stateDiff": None},
            {"trace": [], "vmTrace": {"code": "0x", "ops": []}, "stateDiff": None},
        ]
    }
    traces = from_rpc_response(json.dumps(raw).encode())
    assert isinstance(traces, list)
    assert [list(to_trace_frames(trace)) for trace in traces] == [[], []]


def test_live_reth_memory_delta_is_not_a_valid_parity_delta():
    # Keep upstream defects explicit instead of silently blessing their output as expected.
    vm = CASES["mstore"]["parity"]["vmTrace"]
    assert vm["ops"][2]["ex"]["mem"] == {"off": 0, "data": "0x"}
    assert vm["ops"][3]["ex"]["mem"]["off"] == 32  # Should be offset 0 on MSTORE.
    trace = from_rpc_response(json.dumps({"result": CASES["mstore"]["parity"]}).encode())
    assert isinstance(trace, VMTrace)
    frames = list(to_trace_frames(trace))
    assert frames[-1].memory != bytes.fromhex(
        CASES["mstore"]["geth"]["structLogs"][-1]["memory"][0][2:]
    )


def test_live_reth_missing_call_result_is_reported():
    trace = from_rpc_response(json.dumps({"result": CASES["call"]["parity"]}).encode())
    assert isinstance(trace, VMTrace)
    with pytest.raises(ValueError, match="missing CALL result push"):
        list(to_trace_frames(trace))


def test_live_reth_gas_and_storage_defects():
    case = CASES["storage"]
    for vm, geth in zip(case["parity"]["vmTrace"]["ops"], case["geth"]["structLogs"], strict=True):
        assert vm["ex"]["used"] == geth["gas"]  # Parity specifies remaining gas AFTER execution.
    store = next(op for op in case["parity"]["vmTrace"]["ops"] if op["op"] == "SSTORE")
    assert store["ex"]["store"] is None  # Missing even though SSTORE changed slot zero.


@pytest.mark.parametrize("name", ["create_success", "consecutive_create"])
def test_live_reth_stop_child_erases_parent_vmtrace(name):
    case = CASES[name]
    assert case["parity"]["vmTrace"]["ops"] == []
    assert any(frame["op"] == "CREATE" for frame in case["geth"]["structLogs"])
    assert not case["call_tracer"]["calls"][0].get("error")


def test_precompile_output_uses_return_data_not_padded_memory():
    raw = copy.deepcopy(CASES["precompile_then_contract"]["geth"]["structLogs"])
    call_index = next(i for i, f in enumerate(raw) if f["op"] == "CALL")
    raw[call_index + 1]["returnData"] = "0xab"
    node = get_calltree_from_geth_trace(TraceFrame(**f) for f in raw)
    assert node.calls[0].returndata == b"\xab"


@pytest.mark.parametrize("tx_hash", MAINNET["transactions"])
def test_mainnet_tracing_methods_match(tx_hash):
    case = MAINNET["transactions"][tx_hash]
    tx = case["transaction"]
    struct_tree = get_calltree_from_geth_trace(
        create_trace_frames(case["geth"]["structLogs"]),
        address=tx["to"],
        calldata=tx["input"],
        value=tx["value"],
    )
    call_tree = get_calltree_from_geth_call_trace(case["call_tracer"])
    parity_tree = get_calltree_from_parity_trace(
        ParityTraceList.model_validate(case["parity"]["trace"])
    )
    transaction_tree = get_calltree_from_parity_trace(
        ParityTraceList.model_validate(case["trace_transaction"])
    )
    assert semantic_tree(struct_tree) == semantic_tree(call_tree) == semantic_tree(parity_tree)
    assert parity_tree == transaction_tree


def test_full_block_vmtrace_matches_individual_replay():
    for block in MAINNET["blocks"].values():
        for replay in block["replay"]:
            transaction_hash = replay["transactionHash"]
            individual = block["individual"][transaction_hash]
            assert {k: v for k, v in replay.items() if k not in ("transactionHash", "vmTrace")} == {
                k: v for k, v in individual.items() if k != "vmTrace"
            }
            assert without_vm_code(replay["vmTrace"]) == without_vm_code(individual["vmTrace"])


def without_vm_code(value):
    if isinstance(value, dict):
        return {k: without_vm_code(v) for k, v in value.items() if k != "code"}
    if isinstance(value, list):
        return [without_vm_code(v) for v in value]
    return value


def test_live_reth_block_replay_omits_bytecode():
    block = MAINNET["blocks"]["1000000"]
    replay = block["replay"][0]
    individual = block["individual"][replay["transactionHash"]]
    assert replay["vmTrace"]["code"] == "0x"
    assert individual["vmTrace"]["code"] != "0x"
    assert replay["vmTrace"]["ops"][13]["sub"]["code"] == "0x"
    assert individual["vmTrace"]["ops"][13]["sub"]["code"] != "0x"


@pytest.mark.parametrize("push", [["0x1", "0x2", "0x1"], ["0x1", "0x2"], ["0x1"], None])
def test_dup_replays_from_stack_across_client_encodings(push):
    # Nethermind traces the two existing operands, Erigon/Besu/Reth also the duplicate.
    ops = [operation(0, ["0x1"]), operation(2, ["0x2"]), operation(4), operation(5)]
    ops[2]["ex"]["push"] = push
    assert list(to_trace_frames(decode("0x600160028100", ops)))[-1].stack == [1, 2, 1]


@pytest.mark.parametrize(
    "name",
    [
        "mstore",
        "mload_expansion",
        "sha3_expansion",
        "return_expansion",
        "revert_expansion",
        "log0",
        "log2",
        "mcopy",
        "transient",
        "blobhash",
        "push0_dup_swap",
        "storage",
        "sload_existing",
    ],
)
def test_vmtrace_instruction_and_stack_fields_match_reth(name):
    case = CASES[name]
    trace = from_rpc_response(json.dumps({"result": case["parity"]}).encode())
    assert isinstance(trace, VMTrace)
    frames = list(to_trace_frames(trace))
    expected = case["geth"]["structLogs"]
    assert len(frames) == len(expected)
    for vm, geth in zip(frames, expected, strict=True):
        assert (vm.pc, vm.op, vm.depth, vm.stack) == (
            geth["pc"],
            geth["op"],
            geth["depth"],
            [int(v, 16) for v in geth["stack"]],
        )
