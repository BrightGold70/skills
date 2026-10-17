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
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "h-mad" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import h_mad_state_validate as SV  # noqa: E402
import h_mad_state_write as SW  # noqa: E402

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


#: A committed, redacted snapshot of real orchestrator records (#27).
#:
#: The replay used to read `docs/.bkit-memory.json` alone, which is gitignored
#: h-mad orchestrator state. So in a fresh clone, a linked worktree, a CI runner,
#: or any subagent given `isolation: "worktree"` it did not exist and BOTH replay
#: tests skipped — permanently, silently, and reporting success. Measured
#: 2026-09-13 by reconciling two agents' counts on the SAME commit: `3222 passed`
#: here, `3219 passed, 2 skipped` in a clean worktree. Those two are the only
#: tests in this file validating against records that were NOT authored beside
#: the validator, so the highest-value tests were exactly the ones that vanished
#: in the environment where the suite most often runs unattended.
#:
#: Identifiers are redacted; TYPES, FORMATS and enum values are verbatim, because
#: the validators check structure and structure is the entire payload. Selected
#: to cover every distinct shape in the live store — key-set AND the type of each
#: value — so the union-typed keys survive: `autonomous_entry_ts` occurs as int,
#: str and null, and `owner_session_id` in both a uuid and a short form. The
#: `1970-01-01T00:00:00Z` epoch-zero `started_ts` is kept deliberately; it is the
#: kind of artifact a hand-authored corpus never contains.
REPLAY_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "state_incident_replay.json"


def _replay_sources():
    """The committed fixture ALWAYS, and the live store too when it exists.

    Both, not either. The fixture guarantees the replay runs everywhere; the live
    store is what catches a shape written since the fixture was taken. Dropping
    the live half would make this a frozen corpus — the thing §"Incident replay"
    exists NOT to be.
    """
    sources = [("fixture", REPLAY_FIXTURE)]
    live = REPO_ROOT / "docs" / ".bkit-memory.json"
    if live.is_file():
        sources.append(("live", live))
    return sources


def test_the_replay_fixture_is_committed_and_still_covers_the_awkward_shapes():
    """The guard on the guard.

    A fixture trimmed to one tidy record would leave the replay running and
    measuring nothing, which is this row's defect wearing a fixture. Pins the
    union-typed keys by name rather than asserting a record count, because the
    count is allowed to change and the unions are not.
    """
    assert REPLAY_FIXTURE.is_file(), f"{REPLAY_FIXTURE} is missing — the replay is back to skipping"
    # TRACKED, not merely present. Being present in the author's checkout and
    # absent everywhere else is the whole of #27: `docs/.bkit-memory.json` is a
    # real file here and gitignored, so it existed for every run that reported
    # this file green and for none of the runs that mattered.
    tracked = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "--error-unmatch", str(REPLAY_FIXTURE)],
        capture_output=True, text=True)
    assert tracked.returncode == 0, (
        f"{REPLAY_FIXTURE} is not tracked by git — it will not exist in a clone, "
        f"a linked worktree, or CI, which is the defect this fixture closes")
    records = json.loads(REPLAY_FIXTURE.read_text())["orchestrator_state"]
    assert len(records) >= 5, len(records)
    for key, wanted in (("autonomous_entry_ts", {"int", "str", "NoneType"}),
                        ("owner_session_id", {"str", "NoneType"})):
        got = {type(r[key]).__name__ for r in records.values() if key in r}
        assert wanted <= got, (f"{key} lost a shape: have {sorted(got)}, "
                               f"need {sorted(wanted)}")
    assert any(str(r.get("started_ts", "")).startswith("1970") for r in records.values()), (
        "the epoch-zero started_ts is gone — a hand-authored corpus never has one"
    )


def test_fallback_agrees_on_the_real_records_on_disk():
    # §"Incident replay": the corpus above was authored beside the fallback and
    # therefore shares its assumptions. These records were not.
    ran = 0
    for label, state in _replay_sources():
        records = json.loads(state.read_text()).get("orchestrator_state", {})
        assert records, f"{label} state file has no records to replay"
        for schema in (STRICT, HISTORICAL):
            real = jsonschema.Draft7Validator(schema)
            mini = SV._MiniDraft7(schema)
            for feature, rec in records.items():
                assert mini.is_valid(rec) == real.is_valid(rec), (
                    f"disagreement on {label} record {feature!r}"
                )
                ran += 1
    assert ran, "no records replayed — the replay measured nothing"


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
    # The committed fixture, so this runs in a clean checkout too (#27). It is a
    # real state file in every respect the script cares about.
    state = REPLAY_FIXTURE
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


# FR-1: exercise the public verdict on each backend, not just schema leaves.
@pytest.fixture(params=["library", "bundled"])
def path(request, monkeypatch):
    if request.param == "library":
        assert SV._Draft7Validator is not None, "library path requires jsonschema"
    SV._validators.clear()
    monkeypatch.setattr(SV, "_FORCE_FALLBACK", request.param == "bundled")
    try:
        yield request.param
    finally:
        SV._validators.clear()


@pytest.fixture(scope="session")
def fr1_hostile_module():
    """Use the agent-input stub's real hostile knob for free-form module names."""
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


def _fr1_switch(**over):
    return {"from": "codex", "to": "agy", "reason": "status",
            "ts": "2026-10-16T07:05:09Z", **over}


def _fr1_review_entry(module, **over):
    return {"leg": "5e-review", "module": module, "reviewer": "codex",
            "implementer": "agy", "independent": True, **over}


@pytest.mark.parametrize("name,value", [
    pytest.param("implementer", "codex", id="implementer-codex"),
    pytest.param("implementer", "agy", id="implementer-agy"),
    pytest.param("implementer", None, id="implementer-null"),
    pytest.param("agy_status", "available", id="agy_status-available"),
    pytest.param("agy_status", "unavailable", id="agy_status-unavailable"),
    pytest.param("agy_status", "exhausted", id="agy_status-exhausted"),
    pytest.param("agy_status", None, id="agy_status-null"),
    pytest.param("implementer_switch", None, id="implementer_switch-null"),
    pytest.param("implementer_switch", _fr1_switch(), id="implementer_switch-object"),
    pytest.param("review_independence", [], id="review_independence-empty"),
    pytest.param("review_independence", "one-entry", id="review_independence-one-entry"),
])
def test_fr1_value_accepted(path, name, value, fr1_hostile_module):
    if name == "review_independence" and value == "one-entry":
        value = [_fr1_review_entry(fr1_hostile_module)]
    record = _valid_record(**{name: value})
    assert SV.classify(record) == "strict", f"{path}: {name} must accept {value!r}"


@pytest.mark.parametrize("case", [
    "implementer-grok", "implementer-empty-string", "agy_status-quota",
    "implementer_switch-missing-ts", "implementer_switch-extra-key",
    "implementer_switch-reason-unknown", "implementer_switch-to-gemini",
    "review_independence-not-array", "review_independence-leg-unknown",
    "review_independence-missing-independent", "review_independence-independent-string",
    "review_independence-extra-key",
])
def test_fr1_value_refused(path, case, fr1_hostile_module):
    name, variant = case.split("-", 1)
    if name == "implementer":
        value = "grok" if variant == "grok" else ""
    elif name == "agy_status":
        value = "quota"
    elif name == "implementer_switch":
        value = _fr1_switch()
        if variant == "missing-ts":
            value.pop("ts")
        elif variant == "extra-key":
            value["extra"] = fr1_hostile_module
        elif variant == "reason-unknown":
            value["reason"] = "unknown"
        else:
            value["to"] = "gemini"
    else:
        entry = _fr1_review_entry(fr1_hostile_module)
        if variant == "leg-unknown":
            entry["leg"] = "5e-unknown"
        elif variant == "missing-independent":
            entry.pop("independent")
        elif variant == "independent-string":
            entry["independent"] = "true"
        elif variant == "extra-key":
            entry["extra"] = fr1_hostile_module
        value = entry if variant == "not-array" else [entry]
    record = _valid_record(**{name: value})
    classification = SV.classify(record)
    assert SV.undeclared_keys(record) == [], f"{path}: {name} must be declared before testing refusal"
    assert classification != "strict", f"{path}: {case} must refuse strict validation"


def test_fr1_record_without_new_fields_unchanged(path):
    record = _valid_record()
    assert not set(record).intersection({
        "implementer", "agy_status", "implementer_switch",
        "review_independence", "implementation_authors",
    })
    assert SV.classify(record) == "strict", f"{path}: records without FR-1 fields remain strict"


@pytest.mark.parametrize("ts", [
    pytest.param("not-a-date", id="not-a-date"),
    pytest.param("2026-10-16", id="date-only"),
    pytest.param("2026-02-30T00:00:00Z", id="feb-30"),
    pytest.param("2026-10-16T00:00:00Zjunk", id="zjunk"),
    pytest.param("2016-12-31T23:59:60Z", id="leap-60"),
    pytest.param("2026-10-16T00:00:00+24:00", id="offset-24"),
])
def test_switch_ts_refused(path, ts):
    record = _valid_record(implementer_switch=_fr1_switch(ts=ts))
    classification = SV.classify(record)
    assert SV.undeclared_keys(record) == [], f"{path}: implementer_switch must be declared"
    assert classification == "invalid", f"{path}: implementer_switch.ts must refuse {ts!r} before either tier"


@pytest.mark.parametrize("ts", [
    pytest.param(SW._utc_now(), id="writer-form"),
    pytest.param("2016-12-31T23:59:59Z", id="leap-59"),
    pytest.param("2026-10-16T07:05:09Z", id="zone-upper-z"),
    pytest.param("2026-10-16T07:05:09z", id="zone-lower-z"),
    pytest.param("2026-10-16T07:05:09+09:00", id="zone-offset"),
])
def test_switch_ts_accepted(path, ts):
    record = _valid_record(implementer_switch=_fr1_switch(ts=ts))
    assert SV.classify(record) == "strict", f"{path}: implementer_switch.ts must accept {ts!r}"


@pytest.mark.parametrize("value", [
    pytest.param(5, id="int-5"),
    pytest.param(None, id="none"),
    pytest.param(SW._utc_now() + "\n", id="trailing-newline"),
    pytest.param("２０２６-１０-１６T０７:０５:０９Z", id="fullwidth-digits"),
])
def test_rfc3339_datetime_refuses_non_strings_and_lookalikes(value):
    assert SV.rfc3339_datetime(value) is False, f"rfc3339_datetime must refuse {value!r}"


@pytest.mark.parametrize("case", [
    "empty", "agent-codex", "agent-agy", "agent-grok", "agent-claude", "three-entry-log",
])
def test_implementation_authors_accepted(path, case, fr1_hostile_module):
    if case == "empty":
        value = []
    elif case == "three-entry-log":
        value = [{"module": fr1_hostile_module, "agent": agent}
                 for agent in ("agy", "codex", "agy")]
    else:
        value = [{"module": fr1_hostile_module, "agent": case.removeprefix("agent-")}]
    record = _valid_record(implementation_authors=value)
    assert SV.classify(record) == "strict", f"{path}: implementation_authors must accept {case}"
    # Classification must not normalize the acceptance log into a set or reorder it.
    if case == "three-entry-log":
        assert record["implementation_authors"] == [
            {"module": fr1_hostile_module, "agent": agent}
            for agent in ("agy", "codex", "agy")
        ]


@pytest.mark.parametrize("case", [
    "agent-gemini", "missing-agent", "missing-module", "module-empty",
    "extra-key", "non-object-entry", "non-array",
])
def test_implementation_authors_refused(path, case, fr1_hostile_module):
    entry = {"module": fr1_hostile_module, "agent": "agy"}
    if case == "agent-gemini":
        entry["agent"] = "gemini"
    elif case == "missing-agent":
        entry.pop("agent")
    elif case == "missing-module":
        entry.pop("module")
    elif case == "module-empty":
        entry["module"] = ""
    elif case == "extra-key":
        entry["extra"] = fr1_hostile_module
    value = entry if case == "non-array" else [fr1_hostile_module if case == "non-object-entry" else entry]
    record = _valid_record(implementation_authors=value)
    classification = SV.classify(record)
    assert SV.undeclared_keys(record) == [], f"{path}: implementation_authors must be declared"
    assert classification != "strict", f"{path}: implementation_authors must refuse {case}"


def test_property_valid_implementer_switch_none_does_not_raise(path):
    assert SV.property_valid("implementer_switch", None) is True, (
        f"{path}: property_valid must accept null implementer_switch without indexing ts"
    )


@pytest.mark.parametrize("ts,expected", [
    pytest.param("not-a-date", False, id="bad-ts"),
    pytest.param("2026-10-16T07:05:09Z", True, id="good-ts"),
])
def test_property_valid_applies_the_ts_predicate(path, ts, expected):
    assert SV.property_valid("implementer_switch", _fr1_switch(ts=ts)) is expected, (
        f"{path}: property_valid implementer_switch.ts={ts!r} must be {expected}"
    )


@pytest.mark.parametrize("leg,expected", [
    pytest.param("5e-review", True, id="well-formed"),
    pytest.param("5e-unknown", False, id="bad-leg"),
])
def test_property_valid_review_independence_entry(path, leg, expected, fr1_hostile_module):
    value = [_fr1_review_entry(fr1_hostile_module, leg=leg)]
    assert SV.property_valid("review_independence", value) is expected, (
        f"{path}: property_valid review_independence leg={leg!r} must be {expected}"
    )
