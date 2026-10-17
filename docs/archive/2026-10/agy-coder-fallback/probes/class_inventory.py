#!/usr/bin/env python3
"""Partition the first init.tools inventory into the design's four classes.

Working directory: repository root.
Invocation: python3 docs/03-analysis/probes/agy-coder-fallback/class_inventory.py [FIRST_LOG [SECOND_LOG]]
Control: python3 docs/03-analysis/probes/agy-coder-fallback/class_inventory.py --control
The control overrides the expected total with 59 and uses the real comparison.
FIRST_LOG defaults to the committed 2026-10-01 capture. Both optional paths are
JSONL captures; only the first init event counts. A second capture is compared
with EXPECT independently and its per-class additions/removals are printed.
Membership is name-based, not evidence of actual tool side effects. Duplicate
names count once. Missing/malformed init.tools is reported as drift (FAIL).
PASS and FAIL exit 0; unreadable input or failed git discovery exits 2.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_LOG = "docs/03-analysis/probes/multi-host-runtime/rehearsal/live-agy-2026-10-01.log"
EXPECT = {"total": 58, "a": 11, "b": 5, "c": 1, "d": 41}
CLASSES = {
    "a": {"view_file", "list_dir", "grep_search", "find_by_name", "command_status",
          "read_url_content", "search_web", "ask_question", "finish", "wait", "wait_5_seconds"},
    "b": {"write_to_file", "replace_file_content", "multi_replace_file_content", "sed_file", "notebook_edit"},
    "c": {"run_command"},
}


def inventory(path):
    with path.open(encoding="utf-8") as source:
        for number, line in enumerate(source, 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except ValueError:
                return None, f"invalid JSON on line {number} before first init"
            if isinstance(event, dict) and event.get("event") == "init":
                payload = event.get("init")
                tools = payload.get("tools") if isinstance(payload, dict) else None
                if not isinstance(tools, list) or any(not isinstance(name, str) for name in tools):
                    return None, f"first init on line {number} has no string-array tools"
                return set(tools), None
    return None, "no init event"


def partition(names):
    parts = {key: names & members for key, members in CLASSES.items()}
    parts["d"] = names - set().union(*CLASSES.values())
    return parts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first_log", nargs="?", type=Path, default=Path(DEFAULT_LOG))
    parser.add_argument("second_log", nargs="?", type=Path)
    parser.add_argument("--control", action="store_true")
    args = parser.parse_args()
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        print(f"HEAD: {head}")
        logs = [args.first_log] + ([args.second_log] if args.second_log else [])
        readings = [inventory(path) for path in logs]
    except (OSError, UnicodeError, subprocess.CalledProcessError) as exc:
        print(f"probe cannot run: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    expected = dict(EXPECT)
    if args.control:
        expected["total"] += 1
        print("CONTROL: expected total overridden to 59")
    ok, partitions = True, []
    for path, (names, error) in zip(logs, readings):
        print(f"LOG: {path}")
        if error:
            print(f"inventory shape: computed={error!r} expected='first init.tools string array' MOVED")
            ok = False
        parts = partition(names or set())
        partitions.append(parts)
        counts = {"total": len(names or set()), **{key: len(value) for key, value in parts.items()}}
        for key, actual in counts.items():
            same = actual == expected[key]
            ok &= same
            print(f"{key} names: computed={actual} expected={expected[key]} {'OK' if same else 'MOVED'}")
            if key in parts:
                print("  " + ", ".join(sorted(parts[key])))
    if len(partitions) == 2:
        print("DIFFERENCE: second minus first")
        for key in partitions[0]:
            before, after = partitions[0][key], partitions[1][key]
            print(f"  {key}: added={sorted(after - before)!r} removed={sorted(before - after)!r}")
    print("PROBE: " + ("PASS" if ok else "FAIL"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
