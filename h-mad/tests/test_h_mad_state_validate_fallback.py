"""J4: the state scripts must work on an interpreter without `jsonschema`.

F8/J4: `python3` on a Homebrew/PEP-668 machine has no `jsonschema`, so every
`h_mad_state_write.py` / `_validate.py` / `_staleness.py` call in a run exits 2
until the operator manually substitutes `/opt/anaconda3/bin/python3`. It was hit
twice in the first five minutes of one run. A better error message -- which is
what F8 actually shipped -- is not a fix for a missing dependency.

Of the three filed directions, "degrade to the historical tier when jsonschema is
absent" is rejected outright: silently validating against a weaker schema is the
same class of defect as an unenforced guard. Documenting a required interpreter
helps but leaves the friction. So: a bundled stdlib validator covering exactly
the constructs these two schemas use.

A hand-rolled validator is only trustworthy if it AGREES with the real one, so
the tests below are differential. They run under an interpreter that has
`jsonschema` (the suite's does) and assert the fallback returns the same verdict
on a corpus covering every construct in both schema files -- plus the real
records on disk, per `invariants.base.md` §"Incident replay".

The subtle one is `format`. Draft-07 treats it as an annotation unless a format
checker is passed, and the production code passes none -- so `"started_ts":
"not-a-date"` is VALID today. A fallback that "helpfully" enforced date-time
would reject records the real validator accepts, which is a regression wearing
the costume of an improvement.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "h-mad" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import h_mad_state_validate as SV  # noqa: E402

STRICT = json.loads((SCRIPTS / "h_mad_state_schema.json").read_text())
HISTORICAL = json.loads((SCRIPTS / "h_mad_state_schema_historical.json").read_text())

jsonschema = pytest.importorskip("jsonschema")


def _valid_record(**over):
    rec = {
        "feature": "demo",
        "started_ts": "2026-07-23T00:00:00+00:00",
        "last_completed_phase": 3,
        "current_phase": 4,
        "phase": None,
        "audit_cycles": {"plan": 1, "design": 0, "impl_plan": 0},
        "iterate_cycles": 0,
        "halt_reason": None,
        "halt_ts": None,
    }
    rec.update(over)
    return rec


# Every construct the two schemas use, each with a case that must FAIL and (where
# meaningful) one that must PASS. `format` is deliberately in the pass column.
CORPUS = [
    ("canonical", _valid_record()),
    ("required missing", {k: v for k, v in _valid_record().items() if k != "feature"}),
    ("type wrong (int for string)", _valid_record(feature=7)),
    ("type list accepts null", _valid_record(halt_reason=None)),
    ("type list accepts string", _valid_record(halt_reason="step5:boom")),
    ("enum violation", _valid_record(phase="step9")),
    ("enum accepts member", _valid_record(phase="step5")),
    ("minimum violation", _valid_record(current_phase=-1)),
    ("maximum violation", _valid_record(current_phase=99)),
    ("minLength violation", _valid_record(feature="")),
    ("additionalProperties:false", _valid_record(surprise=1)),
    ("nested object ok", _valid_record(
        substrate={"name": "orca", "agents": {"codex": "term_a"}})),
    ("nested additionalProperties schema violation", _valid_record(
        substrate={"name": "orca", "agents": {"codex": 5}})),
    ("nested additionalProperties:false", _valid_record(
        substrate={"name": "orca", "nope": 1})),
    ("substrate null allowed", _valid_record(substrate=None)),
    ("items violation", _valid_record(production_paths_needing_red_tests=[1, 2])),
    ("items ok", _valid_record(production_paths_needing_red_tests=["a/b.py"])),
    # JSON Schema treats booleans as distinct from integers; Python does not
    # (bool subclasses int). Without this case the bool-guard in _type_ok is
    # unenforced -- found by mutation testing, which passed 5/5 with it deleted.
    ("bool is not an integer", _valid_record(current_phase=True)),
    ("bool is not an integer (nested)", _valid_record(
        audit_cycles={"plan": True, "design": 0, "impl_plan": 0})),
    ("bool is not a string", _valid_record(feature=True)),
    # The trap: format is annotation-only, so this is VALID.
    ("bad format is still valid", _valid_record(started_ts="not-a-date")),
    ("not an object", ["nope"]),
    ("empty object", {}),
]


@pytest.mark.parametrize("schema,label",
                         [(STRICT, "strict"), (HISTORICAL, "historical")])
def test_fallback_agrees_with_jsonschema_on_every_construct(schema, label):
    real = jsonschema.Draft7Validator(schema)
    mini = SV._MiniDraft7(schema)
    for name, record in CORPUS:
        assert mini.is_valid(record) == real.is_valid(record), (
            f"[{label}] disagreement on {name!r}: "
            f"fallback={mini.is_valid(record)} jsonschema={real.is_valid(record)}"
        )


def test_fallback_agrees_on_the_real_records_on_disk():
    # §"Incident replay": the corpus above was authored beside the fallback and
    # therefore shares its assumptions. These records were not.
    state = REPO_ROOT / "docs" / ".bkit-memory.json"
    if not state.is_file():
        pytest.skip("no live state file")
    records = json.loads(state.read_text()).get("orchestrator_state", {})
    assert records, "live state file has no records to replay"
    for schema in (STRICT, HISTORICAL):
        real = jsonschema.Draft7Validator(schema)
        mini = SV._MiniDraft7(schema)
        for feature, rec in records.items():
            assert mini.is_valid(rec) == real.is_valid(rec), (
                f"disagreement on live record {feature!r}"
            )


def test_classify_matches_between_backends_on_the_corpus():
    # classify() is what everything else calls; agreement at the leaf is not
    # agreement at the verdict.
    for name, record in CORPUS:
        with_real = SV.classify(record)
        SV._validators.clear()
        try:
            SV._FORCE_FALLBACK = True
            with_mini = SV.classify(record)
        finally:
            SV._FORCE_FALLBACK = False
            SV._validators.clear()
        assert with_real == with_mini, f"classify disagrees on {name!r}"


def test_state_scripts_run_without_jsonschema():
    """The end-to-end point of J4: a plain `python3` must work.

    Simulated by blocking the import, which is what the operator's interpreter
    does for real.
    """
    state = REPO_ROOT / "docs" / ".bkit-memory.json"
    if not state.is_file():
        pytest.skip("no live state file")
    blocker = (
        "import sys;"
        "sys.modules['jsonschema']=None;"
        "import runpy;"
        "sys.argv=['h_mad_state_validate.py', %r];"
        "runpy.run_path(%r, run_name='__main__')"
        % (str(state), str(SCRIPTS / "h_mad_state_validate.py"))
    )
    r = subprocess.run([sys.executable, "-c", blocker],
                       capture_output=True, text=True)
    assert "jsonschema is required" not in r.stderr, r.stderr
    assert "STATE:" in r.stdout, f"no verdict emitted: {r.stdout!r} {r.stderr!r}"
