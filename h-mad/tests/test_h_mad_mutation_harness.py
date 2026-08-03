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
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
HARNESS = SCRIPTS / "h_mad_mutation_harness.py"

sys.path.insert(0, str(SCRIPTS))
from h_mad_mutation_harness import _restore_file, run_spec  # noqa: E402


GUARD = "THRESHOLD = 5\n# a comment that no test observes\n"

# Exits 0 only while the guard is intact — a stand-in for "the suite is green".
CHECK = (
    "import sys; sys.exit(0 if 'THRESHOLD = 5' in open('guard.py').read() else 1)"
)


def _project(tmp_path: Path, mutations: list[dict], check: str = CHECK) -> Path:
    """A tiny project plus a spec, written to `tmp_path`."""
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
