"""TAKEOVER is reachable MID-SESSION, without the fresh-context halt.

The procedure for adopting a handed-over brief — claim it, verify its premises,
restore its todos with their origin, stamp `**Taken-Over-By:**`, acknowledge on the
worktree — lived only inside READ Step 3.5. And READ Step 0a HALTS when the session
is not fresh. So the one operation you need precisely *because* you are already deep
in a session was reachable only from a mode that refuses to run there. Worse, the
`pending-handovers` scan that DISCOVERS an inbound brief is READ Step 1, so mid-session
you could not even find out one had arrived.

Observed 2026-09-07: an inbound brief landed in this repo mid-session and every step of
Step 3.5 had to be hand-executed, because `/handoff read` would have printed the
`/clear` halt instead.

**Why TAKEOVER may skip the halt when READ may not.** The halt exists because a RESUME
*replaces* context: the prior session's working assumptions would silently outrank the
document just read. A takeover *adds* one owned item and replaces nothing, so that
conflict cannot arise. The rationale must be stated in the skill, not merely acted on —
an unexplained exception to a safety gate is the thing a later reader deletes or copies.

**The procedure is SINGLE-SOURCED.** Copying Step 3.5's body into a second mode would
create precisely the shared-sentence divergence that `h_mad_adoption_check.py` exists to
catch: two internally-consistent copies, drifting apart, with no reviewer able to see it
from either one alone. So the body moves to the TAKEOVER section and READ points at it.
The tests below pin that the load-bearing commands appear exactly ONCE.
"""

from __future__ import annotations

import re
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"


def _norm(text: str) -> str:
    """Collapse whitespace so a markdown reflow cannot break a literal."""
    return " ".join(text.split())


BODY = SKILL.read_text(encoding="utf-8")
FLAT = _norm(BODY)


class TestTheModeExists:
    def test_the_routing_table_names_TAKEOVER(self) -> None:
        assert "**TAKEOVER**" in FLAT, "no TAKEOVER row in the mode routing table"

    def test_the_slash_invocation_is_named(self) -> None:
        assert "/handoff takeover" in FLAT

    def test_the_mode_has_its_own_section(self) -> None:
        assert re.search(r"(?m)^## TAKEOVER mode", BODY), "no top-level TAKEOVER section"

    def test_mid_session_is_the_stated_trigger(self) -> None:
        """The whole point: it is for when you are already working."""
        assert "mid-session" in FLAT.lower()


class TestTheHaltExceptionIsStatedNotJustTaken:
    def test_takeover_says_it_does_not_halt(self) -> None:
        assert "does NOT halt" in FLAT or "no fresh-context halt" in FLAT.lower()

    def test_the_REASON_is_given(self) -> None:
        """An unexplained exception to a safety gate gets deleted or copied.

        READ replaces context; TAKEOVER adds one item and replaces nothing.
        """
        section = _norm(BODY.split("## TAKEOVER mode", 1)[1])
        # The specific contrast, not the words on their own: "replaces"/"adds" occur all
        # over this file, so asserting them passed against a mutant that deleted the
        # whole justification. The battery reported that row SURVIVED.
        assert "a resume *replaces* context" in section or "resume *replaces* context" in section
        assert "adds* one owned item" in section or "adds one owned item" in section
        assert "Step 0a" in section

    def test_READ_still_halts(self) -> None:
        """The exception must not weaken the gate it is an exception to."""
        assert "HALT if the session is not clean" in FLAT


class TestItDiscoversAndDoesNotOverreach:
    def test_takeover_runs_the_pending_handovers_scan(self) -> None:
        """Discovery is half the gap: the scan was READ Step 1 only."""
        section = _norm(BODY.split("## TAKEOVER mode", 1)[1])
        assert "pending-handovers" in section, (
            "the scan must be reachable from TAKEOVER, not only from READ Step 1")
        # The heading itself: a whole-file count of the script name survived a mutant
        # that retitled T1 to "Assume the user handed you the path", because READ
        # Step 1 still mentions the scan and kept the count up.
        assert "Step T1: Find what is addressed to this repo" in section

    def test_takeover_names_what_it_does_NOT_do(self) -> None:
        """A mode that quietly grew into a resume would re-introduce the halt's reason."""
        flat = _norm(BODY.split("## TAKEOVER mode", 1)[1])
        # Each disclaimer as its own SENTENCE. "reconcile"/"sync"/"does not" appear
        # elsewhere in the section's prose, so the loose form passed against a mutant
        # that replaced the remote-sync line with "It may sync and reconcile".
        assert "does **not** sync with the remote" in flat
        assert "does **not** reconcile the working tree" in flat
        assert "It may sync" not in flat, "the never-list was softened into permission"


class TestTheProcedureIsSingleSourced:
    def test_read_step_3_5_delegates_rather_than_duplicating(self) -> None:
        assert re.search(r"(?m)^### Step 3\.5", BODY)
        step = BODY.split("### Step 3.5", 1)[1].split("### Step 3.6", 1)[0]
        assert "TAKEOVER" in step, "READ Step 3.5 must point at the TAKEOVER section"

    def test_READ_step_3_5_carries_no_claim_procedure_of_its_own(self) -> None:
        """The property that matters: ONE adoption procedure, not two drifting copies.

        Not "the oracle is named once" — that was the first version of this test and it
        was simply false. `h_mad_resume_decision.py` legitimately appears at three sites
        doing three different things: READ Step 3.6 REFERENCES it in its auto-resolve
        gate table, HANDOVER Step 2 RELEASES with it, TAKEOVER T2 CLAIMS with it.
        Different operations, different flags. Counting the name conflates them.
        """
        step = BODY.split("### Step 3.5", 1)[1].split("### Step 3.6", 1)[0]
        assert "--claim" not in step, "READ Step 3.5 re-grew its own claim procedure"
        assert "h_mad_state_write.py" not in step

    def test_the_takeover_body_is_marked_as_the_single_source(self) -> None:
        section = BODY.split("## TAKEOVER mode", 1)[1]
        assert "SINGLE-SOURCE" in section
        assert "--claim" in section, "the claim procedure must live HERE"

    def test_the_taken_over_by_stamp_format_appears_once(self) -> None:
        assert FLAT.count("**Taken-Over-By:** <this-repo>") <= 1

    def test_owned_elsewhere_is_still_a_stop(self) -> None:
        """The one branch that must never be softened by a more convenient entry point."""
        assert "owned_elsewhere" in FLAT


class TestTheModeCanActuallyTrigger:
    """A mode absent from the frontmatter `description` is a section nobody reaches.

    The description IS the routing surface — it is what the harness matches an
    invocation against. A TAKEOVER section with no description entry would be
    documentation of a mode that never runs.
    """

    FRONTMATTER = BODY.split("---", 2)[1]

    def test_the_description_says_five_modes(self) -> None:
        assert "five modes" in self.FRONTMATTER
        assert "four modes" not in self.FRONTMATTER

    def test_the_description_names_TAKEOVER_and_its_trigger(self) -> None:
        flat = _norm(self.FRONTMATTER)
        assert "TAKEOVER mode" in flat
        assert "/handoff takeover" in flat

    def test_the_description_states_the_halt_exception(self) -> None:
        """So an invocation is routed here rather than to READ's halt."""
        flat = _norm(self.FRONTMATTER)
        assert "does NOT halt" in flat


class TestAnUnnamedFeatureIsStillClaimed:
    """A brief that names NO feature must not leave the work owned by nobody.

    Hit live on TAKEOVER's first run, 2026-09-07. The
    `audit-loop-cycle-count-evidence` brief carried `**Handover-From:**` and named
    no feature; the state file held 34 records; point 1 handles "no STATE FILE" and
    said nothing about "state file present, feature unnamed". So the takeover
    concluded "nothing to claim" and five adopted items sat unowned — precisely the
    failure this mode exists to prevent, reached THROUGH this mode.

    READ Step 3.6 already carries the repair (`feature record absent, brief carries
    Handover-From` → `--create --claim`), and TAKEOVER deliberately excludes Step
    3.6, so it could not reach it. The repair moves here rather than TAKEOVER
    growing a resume's allowlist.

    The name is DERIVED, never invented: the brief's slug, which is traceable back
    to the document that asked for the work.
    """

    SECTION = BODY.split("## TAKEOVER mode", 1)[1]
    FLAT = _norm(SECTION)

    def test_the_unnamed_feature_case_PRESCRIBES_a_claim(self) -> None:
        """Assert the PRESCRIPTION, not the topic.

        The first version asserted "names no feature", which the mutant's own
        replacement text ("If the brief names no feature, there is nothing to
        claim.") also contains — so the row SURVIVED. Naming the subject is not
        the same as requiring the remedy.
        """
        assert "CREATE the record and claim it" in self.FLAT

    def test_it_prescribes_create_and_claim(self) -> None:
        assert "--create" in self.FLAT and "--claim" in self.FLAT

    def test_the_feature_name_comes_from_the_briefs_slug(self) -> None:
        """Derived and traceable — an invented name is unfindable by the sender.

        Not a bare `"slug" in FLAT`: T3's report template already contains `<slug>`,
        so deleting the derivation rule left the word behind and the row SURVIVED.
        """
        assert "derived and traceable back to the document" in self.FLAT

    def test_owned_elsewhere_still_stops_the_create_path(self) -> None:
        """The new path must not become a way around the live-owner check."""
        assert self.FLAT.count("owned_elsewhere") >= 1
        assert "never a way around" in self.FLAT or "still stops" in self.FLAT

    def test_the_live_incident_is_recorded(self) -> None:
        """A rule without its measurement gets optimised away by the next reader."""
        assert "2026-09-07" in self.FLAT


class TestNoDollarArgInTheSkillBody:
    """`$0` in a documented command is REWRITTEN by slash-command arg substitution.

    Measured twice this session on the same line: it arrived as `…": "read}` when
    invoked as `/handoff read` and as `…": "takeover}` when invoked as
    `/handoff takeover`, while the file on disk holds `$0`. So the INDEX-cleanup
    snippet, as the agent actually receives it, prints the literal argument instead
    of the matching line — a command that silently does the wrong thing.
    """

    def test_no_positional_shell_arg_survives_in_the_body(self) -> None:
        import re as _re
        hits = _re.findall(r"\$[0-9]", BODY)
        assert not hits, f"positional args are rewritten by the renderer: {hits}"
