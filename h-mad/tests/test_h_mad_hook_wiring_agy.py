"""FR-5: distinguish agy wiring verdicts from unreadable configuration.

CLI assertions check stdout before the exit code: argparse's rejection of an
unimplemented --agy also exits 2, but is never an UNREADABLE wiring verdict.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "h-mad" / "scripts" / "h_mad_hook_wiring.py"
GATE = REPO_ROOT / "h-mad" / "hooks" / "h-mad-agy-tdd-gate.py"
ORCA_STUB = REPO_ROOT / "h-mad" / "tests" / "stubs" / "orca"
HOOK_NAME = "h-mad-agy-tdd-gate"
COMMAND = "python3 ~/.gemini/config/skills/h-mad/hooks/h-mad-agy-tdd-gate.py"

sys.path.insert(0, str(SCRIPT.parent))
import h_mad_hook_wiring as hw  # noqa: E402
import h_mad_tdd_judge  # noqa: E402


@pytest.fixture
def agy_project(tmp_path, monkeypatch):
    # Consume the shared hostile knob rather than giving paths tidy ASCII names.
    stub_env = {k: v for k, v in os.environ.items()
                if not k.startswith("HMAD_STUB_")}
    stub_env["HMAD_STUB_HOSTILE"] = "all"
    payload = subprocess.run(
        ["/bin/bash", str(ORCA_STUB), "worktree", "set", "--comment", "fixture"],
        env=stub_env, capture_output=True, text=True, timeout=10, check=True,
    )
    hostile = json.loads(payload.stdout)["result"]["worktree"]["comment"]
    # Keep shell/glob/markdown/newline/Unicode payloads, but no slash or colon
    # inside a component (in particular, no colon inside a PATH entry).
    component = hostile.replace("/", "_").replace(":", "-") + " #100%"
    root = tmp_path / ("project " + component)
    home = tmp_path / ("home " + component)
    root.mkdir()
    installed_gate = home / ".gemini/config/skills/h-mad/hooks" / GATE.name
    installed_gate.parent.mkdir(parents=True)
    installed_gate.symlink_to(GATE)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    (bindir / "python3").symlink_to(sys.executable)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PATH", os.pathsep.join((str(bindir), "/usr/bin", "/bin")))
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    return root, bindir, hostile


def _config():
    return {HOOK_NAME: {
        "enabled": True,
        "PreToolUse": [{"matcher": "*", "hooks": [{
            "type": "command", "command": COMMAND, "timeout": 60,
        }]}],
    }}


def _write_hooks(root, config):
    path = root / ".agents" / "hooks.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def _run(root):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--agy", "--project-root", str(root)],
        cwd=root, env=os.environ.copy(), capture_output=True, text=True,
        timeout=40, check=False,
    )


@pytest.mark.parametrize("case, reason", [
    pytest.param("no-hooks-file", "no-hooks-file", id="no-hooks-file"),
    pytest.param("no-entry", "no-entry", id="no-entry"),
    pytest.param("entry-not-object", "no-entry", id="entry-not-object"),
    pytest.param("disabled", "disabled", id="disabled"),
    pytest.param("matcher-narrow", "matcher-narrow", id="matcher-narrow"),
    pytest.param("pretooluse-absent", "matcher-narrow", id="pretooluse-absent"),
    pytest.param("bad-command", "bad-command", id="bad-command"),
    pytest.param("timeout-below-floor", "timeout-below-floor", id="timeout-below-floor"),
    pytest.param("timeout-absent", "timeout-below-floor", id="timeout-absent"),
    pytest.param("self-check-failed", "self-check-failed", id="self-check-failed"),
])
def test_unwired_reason(agy_project, case, reason):
    root, bindir, hostile = agy_project
    config = _config()
    entry = config[HOOK_NAME]
    group = entry["PreToolUse"][0]
    handler = group["hooks"][0]
    if case == "no-entry":
        # A correct sibling entry must not substitute for the required name.
        config = {"sibling " + hostile: entry}
    elif case == "entry-not-object":
        config[HOOK_NAME] = [entry]
    elif case == "disabled":
        entry["enabled"] = False
    elif case == "matcher-narrow":
        group["matcher"] = "write_to_file"
    elif case == "pretooluse-absent":
        entry["PostToolUse"] = entry.pop("PreToolUse")
    elif case == "bad-command":
        # A basename match or substring search must not accept extra shell text.
        handler["command"] = COMMAND + " ; " + hostile
    elif case == "timeout-below-floor":
        handler["timeout"] = 59
    elif case == "timeout-absent":
        del handler["timeout"]
    elif case == "self-check-failed":
        # A failed self-check is a verdict that can exit 0. Checking rc alone
        # would incorrectly declare this hook WIRED. Keep HOME's real symlink.
        python = bindir / "python3"
        python.unlink()
        python.write_text(
            "#!/bin/sh\nprintf '%s\\n' 'AGY-TDD-GATE: FAIL classification'\nexit 0\n",
            encoding="utf-8",
        )
        python.chmod(0o755)
    if case != "no-hooks-file":
        _write_hooks(root, config)

    process = _run(root)
    assert process.stdout == f"AGY-GATE: UNWIRED reason={reason}\n", (
        f"--agy must report exactly the {reason} verdict for {case}; "
        f"stderr={process.stderr!r}"
    )
    assert process.returncode == 0, f"{case} is an UNWIRED verdict and must exit 0"


@pytest.mark.parametrize("contents, error", [
    pytest.param("{not json", "JSONDecodeError", id="not-json"),
    pytest.param("[]", "not-an-object", id="not-an-object"),
])
def test_unreadable_hooks_file(agy_project, contents, error):
    root, _, _ = agy_project
    path = _write_hooks(root, _config())
    path.write_text(contents, encoding="utf-8")

    process = _run(root)
    expected = f"AGY-GATE: UNREADABLE file={quote(str(path), safe='')} error={error}\n"
    assert process.stdout == expected, (
        f"--agy must emit one UNREADABLE line with the percent-encoded path "
        f"and error={error}; stderr={process.stderr!r}"
    )
    assert process.returncode == 2, f"unreadable {error} configuration must exit 2"


def test_wired(agy_project):
    root, _, _ = agy_project
    _write_hooks(root, _config())

    process = _run(root)
    assert process.stdout == "AGY-GATE: WIRED\n", (
        f"--agy must accept the healthy entry after the real gate's self-check; "
        f"stderr={process.stderr!r}"
    )
    assert process.returncode == 0, "WIRED must exit 0"


@pytest.mark.parametrize("budget, timeout, expected", [
    pytest.param(40.0, 59, "AGY-GATE: UNWIRED reason=timeout-below-floor",
                 id="budget-40-timeout-59"),
    pytest.param(40.0, 60, "AGY-GATE: WIRED", id="budget-40-timeout-60"),
    pytest.param(41.1, 61, "AGY-GATE: UNWIRED reason=timeout-below-floor",
                 id="budget-41.1-timeout-61"),
    pytest.param(41.1, 62, "AGY-GATE: WIRED", id="budget-41.1-timeout-62"),
])
def test_timeout_floor_is_derived_from_the_judge_budget(
    agy_project, monkeypatch, budget, timeout, expected,
):
    root, _, _ = agy_project
    monkeypatch.setattr(h_mad_tdd_judge, "JUDGE_BUDGET_S", budget)
    config = _config()
    config[HOOK_NAME]["PreToolUse"][0]["hooks"][0]["timeout"] = timeout
    _write_hooks(root, config)

    line, code = hw.check_agy(root)
    assert line == expected, (
        f"check_agy must read the live judge budget {budget} and ceil(budget + 20) "
        f"when judging timeout {timeout}"
    )
    assert code == 0, "both WIRED and timeout-below-floor are verdicts with exit 0"


def test_empty_matcher_counts_as_wide(agy_project):
    root, _, _ = agy_project
    config = _config()
    # The enabled field is optional; the empty matcher still covers every tool.
    del config[HOOK_NAME]["enabled"]
    config[HOOK_NAME]["PreToolUse"][0]["matcher"] = ""
    _write_hooks(root, config)

    process = _run(root)
    assert process.stdout == "AGY-GATE: WIRED\n", (
        f"--agy must treat the empty matcher as wide and default enabled to true; "
        f"stderr={process.stderr!r}"
    )
    assert process.returncode == 0, "a wide empty matcher must produce a WIRED exit 0"
