"""Phase-5e mutation harness: disabling a guard must break a test.

`invariants.base.md` already requires this and already names its trap — "a
`.replace()` that matches nothing" exits 0 and reports the guard as enforced.
The doctrine was complete; the executable was not, so every run hand-rolled a
harness and independently re-derived the assert-landed guard the invariant
mandates in prose. Two were written in a single session before this script
existed.

What these tests pin is the part that is easy to get wrong and fatal when it
is: a mutation that never landed must REFUSE rather than report "caught", the
tree must come back byte-identical no matter how the run ends, and a red
baseline must stop the run instead of scoring every mutation against noise.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
HARNESS = SCRIPTS / "h_mad_mutation_harness.py"

sys.path.insert(0, str(SCRIPTS))
import h_mad_mutation_harness  # noqa: E402
from h_mad_mutation_harness import _restore_file, run_spec  # noqa: E402


GUARD = "THRESHOLD = 5\n# a comment that no test observes\n"

# Exits 0 only while the guard is intact — a stand-in for "the suite is green".
CHECK = (
    "import sys; sys.exit(0 if 'THRESHOLD = 5' in open('guard.py').read() else 1)"
)


def _project(tmp_path: Path, mutations: list[dict], check: str = CHECK) -> Path:
    """A tiny project plus a spec, written to `tmp_path`."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "guard.py").write_text(GUARD, encoding="utf-8")
    spec = {
        "root": str(tmp_path),
        "command": [sys.executable, "-c", check],
        "mutations": mutations,
    }
    spec_path = tmp_path / "mutations.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    return spec_path


def _kills_the_guard() -> dict:
    return {"name": "raise the threshold", "file": "guard.py",
            "find": "THRESHOLD = 5", "replace": "THRESHOLD = 9"}


def _untested_line() -> dict:
    return {"name": "edit an unobserved comment", "file": "guard.py",
            "find": "# a comment that no test observes",
            "replace": "# edited"}


def _run_cli(spec_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HARNESS), str(spec_path)],
        capture_output=True, text=True,
    )


# --- the verdicts ---------------------------------------------------------


def test_a_mutation_that_breaks_a_test_is_caught(tmp_path: Path) -> None:
    result = run_spec(_project(tmp_path, [_kills_the_guard()]))
    assert result["verdict"] == "ALL_CAUGHT", result
    assert result["caught"] == 1 and result["survived"] == []


def test_a_mutation_nothing_notices_is_reported_as_a_hole(tmp_path: Path) -> None:
    # The finding the harness exists to produce. Zero failures is not success —
    # it means the guard is unenforced and every gate downstream is blind to it.
    result = run_spec(_project(tmp_path, [_untested_line()]))
    assert result["verdict"] == "SURVIVED", result
    assert "edit an unobserved comment" in " ".join(result["survived"])


def test_survivors_are_reported_even_alongside_caught_mutations(tmp_path: Path) -> None:
    result = run_spec(_project(tmp_path, [_kills_the_guard(), _untested_line()]))
    assert result["verdict"] == "SURVIVED", result
    assert result["caught"] == 1
    assert len(result["survived"]) == 1


# --- the assert-landed guard ---------------------------------------------


def test_an_absent_anchor_is_refused(tmp_path: Path) -> None:
    # The trap `invariants.base.md` names by hand: a `.replace()` matching
    # nothing leaves the guard intact, the suite stays green, and the run
    # reports the guard as enforced. Refusing is the only honest answer.
    spec = _project(tmp_path, [
        {"name": "bad anchor", "file": "guard.py",
         "find": "THRESHOLD = 500", "replace": "X"},
    ])
    result = run_spec(spec)
    assert result["verdict"] == "REFUSED", result
    assert result["caught"] == 0, "an unlanded mutation must never count as caught"


def test_an_ambiguous_anchor_is_refused_not_guessed(tmp_path: Path) -> None:
    # Two matches means the harness cannot know which one the author meant.
    # Replacing both would mutate more than the guard under test and score the
    # wrong thing; replacing the first silently picks for them.
    (tmp_path / "guard.py").write_text("A = 1\nA = 1\n", encoding="utf-8")
    spec_path = tmp_path / "mutations.json"
    spec_path.write_text(json.dumps({
        "root": str(tmp_path),
        "command": [sys.executable, "-c", "import sys; sys.exit(0)"],
        "mutations": [{"name": "ambiguous", "file": "guard.py",
                       "find": "A = 1", "replace": "A = 2"}],
    }), encoding="utf-8")
    result = run_spec(spec_path)
    assert result["verdict"] == "REFUSED", result
    assert "2" in " ".join(result["refused"]), (
        f"the refusal must say how many times it matched: {result['refused']}"
    )


def test_a_refused_mutation_never_touches_the_file(tmp_path: Path) -> None:
    spec = _project(tmp_path, [
        {"name": "bad anchor", "file": "guard.py", "find": "NOPE", "replace": "X"},
    ])
    run_spec(spec)
    assert (tmp_path / "guard.py").read_text(encoding="utf-8") == GUARD


def test_refused_outranks_survived_in_the_verdict(tmp_path: Path) -> None:
    # A refusal is a cannot-judge, and cannot-judge must never be quieter than a
    # finding — same discipline as the wire-pin gate's UNSHAPED. Both counts
    # still appear on the summary line so neither hides the other.
    spec = _project(tmp_path, [
        _untested_line(),
        {"name": "bad anchor", "file": "guard.py", "find": "NOPE", "replace": "X"},
    ])
    result = run_spec(spec)
    assert result["verdict"] == "REFUSED", result
    assert len(result["survived"]) == 1, "the survivor must still be reported"


# --- restore ---------------------------------------------------------------


def test_the_tree_is_restored_byte_for_byte(tmp_path: Path) -> None:
    run_spec(_project(tmp_path, [_kills_the_guard(), _untested_line()]))
    assert (tmp_path / "guard.py").read_text(encoding="utf-8") == GUARD


def test_the_tree_is_restored_even_when_the_command_explodes(tmp_path: Path) -> None:
    # A harness that leaves a mutated tree behind after a crash is worse than no
    # harness: the next run scores against a corrupted baseline.
    spec = _project(tmp_path, [_kills_the_guard()],
                    check="import sys; raise SystemExit(3)")
    run_spec(spec)
    assert (tmp_path / "guard.py").read_text(encoding="utf-8") == GUARD


def test_restore_reports_success_on_a_normal_run(tmp_path: Path) -> None:
    result = run_spec(_project(tmp_path, [_kills_the_guard()]))
    assert result["restore_verified"] is True, result


def test_restore_detects_a_write_that_did_not_persist() -> None:
    # The discriminating half. The previous version of this test only asserted
    # `restore_verified is True` on a healthy run — which stays True when the
    # verification is deleted, so it was an assertion true by construction. The
    # harness caught that in its own suite when "stop verifying the restore
    # landed" SURVIVED.
    #
    # /dev/null accepts a write and reads back empty, so it is a write that
    # succeeds without persisting — exactly the case the re-read exists to catch,
    # and one no exception would reveal.
    assert _restore_file(Path("/dev/null"), "content that cannot persist") is False


def test_restore_confirms_bytes_that_do_persist(tmp_path: Path) -> None:
    target = tmp_path / "f.txt"
    assert _restore_file(target, "hello") is True
    assert target.read_text(encoding="utf-8") == "hello"


# --- the baseline ----------------------------------------------------------


def test_a_red_baseline_stops_the_run(tmp_path: Path) -> None:
    # Scoring mutations against an already-failing suite is meaningless: every
    # mutation "fails" and the report reads as a clean sweep.
    spec = _project(tmp_path, [_kills_the_guard()],
                    check="import sys; sys.exit(1)")
    result = run_spec(spec)
    assert result["verdict"] == "BASELINE_NOT_GREEN", result
    assert result["caught"] == 0 and not result["survived"]


def test_the_baseline_is_rechecked_after_the_run(tmp_path: Path) -> None:
    result = run_spec(_project(tmp_path, [_kills_the_guard()]))
    assert result["baseline_green_after"] is True, (
        "a run that leaves the suite red has corrupted the tree it was measuring"
    )


# --- CLI contract ----------------------------------------------------------


def test_cli_prints_the_token_and_exits_zero_on_a_verdict(tmp_path: Path) -> None:
    proc = _run_cli(_project(tmp_path, [_kills_the_guard()]))
    assert proc.returncode == 0, proc.stderr
    assert "MUTATION: ALL_CAUGHT" in proc.stdout, proc.stdout
    assert "mutations=1" in proc.stdout and "caught=1" in proc.stdout, proc.stdout


def test_cli_survived_is_a_verdict_and_still_exits_zero(tmp_path: Path) -> None:
    # Signal discipline: exit 0 carries a verdict, non-zero is an operational
    # error, so a caller reads the token and never `$?`.
    proc = _run_cli(_project(tmp_path, [_untested_line()]))
    assert proc.returncode == 0, proc.stderr
    assert "MUTATION: SURVIVED" in proc.stdout, proc.stdout
    assert "survived=1" in proc.stdout, proc.stdout


def test_cli_cannot_judge_exits_two(tmp_path: Path) -> None:
    proc = _run_cli(_project(tmp_path, [
        {"name": "bad anchor", "file": "guard.py", "find": "NOPE", "replace": "X"},
    ]))
    assert "MUTATION: REFUSED" in proc.stdout, proc.stdout
    assert proc.returncode == 2, "cannot-judge must not exit 0 alongside real verdicts"


def test_cli_names_each_survivor_so_the_report_is_actionable(tmp_path: Path) -> None:
    proc = _run_cli(_project(tmp_path, [_untested_line()]))
    assert "survived: edit an unobserved comment" in proc.stdout, proc.stdout


def test_cli_emits_the_hmad_marker(tmp_path: Path) -> None:
    proc = _run_cli(_project(tmp_path, [_kills_the_guard()]))
    assert "[H-MAD]" in proc.stdout and "mutation" in proc.stdout, proc.stdout


def test_cli_unreadable_spec_is_an_operational_error(tmp_path: Path) -> None:
    proc = _run_cli(tmp_path / "nope.json")
    assert proc.returncode == 2
    assert "MUTATION: UNREADABLE" in proc.stdout, proc.stdout


def test_harness_is_stdlib_only() -> None:
    source = HARNESS.read_text(encoding="utf-8")
    for banned in ("import yaml", "import requests", "from pydantic", "import jsonschema"):
        assert banned not in source, f"{banned} would break the bare-python3 callers"


# --- per-mutation targets, mechanism attribution, anchor hints -------------
#
# `ALL_CAUGHT` answers "did something go red?", which is not the question 5e
# asks. A mutant can die on a crash, a timeout, or an assertion about something
# else entirely, and each of those is byte-identical to the guard biting. These
# pin the discrimination: when a mutation names the test it is aimed at, only
# that test counts as a kill, and whatever actually bit is reported by name.

REAL_GUARD = "def over(n):\n    return n > 5\n\n\ndef unrelated():\n    return 'stable'\n"

REAL_TESTS = '''
from guard import over, unrelated


def test_the_property_under_test():
    assert over(6) and not over(5)


def test_something_else_entirely():
    assert unrelated() == 'stable'
'''


def _pytest_project(tmp_path: Path, mutations: list[dict], *, targeted: bool = True) -> Path:
    """A real pytest project, so failures carry parseable node ids."""
    (tmp_path / "guard.py").write_text(REAL_GUARD, encoding="utf-8")
    (tmp_path / "test_guard.py").write_text(REAL_TESTS, encoding="utf-8")
    spec = {
        "root": str(tmp_path),
        "command": [sys.executable, "-m", "pytest", "-q", "test_guard.py"],
        "mutations": mutations,
    }
    if targeted:
        spec["target_command"] = [sys.executable, "-m", "pytest", "-q"]
    spec_path = tmp_path / "mutations.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    return spec_path


PIN = "test_guard.py::test_the_property_under_test"
OTHER = "test_guard.py::test_something_else_entirely"


def test_a_mutant_killed_by_its_named_test_is_caught(tmp_path: Path) -> None:
    spec = _pytest_project(tmp_path, [
        {"name": "loosen the bound", "file": "guard.py",
         "find": "return n > 5", "replace": "return n >= 5", "test": PIN},
    ])
    result = run_spec(spec)
    assert result["verdict"] == "ALL_CAUGHT"
    assert result["caught"] == 1
    assert "named test" in result["mechanism"]["loosen the bound"]


def test_a_mutant_caught_by_the_wrong_test_is_a_survivor(tmp_path: Path) -> None:
    """The finding `ALL_CAUGHT` structurally cannot express.

    This mutation breaks `unrelated()`, so the suite goes red and an exit-code
    harness scores a kill. But the test it claims to pin never notices, which
    means the property is unenforced — the same shape as the real `pids[$i]:
    unbound variable` and 60-second-timeout kills that passed `ALL_CAUGHT`.
    """
    spec = _pytest_project(tmp_path, [
        {"name": "break something else", "file": "guard.py",
         "find": "return 'stable'", "replace": "return 'moved'", "test": PIN},
    ])
    result = run_spec(spec)

    assert result["verdict"] == "SURVIVED"
    assert result["survived"] == ["break something else"]
    mechanism = result["mechanism"]["break something else"]
    assert "PASSED but the suite went red elsewhere" in mechanism
    assert OTHER in mechanism


def test_a_mutant_nothing_notices_says_so(tmp_path: Path) -> None:
    spec = _pytest_project(tmp_path, [
        {"name": "edit a docstring", "file": "guard.py",
         "find": "def unrelated():", "replace": "def unrelated():  # noted", "test": PIN},
    ])
    result = run_spec(spec)
    assert result["verdict"] == "SURVIVED"
    assert "nothing bites" in result["mechanism"]["edit a docstring"]


def test_an_untargeted_mutation_still_names_its_killer(tmp_path: Path) -> None:
    spec = _pytest_project(tmp_path, [
        {"name": "loosen the bound", "file": "guard.py",
         "find": "return n > 5", "replace": "return n >= 5"},
    ], targeted=False)
    result = run_spec(spec)
    assert result["verdict"] == "ALL_CAUGHT"
    assert PIN in result["mechanism"]["loosen the bound"]


def test_a_named_test_already_red_is_refused_not_scored(tmp_path: Path) -> None:
    """L559: a kill credited against a pin that was failing anyway measures nothing.

    The pin here is a test that RUNS and asserts a falsehood. An earlier version
    named a test that does not exist, which pytest reports as a collection
    error — so it exercised the "did not run" branch while claiming to test the
    "already failing" one, and passed on a runner crash rather than a red test.
    """
    spec = _pytest_project(tmp_path, [
        {"name": "loosen the bound", "file": "guard.py",
         "find": "return n > 5", "replace": "return n >= 5",
         "test": "test_extra.py::test_already_red"},
    ])
    # In its OWN file, outside the suite `command` runs. That is the whole
    # point: the suite is green, and the single named pin is red — the case the
    # whole-suite baseline structurally cannot see.
    (tmp_path / "test_extra.py").write_text(
        "def test_already_red():\n    assert False\n", encoding="utf-8")
    result = run_spec(spec)

    assert result["verdict"] == "REFUSED"
    assert result["caught"] == 0
    assert "was already failing" in result["refused"][0]


def test_a_named_test_that_does_not_exist_is_refused_as_did_not_run(
    tmp_path: Path
) -> None:
    """A missing nodeid is a broken spec, not a red test. Different fix."""
    spec = _pytest_project(tmp_path, [
        {"name": "loosen the bound", "file": "guard.py",
         "find": "return n > 5", "replace": "return n >= 5",
         "test": "test_guard.py::test_that_does_not_exist"},
    ])
    result = run_spec(spec)

    assert result["verdict"] == "REFUSED"
    assert "did not run" in result["refused"][0]


def test_a_skipped_named_test_is_refused_not_treated_as_green(
    tmp_path: Path
) -> None:
    """`@pytest.mark.skip` exits 0, so an exit-code pre-check calls it GREEN.

    The mutant then survives and reads as a missing guard, when the truth is
    the test was turned off. Measured 2026-08-25: a skipped test exits 0.
    """
    spec = _pytest_project(tmp_path, [
        {"name": "loosen the bound", "file": "guard.py",
         "find": "return n > 5", "replace": "return n >= 5",
         "test": "test_guard.py::test_the_property_under_test"},
    ])
    (tmp_path / "test_guard.py").write_text(
        "import pytest\nfrom guard import over\n\n\n"
        "@pytest.mark.skip(reason='turned off')\n"
        "def test_the_property_under_test():\n    assert over(6) and not over(5)\n",
        encoding="utf-8")
    result = run_spec(spec)

    assert result["verdict"] == "REFUSED"
    assert "was skipped" in result["refused"][0]


def test_a_mutant_that_breaks_collection_is_refused_not_credited_as_a_kill(
    tmp_path: Path
) -> None:
    """A syntax error exits 2 before the assertion ever runs.

    Measured 2026-08-25: pytest exits 2 on a collection error, and the harness
    credited that as `killed by its named test`. It proves the code breaks when
    broken and nothing about the property — the same wrong-mechanism family the
    named-test scoring exists to catch, arriving through the runner instead of
    through another assertion.
    """
    spec = _pytest_project(tmp_path, [
        {"name": "syntax error", "file": "guard.py",
         "find": "def over(n):", "replace": "def over(n:",
         "test": "test_guard.py::test_the_property_under_test"},
    ])
    result = run_spec(spec)

    assert result["verdict"] == "REFUSED", result
    assert result["caught"] == 0
    assert "broke collection" in result["refused"][0]


def test_a_test_field_without_a_target_command_is_a_spec_error(tmp_path: Path) -> None:
    spec = _pytest_project(tmp_path, [
        {"name": "loosen the bound", "file": "guard.py",
         "find": "return n > 5", "replace": "return n >= 5", "test": PIN},
    ], targeted=False)
    proc = _run_cli(spec)
    assert proc.returncode == 2
    assert "MUTATION: UNREADABLE" in proc.stdout
    assert "no `target_command`" in proc.stderr


def test_a_non_string_test_field_is_a_spec_error(tmp_path: Path) -> None:
    spec = _pytest_project(tmp_path, [
        {"name": "loosen the bound", "file": "guard.py",
         "find": "return n > 5", "replace": "return n >= 5", "test": 3},
    ])
    proc = _run_cli(spec)
    assert proc.returncode == 2
    assert "non-string `test`" in proc.stderr


# --- anchor hints ---------------------------------------------------------


def test_a_drifted_anchor_gets_a_near_miss_with_a_line_number(tmp_path: Path) -> None:
    """The REFUSED verdict was already right; the recovery was a manual re-grep."""
    spec = _project(tmp_path, [
        {"name": "drifted", "file": "guard.py",
         "find": "THRESHOLD = 7", "replace": "THRESHOLD = 9"},
    ])
    result = run_spec(spec)

    assert result["verdict"] == "REFUSED"
    hints = result["hints"]["drifted"]
    assert any("line 1:" in h and "THRESHOLD = 5" in h for h in hints), hints


def test_an_anchor_with_no_near_miss_says_so_rather_than_guessing(tmp_path: Path) -> None:
    spec = _project(tmp_path, [
        {"name": "gone", "file": "guard.py",
         "find": "completely unrelated content here", "replace": ""},
    ])
    result = run_spec(spec)
    assert "no near miss found" in result["hints"]["gone"][0]


def test_an_ambiguous_anchor_is_told_where_its_matches_are(tmp_path: Path) -> None:
    (tmp_path / "guard.py").write_text("x = 1\nx = 1\n", encoding="utf-8")
    spec_path = tmp_path / "mutations.json"
    spec_path.write_text(json.dumps({
        "root": str(tmp_path),
        "command": [sys.executable, "-c", "import sys; sys.exit(0)"],
        "mutations": [{"name": "twice", "file": "guard.py", "find": "x = 1", "replace": "x = 2"}],
    }), encoding="utf-8")
    result = run_spec(spec_path)

    assert result["verdict"] == "REFUSED"
    assert "1, 2" in result["hints"]["twice"][0]


def test_the_cli_prints_hints_under_the_refusal(tmp_path: Path) -> None:
    spec = _project(tmp_path, [
        {"name": "drifted", "file": "guard.py",
         "find": "THRESHOLD = 7", "replace": "THRESHOLD = 9"},
    ])
    proc = _run_cli(spec)
    assert "  refused: drifted:" in proc.stdout
    assert "    hint: near miss line 1:" in proc.stdout


def test_the_summary_line_is_unchanged_by_the_new_detail(tmp_path: Path) -> None:
    """Existing callers parse this line; the additions are detail lines only."""
    spec = _project(tmp_path, [_kills_the_guard()])
    proc = _run_cli(spec)
    assert "MUTATION: ALL_CAUGHT mutations=1 caught=1 survived=0 refused=0" in proc.stdout


def test_a_multiline_anchor_still_gets_a_near_miss(tmp_path: Path) -> None:
    """`find` is usually a block; comparing the whole block to single lines finds nothing.

    Only the anchor's FIRST line is comparable to a source line, so a hint
    implementation that matches the whole block degrades to "no near miss" on
    every real multi-line mutation while still looking implemented.
    """
    (tmp_path / "guard.py").write_text(
        "def check(n):\n    return n > 5\n", encoding="utf-8")
    spec_path = tmp_path / "mutations.json"
    spec_path.write_text(json.dumps({
        "root": str(tmp_path),
        "command": [sys.executable, "-c", "import sys; sys.exit(0)"],
        "mutations": [{
            "name": "block drifted", "file": "guard.py",
            "find": "def check(n):\n    return n > 7\n    # trailing", "replace": ""}],
    }), encoding="utf-8")
    result = run_spec(spec_path)

    assert result["verdict"] == "REFUSED"
    hints = result["hints"]["block drifted"]
    assert any("def check(n):" in h for h in hints), hints


def test_identical_lines_are_reported_at_both_locations(tmp_path: Path) -> None:
    """Two matching lines are exactly the case an author needs both numbers for."""
    (tmp_path / "guard.py").write_text(
        "value = compute(a)\nfiller = 0\nvalue = compute(a)\n", encoding="utf-8")
    spec_path = tmp_path / "mutations.json"
    spec_path.write_text(json.dumps({
        "root": str(tmp_path),
        "command": [sys.executable, "-c", "import sys; sys.exit(0)"],
        "mutations": [{"name": "drifted", "file": "guard.py",
                       "find": "value = compute(b)", "replace": ""}],
    }), encoding="utf-8")
    result = run_spec(spec_path)

    hints = result["hints"]["drifted"]
    assert any("line 1:" in h for h in hints), hints
    assert any("line 3:" in h for h in hints), hints


def test_a_command_that_cannot_launch_is_red_not_green(tmp_path: Path) -> None:
    """"I could not measure" must never resolve to "the guard is fine".

    A launch failure that read as green would clear the baseline check and then
    score every mutation as a survivor, reporting a full set of holes that were
    never actually tested.
    """
    (tmp_path / "guard.py").write_text(GUARD, encoding="utf-8")
    spec_path = tmp_path / "mutations.json"
    spec_path.write_text(json.dumps({
        "root": str(tmp_path),
        "command": [str(tmp_path / "no-such-binary")],
        "mutations": [_kills_the_guard()],
    }), encoding="utf-8")
    result = run_spec(spec_path)

    assert result["verdict"] == "BASELINE_NOT_GREEN"


def test_a_same_size_mutation_is_not_masked_by_stale_bytecode(tmp_path: Path) -> None:
    """CPython invalidates a `.pyc` on (source mtime, source size).

    A mutation is frequently byte-size-IDENTICAL and lands inside the same
    filesystem-mtime second as the previous run, so both invalidation inputs
    match and the stale bytecode is reused. The mutant never executes, the file
    on disk is genuinely mutated so the did-it-land check passes, and the run
    reports `survived` — byte-identical to a real coverage gap.

    Measured before the fix: 4 false survivors in 6 trials on a 68-byte-for-
    68-byte swap. This drives the same shape through an importable module.
    """
    (tmp_path / "guard.py").write_text("LIMIT = 5\n", encoding="utf-8")
    (tmp_path / "test_guard.py").write_text(
        "import guard\n\n\ndef test_limit():\n    assert guard.LIMIT == 5\n",
        encoding="utf-8")
    spec_path = tmp_path / "mutations.json"
    spec_path.write_text(json.dumps({
        "root": str(tmp_path),
        "command": [sys.executable, "-m", "pytest", "-q", "test_guard.py"],
        "target_command": [sys.executable, "-m", "pytest", "-q"],
        # Same length on both sides: "LIMIT = 5" -> "LIMIT = 9".
        "mutations": [{"name": "same size", "file": "guard.py",
                       "find": "LIMIT = 5", "replace": "LIMIT = 9",
                       "test": "test_guard.py::test_limit"}],
    }), encoding="utf-8")

    # Warm the bytecode cache first, which is what the precheck run does.
    subprocess.run([sys.executable, "-m", "pytest", "-q", "test_guard.py"],
                   cwd=str(tmp_path), capture_output=True)
    result = run_spec(spec_path)

    assert result["verdict"] == "ALL_CAUGHT", result
    assert result["caught"] == 1


def test_purging_bytecode_leaves_the_sources_alone(tmp_path: Path) -> None:
    """It removes cached `.pyc`, never a source file — the tree must survive."""
    from h_mad_mutation_harness import _purge_bytecode

    (tmp_path / "keep.py").write_text("x = 1\n", encoding="utf-8")
    cache = tmp_path / "pkg" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "keep.cpython-311.pyc").write_bytes(b"stale")
    (cache / "notes.txt").write_text("not bytecode", encoding="utf-8")

    _purge_bytecode(tmp_path)

    assert (tmp_path / "keep.py").exists()
    assert not (cache / "keep.cpython-311.pyc").exists()
    assert (cache / "notes.txt").exists()


def test_every_run_purges_bytecode_before_launching(tmp_path: Path) -> None:
    """`_run` must call the purge, asserted directly rather than via a race.

    The end-to-end version of this — drive a same-size mutation through a nested
    `run_spec` and expect ALL_CAUGHT — depends on whether two writes land in the
    same filesystem-mtime second, so it can pass by luck. Worse, the mutation
    that removes the purge also removes it from the NESTED harness the test
    drives, so the test's own mechanism moves under it. This pins the property
    itself: a stale `.pyc` present before the run is gone by the time the
    command launches.
    """
    from h_mad_mutation_harness import _run

    cache = tmp_path / "__pycache__"
    cache.mkdir()
    stale = cache / "anything.cpython-311.pyc"
    stale.write_bytes(b"stale")

    _run([sys.executable, "-c", "pass"], tmp_path)

    assert not stale.exists(), "_run launched without purging cached bytecode"


# --- anchor precheck: sweep every spec without applying anything -----------
#
# Measured 2026-08-26: 5 of 177 anchors across 14 committed specs no longer
# matched, so those mutations REFUSE and the guards they aim at are unverified
# — and nothing reported that until someone ran each spec, which costs a full
# suite per spec. The precheck is the cheap version: read-only, no test run.


def _drifted_anchor() -> dict:
    return {"name": "anchor that no longer matches", "file": "guard.py",
            "find": "THRESHOLD = 500", "replace": "THRESHOLD = 900"}


def test_precheck_says_ok_when_every_anchor_still_matches_once(tmp_path: Path) -> None:
    from h_mad_mutation_harness import precheck_spec

    result = precheck_spec(_project(tmp_path, [_kills_the_guard(), _untested_line()]))

    assert result["verdict"] == "ANCHORS_OK", result
    assert result["ok"] == 2
    assert result["drifted"] == []


def test_precheck_flags_a_drifted_anchor_with_its_hit_count(tmp_path: Path) -> None:
    from h_mad_mutation_harness import precheck_spec

    result = precheck_spec(_project(tmp_path, [_kills_the_guard(), _drifted_anchor()]))

    assert result["verdict"] == "ANCHORS_DRIFTED", result
    assert result["ok"] == 1
    assert [d["name"] for d in result["drifted"]] == ["anchor that no longer matches"]
    assert result["drifted"][0]["hits"] == 0
    assert result["drifted"][0]["hints"], "a drifted anchor must carry its recovery hint"


def test_precheck_flags_an_anchor_that_matches_more_than_once(tmp_path: Path) -> None:
    """Ambiguous is a defect too: the run would have to choose for the author."""
    from h_mad_mutation_harness import precheck_spec

    (tmp_path / "dup.py").write_text("x = 1\nx = 1\n", encoding="utf-8")
    spec_path = _project(tmp_path, [{"name": "ambiguous", "file": "dup.py",
                                     "find": "x = 1", "replace": "x = 2"}])

    result = precheck_spec(spec_path)

    assert result["verdict"] == "ANCHORS_DRIFTED", result
    assert result["drifted"][0]["hits"] == 2


def test_precheck_applies_nothing_and_runs_nothing(tmp_path: Path) -> None:
    """The whole point of the cheap check: read-only, and no command launched.

    A precheck that quietly ran the suite would cost exactly what it exists to
    avoid, and one that applied a mutation could leave a tree behind — the
    failure the harness's own restore machinery exists to prevent.
    """
    from h_mad_mutation_harness import precheck_spec

    sentinel = tmp_path / "command-ran"
    spec_path = _project(
        tmp_path,
        [_kills_the_guard(), _drifted_anchor()],
        check=f"open({str(sentinel)!r}, 'w').close()",
    )
    before = (tmp_path / "guard.py").read_bytes()

    precheck_spec(spec_path)

    assert (tmp_path / "guard.py").read_bytes() == before, "precheck mutated the tree"
    assert not sentinel.exists(), "precheck launched the spec's command"


def test_precheck_and_the_run_refuse_the_same_anchors(tmp_path: Path) -> None:
    """Anti-drift: both verdicts come from one rule, not two copies of it.

    A precheck with its own `count(...) != 1` would be a second implementation
    of the exact rule this harness exists to enforce, and the first edit to
    either side would make the cheap check disagree with the expensive one —
    the cheap one being the one people would trust.
    """
    from h_mad_mutation_harness import precheck_spec

    spec_path = _project(tmp_path, [_kills_the_guard(), _drifted_anchor()])

    pre = {d["name"] for d in precheck_spec(spec_path)["drifted"]}
    run = {entry.split(":", 1)[0] for entry in run_spec(spec_path)["refused"]}

    assert pre == run, f"precheck {pre} disagrees with the run {run}"


def test_precheck_reports_an_unreadable_target_rather_than_calling_it_ok(
    tmp_path: Path,
) -> None:
    from h_mad_mutation_harness import precheck_spec

    result = precheck_spec(_project(tmp_path, [
        {"name": "gone", "file": "deleted.py", "find": "anything", "replace": "x"},
    ]))

    assert result["verdict"] == "ANCHORS_DRIFTED", result
    assert result["ok"] == 0
    assert result["unreadable"], "a missing target file must not pass silently"


# --- root resolution ------------------------------------------------------
#
# Specs can live next to their mutation fixtures, and `root` exists to make the
# target paths independent of where the harness itself is launched from.


def _root_resolution_spec(spec_dir: Path, root: str | None) -> Path:
    project = spec_dir.parent
    project.mkdir(parents=True, exist_ok=True)
    spec_dir.mkdir(parents=True, exist_ok=True)
    (project / "guard.py").write_text(GUARD, encoding="utf-8")
    spec = {
        "command": [sys.executable, "-c", CHECK],
        "mutations": [_kills_the_guard()],
    }
    if root is not None:
        spec["root"] = root
    spec_path = spec_dir / "mutations.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    return spec_path


def _from_cwd(cwd: Path, spec_path: Path, guard: Path) -> tuple[str, str, bool]:
    from h_mad_mutation_harness import precheck_spec

    previous = Path.cwd()
    try:
        os.chdir(cwd)
        try:
            pre = precheck_spec(spec_path)
            run = run_spec(spec_path)
        except OSError as exc:
            return f"OSError: {exc}", f"OSError: {exc}", guard.read_text(
                encoding="utf-8"
            ) == GUARD
    finally:
        os.chdir(previous)
    return pre["verdict"], run["verdict"], guard.read_text(encoding="utf-8") == GUARD


def test_relative_root_is_resolved_against_the_spec_dir_from_any_cwd(tmp_path: Path) -> None:
    spec_path = _root_resolution_spec(tmp_path / "project" / "specs", "..")
    guard = spec_path.parent.parent / "guard.py"
    repo_root = Path(__file__).resolve().parents[2]
    observed = {
        "spec dir": _from_cwd(spec_path.parent, spec_path, guard),
        "/tmp": _from_cwd(Path("/tmp"), spec_path, guard),
        "repo root": _from_cwd(repo_root, spec_path, guard),
    }

    assert len(set(observed.values())) == 1, (
        "relative root must be spec-relative, not caller-cwd-relative: "
        f"{observed}"
    )
    assert observed["spec dir"] == ("ANCHORS_OK", "ALL_CAUGHT", True)


def test_absolute_root_is_used_exactly_from_any_cwd(tmp_path: Path) -> None:
    project = tmp_path / "project"
    spec_path = _root_resolution_spec(project / "specs", str(project))
    guard = project / "guard.py"
    observed = [
        _from_cwd(spec_path.parent, spec_path, guard),
        _from_cwd(Path("/tmp"), spec_path, guard),
        _from_cwd(Path(__file__).resolve().parents[2], spec_path, guard),
    ]

    assert observed == [("ANCHORS_OK", "ALL_CAUGHT", True)] * 3


def test_absent_root_defaults_to_the_spec_file_directory(tmp_path: Path) -> None:
    spec_dir = tmp_path / "specs-as-project"
    spec_dir.mkdir()
    (spec_dir / "guard.py").write_text(GUARD, encoding="utf-8")
    spec = {
        "command": [sys.executable, "-c", CHECK],
        "mutations": [_kills_the_guard()],
    }
    spec_path = spec_dir / "mutations.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")

    assert _from_cwd(Path("/tmp"), spec_path, spec_dir / "guard.py") == (
        "ANCHORS_OK", "ALL_CAUGHT", True
    )
    assert (spec_dir / "guard.py").read_text(encoding="utf-8") == GUARD


def test_precheck_and_run_share_the_root_resolver(monkeypatch, tmp_path: Path) -> None:
    source = HARNESS.read_text(encoding="utf-8")

    assert "def _resolve_root(spec: dict, spec_path: Path) -> Path:" in source, (
        "root resolution must live in the shared _resolve_root helper"
    )

    calls = []
    shared_root = tmp_path / "shared-root"

    def record_resolved_root(spec: dict, spec_path: Path) -> Path:
        root = shared_root.resolve()
        calls.append((spec_path, root))
        return root

    monkeypatch.setattr(h_mad_mutation_harness, "_resolve_root", record_resolved_root)
    spec_path = _project(shared_root, [_kills_the_guard()])

    h_mad_mutation_harness.precheck_spec(spec_path)
    assert len(calls) == 1, "precheck_spec must resolve the root exactly once, via the helper"
    h_mad_mutation_harness.run_spec(spec_path)
    assert len(calls) == 2, "run_spec must resolve the root through the same helper"

    assert calls == [(spec_path, shared_root.resolve())] * 2, (
        "precheck_spec and run_spec must resolve the same spec through the same "
        f"root helper: {calls}"
    )
    assert "Path(spec.get(\"root\") or spec_path.parent).resolve()" not in source, (
        "the previous cwd-relative root-resolution expression must be removed"
    )


def test_check_anchors_cli_sweeps_several_specs_and_exits_2_on_drift(
    tmp_path: Path,
) -> None:
    clean = _project(tmp_path / "a", [_kills_the_guard()])
    dirty = _project(tmp_path / "b", [_drifted_anchor()])

    proc = subprocess.run(
        [sys.executable, str(HARNESS), "--check-anchors", str(clean), str(dirty)],
        capture_output=True, text=True,
    )

    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "ANCHORS_DRIFTED" in proc.stdout, proc.stdout
    assert "anchor that no longer matches" in proc.stdout, proc.stdout
    assert "[H-MAD]" in proc.stdout, proc.stdout


def test_check_anchors_cli_exits_0_when_every_spec_is_clean(tmp_path: Path) -> None:
    a = _project(tmp_path / "a", [_kills_the_guard()])
    b = _project(tmp_path / "b", [_untested_line()])

    proc = subprocess.run(
        [sys.executable, str(HARNESS), "--check-anchors", str(a), str(b)],
        capture_output=True, text=True,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "ANCHORS_OK" in proc.stdout, proc.stdout


def test_a_bad_spec_in_the_sweep_does_not_abort_the_others(tmp_path: Path) -> None:
    """One unreadable spec must not hide the drift in the specs after it."""
    missing = tmp_path / "nope.json"
    dirty = _project(tmp_path / "b", [_drifted_anchor()])

    proc = subprocess.run(
        [sys.executable, str(HARNESS), "--check-anchors", str(missing), str(dirty)],
        capture_output=True, text=True,
    )

    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "anchor that no longer matches" in proc.stdout, proc.stdout


# --- spec classifier ------------------------------------------------------
#
# A spec-directory glob must not treat every JSON file as a mutation spec, and
# it must not silently drop corrupt JSON. The classifier keys on the one shape
# `_load_spec` already needs before any deeper validation: non-empty mutations.


def _write_json(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _classify_for_red(path: Path) -> tuple[str, str | None]:
    classifier = getattr(
        h_mad_mutation_harness,
        "classify_spec_file",
        lambda _path: ("missing-classifier", "classify_spec_file is not implemented"),
    )
    return classifier(path)


HOSTILE_NON_SPEC_NOTE = "HMAD_STUB_HOSTILE=markers\n===HMAD-DISPATCH-BOUNDARY===\n`$()[]{}"


def test_classifier_agrees_with_load_spec_on_the_mutations_gate(tmp_path: Path) -> None:
    """AC-6.1: `spec` means non-empty mutations; `not-a-spec` means loader rejects that gate."""
    cases = [
        _write_json(tmp_path / "valid.json", {
            "command": [sys.executable, "-c", "pass"],
            "mutations": [_kills_the_guard()],
        }),
        _write_json(tmp_path / "empty-mutations.json", {
            "command": [sys.executable, "-c", "pass"],
            "mutations": [],
        }),
        _write_json(tmp_path / "non-spec.json", {"name": HOSTILE_NON_SPEC_NOTE}),
    ]

    disagreements = []
    for spec_path in cases:
        kind, detail = _classify_for_red(spec_path)
        try:
            loaded = h_mad_mutation_harness._load_spec(spec_path)
            loader_has_mutations = bool(loaded["mutations"])
        except h_mad_mutation_harness.SpecError:
            loader_has_mutations = False

        expected = "spec" if loader_has_mutations else "not-a-spec"
        if kind != expected:
            disagreements.append(
                f"{spec_path.name}: classifier={kind!r} detail={detail!r}, "
                f"loader_mutations_gate={loader_has_mutations}"
            )

    assert not disagreements, (
        "classifier must agree with _load_spec's non-empty mutations gate:\n"
        + "\n".join(disagreements)
    )


def test_unparseable_json_is_named_and_not_counted_as_anchor_drift(tmp_path: Path) -> None:
    """AC-6.2: corrupt JSON is unclassifiable, reported by name, and not drift."""
    clean = _project(tmp_path / "clean", [_kills_the_guard()])
    malformed = tmp_path / "broken.json"
    malformed.write_text("{not-json", encoding="utf-8")

    kind, detail = _classify_for_red(malformed)
    assert kind == "unclassifiable", (
        f"malformed JSON must classify unclassifiable, got {kind!r} detail={detail!r}"
    )

    proc = subprocess.run(
        [sys.executable, str(HARNESS), "--check-anchors", str(clean), str(malformed)],
        capture_output=True, text=True,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "broken.json" in proc.stdout, "unclassifiable JSON must be named on success"
    assert "unclassifiable=1" in proc.stdout, proc.stdout
    assert "drifted=0" in proc.stdout, (
        "unclassifiable JSON must not contribute to anchor drift count:\n"
        + proc.stdout
    )


def test_spec_classification_does_not_skip_a_spec_that_fails_deeper_validation(
    tmp_path: Path,
) -> None:
    """AC-6.3: non-empty mutations make this a spec; deeper SpecError is a finding."""
    bad_spec = _write_json(tmp_path / "missing-command.json", {
        "mutations": [{"name": "has no command"}],
    })

    kind, detail = _classify_for_red(bad_spec)
    assert kind == "spec", (
        "a file with non-empty mutations must classify spec before deeper "
        f"validation, got {kind!r} detail={detail!r}"
    )

    proc = subprocess.run(
        [sys.executable, str(HARNESS), "--check-anchors", str(bad_spec)],
        capture_output=True, text=True,
    )

    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "missing-command.json" in proc.stdout, proc.stdout
    assert "not-a-spec" not in proc.stdout.lower(), (
        "a classified spec that raises SpecError must be a finding, not a skip:\n"
        + proc.stdout
    )


def test_anchor_sweep_names_skipped_and_unclassifiable_files_on_success(
    tmp_path: Path,
) -> None:
    """AC-6.4: skipped and unclassifiable files are listed even for ANCHORS_OK."""
    clean = _project(tmp_path / "clean", [_kills_the_guard()])
    notes = _write_json(tmp_path / "notes.json", {"title": HOSTILE_NON_SPEC_NOTE})
    broken = tmp_path / "empty.json"
    broken.write_text("", encoding="utf-8")

    assert _classify_for_red(notes)[0] == "not-a-spec", (
        "valid JSON without non-empty mutations must classify not-a-spec"
    )
    assert _classify_for_red(broken)[0] == "unclassifiable", (
        "empty JSON file must classify unclassifiable"
    )

    proc = subprocess.run(
        [sys.executable, str(HARNESS), "--check-anchors", str(clean), str(notes), str(broken)],
        capture_output=True, text=True,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "ANCHORS_OK" in proc.stdout, proc.stdout
    assert "notes.json" in proc.stdout and "empty.json" in proc.stdout, (
        "successful sweeps must name skipped and unclassifiable files:\n"
        + proc.stdout
    )
    assert "skipped=1" in proc.stdout and "unclassifiable=1" in proc.stdout, proc.stdout


def test_every_committed_mutation_spec_classifies_as_spec() -> None:
    """AC-6.5: the committed mutation-spec corpus is non-vacuous and all are specs."""
    offenders = []
    for spec_path in _committed_mutation_specs():
        kind, detail = _classify_for_red(spec_path)
        if kind != "spec":
            offenders.append(f"{spec_path}: classifier={kind!r} detail={detail!r}")

    assert not offenders, (
        "every committed tests/mutation-specs/*.json file must classify as spec:\n"
        + "\n".join(offenders)
    )


def test_a_mutation_run_still_takes_exactly_one_spec(tmp_path: Path) -> None:
    """`--check-anchors` widened the positional; the run must not widen with it."""
    a = _project(tmp_path / "a", [_kills_the_guard()])
    b = _project(tmp_path / "b", [_kills_the_guard()])

    proc = subprocess.run(
        [sys.executable, str(HARNESS), str(a), str(b)],
        capture_output=True, text=True,
    )

    assert proc.returncode != 0
    assert "exactly one spec" in (proc.stdout + proc.stderr)


def test_skill_documents_the_anchor_sweep() -> None:
    """A tool nobody is told to run is a tool nobody runs.

    The precheck's whole value is that it is cheap enough to run after every
    edit; that only happens if Phase 5e says so, and says what the token means.
    """
    skill = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")
    assert "--check-anchors" in skill, "Phase 5e never tells anyone to sweep anchors"
    assert "ANCHORS_DRIFTED" in skill, "the drifted token is undocumented"
    assert "a refusal measures NOTHING" in skill, (
        "the sweep is only actionable if the doc says why a REFUSED run is not a pass"
    )


# --- committed mutation specs are portable -------------------------------


def _committed_mutation_specs() -> list[Path]:
    repo = Path(__file__).resolve().parents[2]
    specs = sorted(repo.rglob("tests/mutation-specs/*.json"))
    # This is a non-vacuity guard, not a count pin: a broken layout/walk must
    # not certify "no offenders" by iterating over nothing.
    assert specs, "found no committed mutation specs under tests/mutation-specs/*.json"
    return specs


def _spec_skill_dir(spec_path: Path) -> Path:
    parts = spec_path.parts
    assert "tests" in parts, f"mutation spec path has no 'tests' component: {spec_path}"
    tests_index = len(parts) - 1 - parts[::-1].index("tests")
    return Path(*parts[:tests_index]).resolve()


def test_no_committed_spec_has_an_absolute_root() -> None:
    offenders = []
    for spec_path in _committed_mutation_specs():
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        root = spec.get("root")
        if root and Path(root).is_absolute():
            offenders.append(f"{spec_path}: root={root!r}")

    assert not offenders, (
        "committed mutation specs must not have absolute roots; "
        "use a spec-relative root so a bare clone or copied checkout resolves "
        "the same targets:\n" + "\n".join(offenders)
    )


def test_every_committed_spec_resolves_within_its_own_skill() -> None:
    offenders = []
    for spec_path in _committed_mutation_specs():
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        resolved = h_mad_mutation_harness._resolve_root(spec, spec_path)
        skill_dir = _spec_skill_dir(spec_path)
        if resolved != skill_dir and skill_dir not in resolved.parents:
            offenders.append(
                f"{spec_path}: root resolves to {resolved}, outside skill {skill_dir}"
            )

    assert not offenders, (
        "committed mutation specs must resolve within their own skill directory; "
        "a spec root above the skill can mutate files outside the portable skill "
        "checkout:\n" + "\n".join(offenders)
    )
