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

    MUTATION: ALL_CAUGHT mutations=7 caught=7 survived=0 refused=0 unreadable=0 crash_kills=0 crash_visible=19/19 timeout_kills=0 untargeted=0/7 exit 0
    MUTATION: SURVIVED   mutations=7 caught=5 survived=2 refused=0 unreadable=0 crash_kills=1 crash_visible=12/19 timeout_kills=0 untargeted=0/7 exit 0
    MUTATION: REFUSED    mutations=7 caught=6 survived=0 refused=1 unreadable=0 crash_kills=0 crash_visible=19/19 timeout_kills=1 untargeted=7/7 exit 2
    MUTATION: PRECHECK_FAILED specs=3 drifted=1 unreadable=0               exit 2
    MUTATION: BASELINE_NOT_GREEN                                       exit 2
    MUTATION: RESTORE_FAILED                                           exit 2
    MUTATION: UNREADABLE                                               exit 2
    MUTATION: BUSY holder=8412 age=37s spec=/…/foo.json                exit 2
    MUTATION: TREE_MOVED before=a1b2c3d4e after=f9e8d7c6b inner=ALL_CAUGHT  exit 2
      (HEAD moved while the run was measuring — a sibling session committed into
       the same clone, so the mutations were applied to one tree and scored
       against another. The inner verdict is KEPT and printed.)
      (another run holds this working tree; nothing was applied and nothing
       was measured. `--check-anchors` takes NO lock and keeps working, which
       is why the pre-push hook is unaffected by a run in flight.)
    ANCHORS: ANCHORS_OK specs=17 mutations=243 ok=243 drifted=0 unreadable=0 skipped=1 unclassifiable=0 exit 0
    ANCHORS: ANCHORS_DRIFTED specs=17 mutations=243 ok=240 drifted=2 unreadable=0 skipped=0 unclassifiable=0 exit 2
    ANCHORS: ANCHORS_UNREADABLE specs=17 mutations=243 ok=240 drifted=2 unreadable=1 skipped=0 unclassifiable=0 exit 2
      (also the verdict when unclassifiable>0 — a file that is not JSON at all)
    ANCHORS: ANCHORS_NOTHING_SWEPT specs=0 skipped=1 unclassifiable=1 exit 2

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

A named-test kill is still two events wearing one `1 failed`, and the two
measured cases above are exactly that shape: the guard's assertion bit, or the
mutant CRASHED before the property was reached. `crash_reports` classifies the
scoring run's output structurally — frame lines attributed by basename to the
mutated file, then a terminal exception line — because a bare `Traceback` search
fires on the source of any test whose SUBJECT is a crash (this suite has one:
`test_a_non_utf8_log_does_not_crash` asserts `"Traceback" not in stderr`). Then:

  * **Tier 1 — `SyntaxError` / `IndentationError` / `TabError` in the mutated
    file: REFUSED.** A file that did not parse cannot have exercised a guard, so
    it measured NOTHING. Same reasoning and same category as the collection
    break; the difference is that a script consumed by `subprocess.run` can be
    syntax-broken with pytest's collection fully intact, so the named test RUNS,
    fails on the child's crash, and the collection-break branch never sees it.
  * **Tier 2 — every other exception: ANNOTATED and COUNTED, never refused.**
    The `mechanism:` line carries `(crash: NameError in h_mad_foo.py)` and the
    token line carries `crash_kills=N`. This is deliberately not a refusal: a
    mutation that strips a None-check makes the code raise `AttributeError`, and
    the test asserting the graceful message then fails — there the crash IS the
    property violation. The harness cannot distinguish that from a pre-property
    crash, so it prints the classification and leaves the judgement where the
    `caught:` detail lines already put it — with the author.

Both of those were listed here as permanently unclassified. **Both are now
classified, each in the one direction that can be claimed honestly, and the
reason the old text gave for declining was right about one thing and wrong about
the other.**

  * **The timeout kill** — the second measured case, a 60-second
    `TimeoutExpired`. The old objection stands *as an objection to attribution*:
    the name carries neither `Error` nor `Exception`, and pytest blames the TEST
    file that set the timeout, never the module that hung, so widening
    `_TERMINAL_LINE` would manufacture an attribution wrong by construction. What
    did not follow is that the EVENT is unreportable. `timeout_kill` matches its
    own pattern and returns an UNATTRIBUTED name, published as `timeout_kills=N`
    and never folded into `crash_kills`, whose every entry names a file. It earns
    its own count because it is the kill least likely to be the guard biting: a
    guard that fires returns — it does not hang.
  * **The untargeted branch** (no `test` key). The old reason — "its kill is
    scored against the whole suite, where a traceback may belong to any file" —
    was right about attribution and wrong about LOOKING. `crash_kill` already
    asks only whether a traceback names the file THIS mutation edited, and that
    basename rule is no weaker under a whole-suite run; other files' tracebacks
    are what it discards. So the classification now runs on that branch too. What
    stays true is that an untargeted kill is a weaker measurement, and that is
    now REPORTED — `untargeted=N/M` on the token line — rather than left for a
    reader to discover by opening the spec and counting `test` keys by hand.

The general rule both fixes follow, and the one worth carrying: *unattributable*
and *unreportable* are different. A measurement that cannot say WHICH file can
still say THAT it happened, and publishing the weaker fact beside the count is
strictly better than a silence the reader cannot distinguish from a zero. That is
the same move `crash_visible` made for `crash_kills`.

What still cannot be seen is unchanged: the classifier cannot
see a crash the failing test never SURFACED: `assert r.returncode == 0` with no
message discards the child's stderr, so `crash_kills=0` means "none found",
never "none there". `crash_visible=M/T` on the token line is that caveat made
reportable: T returncode assertions in the files this spec targets, M of which
carry a message and could surface a traceback at all. `crash_kills=0` beside
`crash_visible=19/19` is evidence; beside `12/19` it is a partial reading.

What stays with the author: whether the mechanism that fired is the mechanism
the spec claims. The harness reports; it never judges that. `_mechanism` on a
mutation is a free-text note for exactly that comparison.

Stdlib only: h-mad scripts are invoked with a bare `python3`.
"""
from __future__ import annotations

import argparse
import contextlib
import difflib
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path


class SpecError(Exception):
    """The spec could not be read or does not describe a runnable mutation set."""


def _strip_jsonc(text: str) -> str:
    """Remove `//` and `/* */` comments that sit outside string literals.

    JSONC is the config dialect TypeScript, VS Code and friends write. It is
    never a mutation-spec dialect: `_load_spec` parses with strict ``json``, so
    a spec written with comments could not load even if we accepted it here.
    """
    out: list[str] = []
    i, n = 0, len(text)
    in_string = False
    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < n:
            if text[i + 1] == "/":
                end = text.find("\n", i)
                i = n if end == -1 else end
                continue
            if text[i + 1] == "*":
                end = text.find("*/", i + 2)
                i = n if end == -1 else end + 2
                continue
        out.append(ch)
        i += 1
    return "".join(out)


def classify_spec_file(path: Path) -> tuple[str, str | None]:
    """('spec'|'not-a-spec'|'unclassifiable', detail).

    Directory sweeps see JSON files that are not mutation specs. The classifier
    keys only on the gate `_load_spec` itself needs before mutation validation:
    a non-empty `mutations` list.
    """
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        return "unclassifiable", f"cannot read JSON: {exc}"
    except json.JSONDecodeError as exc:
        # A directory sweep sees config files, not only specs, and a JSONC config
        # (`tsconfig.json` and friends) is not valid strict JSON. Refusing to
        # classify one makes the whole sweep UNREADABLE, which fails the pre-push
        # hook for every commit in the repository -- a real, repo-wide block whose
        # cause is a file that could never have been a spec.
        #
        # Retry with comments removed, and accept the answer ONLY in the direction
        # that cannot hide a corrupted spec: if it now parses and carries no
        # `mutations` list, it is definitively not a spec. A file that parses only
        # after comment-stripping AND carries a `mutations` list stays
        # unclassifiable -- `_load_spec` would reject it anyway, and silence there
        # is exactly the hole the fail-closed default exists to keep shut. A
        # genuinely corrupted spec does not become valid by removing comments, so
        # that path is untouched.
        try:
            relaxed = json.loads(_strip_jsonc(Path(path).read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            return "unclassifiable", f"not valid JSON: {exc}"
        if isinstance(relaxed, dict) and relaxed.get("mutations"):
            return "unclassifiable", f"not valid JSON: {exc}"
        return "not-a-spec", "JSONC config file, no non-empty `mutations` list"

    if not isinstance(data, dict):
        return "not-a-spec", "JSON object has no non-empty `mutations` list"
    # A provenance LEDGER maps every mutation id to the node id that killed it.
    # A feature's closing task legitimately commits one beside the specs, and its
    # rows carry `name` + `test` and no `file`/`find`, because the mutations were
    # applied per task by their own specs. Swept as a spec it fails `_load_spec`
    # for having no `command`, taking the whole sweep to ANCHORS_UNREADABLE --
    # which the pre-push hook blocks on, for every commit in the repository.
    #
    # The ledger must DECLARE itself, and inferring it is not an option that was
    # passed over -- it was tried and is provably wrong. A ledger row and a row
    # of a half-written spec are the same shape, and AC-6.3 pins exactly that
    # case: `{"mutations": [{"name": "has no command"}]}` must classify `spec` so
    # the loader refuses it loudly. A predicate keying on the ABSENCE of
    # `file`/`find` reclassifies that fixture too, which is how a real corrupted
    # spec vanishes from the sweep -- the hole this classifier's fail-closed
    # default exists to keep shut.
    #
    # So the marker is read, never guessed. A `kind` that lies is a visible lie
    # in a committed file, the same standard `codex_status` is held to, rather
    # than an invisible shortcut.
    if data.get("kind") == "ledger":
        return "not-a-spec", "declares `kind: ledger`, not a runnable spec"

    mutations = data.get("mutations")
    if isinstance(mutations, list) and mutations:
        return "spec", None
    return "not-a-spec", "JSON object has no non-empty `mutations` list"


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


def _resolve_root(spec: dict, spec_path: Path) -> Path:
    """The directory a spec's `file` paths are relative to.

    Absolute -> itself. Relative -> resolved against the SPEC's directory, not
    the caller's cwd. Absent -> the spec's directory.
    """
    root_value = spec.get("root")
    if not root_value:
        return spec_path.parent.resolve()

    root = Path(root_value)
    if root.is_absolute():
        return root.resolve()
    return (spec_path.parent / root).resolve()


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
OUTCOME = re.compile(r"(\d+)\s+(passed|failed|skipped|error|errors|xfailed|xpassed)")


def outcome(output: str) -> dict:
    """Counts from a pytest summary. Empty when nothing parseable was printed.

    Scoring on the exit code alone produces two false verdicts, both measured
    2026-08-25:

      * A mutation that breaks collection -- a syntax error, a bad import --
        makes pytest exit 2 before the named test's assertion ever runs, and the
        harness credited that as `killed by its named test`. It proves the code
        breaks when broken, and nothing about the property.
      * `@pytest.mark.skip` exits 0, so the pre-check declared a DISABLED test
        green. The mutant then survives and reads as a missing guard rather than
        as a test that was turned off.

    So the summary is read: a kill requires the test to have RUN and failed, and
    green requires it to have RUN and passed.
    """
    counts = {}
    for number, word in OUTCOME.findall(output):
        counts[word.rstrip("s") if word.startswith("error") else word] = int(number)
    return counts


def ran_and_failed(counts: dict) -> bool:
    return counts.get("failed", 0) > 0


def ran_and_passed(counts: dict) -> bool:
    return (counts.get("passed", 0) > 0
            and not counts.get("failed") and not counts.get("error")
            and not counts.get("skipped"))


def _failing_tests(output: str) -> list[str]:
    """Test ids a pytest run reported as FAILED, newest-format best-effort.

    Attribution is reporting, never a verdict: the harness knows no test runner
    and must not start requiring one. Output it cannot parse yields an empty
    list and the caller says so, rather than guessing.
    """
    return FAILED_LINE.findall(output)


# --- crash-kill VISIBILITY -------------------------------------------------
#
# `crash_kills=0` has two causes with opposite meanings: no mutant died on a
# crash, or one did and the failing assertion never surfaced it. `assert
# r.returncode == 0` with no message discards the child's stderr, so the
# classifier cannot see the traceback and the count reads as absence.
#
# The docstring has said so since the classifier shipped. Prose in a docstring
# is not what a caller greps, and the token line said only `crash_kills=0` —
# so the one consumer that had to know was the one place not told. This closes
# that by MEASURING the blind spot per run and publishing it beside the count.
#
# Scoped to the test files THIS spec targets, not the whole suite: a run's
# blind spot is a property of the rows it actually scored. Measured over the
# repo on 2026-09-14: 452 of 921 returncode assertions carry a message, 49.1%.

def _returncode_assertion_coverage(paths: "set[Path]") -> "tuple[int, int]":
    """(with_message, total) over `assert …returncode…` in `paths`.

    AST, never a regex. A regex that keys on a quote after the comma misses
    `assert r.returncode == 0, r.stdout` — a message that is a NAME, not a
    literal — and under-reports coverage roughly threefold (15% vs 49%,
    measured both ways on this repo before this function was written).
    """
    import ast
    with_msg = total = 0
    for path in sorted(paths):
        try:
            tree = ast.parse(Path(path).read_text(errors="replace"))
        except (OSError, SyntaxError):
            continue          # unreadable is not zero; it simply adds nothing
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assert):
                continue
            if "returncode" not in ast.dump(node.test):
                continue
            total += 1
            if node.msg is not None:
                with_msg += 1
    return with_msg, total


def _spec_test_files(spec: dict, root: "Path") -> "set[Path]":
    """The test files a spec's rows name, resolved against the spec root."""
    out = set()
    for mutation in spec.get("mutations") or []:
        key = mutation.get("test")
        if not isinstance(key, str) or not key:
            continue
        rel = key.split("::", 1)[0]
        candidate = Path(root) / rel
        if candidate.is_file():
            out.add(candidate)
    return out


# --- crash-kill classification -------------------------------------------
#
# A named-test kill is scored on "THAT test failed", which still covers two
# different events wearing one `1 failed`: the guard's assertion bit, or the
# mutant CRASHED before the property was ever reached.
_TRACEBACK_HEADER = "Traceback (most recent call last):"
# pytest prefixes every line of a failure block with `E` plus padding. The
# whitespace is REQUIRED in this pattern: `EOFError:`, `Exception:` and
# `EnvironmentError:` are terminal lines, not markers, and `^\s*E\s*` would eat
# their first letter and classify them as `OFError`.
_PYTEST_MARKER = re.compile(r"^\s*E\s+")
_FRAME_LINE = re.compile(r'^File "([^"]+)", line \d+')
# Dotted names are as real a terminal line as the bare ones:
# `json.decoder.JSONDecodeError: Expecting value` is what this suite's
# subprocess tests actually surface.
_TERMINAL_LINE = re.compile(r"^([\w.]+(?:Error|Exception)): ")
# pytest's own failure footer — `guard.py:9: NameError` — which is the ONLY
# attribution a direct-import failure carries: pytest prints no `Traceback`
# header of its own, so there are no `File "…"` frames to read.
_PYTEST_FOOTER = re.compile(r"^(.+?\.py):\d+: ([\w.]+(?:Error|Exception))$")
# A timeout kill, which `_TERMINAL_LINE` structurally cannot see: the name
# `subprocess.TimeoutExpired` carries neither `Error` nor `Exception`. It is
# matched on its OWN pattern rather than by widening that one, because the two
# findings differ in what they may claim — see `timeout_kill`.
#
# ANCHORED at line start and requiring the `: ` of a terminal exception line,
# exactly as `_TERMINAL_LINE` is, and for the reason `crash_reports` gives in its
# own docstring: a bare search over the output matches any test whose SUBJECT is
# timeouts. That is not hypothetical — the first run of this spec reported
# `timeout_kills=2` against two mutations that never timed out, because the
# tests killing them contain `"subprocess.TimeoutExpired: …"` as a FIXTURE
# STRING and pytest echoes the assertion source into its failure block. The
# leading quote is what the anchor now rejects.
_TIMEOUT_LINE = re.compile(r"^((?:[\w.]+\.)?(?:TimeoutExpired|Timeout)): ")

# Tier 1. `IndentationError` and `TabError` subclass `SyntaxError` but print
# their own names, so all three are listed rather than inferred.
DID_NOT_PARSE = ("SyntaxError", "IndentationError", "TabError")


def crash_reports(output: str) -> list[tuple[str, list[str]]]:
    """Every crash report in a run's output, as (exception type, file basenames).

    A bare `Traceback` search is far too loose to build a verdict on: at least
    one test in this suite asserts on crash-related WORDS as its subject matter
    (`test_a_non_utf8_log_does_not_crash` asserts `"Traceback" not in stderr`),
    and pytest echoes that source line into the failure block. So a report is
    recognised structurally — frame lines, then a terminal exception line — and
    attributed to the files its frames name.

    Three output shapes are handled, all three measured rather than assumed:

      * **subprocess tests** (this suite's dominant shape). The child's stderr
        is embedded in an assertion message, so the `Traceback` header shares a
        line with `AssertionError:` and every line carries pytest's `E ` marker.
      * **a compile-time `SyntaxError`**, which CPython reports with NO
        `Traceback` header at all — just `File "…", line N`, a caret, and the
        terminal line. Requiring a header would leave tier 1, the only tier that
        refuses, unreachable through the shape it exists for.
      * **direct-import tests**, where pytest prints its own `E NameError: …`
        and attributes it only in the footer line.

    What this CANNOT see is a crash the failing test never surfaced. A test
    written `assert r.returncode == 0` with no message discards the child's
    stderr, and its crash kill is indistinguishable from an ordinary assertion
    failure. `crash_kills=0` therefore means "none found", never "none there".
    """
    reports: list[tuple[str, list[str]]] = []
    frames: list[str] = []
    for raw in output.splitlines():
        line = _PYTEST_MARKER.sub("", raw, count=1).strip()

        footer = _PYTEST_FOOTER.match(line)
        if footer:
            # `AssertionError` in a FOOTER is never a crash — it is the shape of a
            # guard's own `assert` firing, which is exactly what a real kill looks
            # like. Counting it inverted the classifier whenever the mutated file
            # WAS a test file: pytest's footer then names that file, `crash_kill`
            # attributes by basename, and every ordinary assertion failure was
            # reported as a crash. Measured over all 92 specs: of 25 crash kills,
            # 13 came from the four specs that mutate `tests/`, and NO spec without
            # a test-targeting mutation reported one — `doc_block_exec_wire.json`
            # read 8 of 8, and all eight were verified real by reading the message
            # each one fails on ("must call dbe.extract exactly once", …).
            #
            # A genuine crash still lands here under its own name — a direct-import
            # `NameError` footer reads `guard.py:9: NameError` — and a child's
            # traceback embedded in an assertion message is recognised by the
            # frames path above, whose terminal line is the real exception. So this
            # narrows exactly one spelling and loses no detection.
            if footer.group(2) != "AssertionError":
                reports.append((footer.group(2), [Path(footer.group(1)).name]))
            frames = []
            continue

        terminal = _TERMINAL_LINE.match(line)
        if terminal:
            if frames:
                reports.append((terminal.group(1), frames))
            frames = []
            # The rest of the line may still open the next report: the headerless
            # SyntaxError arrives as `AssertionError:   File "…", line N`.
            line = line[terminal.end():].lstrip()

        if _TRACEBACK_HEADER in line:
            frames = []
            line = line.split(_TRACEBACK_HEADER, 1)[1].lstrip()

        frame = _FRAME_LINE.match(line)
        if frame:
            frames.append(Path(frame.group(1)).name)
    return reports


def crash_kill(output: str, mutated_file: str) -> str | None:
    """The exception a run crashed with INSIDE `mutated_file`, else None.

    Attribution by basename is the whole difference between a finding and noise:
    a traceback through some other file says nothing about whether this mutation
    reached the property it names.
    """
    target = Path(mutated_file).name
    for exception, files in crash_reports(output):
        if target in files:
            return exception
    return None


def timeout_kill(output: str) -> str | None:
    """The timeout exception name if a run's output shows one, else None.

    This is the second of the two blind spots the module docstring named, and it
    is closed here in the ONE direction that can be closed honestly.

    `crash_kill` answers "did the mutant crash *inside the file I mutated*", and
    its whole value is that basename attribution. A timeout cannot be answered
    that way: pytest attributes `subprocess.TimeoutExpired` to the TEST file
    that called `subprocess.run(..., timeout=…)`, never to the mutated module
    that hung, and the frames in between are the stdlib's. Widening
    `_TERMINAL_LINE` to admit the name would therefore manufacture an attribution
    that is wrong by construction — which is exactly why the docstring declined
    to do it, and that judgement stands.

    What does NOT follow is that the event is unreportable. "Something in this
    run hung until a timeout fired" is knowable without knowing which file hung,
    and it is worth knowing for a reason the other kills are not: a timeout is
    the kill LEAST likely to be the guard biting. An assertion kill is usually
    the property; a crash kill is ambiguous and annotated as such; a timeout kill
    is almost never the property, because a guard that fires returns — it does
    not hang. So this returns an unattributed name and the caller reports it as
    its own count, never folded into `crash_kills`.

    A run whose SUBJECT is timeouts false-positives here unless the match is
    structural, which is the same hazard `crash_reports` documents for the word
    `Traceback` — and this function shipped with a bare `.search()` and was
    caught by its own spec on the first run, reporting `timeout_kills=2` for two
    mutations that never timed out. The killing tests carry
    `"subprocess.TimeoutExpired: …"` as a FIXTURE STRING, and pytest echoes the
    assertion source into its failure block. So the scan is line-based, the
    pytest `E ` marker is stripped first, and the name must open the line and be
    followed by the `: ` of a real terminal exception line. A quoted occurrence
    inside an echoed source line no longer matches.

    The residual cost is bounded in a way the crash case's is not: this count is
    published beside the verdict and changes no verdict, so anything that still
    slips through costs a line of output and never a wrong PASS.
    """
    for raw in output.splitlines():
        line = _PYTEST_MARKER.sub("", raw, count=1).strip()
        match = _TIMEOUT_LINE.match(line)
        if match:
            return match.group(1)
    return None


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


#: Why a self-matching mutation is diagnosed and NOT refused.
#:
#: A backlog row asked for a refusal: "refuse a mutation whose `find` string
#: occurs in its own `replace` text". Calibrated against the specs that already
#: pass, 2026-09-14: **21 of 874 committed mutations** are exactly that shape and
#: every one is a legitimate, caught insertion -- `order = order + order` appended
#: to a sort, `default=False,` added to an argparse line, `name: h-mad` renamed to
#: `name: h-mad-renamed`. A refusal would have rejected all 21 and taken twenty-one
#: working guards offline to prevent a failure mode that is already reported.
#:
#: What is real is the DIAGNOSIS. The incident behind the row was a mutant whose
#: replacement still contained the phrase its assertion greps for, so the mutated
#: tree still matched and the mutation survived for a reason that was a property
#: of the SPEC, not of the code. The harness already catches that empirically --
#: it reports SURVIVED -- and what it could not do was say WHY. Now it can, and
#: the cost of being wrong is a line of text rather than a refused guard.
SELF_MATCHING_NOTE = (
    "self-matching spec: the replacement re-contains the anchor verbatim, so every "
    "substring of the original survives the mutation and any assertion shaped "
    "`assert \"<text>\" in ...` still passes. If a grep-shaped test was expected to "
    "catch this, that is why it did not — the mutation cannot be detected by "
    "containment. Advisory, never a refusal: pure insertions of this shape are "
    "common and usually legitimate (21 of 874 committed mutations, all caught)"
)


def self_matching(find: str, replace: str) -> bool:
    """Does the replacement re-contain its own anchor verbatim?

    Deliberately the whole-string containment test and nothing cleverer. A
    narrower predicate -- "insertion at the end", "the assertion greps for it" --
    needs to know the shape of the test, which this harness does not and must not
    start knowing (`_failing_tests`' docstring makes the same commitment about
    test runners). An empty `find` is not self-matching: it is a spec error the
    anchor check already refuses, and reporting it here as well would put two
    findings on one defect.
    """
    return bool(find) and find in replace


def anchor_status(source: str, find: str) -> tuple[int, list[str]]:
    """How often `find` occurs in `source`, plus recovery hints when that is not 1.

    Extracted so the anchor precheck and the live run cannot drift apart. A
    precheck carrying its own `count(...) != 1` would be a second copy of the
    exact rule this harness exists to enforce, and the first edit to either side
    would make the cheap check disagree with the expensive one — the cheap one
    being the one people would trust, because it is the one they run.
    """
    hits = source.count(find)
    if hits == 1:
        return hits, []
    if hits == 0:
        return hits, [f"near miss {h}" for h in _near_misses(source, find)] or [
            "no near miss found — the anchor may be gone entirely"
        ]
    return hits, [
        "first line of the anchor occurs at "
        + ", ".join(str(n) for n in _match_lines(source, find))
        + " — narrow the anchor until it is unique"
    ]


def precheck_spec(spec_path: Path) -> dict:
    """Anchor-only sweep: does every mutation still match exactly once?

    Applies nothing and runs no command, so it costs a few file reads instead of
    a suite per spec. That is the whole point: a drifted anchor REFUSES, and a
    refusal measures NOTHING — the guard it aims at is unverified while the run
    still exits with a verdict-shaped line. Nothing surfaced that until someone
    paid for a full run of the spec.

    Raises SpecError only when the spec itself is unusable; every other outcome
    is reported per mutation.
    """
    spec_path = Path(spec_path)
    spec = _load_spec(spec_path)
    root = _resolve_root(spec, spec_path)

    result = {
        "spec": str(spec_path),
        "mutations": len(spec["mutations"]),
        "ok": 0,
        "drifted": [],
        "unreadable": [],
        # Advisory only — it never reaches `verdict` below. This is the half of
        # the row that genuinely "needs no execution": you learn a spec cannot be
        # caught by containment from reading it, without paying for a suite run.
        "self_matching": [],
    }

    # One read per file, not per mutation: specs routinely aim a dozen mutations
    # at the same target.
    cache: dict[Path, str] = {}
    for mutation in spec["mutations"]:
        target = (root / mutation["file"]).resolve()
        if target not in cache:
            try:
                cache[target] = target.read_text(encoding="utf-8")
            except OSError as exc:
                result["unreadable"].append(
                    f"{mutation['name']}: cannot read {mutation['file']} ({exc})"
                )
                continue
        if self_matching(mutation["find"], mutation.get("replace", "")):
            result["self_matching"].append(
                {"name": mutation["name"], "file": mutation["file"]}
            )
        hits, hints = anchor_status(cache[target], mutation["find"])
        if hits == 1:
            result["ok"] += 1
        else:
            result["drifted"].append({
                "name": mutation["name"],
                "file": mutation["file"],
                "hits": hits,
                "hints": hints,
            })

    # An unreadable target and a moved anchor are BOTH unverified guards, but they
    # are not the same cannot-judge and the operator's next action differs: restore
    # a file that is gone, versus re-anchor a spec. You cannot re-anchor into a file
    # that does not exist, so UNREADABLE outranks DRIFTED — the same precedence rule
    # that makes REFUSED outrank SURVIVED and the wire-pin gate's UNSHAPED outrank
    # FAIL. The counts stay separate on the summary either way; what J37 was about
    # is that the WORD is the part that gets read.
    result["verdict"] = (
        "ANCHORS_UNREADABLE"
        if result["unreadable"]
        else "ANCHORS_DRIFTED"
        if result["drifted"]
        else "ANCHORS_OK"
    )
    return result


def _sibling_specs(spec_path: Path) -> dict:
    """Specs beside `spec_path`, excluding `spec_path` itself.

    Directory sweeps may see JSON files that are not mutation specs. Reuse the
    same classifier as --check-anchors so "not a spec" is a skip, while a file
    that declares itself a spec is handed to _load_spec/precheck_spec and can
    refuse the run if deeper validation fails.
    """
    spec_path = Path(spec_path).resolve()
    spec_paths = []
    skipped = []
    for sibling in sorted(spec_path.parent.glob("*.json")):
        sibling = sibling.resolve()
        if sibling == spec_path:
            continue
        kind, detail = classify_spec_file(sibling)
        if kind == "spec":
            spec_paths.append(sibling)
        else:
            skipped.append({"path": str(sibling), "reason": detail or kind})
    return {"spec_paths": spec_paths, "skipped": skipped}


# --- tree lock -------------------------------------------------------------
#
# A mutation run and anything else that reads or writes the same working tree
# MEASURE EACH OTHER. The harness rewrites files in place and restores them, so a
# second run -- or a plain `pytest` in another pane, or a sibling session -- sees
# a torn tree and returns a verdict about that rather than about the code.
#
# Measured: a spec was launched while its own anchor lines were still being
# edited and the harness returned REFUSED for an anchor that was fine. That is
# the dangerous shape, because REFUSED is a PLAUSIBLE verdict -- it is exactly
# what a genuinely drifted anchor produces, and nothing at the token tells the
# two apart. The same day, a second session committed into this clone nine
# seconds before a run, moving the suite count by +10 for reasons that were not
# the run's.
#
# So the lock turns a silent wrong measurement into a wait. It is deliberately
# NOT taken by `--check-anchors`, which only reads.


class TreeBusy(Exception):
    """Another mutation run holds this tree. Carries what is known about it."""

    def __init__(self, holder: dict):
        super().__init__(f"tree is held by {holder}")
        self.holder = holder


def _process_alive(pid: int) -> bool:
    """Is `pid` running? EPERM means ALIVE, and that is the load-bearing line.

    `os.kill(pid, 0)` raises `PermissionError` for a process owned by another
    user -- which proves it EXISTS. Reading that as "not alive" is how a live
    holder's lock gets stolen, and it is the same defect this repo already
    recorded for `is_pid_alive` (#40): EPERM is the one answer that must not be
    folded in with ESRCH.
    """
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        # Unknown errno: cannot judge, so do not declare it dead.
        return True
    return True


def _git_head(root: Path) -> str | None:
    """The commit this tree is on, or None when there is no repo to ask.

    None is NOT "unchanged": every caller compares two reads and only acts when
    BOTH are present and differ, so a tree with no git (every tmp-path spec in the
    suite) is never reported as having moved. The inverse — treating an
    unavailable read as a change — would refuse every run in a non-repo.
    """
    try:
        r = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() or None if r.returncode == 0 else None


def _lock_path(root: Path) -> Path:
    """One lock per WORKING TREE, not per spec root.

    Two specs rooted at different sub-directories of one repo still write the
    same tree, so a root-keyed lock would let exactly the collision this exists
    to stop. Resolve the git toplevel and key on that; fall back to the root
    itself when there is no repo (every tmp-path spec in the suite).
    """
    try:
        top = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=10,
        )
        if top.returncode == 0 and top.stdout.strip():
            return Path(top.stdout.strip()) / ".h-mad" / "mutation.lock"
    except (OSError, subprocess.SubprocessError):
        pass
    return root / ".h-mad" / "mutation.lock"


def _read_holder(path: Path) -> dict:
    """Who holds the lock. An unreadable lock is `unparseable`, never `free`.

    `I could not read it` and `nobody holds it` lead to opposite correct actions
    -- wait versus proceed -- so they must not produce the same value. A corrupt
    lock therefore BLOCKS and the message names the file to delete, which is
    recoverable by a human in one command; silently stealing it is not
    recoverable at all, because the run it interrupts reports a plausible
    verdict.
    """
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"pid": None, "spec": None, "started": None, "unparseable": True}


@contextlib.contextmanager
def tree_lock(root: Path, spec_path: Path):
    """Hold the tree for the duration of a run, or raise `TreeBusy`.

    A lock whose holder is gone is STALE and is taken -- a crashed run must not
    wedge the repo forever -- but only when the holder could be identified and
    proven dead. Unparseable, or alive, blocks.
    """
    path = _lock_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({
        "pid": os.getpid(),
        "spec": str(spec_path),
        "root": str(root),
        "started": time.time(),
    })
    while True:
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            holder = _read_holder(path)
            pid = holder.get("pid")
            if holder.get("unparseable") or not isinstance(pid, int) or _process_alive(pid):
                holder["lock"] = str(path)
                raise TreeBusy(holder)
            # Stale. Clear it and retry ONCE through the loop rather than
            # writing over it: two runs can reach this point together, and the
            # O_EXCL retry is what decides between them instead of last-write.
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            continue
        try:
            with os.fdopen(fd, "w") as fh:
                fh.write(payload)
            break
        except OSError:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            raise
    try:
        yield path
    finally:
        # Only release a lock that is still OURS. A stale-take by a third run
        # would otherwise be deleted here by the run that had already lost it.
        try:
            if _read_holder(path).get("pid") == os.getpid():
                path.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            pass


def _run_spec_holding_the_tree(
    spec_path: Path, spec: dict | None = None, root: Path | None = None
) -> dict:
    """Apply each mutation in turn, run the command, always restore.

    Returns a result dict. Raises SpecError only when the spec itself is
    unusable — every other outcome is a verdict.

    `spec`/`root` are passed in by `run_spec`, which has already resolved both to
    take the tree lock. Re-deriving them here would be a THIRD `_resolve_root`
    call, and `test_precheck_and_run_share_the_root_resolver` counts those — it
    caught exactly that when the lock was first wired. They stay optional so a
    direct call still works.
    """
    spec_path = Path(spec_path)
    spec = _load_spec(spec_path) if spec is None else spec
    root = _resolve_root(spec, spec_path) if root is None else root
    command = spec["command"]
    mutations = spec["mutations"]

    target_command = spec.get("target_command")
    siblings = _sibling_specs(spec_path)
    precheck = {"swept": len(siblings["spec_paths"]), "skipped": siblings["skipped"]}

    result = {
        "verdict": "ALL_CAUGHT",
        "mutations": len(mutations),
        "caught": 0,
        "survived": [],
        "refused": [],
        # A SUBSET of `caught`, never a verdict of its own: a caught mutation
        # whose named test failed on a traceback out of the mutated file. Tier 2
        # is printed for the author, not acted on.
        "crash_kills": 0,
        # Also a SUBSET of `caught`, and deliberately NOT folded into
        # `crash_kills`: a timeout is unattributed by construction (pytest blames
        # the test file that set the timeout, not the module that hung), while
        # every `crash_kills` entry names the mutated file. Merging them would
        # put an unattributed count inside an attributed one.
        #
        # It earns its own line because it is the kill least likely to be the
        # guard biting — a guard that fires RETURNS, it does not hang — so a
        # non-zero here is a prompt to go and look, not a reassurance.
        "timeout_kills": 0,
        # How many of this run's mutations were scored WITHOUT a `test` key, and
        # therefore against the whole suite rather than against a named pin. Not
        # a fault and not a subset of anything — a measurement of how much of
        # the score rests on the weaker question ("did the suite go red?")
        # instead of the stronger one ("did THAT test bite?").
        #
        # Published for the same reason `crash_visible` is: the old docstring
        # said untargeted rows were "not classified at all", which was true and
        # invisible. A reader could only discover it by opening the spec and
        # counting `test` keys by hand.
        "untargeted": 0,
        # The DENOMINATOR for `crash_kills`. Computed once per run over the
        # test files this spec's rows name: how many of their returncode
        # assertions carry a message and could therefore surface a traceback
        # at all. Without it `crash_kills=0` is a bare count whose two causes
        # — nothing crashed, versus a crash nothing surfaced — are spelled the
        # same way.
        "crash_visible": "{}/{}".format(*_returncode_assertion_coverage(
            _spec_test_files(spec, root))),
        "restore_verified": True,
        "baseline_green_after": None,
        # Reporting only. `mechanism` answers "which test bit, and was it the
        # one this mutation is about?"; `hints` answers "where did my anchor
        # go?". Neither changes a verdict — the judgement of whether the stated
        # reason matches the mechanism stays with the author.
        "mechanism": {},
        "hints": {},
        "precheck": precheck,
        "drifted": [],
        "unreadable": [],
    }

    drifted_specs = []
    unreadable_specs = []
    for sibling_path in siblings["spec_paths"]:
        try:
            sibling = _load_spec(sibling_path)
            sibling_root = _resolve_root(sibling, sibling_path)
            sibling_precheck = precheck_spec(sibling_path)
        except SpecError as exc:
            unreadable_specs.append({
                "spec": sibling_path.name,
                "root": str(sibling_path.parent.resolve()),
                "error": str(exc),
            })
            continue

        if sibling_precheck["drifted"]:
            drifted_specs.append({
                "spec": sibling_path.name,
                "root": str(sibling_root),
                "mutations": [
                    {
                        "name": entry["name"],
                        "hits": entry["hits"],
                        "hints": entry["hints"],
                    }
                    for entry in sibling_precheck["drifted"]
                ],
            })
        if sibling_precheck["unreadable"]:
            unreadable_specs.append({
                "spec": sibling_path.name,
                "root": str(sibling_root),
                "error": "; ".join(sibling_precheck["unreadable"]),
            })
    if drifted_specs or unreadable_specs:
        return {
            "verdict": "PRECHECK_FAILED",
            "precheck": precheck,
            "drifted": drifted_specs,
            "unreadable": unreadable_specs,
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

            hits, hint_lines = anchor_status(source, mutation["find"])
            if hits != 1:
                # The assert-landed guard, and the reason this script exists. An
                # anchor matching 0 times mutates nothing and the suite stays
                # green — indistinguishable from a guard that holds. Matching
                # more than once means the harness would have to choose for the
                # author, mutating more than the guard under test.
                result["refused"].append(
                    f"{mutation['name']}: spec you ran drifted: anchor matched {hits} times in "
                    f"{mutation['file']}, expected exactly 1"
                )
                # The verdict is correct and load-bearing either way; what was
                # missing is the recovery, which was a manual re-grep for
                # whatever the author's own edits turned the line into.
                result["hints"][mutation["name"]] = hint_lines
                continue

            # L559: a mutant applied over a red pin scores a kill that means
            # nothing. The whole-suite baseline above cannot see a single pin
            # that is already failing, and a targeted run is cheap enough to
            # check every time.
            if scoring_command is not None and mutation.get("test"):
                _, pin_output = _run(scoring_command, root)
                counts = outcome(pin_output)
                if not ran_and_passed(counts):
                    why = ("was skipped" if counts.get("skipped")
                           else "did not run" if not counts
                           else "was already failing")
                    result["refused"].append(
                        f"{mutation['name']}: named test {mutation['test']} {why} "
                        f"before the mutation ({counts or 'no summary'}), so a kill "
                        f"would measure nothing"
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
                pin_green, pin_output = _run(scoring_command, root)
                counts = outcome(pin_output)
                if not pin_green and not ran_and_failed(counts):
                    # Red, but the named test never reached its assertion: the
                    # mutant broke collection. That proves the code breaks when
                    # broken and nothing about the property, so it measured
                    # NOTHING -- a refusal, not a kill.
                    result["refused"].append(
                        f"{mutation['name']}: the run went red without {mutation['test']} "
                        f"failing ({counts or 'no summary'}) — the mutation broke collection "
                        f"rather than the property"
                    )
                elif not pin_green:
                    # The named test ran and failed. That is still two different
                    # events wearing one `1 failed`: the guard's assertion bit,
                    # or the MUTANT CRASHED before the property was reached.
                    crash = crash_kill(pin_output, mutation["file"])
                    basename = Path(mutation["file"]).name
                    if crash in DID_NOT_PARSE:
                        # Tier 1, and the same reasoning as the collection break
                        # above: a file that did not PARSE cannot have exercised
                        # any guard, so it measured NOTHING rather than the
                        # property. Certainty is total here, so this refuses.
                        result["refused"].append(
                            f"{mutation['name']}: {mutation['test']} failed on a "
                            f"{crash} in {basename} — the mutated file did not parse, "
                            f"so it cannot have exercised the guard; like a broken "
                            f"collection this measured NOTHING rather than the property"
                        )
                    else:
                        # Tier 2: annotate and count, never refuse. A mutation
                        # that strips a None-check makes the code raise
                        # `AttributeError`, and the test asserting the graceful
                        # message then fails — there the crash IS the property
                        # violation. The harness cannot tell that from a
                        # pre-property crash, and the author is already the one
                        # who settles that.
                        result["caught"] += 1
                        if crash:
                            result["crash_kills"] += 1
                            detail = f" (crash: {crash} in {basename})"
                        else:
                            detail = f" (assertion: no traceback from {basename})"
                        # A timeout is a THIRD mechanism, not a flavour of the
                        # other two, and it is checked independently of `crash`
                        # for that reason: the run can carry both a traceback in
                        # the mutated file and a timeout, and collapsing them
                        # would hide whichever was checked second.
                        timeout = timeout_kill(pin_output)
                        if timeout:
                            result["timeout_kills"] += 1
                            detail += (
                                f" (timeout: {timeout} — unattributed; a guard that "
                                f"fires returns, so this is unlikely to be the property)"
                            )
                        result["mechanism"][mutation["name"]] = (
                            f"killed by its named test {mutation['test']}{detail}"
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
                    # A survivor is where this diagnosis earns its keep: the
                    # harness has just reported "nothing bites", which is
                    # byte-identical to a real coverage gap, and the spec itself
                    # may be the reason. Appended to the mechanism rather than
                    # printed separately so the two never drift apart in a log.
                    if self_matching(mutation["find"], mutation.get("replace", "")):
                        result["mechanism"][mutation["name"]] += f" — {SELF_MATCHING_NOTE}"
            else:
                # The UNTARGETED branch — the first of the two blind spots the
                # module docstring named. It used to score a kill and stop, with
                # no crash or timeout classification at all, on the reasoning
                # that a whole-suite traceback "may belong to any file".
                #
                # That reasoning is right about ATTRIBUTION and was wrong about
                # LOOKING. `crash_kill` already answers the narrow question —
                # does a traceback name the file THIS mutation edited — and its
                # basename rule is no weaker here than in the targeted branch,
                # because the question does not mention the test. What a
                # whole-suite run adds is other files' tracebacks, which that
                # same rule discards. So the classification runs here too, and a
                # crash that names the mutated file is counted rather than
                # silently folded into `caught`.
                #
                # What stays TRUE from the old comment: an untargeted kill is
                # still a weaker measurement, because the killer may be any test.
                # That is now reported as its own count instead of being left for
                # the reader to infer from the spec file.
                result["untargeted"] += 1
                suite_green, suite_output = _run(command, root)
                if suite_green:
                    result["survived"].append(mutation["name"])
                    # The untargeted branch carried NO mechanism line at all, so
                    # an untargeted survivor printed its name and nothing else.
                    # This is the one thing the harness can say about it without
                    # knowing which test should have bitten.
                    if self_matching(mutation["find"], mutation.get("replace", "")):
                        result["mechanism"][mutation["name"]] = SELF_MATCHING_NOTE
                else:
                    result["caught"] += 1
                    killers = _failing_tests(suite_output)
                    mechanism = (
                        "killed by " + ", ".join(killers[:3]) if killers
                        else "killed, but the runner's output named no test (unparsed)"
                    )
                    crash = crash_kill(suite_output, mutation["file"])
                    if crash:
                        result["crash_kills"] += 1
                        mechanism += f" (crash: {crash} in {Path(mutation['file']).name})"
                    timeout = timeout_kill(suite_output)
                    if timeout:
                        result["timeout_kills"] += 1
                        mechanism += (
                            f" (timeout: {timeout} — unattributed; a guard that "
                            f"fires returns, so this is unlikely to be the property)"
                        )
                    result["mechanism"][mutation["name"]] = mechanism

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


def _check_anchors(spec_paths: list[Path]) -> int:
    """Print an anchor sweep over every spec. 0 iff every anchor still matches once."""
    specs = ok = drifted = unreadable = mutations = skipped = unclassifiable = 0
    for spec_path in spec_paths:
        kind, detail = classify_spec_file(spec_path)
        if kind == "not-a-spec":
            skipped += 1
            print(f"ANCHORS: {spec_path.name} SKIPPED not-a-spec — {detail}")
            continue
        if kind == "unclassifiable":
            unclassifiable += 1
            print(f"ANCHORS: {spec_path.name} UNCLASSIFIABLE — {detail}")
            continue

        try:
            result = precheck_spec(spec_path)
        except SpecError as exc:
            # One unusable spec must not abort the sweep: the specs after it are
            # exactly the ones whose drift would then go unreported.
            specs += 1
            unreadable += 1
            print(f"ANCHORS: {spec_path.name} UNREADABLE — {exc}")
            continue

        specs += 1
        mutations += result["mutations"]
        ok += result["ok"]
        drifted += len(result["drifted"])
        unreadable += len(result["unreadable"])

        head = "ok" if result["verdict"] == "ANCHORS_OK" else "DRIFTED"
        print(f"ANCHORS: {spec_path.name} {head} ok={result['ok']}/{result['mutations']}")
        for entry in result["drifted"]:
            print(
                f"  drifted: {entry['name']} :: {entry['file']} :: "
                f"hits={entry['hits']}, expected exactly 1"
            )
            for hint in entry["hints"]:
                print(f"    hint: {hint}")
        for entry in result["unreadable"]:
            print(f"  unreadable: {entry}")
        # Printed as a per-spec DETAIL line, never as a summary field. The
        # `ANCHORS:`/`MUTATION:` summary lines are parsed by exact string in the
        # suite and by an ordered substring `case` in the pre-push hook whose
        # default arm ALLOWS the push, so a new word there is a coordinated
        # release; a detail line costs nobody anything.
        # One header per spec, then the names. The note is four lines long and a
        # spec routinely has several of these; repeating it per mutation buries
        # the drift and unreadable findings above it, which are the ones that
        # actually stop a run.
        flagged = result.get("self_matching", [])
        if flagged:
            print(f"  self-matching: {len(flagged)} — {SELF_MATCHING_NOTE}")
            for entry in flagged:
                print(f"    mutation: {entry['name']} :: {entry['file']}")

    if specs == 0:
        verdict = "ANCHORS_NOTHING_SWEPT"
        print(
            f"ANCHORS: {verdict} specs=0 skipped={skipped} "
            f"unclassifiable={unclassifiable}"
        )
        print(f"[H-MAD] anchors {verdict}")
        return 2

    # An unparseable file rides the UNREADABLE verdict rather than taking a word
    # of its own: the consuming pre-push hook scores verdicts with an ordered
    # substring `case` whose default arm ALLOWS the push, so a new word would be
    # silently non-blocking there. `unclassifiable=` on the summary keeps the two
    # causes distinguishable without a coordinated release.
    verdict = (
        "ANCHORS_UNREADABLE" if unreadable or unclassifiable
        else "ANCHORS_DRIFTED" if drifted
        else "ANCHORS_OK"
    )
    print(
        f"ANCHORS: {verdict} specs={specs} mutations={mutations} "
        f"ok={ok} drifted={drifted} unreadable={unreadable} "
        f"skipped={skipped} unclassifiable={unclassifiable}"
    )
    if unclassifiable:
        print(
            "  a file under a swept glob that is not JSON at all is a broken spec "
            "until proven otherwise — it judged nothing, so this is not a clean "
            "anchor check. Fix it, or stop matching it with the glob. (A file that "
            "IS valid JSON but declares no mutations is reported SKIPPED not-a-spec "
            "and never blocks.)"
        )
    if unreadable:
        print(
            "  a spec whose TARGET FILE cannot be read aims at something that is no "
            "longer there, so its guard is unverified and it cannot be re-anchored "
            "until the file is restored — fix that before the drifted specs below "
            "(halt `step5e:mutation_unverified:<module>`)."
        )
    if verdict == "ANCHORS_DRIFTED":
        print(
            "  a drifted anchor mutates nothing, so its run REFUSES and the guard "
            "it aims at is unverified — re-anchor before trusting any verdict from "
            "that spec (halt `step5e:mutation_unverified:<module>`)."
        )
    print(f"[H-MAD] anchors {verdict}")
    return 0 if verdict == "ANCHORS_OK" else 2



def run_spec(spec_path: Path) -> dict:
    """`_run_spec_holding_the_tree`, serialised against other runs on this tree."""
    spec_path = Path(spec_path)
    spec = _load_spec(spec_path)
    root = _resolve_root(spec, spec_path)
    try:
        with tree_lock(root, spec_path):
            # The lock serialises OTHER MUTATION RUNS. It cannot stop a sibling
            # session committing into the same clone, and that is not
            # hypothetical: `4915206` landed in the middle of a full-suite run
            # here on 2026-09-14, moving the count by +10 for reasons that were
            # not the run's. A verdict measured across a commit is a statement
            # about a tree that no longer exists.
            before = _git_head(root)
            result = _run_spec_holding_the_tree(spec_path, spec=spec, root=root)
            after = _git_head(root)
            # BOTH present AND different. An unavailable read is not a change —
            # otherwise every tmp-path spec in the suite would refuse.
            if before and after and before != after:
                return {
                    "verdict": "TREE_MOVED",
                    "head_before": before,
                    "head_after": after,
                    # Kept, not discarded: it is still the most informative thing
                    # anyone has about those mutations, and throwing it away would
                    # make the honest verdict cost a whole re-run to look at.
                    "inner": result,
                }
            return result
    except TreeBusy as busy:
        return {"verdict": "BUSY", "holder": busy.holder}


def _print_skipped_precheck_entries(result: dict) -> None:
    for entry in result.get("precheck", {}).get("skipped", []):
        print(f"  skipped: {entry['path']}: {entry['reason']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H-MAD Phase-5e mutation harness")
    parser.add_argument(
        "spec", type=Path, nargs="+",
        help="JSON mutation spec (exactly one to run; several with --check-anchors)",
    )
    parser.add_argument(
        "--check-anchors", action="store_true",
        help="check every mutation's anchor still matches exactly once; "
             "applies nothing and runs no tests",
    )
    args = parser.parse_args(argv)

    if args.check_anchors:
        return _check_anchors(args.spec)
    if len(args.spec) != 1:
        # The run applies mutations and restores them; widening it to N specs
        # silently would multiply that blast radius for a flag that was only
        # ever meant to widen the read-only sweep.
        parser.error("a mutation run takes exactly one spec; use --check-anchors to sweep several")
    args.spec = args.spec[0]

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
    if verdict == "TREE_MOVED":
        inner = result.get("inner") or {}
        print(
            f"MUTATION: TREE_MOVED before={result['head_before'][:9]} "
            f"after={result['head_after'][:9]} inner={inner.get('verdict', 'unknown')}"
        )
        print(
            "  the working tree was COMMITTED INTO while this run was measuring it. "
            "Another session in the same clone moved HEAD, so the mutations were "
            "applied to one tree and scored against another, and the inner verdict "
            "above is a statement about a tree that no longer exists."
        )
        print(
            "  Nothing here is a finding about any guard. Re-run on a settled tree; "
            "if the other session is still working, wait for it rather than "
            "re-running into the same race "
            "(halt `step5e:mutation_unverified:<module>`)."
        )
        print(f"[H-MAD] {label} mutation TREE_MOVED")
        return 2
    if verdict == "BUSY":
        holder = result["holder"]
        pid = holder.get("pid")
        started = holder.get("started")
        age = f"{time.time() - started:.0f}s" if isinstance(started, (int, float)) else "unknown"
        print(
            f"MUTATION: BUSY holder={pid if pid is not None else 'unparseable'} "
            f"age={age} spec={holder.get('spec') or 'unknown'}"
        )
        print(
            "  another mutation run holds this working tree. A run rewrites files in "
            "place, so a second one measures a TORN tree and returns a verdict about "
            "that — REFUSED for an anchor that is fine, which is indistinguishable "
            "from real drift at the token. Nothing was measured; wait for the holder."
        )
        print(
            f"  if you are certain no run is in flight, delete {holder.get('lock')} "
            "— an unparseable lock is never stolen automatically, because "
            "'I could not read it' is not 'nobody holds it' "
            "(halt `step5e:mutation_unverified:<module>`)."
        )
        print(f"[H-MAD] {label} mutation BUSY")
        return 2
    if verdict in {"BASELINE_NOT_GREEN", "RESTORE_FAILED"}:
        print(f"MUTATION: {verdict}")
    elif verdict == "PRECHECK_FAILED":
        print(
            f"MUTATION: {verdict} specs={result['precheck']['swept']} "
            f"drifted={len(result['drifted'])} "
            f"unreadable={len(result['unreadable'])}"
        )
    else:
        print(
            f"MUTATION: {verdict} mutations={result['mutations']} "
            f"caught={result['caught']} survived={len(result['survived'])} "
            f"refused={len(result['refused'])} "
            # `refused` has five causes and one remedy, so splitting the VERDICT
            # would be worse than the disease; what the operator lacked is which
            # cause, and an unreadable target is the one whose next action differs
            # — restore a file, not re-anchor a spec (J37).
            f"unreadable={sum(1 for e in result['refused'] if 'cannot read' in e)} "
            # Appended LAST on purpose: `crash_kills` is a subset of `caught`,
            # not a new outcome, and every existing consumer parses this line by
            # substring from the left. Growing it at the end leaves those reads
            # intact; inserting anywhere earlier would break them silently.
            f"crash_kills={result.get('crash_kills', 0)}"
            # Appended after `crash_kills` for the same reason it was:
            # left-to-right substring readers stay intact. `m/t` is how
            # many of the targeted files' returncode assertions could
            # have surfaced a crash at all — so `crash_kills=0` is never
            # again readable as "none there" without its own denominator.
            f" crash_visible={result.get('crash_visible', '?/?')}"
            # Appended after both, and for the third time the same reason:
            # left-to-right substring readers stay intact.
            #
            # `timeout_kills` is the other half of `crash_kills` — a kill by
            # hang rather than by traceback — kept separate because it is
            # unattributed where `crash_kills` names a file.
            #
            # `untargeted` closes the last silent gap on this line. Every other
            # token describes rows scored against a NAMED test; this one says
            # how many were not, i.e. how much of the verdict rests on "did the
            # suite go red?" rather than "did that test bite?". `ALL_CAUGHT
            # mutations=12 untargeted=12` and `… untargeted=0` are very
            # different reports and used to print identically.
            f" timeout_kills={result.get('timeout_kills', 0)}"
            f" untargeted={result.get('untargeted', 0)}/{result.get('mutations', 0)}"
        )
    _print_skipped_precheck_entries(result)
    mechanism = result.get("mechanism") or {}
    hints = result.get("hints") or {}
    for name in result.get("survived", []):
        print(f"  survived: {name}")
        if name in mechanism:
            print(f"    mechanism: {mechanism[name]}")
    for entry in result.get("refused", []):
        print(f"  refused: {entry}")
        name = entry.split(":", 1)[0]
        for hint in hints.get(name, []):
            print(f"    hint: {hint}")
    for entry in result.get("drifted", []):
        print(f"  drifted: {entry['spec']} root {entry['root']}")
        for mutation in entry["mutations"]:
            print(
                f"    mutation: {mutation['name']} "
                f"hits={mutation['hits']}, expected exactly 1"
            )
            for hint in mutation["hints"]:
                print(f"      hint: {hint}")
    for entry in result.get("unreadable", []):
        print(f"  unreadable: {entry['spec']} root {entry['root']}: {entry['error']}")
    # Caught mutations carry their killer too. `ALL_CAUGHT` is satisfied by a
    # mutant that died on a crash, a timeout, or an unrelated assertion, and
    # none of those prove the property under test was exercised — so the one
    # judgement the harness must NOT make is printed for the author to make.
    if result.get("caught") and mechanism:
        killed = [n for n in mechanism if n not in result.get("survived", [])]
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
    elif verdict == "PRECHECK_FAILED":
        print(
            "  a sibling precheck failed before mutation, so nothing was measured. "
            "Fix the sibling spec and re-run "
            "(halt `step5e:mutation_unverified:<module>`)."
        )

    print(f"[H-MAD] {label} mutation {verdict}")
    return 0 if verdict in {"ALL_CAUGHT", "SURVIVED"} else 2


if __name__ == "__main__":
    sys.exit(main())
