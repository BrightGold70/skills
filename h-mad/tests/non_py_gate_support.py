"""Scratch repositories and real-hook drivers for the non-Python gate contracts."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest

from tdd_gate_support import Outcome, build_venv, decision, hermetic_env, hook_form, write_plan, write_state


CODEX_GATE = Path(__file__).resolve().parents[1] / "hooks/h-mad-codex-tdd-gate.py"
AGY_GATE = Path(__file__).resolve().parents[1] / "hooks/h-mad-agy-tdd-gate.py"
HOOK = CODEX_GATE.with_name("h-mad-tdd-gate.sh")
JUDGE = HOOK.parents[1] / "scripts/h_mad_tdd_judge.py"
CLAUDE_AUTHOR_LINE = "TDD-IMPLEMENTER: claude chosen=codex switch=peers-out reason=env"
DEFAULT_AUTHOR_LINE = "TDD-IMPLEMENTER: codex chosen=codex switch=none"
HOSTILE = 'agent "quoted" \\\n## [H-MAD:MARKER] *?[] Ω\nkind=forged'
BASE_PRODUCTION = ("scripts/tool.sh", "bin/launch", "README.md", "CHANGES.MD")


def gate_env(**extra: str) -> dict[str, str]:
    env = hermetic_env(HMAD_STUB_HOSTILE="all", PYTHONPATH="",
                        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    for name in tuple(env):
        if name.startswith("GIT_"):
            env.pop(name)
    env.update(extra)
    return env


def claude_author_env(**extra: str) -> dict[str, str]:
    env = hermetic_env(HMAD_CODEX_UNAVAILABLE="1", HMAD_AGY_UNAVAILABLE="1",
                       HMAD_STUB_HOSTILE="all", **extra)
    return {key: value for key, value in env.items() if not key.startswith("GIT_")}


def default_authorship_env(bin_dir: Path, **extra: str) -> dict[str, str]:
    env = hermetic_env(HMAD_STUB_HOSTILE="all", **extra)
    env.pop("HMAD_AGY_UNAVAILABLE", None)
    bin_dir.mkdir(parents=True, exist_ok=True)
    codex = bin_dir / "codex"
    codex.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    codex.chmod(0o755)
    env["PATH"] = str(bin_dir) + os.pathsep + env["PATH"]
    return env


def assert_authorship(env: dict, root: Path, key: str,
                      expected: str = CLAUDE_AUTHOR_LINE) -> None:
    proc = subprocess.run(["python3", str(JUDGE), "implementer", "--root", str(root),
                           "--feature", key], cwd=root, env=env, capture_output=True,
                          text=True, timeout=30, check=False)
    assert proc.returncode == 0, f"implementer arrangement failed: {proc.stderr!r}"
    assert proc.stdout.rstrip("\n") == expected, (
        f"authorship arrangement: expected {expected!r}, received {proc.stdout!r}")


def run_claude(root: Path, target: Path, env: dict, hook: Path = HOOK) -> Outcome:
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(target), "content": "x"}}
    proc = subprocess.run(["/bin/bash", str(hook)], input=json.dumps(payload), cwd=root,
                          env={**env, "CLAUDE_PROJECT_DIR": str(root)}, capture_output=True,
                          text=True, timeout=120, check=False)
    return decision(proc, hook_form(hook))


def stub_tree(tmp: Path, listing_stdout: str, listing_rc: int,
              emit_doc_data_body: str = "") -> Path:
    hook = tmp / "h-mad/hooks/h-mad-tdd-gate.sh"
    hook.parent.mkdir(parents=True)
    shutil.copyfile(HOOK, hook)
    scripts = hook.parents[1] / "scripts"
    scripts.mkdir()
    (scripts / JUDGE.name).write_text(
        "import sys\n"
        "if sys.argv[1] == 'listing':\n"
        f" sys.stdout.write({listing_stdout!r})\n sys.exit({listing_rc})\n"
        "if sys.argv[1] == 'state':\n print('TDD-STATE: none')\n",
        encoding="utf-8")
    identity = JUDGE.with_name("h_mad_target_identity.py").read_text(encoding="utf-8")
    if emit_doc_data_body:
        identity += "\n\ndef emit_doc_data(record):\n" + emit_doc_data_body + "\n"
    (scripts / "h_mad_target_identity.py").write_text(identity, encoding="utf-8")
    return hook


def write_file(root: Path, relative: str, body: str = "x\n") -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def task_text(number: int, production: tuple[str, ...], test: str) -> str:
    entries = ", ".join(f"`{name}`" for name in production)
    return (f"## Task {number}: agent input\n{HOSTILE}\n"
            "<!-- human note: **not a field**\nsecond line -->\n"
            "**Task shape**: `new-behaviour`\n"
            f"**Production file**: {entries}\n**Test file**: `{test}`\n")


def set_test_state(root: Path, test_state: str, relative: str = "tests/test_tool.py") -> None:
    assert test_state in {"absent", "passing", "failing"}
    if test_state == "absent":
        (root / relative).unlink(missing_ok=True)
        return
    write_file(root, relative,
               f"def test_tool():\n    assert {test_state == 'passing'}\n")
    # A local interpreter makes the verdict independent of python3's pytest.
    if not (root / ".venv").exists():
        build_venv(root / ".venv", with_pytest=True)


def build_fixture(root: Path, test_state: str) -> Path:
    root.mkdir(parents=True)
    root = root.resolve()
    proc = subprocess.run(["git", "init", "--quiet", str(root)], env=gate_env(),
                          capture_output=True, text=True, timeout=10, check=False)
    assert proc.returncode == 0, f"scratch git init failed: {proc.stderr}"
    (root / ".agents").mkdir()
    write_state(root, {"f": {"phase": "step5"}})
    write_plan(root, "f", task_text(1, BASE_PRODUCTION, "tests/test_tool.py"))
    for name in (*BASE_PRODUCTION, "scripts/other.sh"):
        write_file(root, name)
    set_test_state(root, test_state)
    return root


def selection_fixture(root: Path, state: str) -> Path:
    assert state in {"S1", "S2"}
    root = build_fixture(root, "absent")
    os.link(root / "scripts/tool.sh", root / "scripts/hard.sh")
    write_plan(root, "f", task_text(1, BASE_PRODUCTION, "tests/test_tool.py")
               + task_text(2, ("scripts/hard.sh",), "tests/test_hard.py"))
    set_test_state(root, "failing", "tests/test_hard.py" if state == "S1"
                   else "tests/test_tool.py")
    return root


def two_record_fixture(root: Path, listed: bool) -> Path:
    root = build_fixture(root, "absent")
    os.link(root / "scripts/tool.sh", root / "scripts/hard.sh")
    write_state(root, {"f": {"phase": "step5"}, "g": {"phase": "step5"}})
    production = "scripts/tool.sh" if listed else "scripts/other.sh"
    write_plan(root, "f", task_text(1, (production,), "tests/test_tool.py"))
    write_plan(root, "g", "").write_bytes(b"\xff\xfe")
    return root


def later_plan_fixture(root: Path, test_state: str) -> Path:
    """Two active records, both plans readable: f lists other.sh, g lists tool.sh."""
    root = build_fixture(root, test_state)
    write_state(root, {"f": {"phase": "step5"}, "g": {"phase": "step5"}})
    write_plan(root, "f", task_text(1, ("scripts/other.sh",), "tests/test_other.py"))
    write_plan(root, "g", task_text(1, ("scripts/tool.sh",), "tests/test_tool.py"))
    return root


def newline_name_fixture(root: Path, test_state: str) -> Path:
    root = build_fixture(root, test_state)
    write_file(root, "scripts/tool\n")
    (root / "scripts/alias.sh").symlink_to("tool\n")
    write_plan(root, "f", task_text(1, ("scripts/alias.sh",), "tests/test_tool.py"))
    return root


def member_fixture(root: Path, lower: str, upper: str) -> Path:
    root = build_fixture(root, "absent")
    for name in (lower, upper):
        write_file(root, name)
    write_plan(root, "f", task_text(1, (lower, upper), "tests/test_tool.py"))
    return root


def skip_unless_case_insensitive(directory: Path) -> None:
    probe = directory / "a"
    probe.touch()
    try:
        folds = os.path.exists(directory / "A")
    finally:
        probe.unlink()
    if not folds:
        pytest.skip("requires a case-insensitive volume")


def run_codex(root: Path, relative: str, env: dict, *, add: bool = False) -> Outcome:
    # A second update header in relative drives the real multi-target parser.
    # add=True writes the Add File form, whose body is "+" lines with no hunk.
    if add:
        patch = f"*** Begin Patch\n*** Add File: {relative}\n+x\n*** End Patch\n"
    else:
        patch = f"*** Begin Patch\n*** Update File: {relative}\n@@\n-x\n+y\n*** End Patch\n"
    payload = {"tool_name": "apply_patch", "tool_input": {"command": patch}, "cwd": str(root)}
    clean_env = {k: v for k, v in env.items() if not k.startswith("GIT_")}
    proc = subprocess.run(["python3", str(CODEX_GATE)], input=json.dumps(payload),
                          cwd=root, env=clean_env, capture_output=True, text=True,
                          timeout=60, check=False)
    result = decision(proc, "b")
    match = re.search(r"\bkind=([a-z-]+)", result.reason)
    return Outcome(result.decision, match.group(1) if match else result.kind,
                   result.reason, result.rc)


def run_agy(root: Path, relative: str, env: dict) -> dict:
    payload = {"toolCall": {"name": "write_to_file",
                            "args": {"TargetFile": str(root / relative)}},
               "workspacePaths": [str(root)]}
    clean_env = {k: v for k, v in env.items() if not k.startswith("GIT_")}
    proc = subprocess.run(["python3", str(AGY_GATE)], input=json.dumps(payload),
                          cwd=root / ".agents", env=clean_env,
                          capture_output=True, text=True, timeout=60, check=False)
    assert proc.returncode == 0, f"agy hook protocol must exit zero: {proc.stderr!r}"
    result = json.loads(proc.stdout)
    assert isinstance(result, dict), f"agy hook must emit one decision object: {result!r}"
    assert result.get("decision") in {"allow", "deny"}, f"invalid agy decision: {result!r}"
    return result
