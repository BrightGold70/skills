#!/usr/bin/env python3
"""DO-1a census, in files, using the plan's literal grep patterns.

Working directory: repository root.
Invocation: python3 docs/03-analysis/probes/agy-coder-fallback/census_state_line.py
Control: python3 docs/03-analysis/probes/agy-coder-fallback/census_state_line.py --control
The control overrides the first expected count with 7, exercising the comparison.
Use --root PATH to measure another repository tree (including doctored tracked files).
Equivalent to git ls-files -z h-mad | xargs -0 grep -l with the patterns below;
each file is counted once per query, even if several lines or patterns match.
PASS and FAIL exit 0; unreadable input or failed git discovery exits 2.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

EXPECT = {"DO-1a": 6, "DO-1a/four-pattern": 7}
PATTERNS = {
    "DO-1a": (b"TDD-STATE: active",),
    "DO-1a/four-pattern": (
        b"codex-escape=", b" record=", b"STATE_ACTIVE_RE", b"format_state_line",
    ),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--control", action="store_true")
    args = parser.parse_args()
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.root, text=True).strip()
        print(f"HEAD: {head}")
        paths = subprocess.check_output(["git", "ls-files", "-z", "h-mad"], cwd=args.root)
        hits = {name: [] for name in PATTERNS}
        for raw in paths.split(b"\0"):
            if not raw:
                continue
            path = os.fsdecode(raw)
            content = (args.root / path).read_bytes()
            for name, patterns in PATTERNS.items():
                if any(pattern in content for pattern in patterns):
                    hits[name].append(path)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"probe cannot run: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    expected = dict(EXPECT)
    if args.control:
        expected["DO-1a"] += 1
        print("CONTROL: expected DO-1a files overridden to 7")
    ok = True
    for name, paths in hits.items():
        same = len(paths) == expected[name]
        ok &= same
        print(f"{name} files: computed={len(paths)} expected={expected[name]} {'OK' if same else 'MOVED'}")
        for path in paths:
            print(f"  {path}")
    print("PROBE: " + ("PASS" if ok else "FAIL"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
