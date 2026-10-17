"""Agent selection and timeout wiring for the Phase 5 TDD assembler."""
from __future__ import annotations

import hashlib
import inspect
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import Mock
from urllib.parse import quote

import pytest

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "h_mad_assemble_tdd.py"
sys.path.insert(0, str(SCRIPT.parent))

from h_mad_assemble_tdd import command_block  # noqa: E402
import h_mad_assemble_tdd as assemble_mod  # noqa: E402

BASE_SHA = "8ef6009f"
PLAN = """# Feature implementation plan

## Task 1: hostile-agent-input

- **Task shape**: new-behaviour
**Production**: `pkg/agent.py`

Human text: **[brackets]** `$(printf unsafe)` ===HMAD-DISPATCH-BOUNDARY===
"""
FEATURE = "feature '$(printf unsafe)' [x]"
MODULE = 'pkg/agent "quoted".py'
TEST_PATH = "tests/test [x]$(printf unsafe).py"
AGY_COMMAND = "python3 ~/.gemini/config/skills/h-mad/hooks/h-mad-agy-tdd-gate.py"
AGY_HALT = "ASSEMBLE-TDD: HALT agy_tdd_hook_unverified"
AGY_MARKER = f"[H-MAD] {FEATURE} tdd-assemble halt agy_tdd_hook_unverified Task 1"


@pytest.fixture()
def agy_env(tmp_path: Path) -> dict[str, str]:
    stub_env = {k: v for k, v in os.environ.items() if not k.startswith("HMAD_STUB_")}
    stub_env["HMAD_STUB_HOSTILE"] = "all"
    result = subprocess.run(
        ["/bin/bash", str(SKILL_DIR / "tests/stubs/orca"),
         "worktree", "set", "--comment", "fixture"],
        env=stub_env, capture_output=True, text=True, timeout=10, check=True,
    )
    hostile = json.loads(result.stdout)["result"]["worktree"]["comment"]
    component = hostile.replace("/", "_").replace(":", "-")
    home = tmp_path / ("home " + component)
    gate = home / ".gemini/config/skills/h-mad/hooks/h-mad-agy-tdd-gate.py"
    gate.parent.mkdir(parents=True)
    gate.symlink_to(SKILL_DIR / "hooks/h-mad-agy-tdd-gate.py")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    (bindir / "python3").symlink_to(sys.executable)
    return {
        "HOME": str(home),
        "PATH": os.pathsep.join((str(bindir), "/usr/bin", "/bin")),
        "HMAD_STUB_HOSTILE": "all",
    }


def agy_hooks() -> dict:
    return {"h-mad-agy-tdd-gate": {
        "enabled": True,
        "PreToolUse": [{"matcher": "*", "hooks": [{
            "type": "command", "command": AGY_COMMAND, "timeout": 60,
        }]}],
    }}


def write_agy_hooks(root: Path, config: dict) -> Path:
    hooks = root / ".agents/hooks.json"
    hooks.parent.mkdir(exist_ok=True)
    hooks.write_text(json.dumps(config), encoding="utf-8")
    return hooks


def run_main(plan: Path, root: Path, prompt: Path) -> int:
    try:
        return assemble_mod.main([
            "--feature", FEATURE, "--task", "Task 1", "--phase", "red",
            "--project-root", str(root), "--module", MODULE,
            "--test-path", TEST_PATH, "--impl-plan", str(plan),
            "--expect-fail", "9", "--expect-pass", "2",
            "--python", sys.executable, "--prompt", str(prompt),
            "--agent", "agy",
        ])
    except SystemExit as exc:
        return exc.code


@pytest.fixture()
def plan(tmp_path: Path) -> Path:
    path = tmp_path / "hostile.impl-plan.md"
    path.write_text(PLAN, encoding="utf-8")
    return path


def run_cli(
    script: Path, plan: Path, root: Path, prompt: Path, *extra: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    run_env["HMAD_STUB_HOSTILE"] = "all"
    if env is not None:
        run_env.update(env)
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
        capture_output=True, text=True, env=run_env,
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
        # From the repository root: pytest may run from h-mad/ (the mutation
        # harness does), where the pathspec `h-mad` matches nothing.
        cwd=Path(__file__).resolve().parents[2],
        check=True, capture_output=True, stdin=subprocess.DEVNULL, timeout=60.0,
    ).stdout
    subprocess.run(
        ["tar", "-x", "-C", str(checkout)],
        input=archive, check=True, capture_output=True,
    )
    base_skill = checkout / "h-mad"
    prompt = tmp_path / "prompt.txt"
    # Both runs render the base template: the pin is on the script's no-agent
    # behaviour, and a later edit to the template's prose is not a change to it.
    template = ("--template", str(base_skill / "references" / "codex-implementer-prompt.md"))
    base = run_cli(base_skill / "scripts" / SCRIPT.name, plan, tmp_path, prompt, *template)
    assert base.returncode == 0, base.stdout + base.stderr
    base_prompt = prompt.read_bytes()
    current = run_cli(SCRIPT, plan, tmp_path, prompt, *template)
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


def test_prompt_file_is_agent_independent(
    plan: Path, tmp_path: Path, agy_env: dict[str, str]
) -> None:
    write_agy_hooks(tmp_path, agy_hooks())
    hashes = []
    for agent in ("codex", "grok", "agy"):
        prompt = tmp_path / f"{agent}.prompt.txt"
        proc = run_cli(SCRIPT, plan, tmp_path, prompt, "--agent", agent, env=agy_env)
        assert prompt.is_file(), (
            f"--agent {agent} must stage a prompt independently: {proc.stderr or proc.stdout}"
        )
        hashes.append(hashlib.sha256(prompt.read_bytes()).hexdigest())
    assert len(hashes) == 3 and len(set(hashes)) == 1, (
        "codex, grok and agy must produce identical prompt file bytes"
    )


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


def test_agent_agy_runs_the_wiring_check_before_assembling(
    plan: Path, tmp_path: Path, monkeypatch, capsys,
) -> None:
    record = tmp_path / "check.argv.json"
    stub = tmp_path / "wiring-check.py"
    stub.write_text(
        "import json, sys\nfrom pathlib import Path\n"
        f"Path({str(record)!r}).write_text(json.dumps(sys.argv[1:]))\n"
        "print('AGY-GATE: UNWIRED reason=no-entry')\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    monkeypatch.setattr(assemble_mod, "AGY_WIRING_CHECK", str(stub), raising=False)
    assemble_spy = Mock(wraps=assemble_mod.assemble)
    monkeypatch.setattr(assemble_mod, "assemble", assemble_spy)
    prompt = tmp_path / "prompt.txt"

    code = run_main(plan, tmp_path, prompt)
    stdout = capsys.readouterr().out

    assert record.is_file(), "main must run the agy wiring check before assembling"
    assert json.loads(record.read_text()) == ["--agy", "--project-root", str(tmp_path)], (
        "main must pass --agy and the selected project root to the wiring checker"
    )
    assert not assemble_spy.called, "main must halt on UNWIRED before calling assemble"
    assert stdout.splitlines() == [
        AGY_HALT, "  AGY-GATE: UNWIRED reason=no-entry", AGY_MARKER,
    ], "main must print the HALT, indented check token and marker in order"
    assert not prompt.exists(), "UNWIRED must halt before staging a prompt"
    assert code == 0, "UNWIRED is a verdict and must exit 0"


@pytest.mark.parametrize("reason", [
    "no-hooks-file", "no-entry", "disabled", "matcher-narrow", "bad-command",
    "timeout-below-floor", "self-check-failed",
])
def test_agent_agy_unwired_halts_with_exit_0(
    plan: Path, tmp_path: Path, agy_env: dict[str, str], reason: str,
) -> None:
    config = agy_hooks()
    entry = config["h-mad-agy-tdd-gate"]
    group = entry["PreToolUse"][0]
    handler = group["hooks"][0]
    if reason == "no-entry":
        config = {}
    elif reason == "disabled":
        entry["enabled"] = False
    elif reason == "matcher-narrow":
        group["matcher"] = "write_to_file"
    elif reason == "bad-command":
        handler["command"] = AGY_COMMAND + " ; " + FEATURE
    elif reason == "timeout-below-floor":
        handler["timeout"] = 59
    elif reason == "self-check-failed":
        python = tmp_path / "bin/python3"
        python.unlink()
        python.write_text(
            "#!/bin/sh\nprintf '%s\\n' 'AGY-TDD-GATE: FAIL classification'\nexit 0\n",
            encoding="utf-8",
        )
        python.chmod(0o755)
    if reason != "no-hooks-file":
        write_agy_hooks(tmp_path, config)
    prompt = tmp_path / "prompt.txt"

    proc = run_cli(SCRIPT, plan, tmp_path, prompt, "--agent", "agy", env=agy_env)

    lines = proc.stdout.splitlines()
    assert lines[:1] == [AGY_HALT], f"{reason} must print the agy wiring HALT first"
    assert lines[1:2] == [f"  AGY-GATE: UNWIRED reason={reason}"], (
        f"main must preserve and indent the {reason} checker verdict"
    )
    assert lines[2:] == [AGY_MARKER], "the halt marker must follow the check token"
    assert proc.returncode == 0, f"UNWIRED {reason} must exit 0"
    assert not prompt.exists(), f"UNWIRED {reason} must not stage a prompt"


def test_agent_agy_unreadable_halts_with_exit_2(
    plan: Path, tmp_path: Path, agy_env: dict[str, str],
) -> None:
    hooks = write_agy_hooks(tmp_path, agy_hooks())
    hooks.write_text("{not JSON", encoding="utf-8")
    prompt = tmp_path / "prompt.txt"

    proc = run_cli(SCRIPT, plan, tmp_path, prompt, "--agent", "agy", env=agy_env)

    lines = proc.stdout.splitlines()
    assert lines[:1] == [AGY_HALT], "unreadable hooks must print the agy wiring HALT"
    assert lines[1:2] == [
        f"  AGY-GATE: UNREADABLE file={quote(str(hooks), safe='')} error=JSONDecodeError",
    ], "main must preserve and indent the UNREADABLE checker token"
    assert lines[2:] == [AGY_MARKER], "the halt marker must follow the unreadable token"
    assert proc.returncode == 2, "UNREADABLE must exit 2"
    assert not prompt.exists(), "UNREADABLE must not stage a prompt"


def test_agent_agy_no_token_halts_with_exit_2(
    plan: Path, tmp_path: Path, monkeypatch, capsys,
) -> None:
    stub = tmp_path / "silent-check.py"
    stub.write_text("pass\n", encoding="utf-8")
    monkeypatch.setattr(assemble_mod, "AGY_WIRING_CHECK", str(stub), raising=False)
    prompt = tmp_path / "prompt.txt"

    code = run_main(plan, tmp_path, prompt)

    assert capsys.readouterr().out.splitlines() == [
        AGY_HALT + " check=no-token", AGY_MARKER,
    ], "a checker with no token must print the no-token HALT then the marker"
    assert code == 2, "a checker with no token must exit 2"
    assert not prompt.exists(), "a checker with no token must not stage a prompt"


def test_agent_agy_check_timeout_halts_with_exit_2(
    plan: Path, tmp_path: Path, monkeypatch, capsys,
) -> None:
    stub = tmp_path / "slow-check.py"
    stub.write_text("import time\ntime.sleep(5)\n", encoding="utf-8")
    monkeypatch.setattr(assemble_mod, "AGY_WIRING_CHECK", str(stub), raising=False)
    monkeypatch.setattr(assemble_mod, "AGY_WIRING_TIMEOUT_S", 1, raising=False)
    prompt = tmp_path / "prompt.txt"
    started = time.monotonic()

    code = run_main(plan, tmp_path, prompt)

    assert capsys.readouterr().out.splitlines() == [
        AGY_HALT + " check=no-token", AGY_MARKER,
    ], "a checker timeout must print the no-token HALT then the marker"
    assert code == 2, "a checker timeout must exit 2"
    assert time.monotonic() - started < 4, "main must enforce the 1 second check bound"
    assert not prompt.exists(), "a checker timeout must not stage a prompt"


def test_agent_agy_wired_writes_the_prompt(
    plan: Path, tmp_path: Path, agy_env: dict[str, str],
) -> None:
    write_agy_hooks(tmp_path, agy_hooks())
    prompt = tmp_path / "prompt.txt"

    proc = run_cli(SCRIPT, plan, tmp_path, prompt, "--agent", "agy", env=agy_env)

    assert proc.stdout.startswith("ASSEMBLE-TDD: PASS "), "WIRED must allow assembly"
    assert proc.returncode == 0, "WIRED assembly must exit 0"
    assert prompt.is_file(), "WIRED must stage the prompt"
    assert first_dispatch_line(proc).startswith("hmad-dispatch exec agy "), (
        "WIRED must dispatch the selected agy agent"
    )
    assert "--timeout 1500" in proc.stdout, "agy must default to 1500 seconds"


@pytest.mark.parametrize("agent, timeout", [
    ("codex", 900), ("grok", 1500), ("agy", 1500),
], ids=["codex-900", "grok-1500", "agy-1500"])
def test_agent_default_timeouts(
    plan: Path, tmp_path: Path, agy_env: dict[str, str], agent: str, timeout: int,
) -> None:
    write_agy_hooks(tmp_path, agy_hooks())
    proc = run_cli(
        SCRIPT, plan, tmp_path, tmp_path / "prompt.txt", "--agent", agent, env=agy_env,
    )

    assert f"--timeout {timeout}" in proc.stdout, (
        f"main must select the {timeout} second default for {agent}: {proc.stderr}"
    )
    assert proc.returncode == 0, f"the {agent} default timeout must allow assembly"


def test_docstring_states_the_agy_halt_exit_rule() -> None:
    doc = " ".join(assemble_mod.__doc__.split())
    expected = (
        "exit 0 on PASS and on HALT agy_tdd_hook_unverified after AGY-GATE: UNWIRED; "
        "2 on every other HALT"
    )
    assert expected in doc, "the module docstring must state the agy UNWIRED exit-0 rule"


def test_docstring_drops_the_any_halt_rule() -> None:
    doc = " ".join(assemble_mod.__doc__.split())
    assert "2 on any HALT" not in doc, "the docstring must drop the obsolete any-HALT exit rule"
