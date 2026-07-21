#!/usr/bin/env python3
"""h_mad_state_staleness.py - detect state that is well-formed but wrong.

The two-tier validator checks record shape. A record can pass it and still
describe a world that no longer exists, and both directions were observed on one
feature in one day: a halt_reason that outlived its resolution by four hours and
eight shipped modules, and a last_completed_phase that still read 4 after Phase
5 had completed, merged and pushed. The first would route a resume to `halted`
and present a solved problem as the blocker; the second would route to
enter_autonomous and redo merged work.

Neither is visible to a schema. Only a comparison against observable evidence
finds them, so this checks state against git.

**It reports disagreement; it does not adjudicate.** The failure being fixed is
silent confidence, not a wrong guess — so a finding names what disagrees and
leaves the operator to decide. Verdict travels in the token and the exit code is
0 on any verdict, matching the audit gate, so a finding never registers as a
tool failure.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUTONOMOUS_STALE_AFTER_SECONDS = 6 * 60 * 60


def _ts(value) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _phase_num(value) -> int:
    """Tolerant of every phase form real stores carry (see the validator)."""
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        token = value.strip().lower()
        if token == "complete":
            return 7
        for prefix in ("step", "phase"):
            rest = token[len(prefix):] if token.startswith(prefix) else ""
            if rest[:1].isdigit():
                return int(rest[0])
        if token.isdigit():
            return int(token)
    return 0


def check(record: dict, git: dict, now: str | None = None) -> list[dict[str, Any]]:
    """Return findings where state and git disagree. Empty means consistent."""
    findings: list[dict[str, Any]] = []
    latest = _ts(git.get("latest_commit_ts"))
    impl_commits = int(git.get("impl_commit_count") or 0)
    branch = bool(git.get("branch_exists"))

    # 1. A halt that commits landed after is probably resolved.
    halt_ts = _ts(record.get("halt_ts"))
    if record.get("halt_reason") and halt_ts and latest and latest > halt_ts:
        findings.append({
            "code": "halt_superseded",
            "detail": (
                f"halt_ts {halt_ts:%Y-%m-%dT%H:%M:%SZ} predates the newest commit "
                f"{latest:%Y-%m-%dT%H:%M:%SZ} ({impl_commits} implementation "
                "commits on the branch). The halt may already be resolved — "
                "resume routes to `halted` until halt_reason is cleared."
            ),
        })

    # 2. Implementation shipped, but the phase counter never advanced.
    if branch and impl_commits > 0 and _phase_num(record.get("last_completed_phase")) < 5:
        findings.append({
            "code": "phase_counter_behind",
            "detail": (
                f"last_completed_phase is {record.get('last_completed_phase')!r} "
                f"but {impl_commits} commits reference this feature. A resume "
                "would re-enter Phase 5 and redo shipped work."
            ),
        })

    # 3. Armed for a long time with nothing accounting for it.
    entry = _ts(record.get("autonomous_entry_ts"))
    if record.get("phase") and entry and not record.get("halt_reason"):
        reference = _ts(now) or datetime.now(timezone.utc)
        elapsed = (reference - entry).total_seconds()
        if elapsed > AUTONOMOUS_STALE_AFTER_SECONDS:
            findings.append({
                "code": "autonomous_flag_stale",
                "detail": (
                    f"phase={record.get('phase')!r} has been set for "
                    f"{elapsed / 3600:.1f}h with no halt_reason. Either the run "
                    "is still going, or it ended without disarming the flag — "
                    "which leaves the TDD gate armed."
                ),
            })

    return findings


def _git_facts(repo: Path, feature: str) -> dict:
    """Best-effort. Any failure yields 'no evidence', never a false finding."""

    def run(*args) -> str | None:
        try:
            out = subprocess.run(
                ["git", "-C", str(repo), *args],
                capture_output=True, text=True, timeout=15,
            )
            return out.stdout.strip() if out.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            return None

    branches = run("branch", "--list", f"*{feature}*", "--format=%(refname:short)")
    branch_name = (branches or "").splitlines()[0].strip() if branches else ""
    if not branch_name:
        return {"branch_exists": False, "latest_commit_ts": None, "impl_commit_count": 0}

    latest = run("log", "-1", "--format=%cI", branch_name)

    # Count commits that *reference this feature*, not everything reachable.
    # Two wrong approaches were tried on a real repo first: `rev-list --count
    # <branch>` returned 2404 for an 18-commit feature (the whole history), and
    # counting `merge-base..<branch>` returned 0 once the branch was merged —
    # blind at exactly the moment the real incident happened, which was a phase
    # counter left behind *after* a merge. Grepping the log survives the merge.
    #
    # A feature whose commits do not name it counts 0 and simply yields no
    # finding. That is the right way to be wrong here: this reports
    # disagreement, so a miss costs a nudge and a false positive costs trust.
    count_text = run("rev-list", "--count", f"--grep={feature}", branch_name) or ""
    count = int(count_text) if count_text.isdigit() else 0

    return {
        "branch_exists": True,
        "latest_commit_ts": latest,
        "impl_commit_count": count,
    }


def main(argv: list[str] | None = None) -> int:
    """Run the staleness check CLI."""
    parser = argparse.ArgumentParser(description="H-MAD state staleness check")
    parser.add_argument("state_file", type=Path)
    parser.add_argument("--feature", required=True)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--now", help="Reference time (testing)")
    parser.add_argument("--no-git", action="store_true", help="Do not shell out to git")
    parser.add_argument("--branch-exists", action="store_true")
    parser.add_argument("--latest-commit-ts")
    parser.add_argument("--impl-commit-count", type=int, default=0)
    args = parser.parse_args(argv)

    try:
        state = json.loads(args.state_file.read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: {args.state_file}: {exc}", file=sys.stderr)
        return 2

    record = (state.get("orchestrator_state") or {}).get(args.feature)
    if not record:
        print(f"ERROR: no such feature: {args.feature}", file=sys.stderr)
        return 2

    if args.no_git:
        git = {
            "branch_exists": args.branch_exists,
            "latest_commit_ts": args.latest_commit_ts,
            "impl_commit_count": args.impl_commit_count,
        }
    else:
        git = _git_facts(args.repo, args.feature)

    findings = check(record, git, now=args.now)
    verdict = "SUSPECT" if findings else "CLEAN"
    print(f"STALENESS: {verdict} findings={len(findings)}")
    for f in findings:
        print(f"  {f['code']}: {f['detail']}")
    print(f"[H-MAD] {args.feature} staleness {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
