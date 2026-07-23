from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_DOC = SKILL_DIR / "SKILL.md"


def doc() -> str:
    return SKILL_DOC.read_text(encoding="utf-8")


def telemetry_section(text: str) -> str:
    heading = "## Telemetry"
    start = text.index(heading) + len(heading)
    end = text.index("## ", start)
    return text[start:end]


def test_telemetry_counts_are_derived_from_disk_not_orchestrator_state() -> None:
    section = telemetry_section(doc())
    lower = section.lower()

    assert "derive" in lower or "derived" in lower
    assert "artifact" in lower
    assert "state" in lower
    assert any(
        phrase in lower
        for phrase in (
            "not read from",
            "not taken from",
            "rather than state",
            "instead of state",
        )
    )


def test_telemetry_documents_docs_root_flag_and_default() -> None:
    section = telemetry_section(doc())
    lower = section.lower()

    assert "--docs-root" in section
    assert "default" in lower
    assert "docs" in lower


def test_skill_frontmatter_retains_manifest_name_and_description() -> None:
    text = doc()
    assert text.startswith("---\n")
    end = text.find("\n---", 4)
    assert end != -1
    frontmatter = text[4:end]

    assert "name:" in frontmatter
    assert "description:" in frontmatter
