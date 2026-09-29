#!/usr/bin/env python3
"""Measure the frozen construct seed against committed skill files."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[4]
SKILLS = ("h-mad", "handoff")


def git(*args: str) -> subprocess.CompletedProcess[str]:
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("CLAUDE") and key != "HPW_AGENT_BACKEND"}
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True, text=True, env=env, timeout=60.0, check=False,
    )


def unreadable(reason: str) -> int:
    print(f"SEEDCOV: UNREADABLE reason={reason}")
    return 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sha", required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--branches", action="store_true")
    args = parser.parse_args()

    commit = git("rev-parse", "--verify", "-q", f"{args.sha}^{{commit}}")
    if commit.returncode or not commit.stdout.strip():
        return unreadable("bad_sha")
    sha = commit.stdout.strip()

    try:
        registry = json.loads(args.registry.read_text(encoding="utf-8"))
        entries = registry["constructs"]
        if not isinstance(entries, list):
            raise ValueError("constructs is not an array")
        for entry in entries:
            if not isinstance(entry["id"], str) or not isinstance(entry["skills"], list):
                raise ValueError("invalid entry")
            if not set(entry["skills"]) <= set(SKILLS):
                raise ValueError("invalid skill")
            re.compile(entry["pattern"])
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, re.error):
        return unreadable("bad_registry")

    texts = {}
    for skill in SKILLS:
        shown = git("show", f"{sha}:{skill}/SKILL.md")
        if shown.returncode:
            return unreadable("bad_sha")
        texts[skill] = shown.stdout

    if args.branches:
        sys.path.insert(0, str(ROOT / "h-mad" / "tests"))
        try:
            from host_parity import expand_branches
        except ImportError:
            return unreadable("no_expander")
        cells = []
        dead = 0
        branches = 0
        for entry in entries:
            try:
                variants = expand_branches(entry["pattern"])
            except Exception:
                return unreadable("no_expander")
            for variant in variants:
                branches += 1
                hits_for_branch = []
                for skill in SKILLS:
                    if skill in entry["skills"]:
                        hits = sum(1 for _ in re.finditer(variant, texts[skill]))
                        cells.append((entry["id"], variant, skill, hits))
                        hits_for_branch.append(hits)
                if all(hits == 0 for hits in hits_for_branch):
                    dead += 1
        for ident, variant, skill, hits in cells:
            print(f"CELL id={ident} branch={json.dumps(variant)} skill={skill} hits={hits}")
        for ident, variant, skill, hits in cells:
            if hits == 0:
                print(f"ZERO id={ident} branch={json.dumps(variant)} skill={skill} hits=0")
        print(f"SEEDCOV-BRANCHES: entries={len(entries)} branches={branches} "
              f"cells={len(cells)} zero={sum(hits == 0 for *_, hits in cells)} dead={dead}")
        return 0

    stale = undeclared = 0
    for entry in entries:
        hits = {skill: sum(1 for _ in re.finditer(entry["pattern"], texts[skill]))
                for skill in SKILLS}
        findings = []
        for skill in SKILLS:
            if skill in entry["skills"] and hits[skill] == 0:
                stale += 1
                findings.append(f"stale:{skill}")
            elif skill not in entry["skills"] and hits[skill] > 0:
                undeclared += 1
                findings.append(f"undeclared:{skill}")
        declared = ",".join(entry["skills"])
        verdict = ",".join(findings) if findings else "ok"
        print(f"ENTRY id={entry['id']} h-mad={hits['h-mad']} handoff={hits['handoff']} "
              f"declared={declared} verdict={verdict}")
    status = "PASS" if stale == undeclared == 0 else "FAIL"
    print(f"SEEDCOV: {status} entries={len(entries)} stale={stale} undeclared={undeclared}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
