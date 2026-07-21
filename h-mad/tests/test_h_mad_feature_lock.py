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
        r = subprocess.run([sys.executable, str(w), str(p), "--feature", "demo",
                            "--release"], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        assert read(p)["demo"]["owner_session_id"] is None
