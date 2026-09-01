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
        # Pinned on the script name, not the path: the rule is "ask the oracle",
        # and the invocation moved to the ${CLAUDE_SKILLS_ROOT:-…} form the rest of
        # this skill uses for its own scripts.
        "h_mad_resume_decision.py",
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


# --- the scout must reconcile, not only append ------------------------------

SCOUT = SKILL.parent / "references" / "automation-scout.md"


def test_scout_reconciles_open_rows_before_appending() -> None:
    # The scout is the ONLY writer of docs/skill-candidates.md, and it was
    # append-only: the file's header demands "reconcile a row when the thing it
    # describes ships" while nothing ever did. Measured 2026-08-03 — five rows sat
    # at `candidate: yes` and four described already-shipped work, so the backlog
    # had to be re-derived by hand. This is the inverse hazard shape: a rule stated
    # in an artifact that never reaches the step obliged to act on it.
    text = " ".join(SCOUT.read_text(encoding="utf-8").split())
    assert "### Reconcile the open rows FIRST" in text, "the scout is append-only again"
    assert "before** appending" in text, "ordering matters: appending first dilutes the pass"
    assert "grep -nE '^- \\*\\*.*candidate: \\**yes' docs/skill-candidates.md" in text, (
        "the runnable command must be present, anchored on the row shape (an unanchored "
        "grep matches the file's own prose), AND tolerant of a bolded verdict — bold is "
        "this file's convention for terminal states, so `candidate: **yes**` was "
        "invisible to this check the first time the step ran"
    )
    assert "against source, not against the label" in text, (
        "a row is a claim by a past session; trusting the label is what let 4 stale "
        "rows survive"
    )
    assert "A `no` can still name an upgrade" in text, (
        "the verdict answers 'is this a new skill?', not 'should an existing skill "
        "change?' — one row sat inert while naming its own insertion point"
    )


def test_write_phase_says_the_scout_reconciles() -> None:
    # Both halves: the reference carries the step, and the WRITE phase list has to
    # say the scout does more than append, or a reader skimming WRITE skips it.
    assert "reconciles the open `docs/skill-candidates.md` rows before appending" in _norm(SKILL), (
        "WRITE's scout bullet still describes an append-only phase"
    )


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
    # Named separately so a rename reports itself as a missing heading rather
    # than as a bare `ValueError: substring not found` from .index().
    takeover = "### Step 3.5: Take over handed-over work"
    restore = "### Step 4: Restore the todo list"
    assert takeover in text, f"heading missing or renamed: {takeover!r}"
    assert restore in text, f"heading missing or renamed: {restore!r}"
    assert text.index(takeover) < text.index(restore), (
        "takeover must precede the todo-list restore"
    )


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


# --- Structural invariants of the runnable guidance -------------------------
#
# The four checks below are not literal pins. Each one encodes a defect that was
# measured in this file's own instructions and would otherwise be free to come
# back the next time a block is edited or copied.


def _fenced_blocks() -> list[tuple[int, str, str]]:
    """(first-line-number, enclosing heading, body) for every fenced block."""
    import re

    lines = SKILL.read_text(encoding="utf-8").splitlines()
    out: list[tuple[int, str, str]] = []
    cur: list[str] | None = None
    start = 0
    section = "(top)"
    block_section = "(top)"
    for lineno, line in enumerate(lines, 1):
        heading = re.match(r"^#{2,4} (.+)", line)
        if heading:
            section = heading.group(1)
        if line.strip().startswith("```"):
            if cur is None:
                cur, start, block_section = [], lineno, section
            else:
                out.append((start, block_section, "\n".join(cur)))
                cur = None
            continue
        if cur is not None:
            cur.append(line)
    return out


def test_every_fenced_block_defines_the_shell_vars_it_uses() -> None:
    """Shell state does NOT survive between tool calls, so each block must stand alone.

    Measured: §Commit used `$HP`, `$FILE` and `$LEARN`, all set in an earlier
    block of an earlier section. In a fresh shell they expand to empty, so the
    documented finale ran `python3 "" root` and `git add ""`. Step 3.5 used
    `$STATE` that nothing in READ ever set.
    """
    import re

    offenders = []
    for start, section, body in _fenced_blocks():
        used = set(re.findall(r"\$\{?([A-Z][A-Z0-9_]{1,})\}?", body))
        used -= {"HOME", "PATH", "CLAUDE_SKILLS_ROOT"}
        defined = set(re.findall(r"^\s*([A-Z][A-Z0-9_]*)=", body, re.M))
        if used - defined:
            offenders.append(f"line {start} [{section}]: {sorted(used - defined)}")
    assert not offenders, (
        "fenced blocks use shell variables they do not define:\n  "
        + "\n  ".join(offenders)
    )


def test_no_recursive_glob_in_any_fenced_block() -> None:
    """`**/` is a silent fail-open under the shell this skill actually runs in.

    Measured: with bash's default `globstar` off, `<repo>/**/docs/.bkit-memory.json`
    matches only ONE directory level, so a real state file two levels down is not
    found — and HANDOVER Step 2 then reports "nothing is claimed" and skips the
    release. Under zsh an unmatched `**/` additionally errors past `2>/dev/null`.
    Use `find` instead.
    """
    offenders = [
        f"line {start} [{section}]"
        for start, section, body in _fenced_blocks()
        if "**/" in body
    ]
    assert not offenders, (
        "recursive-glob patterns found (use `find`): " + ", ".join(offenders)
    )


def test_orca_is_only_ever_reached_through_the_wrapper() -> None:
    """The skill states twice that it never calls `orca` directly. Prose must agree.

    Measured: two steps prescribed `orca worktree list` for `childWorktreeIds`,
    which no wrapper verb exposed at the time — so the rule was unsatisfiable and
    the instructions simply contradicted it. `hmad-dispatch worktree-list` now
    carries that payload. Lines that tell the reader NOT to run something are
    exempt: they are the rule being stated, not broken.

    Third exemption: prose that names the *raw* `orca` form in order to contrast
    it with the wrapper (\"a raw `orca worktree ps --json` needs `.result…`\").
    The word `raw` is what marks it as the un-wrapped form being pointed at, so
    the exemption keys on that and not on the command itself.
    """
    import re

    offenders = []
    for lineno, line in enumerate(SKILL.read_text(encoding="utf-8").splitlines(), 1):
        for match in re.finditer(r"`orca ([a-z][a-z-]*)", line):
            if (
                line.lstrip().startswith("- Don't")
                or "never call" in line
                or "raw `orca" in line.lower()
            ):
                continue
            offenders.append(f"line {lineno}: orca {match.group(1)}")
    assert not offenders, (
        "direct `orca` invocations outside the sanctioned don't-lines: "
        + "; ".join(offenders)
    )


def test_example_handoff_filenames_carry_the_branch_separator() -> None:
    """Every example must show the `<branch>__<slug>` form READ actually matches.

    An example in the older `YYYY-MM-DD-<slug>.md` shape teaches a filename that
    READ's exact-branch check cannot find, in the two places a reader is most
    likely to copy from: the resume report and the INDEX entry.
    """
    import re

    text = SKILL.read_text(encoding="utf-8")
    bad = [
        name
        for name in re.findall(r"handoffs/(\d{4}-\d{2}-\d{2}-[A-Za-z0-9_.-]+\.md)", text)
        if "__" not in name
    ]
    assert not bad, f"example handoff filenames missing the `__` separator: {bad}"


# --------------------------------------------------------------------------
# The commit finale must reach a destination on every route.
#
# The defect these pin: §Save writes into the canonical main-worktree store, and
# the finale used to decline to commit whenever it ran from a linked worktree.
# Both halves were individually right and jointly broken — nothing closed the
# loop between them, so the honest "I did not commit this" note was the last
# thing that ever happened to the file. Three docs orphaned on 2026-08-29.
# --------------------------------------------------------------------------

COMMIT_ROUTING = [
    (
        "handoff/scripts/handoff_commit.py",
        "the finale must route through the script; a hand-written branch on ROOT "
        "is what dropped the linked-worktree case on the floor",
    ),
    (
        "every one of them ends with the file reachable from a ref",
        "states the property the three destinations exist to hold — without it a "
        "future edit can add a fourth route that simply declines again",
    ),
    (
        "refs/handoffs/<branch-slug>",
        "names the destination for the case that actually bites: linked worktree "
        "plus a dirty or off-default canonical tree",
    ),
    (
        "It moves no HEAD, stages nothing and touches no working tree",
        "the reason the original objection no longer justifies skipping — drop "
        "this and the skip looks reasonable again",
    ),
    (
        "those commands carry no `-C`, so they act on the session's cwd",
        "in `direct`/`ref` mode the commit lands in the canonical tree while cwd is "
        "a linked worktree; following §Sync/§Push there rebases and pushes the "
        "WRONG branch and reports the handoff as pushed",
    ),
    (
        "Never `git merge` the ref",
        "the ref's first parent can be an arbitrary stale feature tip; merging "
        "would drag that whole history onto the default branch",
    ),
]


@pytest.mark.parametrize(
    "literal,why", COMMIT_ROUTING, ids=[lit[:45] for lit, _ in COMMIT_ROUTING]
)
def test_commit_routing_literal_present(literal: str, why: str) -> None:
    assert " ".join(literal.split()) in _norm(SKILL), f"SKILL.md dropped guidance: {why}"


def test_no_route_through_the_finale_declines_to_commit() -> None:
    # The regression guard. The old prose read "Do **not** auto-commit into the
    # main worktree's branch" and offered no alternative; any wording that
    # re-introduces a terminal decline puts the orphan bug back.
    text = _norm(SKILL)
    for banned in (
        "Do **not** auto-commit into the main worktree's branch",
        "committing/pushing it is a deliberate step to run from the main worktree",
    ):
        assert " ".join(banned.split()) not in text, (
            "the finale declines to commit again with no destination — this is the "
            "exact prose that orphaned three handoff docs"
        )


def test_the_commit_script_is_reachable_from_the_write_phase_list() -> None:
    # Same both-halves-must-land rule as the foreign-work step: the section can
    # be perfect and still be dead prose if WRITE never sends anyone to it.
    text = _norm(SKILL)
    assert 'Proceed to §"Commit and push"' in text, (
        "WRITE's phase list no longer routes to the commit finale"
    )
    assert (SKILL.parent / "scripts" / "handoff_commit.py").is_file(), (
        "SKILL.md points at handoff_commit.py but the script is not shipped"
    )


# --- Step 7: checking once is not monitoring --------------------------------


def test_step_7_exists_and_is_distinguished_from_supervision() -> None:
    """Step 6 says stop monitoring and Step 5 says the receipt proves nothing.
    Between them sat a real gap: asking ONCE, later, whether it was picked up."""
    text = SKILL.read_text(encoding="utf-8")
    doc = " ".join(text.split())
    assert "### Step 7 (optional, later): check ONCE that it landed" in text
    assert "Not a walk-back of Step 6" in doc, (
        "the step must say why it does not contradict `stop monitoring`")
    assert "handover_landed.py" in doc


def test_unknown_is_not_reported_as_not_yet() -> None:
    """The asymmetry that makes this safe for a sender who has already let go."""
    doc = " ".join(SKILL.read_text(encoding="utf-8").split())
    assert "`UNKNOWN` (rc 2) is not `NOT_YET` (rc 1)" in doc
    assert "re-deliver work that is already in progress" in doc


def test_the_unimplemented_third_signal_is_named_with_its_reason() -> None:
    """A dropped requirement that is not written down reads as an oversight, and
    the next reader re-derives it. The blocker is a missing wrapper verb."""
    doc = " ".join(SKILL.read_text(encoding="utf-8").split())
    assert "deliberately **not** implemented" in doc
    assert "no wrapper verb reads an arbitrary terminal handle" in doc
