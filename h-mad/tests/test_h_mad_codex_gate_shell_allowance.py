"""Phase 5: an operator-declared shell allowance for work unrelated to the feature.

While any feature is at step5, the codex gate refuses every shell command that is not
a test, a read-only command or an H-MAD control command, anywhere in the project. A
manuscript run in HemaSuite was refused that way during `guideline-web-evidence-admission`
(row T of HemaSuite's anemia-jmj triage, 2026-10-04), and the operator had to pause the
feature's state and restore it afterwards. Scoping by sub-project would not have helped:
that feature's state lived in the root `docs/.bkit-memory.json`, which governs every
directory beneath it.

The operator can now list command prefixes in `<root>/.h-mad/phase5-shell-allow`, one per
line. A command is admitted only if it stays inside the gate's simple lexical subset (no
chaining, redirection or substitution), its argv starts with a declared prefix token for
token, and its executable resolves. Unchanged and fail-closed:
- an unreadable state file still refuses every shell command;
- an allowance file that cannot be read or parsed refuses, naming the file;
- a codex write to the allowance file during Phase 5 is refused, because a worker that
  could write it could grant itself any command.
"""
import os
from pathlib import Path

import pytest

from test_h_mad_codex_tdd_gate_judge import _root, _run

ALLOW = ".h-mad/phase5-shell-allow"


def _shell(command: str) -> dict:
    return {"tool_name": "shell_command", "tool_input": {"command": command}}


def _fake_bin(tmp_path: Path, name: str = "hpw") -> str:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    exe = bin_dir / name
    exe.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    exe.chmod(0o755)
    return f"{bin_dir}:/usr/bin:/bin"


def _allow(root: Path, text: str) -> Path:
    path = root / ALLOW
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_without_an_allowance_the_command_is_refused(tmp_path):
    root = _root(tmp_path)
    verdict, reason, _ = _run(root, _shell("hpw manuscript run paper"), path=_fake_bin(tmp_path))
    assert verdict == "deny", reason


@pytest.mark.parametrize("command", [
    "hpw manuscript run",
    "hpw manuscript run paper --revision 2",
    "hpw manuscript run 'Revision dir'",
])
def test_a_declared_prefix_is_admitted(tmp_path, command):
    root = _root(tmp_path)
    _allow(root, "# manuscript work, unrelated to the feature\n\nhpw manuscript run\n")
    verdict, reason, _ = _run(root, _shell(command), path=_fake_bin(tmp_path))
    assert verdict == "allow", reason


@pytest.mark.parametrize("command", [
    "hpw manuscript delete paper",
    "hpw manuscript",
    "hpw manuscriptrun",
    "hpwx manuscript run",
])
def test_an_undeclared_command_is_refused(tmp_path, command):
    root = _root(tmp_path)
    _fake_bin(tmp_path, "hpwx")
    _allow(root, "hpw manuscript run\n")
    verdict, reason, _ = _run(root, _shell(command), path=_fake_bin(tmp_path))
    assert verdict == "deny", reason


@pytest.mark.parametrize("command", [
    "hpw manuscript run; touch prod.py",
    "hpw manuscript run && touch prod.py",
    "hpw manuscript run > prod.py",
    "hpw manuscript run $(touch prod.py)",
    "hpw manuscript run `touch prod.py`",
    "hpw manuscript run | sh",
    "FOO=1 hpw manuscript run",
])
def test_a_declared_prefix_cannot_carry_another_command(tmp_path, command):
    root = _root(tmp_path)
    _allow(root, "hpw manuscript run\n")
    verdict, reason, _ = _run(root, _shell(command), path=_fake_bin(tmp_path))
    assert verdict == "deny", reason


def test_an_executable_that_does_not_resolve_is_refused(tmp_path):
    root = _root(tmp_path)
    _allow(root, "hpw manuscript run\n")
    verdict, reason, _ = _run(root, _shell("hpw manuscript run"), path="/usr/bin:/bin")
    assert verdict == "deny", reason


def test_unreadable_state_still_refuses_an_allowed_command(tmp_path):
    root = _root(tmp_path)
    (root / "docs" / ".bkit-memory.json").write_text("{not json", encoding="utf-8")
    _allow(root, "hpw manuscript run\n")
    verdict, reason, _ = _run(root, _shell("hpw manuscript run"), path=_fake_bin(tmp_path))
    assert verdict == "deny", reason


def test_an_allowance_that_is_not_a_regular_file_refuses_and_names_it(tmp_path):
    root = _root(tmp_path)
    (root / ALLOW).mkdir(parents=True)
    verdict, reason, _ = _run(root, _shell("hpw manuscript run"), path=_fake_bin(tmp_path))
    assert verdict == "deny", reason
    assert "phase5-shell-allow is unreadable" in reason


def test_a_malformed_allowance_refuses_and_names_it(tmp_path):
    root = _root(tmp_path)
    _allow(root, "hpw manuscript run\nhpw 'unbalanced\n")
    verdict, reason, _ = _run(root, _shell("hpw manuscript run"), path=_fake_bin(tmp_path))
    assert verdict == "deny", reason
    assert "phase5-shell-allow:2 cannot be parsed" in reason


def test_an_allowance_outside_phase5_changes_nothing(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / ALLOW).mkdir(parents=True)  # unreadable, but no feature is at step5
    verdict, reason, _ = _run(root, _shell("hpw manuscript run"), path=_fake_bin(tmp_path))
    assert verdict == "allow", reason


@pytest.mark.parametrize("spelling", [ALLOW, ".H-MAD/Phase5-Shell-Allow"])
def test_codex_cannot_write_the_allowance_during_phase5(tmp_path, spelling):
    root = _root(tmp_path)
    (root / ".h-mad").mkdir()
    patch = f"*** Begin Patch\n*** Add File: {spelling}\n+sh\n*** End Patch\n"
    verdict, reason, _ = _run(root, {"tool_name": "apply_patch", "tool_input": {"patch": patch}})
    assert verdict == "deny", reason
    assert "phase5-shell-allow" in reason


def test_codex_cannot_edit_an_existing_allowance_during_phase5(tmp_path):
    root = _root(tmp_path)
    _allow(root, "hpw manuscript run\n")
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(root / ALLOW)}}
    verdict, reason, _ = _run(root, payload)
    assert verdict == "deny", reason


def test_other_non_python_writes_under_h_mad_are_unaffected(tmp_path):
    root = _root(tmp_path)
    (root / ".h-mad").mkdir()
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(root / ".h-mad" / "notes.md")}}
    verdict, reason, _ = _run(root, payload)
    assert verdict == "allow", reason


def test_outside_phase5_the_allowance_is_writable(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / ".h-mad").mkdir()
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(root / ALLOW)}}
    verdict, reason, _ = _run(root, payload)
    assert verdict == "allow", reason
