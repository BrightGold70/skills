"""Row 2932: narrow helper agents instead of `general-purpose`.

Measured 2026-11-02 with `claude -p --agent <name>` from an empty dir on Haiku:
a default session starts at 53.3k context, the six h-mad agents at 18.2–21.6k.
Every turn re-reads that base, so helper work an orchestrator used to hand to
`general-purpose` (implement one bounded task, fix one finding, label a batch)
costs ~33k a turn more than it needs to. Of 47 `general-purpose` dispatches in
this repo's transcripts since 2026-10-16, between 19 and 47 were h-mad work.

These tests pin the two helpers' tool grants and contracts, and pin that every
`Agent(subagent_type: …)` SKILL.md prescribes names an `agents/` file, `fork`,
or the one documented `general-purpose` fallback.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from skill_corpus import doc_text

SKILL_DIR = Path(__file__).resolve().parents[1]
AGENTS = SKILL_DIR / "agents"
SKILL_MD = SKILL_DIR / "SKILL.md"

HELPERS = {
    "task-executor": {
        "model": "sonnet",
        "tools": {"Read", "Grep", "Glob", "Bash", "Edit", "Write"},
        "done": "TASK-EXECUTOR: DONE status=<done|blocked> files=N verify=<pass|fail|not-run> "
                "path=<REPORT> lines=N sha256=<64 hex>",
    },
    "task-labeller": {
        "model": "haiku",
        "tools": {"Read", "Grep", "Glob", "Bash", "Write"},
        "done": "TASK-LABELLER: DONE items=N unsure=N path=<REPORT> lines=N sha256=<64 hex>",
    },
}


def _norm(text: str) -> str:
    return " ".join(text.split())


def _frontmatter(path: Path) -> dict[str, str]:
    head = path.read_text(encoding="utf-8").split("---", 2)[1]
    return {k.strip(): v.strip() for k, v in
            (line.split(":", 1) for line in head.strip().splitlines() if ":" in line)}


@pytest.mark.parametrize("name", sorted(HELPERS))
def test_helper_frontmatter_pins_name_model_and_an_exact_tool_grant(name: str) -> None:
    """An exact allowlist: no MCP tool, no nested Agent/Task spawns, nothing extra."""
    fm = _frontmatter(AGENTS / f"{name}.md")
    assert fm["name"] == name
    assert fm["model"] == HELPERS[name]["model"]
    tools = {t.strip() for t in fm["tools"].split(",")}
    assert tools == HELPERS[name]["tools"], tools


def test_the_labeller_cannot_edit() -> None:
    tools = _frontmatter(AGENTS / "task-labeller.md")["tools"]
    assert "Edit" not in tools and "NotebookEdit" not in tools


@pytest.mark.parametrize("name", sorted(HELPERS))
def test_helper_says_done_first_and_hashes_its_report(name: str) -> None:
    body = _norm((AGENTS / f"{name}.md").read_text(encoding="utf-8"))
    assert HELPERS[name]["done"] in body
    assert "starts with the `DONE` line" in body
    assert "<REPORT>.done" in body
    assert "create the marker last" in body
    assert "shasum -a 256" in body


@pytest.mark.parametrize("name", sorted(HELPERS))
def test_helper_never_touches_git_history(name: str) -> None:
    body = _norm((AGENTS / f"{name}.md").read_text(encoding="utf-8"))
    assert "never commit, push, stash, reset or check out" in body


def test_the_executor_writes_only_inside_its_files_and_never_weakens_a_test() -> None:
    body = _norm((AGENTS / "task-executor.md").read_text(encoding="utf-8"))
    assert "edit only the paths listed in `FILES`" in body
    assert "Never edit, skip or weaken a test" in body
    assert "`VERIFY`" in body and "status=blocked" in body


def test_the_labeller_uses_a_closed_label_set_and_admits_doubt() -> None:
    body = _norm((AGENTS / "task-labeller.md").read_text(encoding="utf-8"))
    assert "only labels from `LABELS`" in body
    assert "`UNSURE`" in body
    assert "You edit nothing" in body


PRESCRIBED = re.compile(r'Agent\(subagent_type: "([^"]+)"')


def test_every_prescribed_subagent_type_names_an_agent_file_fork_or_the_fallback() -> None:
    skill = doc_text(SKILL_MD)
    defined = {p.stem for p in AGENTS.glob("*.md")}
    named = set(PRESCRIBED.findall(skill))
    assert named, "the census found no Agent(subagent_type: …) at all — the pattern is stale"
    stray = sorted(named - defined - {"fork", "general-purpose"})
    assert not stray, f"SKILL.md prescribes subagent types with no agents/ file: {stray}"


def test_general_purpose_is_prescribed_only_as_the_bootstrap_fallback() -> None:
    skill = doc_text(SKILL_MD)
    # `[,)]`: a dispatch written with a prompt (`…"general-purpose", prompt:`) counts too.
    hits = [m.start() for m in re.finditer(r'Agent\(subagent_type: "general-purpose"[,)]', skill)]
    assert len(hits) == 1, f"general-purpose prescribed {len(hits)} times; only the bootstrap fallback may"
    window = _norm(skill[max(0, hits[0] - 600):hits[0]])
    assert "not dispatchable by name until the next session" in window


def test_skill_routes_helper_work_to_the_narrow_agents() -> None:
    body = _norm(doc_text(SKILL_MD))
    assert 'Agent(subagent_type: "task-executor"' in body
    assert 'Agent(subagent_type: "task-labeller"' in body
    assert "never `general-purpose`" in body
