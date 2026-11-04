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
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ARMS = ("a", "b")


def build_arms(template: str, var: str, value_a: str, value_b: str) -> tuple[str, str]:
    """The two prompts, identical except where `{{var}}` was substituted."""
    placeholder = "{{" + var + "}}"
    return template.replace(placeholder, value_a), template.replace(placeholder, value_b)


def build_run_arms(
    run_tokens: list[str] | tuple[str, ...], var: str, value_a: str, value_b: str
) -> tuple[list[str], list[str]]:
    """The two dispatch argvs, identical except where `{{var}}` was substituted."""
    placeholder = "{{" + var + "}}"
    return (
        [token.replace(placeholder, value_a) for token in run_tokens],
        [token.replace(placeholder, value_b) for token in run_tokens],
    )


def is_controlled(
    template: str,
    var: str,
    value_a: str,
    value_b: str,
    run_tokens: list[str] | tuple[str, ...] | None = None,
) -> str:
    """Empty string when the pair is a controlled experiment, else the reason.

    The check is the point of the tool, so it is made against the built prompts
    (and built `--run` argvs when `{{var}}` lives in `--run`) rather than trusted
    from construction: re-deriving the template and argv from each arm proves the
    substitution touched only the declared sites. A value that contains the
    placeholder, or one arm's value appearing outside the placeholder in the
    template or `--run`, fails here — those change more than one thing while
    still looking like a single-variable diff.
    """
    placeholder = "{{" + var + "}}"
    tokens = list(run_tokens or ())
    in_template = placeholder in template
    in_run = any(placeholder in token for token in tokens)
    if placeholder not in template:
        if not in_run:
            return f"the template has no {placeholder} — both arms would be identical"
    if value_a == value_b:
        return f"both arms set {var} to the same value, so nothing varies"
    if placeholder in value_a or placeholder in value_b:
        return f"a value contains {placeholder} and re-expands, changing more than {var}"

    if in_template:
        prompt_a, prompt_b = build_arms(template, var, value_a, value_b)
        # Re-deriving the template from each arm is only meaningful when the value
        # is non-empty; an empty arm IS the template with the placeholder removed.
        if value_a and prompt_a.replace(value_a, placeholder) != template:
            return f"arm a differs from the template outside {placeholder}"
        if value_b and prompt_b.replace(value_b, placeholder) != template:
            return f"arm b differs from the template outside {placeholder}"

    if in_run:
        run_a, run_b = build_run_arms(tokens, var, value_a, value_b)
        if value_a and [t.replace(value_a, placeholder) for t in run_a] != tokens:
            return f"arm a argv differs from --run outside {placeholder}"
        if value_b and [t.replace(value_b, placeholder) for t in run_b] != tokens:
            return f"arm b argv differs from --run outside {placeholder}"
    return ""


def _split_run_tokens(argv: list[str]) -> tuple[list[str], list[str]]:
    """Pull `--run <token>` pairs out of argv before argparse sees them.

    argparse treats any value beginning with `-` as an option, so `--run --model`
    fails with `expected one argument` while `--run=--model` works — and every real
    dispatch argv starts with flags, which made the space-separated form SKILL.md
    documents broken for essentially every real invocation (J38). Consuming the
    token positionally here is what lets both forms work; the `=` form is left for
    argparse so existing callers, who had to use it, are untouched.
    """
    rest: list[str] = []
    tokens: list[str] = []
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--run" and index + 1 < len(argv):
            tokens.append(argv[index + 1])
            index += 2
            continue
        rest.append(arg)
        index += 1
    return rest, tokens


def _observe(log_path: Path, pattern: re.Pattern) -> str | None:
    """The LAST capture of `pattern` in the log, or None if there is nothing.

    Last, not first, and for the same reason `h_mad_extract_verdict.py` takes
    `matches[-1]`: an agent's log contains the PROMPT before it contains the
    answer, so the first match is routinely the observable's own name quoted back
    out of the instruction the agent was given. Measured (J39): a log reading
    `emit a line like RESULT: <n>` / `RESULT: 0` / … / `RESULT: 42` observed `0`.

    That failure is specific to what this tool is for. Both arms echo the same
    prompt, so both observe the same echoed value, so the run reports `SAME` — "the
    rule is present and not causally effective" — which is a FINDING, not an
    error. A tool built to establish causality was capable of reporting the prompt
    back to the operator as its result.

    `None` when nothing matched, never `""`: an unobserved arm must stay
    distinguishable from an observed empty one, because two silent arms compare
    equal and `SAME` is the most believable lie available (§`INCONCLUSIVE`).
    """
    try:
        text = log_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    if not text.strip():
        return None
    matches = list(pattern.finditer(text))
    return matches[-1].group(1) if matches else None


def _is_test_path(rel: str) -> bool:
    name = Path(rel).name
    return name.endswith(".py") and (
        name.startswith("test_") or name.endswith("_test.py") or "/tests/" in f"/{rel}"
    )


def _remove_worktree(repo: Path, wt: Path) -> None:
    subprocess.run(
        ["git", "-C", str(repo), "worktree", "remove", "--force", "--force", str(wt)],
        capture_output=True,
    )
    shutil.rmtree(wt, ignore_errors=True)


def verify_replay_control(
    repo: Path, spec: str, python: str = sys.executable
) -> tuple[str, str, list[str], str]:
    """Verify `<red>..<green>` positive control (RED fails at `<red>`, reference GREEN passes).

    Returns `(red_sha, green_sha, red_tests, error_reason)`. `error_reason` is empty
    when the positive control passes.
    """
    red_ref, sep, green_ref = spec.partition("..")
    if not sep or not red_ref or not green_ref:
        return "", "", [], f"invalid --replay range {spec!r}; expected <red>..<green>"
    r_red = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", f"{red_ref}^{{commit}}"],
        capture_output=True, text=True,
    )
    r_green = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", f"{green_ref}^{{commit}}"],
        capture_output=True, text=True,
    )
    if r_red.returncode != 0 or r_green.returncode != 0:
        return "", "", [], f"could not resolve --replay commits {spec!r}"
    red_sha, green_sha = r_red.stdout.strip(), r_green.stdout.strip()
    red_files = subprocess.run(
        ["git", "-C", str(repo), "show", "--name-only", "--format=", red_sha],
        capture_output=True, text=True,
    ).stdout.splitlines()
    red_tests = [p.strip() for p in red_files if p.strip() and _is_test_path(p.strip())]
    if not red_tests:
        return red_sha, green_sha, [], f"no RED test files found in {red_ref}"
    diff_files = subprocess.run(
        ["git", "-C", str(repo), "diff-tree", "--no-commit-id", "--name-only", "-r", red_sha, green_sha],
        capture_output=True, text=True,
    ).stdout.splitlines()
    prod_files = [p.strip() for p in diff_files if p.strip() and not _is_test_path(p.strip())]
    if not prod_files:
        return red_sha, green_sha, red_tests, f"no production files found in {green_ref}"

    ctl_wt = Path(tempfile.mkdtemp(prefix=".h-mad-ab-ctl-", dir=repo.parent))
    try:
        add = subprocess.run(
            ["git", "-C", str(repo), "worktree", "add", "--detach", "--quiet", str(ctl_wt), red_sha],
            capture_output=True, text=True,
        )
        if add.returncode != 0:
            return red_sha, green_sha, red_tests, f"could not add replay control worktree: {add.stderr.strip()}"
        red_run = subprocess.run(
            [python, "-m", "pytest", *red_tests, "-q", "-p", "no:cacheprovider"],
            cwd=str(ctl_wt), stdin=subprocess.DEVNULL, capture_output=True, text=True,
        )
        if red_run.returncode != 1:  # M:AB-REPLAY-RED-CTL
            return (
                red_sha, green_sha, red_tests,
                f"positive control failed: RED tests did not fail at {red_ref} (rc={red_run.returncode})",
            )
        subprocess.run(
            ["git", "-C", str(ctl_wt), "checkout", green_sha, "--", *prod_files],
            capture_output=True, text=True,
        )
        green_run = subprocess.run(
            [python, "-m", "pytest", *red_tests, "-q", "-p", "no:cacheprovider"],
            cwd=str(ctl_wt), stdin=subprocess.DEVNULL, capture_output=True, text=True,
        )
        if green_run.returncode != 0:  # M:AB-REPLAY-GREEN-CTL
            return (
                red_sha, green_sha, red_tests,
                f"positive control failed: reference GREEN did not pass at {green_ref} (rc={green_run.returncode})",
            )
    finally:
        _remove_worktree(repo, ctl_wt)
    return red_sha, green_sha, red_tests, ""


def run_ab(
    out_dir: Path,
    template: str,
    var: str,
    value_a: str,
    value_b: str,
    runner,
    observe: str,
    run_tokens: list[str] | tuple[str, ...] | None = None,
) -> dict:
    """Dispatch both arms through `runner` and diff one observable.

    `runner(arm, prompt_path, log_path) -> int` does the dispatching, so the
    scoring is testable without paying for two live agent runs.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = re.compile(observe)

    reason = is_controlled(template, var, value_a, value_b, run_tokens=run_tokens)
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
    parser.add_argument("--replay", default=None, metavar="RED..GREEN",
                        help="replay a past task in per-arm detached worktrees at <red> "
                             "after verifying the <red>..<green> positive control")
    parser.add_argument("--repo", type=Path, default=Path("."),
                        help="repository for --replay worktrees (default: .)")
    parser.add_argument("--python", default=sys.executable,
                        help="interpreter for --replay pytest runs")
    parser.add_argument("--run", action="append", metavar="TOKEN",
                        help="argv token for the dispatch; repeat. "
                             "{prompt}, {log} and {arm} are substituted per arm — "
                             "use {arm} in any OTHER per-arm path, or both arms share it. "
                             "A token beginning with '-' is fine in either form: "
                             "`--run --model` and `--run=--model` both work")
    argv, run_tokens = _split_run_tokens(sys.argv[1:] if argv is None else list(argv))
    args = parser.parse_args(argv)
    if run_tokens:
        args.run = (args.run or []) + run_tokens
    if not args.run:
        parser.error("--run is required")

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

    run_arms = dict(zip(ARMS, build_run_arms(args.run, args.var, args.a, args.b)))
    replay_red_sha = ""
    replay_tests: list[str] = []
    repo_root = args.repo.resolve()
    if args.replay:
        top = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True,
        )
        if top.returncode == 0 and top.stdout.strip():
            repo_root = Path(top.stdout.strip()).resolve()
        replay_red_sha, _, replay_tests, ctl_err = verify_replay_control(
            repo_root, args.replay, python=args.python
        )
        if ctl_err:
            print(f"AB: UNCONTROLLED var={args.var} a=None b=None")
            print(f"  {ctl_err}")
            print(
                "  the arms differ in more than the declared variable, so any "
                "difference would be attributed to the wrong cause. Nothing was dispatched."
            )
            print("[H-MAD] ab-dispatch UNCONTROLLED")
            return 2

    def runner(arm: str, prompt_path: Path, log_path: Path) -> int:
        wt_arm: Path | None = None
        if args.replay:
            wt_arm = Path(tempfile.mkdtemp(prefix=f".h-mad-ab-{arm}-", dir=repo_root.parent))
            subprocess.run(
                ["git", "-C", str(repo_root), "worktree", "add", "--detach", "--quiet", str(wt_arm), replay_red_sha],
                capture_output=True, text=True,
            )
        try:
            argv_arm = [
                # `{arm}` as well as `{prompt}`/`{log}`: without it every OTHER
                # per-arm path in the argv is byte-identical across arms, so arm B
                # overwrites arm A's output and the comparison reads B against B —
                # silently, and reporting SAME, which is the most believable wrong
                # answer this tool can give (J40/F5). A placeholder rather than
                # flag-awareness: the tool cannot know which of an arbitrary argv is a
                # path, and a guess would be wrong for the next runner.
                token.replace("{prompt}", str(prompt_path))
                     .replace("{log}", str(log_path))
                     .replace("{arm}", arm)
                     .replace("{worktree}", str(wt_arm) if wt_arm else "")
                for token in run_arms[arm]
            ]
            try:
                rc = subprocess.run(
                    argv_arm,
                    cwd=str(wt_arm) if wt_arm else None,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                ).returncode
            except OSError as exc:
                print(f"ERROR: arm {arm} could not launch: {exc}", file=sys.stderr)
                return 127
            if wt_arm is not None:
                edited = subprocess.run(
                    ["git", "-C", str(wt_arm), "status", "--porcelain", "--", *replay_tests],
                    capture_output=True, text=True,
                ).stdout.strip()
                tests_edited = len([ln for ln in edited.splitlines() if ln.strip()])
                pytest_res = subprocess.run(
                    [args.python, "-m", "pytest", *replay_tests, "-q", "-p", "no:cacheprovider"],
                    cwd=str(wt_arm), stdin=subprocess.DEVNULL, capture_output=True, text=True,
                )
                green_result = "pass" if (pytest_res.returncode == 0 and tests_edited == 0) else "fail"  # M:AB-REPLAY-TESTS-EDITED
                existing_log = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
                log_path.write_text(
                    existing_log
                    + f"\nTESTS_EDITED: {tests_edited}\nPYTEST_RC: {pytest_res.returncode}\nGREEN_RESULT: {green_result}\n",
                    encoding="utf-8",
                )
            return rc
        finally:
            if wt_arm is not None:
                _remove_worktree(repo_root, wt_arm)  # M:AB-REPLAY-WT-CLEANUP

    result = run_ab(
        args.out, template, args.var, args.a, args.b, runner, args.observe,
        run_tokens=args.run,
    )
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
