"""Per-feature ownership so two sessions cannot work one feature blind.

The documented concurrency rule was cross-feature ("only one feature may have
phase != null") and keyed on `phase`, which is set to null on halt and at 5g —
so the guard was off exactly when a second session was most likely to pick the
feature up.

Observed: two sessions worked one feature minutes apart. One committed a
Phase-7 closure report recording "match rate: not measured"; the other had
committed a gap analysis four minutes earlier reporting a low match rate and an
explicit do-not-advance verdict. Both landed on the same branch, neither saw the
other, and the branch carried two contradictory conclusions.

Ownership is advisory, not a mutex: it reports who holds a feature and how long
ago they were seen, so a second session makes a deliberate choice instead of an
accidental one. A stale claim must never become a permanent lockout.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import h_mad_state_write as sw  # noqa: E402
import h_mad_resume_decision as rd  # noqa: E402

VALID = {
    "feature": "demo",
    "started_ts": "2026-07-22T00:00:00Z",
    "last_completed_phase": 4,
    "current_phase": 5,
    "phase": None,
    "audit_cycles": {"plan": 1, "design": 1, "impl_plan": 0},
    "iterate_cycles": 0,
    "halt_reason": None,
    "halt_ts": None,
}


def store(tmp_path, records=None) -> Path:
    p = tmp_path / "state.json"
    p.write_text(json.dumps({"version": 1, "orchestrator_state": records or {}}))
    return p


def read(p: Path) -> dict:
    return json.loads(p.read_text())["orchestrator_state"]


class TestSchemaSupportsOwnership:
    def test_owner_fields_are_declared(self):
        schema = json.loads((SCRIPTS / "h_mad_state_schema.json").read_text())
        assert "owner_session_id" in schema["properties"]
        assert "owner_heartbeat_ts" in schema["properties"]

    def test_a_claimed_record_validates_strict(self, tmp_path):
        import h_mad_state_validate as sv

        rec = dict(VALID, owner_session_id="sess-a", owner_heartbeat_ts="2026-07-22T01:00:00Z")
        assert sv.classify(rec) == "strict"


class TestClaimAndRelease:
    def test_claim_records_owner_and_heartbeat(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        sw.claim(p, "demo", "sess-a", now="2026-07-22T01:00:00Z")
        rec = read(p)["demo"]
        assert rec["owner_session_id"] == "sess-a"
        assert rec["owner_heartbeat_ts"] == "2026-07-22T01:00:00Z"

    def test_release_clears_both_fields(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        sw.claim(p, "demo", "sess-a", now="2026-07-22T01:00:00Z")
        sw.release(p, "demo")
        rec = read(p)["demo"]
        assert rec["owner_session_id"] is None
        assert rec["owner_heartbeat_ts"] is None

    def test_reclaim_by_the_same_session_refreshes_the_heartbeat(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        sw.claim(p, "demo", "sess-a", now="2026-07-22T01:00:00Z")
        sw.claim(p, "demo", "sess-a", now="2026-07-22T02:00:00Z")
        assert read(p)["demo"]["owner_heartbeat_ts"] == "2026-07-22T02:00:00Z"

    def test_claim_by_a_second_session_is_refused(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        sw.claim(p, "demo", "sess-a", now="2026-07-22T01:00:00Z")
        with pytest.raises(sw.StateWriteError, match="owned"):
            sw.claim(p, "demo", "sess-b", now="2026-07-22T01:01:00Z")

    def test_force_claim_takes_over(self, tmp_path):
        """A deliberate override must exist — otherwise a crashed session locks
        the feature forever."""
        p = store(tmp_path, {"demo": dict(VALID)})
        sw.claim(p, "demo", "sess-a", now="2026-07-22T01:00:00Z")
        sw.claim(p, "demo", "sess-b", now="2026-07-22T01:01:00Z", force=True)
        assert read(p)["demo"]["owner_session_id"] == "sess-b"


class TestResumeDecisionSurfacesOwnership:
    def test_owned_by_another_session_returns_owned_elsewhere(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID, owner_session_id="sess-a",
                                          owner_heartbeat_ts="2026-07-22T01:00:00Z")})
        token = rd.decide(p, "demo", session_id="sess-b", now="2026-07-22T01:05:00Z")
        assert token == "owned_elsewhere"

    def test_own_claim_does_not_block_us(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID, owner_session_id="sess-a",
                                          owner_heartbeat_ts="2026-07-22T01:00:00Z")})
        token = rd.decide(p, "demo", session_id="sess-a", now="2026-07-22T01:05:00Z")
        assert token == "enter_autonomous"

    def test_stale_claim_does_not_lock_out(self, tmp_path):
        """A heartbeat older than the staleness window is treated as abandoned;
        otherwise a crashed session owns the feature permanently."""
        p = store(tmp_path, {"demo": dict(VALID, owner_session_id="sess-a",
                                          owner_heartbeat_ts="2026-07-22T01:00:00Z")})
        token = rd.decide(p, "demo", session_id="sess-b", now="2026-07-22T09:00:00Z")
        assert token != "owned_elsewhere"

    def test_unclaimed_feature_is_unaffected(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        assert rd.decide(p, "demo", session_id="sess-b") == "enter_autonomous"

    def test_no_session_id_preserves_legacy_behaviour(self, tmp_path):
        """Callers that do not pass a session id must not start seeing a new
        token they cannot interpret."""
        p = store(tmp_path, {"demo": dict(VALID, owner_session_id="sess-a",
                                          owner_heartbeat_ts="2026-07-22T01:00:00Z")})
        assert rd.decide(p, "demo") == "enter_autonomous"

    def test_ownership_outranks_halt(self, tmp_path):
        """A halted feature held by a live session is still held. Routing the
        second session to `halted` would send it to fix something the first is
        already working on — the exact collision this exists to prevent."""
        p = store(tmp_path, {"demo": dict(VALID, halt_reason="step5d:boom",
                                          owner_session_id="sess-a",
                                          owner_heartbeat_ts="2026-07-22T01:00:00Z")})
        assert rd.decide(p, "demo", session_id="sess-b",
                         now="2026-07-22T01:05:00Z") == "owned_elsewhere"


class TestCliSurface:
    def run(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "h_mad_resume_decision.py"), *[str(a) for a in args]],
            capture_output=True, text=True,
        )

    def test_resume_cli_accepts_session_id(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID, owner_session_id="sess-a",
                                          owner_heartbeat_ts="2026-07-22T01:00:00Z")})
        r = self.run("--state", p, "--feature", "demo", "--session-id", "sess-b",
                     "--now", "2026-07-22T01:05:00Z")
        assert r.returncode == 0
        assert r.stdout.strip() == "owned_elsewhere"

    def test_writer_cli_can_claim_and_release(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        w = SCRIPTS / "h_mad_state_write.py"
        r = subprocess.run([sys.executable, str(w), str(p), "--feature", "demo",
                            "--claim", "sess-a"], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        assert read(p)["demo"]["owner_session_id"] == "sess-a"
        # --session-id because the claim above is live and this session owns it.
        # Releasing a live claim anonymously is refused (J45); see
        # TestReleaseOwnershipGuard for that half.
        r = subprocess.run([sys.executable, str(w), str(p), "--feature", "demo",
                            "--release", "--session-id", "sess-a"],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        assert read(p)["demo"]["owner_session_id"] is None


class TestReleaseOwnershipGuard:
    """J45 — `--release` guarded nothing, so `--release` + `--claim` took a LIVE
    owner's feature with no `--force` anywhere.

    `claim()` refuses a live owner and its docstring is explicit that `force` is
    "the verb for taking a feature from a session that is still RUNNING", warning
    that routing routine cases through it "teaches an operator to pass it by
    reflex, which is how the guard stops protecting the case it exists for".
    `release()` sat one function below with no window at all — so the two-step
    bypassed the guard entirely, exit 0 throughout, no warning to anyone.

    The asymmetry that makes this fixable without a force reflex: a session
    releasing its OWN claim is the routine path and stays free, and a stale claim
    stays freely releasable because that is ordinary cleanup. Only releasing a
    claim that is live AND someone else's is a takeover, and only that needs the
    deliberate flag. Both halves now read one window (`h_mad_state_ownership`),
    which is the property `claim()` already had to be fixed once to get.
    """

    def _live(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        sw.claim(p, "demo", "sess-owner")           # heartbeat = now, unambiguously live
        return p

    def test_self_release_of_a_live_claim_still_works(self, tmp_path):
        """The routine end-of-work path. If this needed --force the guard would be
        teaching the exact reflex it exists to prevent."""
        p = self._live(tmp_path)
        sw.release(p, "demo", session_id="sess-owner")
        assert read(p)["demo"]["owner_session_id"] is None

    def test_releasing_a_stale_claim_needs_no_force(self, tmp_path):
        """Ordinary cleanup — the case that must not be routed through --force."""
        p = store(tmp_path, {"demo": dict(VALID)})
        sw.claim(p, "demo", "sess-owner", now="2026-07-01T00:00:00Z")
        sw.release(p, "demo")
        assert read(p)["demo"]["owner_session_id"] is None

    def test_releasing_an_unowned_feature_is_still_safe(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        sw.release(p, "demo")
        assert read(p)["demo"]["owner_session_id"] is None

    def test_releasing_another_sessions_live_claim_is_refused(self, tmp_path):
        p = self._live(tmp_path)
        with pytest.raises(sw.StateWriteError, match="sess-owner"):
            sw.release(p, "demo", session_id="sess-other")
        assert read(p)["demo"]["owner_session_id"] == "sess-owner", "must not have released"

    def test_releasing_a_live_claim_without_saying_who_you_are_is_refused(self, tmp_path):
        """Fails closed. An unidentified caller is the ad-hoc terminal case, which
        is precisely where the accidental release happens."""
        p = self._live(tmp_path)
        with pytest.raises(sw.StateWriteError):
            sw.release(p, "demo")
        assert read(p)["demo"]["owner_session_id"] == "sess-owner"

    def test_force_takes_a_live_foreign_claim(self, tmp_path):
        """The deliberate route stays open — this is a takeover, and now it is
        spelled like one."""
        p = self._live(tmp_path)
        sw.release(p, "demo", session_id="sess-other", force=True)
        assert read(p)["demo"]["owner_session_id"] is None

    def test_the_refusal_routes_to_session_id_not_to_force(self, tmp_path):
        """The message is the guard's whole value: pointing an operator at --force
        for a case --session-id solves is how the reflex gets taught."""
        p = self._live(tmp_path)
        with pytest.raises(sw.StateWriteError) as excinfo:
            sw.release(p, "demo")
        assert "--session-id" in str(excinfo.value)

    def test_release_and_claim_no_longer_bypasses_force(self, tmp_path):
        """The bypass itself, end to end — the thing J45 measured.

        Before the fix: claim was refused, release succeeded, claim then succeeded,
        and the live owner's in-flight feature had changed hands with no --force.
        """
        p = self._live(tmp_path)
        with pytest.raises(sw.StateWriteError):
            sw.claim(p, "demo", "sess-attacker")        # step 1 was always refused
        with pytest.raises(sw.StateWriteError):
            sw.release(p, "demo")                        # step 2 is the hole, now shut
        assert read(p)["demo"]["owner_session_id"] == "sess-owner"

    def test_cli_release_accepts_session_id_and_force(self, tmp_path):
        p = self._live(tmp_path)
        w = SCRIPTS / "h_mad_state_write.py"
        bad = subprocess.run([sys.executable, str(w), str(p), "--feature", "demo",
                              "--release"], capture_output=True, text=True)
        assert bad.returncode == 2, bad.stdout
        ok = subprocess.run([sys.executable, str(w), str(p), "--feature", "demo",
                             "--release", "--session-id", "sess-owner"],
                            capture_output=True, text=True)
        assert ok.returncode == 0, ok.stderr
        assert read(p)["demo"]["owner_session_id"] is None
