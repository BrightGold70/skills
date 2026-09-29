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


# The protocol above has named `analysis.v<N>.md` since 2026-07-23, yet
# grok-codex-fallback and multi-host-runtime closed with only `analysis.md` plus a
# verifier report saved as `gap.v1.md`: the surfaces the orchestrator reads at
# run time (SKILL.md's 6a/6b bullets, phase-table.md) named only the unversioned
# path, and nothing enforced the rule. Telemetry then derived iterate_cycles=0.


def test_phase6_says_a_delegated_verifier_report_is_saved_as_the_versioned_analysis() -> None:
    phase6 = section(doc(), "## Phase 6 — Gap Analysis", "## Phase 6b — Iterate")

    assert "gap.v1.md" in phase6
    assert "analysis_unversioned" in phase6


def test_skill_md_6a_and_6b_bullets_name_the_versioned_analysis() -> None:
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    bullet_6a = next(line for line in text.splitlines() if line.startswith("- **6a** —"))
    bullet_6b = next(line for line in text.splitlines() if line.startswith("- **6b** —"))

    assert "docs/03-analysis/<feature>.analysis.v1.md" in bullet_6a
    assert "docs/03-analysis/<feature>.analysis.md" in bullet_6a
    assert "analysis.v<N>.md" in bullet_6b
    assert "never overwrite" in bullet_6b.lower()


def test_phase_table_6a_row_names_the_versioned_analysis() -> None:
    text = (SKILL_DIR / "references" / "phase-table.md").read_text(encoding="utf-8")
    row_6a = next(line for line in text.splitlines() if line.startswith("- **6a** —"))
    row_6b = next(line for line in text.splitlines() if line.startswith("- **6b** —"))

    assert "docs/03-analysis/<feature>.analysis.v1.md" in row_6a
    assert "analysis.v<N>.md" in row_6b
