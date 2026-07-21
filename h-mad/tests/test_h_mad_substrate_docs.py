"""The measured silent-output cliff must stay in the substrate reference.

An agent above a size threshold reads the staged file, reports a token count,
emits nothing, and returns to its prompt. No error. The pane goes idle, so every
readiness signal reports success and a two-read stability probe reports STABLE —
the pane genuinely is settled, it just has nothing in it.

Two guards already cover the consequences (`send` switches to file-indirection
well below the cliff; verdict/report extraction fails closed on empty output).
What kept getting rediscovered was the number itself, so it is pinned here.
"""

from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SUBSTRATE = SKILL_DIR / "references" / "agent-substrate.md"


def doc() -> str:
    return SUBSTRATE.read_text(encoding="utf-8")


class TestMeasurementsRecorded:
    def test_cliff_section_exists(self):
        low = doc().lower()
        assert "silent" in low
        assert "cliff" in low or "prompt size" in low

    def test_all_three_datapoints_present(self):
        """A range needs both sides: the largest that worked and the smallest
        that did not. One number alone reads as a hard limit it is not."""
        d = doc()
        for size in ("38,921", "49,273", "53,066"):
            assert size in d, f"missing measured datapoint: {size}"

    def test_records_that_clear_did_not_recover(self):
        """Operators will try /clear first; say that it does not work."""
        low = doc().lower()
        assert "/clear" in low and "recover" in low

    def test_marks_the_measurement_as_agent_specific(self):
        """One agent, one session. Not a universal constant."""
        low = doc().lower()
        assert "measured" in low


class TestIdleDetectionCaveat:
    def test_states_stability_cannot_detect_silence(self):
        """The load-bearing caveat: idle-detection and empty-output are
        orthogonal, so `wait` succeeding proves nothing about content."""
        low = doc().lower()
        assert "stable" in low
        assert "nothing" in low or "empty" in low

    def test_points_at_the_guard_that_does_catch_it(self):
        d = doc()
        assert "h_mad_extract_verdict.py" in d or "h_mad_extract_report.py" in d


class TestSentinelEchoTrap:
    def test_warns_against_literal_sentinels_in_prompts(self):
        """A sentinel written literally into the dispatch prompt is echoed by
        the prompt itself, so the orchestrator's own grep matches its own
        instruction rather than the agent's report."""
        low = doc().lower()
        assert "echo" in low
        assert "fragment" in low or "split" in low
