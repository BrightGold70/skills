"""RED pins for the Grok fallback's operator-facing documentation."""

from pathlib import Path

import pytest

from docsections import titled_section


H_MAD = Path(__file__).resolve().parents[1]
SKILL_MD = H_MAD / "SKILL.md"
STATE_SCHEMA_MD = H_MAD / "references" / "state-schema.md"
AGENT_SUBSTRATE_MD = H_MAD / "references" / "agent-substrate.md"

PHASE5_HEADING = "Codex authors Phase 5 — enforced, not just instructed"
EXEC_HEADING = "Exit-code dispatch for 5d/5e (`hmad-dispatch exec`) — default for one-shot"
TEAMMATE_HEADING = "Teammate audit leg — when codex is unavailable"
NEVER_GATE_HEADING = "Never gate on one audit pass"


def _section(path: Path, heading: str) -> str:
    return titled_section(path.read_text(encoding="utf-8"), heading)


def _assert_terms(section: str, *terms: str) -> None:
    for term in terms:
        assert term in section, f"section must document {term!r}"


def test_phase5_section_documents_fallback_agent() -> None:
    section = _section(SKILL_MD, PHASE5_HEADING)
    _assert_terms(
        section,
        "fallback_agent",
        "HMAD_CODEX_UNAVAILABLE",
        "no write-time test-first gate",
        "fallback-grok",
    )


def test_exec_section_documents_exec_grok() -> None:
    section = _section(SKILL_MD, EXEC_HEADING)
    _assert_terms(section, "exec grok", "--agent grok")


def test_teammate_section_documents_the_grok_leg() -> None:
    section = _section(SKILL_MD, TEAMMATE_HEADING)
    _assert_terms(section, "--surfaces agy,grok", "unmeasured")


def test_never_gate_section_cross_references_the_grok_leg() -> None:
    section = _section(SKILL_MD, NEVER_GATE_HEADING)
    _assert_terms(section, "--surfaces agy,grok")


def test_state_schema_doc_names_fallback_agent() -> None:
    text = STATE_SCHEMA_MD.read_text(encoding="utf-8")
    _assert_terms(text, "fallback_agent")


def test_agent_substrate_documents_exec_grok_and_grok_sandbox() -> None:
    section = _section(AGENT_SUBSTRATE_MD, "Verbs")
    _assert_terms(section, "exec grok", "GROK_SANDBOX")


def test_missing_heading_fails_not_skips(tmp_path: Path) -> None:
    original = SKILL_MD.read_text(encoding="utf-8")
    heading_line = f"## {TEAMMATE_HEADING}\n"
    assert original.count(heading_line) == 1, "the teammate heading must occur exactly once"
    scratch = tmp_path / "SKILL.md"
    scratch.write_text(original.replace(heading_line, "", 1), encoding="utf-8")

    with pytest.raises(AssertionError, match="missing section"):
        _section(scratch, TEAMMATE_HEADING)
