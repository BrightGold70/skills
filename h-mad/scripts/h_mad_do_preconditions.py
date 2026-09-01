#!/usr/bin/env python3
"""h_mad_do_preconditions.py — verify /h-mad do prereqs for a feature.

Checks:
  feature.plan.md exists
  feature.design.md exists
  EVERY feature.plan.audit.v*.md at the latest cycle has must-fix=0 (awk gate)
  EVERY feature.design.audit.v*.md at the latest cycle has must-fix=0 (awk gate)

"Every", not "the latest one": a cycle routinely carries more than one audit file
-- `.p1`/`.p2` are two halves of one audit's output, and `.codex`/`.agy` at the
same cycle are two different auditors. Scoring whichever the filesystem listed
first is "gate on one audit pass" wearing a green verdict.

Verdicts, printed as a canonical token:

    PRECONDITION: PASS                        exit 0
    PRECONDITION: FAIL issues=2               exit 0
    PRECONDITION: UNREADABLE                  exit 2

followed by the detail lines (`MISSING:<path>` / `DIRTY:<path>`) that say which
prerequisite is not met.

`FAIL` exits 0 because it is a **verdict**, not an operational error
(`invariants.base.md` §"Audit-gate signal discipline"): a non-zero exit
registers as a Claude Code `PostToolUseFailure` and leaks into coexisting
plugins' error handling. This check used to exit 1 on a normal FAIL and print no
token at all, which left a caller no way to obey "read the token, never `$?`" —
the instruction to branch on the exit code was the only thing it *could* do.
Non-zero is now reserved for the one genuine operational error: a repo root that
cannot be read, where nothing was checked and no verdict exists.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from h_mad_audit_gate import classify, has_gate_sections, _acknowledged_from_text
from h_mad_cycle_counts import latest_audit_paths


def _count_must_fix(path: Path) -> int:
    """Count unwaived Must-fix findings in a report already known to be scoreable.

    Counting only. It answers "how many findings", never "is this a real report" —
    `_audit_issue` owns that question via `has_gate_sections`. Keeping the two
    separate is deliberate: conflating them is what let a report with no findings
    *section* read as a report with no findings (#39).
    """
    text = path.read_text()
    acknowledged = _acknowledged_from_text(text)
    return classify(text, acknowledged=acknowledged)["must_count"]


def _audit_issue(path: Path) -> str | None:
    """Classify one audit report. `None` = clean; otherwise the issue detail line.

    Routes the unscoreable case through the SHARED `has_gate_sections` rather than
    re-deriving it (#39). This caller used to reach straight into `classify()`, so a
    report with no `## Must-fix`/`## Should-fix` headings scored `must_count=0` and
    CLEARED the Phase-5 gate — failing open, while the audit-gate CLI returned
    `GATE: INVALID` on the very same file. Re-deriving the check is exactly how the
    two drifted apart, so the guard must stay shared.

    `INVALID` is deliberately distinct from `DIRTY`: an unscoreable report has no
    findings to go and fix, it needs re-obtaining, and collapsing the two would hand
    the operator the wrong remedy.
    """
    if not has_gate_sections(path.read_text()):
        return f"INVALID:{path}"
    if _count_must_fix(path) > 0:
        return f"DIRTY:{path}"
    return None


def check(repo_root: Path, feature: str) -> tuple[int, list[str]]:
    issues: list[str] = []
    plan_features = repo_root / "docs" / "01-plan" / "features"
    design_features = repo_root / "docs" / "02-design" / "features"

    plan = plan_features / f"{feature}.plan.md"
    if not plan.is_file():
        issues.append(f"MISSING:{plan}")

    design = design_features / f"{feature}.design.md"
    if not design.is_file():
        issues.append(f"MISSING:{design}")

    # EVERY audit at the latest cycle, not one of them. A cycle routinely carries
    # more than one file -- `.p1`/`.p2` are two halves of one audit's output, and
    # `.codex`/`.agy` are two different auditors that, in this project's record,
    # alternate sides and disagree. `latest_audit_path` returns whichever sorted
    # first, so a blocker found by the second auditor cleared the gate while the
    # verdict named the first one's file. Scoring all of them is the same
    # fail-closed rule as `_audit_issue`'s INVALID branch: any one dirty or
    # unscoreable report is an issue.
    for phase, directory in (("plan", plan_features), ("design", design_features)):
        audits = latest_audit_paths(
            repo_root / "docs", feature, phase, include_archive=False
        )
        if not audits:
            issues.append(f"MISSING:{directory}/{feature}.{phase}.audit.v*.md")
            continue
        for audit in audits:
            issue = _audit_issue(audit)
            if issue is not None:
                issues.append(issue)

    return (1 if issues else 0, issues or ["OK"])


def main() -> int:
    parser = argparse.ArgumentParser(description="h-mad do preconditions check")
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--feature", required=True)
    args = parser.parse_args()

    # The one genuine operational error: nothing could be checked, so there is no
    # verdict to report. Reporting FAIL here would blame the feature for a bad
    # path — the same misrouting an unreadable plan used to cause at 5b.
    if not args.repo_root.is_dir():
        print(f"ERROR: --repo-root is not a directory: {args.repo_root}", file=sys.stderr)
        print("PRECONDITION: UNREADABLE")
        print(
            "  nothing was checked, so this is not a verdict about the feature — "
            "check the --repo-root path."
        )
        return 2

    has_issues, lines = check(args.repo_root, args.feature)
    if has_issues:
        print(f"PRECONDITION: FAIL issues={len(lines)}")
    else:
        print("PRECONDITION: PASS")
    for line in lines:
        print(line)
    # Exit 0 on either verdict; the caller reads the token, never `$?`.
    return 0


if __name__ == "__main__":
    sys.exit(main())
