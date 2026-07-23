#!/usr/bin/env python3
"""h_mad_do_preconditions.py — verify /h-mad do prereqs for a feature.

Checks:
  feature.plan.md exists
  feature.design.md exists
  latest feature.plan.audit.v*.md has must-fix=0 (awk gate)
  latest feature.design.audit.v*.md has must-fix=0 (awk gate)

Prints: OK (exit 0)
   or:  MISSING:<path>  (exit 1)
   or:  DIRTY:<path>  (exit 1)
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
    rc, lines = check(args.repo_root, args.feature)
    for line in lines:
        print(line)
    return rc


if __name__ == "__main__":
    sys.exit(main())
