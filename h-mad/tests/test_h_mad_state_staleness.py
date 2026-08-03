"""State that is well-formed and wrong.

The two-tier validator checks record *shape*. Nothing checked whether the
contents still describe reality, and both directions were observed on one
feature in one day:

  - halt_reason recorded a design gap and persisted for over four hours after
    that gap was resolved and eight further modules shipped past it. The resume
    decision checks halt_reason first, so it would have routed to `halted` and
    presented a solved problem as the blocker.
  - Later, last_completed_phase still read 4 while Phase 5 had completed,
    merged and pushed. A resume would have routed to enter_autonomous and
    redone completed, already-merged work.

Both records validated cleanly throughout. A schema cannot see this; only a
comparison against observable evidence can.

The checker reports disagreement, it does not adjudicate. The failure being
fixed is silent confidence, not a wrong guess — so a finding names what
disagrees and leaves the operator to decide.
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "h_mad_state_staleness.py"
sys.path.insert(0, str(SCRIPTS))

import h_mad_state_staleness as st  # noqa: E402

BASE = {
    "feature": "demo",
    "started_ts": "2026-07-21T00:00:00Z",
    "last_completed_phase": 4,
    "current_phase": 5,
    "phase": None,
    "audit_cycles": {"plan": 1, "design": 1, "impl_plan": 0},
    "iterate_cycles": 0,
    "halt_reason": None,
    "halt_ts": None,
}

NO_GIT = {"branch_exists": False, "latest_commit_ts": None, "impl_commit_count": 0}


def codes(findings):
    return {f["code"] for f in findings}


class TestStaleHalt:
    def test_halt_older_than_newest_commit_is_flagged(self):
        rec = dict(BASE, halt_reason="step5d:design_gap", halt_ts="2026-07-21T04:42:36Z")
        git = {"branch_exists": True, "latest_commit_ts": "2026-07-21T18:02:31Z",
               "impl_commit_count": 8}
        assert "halt_superseded" in codes(st.check(rec, git))

    def test_finding_quantifies_the_disagreement(self):
        """'Stale' alone is not actionable; say how many commits landed after."""
        rec = dict(BASE, halt_reason="step5d:x", halt_ts="2026-07-21T04:42:36Z")
        git = {"branch_exists": True, "latest_commit_ts": "2026-07-21T18:02:31Z",
               "impl_commit_count": 8}
        f = next(f for f in st.check(rec, git) if f["code"] == "halt_superseded")
        assert "18:02" in f["detail"] or "04:42" in f["detail"]

    def test_halt_newer_than_last_commit_is_not_flagged(self):
        rec = dict(BASE, halt_reason="step5d:x", halt_ts="2026-07-21T19:00:00Z")
        git = {"branch_exists": True, "latest_commit_ts": "2026-07-21T18:02:31Z",
               "impl_commit_count": 8}
        assert "halt_superseded" not in codes(st.check(rec, git))

    def test_halt_without_a_timestamp_is_not_guessed_at(self):
        rec = dict(BASE, halt_reason="step5d:x", halt_ts=None)
        git = {"branch_exists": True, "latest_commit_ts": "2026-07-21T18:02:31Z",
               "impl_commit_count": 8}
        assert "halt_superseded" not in codes(st.check(rec, git))


class TestPhaseCounterBehind:
    def test_impl_commits_with_low_phase_counter_is_flagged(self):
        rec = dict(BASE, last_completed_phase=4)
        git = {"branch_exists": True, "latest_commit_ts": "2026-07-21T18:00:00Z",
               "impl_commit_count": 12}
        assert "phase_counter_behind" in codes(st.check(rec, git))

    def test_mid_phase5_with_a_correct_counter_is_not_flagged(self):
        # THE false positive. A record actively executing step5 has
        # last_completed_phase=4 BECAUSE Phase 5 is not finished — that is the
        # correct value, not a stale one. Implementation commits exist because
        # earlier tasks in the phase shipped; the phase itself is still running.
        # Hit live on grounding-shadow-measurement: lcp=4 with 18 feature
        # commits, Task 5 genuinely outstanding.
        rec = dict(BASE, last_completed_phase=4, phase="step5")
        git = {"branch_exists": True, "latest_commit_ts": "2026-08-03T00:00:00Z",
               "impl_commit_count": 18}
        assert "phase_counter_behind" not in codes(st.check(rec, git)), (
            "flagged a record that is correctly mid-Phase-5; the counter is not behind"
        )

    def test_no_run_in_flight_with_shipped_work_is_still_flagged(self):
        # Counter-direction 1: nothing in flight (phase cleared) but commits
        # shipped and the counter never advanced — the genuine staleness this
        # check exists for. A resume would re-enter Phase 5 and redo the work.
        rec = dict(BASE, last_completed_phase=4, phase=None)
        git = {"branch_exists": True, "latest_commit_ts": "2026-08-03T00:00:00Z",
               "impl_commit_count": 18}
        assert "phase_counter_behind" in codes(st.check(rec, git))

    def test_a_later_phase_in_flight_with_a_phase4_counter_is_still_flagged(self):
        # Counter-direction 2: executing step6 means Phase 5 COMPLETED, so a
        # counter of 4 is genuinely behind. Suppressing on "any live phase"
        # would silence this.
        rec = dict(BASE, last_completed_phase=4, phase="step6")
        git = {"branch_exists": True, "latest_commit_ts": "2026-08-03T00:00:00Z",
               "impl_commit_count": 18}
        assert "phase_counter_behind" in codes(st.check(rec, git))

    def test_a_counter_more_than_one_behind_the_live_phase_is_still_flagged(self):
        # Counter-direction 3: mid-step5 should mean lcp=4. lcp=2 is behind by
        # more than the phase in flight explains.
        rec = dict(BASE, last_completed_phase=2, phase="step5")
        git = {"branch_exists": True, "latest_commit_ts": "2026-08-03T00:00:00Z",
               "impl_commit_count": 18}
        assert "phase_counter_behind" in codes(st.check(rec, git))

    def test_no_branch_but_commits_counted_is_not_flagged(self):
        # Isolates the `branch` guard. The neighbouring NO_GIT test cannot:
        # it sets branch_exists=False AND impl_commit_count=0, so either
        # condition alone suppresses the finding and deleting the branch check
        # leaves it green. Caught by mutation.
        rec = dict(BASE, last_completed_phase=4, phase=None)
        git = {"branch_exists": False, "latest_commit_ts": "2026-08-03T00:00:00Z",
               "impl_commit_count": 18}
        assert "phase_counter_behind" not in codes(st.check(rec, git)), (
            "flagged a feature with no branch; the commit count alone says nothing "
            "about whether THIS feature shipped"
        )

    def test_no_feature_branch_means_no_claim(self):
        assert "phase_counter_behind" not in codes(st.check(dict(BASE), NO_GIT))

    def test_phase_already_past_5_is_not_flagged(self):
        rec = dict(BASE, last_completed_phase=6)
        git = {"branch_exists": True, "latest_commit_ts": "2026-07-21T18:00:00Z",
               "impl_commit_count": 12}
        assert "phase_counter_behind" not in codes(st.check(rec, git))

    def test_branch_with_no_implementation_commits_is_not_flagged(self):
        git = {"branch_exists": True, "latest_commit_ts": "2026-07-21T18:00:00Z",
               "impl_commit_count": 0}
        assert "phase_counter_behind" not in codes(st.check(dict(BASE), git))


class TestStaleAutonomousFlag:
    def test_long_running_step5_with_no_halt_is_flagged(self):
        rec = dict(BASE, phase="step5", autonomous_entry_ts="2026-07-21T03:08:23Z")
        git = {"branch_exists": True, "latest_commit_ts": "2026-07-21T04:00:00Z",
               "impl_commit_count": 1}
        assert "autonomous_flag_stale" in codes(st.check(rec, git, now="2026-07-21T22:00:00Z"))

    def test_recent_step5_is_not_flagged(self):
        rec = dict(BASE, phase="step5", autonomous_entry_ts="2026-07-21T21:30:00Z")
        git = {"branch_exists": True, "latest_commit_ts": "2026-07-21T21:40:00Z",
               "impl_commit_count": 1}
        assert "autonomous_flag_stale" not in codes(st.check(rec, git, now="2026-07-21T22:00:00Z"))

    def test_halted_step5_is_not_flagged(self):
        """A halt explains the elapsed time; the pair is only suspicious when
        nothing accounts for it."""
        rec = dict(BASE, phase="step5", autonomous_entry_ts="2026-07-21T03:00:00Z",
                   halt_reason="step5d:x", halt_ts="2026-07-21T04:00:00Z")
        git = {"branch_exists": True, "latest_commit_ts": "2026-07-21T03:30:00Z",
               "impl_commit_count": 1}
        assert "autonomous_flag_stale" not in codes(st.check(rec, git, now="2026-07-21T22:00:00Z"))


class TestCleanState:
    def test_a_consistent_record_yields_nothing(self):
        rec = dict(BASE, last_completed_phase=6, current_phase=6)
        git = {"branch_exists": True, "latest_commit_ts": "2026-07-21T18:00:00Z",
               "impl_commit_count": 12}
        assert st.check(rec, git) == []

    def test_a_fresh_feature_yields_nothing(self):
        rec = dict(BASE, last_completed_phase=0, current_phase=0)
        assert st.check(rec, NO_GIT) == []


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

    def test_clean_prints_clean_token_and_exits_0(self, tmp_path):
        p = self.store(tmp_path, dict(BASE, last_completed_phase=0, current_phase=0))
        r = self.run(p, "--feature", "demo", "--no-git")
        assert r.returncode == 0
        assert "STALENESS: CLEAN" in r.stdout

    def test_suspect_prints_findings_and_still_exits_0(self, tmp_path):
        """Verdict via token, never exit code — same discipline as the audit
        gate, so a finding never registers as a tool failure."""
        rec = dict(BASE, halt_reason="step5d:x", halt_ts="2026-07-21T04:00:00Z")
        p = self.store(tmp_path, rec)
        r = self.run(p, "--feature", "demo", "--no-git",
                     "--latest-commit-ts", "2026-07-21T18:00:00Z",
                     "--impl-commit-count", "8", "--branch-exists")
        assert r.returncode == 0
        assert "STALENESS: SUSPECT" in r.stdout
        assert "halt_superseded" in r.stdout

    def test_emits_hmad_marker(self, tmp_path):
        p = self.store(tmp_path, dict(BASE, last_completed_phase=0, current_phase=0))
        r = self.run(p, "--feature", "demo", "--no-git")
        assert "[H-MAD]" in r.stdout

    def test_unknown_feature_exits_2(self, tmp_path):
        p = self.store(tmp_path, dict(BASE))
        r = self.run(p, "--feature", "nope", "--no-git")
        assert r.returncode == 2

    def test_missing_file_exits_2(self, tmp_path):
        r = self.run(tmp_path / "nope.json", "--feature", "demo", "--no-git")
        assert r.returncode == 2
