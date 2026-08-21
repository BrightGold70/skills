"""READ Step 4 must never be a no-op, and Step 5 must name the sink it used.

The defect these pin was invisible in exactly the way that matters: Step 4 said
"use the TodoList tool", no such tool was in that session's tool set, and every
other part of READ succeeded. The reconciliation was correct, the action queue
was never written, and the report distinguished neither -- `**Todos restored:** N`
prints identically whether N items reached a durable list or nothing at all.

Availability is per-SESSION, not per-install: `TaskCreate` was in daily use on
this machine through 2026-08-19 (last call 2026-08-19T07:11:39Z) and was absent
the next morning with no config change. Call counts are point-in-time and are
deliberately not pinned -- see test_call_count_is_not_load_bearing. So the ladder's job is not "cope with a machine that lacks the tool" but
"re-probe every resume and use the best sink that exists right now".

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
            "CLAUDE_CODE_ENABLE_TODO_TOOLS",
            "the todo tools became OPT-IN in Claude Code 2.1.236; a reader whose "
            "probe comes back empty must be sent to the opt-in before the ladder, "
            "or they degrade to a lesser sink while the real tool is one setting away",
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


# --- the corrected diagnosis (2026-08-20) -----------------------------------
#
# The first fix shipped with the report's reasoning intact: "zero TodoWrite
# tool_use calls across every transcript" therefore "no todo tool on this
# machine". Both halves were wrong in a way the conclusion hid -- the name in
# use was TaskCreate (hundreds of calls), and counting calls measures USE, not
# AVAILABILITY. The tool was live through 2026-08-19 and gone the next morning.
# A reader who believes "this install has no todo tool" stops probing, and rung 1
# stays dead after it comes back.


def test_presence_is_documented_as_varying_not_permanent() -> None:
    for literal, why in [
        (
            "its presence varies between sessions on the same machine",
            "'this install has no todo tool' makes a reader stop probing; the "
            "tool returned availability is per-session",
        ),
        (
            "a live check every time, never a fact you carry from the last resume",
            "the check has to re-run, or the ladder freezes on rung 2 forever",
        ),
    ]:
        require(literal, why)


def test_the_invalid_inference_is_named_so_it_is_not_repeated() -> None:
    for literal, why in [
        (
            "Absence of calls is not absence of the tool",
            "counting tool_use is the measurement that produced the wrong diagnosis",
        ),
        (
            "byte-identical to one where it never existed",
            "the indistinguishability is the reason the method cannot work, not a caveat",
        ),
        (
            "A mention is not a tool",
            "hook matchers and agent catalogs carry the name and prove nothing",
        ),
    ]:
        require(literal, why)


def test_rung_one_is_preferred_when_present() -> None:
    require(
        "Prefer this rung when it exists",
        "a durable fallback that outranks the real todo list is a regression: "
        "rung 1 is the only sink the user can see and tick off",
    )


def test_no_claim_that_the_tool_is_permanently_absent() -> None:
    for banned in (
        "some Claude Code installs ship no",
        "zero `TodoWrite` tool_use calls",
    ):
        assert " ".join(banned.split()) not in DOC, (
            f"the retracted claim survives in SKILL.md: {banned!r}"
        )


def test_toolsearch_probe_is_justified_as_not_deferred_only() -> None:
    """An empty `select:` result must be readable as genuine absence.

    ToolSearch's own description is about *deferred* tools, which invites the
    reader to suspect an empty result only means "loaded, not deferred" -- i.e.
    a false negative. Measured 2026-08-21: `select:Bash,Read,Write` returns full
    schemas for tools already in the main tool list, so it resolves non-deferred
    tools too and an empty result is real. Without this in the doc the next
    reader re-derives the doubt and either re-probes or abandons rung 1.
    """
    for literal, why in [
        ("not deferred-only",
         "the probe's soundness is the whole basis for skipping rung 1"),
        ("select:Bash,Read,Write",
         "the measurement that settles it must be reproducible by the reader"),
    ]:
        require(literal, why)


def test_call_count_is_not_load_bearing() -> None:
    """A corpus count is point-in-time; the doc must not rest on one figure.

    An earlier pass recorded 465 TaskCreate calls; a re-count on 2026-08-21 over
    2,734 transcripts returned 429. Neither is obviously wrong -- they did not
    count the same thing -- so a bare figure invites a future reader to "correct"
    it and call the disagreement a defect. The durable facts are the last-seen
    timestamp and the run of zeroes after it.
    """
    for literal, why in [
        ("2026-08-19T07:11:39Z",
         "the last-seen timestamp is the fact that dates the disappearance"),
        ("Do not treat the call count as a fixed figure",
         "stops a future reader filing the 465/429 disagreement as a defect"),
    ]:
        require(literal, why)


def test_inline_checklist_is_mandatory_when_rung_1_is_missing() -> None:
    """The durable sink is invisible; a count alone reads as "todos vanished".

    Reported by the operator 2026-08-21: after a resume restored 6 items to
    `.omc/notepad.md`, the todos were experienced as missing. Both halves of the
    report were true and neither showed the user their queue.
    """
    for literal, why in [
        ("print the inline checklist IN ADDITION",
         "the durable rung is not user-visible, so it cannot be the only sink",
        ),
        ("reads to them as \"my todos disappeared\"",
         "names the observed complaint so a future edit cannot dismiss it as cosmetic",
        ),
    ]:
        require(literal, why)


def test_empty_probe_sends_the_reader_to_the_opt_in_first() -> None:
    """The ladder is the fallback, not the first move.

    An earlier revision of this skill asserted "no user config can add a built-in
    tool" and told the reader not to try re-enabling anything. That was refuted on
    2026-08-21: Claude Code 2.1.236 made the todo tools opt-in, all four names are
    still in the 2.1.238 binary, and `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` in the
    settings `env` block restores them -- proven by a control/treatment A/B where
    the control replied NOTOOL and the treatment emitted a real TaskCreate
    `tool_use`. A doc that forbids the fix sends every future reader to a lesser
    sink while rung 1 sits one setting away.
    """
    for literal, why in [
        # Each literal must be UNIQUE to this guidance. A first pass pinned the bare
        # string "2.1.236", which already appears elsewhere in SKILL.md -- the guard
        # passed with the opt-in section deleted. Measured as MUTATION: SURVIVED.
        ("try the opt-in BEFORE the ladder",
         "the ordering IS the fix; the ladder is the fallback, not the first move"),
        ('{ "env": { "CLAUDE_CODE_ENABLE_TODO_TOOLS": "1" } }',
         "the reader needs the exact knob in copy-pasteable form"),
        ("**opt-in** in Claude Code **2.1.236**",
         "dates the change AND is unique to this section, unlike a bare version string"),
        ("were gated, not removed",
         "the distinction is the whole remedy -- removed would mean nothing to do"),
        ("todoFeatureEnabled",
         "the panel setting is a different switch; enabling only it leaves tools absent"),
    ]:
        require(literal, why)
