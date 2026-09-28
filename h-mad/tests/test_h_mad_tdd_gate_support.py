"""Shared environment support used by H-MAD TDD gate tests."""

import json
import subprocess
import sys

from tdd_gate_support import DROPPED_ENV, hermetic_env


def test_hermetic_env_drops_claude_names_and_backend(monkeypatch) -> None:
    values = {
        "CLAUDE_ZZZ_PROBE": "1",
        "CLAUDE_PROJECT_DIR": "/nowhere",
        "HPW_AGENT_BACKEND": "claude",
        "HMAD_HOST": "claude",
        "HMAD_CODEX_UNAVAILABLE": "1",
        "CODEX_PROJECT_DIR": "/nowhere",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)

    env = hermetic_env(X="1")
    assert not (values.keys() & env.keys())
    assert env["X"] == "1"
    assert env["PATH"]
    assert hermetic_env(CLAUDE_PROJECT_DIR="/r")["CLAUDE_PROJECT_DIR"] == "/r"

    code = (
        "import json, os; "
        f"dropped = {DROPPED_ENV!r}; "
        "print(json.dumps(sorted(k for k in os.environ "
        "if k.startswith('CLAUDE') or k in dropped)))"
    )
    child = subprocess.run(
        [sys.executable, "-c", code],
        env=hermetic_env(),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=60.0,
        check=False,
    )
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout) == []
