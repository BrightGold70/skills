#!/usr/bin/env python3
"""h_mad_do_preconditions.py — verify /h-mad do prereqs for a feature.

Checks:
  feature.plan.md exists
  feature.design.md exists
  latest feature.plan.audit.v*.md has must-fix=0 (awk gate)
  latest feature.design.audit.v*.md has must-fix=0 (awk gate)

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

from h_mad_audit_gate import classify, _acknowledged_from_text
from h_mad_cycle_counts import latest_audit_path


def _count_must_fix(path: Path) -> int:
    text = path.read_text()
    acknowledged = _acknowledged_from_text(text)
    return classify(text, acknowledged=acknowledged)["must_count"]


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

    plan_audit = latest_audit_path(
        repo_root / "docs", feature, "plan", include_archive=False
    )
    if plan_audit is None:
        issues.append(f"MISSING:{plan_features}/{feature}.plan.audit.v*.md")
    elif _count_must_fix(plan_audit) > 0:
        issues.append(f"DIRTY:{plan_audit}")

    design_audit = latest_audit_path(
        repo_root / "docs", feature, "design", include_archive=False
    )
    if design_audit is None:
        issues.append(f"MISSING:{design_features}/{feature}.design.audit.v*.md")
    elif _count_must_fix(design_audit) > 0:
        issues.append(f"DIRTY:{design_audit}")

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
