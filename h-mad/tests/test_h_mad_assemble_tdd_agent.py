"""Agent selection and timeout wiring for the Phase 5 TDD assembler."""
from __future__ import annotations

import hashlib
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "h_mad_assemble_tdd.py"
sys.path.insert(0, str(SCRIPT.parent))

from h_mad_assemble_tdd import command_block  # noqa: E402

BASE_SHA = "507214d"
PLAN = """# Feature implementation plan

## Task 1: hostile-agent-input

- **Task shape**: new-behaviour
**Production**: `pkg/agent.py`

Human text: **[brackets]** `$(printf unsafe)` ===HMAD-DISPATCH-BOUNDARY===
"""
FEATURE = "feature '$(printf unsafe)' [x]"
MODULE = 'pkg/agent "quoted".py'
TEST_PATH = "tests/test [x]$(printf unsafe).py"


@pytest.fixture()
def plan(tmp_path: Path) -> Path:
    path = tmp_path / "hostile.impl-plan.md"
    path.write_text(PLAN, encoding="utf-8")
    return path


def run_cli(
    script: Path, plan: Path, root: Path, prompt: Path, *extra: str
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HMAD_STUB_HOSTILE"] = "all"
    return subprocess.run(
        [
            sys.executable, str(script),
            "--feature", FEATURE, "--task", "Task 1", "--phase", "red",
            "--project-root", str(root), "--module", MODULE,
            "--test-path", TEST_PATH, "--impl-plan", str(plan),
            "--expect-fail", "9", "--expect-pass", "2",
            "--python", sys.executable, "--prompt", str(prompt),
            "--out", str(root / "dispatch.out"),
            "--log", str(root / "dispatch.log"),
            *extra,
        ],
        capture_output=True, text=True, env=env,
    )


def first_dispatch_line(proc: subprocess.CompletedProcess[str]) -> str:
    return next(
        (line for line in proc.stdout.splitlines()
         if line.startswith("hmad-dispatch exec ")),
        "",
    )


def test_no_agent_output_is_byte_identical_to_base(
    plan: Path, tmp_path: Path
) -> None:
    checkout = tmp_path / "base"
    checkout.mkdir()
    archive = subprocess.run(
        ["git", "archive", BASE_SHA, "h-mad"],
        check=True, capture_output=True,
    ).stdout
    subprocess.run(
        ["tar", "-x", "-C", str(checkout)],
        input=archive, check=True, capture_output=True,
    )
    base_skill = checkout / "h-mad"
    prompt = tmp_path / "prompt.txt"
    base = run_cli(base_skill / "scripts" / SCRIPT.name, plan, tmp_path, prompt)
    assert base.returncode == 0, base.stdout + base.stderr
    base_prompt = prompt.read_bytes()
    current = run_cli(SCRIPT, plan, tmp_path, prompt)
    assert current.returncode == 0, current.stdout + current.stderr
    assert current.stdout == base.stdout.replace(str(base_skill), str(SKILL_DIR)), (
        "no-agent stdout must be byte-identical to the base after its SKILL_DIR replacement"
    )
    assert prompt.read_bytes() == base_prompt, "no-agent prompt must match the base bytes"


def test_agent_grok_block_names_exec_grok_with_1500(
    plan: Path, tmp_path: Path
) -> None:
    proc = run_cli(SCRIPT, plan, tmp_path, tmp_path / "prompt.txt", "--agent", "grok")
    dispatch = first_dispatch_line(proc)
    assert dispatch.startswith("hmad-dispatch exec grok "), (
        f"main must pass --agent grok to command_block: {proc.stderr or proc.stdout}"
    )
    assert "--timeout 1500" in proc.stdout, "grok must default to a 1500 second timeout"


@pytest.mark.parametrize(
    ("timeout_args", "expected"),
    [
        (("--timeout", "600"), 600),
        (("--timeout", "900"), 900),
        (("--timeout=900",), 900),
        (("--ti", "900"), 900),
    ],
    ids=["--timeout 600", "--timeout 900", "--timeout=900", "--ti 900"],
)
def test_agent_grok_explicit_timeout_wins(
    plan: Path, tmp_path: Path, timeout_args: tuple[str, ...], expected: int
) -> None:
    proc = run_cli(
        SCRIPT, plan, tmp_path, tmp_path / "prompt.txt",
        "--agent", "grok", *timeout_args,
    )
    assert f"--timeout {expected}" in proc.stdout, (
        f"explicit timeout {expected} must override grok default: {proc.stderr or proc.stdout}"
    )
    assert "--timeout 1500" not in proc.stdout, "explicit timeout must suppress grok default"


def test_agent_codex_default_timeout_is_900(plan: Path, tmp_path: Path) -> None:
    proc = run_cli(SCRIPT, plan, tmp_path, tmp_path / "prompt.txt", "--agent", "codex")
    assert "--timeout 900" in proc.stdout, (
        f"explicit --agent codex must retain the 900 second default: {proc.stderr or proc.stdout}"
    )


def test_prompt_file_is_agent_independent(plan: Path, tmp_path: Path) -> None:
    hashes = []
    for agent in ("codex", "grok"):
        prompt = tmp_path / f"{agent}.prompt.txt"
        proc = run_cli(SCRIPT, plan, tmp_path, prompt, "--agent", agent)
        assert prompt.is_file(), (
            f"--agent {agent} must stage a prompt independently: {proc.stderr or proc.stdout}"
        )
        hashes.append(hashlib.sha256(prompt.read_bytes()).hexdigest())
    assert hashes[0] == hashes[1], "agent selection must not alter prompt file bytes"


def test_unknown_agent_exits_2_and_writes_no_prompt(plan: Path, tmp_path: Path) -> None:
    prompt = tmp_path / "prompt.txt"
    proc = run_cli(SCRIPT, plan, tmp_path, prompt, "--agent", "gpt")
    assert proc.returncode == 2, "unknown agent must exit with argparse status 2"
    assert "invalid choice: 'gpt'" in proc.stderr, (
        f"unknown agent must be rejected as an invalid choice: {proc.stderr}"
    )
    assert not prompt.exists(), "unknown agent must not write a prompt"


def test_state_fallback_agent_is_not_read(plan: Path, tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / ".bkit-memory.json").write_text(
        json.dumps({"fallback_agent": "grok"}), encoding="utf-8"
    )
    proc = run_cli(SCRIPT, plan, tmp_path, tmp_path / "prompt.txt")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert first_dispatch_line(proc).startswith("hmad-dispatch exec codex "), (
        "state fallback_agent must not change the default dispatch agent"
    )


def test_command_block_derives_grok_from_the_codex_line(tmp_path: Path) -> None:
    args = dict(
        feature=FEATURE, module=MODULE, phase="red",
        prompt=tmp_path / "prompt '$(unsafe)'.txt",
        out=tmp_path / "out.txt", log=tmp_path / "log.txt",
        timeout=1500, python=sys.executable, test_path=TEST_PATH,
        project_root=tmp_path,
    )
    codex = command_block(**args)
    assert "agent" in inspect.signature(command_block).parameters, (
        "command_block must accept an agent selector for the grok derivation"
    )
    grok = command_block(**args, agent="grok")
    codex_lines, grok_lines = codex.splitlines(), grok.splitlines()
    assert grok_lines[0].startswith("hmad-dispatch exec grok "), (
        "command_block must derive the grok first line from the codex line"
    )
    assert grok_lines[1:] == codex_lines[1:], (
        "command_block must leave every line after the dispatch line unchanged"
    )
