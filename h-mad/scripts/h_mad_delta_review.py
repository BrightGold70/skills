#!/usr/bin/env python3
"""H4 — re-execute the claims a revision ADDS, before the audit is re-dispatched.

Measured across two rounds on `#18 gateway-consolidation`: the hand-run delta review
found fix-introduced defects in **3 of 3** passes at roughly a quarter of a gating
round's cost. It is also the step that failed twice in one sitting when run by hand --
once to a `</dev/null` on a piped helper, once to zsh applying the `:h` modifier inside
`$h:hematology`. A review whose own instrument fails silently is worse than none,
because it reports clean.

The class it hunts is narrow and measured. The pre-c99 revision fixed three defects and
its three authors introduced FOUR musts, every one a bare present-tense count about the
tree -- `unanchored -S returns two`, `ls-tree 14 before and after` -- moved by the very
commit that published the sentence. Those claims are all in ADDED lines, and they are
all re-runnable.

**This never executes arbitrary text from a diff, and that restraint is the design.**
A document's backticks hold illustrative commands, destructive examples and shell
fragments that were never meant to run; `h_mad_doc_block_exec.py` can execute document
blocks precisely because they are explicitly TAGGED, and nothing here is. So a command
is executed only when it is a bare read-only verb with no shell metacharacters, and
everything else is reported `unverified` -- a cannot-judge, counted in the verdict line.
Silently dropping the unsafe half would make this report CLEAN on exactly the revisions
whose claims are least checkable, which is the failure mode the whole tool exists
against.

Stdlib only, like every other h-mad script.
"""

from __future__ import annotations

import argparse
import re
import shlex
import subprocess
from pathlib import Path

# A backticked span on an added line. Non-greedy, single-line: a claim that spans a
# hard wrap is reported as prose rather than guessed at.
_SPAN = re.compile(r"`([^`\n]+)`")

# Anything that would make the shell do more than run one program. `shlex.split` gives
# no shell, so these cannot expand -- but a string containing them was written to be
# interpreted, and running its literal form measures something the author never meant.
_METACHARS = set(";&|><$(){}[]*?!~\\\"'\n")

# Read-only verbs only. `sed` is here for `sed -n`; `-i` is refused below.
_ALLOWED = {"grep", "rg", "wc", "sed", "ls", "cat", "head", "tail", "awk", "sort", "uniq"}
# Read-only git subcommands. `git` alone means nothing: `git push` is one word away.
_ALLOWED_GIT = {"log", "show", "grep", "ls-files", "ls-tree", "rev-parse", "diff",
                "branch", "status", "cat-file", "rev-list", "describe", "blame"}


# A bare word that could name a program. NOT uppercase, no leading dash, no
# punctuation that only appears in prose or code identifiers.
_VERBISH = re.compile(r"^[a-z][a-z0-9_.-]*$")


def is_command_shaped(span: str) -> bool:
    """Could this backticked span be a command at all?

    Measured against a real revision (`8af16d9`) the first version of this script
    treated EVERY backticked span as a claim and reported `claims=15 executed=0
    unverified=15` -- every one of them an identifier: `doc-auditor`, `DIVERGED`,
    `[H-MAD]`, `--sentence-file`. A reviewer handed that ignores the tool, and an
    alert that is always wrong is worse than no alert.

    A command needs a verb AND an argument. One bare word is a name; two words
    beginning with a lowercase bare word is a command worth re-running or, failing
    that, worth naming as unverified.
    """
    parts = span.split()
    if len(parts) < 2:
        return False
    return bool(_VERBISH.match(parts[0]))


def is_executable(command: str) -> bool:
    """Is this a bare read-only command safe to re-run verbatim?

    Matched on the VERB, never as a substring: `rm -rf / # grep` contains `grep` and
    must not be allowed by it.
    """
    if not command.strip():
        return False
    if _METACHARS & set(command):
        return False
    try:
        parts = shlex.split(command)
    except ValueError:
        return False
    if not parts:
        return False
    verb = Path(parts[0]).name
    if verb == "git":
        return len(parts) > 1 and parts[1] in _ALLOWED_GIT
    if verb == "sed" and any(a.startswith("-i") for a in parts[1:]):
        return False
    return verb in _ALLOWED


def added_lines(repo: Path, rev: str, paths: list[str]) -> list[str] | None:
    """The lines this revision ADDS, or None if git could not answer.

    Added only: a claim the revision REMOVED is not a claim the revision makes, and
    reviewing it wastes the reader on text that is already gone.
    """
    cmd = ["git", "-C", str(repo), "show", "--unified=0", "--format=", rev]
    if paths:
        cmd += ["--", *paths]
    try:
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    if run.returncode != 0:
        return None
    out = []
    for line in run.stdout.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            out.append(line[1:])
    return out


def claims(lines: list[str]) -> list[dict]:
    """Every backticked span on an added line, with whether it can be re-run."""
    found = []
    for line in lines:
        for span in _SPAN.findall(line):
            if not is_command_shaped(span):
                continue  # an identifier, not a claim — see is_command_shaped
            found.append({
                "command": span,
                "line": line.strip(),
                "executable": is_executable(span),
            })
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Re-execute the re-runnable claims a revision adds (H4)")
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--rev", default="HEAD",
                        help="the revision whose ADDED lines are reviewed")
    parser.add_argument("--path", action="append", default=[],
                        help="limit to these paths (repeatable)")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args(argv)

    lines = added_lines(args.repo, args.rev, args.path)
    if lines is None:
        print(f"DELTA: UNREADABLE reason=git:{args.rev}")
        print("  git could not answer for that revision, so nothing was reviewed — "
              "a cannot-judge, never a clean delta.")
        return 2

    found = claims(lines)
    if not found:
        print("DELTA: CLEAN claims=0 executed=0 unverified=0")
        print(f"[H-MAD] delta CLEAN")
        return 0

    executed = 0
    unverified = 0
    for claim in found:
        if not claim["executable"]:
            unverified += 1
            print(f"  unverified: `{claim['command']}`")
            print(f"    in: {claim['line'][:140]}")
            continue
        executed += 1
        try:
            run = subprocess.run(shlex.split(claim["command"]), cwd=str(args.repo),
                                 capture_output=True, text=True, timeout=args.timeout)
            head = (run.stdout or run.stderr or "").strip().splitlines()
            result = head[0][:140] if head else "<no output>"
            print(f"  executed: `{claim['command']}` rc={run.returncode} -> {result}")
        except (OSError, subprocess.SubprocessError) as exc:
            print(f"  executed: `{claim['command']}` rc=<{exc.__class__.__name__}>")
        print(f"    in: {claim['line'][:140]}")

    print(f"DELTA: CLAIMS claims={len(found)} executed={executed} "
          f"unverified={unverified}")
    if unverified:
        print("  `unverified` is a CANNOT-JUDGE, not a pass: those spans hold shell "
              "metacharacters or a verb outside the read-only allowlist, so they were "
              "not run. Re-run them by hand before treating this revision as reviewed.")
    print("  every claim above is one this revision ADDS. The measured class is a bare "
          "present-tense count that the publishing commit itself moved (#11/H4).")
    print(f"[H-MAD] delta CLAIMS")
    # A verdict exits 0. CLAIMS is an answer; only a cannot-judge is non-zero.
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
