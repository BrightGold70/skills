"""Host declaration values retain their exact spelling and whitespace."""

import importlib
import json
from pathlib import Path
import re
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BUDGET = REPO_ROOT / "h-mad" / "scripts" / "h_mad_context_budget.py"


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


def _budget_transcript(tmp_path, *, usage=True):
    home = tmp_path / "home"
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(tmp_path))
    project = home / ".claude" / "projects" / slug
    project.mkdir(parents=True, exist_ok=True)
    transcript = project / "session.jsonl"
    if usage:
        record = {
            "isSidechain": False,
            "type": "assistant",
            "message": {"usage": {
                "input_tokens": 1_000,
                "cache_creation_input_tokens": 2_000,
                "cache_read_input_tokens": 3_000,
                "output_tokens": 999,
            }},
        }
    else:
        record = {"type": "user", "message": {}}
    transcript.write_text(json.dumps(record) + "\n")
    return transcript


def _run_budget(tmp_path, hermetic_env, value, *args):
    env = hermetic_env(
        HOME=str(tmp_path / "home"),
        HMAD_HOST=value,
        HMAD_STUB_HOSTILE="all",
    )
    return subprocess.run(
        [sys.executable, str(BUDGET), *args],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60.0,
    )


@pytest.mark.parametrize("value", ["codex", "agy", "grok"])
def test_budget_host_unsupported_valid_transcript(tmp_path, hermetic_env, value):
    transcript = _budget_transcript(tmp_path)
    result = _run_budget(tmp_path, hermetic_env, value, "--transcript", str(transcript))
    assert result.stdout == f"CTXBUDGET: UNKNOWN reason=host_unsupported host={value}\n"
    assert result.returncode == 2
    assert "used=" not in result.stdout


@pytest.mark.parametrize("value", ["codex", "agy", "grok"])
def test_budget_host_check_precedes_transcript_lookup(tmp_path, hermetic_env, value):
    absent = tmp_path / "absent.jsonl"
    result = _run_budget(tmp_path, hermetic_env, value, "--transcript", str(absent))
    assert result.stdout == f"CTXBUDGET: UNKNOWN reason=host_unsupported host={value}\n"
    assert result.returncode == 2
    assert "used=" not in result.stdout


@pytest.mark.parametrize("value", ["codex", "agy", "grok"])
def test_budget_host_check_precedes_usage_read(tmp_path, hermetic_env, value):
    transcript = _budget_transcript(tmp_path, usage=False)
    result = _run_budget(tmp_path, hermetic_env, value, "--transcript", str(transcript))
    assert result.stdout == f"CTXBUDGET: UNKNOWN reason=host_unsupported host={value}\n"
    assert result.returncode == 2
    assert "used=" not in result.stdout


@pytest.mark.parametrize("value", ["codex", "agy", "grok"])
def test_budget_host_check_precedes_window_check(tmp_path, hermetic_env, value):
    transcript = _budget_transcript(tmp_path)
    result = _run_budget(
        tmp_path, hermetic_env, value, "--transcript", str(transcript), "--window", "0"
    )
    assert result.stdout == f"CTXBUDGET: UNKNOWN reason=host_unsupported host={value}\n"
    assert result.returncode == 2
    assert "used=" not in result.stdout


@pytest.mark.parametrize(
    ("value", "shown"),
    [
        pytest.param("zzz", "zzz", id="zzz"),
        pytest.param("Grok", "Grok", id="Grok"),
        pytest.param(" grok", '" grok"', id="space-grok"),
        pytest.param("zzz\n", '"zzz\\n"', id="zzz-newline"),
    ],
)
def test_budget_unknown_host_encoding(tmp_path, hermetic_env, value, shown):
    transcript = _budget_transcript(tmp_path)
    result = _run_budget(tmp_path, hermetic_env, value, "--transcript", str(transcript))
    assert result.stdout == f"CTXBUDGET: UNKNOWN reason=unknown_host host={shown}\n"
    assert result.returncode == 2
    assert "used=" not in result.stdout


@pytest.mark.parametrize("value", ["zzz"])
def test_budget_unknown_host_precedes_window_check(tmp_path, hermetic_env, value):
    transcript = _budget_transcript(tmp_path)
    result = _run_budget(
        tmp_path, hermetic_env, value, "--transcript", str(transcript), "--window", "0"
    )
    assert result.stdout == f"CTXBUDGET: UNKNOWN reason=unknown_host host={value}\n"
    assert result.returncode == 2
    assert "used=" not in result.stdout
