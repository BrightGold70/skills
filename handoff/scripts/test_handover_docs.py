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
        "Do not `--force` on their behalf; the receiver decides",
        "silently forcing another session's claim hides a decision that is not the "
        "sender's to make",
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
