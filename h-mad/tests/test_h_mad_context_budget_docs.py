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
    # asserting against the rest of the document.
    assert len(section.splitlines()) < 140, "section boundary ran away"
    return " ".join(section.split())


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
        assert "h-mad-advisor-gate.sh" in s
        assert '"matcher": "advisor"' in s

    def test_says_wiring_takes_effect_next_session(self):
        """Hooks are snapshotted at session start. Without this, the session that
        wires it looks broken and the hook gets removed as non-functional."""
        s = _section()
        assert "NEXT session" in s

    def test_gives_a_live_fire_test_and_names_silent_stand_down_as_the_finding(self):
        s = _section()
        assert "HMAD_CONTEXT_WINDOW=1000" in s
        assert "stands down silently" in s

    def test_states_the_fail_open_direction_and_why(self):
        """A gate that blocked on a cannot-judge would deny the early cheap call
        the ladder recommends -- worse than no gate."""
        s = _section()
        assert "fails open" in s
        assert "set -euo" in s

    def test_names_the_override_and_why_it_exists(self):
        s = _section()
        assert "HMAD_ADVISOR_OVERRIDE=1" in s
        assert "deleted from" in s

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
    assert "h-mad-advisor-gate.sh" in never


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
        i = s.index("Run-context ceiling")
        section = s[i:i + 4000]
        assert "handoff" in section.lower()
        assert "--release" in section

    def test_says_why_halt_and_not_warn(self):
        s = SKILL_MD.read_text()
        i = s.index("Run-context ceiling")
        section = s[i:i + 4000]
        assert "unrecoverable" in section

    def test_pins_halt_is_not_deny(self):
        """Anti-conflation with the live advisor hook, stated where a reader will hit it."""
        s = SKILL_MD.read_text()
        i = s.index("Run-context ceiling")
        section = s[i:i + 4000]
        assert "DENY" in section and "HALT" in section

    def test_the_halt_route_is_in_failure_recovery(self):
        fr = (REPO_ROOT / "h-mad" / "references" / "failure-recovery.md").read_text(encoding="utf-8")
        assert "context_ceiling" in fr

