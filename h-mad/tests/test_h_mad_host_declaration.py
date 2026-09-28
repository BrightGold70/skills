"""Host declaration values retain their exact spelling and whitespace."""

import importlib
import json
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.fixture
def host(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    return importlib.import_module("h_mad_host")


@pytest.mark.parametrize(
    ("declaration", "expected"),
    [
        pytest.param(None, ("claude", None), id="unset"),
        pytest.param("", ("claude", ""), id="empty"),
        pytest.param("claude", ("claude", "claude"), id="claude"),
        pytest.param("codex", ("declared", "codex"), id="codex"),
        pytest.param("agy", ("declared", "agy"), id="agy"),
        pytest.param("grok", ("declared", "grok"), id="grok"),
        pytest.param("zzz", ("unknown", "zzz"), id="zzz"),
        pytest.param("Grok", ("unknown", "Grok"), id="Grok"),
        pytest.param(" grok", ("unknown", " grok"), id="space-grok"),
    ],
)
def test_classify_host(host, declaration, expected):
    environ = {} if declaration is None else {"HMAD_HOST": declaration}
    assert host.classify_host(environ) == expected, (
        f"classify_host must preserve the exact HMAD_HOST value {declaration!r}"
    )


def test_hermetic_env_drops_claude_names_and_backend(monkeypatch, hermetic_env):
    ambient = {
        "CLAUDE_ZZZ_PROBE": "1",
        "CLAUDECODE": "1",
        "HPW_AGENT_BACKEND": "claude",
        "HMAD_HOST": "grok",
        "HMAD_CONTEXT_WINDOW": "5",
    }
    for name, value in ambient.items():
        monkeypatch.setenv(name, value)

    child_env = hermetic_env(X="1")
    assert not (ambient.keys() & child_env.keys())
    assert child_env["X"] == "1"

    child = subprocess.run(
        [sys.executable, "-c", "import json, os; print(json.dumps(sorted("
         "name for name in os.environ if name.startswith('CLAUDE'))))"],
        env=child_env,
        capture_output=True,
        text=True,
        timeout=60.0,
        check=True,
    )
    assert json.loads(child.stdout) == []
