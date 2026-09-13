import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "h-mad" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from h_mad_resume_decision import _phase_num, decide  # noqa: E402


def _write_state(tmp_path: Path, feature: str, feat_state: dict) -> Path:
    state_file = tmp_path / ".bkit-memory.json"
    state_file.write_text(
        json.dumps({"version": 1, "orchestrator_state": {feature: feat_state}}),
        encoding="utf-8",
    )
    return state_file


@pytest.mark.parametrize(
    "value,expected",
    [
        (7, 7),          # schema int form
        (4, 4),
        (0, 0),
        ("step7", 7),    # orchestrator "stepN" string form actually written to state
        ("phase7", 7),   # alternate "phaseN" form also seen in real state
        ("step4", 4),
        ("STEP5", 5),    # case-insensitive
        ("complete", 7), # sentinel
        ("5", 5),        # bare digit string
        (None, 0),       # absent/unknown degrades, never raises
        (True, 0),       # bool is an int subclass — must NOT count as 1
        ("garbage", 0),
    ],
)
def test_phase_num_coerces_every_state_form(value, expected) -> None:
    assert _phase_num(value) == expected


def test_decide_complete_from_stepN_string_does_not_crash(tmp_path: Path) -> None:
    # Regression: state stored "step7" (string) while decide() compared `>= 7`
    # (int) -> TypeError on every completed feature. Must return "complete".
    state = _write_state(tmp_path, "feat", {"last_completed_phase": "step7"})
    assert decide(state, "feat") == "complete"


def test_decide_honors_explicit_complete_flag(tmp_path: Path) -> None:
    state = _write_state(
        tmp_path, "feat", {"complete": True, "last_completed_phase": "step5"}
    )
    assert decide(state, "feat") == "complete"


def test_decide_complete_sentinel_phase(tmp_path: Path) -> None:
    state = _write_state(tmp_path, "feat", {"last_completed_phase": "complete"})
    assert decide(state, "feat") == "complete"


def test_decide_current_phase_complete_with_phase7_last(tmp_path: Path) -> None:
    # Real synopsis-manifest-source-ingestion shape: current_phase sentinel
    # plus the "phaseN" (not "stepN") last_completed_phase variant.
    state = _write_state(
        tmp_path,
        "feat",
        {"current_phase": "complete", "last_completed_phase": "phase7"},
    )
    assert decide(state, "feat") == "complete"


def test_decide_routing_thresholds(tmp_path: Path) -> None:
    assert decide(_write_state(tmp_path, "f", {"last_completed_phase": "step4"}), "f") == "enter_autonomous"
    assert decide(_write_state(tmp_path, "f", {"last_completed_phase": "step2"}), "f") == "resume_manual"
    assert decide(_write_state(tmp_path, "f", {"halt_reason": "step5d:no_codex_pane"}), "f") == "halted"


class TestAnUnreadableStateFileIsNotAnEmptyOne:
    """WSG-6. Three different states used to return `start_fresh`, and only two of
    them mean it.

    "No file" and "the file parsed and holds no record for this feature" both
    legitimately mean nothing is claimed. "The file is there and I could not read
    it" does not: the store may hold dozens of records and a live owner for this
    very feature, and `start_fresh` tells the caller to initialise over it. The
    incident that filed this was a state file that vanished with the cause
    undetermined; an unreadable file is the half a tool can defend against.
    """

    def test_invalid_json_is_cannot_judge_not_start_fresh(self, tmp_path: Path) -> None:
        state = tmp_path / ".bkit-memory.json"
        state.write_text('{"orchestrator_state": {"feat": ', encoding="utf-8")
        assert decide(state, "feat") == "cannot_judge"

    def test_a_truncated_write_over_a_POPULATED_store_is_cannot_judge(self, tmp_path: Path) -> None:
        """The realistic shape: the file held records a moment ago and the write was
        cut. Answering `start_fresh` here is what routes a second session onto a
        feature the first is working."""
        good = _write_state(tmp_path, "feat", {"last_completed_phase": 5,
                                               "owner_session_id": "someone-else"})
        whole = good.read_text(encoding="utf-8")
        good.write_text(whole[: len(whole) // 2], encoding="utf-8")
        assert decide(good, "feat") == "cannot_judge"

    def test_an_unreadable_file_is_cannot_judge(self, tmp_path: Path) -> None:
        import os
        state = _write_state(tmp_path, "feat", {"last_completed_phase": 5})
        state.chmod(0o000)
        try:
            if os.access(state, os.R_OK):        # root ignores the mode
                pytest.skip("running as root — the permission path is unreachable")
            assert decide(state, "feat") == "cannot_judge"
        finally:
            state.chmod(0o600)

    def test_an_ABSENT_file_still_starts_fresh_deliberately(self, tmp_path: Path) -> None:
        """Not an oversight. A feature that was never started is the common case, and
        the callers that know better check for the file before asking. Telling "never
        existed" from "vanished" needs evidence this script does not have — so that
        half of WSG-6 stays open rather than being papered over with a false alarm."""
        assert decide(tmp_path / "nonexistent.json", "feat") == "start_fresh"

    def test_the_token_is_documented_where_callers_read_it(self) -> None:
        """A token nobody documented is one every caller's enumeration misclassifies.
        `handoff/SKILL.md` used to end its list with "any other token -> safe to
        proceed", which is fail-OPEN: a token added FOR safety would have been read as
        permission to proceed."""
        skill = (REPO_ROOT / "h-mad" / "SKILL.md").read_text(encoding="utf-8")
        assert "`cannot_judge`" in skill, (
            "the decision-token table must name cannot_judge, or an operator hitting "
            "it has no prescribed action")

        handoff = Path.home() / ".claude" / "skills" / "handoff" / "SKILL.md"
        if not handoff.is_file():
            pytest.skip("handoff skill not installed alongside h-mad")
        text = handoff.read_text(encoding="utf-8")
        assert "`cannot_judge`" in text, (
            "the handoff skill's oracle enumeration does not mention cannot_judge, so "
            "it falls into whatever that list's default is")

        # The POSITIVE invariant, because the negative one is what a bare substring
        # check gets wrong. A first version of this test asserted `"any other token"
        # not in text` and failed on the sentence in THIS repo documenting the
        # retired defect — a proxy that cannot tell a live instruction from prose
        # quoting the instruction it replaced. What actually matters is that the list
        # is CLOSED.
        assert "**anything else** → STOP" in text, (
            "the liveness-oracle enumeration must end with a closed default. Without "
            "one it fails OPEN: every token added to the oracle later is "
            "auto-classified as whatever the trailing bullet says, and cannot_judge "
            "was added FOR safety.")

        # And the specific fail-open construction must not be live: the phrase and the
        # permission on the SAME line is the shape that granted it.
        live = [ln for ln in text.splitlines()
                if "any other token" in ln and "safe to proceed" in ln]
        assert not live, ("fail-open default is live again:\n" + "\n".join(live))


def test_decide_missing_feature_or_state_starts_fresh(tmp_path: Path) -> None:
    state = _write_state(tmp_path, "other", {"last_completed_phase": "step7"})
    assert decide(state, "absent") == "start_fresh"
    assert decide(tmp_path / "nonexistent.json", "feat") == "start_fresh"
