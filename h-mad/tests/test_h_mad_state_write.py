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
