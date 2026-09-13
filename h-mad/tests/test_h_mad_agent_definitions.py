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
        # Staging a path is not consuming it: the body lands in $RP and the message
        # carries only a pointer, so an orchestrator that acts on the message has
        # skipped exactly the owed list the file deliverable was added to protect.
        "Read `$RP` after every author DONE — staging a path is not consuming it.",
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


# --- the authors' report body has no file deliverable (taken-over brief, 2026-09-07) ---
#
# `doc-auditor.md` carries `REPORT`: path to write your report to (:40) and "your
# report file is the deliverable" (:192). The four AUTHORS carried none, so their
# report body travelled through a transport that truncates at ~4 KB and always cuts
# the TAIL -- which is where the h-mad report format puts the owed list, the declines
# with their reasons, and the text owed to sibling authors, none of which is in the
# document. Measured on gateway-consolidation c105: two of three messages from one
# `design-author` run truncated mid-word (at "Restr", first Declined item, and at
# "naming the **ov"), recovery cost three SendMessage round-trips, and the retry
# scoped to "ONLY the tail, under 15 lines" was itself truncated. Independent prior
# evidence 2026-09-06: 3 of 3 authors, always at the owed list.
#
# This is NOT the r17 DONE-line failure and does not mean that fix regressed. r17
# targeted DONE-line loss and succeeded -- the DONE line arrived intact in all three
# c105 messages. Two different failures, one of which had a fix.


@pytest.mark.parametrize("name", sorted(AUTHOR_DONE))
def test_author_is_given_a_report_path(name: str) -> None:
    """Same parameter, same words as the auditor's -- one phrasing, not two."""
    body = _norm(AGENTS / f"{name}.md")
    assert "`REPORT`: path to write your report to" in body, name


@pytest.mark.parametrize("name", sorted(AUTHOR_DONE))
def test_author_writes_the_body_to_the_file_not_the_message(name: str) -> None:
    body = _norm(AGENTS / f"{name}.md")
    assert "Write the report body to `REPORT`" in body, name


@pytest.mark.parametrize("name", sorted(AUTHOR_DONE))
def test_author_handles_an_absent_report_path_explicitly(name: str) -> None:
    """`REPORT=<none>` must be legitimate AND declared, never silently inline.

    Fail-open is right -- an older dispatch that passes no path must still work --
    but a silent fall-back reproduces the defect the next time someone forgets the
    flag, and the reader cannot tell a short report from a truncated one.

    HALF OF THAT DOCSTRING WAS NEVER ASSERTED. The test checked only that
    `REPORT=<none>` is mentioned — and each of these files mentions it TWICE, so a
    mutation deleting the sentence that carries the "AND declared" half left one
    occurrence standing and SURVIVED. The `say so` clause is the entire difference
    between a declared fall-back and a silent one, which is what this test is named
    for.
    """
    body = _norm(AGENTS / f"{name}.md")
    assert "REPORT=<none>" in body, name
    assert "say so on the line after DONE" in body, (
        f"{name}: the fall-back must be DECLARED, not merely permitted — without "
        f"this the reader cannot tell a trimmed report from a truncated one")


@pytest.mark.parametrize("name", sorted(AUTHOR_DONE))
def test_the_owed_list_is_named_as_what_truncation_costs(name: str) -> None:
    """The rule must say WHY the tail matters, or a reader trims the report to fit."""
    body = _norm(AGENTS / f"{name}.md")
    assert "owed list" in body, name


@pytest.mark.parametrize("name", sorted(AUTHOR_DONE))
def test_no_author_still_says_only_the_document_is_the_deliverable(name: str) -> None:
    """`design-author.md:120` read "report short; the document is the deliverable".

    True of the DOCUMENT and false of the report, which carries the owed list and
    the declines. Left standing beside the new rule it tells the author to do the
    thing that loses the tail.
    """
    body = _norm(AGENTS / f"{name}.md")
    assert "the document is the deliverable" not in body, name


def test_the_orchestrator_passes_REPORT_when_dispatching_an_author() -> None:
    """A contract only the agent side knows about is never exercised."""
    body = _norm(SKILL)
    assert 'subagent_type: "plan-author"' in body
    # Anchor on the SECTION HEADING, not the phrase: "Teammate authors" also appears
    # as a cross-reference earlier in the file, so splitting on the phrase lands in
    # the wrong place and the assertion measures a region that was never the target.
    heading = "## Teammate authors — one author, one document, fresh context every time"
    assert heading in body
    section = body.split(heading, 1)[1][:2500]
    assert 'subagent_type: "plan-author"' in section
    # The DISPATCH TEMPLATE, not the prose around it. A bare `REPORT=` check passed
    # while the template had been stripped, because the same section explains
    # `REPORT=<none>` and says "Pass `REPORT=` on every author dispatch" — the
    # mutation battery reported the row SURVIVED and that is what it meant.
    assert 'REPORT=$RP")' in section


# --- probe hygiene (#11/H8 sibling): the orchestrator carried the rule, the authors did not ---

MEASUREMENT = SKILL_DIR / "references" / "measurement-discipline.md"
INVARIANTS = SKILL_DIR / "invariants.base.md"


@pytest.mark.parametrize("name", sorted(AUTHOR_DONE))
def test_author_is_told_to_delete_its_probe(name: str) -> None:
    """An author left an executable `test_env_sleep.py` at a sub-project root.

    SKILL.md has carried "Then delete the probe" for the orchestrator since the
    worktree-selector investigation; none of the four authors did, which is why the
    file reached the tree — an executable probe at a repo root is collected by a
    suite it was never written for.
    """
    body = _norm(AGENTS / f"{name}.md")
    assert "Then delete the probe." in body, name
    assert "becomes a second, untested harness that drifts from the first" in body, name
    assert "Cleaning up is part of the probe, not a courtesy." in body, name


def test_the_orchestrator_still_owns_the_rule_the_authors_now_mirror() -> None:
    """The authors' rule cites SKILL's section by name; if that section is renamed
    or dropped, four agent files point at nothing."""
    body = _norm(SKILL)
    assert "## Confirming a suspected defect before fixing it" in body
    assert "Then **delete the probe**" in body


def test_a_vacuous_criterion_is_named_as_its_own_class() -> None:
    """H8 extension A. Distinct from "a check that cannot fail": this one returns
    the SAME observation in both states, so a mutation battery reports it caught."""
    body = _norm(INVARIANTS)
    assert "cannot discriminate in EITHER direction is vacuous" in body
    assert "name the observation that differs between the implemented and unimplemented" in body
    # The measured case must stay attached to the rule — it is what makes it checkable.
    assert "AC-2.5b" in body and "is_cli_available" in body


def test_self_counting_screens_cover_contracts_stated_elsewhere() -> None:
    """H8 extension B. The 88-vs-94 defect: the edited region was internally
    consistent and two arithmetic checks both verified only that."""
    body = _norm(MEASUREMENT)
    assert "must include contracts stated ELSEWHERE in the document" in body
    assert "an internal-consistency check cannot find this class" in body
    assert "AC-7.5d still required 88" in body


# --- the two-round cap's exit terms (#11/H2): which of the two readings ---

def test_the_cap_says_which_reading_it_means() -> None:
    """The section prescribed "the phase EXITS whatever the verdict" and did not
    say whether that forbids a third GATING ROUND or all further editing. The two
    readings prescribe opposite actions on the same finding."""
    body = _norm(SKILL)
    assert "The cap forbids a third GATING ROUND, not a final corrective revision" in body
    # The three conditions are what make "not a third round" checkable rather than
    # a loophole: no re-audit, no new findings, mechanically checkable fixes.
    assert "it is **not re-audited**" in body
    assert "it fixes **only findings the two rounds already filed**" in body
    # `_norm` joins on whitespace, so only the COLLAPSED spelling can ever match.
    # An earlier version of this assertion offered a `\n`-containing alternative as
    # an `or` branch; that branch is unreachable by construction, and a disjunction
    # with a dead half hides which spelling the rule actually has.
    assert "every fix is **mechanically checkable**" in body


def test_an_open_decision_must_be_an_actual_decision() -> None:
    """`OPEN-DECISION`'s premise is "a wrong choice is a RED failure that costs
    minutes" — which requires a choice to exist. An unsatisfiable criterion
    produces a RED no branch can clear, i.e. a blocked Phase-5 task."""
    body = _norm(SKILL)
    assert ("Name an implementation that satisfies the criterion. If you cannot name one, "
            "it is not an open decision") in body
    assert "it is a defect, and it is fixed by the corrective revision" in body
    # The measured case must stay attached, and so must the re-probe that found it
    # already resolved — a rule written from a live failure and a rule written from
    # a case decided correctly by hand are different claims.
    assert "AC-7.5d still required **88** rows against a document enumerating **94**" in body
    assert "impl-plan v1.76 the AC requires 101 rows" in body


def test_the_awk_backspace_trap_is_recorded() -> None:
    """Recovered from orchestrator label `#30` (2026-09-07).

    The label was carried across four handoffs as an opaque token and then written
    off as unrecoverable. It was recoverable — the definition sat in a 2026-09-05
    handoff. The feature it was filed against has merged and archived, so the FIX is
    moot; the trap is not, and it is a silent-zero: a screen that returns 0 on a file
    full of hits reads as clean.
    """
    body = _norm(MEASUREMENT)
    assert "`\\b` is a BACKSPACE in awk, not a word boundary." in body
    assert "returns 0 on a file full of hits, which reads as a clean screen" in body
    # The remedy must be named, or the rule is a warning with no action.
    assert "grep -oE" in body and "[^0-9]" in body
