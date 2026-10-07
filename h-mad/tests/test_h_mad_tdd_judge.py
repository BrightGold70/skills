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

from tdd_gate_support import (build_venv, detaching_sleeper, fake_venv, hermetic_env,
                              marker_shim, sleeper, stop_detached, write_plan, write_state)

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
JUDGE_PATH = SCRIPTS / "h_mad_tdd_judge.py"
sys.path.insert(0, str(SCRIPTS))
import h_mad_tdd_judge as judge  # noqa: E402 — the intended new-symbol RED

ACTIVE_RE = re.compile(
    r"^TDD-STATE: active codex-escape=(yes|no) blocker=(0|[1-9][0-9]*) "
    r"records=([1-9][0-9]*) fallback=(none|(grok|invalid):([1-9][0-9]*))( record=[^ ,]+,[^ ,]+,[^ ,]+,"
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


# A sleeper must fork `sleep` and write its pid BEFORE the run's deadline kills its group.
# At 1.0s that margin was what the judge's own pre-spawn work left over, and a loaded suite
# run spent it: the judge still reported `timeout` correctly, but nothing was ever written
# and `_pid_gone` failed "never wrote its child pid" (measured: a 0.2s budget reports
# `timeout` with no pidfile, 4/4). 3s leaves the start-up the margin it needs.
SLEEPER_BUDGET_S = 3.0


def _pid_gone(pidfile):
    """The sleeper's `sleep` child is gone. Each wait has its own deadline and its own
    message, so a failure says which half was slow: the pid was never written (the group
    died before the sleeper reached `echo`), or the killed child outlived the wait."""
    deadline = time.monotonic() + 5.0
    while not pidfile.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert pidfile.exists(), (
        "sleeper never wrote its child pid: the run's deadline killed its group before the "
        "sleeper started, so nothing about reaping was measured")
    pid = int(pidfile.read_text())
    deadline = time.monotonic() + 5.0
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
        # Target directly under `sub`: the nearest-first walk (design D2) then probes
        # sub/docs/.bkit-memory.json first, so the reported file is the state file itself.
        chain = judge.read_chain(root, sub / "x.py")
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
    _, _, _, timed_out, _, reap_failed = judge._run_bounded([str(script)], root,
                                                            start + SLEEPER_BUDGET_S)
    assert timed_out
    assert reap_failed is False
    assert time.monotonic() - start < SLEEPER_BUDGET_S + 5.0
    _pid_gone(pidfile)


def test_run_bounded_reap_failure_is_bounded(tmp_path):
    root = _root(tmp_path)
    pidfile = tmp_path / "detached.pid"
    script = detaching_sleeper(tmp_path / "runner", pidfile, 12)
    start = time.monotonic()
    try:
        result = judge._run_bounded([str(script)], root, start + 2.0)
        elapsed = time.monotonic() - start
        assert elapsed < 4.0, f"post-kill reap blocked for {elapsed:.2f}s"
        assert result.timed_out is True
        assert result.reap_failed is True
    finally:
        stop_detached(pidfile)


def test_run_bounded_plain_timeout_is_not_reap_failure(tmp_path):
    root = _root(tmp_path)
    pidfile = tmp_path / "ordinary.pid"
    script = sleeper(tmp_path / "runner", pidfile, 30)
    start = time.monotonic()
    result = judge._run_bounded([str(script)], root, start + SLEEPER_BUDGET_S)
    assert result.timed_out is True
    assert result.reap_failed is False
    assert time.monotonic() - start < SLEEPER_BUDGET_S + 3.0
    _pid_gone(pidfile)


def test_judge_name_map_detach_is_judge_timeout(tmp_path, monkeypatch):
    root = _root(tmp_path)
    pidfile = tmp_path / "map-detached.pid"
    script = detaching_sleeper(tmp_path / "map.sh", pidfile, 12)
    monkeypatch.setattr(judge, "NAME_MAP", script)
    budget_s = 2.0
    start = time.monotonic()
    try:
        verdict = judge.judge(root, _target(root, "tools/x.py"), (), budget_s=budget_s,
                              fallback_interpreter=sys.executable)
        elapsed = time.monotonic() - start
        assert (verdict.decision, verdict.kind) == ("DENY", "judge-timeout"), verdict
        assert elapsed < budget_s + judge.REAP_GRACE_S + 1.0, f"name map reap took {elapsed:.2f}s"
    finally:
        stop_detached(pidfile)


def test_judge_venv_interpreter_detach_is_judge_timeout(tmp_path, monkeypatch):
    root = _root(tmp_path)
    target = _target(root)
    _mapped_test(root)
    pidfile = tmp_path / "pytest-detached.pid"
    script = detaching_sleeper(tmp_path / "interpreter", pidfile, 12)
    monkeypatch.setattr(judge, "select_interpreter", lambda *args: str(script))
    budget_s = 2.0
    start = time.monotonic()
    try:
        verdict = judge.judge(root, target, _records(root), budget_s=budget_s,
                              fallback_interpreter=sys.executable)
        elapsed = time.monotonic() - start
        assert (verdict.decision, verdict.kind) == ("DENY", "judge-timeout"), verdict
        assert elapsed < budget_s + judge.REAP_GRACE_S + 1.0, f"pytest reap took {elapsed:.2f}s"
    finally:
        stop_detached(pidfile)


def test_judge_timeout_has_priority(tmp_path, monkeypatch):
    root = _root(tmp_path)
    target = _target(root)
    first = _plan_test(root, "tests/test_first.py", red=False)
    first.write_text("import missing_module_for_judge_priority\n", encoding="utf-8")
    second = _plan_test(root, "tests/test_second.py", red=False)
    _task_plan(root, "**Production file**: `tools/w.py`\n**Test file**: `tests/test_first.py`",
               "**Production file**: `tools/w.py`\n**Test file**: `tests/test_second.py`")
    pidfile = tmp_path / "priority-detached.pid"
    script = detaching_sleeper(tmp_path / "interpreter", pidfile, 12)
    monkeypatch.setattr(judge, "select_interpreter",
                        lambda test, *args: str(script) if test == second else sys.executable)
    budget_s = 3.0
    start = time.monotonic()
    try:
        verdict = judge.judge(root, target, _records(root), budget_s=budget_s,
                              fallback_interpreter=sys.executable)
        elapsed = time.monotonic() - start
        assert (verdict.decision, verdict.kind) == ("DENY", "judge-timeout"), verdict
        assert "test_first.py: pytest-error" in verdict.reason, verdict.reason
        assert "test_second.py: judge-timeout" in verdict.reason, verdict.reason
        assert elapsed < budget_s + judge.REAP_GRACE_S + 1.0, f"priority reap took {elapsed:.2f}s"
    finally:
        stop_detached(pidfile)


def test_name_map_runs_under_the_budget(tmp_path, monkeypatch):
    root = _root(tmp_path)
    pidfile = tmp_path / "map.pid"
    script = sleeper(tmp_path / "map.sh", pidfile, 30)
    monkeypatch.setattr(judge, "NAME_MAP", script)
    start = time.monotonic()
    verdict = judge.judge(root, _target(root, "tools/x.py"), (), budget_s=SLEEPER_BUDGET_S,
                          fallback_interpreter=sys.executable)
    assert _kind(verdict) == "timeout"
    assert time.monotonic() - start < SLEEPER_BUDGET_S + 5.0
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


# Plan task resolution: W3 caller-to-parser connection (16 items).
def _task_plan(root, *sections):
    write_state(root, {"feat": _step()})
    text = "\n\n".join(
        f"## Task {number}: agent \"quoted\" \\ input\n"
        "[H-MAD:MARKER] human note with `odd * markdown`\n"
        + section
        for number, section in enumerate(sections, 1)
    )
    return write_plan(root, "feat", text + "\n")


def _plan_test(root, rel, *, red=True):
    path = root / "hematology-paper-writer" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("def test_fixture():\n    assert " + ("False" if red else "True") + "\n",
                    encoding="utf-8")
    return path


def test_hemasuite_layout_resolves_from_the_task(tmp_path):
    root = _root(tmp_path)
    target = _target(root, "hematology-paper-writer/cli/_parser.py")
    expected = _plan_test(root, "tests/test_certificate_lock_removed.py")
    _task_plan(root, "**Production file**: `tools/review_round/guideline_excerpts.py`, "
                     "`cli/_parser.py`\n**Test file**: `tests/test_certificate_lock_removed.py`")

    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)

    assert (verdict.decision, verdict.source, verdict.test) == ("ALLOW", "impl-plan", expected), \
        f"judge must follow the plan task to its RED test: {verdict!r}"
    assert verdict.kind == "red-measured"


@pytest.mark.parametrize("production_label,test_label", [
    pytest.param("Production file", "Test file", id="production-file"),
    pytest.param("Production files", "Test file", id="production-files"),
    pytest.param("Production", "Test file", id="production"),
    pytest.param("Production file", "Test file", id="test-file"),
    pytest.param("Production file", "Test files", id="test-files"),
    pytest.param("Production file", "Test", id="test"),
    pytest.param("Production file", "Test file:", id="test-colon-inside"),
])
def test_label_spelling_resolves_the_same(tmp_path, production_label, test_label):
    root = _root(tmp_path)
    target = _target(root)
    expected = _plan_test(root, "tests/test_from_plan.py")
    _task_plan(root, f"**{production_label}**: `tools/w.py`\n"
                     f"**{test_label}**{' ' if test_label.endswith(':') else ':'} `tests/test_from_plan.py`")

    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)

    assert (verdict.decision, verdict.source, verdict.test) == ("ALLOW", "impl-plan", expected), \
        f"judge must resolve {production_label!r}/{test_label!r} task labels: {verdict!r}"


def test_tests_prose_line_contributes_no_candidate(tmp_path):
    root = _root(tmp_path)
    target = _target(root)
    expected = _plan_test(root, "tests/test_from_plan.py")
    absent = root / "hematology-paper-writer/tests/test_absent.py"
    _task_plan(root, "**Production file**: `tools/w.py`\n"
                     "**Test file**: `tests/test_from_plan.py`\n"
                     "**Tests** (5 functions, `tests/test_absent.py`)")

    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)
    resolution = judge.resolve(root, target, _records(root), deadline=time.monotonic() + 40)

    assert (verdict.decision, verdict.source, verdict.test) == ("ALLOW", "impl-plan", expected), \
        f"judge must use the Task test, not Tests prose: {verdict!r}"
    assert absent not in resolution.missing
    assert all(path != absent for path, _ in resolution.present)


def test_none_valued_production_does_not_match(tmp_path):
    root = _root(tmp_path)
    target = _target(root, "docs/x/derive_readings.py")
    _task_plan(root, "**Production file**: none (writes `docs/x/derive_readings.py`)\n"
                     "**Test file**: `tests/test_t.py`")

    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)

    assert (verdict.decision, verdict.kind) == ("DENY", "no-test-resolved"), \
        f"none-valued Production must not create a task match: {verdict!r}"
    assert "test_t.py" not in verdict.reason


def test_several_candidates_first_red_allows(tmp_path):
    root = _root(tmp_path)
    target = _target(root)
    _plan_test(root, "tests/test_one.py", red=False)
    red_test = _plan_test(root, "tests/test_two.py")
    _task_plan(root, "**Production file**: `tools/w.py`\n**Test file**: `tests/test_one.py`",
                     "**Production file**: `tools/w.py`\n**Test file**: `tests/test_two.py`")

    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)

    assert (verdict.decision, verdict.source, verdict.test) == ("ALLOW", "impl-plan", red_test), \
        f"judge must continue past a GREEN candidate to the RED task test: {verdict!r}"


def test_several_candidates_all_green_names_both(tmp_path):
    root = _root(tmp_path)
    target = _target(root)
    _plan_test(root, "tests/test_one.py", red=False)
    _plan_test(root, "tests/test_two.py", red=False)
    _task_plan(root, "**Production file**: `tools/w.py`\n**Test file**: `tests/test_one.py`",
                     "**Production file**: `tools/w.py`\n**Test file**: `tests/test_two.py`")

    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)

    assert (verdict.decision, verdict.kind) == ("DENY", "test-passing"), \
        f"judge must measure both GREEN task tests: {verdict!r}"
    assert "test_one.py" in verdict.reason and "test_two.py" in verdict.reason
    assert "matched" in verdict.reason


def test_task_match_is_authoritative_over_the_name_map(tmp_path):
    root = _root(tmp_path)
    target = _target(root)
    _mapped_test(root)
    _task_plan(root, "**Production file**: `tools/w.py`\n**Test file**: `tests/test_plan_only.py`")

    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)

    assert (verdict.decision, verdict.kind) == ("DENY", "test-missing"), \
        f"matched Task must override the RED name-map test: {verdict!r}"
    assert "test_plan_only.py" in verdict.reason
    assert "test_w.py" not in verdict.reason


def test_mixed_candidates_missing_then_red_allows_the_red(tmp_path):
    root = _root(tmp_path)
    target = _target(root)
    red_test = _plan_test(root, "tests/test_two.py")
    _task_plan(root, "**Production file**: `tools/w.py`\n**Test file**: `tests/test_one.py`",
                     "**Production file**: `tools/w.py`\n**Test file**: `tests/test_two.py`")

    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)

    assert (verdict.decision, verdict.source, verdict.test) == ("ALLOW", "impl-plan", red_test), \
        f"missing first candidate must not hide the RED second candidate: {verdict!r}"


def test_mixed_candidates_missing_then_green_denies_test_passing(tmp_path):
    root = _root(tmp_path)
    target = _target(root)
    _plan_test(root, "tests/test_two.py", red=False)
    _task_plan(root, "**Production file**: `tools/w.py`\n**Test file**: `tests/test_one.py`",
                     "**Production file**: `tools/w.py`\n**Test file**: `tests/test_two.py`")

    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)

    assert (verdict.decision, verdict.kind) == ("DENY", "test-passing"), \
        f"GREEN candidate must be measured even when an earlier candidate is missing: {verdict!r}"
    assert "test_one.py: missing" in verdict.reason
    assert "test_two.py: test-passing" in verdict.reason


def test_candidate_outside_root_is_dropped_and_noted(tmp_path):
    root = _root(tmp_path)
    target = _target(root)
    _task_plan(root, "**Production file**: `tools/w.py`\n"
                     "**Test file**: `../../outside/test_x.py`")

    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)

    assert (verdict.decision, verdict.kind) == ("DENY", "test-missing"), \
        f"outside-root Task candidate must be dropped: {verdict!r}"
    assert "candidate outside root dropped" in verdict.reason


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
    verdict = judge.judge(root, target, _records(root), budget_s=SLEEPER_BUDGET_S,
                          fallback_interpreter=sys.executable)
    assert _kind(verdict) == "timeout"
    assert time.monotonic() - start < SLEEPER_BUDGET_S + 5.0
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


# The two `*-with-subtest` cases need pytest's `subtests` fixture in the interpreter the judge
# runs (sys.executable here): built in from pytest 9, a plugin before that. Without it pytest
# errors on the missing fixture and the judge rightly says `pytest-error`, so the expectation
# depends on the machine, not on the judge. Skip with the reason instead of failing.
_HAS_SUBTESTS = int(pytest.__version__.split(".")[0]) >= 9 or bool(
    __import__("importlib.util").util.find_spec("pytest_subtests"))
_NEEDS_SUBTESTS = pytest.mark.skipif(
    not _HAS_SUBTESTS, reason=f"pytest {pytest.__version__} has no `subtests` fixture (pytest>=9 or pytest-subtests)")


# Scoring through the W4 summary connection: 17 items.
@pytest.mark.parametrize("case,body,decision,kind", [
    ("red", "def test_red():\n    assert False\n", "ALLOW", "red-measured"),
    ("green", "def test_green():\n    assert True\n", "DENY", "test-passing"),
    ("empty", "", "DENY", "no-tests-ran"),
    ("skipped-only", "import pytest\n@pytest.mark.skip\ndef test_skipped():\n    assert False\n",
     "DENY", "no-tests-ran"),
    ("import-error", "import not_a_module_xyz\n", "DENY", "pytest-error"),
    pytest.param("red-with-subtest", "def test_red(subtests):\n    with subtests.test('a'):\n"
                 "        assert True\n        assert False\n", "ALLOW", "red-measured",
                 marks=_NEEDS_SUBTESTS),
    pytest.param("green-with-subtest", "def test_green(subtests):\n    with subtests.test('a'):\n"
                 "        assert True\n        assert True\n", "DENY", "test-passing",
                 marks=_NEEDS_SUBTESTS),
], ids=["red", "green", "empty", "skipped-only", "import-error",
        "red-with-subtest", "green-with-subtest"])
def test_scoring_kinds(tmp_path, case, body, decision, kind):
    root = _root(tmp_path)
    target = _target(root)
    _mapped_test(root, body=body)
    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)
    assert (verdict.decision, verdict.kind) == (decision, kind), f"{case}: {verdict}"
    if case == "import-error":
        assert "import" in verdict.reason and "inside the test body" in verdict.reason


@pytest.mark.parametrize("case,script,decision,kind", [
    ("failed-line-rc0", "printf '1 failed in 0.01s\\n'\nexit 0", "ALLOW", "red-measured"),
    ("silent-rc1", "exit 1", "DENY", "no-summary"),
], ids=["failed-line-rc0", "silent-rc1"])
def test_rc_selects_nothing(tmp_path, case, script, decision, kind):
    root = _root(tmp_path)
    target = _target(root)
    _mapped_test(root)
    fake_venv(root / "hematology-paper-writer", script)
    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)
    assert (verdict.decision, verdict.kind) == (decision, kind), f"{case}: {verdict}"


def test_stray_failed_line_after_a_passing_summary_is_test_passing(tmp_path):
    root = _root(tmp_path)
    target = _target(root)
    _mapped_test(root)
    fake_venv(root / "hematology-paper-writer",
              "printf '2 passed in 0.1s\\n1 failed\\n'\nexit 0")
    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)
    assert (verdict.decision, verdict.kind) == ("DENY", "test-passing"), verdict


def test_quoted_no_module_phrase_is_not_pytest_missing(tmp_path):
    root = _root(tmp_path)
    target = _target(root)
    _mapped_test(root)
    fake_venv(root / "hematology-paper-writer",
              "printf 'E   assert \"No module named pytest\" in out\\n1 failed in 0.01s\\n'\nexit 1")
    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)
    assert (verdict.decision, verdict.kind) == ("ALLOW", "red-measured"), verdict


def test_whole_line_no_module_is_pytest_missing_even_after_red(tmp_path):
    root = _root(tmp_path)
    target = _target(root)
    _mapped_test(root)
    fake_venv(root / "hematology-paper-writer",
              "printf 'x: No module named pytest\\n1 failed in 0.01s\\n'\nexit 1")
    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)
    assert (verdict.decision, verdict.kind) == ("DENY", "pytest-missing"), verdict


@pytest.mark.parametrize("target_form", ["absolute", "relative"])
def test_name_map_source_allows_via_the_cli(tmp_path, target_form):
    root = _root(tmp_path)
    target = _target(root)
    _mapped_test(root)
    write_state(root, {"feat": _step()})
    argument = str(target) if target_form == "absolute" else target.relative_to(root).as_posix()
    result = _cli("judge", "--root", str(root), "--target", argument)
    assert result.returncode == 0, result.stderr
    assert result.stdout == (
        "TDD-JUDGE: ALLOW kind=red-measured source=name-map "
        "test=hematology-paper-writer/tests/test_w.py\n"
    )


def test_contained_venv_shim_runs_pytest(tmp_path):
    root = _root(tmp_path)
    target = _target(root)
    _mapped_test(root)
    marker = tmp_path / "selected-interpreter"
    python = fake_venv(root / "hematology-paper-writer", "exit 0")
    marker_shim(python, marker)
    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)
    assert (verdict.decision, verdict.kind) == ("ALLOW", "red-measured"), verdict
    assert marker.read_text(encoding="utf-8").strip() == str(python)


def test_real_venv_interpreter_symlink_is_accepted(tmp_path):
    root = _root(tmp_path)
    target = _target(root)
    _mapped_test(root)
    hpw = root / "hematology-paper-writer"
    python = build_venv(hpw / ".venv", with_pytest=True)
    assert python.is_symlink() and not os.path.realpath(python).startswith(str(root) + os.sep)
    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)
    assert (verdict.decision, verdict.kind) == ("ALLOW", "red-measured"), verdict


def test_unreadable_plan_with_a_passing_name_map_test_is_test_passing(tmp_path):
    root = _root(tmp_path)
    target = _target(root)
    _mapped_test(root, body="def test_green():\n    assert True\n")
    write_state(root, {"feat": _step()})
    plan = write_plan(root, "feat", "placeholder")
    plan.write_bytes(b"\xff\xfe")
    verdict = judge.judge(root, target, _records(root), fallback_interpreter=sys.executable)
    assert (verdict.decision, verdict.kind) == ("DENY", "test-passing"), verdict
    assert "impl-plan unreadable" in verdict.reason


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
