"""FR-1's schema order and FR-2's availability condition on all four prose surfaces."""
import json
from pathlib import Path


HMAD = Path(__file__).resolve().parents[1]
SCHEMA = HMAD / "scripts" / "h_mad_state_schema.json"
REFERENCE = HMAD / "references" / "state-schema.md"
FR1_FIELDS = [
    "implementer", "agy_status", "implementer_switch",
    "review_independence", "implementation_authors",
]


def _properties():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))["properties"]


def _reference_rows(name):
    return [line for line in REFERENCE.read_text(encoding="utf-8").splitlines()
            if line.startswith(f"| `{name}` |")]


def test_codex_status_schema_description_states_the_resolution():
    description = _properties()["codex_status"]["description"]
    assert "permitting Claude to write the fallback" not in description, (
        "codex_status description must resolve both peers before allowing Claude"
    )
    assert "One switch, both effects" not in description, "codex_status must distinguish author resolution from audit routing"
    assert "h_mad_tdd_judge.py implementer" in description, "codex_status must name the implementer resolution command"


def test_codex_status_reference_row_states_the_resolution():
    rows = _reference_rows("codex_status")
    assert len(rows) == 1, "codex_status must have exactly one reference row"
    assert "permits a Phase-5 authoring fallback" not in rows[0], "codex_status alone cannot permit authoring fallback"
    assert "h_mad_tdd_judge.py implementer" in rows[0], "codex_status row must name the implementer resolution command"


def test_fallback_agent_schema_description_names_both_peers():
    assert "agy is out too" in _properties()["fallback_agent"]["description"], (
        "fallback_agent description must require that agy is out too"
    )


def test_fallback_agent_reference_row_names_both_peers():
    rows = _reference_rows("fallback_agent")
    assert len(rows) == 1, "fallback_agent must have exactly one reference row"
    assert "agy is out too" in rows[0], "fallback_agent reference row must require that agy is out too"


def test_reference_rows_exist_for_the_five_fields():
    for name in FR1_FIELDS:
        assert len(_reference_rows(name)) == 1, f"{name} must have exactly one state-schema.md table row"


def test_new_properties_follow_fallback_agent_in_order():
    properties = list(_properties())
    assert properties[-5:] == FR1_FIELDS, "FR-1 properties must be appended in design order"
    assert properties[properties.index("fallback_agent") + 1:] == FR1_FIELDS, (
        "the five FR-1 properties must immediately follow fallback_agent"
    )
