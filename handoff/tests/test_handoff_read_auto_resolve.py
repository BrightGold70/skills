"""READ Step 3.6 repairs the mechanical divergences and NOTHING else.

Reporting a divergence and leaving it hands the user a second task list on top of
the one the resume just restored. Most divergences have exactly one correct repair
and no judgment in them, so leaving those manual is pure toil.

The danger is the obvious generalisation. "Auto-resolve divergences" as a blanket
rule would have a resume pull a dirty tree, break a live session's claim, or
fast-forward a sibling worktree whose owner is mid-turn — each of which looks
locally safe and is not. So the value of this step is carried by two lists, and
the SHORT one is the safety property: an allowlist that had to be argued entry by
entry, and a never-list naming what stays reported. These tests defend the second
list at least as hard as the first, because a future reader's instinct will be to
grow the allowlist "just for this one case".

The gates matter as much as the entries. Every repair is conditional, and a gate
that cannot be EVALUATED must fail closed — this repo has repeatedly shipped the
opposite (`find` under rtk refusing to run and reading as "nothing is claimed";
an unreadable worktree comment reading as empty and clobbering a human's note).

Literals are whitespace-normalised so a markdown reflow cannot break them.
"""

from __future__ import annotations

from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"
RAW = SKILL.read_text(encoding="utf-8")
DOC = " ".join(RAW.split())


def require(literal: str, why: str) -> None:
    assert " ".join(literal.split()) in DOC, f"handoff/SKILL.md dropped guidance: {why}"


def test_the_step_exists_and_is_ordered_before_the_todo_restore() -> None:
    """A repair after the restore leaves todos describing a world that changed."""
    assert "### Step 3.6" in RAW
    assert RAW.index("### Step 3.6") < RAW.index("### Step 4: Restore the todo list")


def test_the_step_is_scoped_in_its_own_title() -> None:
    """`and only that` is the whole contract, stated where nobody can miss it."""
    require("Resolve what is mechanically resolvable — and only that",
            "the scope limit belongs in the heading, not buried in the body")


def test_the_predicate_rule_fails_closed() -> None:
    require("fail closed",
            "an ungated repair is worse than a reported divergence")
    require('"I could not check" and "the check said yes" must never take the same branch',
            "the asymmetry this repo keeps re-learning, stated in one line")


@pytest.mark.parametrize("entry, why", [
    ("git pull --ff-only", "the only sanctioned remote integration"),
    ("--create --claim", "a handover brief whose feature record does not exist yet"),
    ("never `--force`", "a stale claim is takeable plainly; force is for a LIVE owner"),
    ("commit it", "an untracked handoff doc is the one file READ may commit"),
    ("git log --follow --diff-filter=R", "a moved path is resolvable only when the rename is named"),
    ("exactly one", "the pane-pin gate: one candidate or none"),
])
def test_allowlist_entries_survive(entry: str, why: str) -> None:
    require(entry, why)


@pytest.mark.parametrize("banned, why", [
    ("A dirty or diverged tree",
     "a surprise merge mid-resume is worse than a stale doc"),
    ("Anything in another repo, worktree or lane",
     "a sibling lane may have a live owner who is not watching this session"),
    ("A claim held by a LIVE session",
     "that is a collision and a finding, not a lock to break"),
    ("Any premise the brief asserts about the world",
     "a premise needs a probe, not a repair"),
    ("More than one candidate for a pane pin",
     "a wrong-but-live pin passes every liveness check"),
    ("`--force`, `-D`, `rm`, or a push",
     "irreversible is the definition of not-mechanical here"),
])
def test_never_resolve_list_survives(banned: str, why: str) -> None:
    require(banned, why)


def test_the_fast_forwardable_sibling_is_named_explicitly() -> None:
    """The most tempting entry, and the one a reader will argue is safe.

    It is named in the never-list rather than merely implied by "another worktree",
    because the tempting case is precisely the one that looks clean: no divergence,
    no uncommitted work, a pure fast-forward. The cost is not to git — it is that
    another session's files change under a running agent.
    """
    require("including a sibling branch that is cleanly fast-forwardable",
            "the plausible-looking exception must be refused by name")


def test_the_allowlist_is_declared_closed() -> None:
    require("Nothing outside it.", "an open-ended allowlist is not an allowlist")
    require("don't extend the allowlist in the moment",
            "the growth path is the failure mode, not the current entries")


def test_repairs_are_reported_separately_from_divergences() -> None:
    """A repair nobody is told about is indistinguishable from nothing broken."""
    require("Step 5 gains a **Resolved** block, separate from **Divergences**",
            "merging the two hides both")
    require("Name the command for each repair so it can be undone",
            "undoability is what makes an automatic repair acceptable")


def test_an_empty_resolved_block_is_still_printed() -> None:
    """Omitting it teaches the reader the resume does not do this at all."""
    require("**Resolved:** none", "absence and inaction must not print identically")


def test_the_report_template_demonstrates_both_blocks() -> None:
    """The template is what gets copied; guidance it contradicts loses."""
    i = RAW.index("## Session resumed")
    block = RAW[i:i + 1600]
    assert "**Resolved**" in block, "the template must show a resolved block"
    assert "NOT resolved" in block, "and must show the reported-only list beside it"


def test_opt_out_exists() -> None:
    require("--report-only", "resuming into a tree someone else is working needs an escape")


def test_read_mode_is_still_not_allowed_to_start_the_work() -> None:
    """Resolving divergences must not become 'and then it did the first todo'."""
    require("Don't start executing tasks",
            "Step 3.6 widens repair, never execution")


def test_the_historical_record_rule_survives_the_new_commit() -> None:
    """Step 3.6 commits an untracked doc, which is not the same as editing one."""
    require("Don't rewrite or update the handoff doc in read mode",
            "READ must not edit the doc's content")
    require("which changes no content",
            "the one permitted write must be distinguished from an edit")


# --- the sibling gate was PROPOSED and REFUSED, and the refusal is the record --
#
# Task carried from the 2026-09-01 handoff: "widen Step 3.6's allowlist to the
# fast-forwardable sibling, gated on no live agent in that worktree". The gate was
# specified and then falsified before any code was written, so what ships is the
# negative result. These pins exist because the idea is genuinely attractive and
# WILL be had again -- and a refusal nobody wrote down is re-derived from scratch,
# which is the same "the workaround leaves no trace" shape as the wire-pin gate.


def test_the_refused_gate_is_recorded_where_the_next_reader_will_look() -> None:
    """Named in the never-list entry itself, not in a commit message.

    A reader who has this idea reads the bullet that refuses it. If the reason
    lives anywhere else, they re-derive the proposal instead of finding it
    already answered.
    """
    require("The gate that would have made this resolvable was proposed, specified, and refused",
            "the refused proposal must be findable from the entry that refuses it")


def test_the_presence_absence_asymmetry_is_the_stated_reason() -> None:
    """A tail proves presence; nothing proves absence.

    This is the load-bearing half and it generalises past Orca: a quiet pane is
    an idle agent, and a non-Orca session is invisible to any Orca-side check.
    Softening it to "check whether an agent is there" restores the proposal.
    """
    require("proves an agent is **present** (a banner), never that one is **absent**",
            "presence is observable, absence is not — that is why the gate fails")
    require("invisible to every Orca-side check",
            "a non-Orca session in that worktree is unobservable, not merely unlikely")


def test_the_verdict_is_stated_as_a_rule_not_a_preference() -> None:
    """The general form, so the next unbuildable gate is recognised as one."""
    require("A gate that can never legitimately pass IS this never-list entry",
            "the reusable rule, not a one-off judgement about this worktree")


def test_a_refused_repair_still_names_its_command() -> None:
    """The ergonomic half of the repair is free and is not refused.

    The reason the never-list is tolerable is that the user loses one keystroke,
    not the information. Dropping this turns every never-list entry into pure
    toil and re-creates the pressure to widen the allowlist.
    """
    require("**Report it with the command, don't run it.**",
            "reporting with the ready command is the sanctioned half of this repair")
    require('git rev-list --left-right --count "refs/remotes/origin/<branch>...refs/heads/<branch>"',
            "the count must come from here, via the shared ref namespace")
    require("with no `-C` into their tree and\nno read of their working files",
            "the measurement itself must not touch the lane it describes")


def test_the_template_demonstrates_the_ready_command() -> None:
    """The template is what gets copied; a bare refusal there teaches a bare refusal."""
    i = RAW.index("**Divergences** (reported, NOT resolved")
    block = RAW[i:RAW.index("**Todos restored:**", i)]
    assert "not pulled" in block, block
    assert "pull --ff-only" in block, "the divergence line must carry the command it did not run"
