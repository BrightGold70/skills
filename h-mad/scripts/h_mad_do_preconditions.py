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
import re
import sys
from pathlib import Path

AUDIT_VERSION_RE = re.compile(r"\.audit\.v(\d+)\.md$")


def _count_must_fix(path: Path) -> int:
    in_section = False
    count = 0
    for line in path.read_text().splitlines():
        if line.startswith("## Must-fix"):
            in_section = True
            continue
        if line.startswith("## "):
            in_section = False
            continue
        if in_section and line.startswith("- "):
            count += 1
    return count


def _latest_audit(features_dir: Path, feature: str, phase: str) -> Path | None:
    pattern = f"{feature}.{phase}.audit.v*.md"
    candidates = list(features_dir.glob(pattern))
    if not candidates:
        return None
    def _ver(p: Path) -> int:
        m = AUDIT_VERSION_RE.search(p.name)
        return int(m.group(1)) if m else 0
    return max(candidates, key=_ver)


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

    plan_audit = _latest_audit(plan_features, feature, "plan") if plan_features.is_dir() else None
    if plan_audit is None:
        issues.append(f"MISSING:{plan_features}/{feature}.plan.audit.v*.md")
    elif _count_must_fix(plan_audit) > 0:
        issues.append(f"DIRTY:{plan_audit}")

    design_audit = _latest_audit(design_features, feature, "design") if design_features.is_dir() else None
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
