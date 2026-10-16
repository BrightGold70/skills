"""FR-2: implementer selection, its CLI token, and durable switch recording."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote

import pytest

from tdd_gate_support import hermetic_env, write_state

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
JUDGE_PATH = SCRIPTS / "h_mad_tdd_judge.py"
sys.path.insert(0, str(SCRIPTS))
import h_mad_tdd_judge as judge  # noqa: E402
from h_mad_state_validate import rfc3339_datetime  # noqa: E402

HOSTILE = 'agent "q"\\newline\n[H-MAD:MARKER]%,*?'
FEATURE = "implementer " + HOSTILE


@pytest.fixture(autouse=True)
def _strip_ambient(monkeypatch):
    for name in list(os.environ):
        if name.startswith("CLAUDE") or name in (
            "HPW_AGENT_BACKEND", "HMAD_HOST", "HMAD_CODEX_UNAVAILABLE",
            "HMAD_AGY_UNAVAILABLE", "CODEX_PROJECT_DIR",
        ):
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")


def _which(*available):
    return lambda peer: "/hostile path/" + HOSTILE + "/" + peer if peer in available else None


def _record(**extra):
    return {
        "feature": FEATURE,
        "started_ts": "2026-10-16T00:00:00Z",
        "last_completed_phase": 4,
        "current_phase": 5,
        "phase": "step5",
        "audit_cycles": {"plan": 1, "design": 1, "impl_plan": 1},
        "iterate_cycles": 0,
        "halt_reason": None,
        "halt_ts": None,
        "codex_status": "available",
        "agy_status": "available",
        **extra,
    }


def _root(tmp_path):
    root = tmp_path / ("root " + HOSTILE)
    root.mkdir()
    return root


def _verb(root, *, available=("codex", "agy"), record=False, cwd=None):
    bindir = root / "controlled-bin"
    bindir.mkdir(exist_ok=True)
    for peer in ("codex", "agy"):
        stub = bindir / peer
        if peer in available:
            stub.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            stub.chmod(0o755)
        elif stub.exists():
            stub.unlink()
    env = hermetic_env(PATH=str(bindir), HMAD_STUB_HOSTILE="all")
    env.pop("HMAD_AGY_UNAVAILABLE", None)
    args = [sys.executable, str(JUDGE_PATH), "implementer", "--root", str(root),
            "--feature", FEATURE]
    if record:
        args.append("--record")
    return subprocess.run(args, env=env, cwd=cwd or root, stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, timeout=30, check=False)


def _assert_line(proc, expected):
    assert proc.returncode == 0, (
        "implementer verb must exit 0 after emitting its FR-2 token: " + proc.stderr
    )
    assert proc.stdout == expected + "\n", "implementer verb must emit exactly the FR-2 row"


@pytest.mark.parametrize("tag", ["absent", "codex", "agy", "invalid"])
@pytest.mark.parametrize("codex_available", [True, False], ids=["codex-yes", "codex-no"])
@pytest.mark.parametrize("agy_available", [True, False], ids=["agy-yes", "agy-no"])
def test_resolve_implementer_matrix(tmp_path, tag, codex_available, agy_available):
    resolve = judge.resolve_implementer
    raw = json.dumps(HOSTILE, separators=(",", ":"))
    implementer = "invalid:" + raw if tag == "invalid" else tag
    record = judge.Record(FEATURE, "available", tmp_path / "state.json", "absent",
                          implementer=implementer, agy_status="available")
    available = {peer for peer, present in (("codex", codex_available), ("agy", agy_available))
                 if present}
    result = resolve(record, env={}, which=_which(*available))
    if tag == "invalid":
        expected = ("invalid", None, None, "implementer", raw)
    else:
        chosen = "agy" if tag == "agy" else "codex"
        other = "codex" if chosen == "agy" else "agy"
        resolved = chosen if chosen in available else other if other in available else "claude"
        expected = (resolved, chosen, None if resolved == chosen else "cli-absent", None, "")
    assert isinstance(result, judge.Implementer)
    assert tuple(result) == expected, "FR-2 must choose the requested peer, other peer, then fallback"


@pytest.mark.parametrize("case,status,env,available,reason", [
    ("env", "available", {"HMAD_CODEX_UNAVAILABLE": HOSTILE}, ("codex", "agy"), "env"),
    ("status-unavailable", "unavailable", {}, ("codex", "agy"), "status"),
    ("status-exhausted", "exhausted", {}, ("codex", "agy"), "status"),
    ("cli-absent", "available", {}, ("agy",), "cli-absent"),
], ids=["env", "status-unavailable", "status-exhausted", "cli-absent"])
def test_each_cause_alone(tmp_path, case, status, env, available, reason):
    resolve = judge.resolve_implementer
    record = judge.Record(FEATURE, status, tmp_path / "state.json", "absent",
                          implementer="codex", agy_status="available")
    result = resolve(record, env=env, which=_which(*available))
    assert tuple(result) == ("agy", "codex", reason, None, ""), (
        f"the isolated {case} cause must switch codex to agy with reason={reason}"
    )


@pytest.mark.parametrize("tag,resolved,invalid_field,invalid_value", [
    ("absent", "claude", None, ""),
    ("null", "claude", None, ""),
    ("claude", "claude", None, ""),
    ("grok", "grok", None, ""),
    ("invalid:" + json.dumps(HOSTILE), "invalid", "fallback_agent", json.dumps(HOSTILE)),
], ids=["absent", "null", "claude", "grok", "invalid"])
def test_peers_out_fallback_tag_decides(tmp_path, tag, resolved, invalid_field, invalid_value):
    resolve = judge.resolve_implementer
    record = judge.Record(FEATURE, "exhausted", tmp_path / "state.json", tag,
                          implementer="codex", agy_status="unavailable")
    result = resolve(record, env={}, which=_which("codex", "agy"))
    assert tuple(result) == (resolved, "codex", "status", invalid_field, invalid_value), (
        "with both peers out, only the fallback tag decides the author or invalid field"
    )


def test_record_defaults_keep_positional_construction(tmp_path):
    path = tmp_path / "state.json"
    record = judge.Record(FEATURE, "available", path, "absent")
    assert record.implementer == "absent", "four-argument Record must default implementer to absent"
    assert record.agy_status == "available", "four-argument Record must default agy to available"
    assert tuple(record[:4]) == (FEATURE, "available", path, "absent")
    assert record._fields[-2:] == ("implementer", "agy_status")


@pytest.mark.parametrize("state,expected", [
    ({}, "absent"),
    ({"implementer": None}, "null"),
    ({"implementer": "codex"}, "codex"),
    ({"implementer": "agy"}, "agy"),
    ({"implementer": "grok"}, 'invalid:"grok"'),
    ({"implementer": 42}, "invalid:42"),
], ids=["absent", "null", "codex", "agy", "invalid-string", "invalid-number"])
def test_implementer_tag(state, expected):
    assert judge._implementer_tag(state) == expected, "implementer tags must preserve absence/null/invalid"


@pytest.mark.parametrize("fields,expected", [
    ({}, "available"),
    ({"agy_status": None}, "available"),
    ({"agy_status": "exhausted"}, "exhausted"),
], ids=["absent", "null", "exhausted"])
def test_agy_status_read_like_codex_status(tmp_path, fields, expected):
    state = {"phase": "step5", "implementer": "agy", **fields}
    data = {"orchestrator_state": {FEATURE: state}}
    records = judge._active_records(data, tmp_path / "state.json")
    assert len(records) == 1
    assert records[0].agy_status == expected, "active records must read agy status like codex status"
    assert records[0].codex_status == "available"
    assert records[0].implementer == "agy", "active records must populate the implementer tag"


@pytest.mark.parametrize("case", [
    "file-absent", "key-absent", "unreadable", "not-an-object", "invalid-field",
    "switch-none", "peer-switch", "peers-out",
])
def test_implementer_verb_line(tmp_path, case):
    root = _root(tmp_path)
    state_file = root / "docs" / ".bkit-memory.json"
    expected = "TDD-IMPLEMENTER: no-record feature=" + quote(FEATURE, safe="/._-")
    if case == "key-absent":
        write_state(root, {"another feature": _record(implementer="agy")})
    elif case == "unreadable":
        state_file.parent.mkdir()
        state_file.write_text("{", encoding="utf-8")
        expected = ("TDD-IMPLEMENTER: unreadable file=" + quote(str(state_file), safe="/._-")
                    + " error=JSONDecodeError")
    elif case == "not-an-object":
        write_state(root, {FEATURE: []})
        expected = ("TDD-IMPLEMENTER: unreadable file=" + quote(str(state_file), safe="/._-")
                    + " error=not-an-object")
    elif case == "invalid-field":
        write_state(root, {FEATURE: _record(implementer=HOSTILE)})
        raw = json.dumps(HOSTILE, separators=(",", ":"))
        expected = "TDD-IMPLEMENTER: invalid field=implementer value=" + quote(raw, safe="/._-")
    elif case == "switch-none":
        write_state(root, {FEATURE: _record(implementer="agy")})
        expected = "TDD-IMPLEMENTER: agy chosen=agy switch=none"
    elif case == "peer-switch":
        write_state(root, {FEATURE: _record(implementer="codex", codex_status="exhausted")})
        expected = "TDD-IMPLEMENTER: agy chosen=codex switch=codex->agy reason=status"
    elif case == "peers-out":
        write_state(root, {FEATURE: _record(implementer="agy", agy_status="unavailable",
                                          codex_status="exhausted", fallback_agent="grok")})
        expected = "TDD-IMPLEMENTER: grok chosen=agy switch=peers-out reason=status"
    _assert_line(_verb(root), expected)


def test_implementer_verb_reads_the_record_whatever_its_phase(tmp_path):
    root = _root(tmp_path)
    write_state(root, {FEATURE: _record(phase="step4", current_phase=4, implementer="agy"),
                       "another feature": _record(implementer="codex")})
    child = root / "nested"
    child.mkdir()
    write_state(child, {FEATURE: _record(implementer="codex")})
    _assert_line(_verb(root, cwd=child), "TDD-IMPLEMENTER: agy chosen=agy switch=none")


def test_implementer_verb_record_writes_switch_once(tmp_path):
    root = _root(tmp_path)
    state_file = write_state(root, {FEATURE: _record(implementer="codex", codex_status="exhausted")})
    before = state_file.read_bytes()
    expected = "TDD-IMPLEMENTER: agy chosen=codex switch=codex->agy reason=status"
    _assert_line(_verb(root, record=True), expected)
    first = state_file.read_bytes()
    assert first != before, "--record must durably write the selected switch"
    saved = json.loads(first)["orchestrator_state"][FEATURE]
    switch = saved["implementer_switch"]
    assert set(switch) == {"from", "to", "reason", "ts"}
    assert {key: switch[key] for key in ("from", "to", "reason")} == {
        "from": "codex", "to": "agy", "reason": "status",
    }
    assert rfc3339_datetime(switch["ts"]), "switch timestamp must pass the shared RFC3339 predicate"
    assert {key: value for key, value in saved.items() if key != "implementer_switch"} == _record(
        implementer="codex", codex_status="exhausted",
    )
    # Cross a whole UTC second so an unconditional timestamp rewrite cannot pass by coincidence.
    time.sleep(1.1)
    _assert_line(_verb(root, record=True), expected)
    assert state_file.read_bytes() == first, "an identical switch must skip writing, including its ts"


def test_implementer_verb_record_failed(tmp_path):
    root = _root(tmp_path)
    state_file = write_state(root, {FEATURE: _record(implementer="codex", codex_status="exhausted",
                                                   undeclared_field=HOSTILE)})
    before = state_file.read_bytes()
    expected = "TDD-IMPLEMENTER: agy chosen=codex switch=codex->agy reason=status record=failed"
    _assert_line(_verb(root, record=True), expected)
    assert state_file.read_bytes() == before, "StateWriteError must leave the store unchanged"
    # A sidecar directory makes the real writer raise OSError even for a strict record.
    write_state(root, {FEATURE: _record(implementer="codex", codex_status="exhausted")})
    state_file.with_suffix(".json.lock").unlink(missing_ok=True)
    state_file.with_suffix(".json.lock").mkdir()
    before = state_file.read_bytes()
    _assert_line(_verb(root, record=True), expected)
    assert state_file.read_bytes() == before, "OSError must leave the store unchanged"


def test_implementer_verb_switch_none_writes_nothing(tmp_path):
    root = _root(tmp_path)
    state_file = write_state(root, {FEATURE: _record(implementer="codex")})
    before = state_file.read_bytes()
    _assert_line(_verb(root, record=True), "TDD-IMPLEMENTER: codex chosen=codex switch=none")
    assert state_file.read_bytes() == before, "switch=none must leave the store byte-identical"
    assert "implementer_switch" not in json.loads(before)["orchestrator_state"][FEATURE]
