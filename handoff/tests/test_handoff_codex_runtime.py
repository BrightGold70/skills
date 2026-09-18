from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _frontmatter() -> dict:
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    _, raw, _ = text.split("---", 2)
    return yaml.safe_load(raw)


def test_frontmatter_is_valid_for_codex_skill_discovery():
    metadata = _frontmatter()
    assert metadata["name"] == "handoff"
    assert isinstance(metadata["description"], str)
    assert len(metadata["description"]) < 1024


def test_entrypoint_routes_codex_to_host_adapter():
    entrypoint = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    adapter = (ROOT / "references" / "codex-runtime.md").read_text(encoding="utf-8")

    assert "references/codex-runtime.md" in entrypoint
    for mode in ("WRITE", "READ", "LEARN", "HANDOVER", "TAKEOVER"):
        assert mode in adapter
    for token in (
        "collaboration.spawn_agent",
        ".omc/notepad.md",
        "HANDOFF_SKILL_ROOT",
        "request_user_input",
    ):
        assert token in adapter
    for token in ("AskUserQuestion", "TodoWrite", "Skill(skill:"):
        assert token not in adapter
