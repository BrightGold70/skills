"""Caller-level RED tests for the Codex hook's judge and state-chain wires."""
from __future__ import annotations

import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import time

import pytest

from tdd_gate_support import build_venv, fake_venv, hermetic_env, shell_corpus, sleeper, write_plan, write_state


CODEX_GATE = Path(__file__).resolve().parents[1] / "hooks" / "h-mad-codex-tdd-gate.py"
HOSTILE_KEY = 'agent "q"\\newline\n[H-MAD:MARKER]%'
TARGET = "hematology-paper-writer/tools/w.py"


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "root"
    root.mkdir()
    write_state(root, {HOSTILE_KEY: {"phase": "step5"}})
    return root


def _file(root: Path, relative: str, body: str = "# governed production\n") -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _payload(target: str = TARGET, *, cwd: str | None = None) -> dict:
    payload = {"tool_name": "apply_patch", "tool_input": {
        "patch": f"*** Update File: {target}\n",
    }}
    if cwd is not None:
        payload["cwd"] = cwd
    return payload


def _run(root: Path, payload: dict, *, gate: Path = CODEX_GATE, timeout: float = 60.0,
         path: str | None = None):
    start = time.monotonic()
    try:
        process = subprocess.run(
            [sys.executable, str(gate)], input=json.dumps(payload), capture_output=True,
            text=True, cwd=root,
            env=hermetic_env(CODEX_PROJECT_DIR=str(root), HMAD_STUB_HOSTILE="all",
                             **({"PATH": path} if path is not None else {})),
            timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired:
        return "invalid", "subprocess timed out", time.monotonic() - start
    output = process.stdout.strip()
    elapsed = time.monotonic() - start
    if process.returncode != 0:
        return "invalid", output, elapsed
    if output in ("", "{}"):
        return "allow", "", elapsed
    try:
        decision = json.loads(output)["hookSpecificOutput"]
        if decision["permissionDecision"] == "deny":
            return "deny", decision["permissionDecisionReason"], elapsed
    except (ValueError, KeyError, TypeError):
        pass
    return "invalid", output, elapsed


def _pid_gone(pidfile: Path) -> None:
    assert pidfile.exists(), "the bounded judge never started the sleeper"
    pid = int(pidfile.read_text(encoding="utf-8"))
    deadline = time.monotonic() + 0.5
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.01)
    with pytest.raises(ProcessLookupError, match=""):
        os.kill(pid, 0)


@pytest.mark.parametrize("kind", [
    "red-measured", "no-test-resolved", "test-missing", "venv-escapes-root",
    "pytest-missing", "pytest-error", "no-tests-ran", "no-summary",
    "test-passing", "timeout", "judge-error",
])
def test_codex_gate_kind(tmp_path, kind):
    root = _root(tmp_path)
    _file(root, TARGET)
    target = TARGET
    if kind != "test-missing":
        body = "def test_red():\n    assert False\n"
        if kind == "pytest-error":
            body = "import module_that_does_not_exist_for_gate\n"
        elif kind == "no-tests-ran":
            body = "# no tests collected\n"
        elif kind == "test-passing":
            body = "def test_green():\n    assert True\n"
        _file(root, "hematology-paper-writer/tests/test_w.py", body)

    if kind == "no-test-resolved":
        target = "tools/x.py"
        _file(root, target)
    elif kind == "venv-escapes-root":
        outside = tmp_path / "outside"
        fake_venv(outside, "exit 0")
        (root / "hematology-paper-writer/.venv").symlink_to(outside / ".venv", target_is_directory=True)
    elif kind == "pytest-missing":
        build_venv(root / "hematology-paper-writer/.venv", with_pytest=False)
    elif kind == "no-summary":
        fake_venv(root / "hematology-paper-writer", "exit 1")
    elif kind == "timeout":
        python = fake_venv(root / "hematology-paper-writer", "exit 0")
        pidfile = tmp_path / "sleeper.pid"
        sleeper(python, pidfile, seconds=90)
    elif kind == "judge-error":
        other = tmp_path / "B"
        gate = other / "hooks/h-mad-codex-tdd-gate.py"
        gate.parent.mkdir(parents=True)
        shutil.copyfile(CODEX_GATE, gate)
        _file(other, "scripts/h_mad_tdd_judge.py", 'raise ImportError("broken judge for AC-5.4")\n')

    verdict, reason, elapsed = _run(
        root, _payload(target), gate=gate if kind == "judge-error" else CODEX_GATE,
        timeout=120.0 if kind == "timeout" else 60.0,
    )
    if kind == "red-measured":
        assert verdict == "allow", (verdict, reason)
    else:
        assert verdict == "deny", f"{kind}: expected JSON deny, got {verdict}: {reason}"
        assert f"kind={kind}" in reason, f"{kind}: {reason}"
    if kind == "timeout":
        assert elapsed < 60.0, f"judge exceeded its 40-second budget: {elapsed:.2f}s"
        _pid_gone(pidfile)


def test_root_step5_governs_a_subproject_with_its_own_state(tmp_path):
    root = _root(tmp_path)
    write_state(root / "hematology-paper-writer", {})
    _file(root, TARGET)
    _file(root, "hematology-paper-writer/tests/test_w.py", "def test_green():\n    assert True\n")
    verdict, reason, _ = _run(root, _payload())
    assert verdict == "deny", f"read_chain must retain root step5: {verdict}: {reason}"
    assert "kind=test-passing" in reason


def _cwd_project(tmp_path: Path, test_body: str):
    root = _root(tmp_path)
    relative = "hematology-paper-writer/tools/review_round/guideline_excerpts.py"
    _file(root, relative)
    _file(root, "hematology-paper-writer/tests/test_guideline_excerpts.py", test_body)
    write_plan(root, HOSTILE_KEY, (
        "## Task 1: review_round\n"
        "**Production file**: `tools/review_round/guideline_excerpts.py`\n"
        "**Test file**: `tests/test_guideline_excerpts.py`\n"
    ))
    alias = tmp_path / "alias"
    alias.symlink_to(root, target_is_directory=True)
    cwd = str(alias / "hematology-paper-writer")
    assert os.path.realpath(cwd) != cwd
    return root, cwd, relative


def test_payload_cwd_base_resolves_a_subproject_relative_target(tmp_path):
    root, cwd, _ = _cwd_project(tmp_path, "def test_red():\n    assert False\n")
    verdict, reason, _ = _run(root, _payload("tools/review_round/guideline_excerpts.py", cwd=cwd))
    assert verdict == "allow", f"payload cwd must resolve the RED project target: {verdict}: {reason}"


def test_payload_cwd_deny_names_the_prefixed_path(tmp_path):
    root, cwd, relative = _cwd_project(tmp_path, "def test_green():\n    assert True\n")
    verdict, reason, _ = _run(root, _payload("tools/review_round/guideline_excerpts.py", cwd=cwd))
    assert verdict == "deny", f"payload cwd must resolve the GREEN project target: {verdict}: {reason}"
    assert relative in reason, f"deny must name root-relative project path: {reason}"


def test_payload_cwd_outside_the_root_falls_back_to_the_root(tmp_path):
    root = _root(tmp_path)
    _file(root, TARGET)
    _file(root, "hematology-paper-writer/tests/test_w.py", "def test_red():\n    assert False\n")
    verdict, reason, _ = _run(root, _payload(cwd=str(tmp_path)))
    assert verdict == "allow", f"outside cwd must fall back to root: {verdict}: {reason}"


def test_fifo_state_on_the_chain_denies_a_write_without_blocking(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    state = root / "hematology-paper-writer/docs/.bkit-memory.json"
    state.parent.mkdir(parents=True)
    os.mkfifo(state)
    verdict, reason, elapsed = _run(root, _payload(), timeout=5.0)
    assert elapsed < 1.0, f"FIFO state read blocked the write for {elapsed:.2f}s"
    assert verdict == "deny" and "unreadable" in reason, (verdict, reason)


def test_fifo_state_off_the_chain_denies_shell_without_blocking(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    state = root / "other/docs/.bkit-memory.json"
    state.parent.mkdir(parents=True)
    os.mkfifo(state)
    verdict, reason, elapsed = _run(
        root, {"tool_name": "shell_command", "tool_input": {"command": "ls"}}, timeout=5.0,
    )
    assert elapsed < 1.0, f"FIFO state scan blocked the shell for {elapsed:.2f}s"
    assert verdict == "deny" and "state is unreadable" in reason, (verdict, reason)


def test_unsearchable_docs_on_the_chain_denies_although_the_scan_is_inactive(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    state = write_state(root / "hematology-paper-writer", {HOSTILE_KEY: {"phase": "step5"}})
    docs = state.parent
    docs.chmod(0)
    try:
        verdict, reason, _ = _run(root, _payload())
    finally:
        docs.chmod(0o755)
    assert verdict == "deny", f"unsearchable governing state must fail closed: {verdict}: {reason}"
    assert "kind=judge-error" in reason, reason


def test_codex_gate_keeps_no_private_resolver():
    source = CODEX_GATE.read_text(encoding="utf-8")
    for token in ("_target_phase5_status", "_derived_test", "_test_exit", "h_mad_derive_test_path.sh"):
        assert token not in source, f"hook still owns private resolution: {token}"


@pytest.fixture(scope="module")
def shell_rows(tmp_path_factory):
    scripts_dir = CODEX_GATE.parent.parent / "scripts"
    return shell_corpus(tmp_path_factory.mktemp("shell-policy"), scripts_dir)


def _shell_verdict(root: Path, cwd: Path, command: str) -> tuple[str, str]:
    verdict, reason, _ = _run(
        root, {"tool_name": "shell_command", "cwd": str(cwd),
               "tool_input": {"command": command}}, path="/usr/bin:/bin",
    )
    return verdict, reason


def test_codex_gate_allows_documented_budget_command_in_step5(tmp_path):
    adapter = CODEX_GATE.parent.parent / "references" / "codex-runtime.md"
    script = CODEX_GATE.parent.parent / "scripts" / "h_mad_context_budget.py"
    documented = 'python3 "<HMAD_SKILL_ROOT>/scripts/h_mad_context_budget.py" --host codex'
    assert documented in adapter.read_text(encoding="utf-8")
    command = documented.replace("<HMAD_SKILL_ROOT>", str(script.parent.parent))
    assert command == f'python3 "{script}" --host codex'
    root = _root(tmp_path)
    verdict, reason, _ = _run(
        root, {"tool_name": "exec_command", "tool_input": {"cmd": command}, "cwd": str(root)},
    )
    assert verdict == "allow", reason


@pytest.mark.parametrize("name,expected", [
    ("contained/sub-cwd/pytest", "allow"),
    ("contained/root-prefix/pytest", "allow"),
    ("venv-symlink-out/sub-cwd/pytest", "deny"),
    ("venv-symlink-out/root-prefix/pytest", "deny"),
    ("contained/doubled/pytest", "deny"),
    ("contained/sub-cwd/c-write", "deny"),
    ("contained/root-prefix/c-write", "deny"),
    ("contained/doubled/c-write", "deny"),
    ("venv-symlink-out/sub-cwd/c-write", "deny"),
    ("venv-symlink-out/root-prefix/c-write", "deny"),
    ("venv-symlink-out/doubled/c-write", "deny"),
], ids=[
    "sub-cwd-contained", "root-cwd-contained", "sub-cwd-escaping", "root-cwd-escaping",
    "doubled-path", "c-sub-cwd-contained", "c-root-cwd-contained", "c-doubled-contained",
    "c-sub-cwd-escaping", "c-root-cwd-escaping", "c-doubled-escaping",
])
def test_shell_venv_token(shell_rows, name, expected):
    row = next(row for row in shell_rows if row.name == name)
    verdict, reason = _shell_verdict(row.root, row.cwd, row.command)
    assert verdict == expected, f"{name}: venv token must be {expected}: {verdict}: {reason}"


@pytest.mark.parametrize("case,expected", [
    ("contained-venv", "allow"),
    ("usr-bin-python3-control", "allow"),
    ("escaping-venv", "deny"),
    ("script-outside-scripts", "deny"),
], ids=["contained-venv", "usr-bin-python3-control", "escaping-venv", "script-outside-scripts"])
def test_shell_control_allowlist_under_a_venv(shell_rows, case, expected):
    by_name = {row.name: row for row in shell_rows}
    if case == "contained-venv":
        row = by_name["contained/sub-cwd/pytest"]
    elif case == "usr-bin-python3-control":
        row = by_name["control/usr-python-pytest"]
    elif case == "escaping-venv":
        row = by_name["venv-symlink-out/sub-cwd/pytest"]
    else:
        row = by_name["contained/sub-cwd/pytest"]
        script = row.cwd / "h_mad_wire_registry.py"
        script.write_text("# script outside h-mad/scripts\n", encoding="utf-8")
        command = f".venv/bin/python {script} verify"
        verdict, reason = _shell_verdict(row.root, row.cwd, command)
        assert verdict == expected, f"scripts-root rule must deny {command}: {verdict}: {reason}"
        return
    verdict, reason = _shell_verdict(row.root, row.cwd, row.command)
    assert verdict == expected, f"{case}: shell control must be {expected}: {verdict}: {reason}"


def test_venv_token_keys_on_the_lexical_name(tmp_path):
    root = _root(tmp_path)
    sub = root / "hematology-paper-writer"
    python = fake_venv(sub, "exit 0")
    python.unlink()
    python.symlink_to("/bin/cat")
    (sub / "notes.txt").write_text("notes\n", encoding="utf-8")
    verdict, reason = _shell_verdict(root, sub, ".venv/bin/python notes.txt")
    assert verdict == "deny", f"lexical python token must retain python argv rules: {verdict}: {reason}"


def test_shell_policy_corpus_allows_exactly_the_expected_rows(shell_rows):
    actual = set()
    expected = {row.name for row in shell_rows if row.expected_new == "allow"}
    for row in shell_rows:
        verdict, reason = _shell_verdict(row.root, row.cwd, row.command)
        assert verdict in {"allow", "deny"}, f"{row.name}: invalid verdict {verdict}: {reason}"
        if verdict == "allow":
            actual.add(row.name)
    assert actual == expected, f"shell-policy corpus allowed mismatch: missing={expected - actual}, extra={actual - expected}"


def test_venv_token_still_obeys_the_argv_rules(shell_rows):
    row = next(row for row in shell_rows if row.name == "contained/sub-cwd/pytest")
    command = ".venv/bin/python -c pass"
    assert runpy.run_path(str(CODEX_GATE))["SIMPLE_SHELL_COMMAND"].fullmatch(command), \
        "argv-rule oracle must pass the lexical shell subset"
    verdict, reason = _shell_verdict(row.root, row.cwd, command)
    assert verdict == "deny", f"contained venv must still reject python -c: {verdict}: {reason}"
