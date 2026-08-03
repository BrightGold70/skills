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
      "mutations": [
        {"name": "drop the allowlist", "file": "src/gate.py",
         "find": "<exact text>", "replace": ""}
      ]
    }

`command` is an argv list rather than a shell string on purpose: a shell string
would make the harness's own behaviour depend on quoting, and this tool's whole
value is that it does exactly and verifiably what it says.

Stdlib only: h-mad scripts are invoked with a bare `python3`.
"""
from __future__ import annotations

import argparse
import json
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


def _suite_is_green(command: list[str], root: Path) -> bool:
    """True when the command exits 0. Anything else — including a crash — is red."""
    try:
        return subprocess.run(
            command, cwd=str(root), capture_output=True, text=True
        ).returncode == 0
    except OSError:
        # The command could not be launched at all. That is red, not green: the
        # safe reading of "I could not measure" is never "the guard is fine".
        return False


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

    result = {
        "verdict": "ALL_CAUGHT",
        "mutations": len(mutations),
        "caught": 0,
        "survived": [],
        "refused": [],
        "restore_verified": True,
        "baseline_green_after": None,
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

            if _suite_is_green(command, root):
                result["survived"].append(mutation["name"])
            else:
                result["caught"] += 1

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
    for name in result["survived"]:
        print(f"  survived: {name}")
    for entry in result["refused"]:
        print(f"  refused: {entry}")

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
