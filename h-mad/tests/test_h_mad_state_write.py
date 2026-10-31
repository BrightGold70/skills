"""Tests for h_mad_state_write.py — the orchestrator_state write path.

Until now there was none. `h_mad_resume_decision.py` reads state and
`h_mad_telemetry.py` reads it; nothing wrote it. The agent wrote state by
following prose in SKILL.md, which is why an established store drifted to 38
record shapes over 53 distinct keys against a 13-key schema, and why the
two-tier validator had to be documentation rather than enforcement.

A writer closes that loop: validation happens before the bytes land, so an
invented key cannot reach the file at all. It also gives the concurrency work a
place to hold a lock.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "h_mad_state_write.py"
sys.path.insert(0, str(SCRIPTS))

import h_mad_state_write as sw  # noqa: E402

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


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *[str(a) for a in args]],
        capture_output=True,
        text=True,
    )


class TestCreate:
    def test_creates_a_schema_valid_record(self, tmp_path):
        p = store(tmp_path)
        sw.create_feature(p, "demo")
        rec = read(p)["demo"]
        assert rec["feature"] == "demo"
        assert rec["current_phase"] == 0
        assert rec["phase"] is None

    def test_created_record_passes_strict_validation(self, tmp_path):
        import h_mad_state_validate as sv

        p = store(tmp_path)
        sw.create_feature(p, "demo")
        assert sv.classify(read(p)["demo"]) == "strict"

    def test_create_is_idempotent_and_does_not_clobber(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID, iterate_cycles=3)})
        sw.create_feature(p, "demo")
        assert read(p)["demo"]["iterate_cycles"] == 3

    def test_default_started_ts_is_current_utc_time_not_epoch(self, tmp_path):
        p = store(tmp_path)
        before = datetime.now(timezone.utc)
        sw.create_feature(p, "demo")
        after = datetime.now(timezone.utc)
        started = datetime.fromisoformat(read(p)["demo"]["started_ts"].replace("Z", "+00:00"))
        assert started != datetime(1970, 1, 1, tzinfo=timezone.utc)
        assert before - timedelta(seconds=120) <= started <= after + timedelta(seconds=120)

    def test_explicit_started_ts_is_stored_verbatim(self, tmp_path):
        p = store(tmp_path)
        explicit = "2001-02-03T04:05:06+09:00"
        sw.create_feature(p, "demo", explicit)
        assert read(p)["demo"]["started_ts"] == explicit

    def test_epoch_record_survives_unrelated_feature_write_byte_identically(self, tmp_path):
        old = dict(VALID, feature="old", started_ts="1970-01-01T00:00:00Z")
        p = store(tmp_path, {"old": old})
        before = json.dumps(old, sort_keys=True)
        sw.create_feature(p, "new")
        assert json.dumps(read(p)["old"], sort_keys=True) == before

    def test_new_default_started_ts_produces_short_telemetry_elapsed(self, tmp_path):
        import h_mad_telemetry as telemetry

        p = store(tmp_path)
        sw.create_feature(p, "demo")
        out = tmp_path / "telemetry.jsonl"
        assert telemetry.main(["record", "--feature", "demo", "--state", str(p), "--out", str(out)]) == 0
        row = json.loads(out.read_text().splitlines()[0])
        assert row["elapsed_min"] < 60


class TestSetFields:
    def test_merges_into_an_existing_record(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        sw.set_fields(p, "demo", last_completed_phase=5, current_phase=6)
        rec = read(p)["demo"]
        assert rec["last_completed_phase"] == 5
        assert rec["current_phase"] == 6
        assert rec["feature"] == "demo", "untouched fields must survive"

    def test_preserves_other_features(self, tmp_path):
        p = store(tmp_path, {"a": dict(VALID, feature="a"), "b": dict(VALID, feature="b")})
        sw.set_fields(p, "a", iterate_cycles=2)
        assert read(p)["b"]["iterate_cycles"] == 0

    def test_autonomous_entry_ts_accepts_integer_epoch(self, tmp_path):
        # F12: Phase-5a writes autonomous_entry_ts=<now> (an epoch int). The
        # strict schema previously typed it string|null, so the writer refused
        # the very value the SKILL prescribes and the timestamp stayed null.
        import h_mad_state_validate as sv

        p = store(tmp_path, {"demo": dict(VALID)})
        sw.set_fields(p, "demo", autonomous_entry_ts=1784673715)
        rec = read(p)["demo"]
        assert rec["autonomous_entry_ts"] == 1784673715
        assert sv.classify(rec) == "strict"

    def test_can_write_null(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID, phase="step5")})
        sw.set_fields(p, "demo", phase=None)
        assert read(p)["demo"]["phase"] is None

    def test_unknown_feature_raises(self, tmp_path):
        p = store(tmp_path)
        with pytest.raises(sw.StateWriteError, match="no such feature"):
            sw.set_fields(p, "nope", iterate_cycles=1)


class TestValidationBeforeWrite:
    """The whole point: an invalid record must never reach the file."""

    def test_invented_key_is_rejected(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        before = p.read_text()
        with pytest.raises(sw.StateWriteError):
            sw.set_fields(p, "demo", merge_sha="abc123")
        assert p.read_text() == before, "file must be untouched on rejection"

    def test_invalid_value_is_rejected(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        before = p.read_text()
        with pytest.raises(sw.StateWriteError):
            sw.set_fields(p, "demo", phase="bogus")
        assert p.read_text() == before

    def test_out_of_range_phase_is_rejected(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        with pytest.raises(sw.StateWriteError):
            sw.set_fields(p, "demo", current_phase=99)

    def test_archreview_enum_is_enforced(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        sw.set_fields(p, "demo", archreview="SKIPPED_NO_PANE")
        assert read(p)["demo"]["archreview"] == "SKIPPED_NO_PANE"
        with pytest.raises(sw.StateWriteError):
            sw.set_fields(p, "demo", archreview="PROBABLY_FINE")

    def test_a_pre_existing_legacy_sibling_does_not_block_the_write(self, tmp_path):
        """Most real stores hold legacy records. Validating the whole store on
        every write would make the writer unusable on any store with history."""
        legacy = {"current_phase": "complete", "last_completed_phase": "phase7", "phase": None}
        p = store(tmp_path, {"old": legacy, "demo": dict(VALID)})
        sw.set_fields(p, "demo", iterate_cycles=1)
        assert read(p)["demo"]["iterate_cycles"] == 1
        assert read(p)["old"] == legacy, "legacy sibling must be left alone"


class TestAtomicity:
    def test_no_temp_files_left_behind(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        sw.set_fields(p, "demo", iterate_cycles=1)
        strays = [f for f in os.listdir(tmp_path) if f.endswith(".tmp")]
        assert not strays, f"left temp files: {strays}"

    def test_lock_sidecar_is_single_and_predictable(self, tmp_path):
        """The lock file persists by design — unlinking it would race another
        holder. What must not happen is accumulation or an unpredictable name.
        """
        p = store(tmp_path, {"demo": dict(VALID)})
        for i in range(3):
            sw.set_fields(p, "demo", iterate_cycles=i)
        assert sorted(os.listdir(tmp_path)) == ["state.json", "state.json.lock"]

    def test_rejected_write_leaves_no_temp_file(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        with pytest.raises(sw.StateWriteError):
            sw.set_fields(p, "demo", phase="bogus")
        strays = [f for f in os.listdir(tmp_path) if f.endswith(".tmp")]
        assert not strays

    def test_store_stays_parseable_across_writes(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        for i in range(5):
            sw.set_fields(p, "demo", iterate_cycles=i)
        assert json.loads(p.read_text())["orchestrator_state"]["demo"]["iterate_cycles"] == 4

    def test_top_level_keys_survive(self, tmp_path):
        p = tmp_path / "state.json"
        p.write_text(json.dumps({"version": 1, "extra": "keep", "orchestrator_state": {"demo": dict(VALID)}}))
        sw.set_fields(p, "demo", iterate_cycles=1)
        assert json.loads(p.read_text())["extra"] == "keep"


class TestCli:
    def test_sets_a_typed_value_and_prints_a_token(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        r = run(p, "--feature", "demo", "--set", "last_completed_phase=5")
        assert r.returncode == 0
        assert "STATE-WRITE: OK" in r.stdout
        assert read(p)["demo"]["last_completed_phase"] == 5, "must coerce to int"

    def test_null_literal_is_parsed(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID, phase="step5")})
        r = run(p, "--feature", "demo", "--set", "phase=null")
        assert r.returncode == 0
        assert read(p)["demo"]["phase"] is None

    def test_string_value_stays_a_string(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        run(p, "--feature", "demo", "--set", "halt_reason=step5d:red_not_all_failing")
        assert read(p)["demo"]["halt_reason"] == "step5d:red_not_all_failing"

    def test_accepts_operator_override_and_round_trips(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        r = run(p, "--feature", "demo", "--set", "archreview=SKIPPED_OPERATOR_OVERRIDE")
        assert r.returncode == 0
        assert read(p)["demo"]["archreview"] == "SKIPPED_OPERATOR_OVERRIDE"

    def test_rejects_misspelled_operator_override_without_writing(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        before = p.read_bytes()
        r = run(p, "--feature", "demo", "--set", "archreview=SKIPPED_OVERRIDE")
        assert r.returncode == 2
        assert p.read_bytes() == before

    def test_rejection_exits_2_and_writes_nothing(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        before = p.read_text()
        r = run(p, "--feature", "demo", "--set", "merge_sha=abc")
        assert r.returncode == 2
        assert p.read_text() == before
        assert "STATE-WRITE: OK" not in r.stdout

    def test_create_flag(self, tmp_path):
        p = store(tmp_path)
        r = run(p, "--feature", "fresh", "--create")
        assert r.returncode == 0
        assert "fresh" in read(p)

    def test_missing_file_exits_2(self, tmp_path):
        r = run(tmp_path / "nope.json", "--feature", "demo", "--set", "iterate_cycles=1")
        assert r.returncode == 2


class TestLocking:
    """Foundation for the concurrency guard: writes serialise."""

    def test_sequential_writes_both_land(self, tmp_path):
        p = store(tmp_path, {"a": dict(VALID, feature="a"), "b": dict(VALID, feature="b")})
        sw.set_fields(p, "a", iterate_cycles=1)
        sw.set_fields(p, "b", iterate_cycles=2)
        s = read(p)
        assert s["a"]["iterate_cycles"] == 1
        assert s["b"]["iterate_cycles"] == 2

    def test_lock_is_released_after_a_rejected_write(self, tmp_path):
        """A validation failure must not strand the lock."""
        p = store(tmp_path, {"demo": dict(VALID)})
        with pytest.raises(sw.StateWriteError):
            sw.set_fields(p, "demo", phase="bogus")
        sw.set_fields(p, "demo", iterate_cycles=1)
        assert read(p)["demo"]["iterate_cycles"] == 1


class TestUndeclaredKeys:
    """J48 — an ad-hoc key must not brick the record it lands on.

    A prior session wrote `current_step`, `phase5_baseline` and `phase5_progress`
    into a live record. The guard then refused EVERY subsequent write, on a
    feature halted mid-Phase-5: the claim could be neither released nor taken.
    The guard was right to refuse the keys and wrong to leave no way out but the
    hand-edit the write path exists to prevent — and its message named the tier
    ("historical") rather than the keys, so an operator could not tell what to
    remove without reading the JSON.
    """

    BRICKED = dict(
        VALID,
        owner_session_id="dead-session",
        owner_heartbeat_ts="2026-07-22T00:00:00Z",
        current_step="5d",
        phase5_baseline="abc123",
        phase5_progress="3/7",
    )

    def test_a_write_that_introduces_an_undeclared_key_is_still_refused(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        with pytest.raises(sw.StateWriteError):
            sw.set_fields(p, "demo", phase5_progress="3/7")
        assert "phase5_progress" not in read(p)["demo"]

    def test_refusal_names_the_offending_keys_not_just_the_tier(self, tmp_path):
        p = store(tmp_path, {"demo": dict(self.BRICKED)})
        with pytest.raises(sw.StateWriteError) as exc:
            sw.release(p, "demo")
        message = str(exc.value)
        for key in ("current_step", "phase5_baseline", "phase5_progress"):
            assert key in message, f"refusal does not name {key}: {message}"

    def test_refusal_points_at_the_repair_verb(self, tmp_path):
        p = store(tmp_path, {"demo": dict(self.BRICKED)})
        with pytest.raises(sw.StateWriteError) as exc:
            sw.release(p, "demo")
        assert "--drop-undeclared" in str(exc.value)

    def test_refusal_distinguishes_a_preexisting_key_from_an_introduced_one(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID, phase5_progress="3/7")})
        with pytest.raises(sw.StateWriteError) as exc:
            sw.set_fields(p, "demo", current_step="5d")
        message = str(exc.value)
        assert "introduces current_step" in message
        assert "phase5_progress was already on the record" in message

    def test_drop_undeclared_removes_exactly_the_undeclared_keys(self, tmp_path):
        p = store(tmp_path, {"demo": dict(self.BRICKED)})
        _, removed = sw.drop_undeclared(p, "demo")
        assert sorted(removed) == ["current_step", "phase5_baseline", "phase5_progress"]
        record = read(p)["demo"]
        assert not (set(removed) & set(record))
        assert record["owner_session_id"] == "dead-session"  # declared keys survive
        assert record["current_phase"] == 5

    def test_drop_undeclared_restores_the_record_to_writable(self, tmp_path):
        p = store(tmp_path, {"demo": dict(self.BRICKED)})
        sw.drop_undeclared(p, "demo")
        sw.release(p, "demo")
        assert read(p)["demo"]["owner_session_id"] is None

    def test_drop_undeclared_is_idempotent_on_a_clean_record(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        before = p.read_text()
        _, removed = sw.drop_undeclared(p, "demo")
        assert removed == []
        assert p.read_text() == before

    def test_drop_undeclared_cannot_launder_an_otherwise_broken_record(self, tmp_path):
        """Stripping is not a bypass: what is left is validated like any write."""
        p = store(tmp_path, {"demo": dict(VALID, phase="bogus", phase5_progress="3/7")})
        before = p.read_text()
        with pytest.raises(sw.StateWriteError):
            sw.drop_undeclared(p, "demo")
        assert p.read_text() == before

    def test_cli_repairs_and_releases_a_bricked_record_in_one_command(self, tmp_path):
        p = store(tmp_path, {"demo": dict(self.BRICKED)})
        result = run(p, "--feature", "demo", "--drop-undeclared", "--release")
        assert result.returncode == 0, result.stderr
        assert "DROPPED" in result.stdout
        for key in ("current_step", "phase5_baseline", "phase5_progress"):
            assert key in result.stdout, f"CLI does not report dropping {key}"
        assert read(p)["demo"]["owner_session_id"] is None


class TestClaimProtocolEnforcement:
    """TLA+ F1 and F2 (skill-candidates, 2026-10-25 model check).

    F1: a session that lost its claim kept writing phases — `--set ... --session-id
    <old owner>` landed at exit 0, only the heartbeat refresh was skipped.
    F2: `--set owner_session_id=` / `--set owner_heartbeat_ts=` moved or froze a
    claim with no `--force`, and a null heartbeat then pinned the claim as live
    (`owner_is_live(None)` is True) so neither `--claim` nor an anonymous
    `--release` could free it. Ownership moves only through claim/release/beat.
    """

    OWNED = dict(VALID, owner_session_id="s1", owner_heartbeat_ts="2026-07-22T00:00:00Z")

    def test_a_displaced_owners_set_is_refused_and_writes_nothing(self, tmp_path):
        p = store(tmp_path, {"demo": dict(self.OWNED, owner_session_id="s2")})
        before = p.read_bytes()
        with pytest.raises(sw.StateWriteError) as exc:
            sw.merge_fields(p, "demo", {"current_phase": 6}, session_id="s1")
        assert "'s2'" in str(exc.value)
        assert p.read_bytes() == before

    def test_a_displaced_owners_append_is_refused(self, tmp_path):
        p = store(tmp_path, {"demo": dict(self.OWNED, owner_session_id="s2")})
        before = p.read_bytes()
        with pytest.raises(sw.StateWriteError) as exc:
            sw.merge_fields(p, "demo", {}, session_id="s1",
                            appends=[("implementation_authors", {"module": "m", "agent": "codex"})])
        assert "'s2'" in str(exc.value), "refused for ownership, not for the entry's shape"
        assert p.read_bytes() == before

    def test_cli_displaced_owner_set_exits_2_and_writes_nothing(self, tmp_path):
        p = store(tmp_path, {"demo": dict(self.OWNED, owner_session_id="s2")})
        before = p.read_bytes()
        r = run(p, "--feature", "demo", "--set", "current_phase=6", "--session-id", "s1")
        assert r.returncode == 2
        assert "STATE-WRITE: OK" not in r.stdout
        assert p.read_bytes() == before

    def test_a_session_id_on_an_unowned_record_is_still_accepted(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        sw.merge_fields(p, "demo", {"current_phase": 6}, session_id="s1")
        rec = read(p)["demo"]
        assert rec["current_phase"] == 6
        assert rec.get("owner_session_id") is None, "a set never claims"
        assert rec.get("owner_heartbeat_ts") is None, "nor beats a claim nobody holds"

    def test_claim_then_set_in_one_cli_call_is_the_owners_write(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        r = run(p, "--feature", "demo", "--claim", "s1", "--set", "current_phase=6",
                "--session-id", "s1")
        assert r.returncode == 0, r.stderr
        assert read(p)["demo"]["current_phase"] == 6

    @pytest.mark.parametrize("key,value", [("owner_session_id", "s2"),
                                           ("owner_heartbeat_ts", None)])
    def test_set_of_an_owner_field_is_refused(self, tmp_path, key, value):
        p = store(tmp_path, {"demo": dict(self.OWNED)})
        before = p.read_bytes()
        with pytest.raises(sw.StateWriteError) as exc:
            sw.merge_fields(p, "demo", {key: value})
        assert "--claim" in str(exc.value)
        assert p.read_bytes() == before

    def test_cli_refuses_an_owner_field_before_create_or_claim_lands(self, tmp_path):
        # Review finding: --create/--claim were persisted before the --set check ran,
        # so a refused invocation still left a claim behind.
        p = store(tmp_path)
        before = p.read_bytes()
        r = run(p, "--feature", "demo", "--create", "--claim", "s1",
                "--set", "owner_session_id=s9")
        assert r.returncode == 2
        assert p.read_bytes() == before

    def test_cli_refuses_a_claim_paired_with_another_sessions_write(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        before = p.read_bytes()
        r = run(p, "--feature", "demo", "--claim", "s1", "--set", "current_phase=6",
                "--session-id", "s2")
        assert r.returncode == 2
        assert p.read_bytes() == before, "the claim must not land when the write is refused"

    @pytest.mark.parametrize("item", ["owner_session_id=s2", "owner_heartbeat_ts=null"])
    def test_cli_set_of_an_owner_field_exits_2_even_from_the_owner(self, tmp_path, item):
        p = store(tmp_path, {"demo": dict(self.OWNED)})
        before = p.read_bytes()
        r = run(p, "--feature", "demo", "--set", item, "--session-id", "s1")
        assert r.returncode == 2
        assert p.read_bytes() == before


class TestHeartbeatBeats:
    """#126 — the heartbeat that did not beat.

    `claim` was the only writer of `owner_heartbeat_ts`, so a claim beat once at
    Phase 0 and then aged toward the two-hour staleness window while its owner was
    busiest. Measured live: one beat, then nothing for hours. A stale-looking live
    claim is takeable with a plain `--claim`, which is the collision the window
    exists to prevent. Two writers now: an explicit `--beat`, and any `--set` made
    by the owner (a phase write is a sign of life).
    """

    OWNED = dict(VALID, owner_session_id="me", owner_heartbeat_ts="2026-07-22T00:00:00Z")

    def test_beat_refreshes_the_owners_heartbeat(self, tmp_path):
        p = store(tmp_path, {"demo": dict(self.OWNED)})
        sw.beat(p, "demo", "me", now="2026-07-22T01:30:00Z")
        assert read(p)["demo"]["owner_heartbeat_ts"] == "2026-07-22T01:30:00Z"
        assert read(p)["demo"]["owner_session_id"] == "me"

    def test_a_beat_keeps_a_claim_live_past_the_window(self, tmp_path):
        from h_mad_state_ownership import owner_is_live
        p = store(tmp_path, {"demo": dict(self.OWNED)})
        assert not owner_is_live("2026-07-22T00:00:00Z", "2026-07-22T03:00:00Z")
        sw.beat(p, "demo", "me", now="2026-07-22T02:30:00Z")
        assert owner_is_live(read(p)["demo"]["owner_heartbeat_ts"], "2026-07-22T03:00:00Z")

    def test_beat_refuses_an_unowned_feature_and_does_not_claim(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        with pytest.raises(sw.StateWriteError) as exc:
            sw.beat(p, "demo", "me")
        assert "--claim" in str(exc.value)
        assert read(p)["demo"].get("owner_session_id") is None

    def test_beat_refuses_a_foreign_claim_and_leaves_its_heartbeat_alone(self, tmp_path):
        p = store(tmp_path, {"demo": dict(self.OWNED)})
        with pytest.raises(sw.StateWriteError) as exc:
            sw.beat(p, "demo", "someone-else", now="2026-07-22T01:00:00Z")
        assert "'me'" in str(exc.value)
        assert read(p)["demo"]["owner_heartbeat_ts"] == "2026-07-22T00:00:00Z"

    def test_beat_without_a_session_id_is_refused(self, tmp_path):
        p = store(tmp_path, {"demo": dict(self.OWNED)})
        with pytest.raises(sw.StateWriteError):
            sw.beat(p, "demo", None)
        assert read(p)["demo"]["owner_heartbeat_ts"] == "2026-07-22T00:00:00Z"

    def test_a_set_by_the_owner_refreshes_the_heartbeat(self, tmp_path):
        p = store(tmp_path, {"demo": dict(self.OWNED)})
        sw.merge_fields(p, "demo", {"current_phase": 6}, session_id="me", now="2026-07-22T01:00:00Z")
        rec = read(p)["demo"]
        assert rec["current_phase"] == 6
        assert rec["owner_heartbeat_ts"] == "2026-07-22T01:00:00Z"

    def test_a_set_without_a_session_id_leaves_the_heartbeat_alone(self, tmp_path):
        p = store(tmp_path, {"demo": dict(self.OWNED)})
        sw.set_fields(p, "demo", current_phase=6)
        assert read(p)["demo"]["owner_heartbeat_ts"] == "2026-07-22T00:00:00Z"

    def test_a_set_by_a_bystander_does_not_manufacture_liveness(self, tmp_path):
        # The write itself is now refused too (TLA+ F1, TestClaimProtocolEnforcement);
        # what this test still pins is that the claim's heartbeat is untouched.
        p = store(tmp_path, {"demo": dict(self.OWNED)})
        with pytest.raises(sw.StateWriteError):
            sw.merge_fields(p, "demo", {"current_phase": 6}, session_id="someone-else",
                            now="2026-07-22T01:00:00Z")
        rec = read(p)["demo"]
        assert rec["owner_heartbeat_ts"] == "2026-07-22T00:00:00Z"
        assert rec["owner_session_id"] == "me"

    def test_cli_beat_prints_a_token_and_exits_0(self, tmp_path):
        p = store(tmp_path, {"demo": dict(self.OWNED)})
        r = run(p, "--feature", "demo", "--beat", "--session-id", "me")
        assert r.returncode == 0, r.stderr
        assert "STATE-WRITE: BEAT feature=demo owner=me ts=" in r.stdout
        assert read(p)["demo"]["owner_heartbeat_ts"] != "2026-07-22T00:00:00Z"

    def test_cli_beat_without_session_id_exits_2_and_writes_nothing(self, tmp_path):
        p = store(tmp_path, {"demo": dict(self.OWNED)})
        before = p.read_bytes()
        r = run(p, "--feature", "demo", "--beat")
        assert r.returncode == 2
        assert "--session-id" in r.stderr
        assert p.read_bytes() == before

    def test_cli_set_with_owner_session_id_beats(self, tmp_path):
        p = store(tmp_path, {"demo": dict(self.OWNED)})
        r = run(p, "--feature", "demo", "--set", "current_phase=6", "--session-id", "me")
        assert r.returncode == 0, r.stderr
        assert read(p)["demo"]["owner_heartbeat_ts"] != "2026-07-22T00:00:00Z"

    @pytest.mark.parametrize("key", ["now", "session_id", "fields"])
    def test_a_set_key_named_like_the_signature_is_refused_not_swallowed(self, tmp_path, key):
        """Review finding: with **kwargs, `--set now=<ts>` became the heartbeat value
        and `--set session_id=x` was a TypeError at exit 1. Both must be the ordinary
        undeclared-key refusal at exit 2, writing nothing."""
        p = store(tmp_path, {"demo": dict(self.OWNED)})
        before = p.read_bytes()
        r = run(p, "--feature", "demo", "--set", f"{key}=2030-01-01T00:00:00Z",
                "--session-id", "me")
        assert r.returncode == 2, (r.returncode, r.stderr)
        assert "Traceback" not in r.stderr
        assert p.read_bytes() == before


class TestAppend:
    """FR-7: additions preserve history and validate the whole write atomically."""

    @pytest.fixture(scope="class")
    def hostile_module(self):
        env = {key: value for key, value in os.environ.items()
               if not key.startswith("HMAD_STUB_")}
        env["HMAD_STUB_HOSTILE"] = "all"
        result = subprocess.run(
            ["bash", str(Path(__file__).parent / "stubs" / "orca"),
             "worktree", "set", "--comment", "module fixture"],
            capture_output=True, text=True, env=env, timeout=10, check=True,
        )
        module = json.loads(result.stdout)["result"]["worktree"]["comment"]
        assert "\n" in module and "[a](b)" in module and "⟦/h-mad⟧" in module
        return module

    @staticmethod
    def _review(module, **overrides):
        return {"leg": "5e-review", "module": module, "reviewer": "codex",
                "implementer": "agy", "independent": True, **overrides}

    def test_append_keeps_both_earlier_entries(self, tmp_path, hostile_module):
        earlier = [self._review(hostile_module + " / first"),
                   self._review(hostile_module + " / second", leg="5e-verify")]
        earlier_text = [json.dumps(entry) for entry in earlier]
        added = self._review(hostile_module, leg="6a-prime")
        p = store(tmp_path, {"demo": dict(VALID, review_independence=earlier)})

        r = run(p, "--feature", "demo", "--append",
                "review_independence=" + json.dumps(added))

        assert r.returncode == 0, f"append must preserve both earlier entries: {r.stderr}"
        entries = read(p)["demo"]["review_independence"]
        assert [json.dumps(entry) for entry in entries[:2]] == earlier_text
        assert entries == [*earlier, added]

    def test_two_appends_in_one_call_keep_order(self, tmp_path, hostile_module):
        prior = self._review(hostile_module, leg="6a-prime")
        first = self._review(hostile_module + " / first")
        second = self._review(hostile_module + " / second", leg="5e-verify")
        p = store(tmp_path, {"demo": dict(VALID, review_independence=[prior])})

        r = run(p, "--feature", "demo", "--append",
                "review_independence=" + json.dumps(first), "--append",
                "review_independence=" + json.dumps(second))

        assert r.returncode == 0, f"repeated appends must accumulate in order: {r.stderr}"
        assert read(p)["demo"]["review_independence"] == [prior, first, second]

    def test_set_and_append_on_the_same_key_are_refused(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID)})
        before = p.read_bytes()

        r = run(p, "--feature", "demo", "--set",
                "production_paths_needing_red_tests=[]", "--append",
                'production_paths_needing_red_tests=["a"]')

        assert "--set and --append name the same key: production_paths_needing_red_tests" in r.stderr
        assert "unrecognized arguments" not in r.stderr
        assert r.returncode == 2, r.stderr
        assert p.read_bytes() == before, "same-key refusal must leave the store byte-identical"

    @pytest.mark.parametrize("key", ["review_independence", "implementation_authors"])
    def test_append_only_key_refuses_set(self, tmp_path, key, hostile_module):
        entry = (self._review(hostile_module) if key == "review_independence"
                 else {"module": hostile_module, "agent": "codex"})
        p = store(tmp_path, {"demo": dict(VALID, **{key: [entry]})})
        before = p.read_bytes()

        r = run(p, "--feature", "demo", "--set", f"{key}=[]")

        assert f"{key} is append-only: use --append" in r.stderr
        assert r.returncode == 2, r.stderr
        assert p.read_bytes() == before, "--set must never replace append-only history"

    def test_append_only_refusal_applies_to_library_callers(self, tmp_path, hostile_module):
        p = store(tmp_path, {"demo": dict(
            VALID, review_independence=[self._review(hostile_module)],
            implementation_authors=[{"module": hostile_module, "agent": "codex"}],
        )})
        before = p.read_bytes()

        for key in ("review_independence", "implementation_authors"):
            with pytest.raises(sw.StateWriteError, match=f"{key} is append-only: use --append"):
                sw.merge_fields(p, "demo", {key: []})
            assert p.read_bytes() == before, "library refusal must preserve append-only history"

    def test_append_value_is_strict_json(self, tmp_path, hostile_module):
        p = store(tmp_path, {"demo": dict(VALID)})
        before = p.read_bytes()
        item = "review_independence=" + hostile_module

        r = run(p, "--feature", "demo", "--set", "iterate_cycles=1", "--append", item)

        assert r.stderr.startswith("ERROR: "), "invalid --append JSON must use the writer's ERROR line"
        assert "--append" in r.stderr and (item in r.stderr or repr(item) in r.stderr), r.stderr
        assert "unrecognized arguments" not in r.stderr
        assert r.returncode == 2, r.stderr
        assert p.read_bytes() == before, "strict JSON refusal must also roll back the --set"

    def test_append_to_non_array_refused(self, tmp_path):
        p = store(tmp_path, {"demo": dict(VALID, current_phase=5)})
        before = p.read_bytes()

        r = run(p, "--feature", "demo", "--set", "iterate_cycles=1",
                "--append", "current_phase=6")

        assert "cannot append to a non-array value" in r.stderr
        assert "unrecognized arguments" not in r.stderr
        assert r.returncode == 2, r.stderr
        assert p.read_bytes() == before, "non-array refusal must also roll back the --set"

    @pytest.mark.parametrize("case", [
        pytest.param("review_independence", id="review-independence-bad-leg"),
        pytest.param("implementation_authors", id="implementation-authors-gemini"),
    ])
    def test_refused_entry_leaves_store_byte_identical(self, tmp_path, case, hostile_module):
        prior = (self._review(hostile_module) if case == "review_independence"
                 else {"module": hostile_module, "agent": "codex"})
        invalid = (self._review(hostile_module, leg="bad-leg") if case == "review_independence"
                   else {"module": hostile_module, "agent": "gemini"})
        p = store(tmp_path, {"demo": dict(VALID, **{case: [prior]})})
        before = p.read_bytes()

        r = run(p, "--feature", "demo", "--set", "iterate_cycles=1",
                "--append", case + "=" + json.dumps(prior),
                "--append", case + "=" + json.dumps(invalid))

        assert "would not validate" in r.stderr, "invalid append must reach the writer's schema refusal"
        assert "unrecognized arguments" not in r.stderr
        assert r.returncode == 2, r.stderr
        assert p.read_bytes() == before, "schema refusal must roll back every append and set"

    def test_ok_line_lists_appended_keys(self, tmp_path, hostile_module):
        review = self._review(hostile_module)
        author = {"module": hostile_module, "agent": "codex"}
        p = store(tmp_path, {"demo": dict(VALID)})

        r = run(p, "--feature", "demo", "--set", "iterate_cycles=1",
                "--append", "review_independence=" + json.dumps(review),
                "--append", "implementation_authors=" + json.dumps(author))

        expected = ("STATE-WRITE: OK feature=demo keys=3 "
                    "implementation_authors,iterate_cycles,review_independence")
        assert expected in r.stdout.splitlines(), f"OK line must list appended and set keys: {r.stdout!r} {r.stderr}"
        assert r.returncode == 0, r.stderr
        record = read(p)["demo"]
        assert record["iterate_cycles"] == 1
        assert record["review_independence"] == [review]
        assert record["implementation_authors"] == [author]

    def test_owner_append_refreshes_the_heartbeat(self, tmp_path, hostile_module):
        old_heartbeat = "2026-07-22T00:00:00Z"
        review = self._review(hostile_module)
        p = store(tmp_path, {"demo": dict(
            VALID, owner_session_id=hostile_module, owner_heartbeat_ts=old_heartbeat,
        )})

        r = run(p, "--feature", "demo", "--session-id", hostile_module,
                "--append", "review_independence=" + json.dumps(review))

        assert r.returncode == 0, f"an owner's append must refresh the heartbeat: {r.stderr}"
        record = read(p)["demo"]
        assert record["owner_heartbeat_ts"] != old_heartbeat
        assert datetime.fromisoformat(record["owner_heartbeat_ts"].replace("Z", "+00:00")) > datetime.fromisoformat(old_heartbeat.replace("Z", "+00:00"))
        assert record["owner_session_id"] == hostile_module
        assert record["review_independence"] == [review]

    def test_append_implementation_authors_entry(self, tmp_path, hostile_module):
        author = {"module": hostile_module, "agent": "codex"}
        p = store(tmp_path, {"demo": dict(VALID, implementation_authors=[author])})

        r = run(p, "--feature", "demo", "--append",
                "implementation_authors=" + json.dumps(author))

        assert r.returncode == 0, f"implementation author append must keep duplicate accepted entries: {r.stderr}"
        assert read(p)["demo"]["implementation_authors"] == [author, author]
