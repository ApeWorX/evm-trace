import json

import pytest

from evm_trace.vmtrace import IncompleteTraceError, VMTrace, from_rpc_response, to_trace_frames


def decode(code, ops):
    trace = from_rpc_response(
        json.dumps(
            {"result": {"trace": [], "vmTrace": {"code": code, "ops": ops}, "stateDiff": None}}
        ).encode()
    )
    assert isinstance(trace, VMTrace)
    return trace


def operation(pc, push=(), *, mem=None, sub=None, executed=True):
    return {
        "pc": pc,
        "cost": 3,
        "ex": {"used": 100, "push": list(push), "mem": mem, "store": None} if executed else None,
        "sub": sub,
    }


def test_vmtrace_decodes_without_erigon_extensions():
    trace = decode(
        "0x600160020100",
        [operation(0, ["0x1"]), operation(2, ["0x2"]), operation(4, ["0x3"]), operation(5)],
    )
    frames = list(to_trace_frames(trace))
    assert [frame.op for frame in frames] == ["PUSH1", "PUSH1", "ADD", "STOP"]
    assert [frame.stack for frame in frames] == [[], [1], [1, 2], [3]]


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
        (frame.op, frame.stack, bytes(frame.memory))
        for frame in to_trace_frames(trace, copy_memory=copy_memory)
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
    assert [
        frame.op for frame in to_trace_frames(decode("0xf1", [operation(0, executed=False)]))
    ] == ["CALL"]


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


def test_live_reth_missing_call_result_is_reported(reth_trace_cases):
    trace = from_rpc_response(json.dumps({"result": reth_trace_cases["call"]["parity"]}).encode())
    assert isinstance(trace, VMTrace)
    with pytest.raises(IncompleteTraceError, match="missing CALL result push"):
        list(to_trace_frames(trace))


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
def test_vmtrace_instruction_and_stack_fields_match_reth(name, reth_trace_cases):
    case = reth_trace_cases[name]
    trace = from_rpc_response(json.dumps({"result": case["parity"]}).encode())
    assert isinstance(trace, VMTrace)
    frames = list(to_trace_frames(trace))
    expected = case["geth"]["structLogs"]
    assert len(frames) == len(expected)
    for vm_frame, geth in zip(frames, expected, strict=True):
        assert (vm_frame.pc, vm_frame.op, vm_frame.depth, vm_frame.stack) == (
            geth["pc"],
            geth["op"],
            geth["depth"],
            [int(value, 16) for value in geth["stack"]],
        )


@pytest.mark.parametrize(
    "code,expected", [("0x20", "KECCAK256"), ("0x44", "DIFFICULTY"), ("0xfe", "INVALID")]
)
def test_recovered_opcode_names(code, expected):
    trace = decode(code, [operation(0, executed=False)])
    assert [frame.op for frame in to_trace_frames(trace)] == [expected]


@pytest.mark.parametrize("opcode", ["SHA3", "PREVRANDAO", "STOP"])
def test_explicit_opcode_name_without_bytecode(opcode):
    trace = decode("0x", [{**operation(0, executed=False), "op": opcode}])
    assert [frame.op for frame in to_trace_frames(trace)] == [opcode]


@pytest.mark.parametrize("program_counter", [0, 3])
def test_missing_bytecode_cannot_recover_opcode(program_counter):
    trace = decode("0x", [operation(program_counter)])
    with pytest.raises(IncompleteTraceError, match="missing bytecode"):
        next(to_trace_frames(trace))


def test_missing_nested_bytecode_is_reported():
    child = {"code": "0x", "ops": [operation(0)]}
    ops = [
        operation(0, ["0x0"]),
        operation(1, ["0x0"]),
        operation(2, ["0x0"]),
        operation(3, ["0x1"], sub=child),
    ]
    with pytest.raises(IncompleteTraceError, match="missing bytecode"):
        list(to_trace_frames(decode("0x5f5f5ff0", ops)))


@pytest.mark.parametrize("code,stop_pc", [("0x6001", 2), ("0x61", 3)])
def test_implicit_stop_after_known_code(code, stop_pc):
    trace = decode(code, [operation(0, ["0x1"]), operation(stop_pc)])
    frames = list(to_trace_frames(trace))
    assert frames[-1].op == "STOP"
    assert frames[-1].stack == [1]


def test_negative_program_counter_is_rejected():
    with pytest.raises(ValueError, match="negative program counter"):
        list(to_trace_frames(decode("0x00", [operation(-1)])))


@pytest.mark.parametrize(
    "opcode", ["CALL", "CALLCODE", "DELEGATECALL", "STATICCALL", "CREATE", "CREATE2"]
)
@pytest.mark.parametrize("push", [None, []])
def test_missing_call_or_create_result(opcode, push):
    op = {**operation(0), "op": opcode}
    op["ex"]["push"] = push
    with pytest.raises(IncompleteTraceError, match=f"missing {opcode} result push"):
        list(to_trace_frames(decode("0x", [op])))
