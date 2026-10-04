#!/usr/bin/env python3
"""Re-derive a spec's acceptance-criteria count and check every paired claim.

A plan's Success Criteria saying "All N ACs pass" went stale three times in one
feature (38, 39, 40, 43), each caught by an auditor rather than by a check, and
twice the inserted AC also broke contiguous numbering (`AC-3.8b` before
`AC-3.7`). Both are mechanical, so this does them.

Usage:
  h_mad_ac_census.py <feature>.spec.md [<paired doc> ...]

An AC is a list item `- AC-<fr>.<n>[letter]:` (optionally bold). Within each FR
the numbers must be exactly 1..n with no gap or duplicate, and a lettered AC
(`AC-2.2b`) needs its base (`AC-2.2`). Each paired doc's `All <N> ACs` must equal
the count. Document order is reported as `ORDER (advisory):` and never moves the
verdict; an AC may carry a tag before its colon (`AC-2.1 (layout):`, `AC-3.3 [OD-1]:`).

Prints `ACS: OK count=N frs=K`, `ACS: DRIFT count=N frs=K` (with one `CLAIM:`, `GAP:` or
`DUPLICATE:` line per finding), `ACS: NONE count=0` when the spec has no ACs in this
shape, or `ACS: UNREADABLE <reason>`. Read the token, not `$?`: a verdict exits
0, an unreadable input exits 2.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

AC = re.compile(r"^\s*-\s+(?:\*\*)?AC-(\d+)\.(\d+)([a-z]?)(?:\*\*)?(?: (?:\([^)]*\)|\[[^\]]*\]))?[:.]")
CLAIM = re.compile(r"\bAll (\d+) ACs\b")


def parse(text: str) -> list[tuple[int, int, str]]:
    return [(int(m[1]), int(m[2]), m[3]) for m in map(AC.match, text.splitlines()) if m]


def numbering_findings(acs: list[tuple[int, int, str]]) -> list[str]:
    """Gaps, duplicates and orphan letters: each FR must number 1..n exactly."""
    out, seen, bases = [], set(), {}
    for fr, n, letter in acs:
        name = f"AC-{fr}.{n}{letter}"
        if name in seen:
            out.append(f"DUPLICATE: {name}")
        seen.add(name)
        if not letter:
            bases.setdefault(fr, set()).add(n)
    for fr, nums in sorted(bases.items()):
        for missing in sorted(set(range(1, max(nums) + 1)) - nums):
            later = min(n for n in nums if n > missing)
            out.append(f"GAP: FR-{fr} has AC-{fr}.{later} but no AC-{fr}.{missing}")
    for fr, n, letter in acs:
        if letter and n not in bases.get(fr, set()):
            out.append(f"GAP: FR-{fr} has AC-{fr}.{n}{letter} but no AC-{fr}.{n}")
    return out


def order_advisories(acs: list[tuple[int, int, str]]) -> list[str]:
    """Document order, ADVISORY. Calibrated on the committed corpus: four audited
    specs place an AC beside its topic rather than in numeric order and none of
    them has a gap, so order alone never moves the verdict."""
    last: dict[int, tuple[int, str]] = {}
    out = []
    for fr, n, letter in acs:
        prev = last.get(fr)
        if prev is not None and (n, letter) < prev:
            out.append(f"ORDER (advisory): FR-{fr} AC-{fr}.{n}{letter} after "
                       f"AC-{fr}.{prev[0]}{prev[1]}")
        last[fr] = max(prev, (n, letter)) if prev else (n, letter)
    return out


def claim_findings(count: int, docs: list[Path]) -> list[str]:
    out = []
    for doc in docs:
        for lineno, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
            for m in CLAIM.finditer(line):
                if int(m[1]) != count:
                    out.append(f"CLAIM: {doc.name}:{lineno} says {m[1]}, spec has {count}")
    return out


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("usage: h_mad_ac_census.py <spec.md> [<paired doc> ...]", file=sys.stderr)
        return 2
    spec, docs = Path(args[0]), [Path(a) for a in args[1:]]
    try:
        acs = parse(spec.read_text(encoding="utf-8"))
        findings = numbering_findings(acs) + claim_findings(len(acs), docs) if acs else []
    except (OSError, UnicodeDecodeError) as exc:
        print(f"ACS: UNREADABLE {exc}")
        return 2
    if not acs:
        print("ACS: NONE count=0")
        return 0
    frs = len({fr for fr, _, _ in acs})
    print(f"ACS: {'DRIFT' if findings else 'OK'} count={len(acs)} frs={frs}")
    for line in findings + order_advisories(acs):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
