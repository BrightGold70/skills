"""Schema contract for the optional Phase-5 fallback agent."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
REPLAY = Path(__file__).resolve().parent / "fixtures" / "state_incident_replay.json"
sys.path.insert(0, str(SCRIPTS))

import h_mad_state_validate as state_validate  # noqa: E402


def run_writer(state: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "h_mad_state_write.py"), str(state),
         "--feature", "feat", *args],
        capture_output=True,
        text=True,
    )


def create_record(state: Path) -> None:
    result = run_writer(state, "--create")
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("grok", "grok"), ("claude", "claude"), ("null", None)],
)
def test_fallback_agent_set_writes_a_strict_record(tmp_path, raw, expected):
    state = tmp_path / "state.json"
    state.write_text("{}")
    create_record(state)

    result = run_writer(state, "--set", f"fallback_agent={raw}")

    assert result.returncode == 0, f"fallback_agent={raw}: {result.stderr}"
    record = json.loads(state.read_text())["orchestrator_state"]["feat"]
    assert "fallback_agent" in record
    assert record["fallback_agent"] == expected
    assert state_validate.classify(record) == "strict"


@pytest.mark.parametrize("raw", ["codex", "agy", "Grok"])
def test_fallback_agent_set_refuses_values_outside_the_enum(tmp_path, raw):
    state = tmp_path / "state.json"
    state.write_text("{}")
    create_record(state)
    before = state.read_bytes()

    result = run_writer(state, "--set", f"fallback_agent={raw}")

    assert result.returncode != 0, f"fallback_agent={raw} was accepted"
    assert state.read_bytes() == before, f"fallback_agent={raw} changed the state file"


def test_incident_replay_tiers_unchanged_by_fallback_agent(tmp_path, monkeypatch):
    records = json.loads(REPLAY.read_text())["orchestrator_state"]
    assert records, "incident replay has no records"
    current = {name: state_validate.classify(record) for name, record in records.items()}
    assert "strict" in current.values(), "incident replay no longer exercises strict records"

    schema = json.loads(state_validate.STRICT_SCHEMA.read_text())
    schema["properties"].pop("fallback_agent", None)
    without_fallback = tmp_path / "schema_without_fallback_agent.json"
    without_fallback.write_text(json.dumps(schema))
    monkeypatch.setattr(state_validate, "STRICT_SCHEMA", without_fallback)
    monkeypatch.setattr(state_validate, "_schemas", {})
    monkeypatch.setattr(state_validate, "_validators", {})

    for name, record in records.items():
        assert state_validate.classify(record) == current[name], name


def test_fallback_agent_description_states_the_four_facts():
    schema = json.loads(state_validate.STRICT_SCHEMA.read_text())
    properties = schema["properties"]
    fallback = properties["fallback_agent"]
    assert "fallback_agent" not in schema["required"]
    assert list(properties).index("fallback_agent") == list(properties).index("codex_status") + 1
    assert fallback["enum"] == ["grok", "claude", None]
    description = fallback["description"]

    for fact in (
        "read only when codex is out",
        "are equivalent",
        "HMAD_CODEX_UNAVAILABLE does not override",
        "prose-enforced",
    ):
        assert fact in description, f"fallback_agent description omits {fact!r}"
