#!/usr/bin/env python3
"""Controlled A/B dispatch: two prompts differing in exactly ONE variable.

A single dispatch cannot tell you whether a rule in the prompt did anything. An
agent that would have done the right thing anyway looks identical to one the
rule steered, and "the rule is present" then gets recorded as "the rule works".
Two arms differing in one variable, diffed on an observable, is what turns the
first claim into the second. It has been run twice by hand — the context-budget
advisory against `HMAD_CONTEXT_WINDOW`, and a time-bound rule present vs absent
— and both times the control is what made the result mean anything.

Three refusals carry the tool:

`UNCONTROLLED` — the arms differ in more than the declared variable (or in
nothing at all). This is the mistake a human A/B actually makes, and it is
silent: the run completes, the numbers differ, and the difference is attributed
to the wrong cause.

`INCONCLUSIVE` — an arm produced no log, or the observable never matched in one.
Two silent arms compare equal, so `SAME` is the most believable lie available
here. Nothing was observed, so nothing was compared.

The exit code is reported and never scored. Both arms exit 0 routinely: a
dispatch killed by its parent shell, a skipped test and a clean run all do, and
this repo has been fooled by each of them.

Stdlib only, like every other h-mad script.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ARMS = ("a", "b")


def build_arms(template: str, var: str, value_a: str, value_b: str) -> tuple[str, str]:
    """The two prompts, identical except where `{{var}}` was substituted."""
    placeholder = "{{" + var + "}}"
    return template.replace(placeholder, value_a), template.replace(placeholder, value_b)


def is_controlled(template: str, var: str, value_a: str, value_b: str) -> str:
    """Empty string when the pair is a controlled experiment, else the reason.

    The check is the point of the tool, so it is made against the built prompts
    rather than trusted from construction: re-deriving the template from each
    arm proves the substitution touched only the declared sites. A value that
    contains the placeholder, or one arm's value appearing inside the other's,
    fails here — those change more than one thing while still looking like a
    single-variable diff.
    """
    placeholder = "{{" + var + "}}"
    if placeholder not in template:
        return f"the template has no {placeholder} — both arms would be identical"
    if value_a == value_b:
        return f"both arms set {var} to the same value, so nothing varies"
    if placeholder in value_a or placeholder in value_b:
        return f"a value contains {placeholder} and re-expands, changing more than {var}"

    prompt_a, prompt_b = build_arms(template, var, value_a, value_b)
    # Re-deriving the template from each arm is only meaningful when the value
    # is non-empty; an empty arm IS the template with the placeholder removed.
    if value_a and prompt_a.replace(value_a, placeholder) != template:
        return f"arm a differs from the template outside {placeholder}"
    if value_b and prompt_b.replace(value_b, placeholder) != template:
        return f"arm b differs from the template outside {placeholder}"
    return ""


def _observe(log_path: Path, pattern: re.Pattern) -> str | None:
    """The first capture of `pattern` in the log, or None if there is nothing."""
    try:
        text = log_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    if not text.strip():
        return None
    match = pattern.search(text)
    return match.group(1) if match else None


def run_ab(
    out_dir: Path,
    template: str,
    var: str,
    value_a: str,
    value_b: str,
    runner,
    observe: str,
) -> dict:
    """Dispatch both arms through `runner` and diff one observable.

    `runner(arm, prompt_path, log_path) -> int` does the dispatching, so the
    scoring is testable without paying for two live agent runs.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = re.compile(observe)

    reason = is_controlled(template, var, value_a, value_b)
    if reason:
        # Refused BEFORE dispatching: an uncontrolled pair cannot produce a
        # finding, so paying for two agent runs to learn that is pure waste.
        return {"verdict": "UNCONTROLLED", "reason": reason, "a": None, "b": None,
                "exits": {}}

    prompts = dict(zip(ARMS, build_arms(template, var, value_a, value_b)))
    observations: dict[str, str | None] = {}
    exits: dict[str, int] = {}
    for arm in ARMS:
        prompt_path = out_dir / f"ab-{arm}.prompt.md"
        log_path = out_dir / f"ab-{arm}.log"
        prompt_path.write_text(prompts[arm], encoding="utf-8")
        exits[arm] = runner(arm, prompt_path, log_path)
        observations[arm] = _observe(log_path, pattern)

    silent = [arm for arm in ARMS if observations[arm] is None]
    if silent:
        return {
            "verdict": "INCONCLUSIVE",
            "reason": "no observation from arm " + " and arm ".join(silent)
                      + " — nothing was observed, so nothing was compared",
            "a": observations["a"], "b": observations["b"], "exits": exits,
        }

    same = observations["a"] == observations["b"]
    return {
        "verdict": "SAME" if same else "DIFFERENT",
        "reason": "" if not same else f"{var} did not change the observable",
        "a": observations["a"], "b": observations["b"], "exits": exits,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Dispatch two prompts differing in one variable and diff an observable"
    )
    parser.add_argument("--template", type=Path, required=True,
                        help="prompt file containing {{VAR}}")
    parser.add_argument("--var", required=True, help="the ONE variable that differs")
    parser.add_argument("--a", required=True, help="value for arm a")
    parser.add_argument("--b", required=True, help="value for arm b (often empty)")
    parser.add_argument("--observe", required=True,
                        help="regex with ONE capture group, applied to each arm's log")
    parser.add_argument("--out", type=Path, required=True,
                        help="directory for the two prompts and two logs")
    parser.add_argument("--run", action="append", required=True, metavar="TOKEN",
                        help="argv token for the dispatch; repeat. "
                             "{prompt} and {log} are substituted per arm")
    args = parser.parse_args(argv)

    try:
        pattern = re.compile(args.observe)
    except re.error as exc:
        parser.error(f"--observe is not a valid regex: {exc}")
    if pattern.groups < 1:
        # Without a group there is nothing to compare, and `re` would raise
        # after both dispatches had already been paid for.
        parser.error("--observe needs exactly one capture group — the observable")

    try:
        template = args.template.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("AB: UNREADABLE")
        print("  the template could not be read, so nothing was dispatched.")
        print("[H-MAD] ab-dispatch UNREADABLE")
        return 2

    def runner(arm: str, prompt_path: Path, log_path: Path) -> int:
        argv_arm = [
            token.replace("{prompt}", str(prompt_path)).replace("{log}", str(log_path))
            for token in args.run
        ]
        try:
            return subprocess.run(argv_arm, capture_output=True).returncode
        except OSError as exc:
            print(f"ERROR: arm {arm} could not launch: {exc}", file=sys.stderr)
            return 127

    result = run_ab(args.out, template, args.var, args.a, args.b, runner, args.observe)
    verdict = result["verdict"]

    print(f"AB: {verdict} var={args.var} a={result['a']} b={result['b']}")
    if result["exits"]:
        # Reported, never scored — a crashed arm must be visible even when the
        # observable happened to differ.
        print("  exits: " + ", ".join(f"{arm}={code}" for arm, code in result["exits"].items()))
    if result["reason"]:
        print(f"  {result['reason']}")
    if verdict == "UNCONTROLLED":
        print(
            "  the arms differ in more than the declared variable, so any "
            "difference would be attributed to the wrong cause. Nothing was dispatched."
        )
    elif verdict == "INCONCLUSIVE":
        print(
            "  two silent arms compare equal, so this is NOT a SAME. Fix the "
            "dispatch or the observable and re-run."
        )
    elif verdict == "SAME":
        print(
            "  a real SAME is a finding: the variable did not steer the agent. "
            "The rule is present and not causally effective."
        )
    print(f"[H-MAD] ab-dispatch {verdict}")
    return 0 if verdict in {"DIFFERENT", "SAME"} else 2


if __name__ == "__main__":
    sys.exit(main())
