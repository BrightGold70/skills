"""Doc-tests over `h-mad/agents/*.md`, the orchestrator-side author rules in SKILL.md,
and the prose sites that used to claim the `exec` path is uncapped.

Nothing pinned the agent definitions before 2026-09-05. A rule nobody tests is advice:
the r17 design author called `advisor()` and read a 3,500-line document whole, died of
context overflow, and a successor was spawned without anyone ruling ownership. These
literals are the gate on the rules that close that.
"""
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[1]
AGENTS = SKILL_DIR / "agents"
SKILL = SKILL_DIR / "SKILL.md"
SUBSTRATE = SKILL_DIR / "references" / "agent-substrate.md"
IMPLEMENTER = SKILL_DIR / "references" / "codex-implementer-prompt.md"
WRAPPER = SKILL_DIR / "scripts" / "hmad-dispatch.sh"


def _norm(path: Path) -> str:
    """Collapse whitespace so a literal survives reflow/indentation."""
    return " ".join(path.read_text(encoding="utf-8").split())


AUTHOR_DONE = {
    "design-author": "DESIGN-AUTHOR: DONE version=v1.N",
    "plan-author": "PLAN-AUTHOR: DONE version=v1.N",
    "implplan-author": "IMPLPLAN-AUTHOR: DONE version=v1.N",
    "spec-author": "SPEC-AUTHOR: DONE version=v1.N",
}


@pytest.mark.parametrize("name", sorted(AUTHOR_DONE) + ["doc-auditor"])
def test_agent_never_calls_advisor_and_reads_in_slices(name: str) -> None:
    body = _norm(AGENTS / f"{name}.md")
    assert "Never call `advisor()`, and read in slices." in body, name
    assert "at most ~400 lines per call" in body, name
    assert "You have no advisor" in body, name


@pytest.mark.parametrize("name,done", sorted(AUTHOR_DONE.items()))
def test_author_final_message_starts_with_done_line(name: str, done: str) -> None:
    body = _norm(AGENTS / f"{name}.md")
    assert "Your final message starts with the `DONE` line" in body, name
    assert done in body, f"{name}: DONE line format {done!r} not stated"
    # assert-before-write: the only agent-side defence against two authors on one file
    assert "if either moved, stop and report" in body, name


def test_doc_auditor_final_message_starts_with_done_line() -> None:
    body = _norm(AGENTS / "doc-auditor.md")
    assert "starts with the `DONE` line" in body
    assert "DOC-AUDITOR: DONE must=N should=N nit=N" in body


def test_skill_orchestrator_owns_the_successor_ownership_rules() -> None:
    body = _norm(SKILL)
    for literal in (
        "Author dispatch rules the ORCHESTRATOR owns.",
        "recoverable, not death",
        "Rule ownership explicitly before spawning a successor.",
        "Collect on the `DONE` line, not on the notification.",
    ):
        assert literal in body, f"SKILL.md dropped orchestrator author rule: {literal!r}"


def test_implementer_scopes_the_import_error_red_rule_to_wiring_tasks() -> None:
    body = _norm(IMPLEMENTER)
    # the pinned question survives (test_h_mad_tdd_dispatch_discipline_prompt.py owns it)
    assert "For each FAILING test: does the failure message name the property under test?" in body
    assert "For a `wiring` task" in body
    assert "the first RED is `AttributeError`/`ImportError` **by construction**" in body
    assert "Say which case each failing test is." in body


def test_skill_names_vh_tail_as_the_first_oversize_remedy_and_the_wrapper_token() -> None:
    body = _norm(SKILL)
    assert body.count("first remedy is `--vh-tail N`") >= 2, (
        "both the exec-path paragraph and step 5.5 must name --vh-tail as the first remedy")
    assert "INPUT_TOO_LARGE" in body
    assert "1,048,576 characters" in body


def test_no_surface_still_claims_the_exec_path_is_uncapped() -> None:
    """The value sweep, kept as a gate: the false claim lived in four files."""
    skill, substrate, wrapper = _norm(SKILL), _norm(SUBSTRATE), _norm(WRAPPER)
    for text, where in ((skill, "SKILL.md"), (substrate, "agent-substrate.md")):
        assert "mechanically uncapped" not in text, where
        assert "bounded only by `ARG_MAX`" not in text, where
    assert "removes the limit outright" not in skill
    assert "no frontier" not in substrate
    assert "the arg is never the limit" not in wrapper
    assert "bounded only by ARG_MAX" not in wrapper


def test_skill_has_no_bare_heading_stub() -> None:
    """A lone `#` line arrived with commit bea1b60 and sat between two sections for weeks."""
    lines = SKILL.read_text(encoding="utf-8").splitlines()
    assert "#" not in lines, [i + 1 for i, l in enumerate(lines) if l == "#"]
