"""Tests for h_mad_state_validate.py — two-tier orchestrator_state validation.

Background: the v2.2 schema was aspirational. Nothing enforced it at write
time, `additionalProperties: false` rejected every key a run invented, and an
established store drifted to 38 distinct record shapes over 53 distinct keys.
The documented whole-store validation snippet therefore always failed, which
made it useless and so nobody ran it.

Two tiers fix that honestly: STRICT is v2.2 and governs new records;
HISTORICAL accepts what older runs actually wrote, so a store validates
end-to-end and genuinely broken records still stand out.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "h_mad_state_validate.py"
sys.path.insert(0, str(SCRIPTS))

import h_mad_state_validate as sv  # noqa: E402


STRICT_RECORD = {
    "feature": "review-pipeline-correctness",
    "started_ts": "2026-07-21T00:02:21Z",
    "last_completed_phase": 4,
    "current_phase": 5,
    "phase": "step5",
    "autonomous_entry_ts": "2026-07-21T03:08:23Z",
    "audit_cycles": {"plan": 2, "design": 3, "impl_plan": 2},
    "iterate_cycles": 0,
    "halt_reason": None,
    "halt_ts": None,
}

# Shape observed 7x in a real store: string phases, per-phase cycle keys,
# and sha keys the strict schema never allowed.
LEGACY_RECORD = {
    "current_phase": "complete",
    "last_completed_phase": "phase7_closure",
    "phase": None,
    "halt_reason": None,
    "plan_audit_cycles": 5,
    "design_audit_cycles": 11,
    "impl_plan_audit_cycles": 5,
    "autonomous_entry_ts": "2026-07-09T00:37:00Z",
    "baseline_commit": "a6f4d3d6",
    "impl_commit": "7b015610",
    "match_rate": 100,
}


def write_store(tmp_path, records) -> Path:
    p = tmp_path / "state.json"
    p.write_text(json.dumps({"version": 1, "orchestrator_state": records}))
    return p


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *[str(a) for a in args]],
        capture_output=True,
        text=True,
    )


class TestClassify:
    def test_v22_record_is_strict(self):
        assert sv.classify(STRICT_RECORD) == "strict"

    def test_legacy_record_is_historical(self):
        assert sv.classify(LEGACY_RECORD) == "historical"

    def test_epoch_int_timestamp_is_historical_not_invalid(self):
        rec = dict(LEGACY_RECORD, autonomous_entry_ts=1783749368)
        assert sv.classify(rec) == "historical"

    def test_string_phase_marker_is_historical(self):
        rec = dict(LEGACY_RECORD, phase="complete")
        assert sv.classify(rec) == "historical"

    @pytest.mark.parametrize(
        "missing", ["current_phase", "last_completed_phase", "phase"]
    )
    def test_missing_a_universal_key_is_invalid(self, missing):
        rec = {k: v for k, v in LEGACY_RECORD.items() if k != missing}
        assert sv.classify(rec) == "invalid"

    def test_empty_record_is_invalid(self):
        assert sv.classify({}) == "invalid"

    def test_non_object_is_invalid(self):
        assert sv.classify("not-a-record") == "invalid"


class TestCliVerdict:
    def test_all_strict_passes(self, tmp_path):
        store = write_store(tmp_path, {"a": STRICT_RECORD})
        r = run_cli(store)
        assert r.returncode == 0
        assert "STATE: PASS strict=1 historical=0 invalid=0" in r.stdout

    def test_mixed_store_passes_and_reports_both_tiers(self, tmp_path):
        store = write_store(
            tmp_path, {"a": STRICT_RECORD, "b": LEGACY_RECORD, "c": LEGACY_RECORD}
        )
        r = run_cli(store)
        assert r.returncode == 0
        assert "STATE: PASS strict=1 historical=2 invalid=0" in r.stdout

    def test_invalid_record_fails_and_is_named(self, tmp_path):
        store = write_store(tmp_path, {"good": STRICT_RECORD, "broken": {}})
        r = run_cli(store)
        assert r.returncode == 0, "verdict must not be signalled by exit code"
        assert "STATE: FAIL" in r.stdout
        assert "invalid=1" in r.stdout
        assert "broken" in r.stdout

    def test_emits_hmad_marker(self, tmp_path):
        store = write_store(tmp_path, {"a": STRICT_RECORD})
        r = run_cli(store)
        assert "[H-MAD]" in r.stdout

    def test_empty_store_passes(self, tmp_path):
        store = write_store(tmp_path, {})
        r = run_cli(store)
        assert r.returncode == 0
        assert "STATE: PASS" in r.stdout


class TestStrictOnly:
    """New records must meet v2.2 — that is how drift stops."""

    def test_legacy_fails_under_strict_only(self, tmp_path):
        store = write_store(tmp_path, {"b": LEGACY_RECORD})
        r = run_cli(store, "--strict-only")
        assert "STATE: FAIL" in r.stdout
        assert r.returncode == 0

    def test_strict_passes_under_strict_only(self, tmp_path):
        store = write_store(tmp_path, {"a": STRICT_RECORD})
        r = run_cli(store, "--strict-only")
        assert "STATE: PASS" in r.stdout

    def test_feature_scopes_to_one_record(self, tmp_path):
        """The write-path check validates only the record just written."""
        store = write_store(tmp_path, {"a": STRICT_RECORD, "b": LEGACY_RECORD})
        r = run_cli(store, "--feature", "a", "--strict-only")
        assert "STATE: PASS" in r.stdout


class TestOperationalErrors:
    """Exit code is reserved for operational failure, never for a verdict."""

    def test_missing_file_exits_2(self, tmp_path):
        r = run_cli(tmp_path / "nope.json")
        assert r.returncode == 2
        assert "STATE:" not in r.stdout

    def test_malformed_json_exits_2(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{not json")
        r = run_cli(p)
        assert r.returncode == 2

    def test_unknown_feature_exits_2(self, tmp_path):
        store = write_store(tmp_path, {"a": STRICT_RECORD})
        r = run_cli(store, "--feature", "does-not-exist")
        assert r.returncode == 2
