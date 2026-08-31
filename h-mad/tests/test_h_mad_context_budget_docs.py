"""The orchestrator's own window is a consumable, and one tool call can end a run.

`advisor()` forwards the WHOLE transcript to a second model and bills it into the
same turn, so the turn costs ~2x the current context. Nothing at the call site shows
that -- the visible return is ~4KB of advice -- and the cost scales with session age,
so the identical call is free in Phase 1 and fatal in Phase 6. It is fatal in Phase 6
specifically because the tool's own guidance ("call before declaring done") points
there, which means the failure is not carelessness: following the instructions is
what triggers it.

Measured live: a call at 525,742 on a 1M window produced a 1,056,891-token turn and
overflowed. From the UI that reads as "context suddenly full from ~50% remaining".

These tests keep the load-bearing facts in SKILL.md. Docs decay by having their
numbers and caveats trimmed as noise long before any code changes, and every fact
below is one whose removal turns the section into a suggestion:

  * the multiplier and the ceiling -- without them "be careful" is unactionable;
  * "no parameters" -- without it the reader looks for a way to send less, and there
    is none;
  * the substitute ladder -- without it the only escape looks like /compact, which
    is the lossy last resort, not the fix;
  * "snapshotted at call time" -- without it the reader batches the call with a
    heavy read turn and pays for both.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_MD = REPO_ROOT / "h-mad" / "SKILL.md"

MARKER = "## Orchestrator context hygiene (your own window)"


def _section() -> str:
    """Body from MARKER to the next h2, whitespace-normalised.

    Bounded on top-level `## ` only: the section owns `###` subsections, and a
    boundary that accepted them would cut the extract before the ladder -- every
    assertion about the ladder would then fail for the wrong reason. Fences are
    tracked because the bash block contains `#` comments, and a naive
    startswith("#") ends the section inside its own example.
    """
    text = SKILL_MD.read_text()
    assert MARKER in text, "the orchestrator context-hygiene section is gone"
    body = text.split(MARKER, 1)[1]

    kept, in_fence = [], False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            kept.append(line)
            continue
        if not in_fence and line.startswith("## "):
            break
        kept.append(line)
    section = "\n".join(kept)
    # A runaway extract is not evidence about anything; fail here rather than
    # asserting against the rest of the document. The number only has to sit far
    # below a real runaway — a broken boundary runs to end-of-file, thousands of
    # lines — so it is a detector, not a prose budget. Re-anchored 140 -> 160 on
    # 2026-08-24 when J44's root cause joined the section (the previous author was
    # squeezing under it at 139).
    assert len(section.splitlines()) < 160, "section boundary ran away"
    return " ".join(section.split())



def _titled_section(text: str, title: str) -> str:
    """The named `##` section, bounded by the NEXT `##` heading.

    Distinct from `_section()` above, which extracts one fixed MARKER section.

    Not a fixed-width slice. A character window silently stops covering the end of
    its own section the moment anyone adds a paragraph to it, so the assertions
    below would go quietly vacuous exactly when the section grew -- measured: a
    routing paragraph added to the run-ceiling section pushed the `HALT`/`DENY`
    distinction past a 4000-char window and turned a real pin into a failure whose
    honest reading was "the test lost sight of the text", not "the doc regressed".
    """
    start = text.index(title)
    nxt = text.find("\n## ", start + 1)
    return text[start:] if nxt == -1 else text[start:nxt]

class TestThePrice:
    def test_states_the_payload_is_unselectable(self):
        """The first question a reader asks is "can I send it less?". No."""
        s = _section()
        assert "no parameters" in s
        assert "entire transcript" in s

    def test_keeps_the_measured_multiplier(self):
        s = _section()
        assert "2.03" in s and "2.01" in s
        assert "525,742" in s and "1,056,891" in s

    def test_states_the_50_percent_consequence_in_one_line(self):
        s = _section()
        assert "At 50% used, one advisor call = 100%" in s

    def test_says_the_spike_is_transient_but_the_overflow_is_not(self):
        """Both halves matter: transient stops over-restriction, unrecoverable
        stops the "I'll compact afterwards" plan."""
        s = _section()
        assert "transient, not cumulative" in s
        assert "recoverable by compacting afterwards" in s

    def test_counts_the_non_free_session_start(self):
        s = _section()
        assert "86k" in s

    def test_names_where_the_guidance_itself_points(self):
        """Without this the rule reads as contradicting the advisor tool, and a
        contradiction with no explanation gets resolved in favour of the tool."""
        s = _section()
        assert "before declaring done" in s


class TestTheCeiling:
    def test_pins_45_and_says_why_it_is_not_50(self):
        s = _section()
        assert "45%" in s
        assert "floor" in s

    def test_names_the_measuring_command_and_its_token(self):
        s = _section()
        assert "h_mad_context_budget.py" in s
        assert "CTXBUDGET:" in s
        assert "never `$?`" in s

    def test_distinguishes_budget_remaining_from_window_used(self):
        """`<total_tokens>` is the number in front of the reader; if the doc does
        not disqualify it, it is the number they will use."""
        s = _section()
        assert "total_tokens" in s
        assert "budget *remaining*" in s

    def test_says_unknown_carries_no_used_count(self):
        s = _section()
        assert "UNKNOWN" in s
        assert "no `used=`" in s


    def test_names_how_the_transcript_is_found_and_why_not_by_path(self):
        """A tool that reports UNKNOWN from the reader's actual cwd gets abandoned,
        and the mtime shortcut fails toward a false OK with two sessions open. Both
        rejected alternatives have to stay named or someone re-adds them."""
        s = _section()
        assert "CLAUDE_CODE_SESSION_ID" in s
        assert "any cwd" in s
        assert "newest-mtime" in s
        assert "false `OK`" in s


class TestChannelRouting:
    def test_agy_is_the_default_not_advisor(self):
        """The whole point of the section: advisor() is the exception. If this line
        softens, the expensive channel silently becomes the default again."""
        s = _section()
        assert "**agy is**" in s
        assert "hardest calls only" in s

    def test_routes_by_required_input_not_by_difficulty(self):
        """"Hard vs easy" is unjudgeable in the moment; "what must this advice read"
        is a fact about the question."""
        s = _section()
        assert "required input" in s
        assert "unjudgeable in the moment" in s
        # the NEGATION is the load-bearing half: naming the required input while
        # still inviting a difficulty judgement leaves the old, unusable rule in place
        assert "not by how hard the question feels" in s

    def test_the_three_channels_and_their_distinguishing_property(self):
        s = _section()
        assert "hmad-dispatch exec agy" in s
        assert 'subagent_type: "fork"' in s
        assert "your** model" in s or "your model" in s
        assert "second copy of the session" in s

    def test_names_the_cost_of_defaulting_to_agy(self):
        """A fresh reviewer confidently re-proposes the thing you just reverted.
        Without this warning the default is a trap when you are stuck."""
        s = _section()
        assert "trajectory awareness" in s
        assert "rolled back five minutes ago" in s
        assert "failed attempts" in s

    def test_maps_the_phases_both_ways(self):
        s = _section()
        assert "Phases 1–4" in s
        assert "6a-prime" in s
        assert "5d/5e" in s and "6b" in s
        assert "wrong tool" in s

    def test_keeps_advisor_early_and_compact_last(self):
        s = _section()
        assert "Phases 1–3" in s
        assert "/compact" in s and "lossy" in s
        assert "**after** the overflow recovers nothing" in s

    def test_bans_batching_the_call_into_a_heavy_turn(self):
        s = _section()
        assert "snapshotted at call time" in s


class TestMechanicalEnforcement:
    def test_names_the_hook_and_the_settings_wiring(self):
        s = _section()
        assert "h-mad-advisor-warn.sh" in s
        assert "PostToolUse" in s
        assert '"matcher": "*"' in s

    def test_says_why_it_cannot_be_a_gate(self):
        """J44: `advisor` is a server-side tool that no tool-scoped hook event
        fires for. Without the reason travelling with the section, the next reader
        sees an advisory where a gate would do and re-proposes the matcher that
        provably never runs."""
        s = _section()
        assert "server_tool_use" in s
        assert "J44" in s
        assert "advisory, not a gate" in s

    def test_does_not_assert_wiring_needs_a_relaunch(self):
        """The old text said hooks are snapshotted at session start, so wiring takes
        effect NEXT session. Measured false on 2.1.241: a registration added
        mid-session was invoked ~13 minutes later in the same session. The section
        must tell the reader to VERIFY rather than to assume either way — an
        unverifiable claim here is what let J44's dead hook look installed."""
        s = _section()
        assert "measured false" in s
        assert "Verify it fires" in s
        assert "do not assume either way" in s

    def test_gives_a_live_fire_test_and_names_silent_stand_down_as_the_finding(self):
        s = _section()
        assert "HMAD_CONTEXT_WINDOW=1000" in s
        assert "stands down silently" in s

    def test_states_the_silent_direction_and_why(self):
        """A warning fired on a cannot-judge trains the reader to ignore it, and
        then the one that matters lands on deaf ears."""
        s = _section()
        assert "stays silent" in s
        assert "set -euo" in s

    def test_states_that_there_is_no_override(self):
        """The gate needed one because it could refuse. An advisory that ships an
        escape hatch is telling the reader it blocks."""
        s = _section()
        assert "**no override env var**" in s
        assert "nothing to escape" in s

    def test_states_the_two_limits(self):
        s = _section()
        assert "only sessions where it is wired" in s
        assert "defaults to 1M" in s


def test_never_list_carries_the_rule():
    """A rule that lives only in a prose section is advisory. The NEVER list is
    where this skill's non-negotiables are read from."""
    text = SKILL_MD.read_text()
    never = text.split("## What you NEVER do", 1)[1].split("\n## ", 1)[0]
    assert "advisor()" in never
    assert "45%" in never
    assert "CTXBUDGET:" in never
    assert "h-mad-advisor-warn.sh" in never


def test_helper_script_is_listed():
    text = SKILL_MD.read_text()
    helpers = text.split("## Helper scripts", 1)[1]
    assert "h_mad_context_budget.py" in helpers


class TestRunCeilingDocumented:
    """The 80% run ceiling is only real if SKILL.md obliges someone to read it.

    A ceiling documented as advice is the shape this repo keeps re-learning: the
    PREFLIGHT token was correct and advisory for a long time, and an advisory signal
    nobody is obliged to consume is worth about as much as no signal.
    """

    def test_names_the_run_mode_and_its_ceiling(self):
        s = SKILL_MD.read_text()
        assert "--mode run" in s
        assert "ceiling=80" in s

    def test_distinguishes_the_two_ceilings(self):
        """45 and 80 answer different questions and prescribe opposite remedies."""
        s = SKILL_MD.read_text()
        assert "Run-context ceiling" in s
        assert "--mode advisor" in s

    def test_states_the_halt_route(self):
        assert "<phase>:context_ceiling" in SKILL_MD.read_text()

    def test_requires_the_handoff_before_stopping(self):
        """The halt is worthless without it — that is the whole point of the route."""
        s = SKILL_MD.read_text()
        section = _titled_section(s, "Run-context ceiling")
        assert "handoff" in section.lower()
        assert "--release" in section

    def test_says_why_halt_and_not_warn(self):
        s = SKILL_MD.read_text()
        section = _titled_section(s, "Run-context ceiling")
        assert "unrecoverable" in section

    def test_pins_halt_is_not_deny(self):
        """Anti-conflation with the live advisor hook, stated where a reader will hit it."""
        s = SKILL_MD.read_text()
        section = _titled_section(s, "Run-context ceiling")
        assert "DENY" in section and "HALT" in section

    def test_the_halt_route_is_in_failure_recovery(self):
        fr = (REPO_ROOT / "h-mad" / "references" / "failure-recovery.md").read_text(encoding="utf-8")
        assert "context_ceiling" in fr



class TestCeilingRoutesToTheHandoffSkill:
    """The ceiling buys a resumable session, and only the skill delivers one.

    "Write the handoff" was the instruction for a long time, and it is satisfiable
    by a markdown file written anywhere under any name -- which the handoff skill's
    READ mode cannot find. READ locates a doc by the CANONICAL main-worktree store
    and an exact `<branch-slug>__` match, so a hand-written doc in a linked worktree
    is not merely untidy: it is invisible to the resume the halt was spent to buy,
    and nothing reports that at the time of writing.
    """

    def test_names_the_skill_and_its_write_mode(self):
        section = _titled_section(SKILL_MD.read_text(), "Run-context ceiling")
        assert "handoff" in section and "WRITE" in section
        assert 'Skill(skill: "handoff")' in section, (
            "the route must be invocable as written -- 'write the handoff' is "
            "advice, not a route"
        )

    def test_forbids_a_hand_written_substitute_and_says_why(self):
        section = _titled_section(SKILL_MD.read_text(), "Run-context ceiling")
        assert "branch-slug" in section or "branch slug" in section
        assert "canonical" in section.lower()
        assert "invisible to the resume" in section

    def test_names_what_write_adds_that_a_doc_omits(self):
        """Each of these is a thing the NEXT session depends on, not a nicety."""
        section = _titled_section(SKILL_MD.read_text(), "Run-context ceiling")
        for token in ("INDEX.md", "auto-memory", "handoff_commit.py"):
            assert token in section, token

    def test_budgets_the_write_itself_and_ranks_the_escape_hatches(self):
        """At 80% the write costs context too, so the order of sacrifice matters."""
        section = _titled_section(SKILL_MD.read_text(), "Run-context ceiling")
        assert "--skip-scout" in section and "--skip-memories" in section
        assert "not\ndiscretionary" in section or "not discretionary" in section
        assert section.index("--skip-scout") < section.index("--skip-memories"), (
            "the cheaper loss must be named first -- memories are what surface "
            "in the next session"
        )

    def test_the_never_list_routes_to_the_skill_too(self):
        """A reader who reaches the ban list must not be told merely to 'write' one."""
        s = SKILL_MD.read_text()
        never = s[s.index("## What you NEVER do"):]
        line = next(ln for ln in never.splitlines() if "CTXBUDGET: HALT mode=run" in ln)
        assert "handoff" in line and "skill" in line, line

    def test_points_handover_at_the_other_mode(self):
        """Work that belongs elsewhere must not be closed out as if it were ours."""
        section = _titled_section(SKILL_MD.read_text(), "Run-context ceiling")
        assert "HANDOVER" in section
