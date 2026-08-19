"""READ Step 4 must never be a no-op, and Step 5 must name the sink it used.

The defect these pin was invisible in exactly the way that matters: Step 4 said
"use the TodoList tool", the tool did not exist in the install, and every other
part of READ succeeded. The reconciliation was correct, the action queue was
never written, and the report distinguished neither -- `**Todos restored:** N`
prints identically whether N items reached a durable list or nothing at all.

Guidance is the whole fix (no user config can add a built-in tool), so the
guidance is what gets pinned. Literals are whitespace-normalised so a markdown
reflow cannot break them.
"""

from __future__ import annotations

import re

import pytest

from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"
RAW = SKILL.read_text(encoding="utf-8")
DOC = " ".join(RAW.split())


def require(literal: str, why: str) -> None:
    assert " ".join(literal.split()) in DOC, f"handoff/SKILL.md dropped guidance: {why}"


def test_step4_states_the_tool_is_not_guaranteed() -> None:
    for literal, why in [
        (
            "this step must never be a no-op",
            "the no-op is the defect; naming it is what stops a future rewrite "
            "from collapsing the ladder back to one tool",
        ),
        (
            "A todo-authoring tool is *not* guaranteed",
            "an unconditional instruction is the bug, not the tool's absence",
        ),
        (
            "no user config can add a built-in",
            "without this a reader burns the session trying to re-enable the tool",
        ),
    ]:
        require(literal, why)


@pytest.mark.parametrize(
    "rung, why",
    [
        ("`TaskCreate`, `TodoWrite`, or equivalent",
         "rung 1 must still be preferred where it exists"),
        ("mcp__plugin_oh-my-claudecode_t__notepad_write_working",
         "rung 2 is the only DURABLE sink; naming the exact tool is what makes it usable"),
        ("An inline numbered checklist in the Step 5 report",
         "rung 3 is always reachable, so the ladder cannot bottom out"),
    ],
)
def test_all_three_rungs_are_named(rung: str, why: str) -> None:
    require(rung, why)


def test_the_rungs_are_ordered_as_a_ladder() -> None:
    # A set of options is not a ladder. If rung 3 could be read as co-equal with
    # rung 1, "restored to this report only" becomes a legitimate first choice.
    order = [
        DOC.index("A task/TodoList tool"),
        DOC.index("mcp__plugin_oh-my-claudecode_t__notepad_write_working"),
        DOC.index("An inline numbered checklist in the Step 5 report"),
    ]
    assert order == sorted(order), f"rungs are out of order: {order}"
    require("Take the first sink that exists", "the selection rule, not just the list")


def test_step4_rules_survive_the_sink_choice() -> None:
    # The prefix/verify-note/dedupe rules predate the ladder and are properties of
    # the todos. A ladder that silently scoped them to rung 1 would be a
    # regression dressed as a fix.
    require(
        "every rule below still applies",
        "the prefix, verify-path note, and dedupe rules are sink-independent",
    )


def test_step5_names_the_sink() -> None:
    for literal, why in [
        (
            "**Todos restored to:** <task tool | .omc/notepad.md | this report only>",
            "an unnamed sink is what made the failure silent",
        ),
        (
            "write it out in full rather than truncating to the first item",
            "when the report IS the list, truncating it discards the restore",
        ),
    ]:
        require(literal, why)


def test_the_report_template_demonstrates_the_sink_line() -> None:
    # A rule stated in prose but absent from the template gets copied out of the
    # template and lost.
    block = RAW.split("## Session resumed", 1)[1].split("```", 1)[0]
    assert "Restored to:" in block, "the fenced report template omits the sink line"


def test_frontmatter_does_not_advertise_a_hard_dependency() -> None:
    front = RAW.split("---", 2)[1]
    assert "restoring the TodoList" not in front, (
        "the description still promises a TodoList restore, which is the "
        "hard dependency this fix removed"
    )
    assert "never no-ops" in " ".join(front.split()), (
        "the description should say the step always lands somewhere"
    )


def test_handover_letting_go_accounts_for_a_durable_sink() -> None:
    # Introducing a durable sink creates a matching obligation: an item handed
    # over but left in .omc/notepad.md returns on the next resume as work you own.
    require(
        "dropping* means editing that file",
        "HANDOVER Step 6 must delete from a durable list, not merely stop mentioning it",
    )


def test_write_side_hedge_is_unchanged() -> None:
    # WRITE already had the correct shape; it is the model Step 4 was rewritten
    # against. If it ever hardens, the asymmetry comes back facing the other way.
    require(
        "if you have a TodoList / task tool, read it",
        "the WRITE gather step must stay conditional",
    )


def test_no_unconditional_todo_tool_instruction_remains() -> None:
    # The value sweep, mechanised: any surviving imperative that assumes the tool.
    bad = [
        (i, ln)
        for i, ln in enumerate(RAW.splitlines(), 1)
        if re.search(r"[Uu]se the TodoList tool|[Uu]se TodoWrite|[Cc]reate TodoWrite", ln)
    ]
    assert not bad, f"unconditional todo-tool instruction survives: {bad}"
