"""FR-7/FR-10 doc pins and OD-1(A)'s test-local attribution transcription.

The transcription selects what the procedure says; it cannot prove an
orchestrator follows that procedure. No production reader of authors is added.
"""

import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
sys.path.insert(0, str(ROOT / "scripts"))

import h_mad_phase7_preconditions as p7  # noqa: E402
from h_mad_state_validate import property_valid  # noqa: E402


def _span(start, end):
    text = SKILL.read_text(encoding="utf-8")
    assert text.count(start) == 1, f"expected exactly one SKILL.md {start!r}"
    begin = text.index(start)
    return " ".join(text[begin:text.index(end, begin)].split())


def _closure():
    return _span("7. **Closure (autonomous)**", "\n## Phase 5")


def _require(text, sentence, property_name):
    assert " ".join(sentence.split()) in text, property_name


def _author_append(text, property_name):
    match = re.search(r"--append implementation_authors='(\{[^\n]*?\})'", text)
    assert match, f"{property_name}: missing --append implementation_authors JSON"
    assert json.loads(match.group(1)) == {"module": "<module>", "agent": "<agent>"}, (
        f"{property_name}: append must hold the module and accepted dispatch's agent"
    )


def test_closure_step_carries_every_warning_line():
    closure = _closure()
    _require(closure, "Carry every `WARNING` line into the Phase-7 report", (
        "Phase-7 closure must carry every WARNING line into the report"
    ))
    for code in ("review_non_independent", "review_independence_unrecorded",
                 "review_independence_malformed"):
        assert code in closure, f"Phase-7 closure must name WARNING {code}"


def test_closure_step_appends_review_independence_for_every_implementer():
    closure = _closure()
    _require(closure, "After each 5e-review, 5e-verify and 6a-prime leg", (
        "closure must append review independence after each of the three review legs"
    ))
    assert "--append review_independence=" in closure, (
        "closure must run --append review_independence after each review leg"
    )
    assert "for every implementer" in closure, (
        "review-independence recording must apply for every implementer"
    )
    for key in ("leg", "module", "reviewer", "implementer", "independent"):
        assert f'"{key}":' in closure, f"review append must include JSON key {key}"
    assert "`independent` is `reviewer != implementer`" in closure
    _require(closure, "one 6a-prime entry per module", (
        "whole-diff architectural review must record each module's independence"
    ))


def test_attribution_step_names_the_dispatch_as_the_source():
    closure = _closure()
    _require(closure, "`implementer` is read from the dispatch", (
        "attribution must name the accepted implementation dispatch as implementer source"
    ))
    _require(closure, "never read from `implementer_switch.to` or from the `implementer` field", (
        "routing fields must never be used as attribution sources"
    ))
    for token in ("TDD-IMPLEMENTER:", "--agent", "claude"):
        assert token in closure, f"dispatch attribution must explain {token}"


def test_5e_bullet_appends_the_author_at_green_acceptance():
    bullet = _span("- **5e** — GREEN dispatch", "- **5f** —")
    _author_append(bullet, "5e GREEN acceptance")
    for sentence in (
        "when the orchestrator accepts a module's GREEN dispatch",
        "DONE", "DONE_WITH_CONCERNS",
        "before the module's 5e spec-review leg runs",
        "Every accepted fix dispatch", "before the next leg that reviews the fixed code",
        "TDD-IMPLEMENTER:",
    ):
        _require(bullet, sentence, f"5e author append must state {sentence!r}")


def test_6a_prime_fix_appends_the_author():
    bullet = _span("- **6a-prime** — architectural review via agy", "- **6a**")
    _author_append(bullet, "6a-prime accepted fix")
    for sentence in (
        "WITH_FIXES", "accepted fix dispatch",
        "before the next leg that reviews the fixed code", "TDD-IMPLEMENTER:",
    ):
        _require(bullet, sentence, f"6a-prime fix author append must state {sentence!r}")


def test_5d_bullet_appends_no_author():
    bullet = _span("- **5d** — RED dispatch", "- **5e** — GREEN dispatch")
    assert not re.search(r"--append\s+implementation_authors\s*=", bullet), (
        "5d RED writes tests and must never append an implementation author"
    )


def attribute(record, leg, module, reviewer):
    """Transcribe FR-7: durable complete author set, or no entry (OD-1(A))."""
    entries = record.get("implementation_authors")
    if not isinstance(entries, list) or not all(
        property_valid("implementation_authors", [entry]) for entry in entries
    ):
        return None
    authors = [entry["agent"] for entry in entries if entry["module"] == module]
    if not authors:
        return None
    implementer = reviewer if reviewer in authors else authors[-1]
    return {"leg": leg, "module": module, "reviewer": reviewer,
            "implementer": implementer, "independent": reviewer != implementer}


def _mutant_attribute(record, leg, module, reviewer, mutant, dispatches):
    """The five named AC-7.3 counter-rules, deliberately wrong transcriptions."""
    changed = json.loads(json.dumps(record))
    if mutant == "routing-as-authorship":
        changed["implementation_authors"] = [
            {"module": module, "agent": record["implementer_switch"]["to"]}
        ]
    elif mutant == "authors-from-review-projection":
        changed["implementation_authors"] = [
            {"module": module, "agent": entry["implementer"]}
            for entry in record["review_independence"] if entry["module"] == module
        ]
    elif mutant == "absent-means-independent":
        authors = [entry["agent"] for entry in record.get("implementation_authors", [])
                   if entry["module"] == module]
        return {"leg": leg, "module": module, "reviewer": reviewer,
                "implementer": authors[-1] if authors else "codex",
                "independent": reviewer not in authors}
    elif mutant in ("red-counts-as-author", "unaccepted-counts-as-author"):
        # Keep dispatch order. The faulty rule includes the RED / unaccepted
        # agent instead of taking only the durable accepted implementation set.
        changed["implementation_authors"] = [
            {"module": module, "agent": dispatch["agent"]} for dispatch in dispatches
        ]
    else:
        raise AssertionError(f"unknown mutant {mutant}")
    return attribute(changed, leg, module, reviewer)


@pytest.fixture(scope="module")
def hostile_module():
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("HMAD_STUB_")}
    env["HMAD_STUB_HOSTILE"] = "all"
    result = subprocess.run(
        ["bash", str(ROOT / "tests" / "stubs" / "orca"), "worktree", "set"],
        env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"hostile module fixture failed: {result.stderr}"
    module = json.loads(result.stdout)["result"]["worktree"]["comment"]
    assert all(token in module for token in ("\n", "\t", "[a](b)", "⟦/h-mad⟧", "*"))
    return module


CASES = (
    ("routing-is-not-authorship", "routing-as-authorship"),
    ("multi-author-recovered", "authors-from-review-projection"),
    ("pre-field-feature", "absent-means-independent"),
    ("red-is-not-authorship", "red-counts-as-author"),
    ("unaccepted-dispatches-author-nothing", "unaccepted-counts-as-author"),
)


@pytest.mark.parametrize("case,mutant", CASES, ids=[case for case, _ in CASES])
def test_attribution_transcription(case, mutant, hostile_module, tmp_path):
    module = hostile_module
    record = {"feature": "attribution", "last_completed_phase": 6,
              "archreview": "READY_TO_MERGE", "halt_reason": None,
              "implementation_authors": [
                  {"module": module, "agent": "codex"},
                  {"module": module + "-other", "agent": "agy"},
              ]}
    dispatches = []
    reviewer, leg = "agy", "5e-review"

    def expected(leg, reviewer, implementer, independent):
        return {"leg": leg, "module": module, "reviewer": reviewer,
                "implementer": implementer, "independent": independent}

    if case == "routing-is-not-authorship":
        record.update(implementer="agy", implementer_switch={
            "to": "agy", "reason": "codex-out", "ts": "2026-10-16T12:00:00Z"})
        reviewer = "codex"
        wanted = expected(leg, reviewer, "codex", False)
    elif case == "multi-author-recovered":
        record["implementation_authors"].insert(0, {"module": module, "agent": "agy"})
        record["review_independence"] = []
        for prior_leg, prior_reviewer, independent in (
            ("5e-review", "grok", True), ("5e-verify", "codex", False),
        ):
            entry = attribute(record, prior_leg, module, prior_reviewer)
            assert entry == expected(prior_leg, prior_reviewer, "codex", independent)
            record["review_independence"].append(entry)
        leg = "6a-prime"
        wanted = expected(leg, reviewer, "agy", False)
    elif case == "pre-field-feature":
        del record["implementation_authors"]
        for prior_leg, prior_reviewer in (("5e-review", "grok"), ("5e-verify", "codex")):
            assert attribute(record, prior_leg, module, prior_reviewer) is None
        leg, wanted = "6a-prime", None
    else:
        dispatches = [
            {"phase": "red" if case == "red-is-not-authorship" else "green",
             "agent": "agy", "accepted": case == "red-is-not-authorship"},
            {"phase": "green", "agent": "codex", "accepted": True},
        ]
        wanted = expected(leg, reviewer, "codex", True)

    # A JSON round trip is intentional: no in-context dispatch list survives
    # recovery. Only the durable record is supplied to the correct procedure.
    path = tmp_path / "record.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    durable = json.loads(path.read_text(encoding="utf-8"))
    before = json.dumps(durable, sort_keys=True)
    actual = attribute(durable, leg, module, reviewer)
    assert actual == wanted, f"{case}: FR-7 attribution selected the wrong entry"
    wrong = _mutant_attribute(durable, leg, module, reviewer, mutant, dispatches)
    assert wrong != wanted, f"{case}: fixture does not distinguish named mutant {mutant}"
    assert json.dumps(durable, sort_keys=True) == before, "attribution must only read the record"

    if case == "routing-is-not-authorship":
        analysis = tmp_path / "attribution.analysis.md"
        analysis.write_text(f"## Match Rate: 100%\n\n{module}\n", encoding="utf-8")
        result = p7.check(dict(durable, review_independence=[actual]), analysis)
        warnings = {entry["code"] for entry in result["warnings"]}
        assert "review_non_independent" in warnings, (
            "dispatch-based self-review must reach check's review_non_independent WARNING"
        )
        mutated = p7.check(dict(durable, review_independence=[wrong]), analysis)
        assert "review_non_independent" not in {entry["code"] for entry in mutated["warnings"]}

    if case == "pre-field-feature":
        # The three closed no-entry cases: absent, no entry for this module,
        # and any malformed field (even a bad entry for another module).
        for entries in ([], [{"module": module + "-other", "agent": "agy"}],
                        None, {}, "bad", [None],
                        [{"module": module, "agent": "unknown"}],
                        [{"module": module, "agent": "codex"},
                         {"module": module + "-other", "agent": "unknown"}]):
            assert attribute(dict(durable, implementation_authors=entries),
                             leg, module, reviewer) is None, (
                f"no-entry rule must reject an unestablished author set: {entries!r}"
            )


def test_transcription_is_tied_to_the_skill_text():
    closure = _closure()
    for sentence in (
        "The author set is read from `implementation_authors` only",
        "never read from `implementer_switch.to` or from the `implementer` field",
        'property_valid("implementation_authors", [entry])',
        "If the reviewer is in that module's author set",
        "`implementer` is the reviewer and `independent` is `false`",
        "Otherwise `implementer` is the agent of the module's latest entry",
        "When no author can be read, no entry is written",
        "the record has no `implementation_authors` field",
        "the field is present and holds no well-formed entry",
        "the field is present and is not a list, or holds an entry that is not well-formed",
        "5d RED", "halted, timed out or was rejected",
    ):
        _require(closure, sentence, f"FR-7 transcription must be tied to SKILL.md rule: {sentence}")
