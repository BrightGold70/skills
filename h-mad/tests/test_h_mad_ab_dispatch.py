"""Controlled A/B dispatch: two prompts differing in exactly one variable.

Used twice by hand before it was a tool — the context-budget advisory against
`HMAD_CONTEXT_WINDOW`, and a time-bound rule present vs absent — and both times
the CONTROL is what turned "the rule is present in the prompt" into "the rule is
causally effective". A single arm proves nothing: an agent that would have done
the right thing anyway is indistinguishable from one the rule steered.

Three things this refuses, because each one produces a confident wrong answer:

- Scoring on the exit code. Both arms exit 0 routinely — a killed dispatch, a
  skipped test and a clean run all do.
- Reading two silent arms as `SAME`. Nothing was observed, so nothing was
  compared, and "no difference" is the most believable lie available.
- Calling an experiment controlled when the arms differ in more than the one
  declared variable. That is the mistake a human A/B actually makes.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
AB = SCRIPTS / "h_mad_ab_dispatch.py"

sys.path.insert(0, str(SCRIPTS))
from h_mad_ab_dispatch import build_arms, run_ab  # noqa: E402


TEMPLATE = "Do the task.\n\nRULE: {{RULE}}\n\nReport when done.\n"


def _fake_runner(observations: dict[str, str], exits: dict[str, int] | None = None):
    """A runner that writes a canned log per arm instead of dispatching."""
    exits = exits or {}

    def run(arm: str, prompt_path: Path, log_path: Path) -> int:
        text = observations.get(arm)
        if text is not None:
            log_path.write_text(text, encoding="utf-8")
        return exits.get(arm, 0)

    return run


# --- the control ----------------------------------------------------------


def test_the_two_arms_differ_only_at_the_variable() -> None:
    a, b = build_arms(TEMPLATE, "RULE", "obey the time bound", "")

    assert "obey the time bound" in a
    assert "obey the time bound" not in b
    # Everything else is byte-identical: that is what makes the diff mean anything.
    assert a.replace("obey the time bound", "") == b


def test_a_template_without_the_variable_is_uncontrolled(tmp_path: Path) -> None:
    """Both arms would be identical, so any observed difference is noise."""
    result = run_ab(
        tmp_path, "no placeholder here\n", "RULE", "on", "off",
        _fake_runner({"a": "X", "b": "Y"}), observe=r"(X|Y)",
    )

    assert result["verdict"] == "UNCONTROLLED", result
    assert "RULE" in result["reason"]


def test_two_equal_values_are_uncontrolled(tmp_path: Path) -> None:
    result = run_ab(
        tmp_path, TEMPLATE, "RULE", "same", "same",
        _fake_runner({"a": "X", "b": "Y"}), observe=r"(X|Y)",
    )

    assert result["verdict"] == "UNCONTROLLED", result


def test_a_value_that_smuggles_in_the_other_arm_is_uncontrolled(
    tmp_path: Path,
) -> None:
    """A value containing the placeholder re-expands and changes more than one
    thing — the arms are then not a controlled pair, however they were built."""
    result = run_ab(
        tmp_path, TEMPLATE, "RULE", "{{RULE}} and more", "off",
        _fake_runner({"a": "X", "b": "Y"}), observe=r"(X|Y)",
    )

    assert result["verdict"] == "UNCONTROLLED", result


# --- the verdicts ---------------------------------------------------------


def test_a_real_difference_is_reported_with_both_observations(tmp_path: Path) -> None:
    result = run_ab(
        tmp_path, TEMPLATE, "RULE", "obey", "",
        _fake_runner({"a": "DEADLINE: 1800\n", "b": "DEADLINE: none\n"}),
        observe=r"DEADLINE: (\S+)",
    )

    assert result["verdict"] == "DIFFERENT", result
    assert result["a"] == "1800"
    assert result["b"] == "none"


def test_no_difference_is_reported_as_same(tmp_path: Path) -> None:
    """A real SAME is a finding: the variable did not steer anything."""
    result = run_ab(
        tmp_path, TEMPLATE, "RULE", "obey", "",
        _fake_runner({"a": "DEADLINE: none\n", "b": "DEADLINE: none\n"}),
        observe=r"DEADLINE: (\S+)",
    )

    assert result["verdict"] == "SAME", result


# --- what must never read as SAME ----------------------------------------


def test_an_arm_that_produced_no_log_is_inconclusive(tmp_path: Path) -> None:
    """Two silent arms compare equal. Nothing was observed, so nothing was
    compared — and `SAME` would be the most believable lie available."""
    result = run_ab(
        tmp_path, TEMPLATE, "RULE", "obey", "",
        _fake_runner({}), observe=r"DEADLINE: (\S+)",
    )

    assert result["verdict"] == "INCONCLUSIVE", result
    assert "a" in result["reason"] and "b" in result["reason"]


def test_one_silent_arm_is_inconclusive_and_names_it(tmp_path: Path) -> None:
    result = run_ab(
        tmp_path, TEMPLATE, "RULE", "obey", "",
        _fake_runner({"a": "DEADLINE: 1800\n"}), observe=r"DEADLINE: (\S+)",
    )

    assert result["verdict"] == "INCONCLUSIVE", result
    assert "b" in result["reason"], result["reason"]


def test_an_arm_whose_observable_never_matched_is_inconclusive(tmp_path: Path) -> None:
    """A log that ran and says nothing about the observable is not evidence of
    sameness — it is evidence the probe was aimed wrong."""
    result = run_ab(
        tmp_path, TEMPLATE, "RULE", "obey", "",
        _fake_runner({"a": "DEADLINE: 1800\n", "b": "the agent talked about other things\n"}),
        observe=r"DEADLINE: (\S+)",
    )

    assert result["verdict"] == "INCONCLUSIVE", result
    assert "b" in result["reason"]


# --- the exit code is reported, never scored ------------------------------


def test_a_nonzero_exit_does_not_decide_the_verdict(tmp_path: Path) -> None:
    """Both arms exit 0 routinely — a killed dispatch, a skipped test and a
    clean run all do — so the exit code cannot carry the finding. It is still
    reported, because a crashed arm is something the reader must see."""
    result = run_ab(
        tmp_path, TEMPLATE, "RULE", "obey", "",
        _fake_runner({"a": "DEADLINE: 1800\n", "b": "DEADLINE: none\n"}, exits={"b": 9}),
        observe=r"DEADLINE: (\S+)",
    )

    assert result["verdict"] == "DIFFERENT", result
    assert result["exits"]["b"] == 9, "a crashed arm must still be visible"


def test_a_zero_exit_with_an_empty_log_is_still_inconclusive(tmp_path: Path) -> None:
    """The exact shape of the failure this exists for: exit 0 and nothing done."""
    result = run_ab(
        tmp_path, TEMPLATE, "RULE", "obey", "",
        _fake_runner({"a": "DEADLINE: 1800\n", "b": ""}),
        observe=r"DEADLINE: (\S+)",
    )

    assert result["verdict"] == "INCONCLUSIVE", result


# --- artefacts ------------------------------------------------------------


def test_both_prompts_are_written_so_the_experiment_can_be_re_read(
    tmp_path: Path,
) -> None:
    """An A/B nobody can re-read is an anecdote."""
    run_ab(
        tmp_path, TEMPLATE, "RULE", "obey", "",
        _fake_runner({"a": "DEADLINE: 1\n", "b": "DEADLINE: 2\n"}),
        observe=r"DEADLINE: (\S+)",
    )

    assert (tmp_path / "ab-a.prompt.md").read_text(encoding="utf-8").count("obey") == 1
    assert "obey" not in (tmp_path / "ab-b.prompt.md").read_text(encoding="utf-8")


# --- CLI ------------------------------------------------------------------


def _cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(AB), *args], capture_output=True, text=True)


def test_cli_runs_a_real_pair_and_prints_the_token(tmp_path: Path) -> None:
    template = tmp_path / "t.md"
    template.write_text(TEMPLATE, encoding="utf-8")
    # A runner that simply echoes its own prompt file into the log, so the two
    # arms genuinely differ in the observable.
    runner = tmp_path / "runner.py"
    runner.write_text(
        "import sys, pathlib\n"
        "p, log = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])\n"
        "rule = 'yes' if 'obey' in p.read_text() else 'no'\n"
        "log.write_text('DEADLINE: ' + rule + chr(10))\n",
        encoding="utf-8",
    )

    proc = _cli(
        "--template", str(template), "--var", "RULE", "--a", "obey", "--b", "",
        "--observe", r"DEADLINE: (\S+)", "--out", str(tmp_path),
        "--run", sys.executable, "--run", str(runner),
        "--run", "{prompt}", "--run", "{log}",
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "AB: DIFFERENT" in proc.stdout, proc.stdout
    assert "a=yes" in proc.stdout and "b=no" in proc.stdout, proc.stdout
    assert "[H-MAD]" in proc.stdout, proc.stdout


def test_cli_exits_2_on_inconclusive(tmp_path: Path) -> None:
    template = tmp_path / "t.md"
    template.write_text(TEMPLATE, encoding="utf-8")
    runner = tmp_path / "runner.py"
    runner.write_text("import sys\n", encoding="utf-8")  # writes no log at all

    proc = _cli(
        "--template", str(template), "--var", "RULE", "--a", "obey", "--b", "",
        "--observe", r"DEADLINE: (\S+)", "--out", str(tmp_path),
        "--run", sys.executable, "--run", str(runner),
        "--run", "{prompt}", "--run", "{log}",
    )

    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "AB: INCONCLUSIVE" in proc.stdout, proc.stdout
    # The verdict token, not the word: the explanatory line deliberately says
    # "this is NOT a SAME", and a bare substring check would forbid saying so.
    assert "AB: SAME" not in proc.stdout


def test_cli_requires_a_capture_group(tmp_path: Path) -> None:
    """Without one there is nothing to compare, and `re` would raise mid-run —
    after both dispatches had already been paid for."""
    template = tmp_path / "t.md"
    template.write_text(TEMPLATE, encoding="utf-8")

    proc = _cli(
        "--template", str(template), "--var", "RULE", "--a", "x", "--b", "y",
        "--observe", r"DEADLINE: \S+", "--out", str(tmp_path),
        "--run", "true",
    )

    assert proc.returncode != 0
    assert "capture group" in (proc.stdout + proc.stderr)


def test_the_skill_documents_the_harness() -> None:
    skill = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")
    assert "h_mad_ab_dispatch.py" in skill, "a tool nobody is told to run is never run"
    assert "AB:" in skill, "the token is undocumented"
    assert "INCONCLUSIVE" in skill, (
        "the reader must be told that two silent arms are not a SAME"
    )


def test_a_blank_log_is_not_an_observation_even_for_a_permissive_probe(
    tmp_path: Path,
) -> None:
    """`DEADLINE: (\\S+)` cannot match an empty log, so it cannot discriminate
    the blank-log guard — the earlier test passed with the guard removed.

    A permissive probe like `(.*)` DOES match an empty string and would record
    an empty observation as a real one. Both arms then observe `""` and compare
    equal, which is the silent-arm lie wearing a successful experiment's report.
    Found by mutation.
    """
    result = run_ab(
        tmp_path, TEMPLATE, "RULE", "obey", "",
        _fake_runner({"a": "", "b": ""}), observe=r"(.*)",
    )

    assert result["verdict"] == "INCONCLUSIVE", result


def test_differing_exit_codes_do_not_manufacture_a_difference(
    tmp_path: Path,
) -> None:
    """The discriminating direction the first exit-code test missed.

    With observations EQUAL and exits DIFFERENT, scoring on the exit code flips
    a real `SAME` — the finding that the rule is not causally effective — into
    a `DIFFERENT` that credits the variable for a crash. The earlier test had
    exits differing AND observations differing, so both the guard and the bug
    produced `DIFFERENT`.
    """
    result = run_ab(
        tmp_path, TEMPLATE, "RULE", "obey", "",
        _fake_runner({"a": "DEADLINE: none\n", "b": "DEADLINE: none\n"}, exits={"b": 9}),
        observe=r"DEADLINE: (\S+)",
    )

    assert result["verdict"] == "SAME", result
    assert result["exits"]["b"] == 9
