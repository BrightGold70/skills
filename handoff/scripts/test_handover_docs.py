"""HANDOVER mode's load-bearing guidance must stay in SKILL.md.

A mutation run on a sibling skill proved the failure mode this file exists to
stop: deleting a documented guarantee broke no test at all, so the guidance was
free to drift out while the code kept working. Prose that carries a rule needs a
test the same way code does.

Every assertion is a distinctive contiguous literal, whitespace-normalised so a
markdown reflow cannot break it, and each one names WHY it is load-bearing —
if a future edit trips one of these, the message should explain what it cost.
"""
from __future__ import annotations

from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"


def _norm(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


GUIDANCE = [
    (
        "| **HANDOVER** |",
        "the routing table is what picks the mode; without a row the section is unreachable",
    ),
    (
        "HANDOVER **composes with** `orca-cli` rather than replacing it",
        "orca-cli owns the same trigger words, so the boundary has to be stated or both "
        "fire and the model picks arbitrarily",
    ),
    (
        "Never reimplement that transport here.",
        "duplicating orca-cli's Full Handoffs commands creates two places to keep in sync",
    ),
    (
        "--feature \"<feature>\" --release",
        "the release step is the piece with no other home — omit it and the receiver "
        "inherits a claim only `--force` can break",
    ),
    (
        "`--force` is the verb for taking a feature from a session that is still *live*",
        "without the why, release reads as ceremony and gets skipped",
    ),
    (
        "Never `--claim --force` on the receiver's behalf",
        "silently forcing another session's claim hides a decision that is not the "
        "sender's to make (reworded while fixing agy M1; the rule is unchanged)",
    ),
    (
        "python3 \"$HP\" --repo \"<target-repo>\" dir",
        "the brief must be written into the RECEIVER's store; the --repo flag is how",
    ),
    (
        "a typo would otherwise produce a real-looking `docs/handoffs` directory that "
        "the writer creates, reports, and nobody ever reads",
        "explains why --repo refuses rather than resolving — the silent-success failure",
    ),
    (
        "Send the path, not the payload.",
        "a prompt carrying the whole doc decays the moment the doc changes",
    ),
    (
        "**stop monitoring**",
        "handing over and hovering is supervision, which is a different skill and a "
        "different request",
    ),
    (
        "Don't deliver before releasing the claim",
        "ordering is the whole point: released-after is indistinguishable from never",
    ),
    # --- WRITE must ROUTE foreign work, not just describe it ------------------
    (
        "## Route foreign-worktree work before closing out",
        "without this step WRITE files a foreign item in the sender's doc and calls "
        "it handled; the receiving session never learns of it",
    ),
    (
        "Recording an item's `repo · branch · worktree` (§\"Required template\") makes "
        "it *findable*. It does not make it *found*.",
        "the location rule reads as sufficient on its own — this is why it is not",
    ),
    (
        "READ mode resolves the canonical store of the repo it is invoked in",
        "the mechanical reason a foreign item parked here is unreachable: the only "
        "session that would act on it never reads this store",
    ),
    (
        "Recording the location is not the same as handing it over.",
        "the reminder has to sit at the point of authoring too, not only in the "
        "close-out phase, or the item is written wrong before the phase runs",
    ),
    (
        "a *good* entry in the wrong doc",
        "names the actual failure mode — quality of the entry is not the problem, "
        "so 'document it well' does not fix it",
    ),
]


@pytest.mark.parametrize(
    "literal,why", GUIDANCE, ids=[lit[:45] for lit, _ in GUIDANCE]
)
def test_handover_guidance_literal_present(literal: str, why: str) -> None:
    assert " ".join(literal.split()) in _norm(SKILL), f"SKILL.md dropped guidance: {why}"


def test_the_routing_phase_is_actually_wired_into_write() -> None:
    # Both halves must land together. A section can be written perfectly and
    # still be dead prose if the WRITE phase list never sends anyone to it —
    # which is exactly what a mutation proved: deleting the list entry left every
    # content assertion passing. Pin the reference, not just the section.
    text = _norm(SKILL)
    heading = "## Route foreign-worktree work before closing out"
    pointer = 'Proceed to §"Route foreign-worktree work before closing out"'
    assert heading in text, "the section is gone"
    assert pointer in text, (
        "WRITE's phase list no longer routes to the foreign-work step — the section "
        "exists but nothing reaches it, so a foreign item is filed and forgotten "
        "exactly as before"
    )
    # And it must run before the doc is committed, or the routing decision lands
    # after the artifact it should have changed.
    assert text.index(pointer) < text.index('Proceed to §"Commit and push"'), (
        "the foreign-work step must precede commit; routing after the commit "
        "cannot change what the doc says"
    )


def test_frontmatter_announces_four_modes() -> None:
    # The description is the only thing in context before the skill triggers, so
    # a HANDOVER section the description never mentions is a section that never
    # runs. "three modes" left behind is the specific stale-count bug.
    text = _norm(SKILL)
    assert "Use this skill in four modes." in text, (
        "the mode count is stale — HANDOVER will not be discovered from the description"
    )
    assert "Use this skill in three modes." not in text, "stale mode count left behind"


def test_frontmatter_carries_handover_triggers_and_the_boundary() -> None:
    text = _norm(SKILL)
    assert "HANDOVER mode — move ownership of tracked work" in text, (
        "the description must say what HANDOVER does or it cannot be selected"
    )
    for phrase, why in [
        ("hand off X to <worktree>", "the most common phrasing must appear verbatim"),
        ("Use the `orca-cli` skill directly instead", "the negative boundary keeps "
         "HANDOVER from stealing plain prompt-delivery requests"),
        ("`orchestration` skill when the user wants the work supervised", "supervised "
         "work is a different skill; without this the three overlap"),
    ]:
        assert " ".join(phrase.split()) in text, f"description dropped: {why}"


# --- agy review findings (2026-08-03) --------------------------------------
#
# An independent reviewer returned NEEDS_WORK on the skill with four Must-fix
# items, all verified true. Three of them were things a human had already
# hand-worked-around while running a real handover — the document stated a rule
# and withheld the command needed to obey it, so the agent improvises. These pin
# the fixes; each name says which finding it guards.

REVIEW_FIXES = [
    # M1 — the release step named a placeholder and no way to inspect the claim.
    (
        "python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py",
        "M1: the liveness question needs an oracle, not an eyeballed timestamp — "
        "and this one shares the writer's staleness window so they cannot disagree",
    ),
    (
        "**`owned_elsewhere`** → the owner is **LIVE**",
        "M1: the live/dead branch must be decidable from a command's output",
    ),
    (
        "No state file means no claim to release.",
        "M1: without this the agent invents a state-file path when none exists",
    ),
    # M2 — 'preserve the comment' with only the clobbering command supplied.
    (
        "`worktree-current` reads the worktree you are *in*, which is the sender",
        "M2: names why the WRITE-mode read command is the wrong tool here",
    ),
    (
        "preserving is something you do by *composing the new value*",
        "M2: worktree-comment always overwrites; the rule is unobeyable unless "
        "the agent knows preservation is its job, not the command's",
    ),
    # M3 — HANDOVER invoked from WRITE read as terminal.
    (
        "it does not mean end your turn",
        "M3: 'let go' read as terminal orphans the rest of WRITE — doc never committed",
    ),
    (
        "as a subroutine you return from",
        "M3: the calling side must say so too, not just the callee",
    ),
    # M4 — index prepend had no empty-file case.
    (
        "If the index has no `- ` bullet yet",
        "M4: a fresh index has no anchor; without a fallback the agent guesses",
    ),
    # S1 — READ Step 0/Step 3 overlap read as a contradiction.
    (
        "normally impossible here — Step 0 already fast-forwarded this exact case",
        "S1: explains the redundancy instead of leaving two rules that look contradictory",
    ),
    # S2 — orca-cli referenced with no way to reach it.
    (
        "Invoke the **`orca-cli` skill by name**",
        "S2: 'read the orca-cli skill' without saying how invites a path hunt",
    ),
    # S3 — compound 'wrap up AND hand off' matched two modes.
    (
        "**Compound requests are WRITE, not a coin flip.**",
        "S3: naming both modes at once must not resolve arbitrarily",
    ),
    # N2 — required-looking log column invited a fabricated path.
    (
        "Write `none` or `stdout` when there is no log file",
        "N2: a fabricated log path is worse than an absent one",
    ),
]


@pytest.mark.parametrize(
    "literal,why", REVIEW_FIXES, ids=[w.split(":")[0] + "-" + lit[:28] for lit, w in REVIEW_FIXES]
)
def test_review_fix_present(literal: str, why: str) -> None:
    assert " ".join(literal.split()) in _norm(SKILL), f"regressed: {why}"


# --- LEARN's documented output must match what learn.py prints -------------


def test_learn_step4_example_matches_the_real_renderer() -> None:
    # Found by dogfooding the new agy skill-reviewer template against LEARN mode.
    # The Step 4 example dropped the leading "- " and the "[confidence]" field, so
    # an agent checking its own run against the doc sees a mismatch and cannot tell
    # whether the save worked. Derive the shape from the renderer rather than
    # restating it, so the two cannot drift apart again.
    learn_py = SKILL.parent / "scripts" / "learn.py"
    render = " ".join(learn_py.read_text(encoding="utf-8").split())
    assert 'f"- {self.date_str} · {self.category} · [{self.confidence}]"' in render, (
        "learn.py's render() changed shape; update this test AND the Step 4 example together"
    )
    example = [
        ln for ln in SKILL.read_text(encoding="utf-8").splitlines()
        if "lightrag,nan-embed" in ln and "Learning saved" not in ln
    ]
    assert example, "the Step 4 success example is gone"
    for ln in example:
        stripped = ln.strip()
        assert stripped.startswith("- "), f"example lost the list bullet render() emits: {stripped[:60]}"
        assert "· [0.7] ·" in stripped, f"example lost the [confidence] field render() emits: {stripped[:60]}"


# --- READ Step 3 must reconcile PR state -----------------------------------

PR_STATE = [
    (
        "**PR state** — if the doc's Next Steps or Open Items name a PR",
        "the bullet itself; without it Step 3 has no PR check at all",
    ),
    (
        "gh pr view <N> --json state,mergedAt,title",
        "the runnable check — naming the hazard without the command is what this "
        "skill family keeps regressing into",
    ),
    (
        "git log --oneline -50 | grep -F '(#<N>)'",
        "a squash-merge lands under a rewritten title, so `gh` alone is not a "
        "complete answer — and `gh` may be absent or unauthenticated",
    ),
    (
        "do **not** silently assume it is still open",
        "an unverifiable PR state must be reported as unverified; assuming OPEN is "
        "what restores a stale merge instruction as the top todo",
    ),
]


@pytest.mark.parametrize("literal,why", PR_STATE, ids=[lit[:40] for lit, _ in PR_STATE])
def test_read_reconciles_pr_state(literal: str, why: str) -> None:
    # A PR claim is the only handoff state living entirely off the local machine,
    # so every other Step 3 check passes while it is stale. Observed: "merge PR
    # #18" survived into a resume as the top Next Step, hours after #18 merged.
    assert " ".join(literal.split()) in _norm(SKILL), f"READ lost its PR reconciliation: {why}"


def test_pr_state_is_in_step_3_not_orphaned_prose() -> None:
    # Both halves: the bullet is only reachable if it sits in the reconciliation
    # list. Pinning the text alone would pass with the bullet moved somewhere the
    # resume flow never reads.
    text = _norm(SKILL)
    step3 = text.split("### Step 3: Reconcile with reality")[1].split("### Step 4")[0]
    assert "**PR state**" in step3, "the PR bullet is not inside Step 3's reconciliation list"


# --- N1: extraction must not leave dangling pointers ----------------------

REFERENCES = SKILL.parent / "references"


def test_extracted_reference_files_exist() -> None:
    # N1 moved two WRITE phases out of SKILL.md to stop ~100 lines of secondary
    # rules diluting the critical path. An extraction that leaves the pointer
    # dangling is strictly worse than no extraction: the phase silently stops
    # happening and nothing says so.
    for name in ("auto-memories.md", "automation-scout.md"):
        path = REFERENCES / name
        assert path.is_file(), f"SKILL.md routes to references/{name} but it does not exist"
        assert path.read_text(encoding="utf-8").strip(), f"references/{name} is empty"


def test_skill_routes_to_both_reference_files() -> None:
    # Assert the ACTIONABLE instruction, not merely that the filename appears.
    # Each name is also mentioned in the WRITE phase list, so a bare `in text`
    # check stays green while the bullet that actually tells the agent to read
    # and follow the file is broken — a mutation proved exactly that.
    text = _norm(SKILL)
    for name, why in [
        ("references/auto-memories.md", "auto-memories is what makes a fact surface in "
         "FUTURE sessions; docs/learnings.md alone does not"),
        ("references/automation-scout.md", "the scout phase has no other caller"),
    ]:
        instruction = f"read `{name}` and follow it"
        assert instruction in text, (
            f"nothing instructs the agent to read {name} — the phase is unreachable ({why})"
        )


def test_extraction_kept_the_phases_mandatory_not_optional() -> None:
    # The risk of moving a step into a reference file is that it reads as
    # background material. Say plainly that it still runs.
    assert "They are real steps, not optional reading" in _norm(SKILL), (
        "extracted phases must not read as optional background"
    )


def test_write_phase_list_is_contiguously_numbered() -> None:
    # Renumbering after adding/removing a phase is exactly the kind of edit that
    # silently drops a step — a list going 1,2,3,4,5,7 means item 6 vanished.
    import re
    body = SKILL.read_text(encoding="utf-8").split("## After writing", 1)[1].split("\n---", 1)[0]
    nums = [int(m.group(1)) for m in re.finditer(r"^(\d+)\. ", body, re.M)]
    assert nums == list(range(1, len(nums) + 1)), f"phase list numbering is broken: {nums}"


# --- the receiving half: TAKEOVER ------------------------------------------
#
# HANDOVER was half a protocol. The sender released ownership and stopped
# watching; nothing told the receiver to CLAIM. A handed-over feature therefore
# sat owned by nobody, and a third session could start the same work without
# either side seeing a collision.
#
# Takeover lives inside READ rather than as a fifth mode — the same shape as
# WRITE's foreign-work routing. READ already locates the brief in the receiver's
# store and restores todos; it just could not tell a handover from a resume.

TAKEOVER = [
    (
        "### Step 3.5: Take over handed-over work",
        "the receiving half needs a step; without it READ restores todos and "
        "never claims, leaving the work owned by nobody",
    ),
    (
        "**Handover-From:** <sender-repo> · <sender-branch> · session <sender-session-id>",
        "the marker is what makes a brief machine-detectable; prose reads clearly "
        "to a human and is invisible to READ",
    ),
    (
        "Skip this unless the doc carries a `**Handover-From:**` line",
        "the step must be gated on the marker, or every ordinary resume tries to claim",
    ),
    (
        "--feature \"<feature>\" --claim \"<your-session-id>\"",
        "claiming is the step with no other home — the sender released, so someone "
        "must take it",
    ),
    (
        "`owned_elsewhere` → someone **live** holds it",
        "a handover can race a live session; taking it then is a collision, not a formality",
    ),
    (
        "A brief is a claim about the world made by a session that has stopped.",
        "premises must be re-verified on arrival; a confident brief is not evidence",
    ),
    (
        "Do not** silently work a handed-over item without claiming it",
        "the exact failure: sender let go, receiver started, state says nobody owns it",
    ),
    # The locate defect found while taking a real handover.
    (
        "a brief carrying `**Handover-From:**` is addressed to this repo, not to a branch",
        "a sender names the file for the branch they targeted, so a handover lands as "
        "`-main__` while the receiver sits on a feature branch and check 2 misses it",
    ),
    # S4 from the orca-cli review.
    (
        "`--no-parent` is the **default, not a rule**",
        "hardcoding it strips lineage the user explicitly asked for",
    ),
]


@pytest.mark.parametrize(
    "literal,why", TAKEOVER, ids=[lit[:42] for lit, _ in TAKEOVER]
)
def test_takeover_guidance_present(literal: str, why: str) -> None:
    assert " ".join(literal.split()) in _norm(SKILL), f"regressed: {why}"


def test_takeover_runs_before_the_todos_are_restored() -> None:
    # Ordering is load-bearing: the claim must land before the work becomes
    # yours. Restoring todos first and claiming later is indistinguishable from
    # never claiming if the session stops in between.
    text = _norm(SKILL)
    assert text.index("### Step 3.5: Take over handed-over work") < text.index(
        "### Step 4: Restore the TodoList"
    ), "takeover must precede the TodoList restore"


def test_handover_writes_the_marker_that_takeover_reads() -> None:
    # Both halves must land together, or the marker is written and never read
    # (or read and never written). Same both-halves rule as the WRITE routing step.
    text = _norm(SKILL)
    assert "Add the handover marker, directly under the" in text, (
        "HANDOVER no longer writes the marker, so takeover can never trigger"
    )
    assert "Skip this unless the doc carries a `**Handover-From:**` line" in text, (
        "READ no longer reads the marker, so writing it is pointless"
    )


# --- the stamp-preserve list must cover every prefix this skill writes -----
#
# WRITE stamps `handoff:`, HANDOVER Step 4 stamps `handover:`, TAKEOVER stamps
# `taken over:`. WRITE's rule knew only `handoff:`/`h-mad`, so it treated its own
# sibling modes' stamps as human notes and appended — a worktree would accumulate
# `handover: … — handoff: … — handoff: …` instead of one current checkpoint. Hit
# live while stamping a real takeover.

_PREFIXES = ["handoff:", "handover:", "taken over:", "h-mad"]


def test_both_preserve_rules_list_every_prefix_this_skill_writes() -> None:
    text = _norm(SKILL)
    write_rule = "does not already start with `handoff:`, `handover:`, `taken over:` or `h-mad`"
    handover_rule = "does **not** start with `handoff:`, `handover:`, `taken over:` or `h-mad`"
    assert write_rule in text, (
        "WRITE's stamp-preserve list is missing a prefix this skill writes; it will "
        "append to its own sibling modes' stamps instead of replacing them"
    )
    assert handover_rule in text, "HANDOVER Step 4's preserve list drifted from WRITE's"


def test_the_two_preserve_lists_are_identical() -> None:
    # Two rules that must agree are two places to forget. Pin the agreement, not
    # just each list — this defect was exactly a drift between them.
    text = _norm(SKILL)
    for p in _PREFIXES:
        occurrences = text.count(f"`{p}`")
        assert occurrences >= 2, (
            f"prefix `{p}` appears in {occurrences} preserve rule(s); WRITE and "
            "HANDOVER Step 4 must both list it"
        )


def test_the_reason_is_stated_not_just_the_list() -> None:
    assert "treats its sibling modes' stamps as human notes" in _norm(SKILL), (
        "without the why, a future edit trims the list back to the mode it is reading"
    )
