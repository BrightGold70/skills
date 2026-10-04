#!/usr/bin/env python3
"""Which h-mad runs are live right now, in any lane? Ask before a skill change lands.

`~/.claude/skills/h-mad` is a symlink into the skills repo, so a change there alters
the installed skill in every session at once, including one mid-cycle. `3219bdd`
landed while a HemaSuite run was in flight and "silently invalidated a batch-18
decision": nothing broke, the damage was to reasoning already done by a gate that
then moved. This names the live lanes. It never blocks; holding the change is a
judgement for the operator.

Usage:
  h_mad_live_runs.py [--path DIR ...] [--if-staged-skill]

Lanes are the Orca worktrees (`hmad-dispatch worktree-ps`), or the `--path` dirs
given. A lane is live when its `docs/.bkit-memory.json` holds a feature whose claim
heartbeat is still within the ownership window — the same `owner_is_live` rule
`--claim` uses, so this and the claim logic cannot disagree.

Prints `LIVE-RUNS: <K> checked=<N>` with one `live:` line each, `LIVE-RUNS: NONE
checked=<N>`, or `LIVE-RUNS: UNKNOWN …` when lanes could not be listed or a state
file could not be read: "could not check" must never read as "none live". Exit 0.

`--if-staged-skill` prints nothing unless a file staged in the current repo sits under
a directory holding a SKILL.md; the advisory pre-commit hook calls it that way.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from h_mad_state_ownership import owner_is_live  # noqa: E402

STATE = Path("docs") / ".bkit-memory.json"


def orca_lanes() -> list[Path] | None:
    try:
        run = subprocess.run(["hmad-dispatch", "worktree-ps", "--limit", "200"],
                             capture_output=True, text=True, timeout=30)
        data = json.loads(run.stdout) if run.returncode == 0 else None
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    # Post-unwrap shape; a missing container is not an empty list.
    if not isinstance(data, dict) or "worktrees" not in data:
        return None
    return [Path(w["path"]) for w in data["worktrees"] if w.get("path")]


def live_claims(lane: Path) -> list[tuple[str, str, str]]:
    """(feature, owner, heartbeat) per live claim; raises ValueError if unreadable."""
    path = lane / STATE
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise ValueError(str(exc)) from exc
    records = (data.get("orchestrator_state") or {}) if isinstance(data, dict) else {}
    return [(feature, str(r["owner_session_id"]), str(r.get("owner_heartbeat_ts")))
            for feature, r in sorted(records.items())
            if isinstance(r, dict) and r.get("owner_session_id")
            and owner_is_live(r.get("owner_heartbeat_ts"))]


def staged_skill_change(cwd: Path) -> bool:
    run = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True)
    if run.returncode != 0:
        return False
    repo = Path(run.stdout.strip())
    staged = subprocess.run(["git", "-C", str(repo), "diff", "--cached", "--name-only", "-z"],
                            capture_output=True, text=True).stdout.split("\0")
    for rel in filter(None, staged):
        for parent in (repo / rel).parents:
            if parent == repo.parent:
                break
            if (parent / "SKILL.md").is_file():
                return True
    return False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--path", type=Path, action="append", default=[])
    ap.add_argument("--if-staged-skill", action="store_true")
    args = ap.parse_args(argv)

    if args.if_staged_skill and not staged_skill_change(Path.cwd()):
        return 0
    lanes = args.path or orca_lanes()
    if lanes is None:
        print("LIVE-RUNS: UNKNOWN could not list lanes (hmad-dispatch worktree-ps); "
              "pass --path to check specific lanes")
        return 0

    live, unreadable = [], []
    for lane in lanes:
        try:
            live += [(lane, *claim) for claim in live_claims(lane)]
        except ValueError as exc:
            unreadable.append((lane, exc))
    if unreadable:
        print(f"LIVE-RUNS: UNKNOWN live={len(live)} unreadable={len(unreadable)} checked={len(lanes)}")
    elif live:
        print(f"LIVE-RUNS: {len(live)} checked={len(lanes)}")
    else:
        print(f"LIVE-RUNS: NONE checked={len(lanes)}")
    for lane, feature, owner, beat in live:
        print(f"  live: {lane} · {feature} · owner {owner[:8]} · heartbeat {beat}")
    for lane, exc in unreadable:
        print(f"  unreadable: {lane / STATE} — {exc}")
    if live:
        print("  a skill change lands in those sessions immediately; decide whether to hold it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
