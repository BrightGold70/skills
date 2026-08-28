#!/usr/bin/env python3
"""h_mad_baseline_sha.py — derive the Phase-5c baseline sha, and prove it.

Phase 6a-prime reviews `BASE = 5c sha` and 5f takes `--base <5c sha>`, but nothing
produced that value, so it was produced by hand. The recorded attempt used
`git merge-base main <branch>` — which returns the wrong commit, and returns it
plausibly. 5c is defined as `git checkout -b …; commit impl-plan + audit files`, so
the 5c commit is the branch's FIRST commit and the merge-base is the commit it
forked FROM: off by exactly one, and that one is the impl-plan commit. Measured on
the feature that filed the row (J41): merge-base `b5c8f41`, real 5c `730cc16`, 313
lines between them — the impl-plan and its three audits, which then enter the
6a-prime diff as newly-added content when the contract makes them a separate INPUT
to that review.

The original was "verified" by re-running the same `merge-base` command that
produced it. That is not a control; it is the question restated.

Verdicts, printed as a canonical token:

    BASELINE: OK sha=<40-hex> branch=<b> trunk=<t>            exit 0
    BASELINE: UNVERIFIED reason=no_impl_plan candidate=<sha>  exit 0
    BASELINE: NONE reason=no_commits_on_branch branch=<b>     exit 0
    BASELINE: UNREADABLE reason=<r>                           exit 2

**Only `OK` carries `sha=`.** Every other outcome omits it, `UNVERIFIED` included —
which is why the unvouched value is reported as `candidate=` instead. A caller
scraping for `sha=` must not be able to receive a value nothing stands behind: the
defect this script exists for was a wrong sha that looked exactly like a right one,
and re-creating that shape here would be the same bug one level up
(`invariants.base.md` §"Audit-gate signal discipline").

Why derive rather than store the value in orchestrator state:

  * A stored sha does not survive a rebase — it points at the old, orphaned commit,
    while this recomputes and finds the new first commit, still 5c semantically.
  * A stored sha cannot tell you it is wrong. This can: "the branch's first commit
    is 5c" is a protocol invariant with an observable consequence — that commit
    touches an impl-plan — so a violated assumption becomes `UNVERIFIED` rather
    than a confident wrong answer. That asymmetry is the whole argument (J41).

`UNVERIFIED` is a real verdict, not an error: the derivation ran and its assumption
was checked and failed, which means something was committed to the branch before
the impl-plan. Read the token, never `$?`.

Stdlib-only.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


class BaselineError(Exception):
    """Nothing could be derived — an operational error, never a verdict."""


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        raise BaselineError(detail[0] if detail else f"git {args[0]} failed")
    return result.stdout.strip()


def _first_commit_on_branch(repo: Path, branch: str, trunk: str) -> str | None:
    """The oldest commit reachable from `branch` and not from `trunk`.

    `--first-parent` so a merged-in side branch cannot supply an older commit than
    the one that started this branch.
    """
    out = _git(repo, "rev-list", "--first-parent", branch, "--not", trunk)
    lines = [line for line in out.splitlines() if line.strip()]
    return lines[-1] if lines else None


def _touches_impl_plan(repo: Path, sha: str) -> bool:
    """Whether a commit touches an impl-plan document.

    The observable consequence of 5c's definition. Deliberately a substring test on
    the path rather than a fixed directory: projects place `docs/01-plan/features/`
    differently, and a check that only passes for this repository's layout would
    report `UNVERIFIED` for every other project — a false alarm being as useless
    here as a false pass.
    """
    names = _git(repo, "show", "--name-only", "--format=", sha)
    return any("impl-plan" in line for line in names.splitlines() if line.strip())


def derive(repo: Path, branch: str, trunk: str) -> dict:
    """-> {'verdict', 'sha'|None, 'candidate'|None, 'reason'|None}. Raises BaselineError."""
    for ref in (branch, trunk):
        try:
            _git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
        except BaselineError:
            raise BaselineError(f"unknown_ref:{ref}") from None

    sha = _first_commit_on_branch(repo, branch, trunk)
    if sha is None:
        return {"verdict": "NONE", "sha": None, "candidate": None,
                "reason": "no_commits_on_branch"}
    if not _touches_impl_plan(repo, sha):
        return {"verdict": "UNVERIFIED", "sha": None, "candidate": sha,
                "reason": "no_impl_plan"}
    return {"verdict": "OK", "sha": sha, "candidate": None, "reason": None}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Derive and verify the Phase-5c baseline sha")
    parser.add_argument("--branch", required=True, help="the feature branch")
    parser.add_argument("--trunk", default="main", help="the branch it forked from (default: main)")
    parser.add_argument("--repo", type=Path, default=Path("."), help="repository root")
    args = parser.parse_args(argv)

    try:
        result = derive(args.repo, args.branch, args.trunk)
    except BaselineError as exc:
        # No verdict exists. Carries no sha and no candidate, so a cannot-judge can
        # never be read as a value.
        print(f"BASELINE: UNREADABLE reason={exc}")
        print("[H-MAD] baseline UNREADABLE")
        return 2

    if result["verdict"] == "OK":
        print(f"BASELINE: OK sha={result['sha']} branch={args.branch} trunk={args.trunk}")
    elif result["verdict"] == "UNVERIFIED":
        print(
            f"BASELINE: UNVERIFIED reason={result['reason']} "
            f"candidate={result['candidate']} branch={args.branch}"
        )
        print(
            "  the branch's first commit does not touch an impl-plan, so something was "
            "committed before 5c and the first-commit rule does not hold here — "
            "identify the 5c commit by hand rather than using the candidate above."
        )
    else:
        print(f"BASELINE: NONE reason={result['reason']} branch={args.branch}")

    print(f"[H-MAD] baseline {result['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
