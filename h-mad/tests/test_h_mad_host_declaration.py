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
RESUME_DECISION = REPO_ROOT / "h-mad" / "scripts" / "h_mad_resume_decision.py"
NOW = "2026-09-28T00:00:00Z"


@pytest.fixture
def host(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    return importlib.import_module("h_mad_host")


@pytest.fixture
def resume_decision(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    return importlib.import_module("h_mad_resume_decision")


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


def test_explicit_host_precedes_environment(host):
    assert host.classify_host({}, explicit_host="codex") == ("declared", "codex")
    assert host.classify_host({"HMAD_HOST": "grok"}, explicit_host="codex") == ("declared", "codex")


def test_unknown_explicit_host_is_refused(host):
    assert host.classify_host({"HMAD_HOST": "claude"}, explicit_host="zzz") == ("unknown", "zzz")
    assert host.classify_host({"HMAD_HOST": "claude"}, explicit_host="") == ("unknown", "")


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


@pytest.mark.parametrize("declaration", [None, "grok"])
def test_budget_host_flag_wins(tmp_path, hermetic_env, declaration):
    env = hermetic_env(HOME=str(tmp_path / "home"))
    if declaration is not None:
        env["HMAD_HOST"] = declaration
    result = subprocess.run(
        [sys.executable, str(BUDGET), "--host", "codex"],
        cwd=tmp_path, env=env, input="", capture_output=True, text=True, timeout=60.0,
    )
    assert result.returncode == 2
    assert result.stdout == "CTXBUDGET: UNKNOWN reason=host_unsupported host=codex\n"


def test_budget_unknown_host_flag_is_refused(tmp_path, hermetic_env):
    result = subprocess.run(
        [sys.executable, str(BUDGET), "--host", "zzz"],
        cwd=tmp_path, env=hermetic_env(HMAD_HOST="claude"), input="",
        capture_output=True, text=True, timeout=60.0,
    )
    assert result.returncode == 2
    assert result.stdout == "CTXBUDGET: UNKNOWN reason=unknown_host host=zzz\n"


def test_resume_host_flag_wins_and_unknown_refuses(tmp_path, hermetic_env):
    state = _resume_state(tmp_path, "no-owner")
    for declaration, flag, expected in (
        (None, "codex", "cannot_judge"),
        ("grok", "claude", "enter_autonomous"),
        ("claude", "zzz", "cannot_judge"),
    ):
        env = hermetic_env()
        if declaration is not None:
            env["HMAD_HOST"] = declaration
        result = subprocess.run(
            [sys.executable, str(RESUME_DECISION), "--state", str(state),
             "--feature", "fx", "--host", flag],
            cwd=tmp_path, env=env, input="", capture_output=True, text=True, timeout=60.0,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == expected


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


def _resume_state(tmp_path, state):
    # The canonical docs/ layout: outside it the oracle answers cannot_judge on the
    # no-record paths by itself (2026-10-07), which would hide a host check moved
    # below them -- the W2a/W2b mutations survived exactly that way.
    (tmp_path / "docs").mkdir(exist_ok=True)
    state_file = tmp_path / "docs" / ".bkit-memory.json"
    if state == "absent-file":
        return state_file
    if state == "unreadable-file":
        state_file.write_text("{", encoding="utf-8")
        return state_file
    feature = "other" if state == "absent-feature" else "fx"
    record = {"last_completed_phase": 4}
    if state == "live-foreign-owner":
        record.update(owner_session_id="sess-other", owner_heartbeat_ts=NOW)
    state_file.write_text(
        json.dumps({"version": 1, "orchestrator_state": {feature: record}}),
        encoding="utf-8",
    )
    return state_file


@pytest.mark.parametrize(
    ("declaration", "expected_unknown"),
    [
        pytest.param(None, False, id="unset"),
        pytest.param("", False, id="empty"),
        pytest.param("claude", False, id="claude"),
        pytest.param("codex", True, id="codex"),
        pytest.param("agy", True, id="agy"),
        pytest.param("grok", True, id="grok"),
        pytest.param("zzz", True, id="zzz"),
        pytest.param("Grok", True, id="Grok"),
        pytest.param(" grok", True, id="space-grok"),
    ],
)
def test_budget_and_decide_agree(
    tmp_path, monkeypatch, hermetic_env, resume_decision, declaration, expected_unknown
):
    if declaration is None:
        monkeypatch.delenv("HMAD_HOST", raising=False)
    else:
        monkeypatch.setenv("HMAD_HOST", declaration)
    monkeypatch.setenv("CLAUDE_ZZZ_PROBE", "1")
    transcript = _budget_transcript(tmp_path)
    budget_env = hermetic_env(HOME=str(tmp_path / "home"), HMAD_STUB_HOSTILE="all")
    if declaration is not None:
        budget_env["HMAD_HOST"] = declaration
    budget = subprocess.run(
        [sys.executable, str(BUDGET), "--transcript", str(transcript)],
        cwd=tmp_path,
        env=budget_env,
        capture_output=True,
        text=True,
        timeout=60.0,
    )
    budget_unknown = (
        "reason=host_unsupported" in budget.stdout
        or "reason=unknown_host" in budget.stdout
    )
    assert budget_unknown is expected_unknown, budget.stdout
    decision = resume_decision.decide(_resume_state(tmp_path, "no-owner"), "fx", now=NOW)
    assert (decision == "cannot_judge") is budget_unknown, (
        f"decide and context budget disagree for HMAD_HOST={declaration!r}: "
        f"decision={decision!r}, budget={budget.stdout!r}"
    )


@pytest.mark.parametrize(
    "state",
    ["live-foreign-owner", "no-owner", "absent-file", "unreadable-file", "absent-feature"],
)
@pytest.mark.parametrize("host_value", ["codex", "agy", "grok"])
def test_decide_cannot_judge_without_session_id(
    tmp_path, monkeypatch, resume_decision, host_value, state
):
    monkeypatch.setenv("HMAD_HOST", host_value)
    result = resume_decision.decide(_resume_state(tmp_path, state), "fx", now=NOW)
    assert result == "cannot_judge", (
        f"decide must return cannot_judge without a session id on {host_value}/{state}; "
        f"got {result!r}"
    )


@pytest.mark.parametrize("host_value", ["codex", "agy", "grok"])
def test_decide_routes_normally_with_session_id(
    tmp_path, monkeypatch, resume_decision, host_value
):
    monkeypatch.setenv("HMAD_HOST", host_value)
    result = resume_decision.decide(
        _resume_state(tmp_path, "no-owner"), "fx", session_id="sess-mine", now=NOW
    )
    assert result == "enter_autonomous", (
        f"decide must enter autonomous work with a session id on {host_value}; got {result!r}"
    )


@pytest.mark.parametrize(
    ("host_value", "state"),
    [
        pytest.param("zzz", "live-foreign-owner", id="zzz-live-foreign-owner"),
        pytest.param("zzz", "no-owner", id="zzz-no-owner"),
    ],
)
def test_decide_unknown_host_without_session_id(
    tmp_path, monkeypatch, resume_decision, host_value, state
):
    monkeypatch.setenv("HMAD_HOST", host_value)
    result = resume_decision.decide(_resume_state(tmp_path, state), "fx", now=NOW)
    assert result == "cannot_judge", (
        f"decide must return cannot_judge for unknown host without a session id "
        f"on {state}; got {result!r}"
    )


@pytest.mark.parametrize(
    ("host_value", "state"),
    [
        pytest.param("grok", "live-foreign-owner", id="grok-live-foreign-owner"),
        pytest.param("grok", "no-owner", id="grok-no-owner"),
    ],
)
def test_decide_empty_session_id_is_no_id(
    tmp_path, monkeypatch, resume_decision, host_value, state
):
    monkeypatch.setenv("HMAD_HOST", host_value)
    result = resume_decision.decide(
        _resume_state(tmp_path, state), "fx", session_id="", now=NOW
    )
    assert result == "cannot_judge", (
        f"decide must treat an empty session id as absent on grok/{state}; got {result!r}"
    )


def test_resume_decision_cli_under_grok(tmp_path, hermetic_env):
    state_file = _resume_state(tmp_path, "no-owner")
    result = subprocess.run(
        [sys.executable, str(RESUME_DECISION), "--state", str(state_file), "--feature", "fx"],
        env=hermetic_env(HMAD_HOST="grok", HMAD_STUB_HOSTILE="all"),
        capture_output=True,
        text=True,
        timeout=60.0,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "cannot_judge\n", (
        f"resume decision CLI must print cannot_judge on grok without a session id; "
        f"got {result.stdout!r}"
    )
