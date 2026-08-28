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


class TestObservableFidelity:
    """J39 — `_observe` took the FIRST regex match; every other extractor in this
    skill takes the LAST.

    `h_mad_extract_verdict.py` uses `matches[-1]` deliberately, because an agent's
    log contains the prompt before it contains the answer. `_observe` used
    `pattern.search()`, so a prompt echo — the observable's own name, quoted back
    in the instruction the agent was given — wins over the value the agent
    actually produced. Measured before the fix: a log containing the instruction
    `emit a line like RESULT: <n>`, then `RESULT: 0` as the echo, then `RESULT: 42`
    as the real answer, returned **0**.

    The consequence is specific to what this tool is for. Both arms echo the same
    prompt, so both observe the same value, so the run reports `SAME` — "the rule
    is present and not causally effective" — which is a *finding*, not an error. A
    tool built to establish causality would have been reporting the prompt back to
    the operator as a result.
    """

    def test_the_last_match_wins_not_the_prompt_echo(self, tmp_path):
        import re
        from h_mad_ab_dispatch import _observe

        log = tmp_path / "arm.log"
        log.write_text(
            "Instruction: emit a line like RESULT: <n>\n"
            "RESULT: 0\n"
            "...agent works...\n"
            "RESULT: 42\n",
            encoding="utf-8",
        )

        assert _observe(log, re.compile(r"RESULT: (\d+)")) == "42"

    def test_a_single_match_is_unchanged(self, tmp_path):
        """The accept direction — last-match must not break the ordinary log."""
        import re
        from h_mad_ab_dispatch import _observe

        log = tmp_path / "arm.log"
        log.write_text("noise\nRESULT: 7\nmore noise\n", encoding="utf-8")

        assert _observe(log, re.compile(r"RESULT: (\d+)")) == "7"

    def test_no_match_is_still_none(self, tmp_path):
        """`None` drives INCONCLUSIVE. Two silent arms must never compare equal,
        so this may not start returning an empty string."""
        import re
        from h_mad_ab_dispatch import _observe

        log = tmp_path / "arm.log"
        log.write_text("nothing here\n", encoding="utf-8")

        assert _observe(log, re.compile(r"RESULT: (\d+)")) is None

    def test_matches_the_extractor_this_skill_already_standardised_on(self, tmp_path):
        """Pinned against the real extractor rather than restating its rule here.

        The defect was an inconsistency, so the assertion is the consistency: if
        `extract_verdict` ever changes which match wins, this fails and someone
        decides deliberately instead of the two drifting apart again.
        """
        import re
        from h_mad_ab_dispatch import _observe
        from h_mad_extract_verdict import extract_verdict

        body = "VALUE: first\nnoise\nVALUE: last\n"
        log = tmp_path / "arm.log"
        log.write_text(body, encoding="utf-8")

        assert _observe(log, re.compile(r"VALUE: (\w+)")) == extract_verdict(body, "VALUE")

    def test_a_regex_without_a_capture_group_is_refused_at_the_boundary(self, tmp_path):
        """Already true before this change; pinned because last-match is being
        rewritten around `group(1)` and losing this would turn an operator error
        into a stack trace mid-dispatch. Probed first: the guard exists and prints
        `--observe needs exactly one capture group`, so this is a regression pin,
        not a new fix."""
        result = subprocess.run(
            [sys.executable, str(AB), "--template", str(tmp_path / "t.md"),
             "--var", "V", "--a", "x", "--b", "y",
             "--observe", r"RESULT: \d+", "--out", str(tmp_path / "o"),
             "--run", "true"],
            capture_output=True, text=True,
        )
        assert result.returncode == 2, result.stdout
        assert "capture group" in (result.stdout + result.stderr)


class TestRunTokenParsing:
    """J38 — the invocation SKILL.md documents is the one that fails.

    `--run` is `action="append"`, so argparse treats a value beginning with `-` as
    an option: `--run --model` errors with `expected one argument` while
    `--run=--model` works. Every real dispatch argv starts with flags, so the
    documented space-separated form is broken for essentially every real use.
    """

    def test_dash_leading_token_in_the_documented_space_separated_form(self, tmp_path):
        template = tmp_path / "t.md"
        template.write_text("R: {{V}}\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(AB), "--template", str(template),
             "--var", "V", "--a", "on", "--b", "off",
             "--observe", r"RESULT: (\d+)", "--out", str(tmp_path / "o"),
             "--run", "echo", "--run", "--model", "--run", "gpt-5.5"],
            capture_output=True, text=True,
        )
        combined = result.stdout + result.stderr
        # Assert PARSING, never the outcome: INCONCLUSIVE legitimately exits 2, so
        # scoring this on the exit code would pass for a tool that never parsed the
        # argv at all — the same "exit code is not a verdict" trap this tool exists
        # to enforce elsewhere.
        assert "expected one argument" not in combined, combined
        assert "usage:" not in combined, combined

    def test_the_equals_form_still_works(self, tmp_path):
        """It is what every existing caller had to use; it must not regress."""
        template = tmp_path / "t.md"
        template.write_text("R: {{V}}\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(AB), "--template", str(template),
             "--var", "V", "--a", "on", "--b", "off",
             "--observe", r"RESULT: (\d+)", "--out", str(tmp_path / "o"),
             "--run=echo", "--run=--model", "--run=gpt-5.5"],
            capture_output=True, text=True,
        )
        combined = result.stdout + result.stderr
        assert "expected one argument" not in combined, combined
        assert "usage:" not in combined, combined


def test_skill_documents_a_run_form_that_actually_parses():
    skill = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")
    line = next(l for l in skill.splitlines() if "h_mad_ab_dispatch.py" in l and "--run" in l)
    assert "--run" in line
    # The documented form must not be the bare space-separated one that argparse
    # rejects for a dash-leading token, unless the tool now accepts it.
    assert "argv token" in line


class TestPerArmPathScoping:
    """J40 (F5) — only `{prompt}` and `{log}` were substituted, so every OTHER
    per-arm path in `--run` was byte-identical across the two arms.

    An operator writing `--run --out --run /tmp/result.json` gets one file: arm B
    overwrites arm A, and the comparison then reads B against B. That is silent,
    and it produces `SAME` — "the rule is not causally effective" — which is the
    single most believable wrong answer this tool can give, and the one its whole
    verdict set exists to prevent elsewhere.

    Fixed with an `{arm}` placeholder rather than by teaching the tool about
    specific flags: the tool cannot know which of an arbitrary argv is a path, and
    a guess would be wrong for the next runner. `{arm}` composes with anything.
    """

    def test_two_arms_no_longer_share_an_output_path(self, tmp_path):
        """End to end through the CLI: the arms must not collide on a path the
        operator supplied, which is the whole of F5."""
        template = tmp_path / "t.md"
        template.write_text("R: {{V}}\n", encoding="utf-8")
        target = tmp_path / "res_{arm}.txt"
        result = subprocess.run(
            [sys.executable, str(AB), "--template", str(template),
             "--var", "V", "--a", "on", "--b", "off",
             "--observe", r"RESULT: (\w+)", "--out", str(tmp_path / "o"),
             "--run", "sh", "--run", "-c",
             "--run", f"printf 'RESULT: %s\\n' \"$0\" > {target}; printf 'RESULT: %s\\n' \"$0\" > {{log}}",
             "--run", "{arm}"],
            capture_output=True, text=True,
        )
        assert (tmp_path / "res_a.txt").exists(), result.stdout + result.stderr
        assert (tmp_path / "res_b.txt").exists(), result.stdout + result.stderr

    def test_a_run_without_the_arm_placeholder_is_unchanged(self, tmp_path):
        """Accept direction: adding a placeholder must not disturb callers that
        never use it."""
        template = tmp_path / "t.md"
        template.write_text("R: {{V}}\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(AB), "--template", str(template),
             "--var", "V", "--a", "on", "--b", "off",
             "--observe", r"RESULT: (\w+)", "--out", str(tmp_path / "o"),
             "--run", "true"],
            capture_output=True, text=True,
        )
        assert "usage:" not in (result.stdout + result.stderr)


def test_skill_states_the_environment_is_not_controlled():
    """J40 (F3) — the tool controls the PROMPT and nothing else.

    An arm difference outside the declared variable — a changed file on disk, a
    different model default, an env var — is invisible to it, and `UNCONTROLLED`
    only ever compares the two prompts. That is a real limit on what a `SAME` or a
    difference means, and an unstated limit reads as a guarantee.
    """
    skill = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")
    assert "does not control the environment" in skill
