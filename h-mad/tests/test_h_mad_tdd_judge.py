"""Contract tests for the H-MAD TDD judge before its production module exists."""
from __future__ import annotations

import ast
import json
import os
import re
import stat
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import unquote

import pytest

from tdd_gate_support import (build_venv, fake_venv, hermetic_env, marker_shim,
                              sleeper, write_plan, write_state)

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
JUDGE_PATH = SCRIPTS / "h_mad_tdd_judge.py"
sys.path.insert(0, str(SCRIPTS))
import h_mad_tdd_judge as judge  # noqa: E402 — the intended new-symbol RED

ACTIVE_RE = re.compile(
    r"^TDD-STATE: active codex-escape=(yes|no) blocker=(0|[1-9][0-9]*) "
    r"records=([1-9][0-9]*)( record=[^ ,]+,[^ ,]+,[^ ,]+,"
    r"(absent|null|grok|claude|invalid:[^ ,]+))+$"
)


@pytest.fixture(autouse=True)
def _strip_ambient(monkeypatch):
    for name in list(os.environ):
        if name.startswith("CLAUDE") or name in ("HPW_AGENT_BACKEND", "HMAD_HOST", "HMAD_CODEX_UNAVAILABLE", "CODEX_PROJECT_DIR"):
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")


def _step(status="available", **extra):
    return {"phase": "step5", "codex_status": status, **extra}


def _root(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    return root


def _target(root, rel="hematology-paper-writer/tools/w.py"):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("# governed production\n", encoding="utf-8")
    return p


def _mapped_test(root, *, body="def test_red():\n    assert False\n"):
    p = root / "hematology-paper-writer/tests/test_w.py"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def _records(root, status="available"):
    path = write_state(root, {"feat": _step(status)})
    return judge.read_chain(root, root / "hematology-paper-writer/tools/w.py").records


def _kind(verdict):
    assert verdict.decision == "DENY"
    return verdict.kind


def _cli(*args):
    return subprocess.run([sys.executable, str(JUDGE_PATH), *args],
                          env=hermetic_env(), stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, timeout=60.0, check=False)


def _pid_gone(pidfile):
    deadline = time.monotonic() + 0.5
    while not pidfile.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert pidfile.exists(), "sleeper never wrote its child pid"
    pid = int(pidfile.read_text())
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.01)
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


# Chain: 17 items.
def test_chain_reads_every_state_file_up_to_root(tmp_path):
    root = _root(tmp_path)
    state = write_state(root, {"feat": _step()})
    write_state(root / "sub", {})
    chain = judge.read_chain(root, _target(root, "sub/tools/x.py"))
    assert chain.value == "active"
    assert [r.key for r in chain.records] == ["feat"]
    assert chain.records[0].state_file == state


def test_chain_orders_records_nearest_first(tmp_path):
    root = _root(tmp_path)
    write_state(root, {"b": _step()})
    write_state(root / "sub", {"a": _step()})
    assert [r.key for r in judge.read_chain(root, _target(root, "sub/tools/x.py")).records] == ["a", "b"]


def test_chain_without_step5_is_none(tmp_path):
    root = _root(tmp_path)
    write_state(root, {"old": {"phase": "step4"}})
    assert judge.read_chain(root, _target(root)).value == "none"


@pytest.mark.parametrize("case", ["root-unreadable-sub-step5", "sub-unreadable-root-step5"])
def test_first_unreadable_file_decides(tmp_path, case):
    root = _root(tmp_path)
    sub = root / "sub"
    write_state(root, {"b": _step()})
    write_state(sub, {"a": _step()})
    bad = root if case.startswith("root") else sub
    (bad / "docs/.bkit-memory.json").write_text("{invalid JSON", encoding="utf-8")
    chain = judge.read_chain(root, _target(root, "sub/tools/x.py"))
    assert chain.value == "unreadable"
    assert chain.error_file == bad / "docs/.bkit-memory.json"
    assert chain.records == ()


@pytest.mark.parametrize("case,error", [("fifo", "not-a-regular-file"),
                                         ("directory", "not-a-regular-file"),
                                         ("dangling-symlink", "FileNotFoundError")])
def test_non_regular_state_is_unreadable(tmp_path, case, error):
    root = _root(tmp_path)
    path = root / "docs/.bkit-memory.json"
    path.parent.mkdir()
    if case == "fifo":
        os.mkfifo(path)
    elif case == "directory":
        path.mkdir()
    else:
        path.symlink_to(root / "absent")
    started = time.monotonic()
    chain = judge.read_chain(root, _target(root))
    assert chain.value == "unreadable"
    assert chain.error == error
    if case == "fifo":
        assert time.monotonic() - started < 1.0


@pytest.mark.parametrize("case", ["chmod-dir", "chmod-docs"])
def test_unsearchable_directory_is_unreadable(tmp_path, case):
    root = _root(tmp_path)
    sub = root / "sub"
    path = write_state(sub, {"a": _step()})
    locked = sub if case == "chmod-dir" else sub / "docs"
    locked.chmod(0)
    try:
        chain = judge.read_chain(root, sub / "tools/x.py")
        assert chain.value == "unreadable"
        assert chain.error_file == path
        assert chain.error == "PermissionError"
    finally:
        locked.chmod(0o755)


def test_docs_regular_file_is_absent(tmp_path):
    root = _root(tmp_path)
    write_state(root, {"feat": _step()})
    sub = root / "sub"
    sub.mkdir()
    (sub / "docs").write_text("file, not directory")
    chain = judge.read_chain(root, sub / "x.py")
    assert chain.value == "active"
    assert [r.key for r in chain.records] == ["feat"]


@pytest.mark.parametrize("case", ["list-top", "state-not-object"])
def test_state_that_is_not_an_object_is_unreadable(tmp_path, case):
    root = _root(tmp_path)
    p = write_state(root, {})
    p.write_text("[]" if case == "list-top" else '{"orchestrator_state": []}')
    chain = judge.read_chain(root, _target(root))
    assert (chain.value, chain.error) == ("unreadable", "not-an-object")


@pytest.mark.parametrize("case,expected", [("root-step5", "active"), ("root-none", "none")])
def test_outside_target_reads_the_root_alone(tmp_path, case, expected):
    root = _root(tmp_path)
    write_state(root, {"feat": _step()} if case == "root-step5" else {})
    write_state(tmp_path, {"outside": _step()})
    chain = judge.read_chain(root, tmp_path / "outside.py")
    assert chain.value == expected
    assert all(r.key == "feat" for r in chain.records)


def test_no_target_reads_the_root_alone(tmp_path):
    root = _root(tmp_path)
    write_state(root / "sub", {"feat": _step()})
    assert judge.read_chain(root, None).value == "none"


def test_missing_parent_directories_are_skipped(tmp_path):
    root = _root(tmp_path)
    write_state(root / "sub", {"feat": _step()})
    chain = judge.read_chain(root, root / "sub/newdir/deeper/x.py")
    assert chain.value == "active"
    assert [r.key for r in chain.records] == ["feat"]


# Fallback tags: 14 items, including hostile human-supplied key bytes.
_FALLBACK = [
    ("absent", False, None, "absent", "absent"),
    ("null", True, None, "null", "null"),
    ("grok", True, "grok", "grok", "grok"),
    ("claude", True, "claude", "claude", "claude"),
    ("false", True, False, "invalid:false", "invalid:false"),
    ("true", True, True, "invalid:true", "invalid:true"),
    ("zero", True, 0, "invalid:0", "invalid:0"),
    ("empty-string", True, "", 'invalid:""', "invalid:%22%22"),
    ("capital-grok", True, "Grok", 'invalid:"Grok"', "invalid:%22Grok%22"),
    ("string-null", True, "null", 'invalid:"null"', "invalid:%22null%22"),
    ("codex", True, "codex", 'invalid:"codex"', "invalid:%22codex%22"),
    ("empty-object", True, {}, "invalid:{}", "invalid:%7B%7D"),
    ("empty-list", True, [], "invalid:[]", "invalid:%5B%5D"),
    ("nested-object", True, {"a": [1, 2]}, 'invalid:{"a":[1,2]}',
     "invalid:%7B%22a%22%3A%5B1%2C2%5D%7D"),
]


@pytest.mark.parametrize("case,present,value,tag,wire", _FALLBACK, ids=[x[0] for x in _FALLBACK])
def test_fallback_tag(tmp_path, case, present, value, tag, wire):
    root = _root(tmp_path)
    key = 'agent "q"\\newline\n[H-MAD:MARKER]%'
    state = _step(**({"fallback_agent": value} if present else {}))
    write_state(root, {key: state})
    chain = judge.read_chain(root, _target(root))
    assert chain.records[0].fallback == tag, case
    line = judge.format_state_line(chain, root)
    assert ACTIVE_RE.fullmatch(line), line
    assert line.rsplit(",", 1)[1] == wire
    if wire.startswith("invalid:"):
        assert unquote(wire[len("invalid:"):]) == json.dumps(value, separators=(",", ":"))


# State lines: 11 items.
def test_state_line_none(tmp_path):
    root = _root(tmp_path)
    assert judge.format_state_line(judge.read_chain(root, None), root) == "TDD-STATE: none"


def test_state_line_unreadable(tmp_path):
    root = _root(tmp_path)
    p = write_state(root, {})
    p.write_text("[")
    line = judge.format_state_line(judge.read_chain(root, None), root)
    assert re.fullmatch(r"TDD-STATE: unreadable file=[^ ]+ error=[A-Za-z_-][A-Za-z0-9_-]*", line)
    assert Path(unquote(line.split(" file=", 1)[1].split(" error=", 1)[0])).is_absolute()


@pytest.mark.parametrize("statuses,escape,blocker", [
    (["available"], "no", 1), (["exhausted"], "yes", 0),
    (["exhausted", "available"], "no", 2), (["available", "exhausted"], "no", 1),
    (["exhausted", "exhausted"], "yes", 0), (["unavailable", "exhausted"], "yes", 0),
], ids=["single-available", "single-exhausted", "exhausted-then-available",
        "available-then-exhausted", "both-escaping", "unavailable-and-exhausted"])
def test_state_line_escape_and_blocker(tmp_path, statuses, escape, blocker):
    root = _root(tmp_path)
    write_state(root, {f"k{i}": _step(s) for i, s in enumerate(statuses)})
    line = judge.format_state_line(judge.read_chain(root, None), root)
    assert ACTIVE_RE.fullmatch(line)
    assert f"codex-escape={escape} blocker={blocker} records={len(statuses)}" in line


@pytest.mark.parametrize("case", ["empty-key", "empty-status"])
def test_state_line_empty_values_encode_as_percent(tmp_path, case):
    root = _root(tmp_path)
    write_state(root, {"" if case == "empty-key" else "k": _step("" if case == "empty-status" else "available")})
    line = judge.format_state_line(judge.read_chain(root, None), root)
    assert ACTIVE_RE.fullmatch(line)
    field = line.split(" record=", 1)[1].split(",")
    token = field[0 if case == "empty-key" else 1]
    assert token == "%"
    assert ("" if token == "%" else unquote(token)) == ""


def test_state_line_path_with_space_decodes(tmp_path):
    root = tmp_path / 'a b "q"'
    root.mkdir()
    state = write_state(root, {"feat": _step()})
    line = judge.format_state_line(judge.read_chain(root, None), root)
    assert ACTIVE_RE.fullmatch(line)
    assert unquote(line.split(" record=", 1)[1].split(",")[2]) == str(state)


# CLI: 9 items.
@pytest.mark.parametrize("case", ["none", "active", "unreadable"])
def test_cli_state_verb(tmp_path, case):
    root = _root(tmp_path)
    if case != "none":
        path = write_state(root, {"feat": _step()})
        if case == "unreadable":
            path.write_text("{")
    result = _cli("state", "--root", str(root), "--target", "tools/x.py")
    assert result.returncode == 0, result.stderr
    assert len(result.stdout.splitlines()) == 1
    if case == "active":
        assert ACTIVE_RE.fullmatch(result.stdout.strip())
    elif case == "none":
        assert result.stdout == "TDD-STATE: none\n"
    else:
        assert re.fullmatch(r"TDD-STATE: unreadable file=[^ ]+ error=[A-Za-z_-][A-Za-z0-9_-]*\n", result.stdout)


@pytest.mark.parametrize("case", ["empty-root", "missing-root", "unknown-verb"])
def test_cli_usage_error(tmp_path, case):
    argv = ["state", "--root", ""] if case == "empty-root" else (
        ["state", "--root", str(tmp_path / "missing")] if case == "missing-root" else ["bogus"])
    result = _cli(*argv)
    assert result.returncode == 2
    assert result.stdout == ""


def test_cli_judge_exception_is_a_judge_error_line(tmp_path, monkeypatch, capsys):
    root = _root(tmp_path)
    write_state(root, {"feat": _step()})
    def boom(*args, **kwargs):
        raise RuntimeError("boom")
    monkeypatch.setattr(judge, "judge", boom)
    assert judge.main(["judge", "--root", str(root), "--target", "tools/x.py"]) == 0
    assert capsys.readouterr().out == "TDD-JUDGE: DENY kind=judge-error reason=RuntimeError: boom\n"


def test_cli_state_exception_prints_nothing(tmp_path, monkeypatch, capsys):
    root = _root(tmp_path)
    def boom(*args, **kwargs):
        raise RuntimeError("boom")
    monkeypatch.setattr(judge, "read_chain", boom)
    assert judge.main(["state", "--root", str(root)]) == 2
    assert capsys.readouterr().out == ""


def test_cli_judge_on_a_chain_that_is_not_active(tmp_path):
    root = _root(tmp_path)
    result = _cli("judge", "--root", str(root), "--target", "tools/x.py")
    assert result.returncode == 0
    assert result.stdout.startswith("TDD-JUDGE: DENY kind=judge-error reason=chain is none at judge time")
    assert len(result.stdout.splitlines()) == 1


# Verdict formatter: 3 items.
@pytest.mark.parametrize("case", ["allow-inside", "allow-outside", "deny-control-chars"])
def test_verdict_line_format(tmp_path, case):
    root = _root(tmp_path)
    if case.startswith("allow"):
        test = root / "tests/a b.py" if case == "allow-inside" else tmp_path / "outside/a b.py"
        verdict = judge.Verdict("ALLOW", "red-measured", "", "name-map", test)
        line = judge.format_verdict_line(verdict, root)
        expected = "tests/a%20b.py" if case == "allow-inside" else str(test).replace(" ", "%20")
        assert line == f"TDD-JUDGE: ALLOW kind=red-measured source=name-map test={expected}"
    else:
        verdict = judge.Verdict("DENY", "no-summary", "one\ntwo\tthree", "", None)
        assert judge.format_verdict_line(verdict, root) == "TDD-JUDGE: DENY kind=no-summary reason=one two three"


# Venv: 9 items.
@pytest.mark.parametrize("case,contained", [
    ("contained", True), ("venv-symlink-out", False), ("bin-symlink-out", False),
    ("cfg-missing", False), ("cfg-symlink", False), ("venv-out-bin-back-in", False),
])
def test_venv_contained_rows(tmp_path, case, contained):
    root = _root(tmp_path)
    project = root / "hpw"
    project.mkdir()
    fake_venv(project, "exit 0")
    venv = project / ".venv"
    outside = tmp_path / "outside-venv"
    outside.mkdir()
    (outside / "bin").mkdir()
    (outside / "pyvenv.cfg").write_text("home=outside\n")
    if case == "venv-symlink-out":
        (venv / "bin/python").unlink()
        (venv / "bin").rmdir()
        (venv / "pyvenv.cfg").unlink()
        venv.rmdir()
        venv.symlink_to(outside, target_is_directory=True)
        assert not os.path.realpath(venv).startswith(str(root) + os.sep)
    elif case == "bin-symlink-out":
        (venv / "bin/python").unlink()
        (venv / "bin").rmdir()
        (venv / "bin").symlink_to(outside / "bin", target_is_directory=True)
        assert not os.path.realpath(venv / "bin").startswith(str(root) + os.sep)
    elif case == "cfg-missing":
        (venv / "pyvenv.cfg").unlink()
        assert not os.path.lexists(venv / "pyvenv.cfg")
    elif case == "cfg-symlink":
        cfg = venv / "pyvenv.cfg"
        cfg.unlink()
        real = project / "cfg-real"
        real.write_text("home=inside\n")
        cfg.symlink_to(real)
        assert cfg.is_symlink() and not stat.S_ISREG(cfg.lstat().st_mode)
    elif case == "venv-out-bin-back-in":
        inside_bin = project / "safe-bin"
        inside_bin.mkdir()
        (venv / "bin/python").unlink()
        (venv / "bin").rmdir()
        (venv / "pyvenv.cfg").unlink()
        venv.rmdir()
        (outside / "bin").rmdir()
        (outside / "bin").symlink_to(inside_bin, target_is_directory=True)
        venv.symlink_to(outside, target_is_directory=True)
        assert not os.path.realpath(venv).startswith(str(root) + os.sep)
        assert os.path.realpath(venv / "bin").startswith(str(root) + os.sep)
        assert stat.S_ISREG((venv / "pyvenv.cfg").lstat().st_mode)
    assert judge.venv_contained(project, root) is contained


def test_select_interpreter_takes_the_nearest_venv(tmp_path):
    root = _root(tmp_path)
    fake_venv(root, "exit 0")
    hpw = root / "hpw"
    near = fake_venv(hpw, "exit 0")
    test = hpw / "tests/test_x.py"
    assert judge.select_interpreter(test, root, "fallback") == str(near)


def test_select_interpreter_without_a_venv_uses_the_fallback(tmp_path):
    root = _root(tmp_path)
    assert judge.select_interpreter(root / "tests/test_x.py", root, "fallback") == "fallback"


def test_select_interpreter_never_skips_an_escaping_venv(tmp_path):
    root = _root(tmp_path)
    fake_venv(root, "exit 0")
    hpw = root / "hpw"
    hpw.mkdir()
    outside = tmp_path / "outside"
    fake_venv(outside, "exit 0")
    (hpw / ".venv").symlink_to(outside / ".venv", target_is_directory=True)
    verdict = judge.select_interpreter(hpw / "tests/test_x.py", root, "fallback")
    assert _kind(verdict) == "venv-escapes-root"
    assert str(hpw / ".venv") in verdict.reason
    assert os.path.realpath(hpw / ".venv") in verdict.reason


# Bounded runner: 4 items.
def test_run_bounded_kills_the_process_group(tmp_path):
    root = _root(tmp_path)
    pidfile = tmp_path / "child.pid"
    script = sleeper(tmp_path / "runner", pidfile, 30)
    start = time.monotonic()
    _, _, _, timed_out, _ = judge._run_bounded([str(script)], root, start + 1.0)
    assert timed_out
    assert time.monotonic() - start < 6.0
    _pid_gone(pidfile)


def test_name_map_runs_under_the_budget(tmp_path, monkeypatch):
    root = _root(tmp_path)
    pidfile = tmp_path / "map.pid"
    script = sleeper(tmp_path / "map.sh", pidfile, 30)
    monkeypatch.setattr(judge, "NAME_MAP", script)
    start = time.monotonic()
    verdict = judge.judge(root, _target(root, "tools/x.py"), (), budget_s=1.0,
                          fallback_interpreter=sys.executable)
    assert _kind(verdict) == "timeout"
    assert time.monotonic() - start < 6.0
    _pid_gone(pidfile)


def test_spent_budget_is_timeout_without_a_run(tmp_path):
    root = _root(tmp_path)
    _target(root)
    _mapped_test(root)
    marker = tmp_path / "ran"
    python = fake_venv(root / "hematology-paper-writer", "exit 0")
    marker_shim(python, marker)
    verdict = judge.judge(root, root / "hematology-paper-writer/tools/w.py", _records(root),
                          budget_s=0.0, fallback_interpreter=sys.executable)
    assert _kind(verdict) == "timeout"
    assert not marker.exists()


def test_judge_source_has_no_subprocess_run():
    assert "subprocess.run" not in JUDGE_PATH.read_text(encoding="utf-8")


# Resolution before the W3 plan-parser connection: 4 items.
def test_unmapped_path_is_no_test_resolved(tmp_path):
    root = _root(tmp_path)
    target = _target(root, "tools/x.py")
    write_state(root, {"feat": _step()})
    plan = write_plan(root, "feat", "## Task 1: other\n**Production file**: `tools/other.py`\n**Test file**: `tests/test_other.py`\n")
    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)
    assert _kind(verdict) == "no-test-resolved"
    assert str(plan) in verdict.reason
    assert "matched none" in verdict.reason
    assert "name map: empty for tools/x.py" in verdict.reason


def test_name_map_missing_test_is_test_missing(tmp_path):
    root = _root(tmp_path)
    target = _target(root)
    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)
    assert _kind(verdict) == "test-missing"
    assert "author the failing test first" in verdict.reason


def test_unreadable_plan_is_named_in_test_missing(tmp_path):
    root = _root(tmp_path)
    target = _target(root)
    write_state(root, {"feat": _step()})
    plan = write_plan(root, "feat", "placeholder")
    plan.write_bytes(b"\xff\xfe")
    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)
    assert _kind(verdict) == "test-missing"
    assert "impl-plan unreadable: UnicodeDecodeError" in verdict.reason


def test_name_map_stderr_is_not_a_path(tmp_path, monkeypatch):
    root = _root(tmp_path)
    target = _target(root)
    script = tmp_path / "stderr-map.sh"
    script.write_text("#!/bin/sh\necho hematology-paper-writer/tests/test_w.py >&2\n")
    script.chmod(0o755)
    monkeypatch.setattr(judge, "NAME_MAP", script)
    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)
    assert _kind(verdict) == "no-test-resolved"
    assert "name map: empty for hematology-paper-writer/tools/w.py" in verdict.reason


# Scoring before the W4 summary connection: 5 items.
@pytest.mark.parametrize("case", ["project-venv", "gate-interpreter"])
def test_pytest_missing_denies(tmp_path, case):
    root = _root(tmp_path)
    target = _target(root)
    _mapped_test(root, body="def test_pass():\n    assert True\n")
    if case == "project-venv":
        interpreter = build_venv(root / "hematology-paper-writer/.venv", with_pytest=False)
    else:
        interpreter = build_venv(tmp_path / "gate-venv", with_pytest=False)
    verdict = judge.judge(root, target, _records(root), fallback_interpreter=(
        sys.executable if case == "project-venv" else str(interpreter)))
    assert _kind(verdict) == "pytest-missing"


def test_timeout_kind(tmp_path):
    root = _root(tmp_path)
    target = _target(root)
    _mapped_test(root)
    pidfile = tmp_path / "pytest.pid"
    python = fake_venv(root / "hematology-paper-writer", "exit 0")
    sleeper(python, pidfile, 30)
    start = time.monotonic()
    verdict = judge.judge(root, target, _records(root), budget_s=1.0,
                          fallback_interpreter=sys.executable)
    assert _kind(verdict) == "timeout"
    assert time.monotonic() - start < 6.0
    _pid_gone(pidfile)


def test_interpreter_that_cannot_start_is_no_summary(tmp_path):
    root = _root(tmp_path)
    target = _target(root)
    _mapped_test(root)
    python = fake_venv(root / "hematology-paper-writer", "exit 0")
    python.chmod(0o644)
    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)
    assert _kind(verdict) == "no-summary"
    assert "PermissionError" in verdict.reason


def test_escaping_venv_denies_before_any_run(tmp_path):
    root = _root(tmp_path)
    target = _target(root)
    _mapped_test(root)
    project = root / "hematology-paper-writer"
    outside = tmp_path / "outside-venv"
    python = fake_venv(outside, "exit 0")
    marker = tmp_path / "escaped-ran"
    marker_shim(python, marker)
    (project / ".venv").symlink_to(outside / ".venv", target_is_directory=True)
    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)
    assert _kind(verdict) == "venv-escapes-root"
    assert not marker.exists()


# 3.9 syntax and import floor: 4 items.
@pytest.mark.parametrize("name", ["h_mad_tdd_judge", "h_mad_wire_pin_gate",
                                  "h_mad_wire_registry", "h_mad_audit_gate"])
def test_three_nine_floor(name):
    floor = Path("/usr/bin/python3")
    assert floor.is_file(), "Python 3.9 floor interpreter missing"
    source = (SCRIPTS / f"{name}.py").read_text(encoding="utf-8")
    ast.parse(source, feature_version=(3, 9))
    result = subprocess.run(
        [str(floor), "-c", f"import sys; sys.path.insert(0, {str(SCRIPTS)!r}); import {name}"],
        stdin=subprocess.DEVNULL, capture_output=True, text=True,
        env=hermetic_env(), timeout=60.0, check=False,
    )
    assert result.returncode == 0, result.stderr
