#!/usr/bin/env python3
"""Compare gate verdicts from two REPRO readings."""

from __future__ import annotations

import re
import sys
from pathlib import Path


Key = tuple[str, str, str]
Verdict = tuple[str, str]
APPROVED: frozenset[Key] = frozenset({
    ("M-10", "claude", "step5"),
    ("M-10", "codex", "step5"),
    ("M-11", "claude", "step5"),
    ("leaf-symlink", "claude", "step5"),
    ("FR-8 literal-uuid", "codex", "step5"),
    ("FR-8 flag", "codex", "step5"),
    # Operator decision 2026-09-30: the unfixed Codex gate denied this loop at
    # step3 (judge-error); ungoverned state must allow, as the Claude gate does.
    ("M-18 M-14", "codex", "step3"),
})
GATE_LINE = re.compile(
    r"^REPRO: cell=(?P<cell>.+?) gate=(?P<gate>claude|codex) "
    r"state=(?P<state>step5|step3) decision=(?P<decision>allow|deny) "
    r"kind=(?P<kind>.+)$"
)


def parse_reading(path: Path) -> dict[Key, Verdict]:
    readings: dict[Key, Verdict] = {}
    reachable: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("REPRO: agent-cli-reachable="):
            reachable.append(line.removeprefix("REPRO: agent-cli-reachable="))
        match = GATE_LINE.fullmatch(line)
        if match is None:
            continue
        key = (match["cell"], match["gate"], match["state"])
        if key in readings:
            raise ValueError(f"{path}: duplicate gate key {key}")
        readings[key] = (match["decision"], match["kind"])
    if reachable != ["no"]:
        raise ValueError(f"{path}: invalid agent-cli-reachable line: {reachable!r}")
    return readings


def compare(old: dict[Key, Verdict], new: dict[Key, Verdict]) -> tuple[bool, int, int, list[str]]:
    offending: list[str] = []
    softened = approved = 0
    for key in sorted(old.keys() | new.keys()):
        label = f"cell={key[0]} gate={key[1]} state={key[2]}"
        if key not in old or key not in new:
            offending.append(f"{label} missing={'old' if key not in old else 'new'}")
            continue
        before, after = old[key], new[key]
        if before[0] == "deny" and after[0] == "allow":
            softened += 1
            if key in APPROVED:
                approved += 1
            else:
                offending.append(f"{label} deny-to-allow unapproved")
        elif before[0] == after[0] == "deny" and before[1] != after[1]:
            print(f"KIND: {label} {before[1]} -> {after[1]}")
    return not offending, softened, approved, offending


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: compare_readings.py OLD NEW", file=sys.stderr)
        return 2
    try:
        old, new = (parse_reading(Path(name)) for name in argv)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"reading error: {exc}", file=sys.stderr)
        return 1
    ok, softened, approved, offending = compare(old, new)
    if ok:
        print(f"COMPARE: PASS softened={softened} approved={approved}")
    else:
        print("COMPARE: FAIL")
        for key in offending:
            print(key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
