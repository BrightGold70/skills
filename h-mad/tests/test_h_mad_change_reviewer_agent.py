"""`change-reviewer`: a fresh-context reviewer of a CHANGE that writes its report to a file.

Five consecutive adversarial review rounds (multi-host-runtime, R18-R22) dispatched a
reviewer type with no Write tool. It could not write the report file it was handed, and its
final reply truncated at about 4 KB, so every round relayed the report to the orchestrator in
<=3 KB SendMessage chunks that the orchestrator reassembled by hand. The fix is a reviewer that
owns exactly one file, its report, and says DONE with a digest of it, following the
`doc-auditor` protocol.

Registration is pinned too: SKILL.md registers the agents by a hand-written list in three
places, and nothing checked that list against `agents/`, so a new definition could ship
unregistered and fail only as "unknown agent type" mid-run.
"""
import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
AGENTS = SKILL_DIR / "agents"
SKILL_MD = SKILL_DIR / "SKILL.md"
REVIEWER = AGENTS / "change-reviewer.md"


def _norm(text: str) -> str:
    return " ".join(text.split())


def _frontmatter(path: Path) -> dict:
    head = path.read_text(encoding="utf-8").split("---", 2)[1]
    return {k.strip(): v.strip() for k, v in
            (line.split(":", 1) for line in head.strip().splitlines() if ":" in line)}


def test_every_agent_is_registered_in_every_install_list():
    defined = sorted(p.stem for p in AGENTS.glob("*.md"))
    lists = re.findall(r"for n in ([a-z -]+); do\s*\n\s*(?:ln -sfn|\[ -r)", SKILL_MD.read_text(encoding="utf-8"))
    assert len(lists) == 3, lists  # a new list must be added here deliberately
    for names in lists:
        assert sorted(names.split()) == defined, (names, defined)


def test_change_reviewer_has_write_and_no_edit_tools():
    """Bash can still write; the one-file rule is prompt-level. This pins the tool grant."""
    fm = _frontmatter(REVIEWER)
    assert fm["name"] == "change-reviewer"
    tools = {t.strip() for t in fm["tools"].split(",")}
    assert "Write" in tools, tools
    assert "Edit" not in tools and "NotebookEdit" not in tools, tools


def test_change_reviewer_writes_one_file_and_says_done_first():
    body = _norm(REVIEWER.read_text(encoding="utf-8"))
    assert "`REPORT`" in body
    assert "You write exactly one file" in body
    assert "CHANGE-REVIEWER: DONE must=N should=N nit=N path=<REPORT> lines=N sha256=<64 hex>" in body
    assert "starts with the `DONE` line" in body
    assert "<REPORT>.done" in body
    assert "Write the report fully before creating the marker" in body
    assert "create the marker last" in body


def test_change_reviewer_carries_the_evidence_rules():
    body = _norm(REVIEWER.read_text(encoding="utf-8"))
    assert "Never state a location you have not opened" in body
    assert "is a Should-fix marked `unverified`, never a Must-fix" in body


def test_skill_routes_change_reviews_to_the_writing_reviewer():
    body = _norm(SKILL_MD.read_text(encoding="utf-8"))
    assert 'Agent(subagent_type: "change-reviewer"' in body
    assert "goes to `change-reviewer`" in body
    assert "Never use a reviewer type without a Write tool" in body
    assert "Gate it through `h_mad_done_gate.py` before reading the report" in body
    assert '§"Teammate change review") live in `agents/`' in body
    assert "`agents/change-reviewer.md` — fresh-context review of a CHANGE" in body
    assert "truncat" in body.split('Agent(subagent_type: "change-reviewer"', 1)[0][-2500:]
