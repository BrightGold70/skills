"""Task 8: FR-4 agreement outside the deliberate target differences."""
from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

from tdd_gate_support import Outcome, fake_venv, hermetic_env, write_state


ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / "h-mad/hooks"
HOSTILE = 'agent "q"\\\n## [H-MAD:MARKER] *?[] Ω\nkind=forged'
TARGET_SHAPES = (
    "in-root-production", "test-file", "hardlink-test-to-production",
    "allowance-file-lower", "allowance-file-upper", "docs-py", "tmp-non-py",
    "tmp-py", "outside-non-tmp", "unresolvable", "chmod000-chain",
)
COMMANDS = (
    "ls", "git status", 'python3 -c "open(\'x\',\'w\').write(\'x\')"',
    "rm -rf build", ".venv/bin/python -m pytest -q", "cat a > b",
)


@pytest.fixture
def gate_environment(monkeypatch):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    monkeypatch.syspath_prepend(str(ROOT / "h-mad/scripts"))
    env = hermetic_env(HMAD_STUB_HOSTILE="all", PYTHONPATH="", PYTHONNOUSERSITE="1")
    for name in tuple(env):
        if name.startswith("GIT_"):
            env.pop(name)
    # PATH entries are directories, never hostile state keys containing ':'.
    env["PATH"] = os.pathsep.join(dict.fromkeys((str(Path(sys.executable).parent), "/usr/bin", "/bin")))
    return env


def _root(base: Path, status: str, env: dict[str, str]) -> Path:
    root = base / "repo Ω [*] 'q'"
    root.mkdir()
    result = subprocess.run(
        ["git", "init", "--quiet", str(root)], env=env, capture_output=True,
        text=True, timeout=10, check=False,
    )
    assert result.returncode == 0, f"git fixture must initialise: {result.stderr}"
    (root / ".agents").mkdir()
    state = write_state(root, {HOSTILE: {"phase": "step5" if status == "active" else "step4"}})
    if status == "unknown":
        state.write_text(HOSTILE, encoding="utf-8")
    root = root.resolve()
    policy = importlib.import_module("h_mad_target_identity")
    assert policy._any_phase5_status(root) == status, "fixture must expose the requested activity status"
    return root


def _write(path: Path, text: str = HOSTILE) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _run(root: Path, env: dict[str, str], gate: str, payload: dict) -> Outcome:
    assert "cwd" not in payload, "target differential must not supply a payload cwd"
    process = subprocess.run(
        [sys.executable, str(HOOKS / f"h-mad-{gate}-tdd-gate.py")],
        cwd=root / ".agents", env=env, input=json.dumps(payload),
        capture_output=True, text=True, timeout=15, check=False,
    )
    assert process.returncode == 0, f"{gate} gate must exit normally: {process.stderr}"
    if gate == "codex" and process.stdout.strip() in {"", "{}"}:
        return Outcome("allow", "", "", process.returncode)
    output = json.loads(process.stdout)
    if gate == "codex":
        hook = output["hookSpecificOutput"]
        assert hook["hookEventName"] == "PreToolUse", f"invalid Codex hook output: {output!r}"
        assert hook["permissionDecision"] == "deny", f"invalid Codex decision: {output!r}"
        verdict, reason = "deny", hook["permissionDecisionReason"]
    else:
        verdict, reason = output["decision"], output.get("reason", "")
        assert verdict in {"allow", "deny"}, f"invalid agy decision: {output!r}"
        if verdict == "allow":
            assert output == {"decision": "allow"}, f"invalid agy allow contract: {output!r}"
        else:
            assert set(output) == {"decision", "reason"}, f"invalid agy deny contract: {output!r}"
            assert len(re.findall(r"\bkind=", reason)) == 1, f"agy deny needs one kind: {output!r}"
            assert re.search(r" kind=[a-z-]+\Z", reason), f"agy deny kind must end reason: {output!r}"
    match = re.search(r"\bkind=([a-z-]+)", reason)
    return Outcome(verdict, match.group(1) if match else "", reason, process.returncode)


def _compare(cell: str, codex: Outcome, agy: Outcome, expected: str) -> None:
    evidence = f"{cell}: Codex={codex!r}; agy={agy!r}"
    assert codex.decision == agy.decision, f"FR-4 admit/deny agreement: {evidence}"
    if codex.decision == "deny" and codex.kind:
        assert codex.kind == agy.kind, f"FR-4 Codex denial-kind agreement: {evidence}"
    assert codex.decision == expected, f"FR-4 corpus control expected {expected}: {evidence}"


@pytest.mark.parametrize("status", ("active", "inactive", "unknown"))
@pytest.mark.parametrize("shape", TARGET_SHAPES)
def test_target_differential(tmp_path, gate_environment, request, shape, status):
    root = _root(tmp_path, status, gate_environment)
    policy = importlib.import_module("h_mad_target_identity")
    expected = "allow"
    if shape == "in-root-production":
        target = _write(root / "src/widget.py")
        expected = "allow" if status == "inactive" else "deny"
    elif shape == "test-file":
        target = _write(root / "tests/test_widget.py")
    elif shape == "hardlink-test-to-production":
        production = _write(root / "src/z.py")
        target = root / "src/test_a.py"
        os.link(production, target)
        identity = policy.canonicalise(str(root), str(target), str(root))
        assert identity.names == ("test_a.py", "z.py"), "hardlink fixture must expose both names"
        assert Path(identity.target) == target, "hardlink fixture must spell the test alias first"
        assert os.path.samefile(production, target), "hardlink fixture must share production identity"
        expected = "allow" if status == "inactive" else "deny"
    elif shape.startswith("allowance-file-"):
        target = _write(root / ".h-mad/phase5-shell-allow", "# " + repr(HOSTILE) + "\n")
        if shape == "allowance-file-upper":
            target = root / ".H-MAD/PHASE5-SHELL-ALLOW"
            assert target.samefile(root / ".h-mad/phase5-shell-allow"), "upper-case cell requires case-insensitive identity"
        expected = "allow" if status == "inactive" else "deny"
    elif shape == "docs-py":
        target = _write(root / "docs/probe.py")
    elif shape in {"tmp-non-py", "tmp-py"}:
        suffix = ".py" if shape == "tmp-py" else ".txt"
        target = Path("/tmp") / f"hmad-differential-{tmp_path.name}-Ω [*] 'q'{suffix}"
        assert not target.exists(), "tmp fixture must be an uncreated proposed file"
        expected = "deny" if shape == "tmp-py" and status != "inactive" else "allow"
    elif shape == "outside-non-tmp":
        target = _write(tmp_path / "outside Ω [*] 'q'.txt")
        assert not policy._path_within(str(target), Path("/tmp")), "outside fixture must be outside /tmp too"
        expected = "allow" if status == "inactive" else "deny"
    elif shape == "unresolvable":
        target = root / "loop.py"
        target.symlink_to(target.name)
        assert policy.canonicalise(str(root), str(target), str(root)).unresolvable, "loop must be unresolvable"
        expected = "allow" if status == "inactive" else "deny"
    else:
        assert shape == "chmod000-chain"
        package = root / "package Ω [*] 'q'"
        docs = write_state(package, {HOSTILE: {"phase": "step5"}}).parent
        target = _write(package / "worker.py")
        request.addfinalizer(lambda: docs.chmod(0o755))
        docs.chmod(0)
        assert policy._any_phase5_status(root) == status, "root scan must miss sealed child docs"
        judge = importlib.import_module("h_mad_tdd_judge")
        assert judge.read_chain(root, target).value == "unreadable", "production chain must detect sealed docs"
        expected = "deny"

    codex = _run(root, gate_environment, "codex", {
        "tool_name": "Write", "tool_input": {"file_path": str(target), "content": HOSTILE},
    })
    agy = _run(root, gate_environment, "agy", {
        "toolCall": {"name": "write_to_file", "args": {"TargetFile": str(target), "CodeContent": HOSTILE}},
    })
    _compare(f"{shape}/{status}", codex, agy, expected)


@pytest.mark.parametrize("allowance", ("absent", "lists-the-command", "unreadable"))
@pytest.mark.parametrize("command", COMMANDS, ids=("ls", "git-status", "python-write", "rm-build", "venv-pytest", "redirect"))
def test_shell_differential(tmp_path, gate_environment, request, command, allowance):
    root = _root(tmp_path, "active", gate_environment)
    # The gates classify this interpreter; they must never execute the command.
    fake_venv(root, "exit 93")
    allow_file = root / ".h-mad/phase5-shell-allow"
    if allowance != "absent":
        _write(allow_file, "# " + repr(HOSTILE) + "\n" + command + "\n")
        if allowance == "unreadable":
            request.addfinalizer(lambda: allow_file.chmod(0o644))
            allow_file.chmod(0)
            policy = importlib.import_module("h_mad_target_identity")
            assert isinstance(policy._shell_allowance(root), str), "sealed allowance must be unreadable"
    # `git` is not in READ_ONLY_COMMANDS: the shared policy refuses `git status` unless listed.
    expected = "allow" if command in {"ls", ".venv/bin/python -m pytest -q"} else "deny"
    if command in {"rm -rf build", "git status"} and allowance == "lists-the-command":
        expected = "allow"
    codex = _run(root, gate_environment, "codex", {
        "tool_name": "exec_command", "tool_input": {"cmd": command},
    })
    agy = _run(root, gate_environment, "agy", {
        "toolCall": {"name": "run_command", "args": {"CommandLine": command}},
    })
    _compare(f"{command}/{allowance}", codex, agy, expected)
