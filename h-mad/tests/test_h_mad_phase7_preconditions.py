"""Phase 7 merges. Nothing stopped it merging before Phase 6 ran.

SKILL.md documents 6 (verification) before 7 (closure), and 7 is what merges and
pushes. The ordering lived only as prose in a document the orchestrator trusts
itself to follow.

Observed: a feature completed Phase 5, merged to main and pushed — no gap
analysis, no architectural review, no telemetry, no archive. The suite was green,
which was the only signal anyone had, and green tests turned out to say nothing
about spec conformance: the later gap analysis measured 0%.

This gate makes the sequence checkable instead of merely documented. It reads
state and the analysis artifact; it does not merge anything itself.
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "h_mad_phase7_preconditions.py"
sys.path.insert(0, str(SCRIPTS))

import h_mad_phase7_preconditions as p7  # noqa: E402

READY = {
    "feature": "demo",
    "started_ts": "2026-07-22T00:00:00Z",
    "last_completed_phase": 6,
    "current_phase": 7,
    "phase": None,
    "audit_cycles": {"plan": 1, "design": 1, "impl_plan": 1},
    "iterate_cycles": 0,
    "halt_reason": None,
    "halt_ts": None,
}

ANALYSIS = "# Analysis: demo\n\n## Match Rate: 96%\n\n## Verdict\nAdvance.\n"


def codes(result):
    return {b["code"] for b in result["blockers"]}


class TestMatchRateParsing:
    def test_reads_a_percentage(self):
        assert p7.parse_match_rate("## Match Rate: 96%") == 96.0

    def test_reads_a_decimal(self):
        assert p7.parse_match_rate("## Match Rate: 89.5%") == 89.5

    def test_reads_a_bolded_zero(self):
        """The real analysis wrote **0%** — a falsy value that must not be
        mistaken for 'absent'."""
        assert p7.parse_match_rate("## Match Rate: **0%**") == 0.0

    def test_absent_rate_is_none_not_zero(self):
        assert p7.parse_match_rate("# Analysis\nno rate here") is None

    def test_takes_the_first_rate(self):
        assert p7.parse_match_rate("## Match Rate: 96%\nlater: 12%") == 96.0


class TestBlockers:
    def test_ready_state_passes(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text(ANALYSIS)
        assert p7.check(READY, a)["ready"] is True

    def test_phase_below_6_blocks(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text(ANALYSIS)
        rec = dict(READY, last_completed_phase=5)
        assert "verification_not_run" in codes(p7.check(rec, a))

    def test_missing_analysis_blocks(self, tmp_path):
        assert "analysis_missing" in codes(p7.check(READY, tmp_path / "nope.md"))

    def test_low_match_rate_blocks(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text("## Match Rate: 42%")
        assert "match_rate_below_threshold" in codes(p7.check(READY, a))

    def test_zero_match_rate_blocks(self, tmp_path):
        """The exact observed case. A falsy rate must block, not skip the check."""
        a = tmp_path / "demo.analysis.md"
        a.write_text("## Match Rate: **0%**")
        assert "match_rate_below_threshold" in codes(p7.check(READY, a))

    def test_unparseable_rate_blocks(self, tmp_path):
        """An analysis with no measurement is not evidence of a passing one."""
        a = tmp_path / "demo.analysis.md"
        a.write_text("# Analysis: demo\nlooks fine to me")
        assert "match_rate_unreadable" in codes(p7.check(READY, a))

    def test_open_halt_blocks(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text(ANALYSIS)
        rec = dict(READY, halt_reason="step6a:x")
        assert "halted" in codes(p7.check(rec, a))

    def test_blockers_accumulate(self, tmp_path):
        rec = dict(READY, last_completed_phase=4, halt_reason="step5:x")
        result = p7.check(rec, tmp_path / "nope.md")
        assert len(result["blockers"]) >= 3
        assert result["ready"] is False


class TestSkippedArchreviewIsReportedNotBlocking:
    """#10 allows a deliberate skip; it must reach the report, not the gate."""

    def test_skipped_archreview_does_not_block(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text(ANALYSIS)
        rec = dict(READY, archreview="SKIPPED_NO_PANE")
        assert p7.check(rec, a)["ready"] is True

    def test_skipped_archreview_is_surfaced_as_a_warning(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text(ANALYSIS)
        rec = dict(READY, archreview="SKIPPED_NO_PANE")
        assert any("archreview" in w["code"] for w in p7.check(rec, a)["warnings"])

    def test_failed_archreview_does_block(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text(ANALYSIS)
        rec = dict(READY, archreview="NO")
        assert "archreview_failed" in codes(p7.check(rec, a))


class TestCli:
    def store(self, tmp_path, rec):
        p = tmp_path / "state.json"
        p.write_text(json.dumps({"version": 1, "orchestrator_state": {"demo": rec}}))
        return p

    def run(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *[str(a) for a in args]],
            capture_output=True, text=True,
        )

    def test_ready_prints_token_and_exits_0(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text(ANALYSIS)
        p = self.store(tmp_path, READY)
        r = self.run(p, "--feature", "demo", "--analysis", a)
        assert r.returncode == 0
        assert "PHASE7: READY" in r.stdout

    def test_blocked_prints_reasons_and_still_exits_0(self, tmp_path):
        p = self.store(tmp_path, dict(READY, last_completed_phase=5))
        r = self.run(p, "--feature", "demo", "--analysis", tmp_path / "nope.md")
        assert r.returncode == 0, "verdict travels in the token, not the exit code"
        assert "PHASE7: BLOCKED" in r.stdout
        assert "verification_not_run" in r.stdout

    def test_emits_hmad_marker(self, tmp_path):
        p = self.store(tmp_path, dict(READY, last_completed_phase=5))
        r = self.run(p, "--feature", "demo", "--analysis", tmp_path / "nope.md")
        assert "[H-MAD]" in r.stdout

    def test_missing_feature_exits_2(self, tmp_path):
        p = self.store(tmp_path, READY)
        r = self.run(p, "--feature", "nope", "--analysis", tmp_path / "a.md")
        assert r.returncode == 2
