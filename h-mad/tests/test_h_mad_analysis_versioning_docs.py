from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
PROTOCOL = SKILL_DIR / "references" / "inline-protocols.md"


def doc() -> str:
    return PROTOCOL.read_text(encoding="utf-8")


def section(text: str, heading: str, next_heading: str) -> str:
    start = text.index(heading) + len(heading)
    end = text.index(next_heading, start)
    return text[start:end]


def test_phase6_save_versions_analysis_and_refreshes_legacy_path() -> None:
    phase6 = section(doc(), "## Phase 6 — Gap Analysis", "## Phase 6b — Iterate")

    assert "docs/03-analysis/<feature>.analysis.v1.md" in phase6
    assert "docs/03-analysis/<feature>.analysis.md" in phase6


def test_phase6b_versions_next_unused_cycle_without_overwriting_and_refreshes_latest() -> None:
    phase6b = section(doc(), "## Phase 6b — Iterate", "## Phase 7 — Report + Archive")
    lower = phase6b.lower()

    assert "next unused v<n>" in lower
    assert "docs/03-analysis/<feature>.analysis.md" in phase6b
    assert "do not overwrite" in lower or "never overwrite" in lower


def test_protocol_explains_latest_unversioned_path_and_phase7_parser_dependency() -> None:
    phase6 = section(doc(), "## Phase 6 — Gap Analysis", "## Phase 6b — Iterate")
    lower = phase6.lower()

    assert "docs/03-analysis/<feature>.analysis.md" in phase6
    assert "latest" in lower
    assert "h_mad_phase7_preconditions.py" in phase6


def test_protocol_names_cycle_count_consumer_and_iteration_formula() -> None:
    phase6 = section(doc(), "## Phase 6 — Gap Analysis", "## Phase 6b — Iterate")
    lower = phase6.lower()

    assert "h_mad_cycle_counts.py" in phase6
    assert "max(n) - 1" in lower
