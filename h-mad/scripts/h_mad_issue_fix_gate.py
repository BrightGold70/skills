#!/usr/bin/env python3
"""Gate the `file-issue-then-fix-under-TDD` linkage.

The loop this guards ran 14 times in a single session with an identical shape:
measure something, file an issue carrying the measurement, write ONE failing test
file per issue, fix it, close the issue with a `Closes #N` trailer.

What breaks in that loop is never the fixing. It is the **linkage** — an issue
fixed with no test naming it, a test landed with no trailer closing the issue, or
(worst, because it is invisible) a test whose connection to the measurement lives
only in the author's head. Six weeks later nothing on disk says which observation
the test exists to pin, and the test looks arbitrary enough to delete.

So this gate answers exactly one question: *is issue N tied to a test and to a
closing trailer?* It deliberately does not file, close, or read issues.
`invariants.base.md` §"No new external dependency" forbids the skill acquiring a
new CLI, and `gh` is not among its dependencies. `--suggest` PRINTS a `gh`
command for the operator, which is not a dependency; shelling out to it would be.

Verdict discipline, per `invariants.base.md` §"Audit-gate signal discipline":
PASS/FAIL is an `ISSUEFIX:` stdout token with **exit 0**. A non-zero exit is
reserved for a genuine operational error (here: no usable git repository), so an
orchestrator can tell "the work is not linked" from "I could not check".

Usage:
    h_mad_issue_fix_gate.py --issue 42 --test tests/test_thing.py [--base main]
                            [--repo-root .] [--suggest]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

TOKEN = "ISSUEFIX"
# GitHub honours these (case-insensitively) to auto-close on merge. Accepting only
# one of them would fail a correctly-closed issue.
_CLOSING_WORDS = ("close", "closes", "closed", "fix", "fixes", "fixed",
                  "resolve", "resolves", "resolved")


def _issue_re(number: str) -> re.Pattern[str]:
    """`#N` on a boundary. A prefix match would let #42's test satisfy #4."""
    return re.compile(rf"#{re.escape(number)}(?!\d)")


def _closing_re(number: str) -> re.Pattern[str]:
    words = "|".join(_CLOSING_WORDS)
    return re.compile(rf"\b(?:{words})\s+#{re.escape(number)}(?!\d)", re.IGNORECASE)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True)


def _commit_messages(repo: Path, base: str) -> list[str]:
    """Messages of commits on HEAD not reachable from `base`.

    Falls back to the whole history in the two cases where the RANGE, not the
    work, is what came up empty:

    * `base` does not resolve -- a branch cut from a ref that no longer exists.
    * `base..HEAD` is empty because base IS HEAD -- the fix landed directly on
      the base branch, which is the normal shape for a small repo.

    Reporting `trailer_missing` from an empty range would be a verdict about the
    range rather than about the work, and the trailer is usually sitting right
    there in the commit the range excluded.
    """
    def _messages(rng: str) -> list[str]:
        out = _git(repo, "log", "--format=%B%x00", rng)
        if out.returncode != 0:
            return []
        return [m for m in out.stdout.split("\x00") if m.strip()]

    if _git(repo, "rev-parse", "--verify", "--quiet", base).returncode != 0:
        return _messages("HEAD")
    return _messages(f"{base}..HEAD") or _messages("HEAD")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--issue", required=True)
    ap.add_argument("--test", required=True,
                    help="path to the test file pinning this issue, relative to --repo-root")
    ap.add_argument("--base", default="main", help="branch point to scan commits from")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--suggest", action="store_true",
                    help="also print the gh command to file/close the issue (never runs it)")
    args = ap.parse_args(argv)

    repo = Path(args.repo_root).resolve()
    number = args.issue.lstrip("#")

    if not number.isdigit():
        print(f"{TOKEN}: operational error — issue must be a number, got {args.issue!r}",
              file=sys.stderr)
        return 2
    if _git(repo, "rev-parse", "--git-dir").returncode != 0:
        print(f"{TOKEN}: operational error — {repo} is not a git repository",
              file=sys.stderr)
        return 2

    reasons: list[str] = []

    test_path = repo / args.test
    if not test_path.is_file():
        reasons.append("test_missing")
    elif not _issue_re(number).search(test_path.read_text(encoding="utf-8", errors="replace")):
        # The test exists but never names the issue, so nothing on disk ties it
        # to the measurement that justified it.
        reasons.append("test_omits_issue")

    if not any(_closing_re(number).search(m) for m in _commit_messages(repo, args.base)):
        reasons.append("trailer_missing")

    verdict = "PASS" if not reasons else "FAIL"
    line = f"{TOKEN}: {verdict} issue={number} test={args.test}"
    if reasons:
        line += f" reasons={','.join(reasons)}"
    print(line)

    if args.suggest:
        print(f"  gh issue view {number} --comment  "
              f"# file with: gh issue create --title '<measurement>' --body-file <path>")
        print(f"  git commit --trailer 'Closes #{number}'  # or put 'Closes #{number}' in the body")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
