#!/usr/bin/env python3
"""h_mad_mutation_harness.py — Phase-5e: disable each guard, prove a test bites.

`invariants.base.md` §"Mutation verification" already requires this and already
names the way it fails: "a `.replace()` that matches nothing" leaves the guard
intact, the suite stays green, and the run reports the guard as ENFORCED. The
doctrine was complete; the executable was not — so every run hand-rolled a
harness and independently re-derived the same assert-landed guard, with the
correctness of the whole 5e pass resting on getting it right each time.

This is that harness, once.

Verdicts, printed as a canonical token:

    MUTATION: ALL_CAUGHT mutations=7 caught=7 survived=0 refused=0     exit 0
    MUTATION: SURVIVED   mutations=7 caught=5 survived=2 refused=0     exit 0
    MUTATION: REFUSED    mutations=7 caught=6 survived=0 refused=1     exit 2
    MUTATION: BASELINE_NOT_GREEN                                       exit 2
    MUTATION: RESTORE_FAILED                                           exit 2
    MUTATION: UNREADABLE                                               exit 2

`survived` and `refused` both sit on the summary line because they answer
different questions and neither may hide the other: a survivor is a guard that
does not bite, a refusal is a mutation that never landed and therefore measured
nothing. REFUSED outranks SURVIVED in the verdict word for the same reason the
wire-pin gate's UNSHAPED outranks a FAIL — "cannot judge" must never read as
"nothing to fix" — but the counts stay visible either way.

Exit 0 is reserved for a real verdict (§"Audit-gate signal discipline"), so
callers read the token, never `$?`. A SURVIVED run is a genuine measurement and
exits 0; only a run that could not measure exits non-zero.

Spec format (JSON):

    {
      "root": "/abs/path/to/repo",          # optional; defaults to the spec's dir
      "command": ["pytest", "-q"],          # argv list, run with cwd=root, no shell
      "target_command": ["pytest", "-q"],   # optional; prefix for per-mutation runs
      "mutations": [
        {"name": "drop the allowlist", "file": "src/gate.py",
         "find": "<exact text>", "replace": "",
         "test": "tests/test_gate.py::test_allowlist"}   # optional
      ]
    }

`command` is an argv list rather than a shell string on purpose: a shell string
would make the harness's own behaviour depend on quoting, and this tool's whole
value is that it does exactly and verifiably what it says.

`test` names the ONE test a mutation is aimed at, and changes the question the
run asks. Without it, scoring is "did the suite go red?" — which `ALL_CAUGHT`
answers, and which is not what 5e needs to know: a mutant can die on a crash, a
timeout, or an assertion about something else entirely, and each is
indistinguishable from the guard biting. Measured cases: a mutant that tripped
`assert r.returncode == 0` on an unbound-variable crash without reaching the
property, and one caught by a 60-second `TimeoutExpired` because an orphaned
process held a pipe open. Both scored as clean kills.

With `test`, a kill means THAT test failed. If it passes while the suite goes
red, the mutation is a SURVIVOR and the detail line names what actually bit —
"caught by the wrong assertion" is a finding, not a pass. The named test is also
required green before the mutation is applied, because a kill credited against
a pin that was already failing measures nothing and the whole-suite baseline
cannot see one red pin.

What stays with the author: whether the mechanism that fired is the mechanism
the spec claims. The harness reports; it never judges that. `_mechanism` on a
mutation is a free-text note for exactly that comparison.

Stdlib only: h-mad scripts are invoked with a bare `python3`.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import signal
import subprocess
import sys
from pathlib import Path


class SpecError(Exception):
    """The spec could not be read or does not describe a runnable mutation set."""


def _load_spec(spec_path: Path) -> dict:
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SpecError(f"cannot read spec: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SpecError(f"spec is not valid JSON: {exc}") from exc

    command = spec.get("command")
    if not isinstance(command, list) or not command or not all(
        isinstance(part, str) for part in command
    ):
        raise SpecError("spec needs a non-empty `command` argv list of strings")
    mutations = spec.get("mutations")
    if not isinstance(mutations, list) or not mutations:
        raise SpecError("spec needs a non-empty `mutations` list")
    for index, mutation in enumerate(mutations):
        missing = [k for k in ("name", "file", "find") if not mutation.get(k)]
        if missing:
            raise SpecError(f"mutation {index} is missing {', '.join(missing)}")
        if "replace" not in mutation:
            raise SpecError(f"mutation {index} ({mutation['name']}) has no `replace`")
        if mutation.get("test") is not None and not isinstance(mutation["test"], str):
            raise SpecError(f"mutation {index} ({mutation['name']}) has a non-string `test`")

    target = spec.get("target_command")
    if target is not None and (
        not isinstance(target, list) or not target
        or not all(isinstance(part, str) for part in target)
    ):
        raise SpecError("`target_command`, when present, must be a non-empty argv list of strings")
    if target is None and any(m.get("test") for m in mutations):
        # Naming a test and giving the harness no way to run one is the kind of
        # half-wired spec that would otherwise silently fall back to whole-suite
        # scoring and report a per-test verdict it never computed.
        raise SpecError("a mutation names a `test` but the spec has no `target_command`")
    return spec


def _restore_file(path: Path, text: str) -> bool:
    """Write `text` back and RE-READ to prove it landed. True iff it did.

    The harness refuses to trust a mutation it has not seen on disk; its own
    restore is held to the same standard. A write can succeed and still not
    persist the bytes — and a half-restored tree silently corrupts every later
    run, which is worse than any result the run could have produced.
    """
    try:
        path.write_text(text, encoding="utf-8")
        return path.read_text(encoding="utf-8") == text
    except OSError:
        return False


def _purge_bytecode(root: Path) -> None:
    """Drop cached bytecode under `root` so the next run reads the source.

    CPython invalidates a `.pyc` on (source mtime, source size). A mutation is
    frequently byte-size-IDENTICAL — swapping one identifier for another of the
    same length, `not x` for `x is None`, a threshold digit — and the harness
    applies it milliseconds after the previous run, inside the same
    filesystem-mtime second. Both invalidation inputs then match and the stale
    bytecode is reused, so the mutant never executes and the run reports
    `survived`: byte-identical to a real coverage gap, and the file on disk is
    genuinely mutated, so the existing did-it-land check passes.

    Measured 2026-08-25 on a same-size mutation to `h_mad_assemble_tdd.py`:
    4 false survivors in 6 trials. Restores are corrupted the same way — the
    next mutation's run can execute the PREVIOUS mutant — so this runs on both
    sides of every scoring run rather than only before it.
    """
    for cached in root.rglob("__pycache__"):
        if not cached.is_dir():
            continue
        for entry in cached.glob("*.pyc"):
            try:
                entry.unlink()
            except OSError:
                pass


def _run(command: list[str], root: Path) -> tuple[bool, str]:
    """(green, output). Anything but exit 0 — including a crash — is red."""
    _purge_bytecode(root)
    try:
        proc = subprocess.run(command, cwd=str(root), capture_output=True, text=True)
    except OSError as exc:
        # The command could not be launched at all. That is red, not green: the
        # safe reading of "I could not measure" is never "the guard is fine".
        return False, f"could not launch: {exc}"
    return proc.returncode == 0, (proc.stdout or "") + (proc.stderr or "")


def _suite_is_green(command: list[str], root: Path) -> bool:
    """True when the command exits 0. Anything else — including a crash — is red."""
    return _run(command, root)[0]


FAILED_LINE = re.compile(r"^FAILED\s+(\S+)", re.MULTILINE)


def _failing_tests(output: str) -> list[str]:
    """Test ids a pytest run reported as FAILED, newest-format best-effort.

    Attribution is reporting, never a verdict: the harness knows no test runner
    and must not start requiring one. Output it cannot parse yields an empty
    list and the caller says so, rather than guessing.
    """
    return FAILED_LINE.findall(output)


def _near_misses(source: str, find: str, limit: int = 3) -> list[str]:
    """Lines closest to the anchor's FIRST line, for an anchor that matched 0 times.

    An anchor drifts far more often because the author's own edits moved the
    line than because the line is gone, and the recovery — re-grepping by hand
    for whatever it became — is the whole cost of the REFUSED verdict. `find`
    is frequently multi-line, so the first line is what gets compared; matching
    the whole block against single lines finds nothing useful.
    """
    needle = find.split("\n", 1)[0].strip()
    if not needle:
        return []
    lines = source.split("\n")
    # Scored per LINE, not per distinct string: an identical line occurring
    # twice is exactly the case an author needs both locations for, and
    # `list.index()` would report the first one twice instead.
    scored = [
        (difflib.SequenceMatcher(None, needle, ln.strip()).ratio(), i)
        for i, ln in enumerate(lines)
        if ln.strip()
    ]
    best = sorted((s for s in scored if s[0] >= 0.6), key=lambda s: (-s[0], s[1]))[:limit]
    return [f"line {i + 1}: {lines[i].strip()[:100]}" for _, i in best]


def _match_lines(source: str, find: str, limit: int = 5) -> list[int]:
    """1-based line numbers where the anchor's first line occurs."""
    needle = find.split("\n", 1)[0]
    return [
        i + 1 for i, ln in enumerate(source.split("\n")) if needle in ln
    ][:limit]


def run_spec(spec_path: Path) -> dict:
    """Apply each mutation in turn, run the command, always restore.

    Returns a result dict. Raises SpecError only when the spec itself is
    unusable — every other outcome is a verdict.
    """
    spec_path = Path(spec_path)
    spec = _load_spec(spec_path)
    root = Path(spec.get("root") or spec_path.parent).resolve()
    command = spec["command"]
    mutations = spec["mutations"]

    target_command = spec.get("target_command")

    result = {
        "verdict": "ALL_CAUGHT",
        "mutations": len(mutations),
        "caught": 0,
        "survived": [],
        "refused": [],
        "restore_verified": True,
        "baseline_green_after": None,
        # Reporting only. `mechanism` answers "which test bit, and was it the
        # one this mutation is about?"; `hints` answers "where did my anchor
        # go?". Neither changes a verdict — the judgement of whether the stated
        # reason matches the mechanism stays with the author.
        "mechanism": {},
        "hints": {},
    }

    # Mutations are scored by "did the suite go red?", which means nothing if it
    # was already red. Checking first turns a whole misleading report into one
    # honest line.
    if not _suite_is_green(command, root):
        result["verdict"] = "BASELINE_NOT_GREEN"
        return result

    # One saved copy per file, taken before anything is touched, so a mutation
    # is always reverted against the original rather than against whatever the
    # previous mutation left behind.
    originals: dict[Path, str] = {}

    def restore_all() -> bool:
        """Put every touched file back. False if any did not verifiably land."""
        results = [_restore_file(path, text) for path, text in originals.items()]
        return all(results)

    def _on_signal(signum, _frame):
        # An interrupted run must not leave a mutated tree behind. Restore, then
        # die with the conventional 128+N so the interrupt is not disguised.
        restore_all()
        sys.exit(128 + signum)

    previous_handlers = {}
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            previous_handlers[sig] = signal.signal(sig, _on_signal)
        except (ValueError, OSError):
            # Not on the main thread, or unsupported. Best-effort: the finally
            # block below is the real guarantee.
            pass

    try:
        for mutation in mutations:
            target = (root / mutation["file"]).resolve()
            try:
                source = target.read_text(encoding="utf-8")
            except OSError as exc:
                result["refused"].append(f"{mutation['name']}: cannot read {mutation['file']} ({exc})")
                continue

            # A mutation may name the single test it is aimed at. Scoring then
            # asks "did THAT test bite?" rather than "did anything go red?",
            # which are different questions: `ALL_CAUGHT` is satisfied by a
            # mutant caught by an unrelated assertion, a crash, or a timeout,
            # and none of those prove the property under test was exercised.
            scoring_command = None
            if target_command and mutation.get("test"):
                scoring_command = list(target_command) + [mutation["test"]]

            hits = source.count(mutation["find"])
            if hits != 1:
                # The assert-landed guard, and the reason this script exists. An
                # anchor matching 0 times mutates nothing and the suite stays
                # green — indistinguishable from a guard that holds. Matching
                # more than once means the harness would have to choose for the
                # author, mutating more than the guard under test.
                result["refused"].append(
                    f"{mutation['name']}: anchor matched {hits} times in "
                    f"{mutation['file']}, expected exactly 1"
                )
                # The verdict is correct and load-bearing either way; what was
                # missing is the recovery, which was a manual re-grep for
                # whatever the author's own edits turned the line into.
                if hits == 0:
                    result["hints"][mutation["name"]] = [
                        f"near miss {h}" for h in _near_misses(source, mutation["find"])
                    ] or ["no near miss found — the anchor may be gone entirely"]
                else:
                    result["hints"][mutation["name"]] = [
                        "first line of the anchor occurs at "
                        + ", ".join(str(n) for n in _match_lines(source, mutation["find"]))
                        + " — narrow the anchor until it is unique"
                    ]
                continue

            # L559: a mutant applied over a red pin scores a kill that means
            # nothing. The whole-suite baseline above cannot see a single pin
            # that is already failing, and a targeted run is cheap enough to
            # check every time.
            if scoring_command is not None and mutation.get("test"):
                pin_green, _ = _run(scoring_command, root)
                if not pin_green:
                    result["refused"].append(
                        f"{mutation['name']}: named test {mutation['test']} was already "
                        f"failing before the mutation, so a kill would measure nothing"
                    )
                    continue

            originals.setdefault(target, source)
            mutated = source.replace(mutation["find"], mutation["replace"])
            target.write_text(mutated, encoding="utf-8")

            # Belt and braces: confirm the bytes on disk actually differ. A
            # write that silently no-ops would otherwise score as a clean run.
            if target.read_text(encoding="utf-8") == source:
                result["refused"].append(
                    f"{mutation['name']}: the mutation did not land on disk"
                )
                target.write_text(source, encoding="utf-8")
                continue

            if scoring_command is not None:
                pin_green, _ = _run(scoring_command, root)
                if not pin_green:
                    result["caught"] += 1
                    result["mechanism"][mutation["name"]] = (
                        f"killed by its named test {mutation['test']}"
                    )
                else:
                    # The named test shrugged. Ask the whole suite what did
                    # notice, because "something else bit" and "nothing bit"
                    # are different findings and only one of them is a hole.
                    suite_green, suite_output = _run(command, root)
                    result["survived"].append(mutation["name"])
                    others = [t for t in _failing_tests(suite_output) if mutation["test"] not in t]
                    if suite_green:
                        result["mechanism"][mutation["name"]] = (
                            f"named test {mutation['test']} passed and so did the "
                            f"whole suite — nothing bites"
                        )
                    else:
                        result["mechanism"][mutation["name"]] = (
                            f"named test {mutation['test']} PASSED but the suite went "
                            f"red elsewhere ({', '.join(others[:3]) or 'unparsed'}) — the "
                            f"mutant is caught by the wrong assertion"
                        )
            else:
                suite_green, suite_output = _run(command, root)
                if suite_green:
                    result["survived"].append(mutation["name"])
                else:
                    result["caught"] += 1
                    killers = _failing_tests(suite_output)
                    result["mechanism"][mutation["name"]] = (
                        "killed by " + ", ".join(killers[:3]) if killers
                        else "killed, but the runner's output named no test (unparsed)"
                    )

            target.write_text(source, encoding="utf-8")
    finally:
        result["restore_verified"] = restore_all()
        for sig, handler in previous_handlers.items():
            try:
                signal.signal(sig, handler)
            except (ValueError, OSError):
                pass

    if not result["restore_verified"]:
        result["verdict"] = "RESTORE_FAILED"
        return result

    # The tree is back; prove it by re-running the suite. A run that leaves the
    # suite red has corrupted the very thing it was measuring, and saying so is
    # more useful than any mutation result it produced.
    result["baseline_green_after"] = _suite_is_green(command, root)
    if not result["baseline_green_after"]:
        result["verdict"] = "RESTORE_FAILED"
        return result

    if result["refused"]:
        result["verdict"] = "REFUSED"
    elif result["survived"]:
        result["verdict"] = "SURVIVED"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H-MAD Phase-5e mutation harness")
    parser.add_argument("spec", type=Path, help="JSON mutation spec")
    args = parser.parse_args(argv)

    label = args.spec.name.split(".")[0] or "unknown"

    try:
        result = run_spec(args.spec)
    except SpecError as exc:
        # Same reasoning as the wire-pin gate's UNREADABLE: the caller's contract
        # is to read the token, so an error announced only on stderr is silence.
        print(f"ERROR: {exc}", file=sys.stderr)
        print("MUTATION: UNREADABLE")
        print(
            "  the mutation spec could not be read, so nothing was measured — an "
            "operational error, not a verdict about any guard "
            "(halt `step5e:mutation_unverified:<module>`)."
        )
        print(f"[H-MAD] {label} mutation UNREADABLE")
        return 2

    verdict = result["verdict"]
    if verdict in {"BASELINE_NOT_GREEN", "RESTORE_FAILED"}:
        print(f"MUTATION: {verdict}")
    else:
        print(
            f"MUTATION: {verdict} mutations={result['mutations']} "
            f"caught={result['caught']} survived={len(result['survived'])} "
            f"refused={len(result['refused'])}"
        )
    mechanism = result.get("mechanism") or {}
    hints = result.get("hints") or {}
    for name in result["survived"]:
        print(f"  survived: {name}")
        if name in mechanism:
            print(f"    mechanism: {mechanism[name]}")
    for entry in result["refused"]:
        print(f"  refused: {entry}")
        name = entry.split(":", 1)[0]
        for hint in hints.get(name, []):
            print(f"    hint: {hint}")
    # Caught mutations carry their killer too. `ALL_CAUGHT` is satisfied by a
    # mutant that died on a crash, a timeout, or an unrelated assertion, and
    # none of those prove the property under test was exercised — so the one
    # judgement the harness must NOT make is printed for the author to make.
    if result["caught"] and mechanism:
        killed = [n for n in mechanism if n not in result["survived"]]
        for name in killed:
            print(f"  caught: {name}")
            print(f"    mechanism: {mechanism[name]}")

    if verdict == "BASELINE_NOT_GREEN":
        print(
            "  the suite was already red before any mutation, so every mutation "
            "would 'fail' and the report would read as a clean sweep. Get to green "
            "first (halt `step5e:mutation_unverified:<module>`)."
        )
    elif verdict == "RESTORE_FAILED":
        print(
            "  the tree was NOT restored to its pre-mutation state — treat the "
            "working tree as untrusted and reset it before doing anything else. "
            "No mutation result from this run is usable."
        )
    elif verdict == "SURVIVED":
        print(
            "  a mutation the suite did not notice is a guard that does not bite: "
            "the behaviour it protects is unenforced, and every later gate is blind "
            "to it. Write the discriminating test before accepting the work "
            "(halt `step5e:mutation_survived:<module>`)."
        )
    elif verdict == "REFUSED":
        print(
            "  a refused mutation measured NOTHING — it is not a pass. An anchor "
            "that matches zero times leaves the guard intact and the suite green, "
            "which is exactly what an enforced guard looks like. Fix the anchor and "
            "re-run (halt `step5e:mutation_unverified:<module>`)."
        )

    print(f"[H-MAD] {label} mutation {verdict}")
    return 0 if verdict in {"ALL_CAUGHT", "SURVIVED"} else 2


if __name__ == "__main__":
    sys.exit(main())
