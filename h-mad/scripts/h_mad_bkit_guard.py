#!/usr/bin/env python3
"""h_mad_bkit_guard.py - keep bkit's SessionStart migration off h-mad's state file.

h-mad keeps orchestrator state at `<project>/docs/.bkit-memory.json`, which is
bkit's LEGACY path. bkit's SessionStart hook (`hooks/startup/migration.js`, vendor
code, not patchable from here) RENAMES that file to `<project>/.bkit/state/memory.json`
whenever the legacy file exists and the new one does not, and skips when the new one
already exists. So the first Claude session started inside a fresh git worktree
silently moves h-mad's store away, and the resume oracle then answers `state_lost`
for a record that is intact one directory over. Reproduced 2026-10-26.

Two halves, operator-chosen ("seed + detect"):

* `seed()` makes sure bkit's target exists (an empty `{}`), so bkit always finds
  one and never migrates. It never overwrites, and it never raises: a seed failure
  is a warning, not a failed state write.
* `migrated_record()` reports where a migrated copy of a feature's record sits,
  so the oracle can say `migrated_by_bkit` and print a restore-by-COPY hint
  instead of `state_lost`. A copy, not a move: a move would leave bkit without a
  target and the next session start would migrate the file away again.

Only the canonical shape is handled: a state path ending in `docs/.bkit-memory.json`,
whose project root is that `docs/` directory's parent. Any other shape is not
bkit's legacy path, so bkit never touches it and nothing is seeded or probed.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

LEGACY_NAME = ".bkit-memory.json"
TARGET_REL = Path(".bkit") / "state" / "memory.json"


def project_root(state_file: Path) -> Path | None:
    """The project root for a canonical `<root>/docs/.bkit-memory.json`, else None."""
    state_file = Path(state_file)
    if state_file.name != LEGACY_NAME or state_file.parent.name != "docs":
        return None
    return state_file.parent.parent


def bkit_target(state_file: Path) -> Path | None:
    root = project_root(state_file)
    return None if root is None else root / TARGET_REL


def seed_root(root: Path) -> Path | None:
    """Create `<root>/.bkit/state/memory.json` as `{}` if absent. Never overwrites.

    Returns the path when this call created it, else None. Never raises: every
    failure is a warning on stderr, because a seed exists to protect the state
    write and must never be the reason one fails.
    """
    target = Path(root) / TARGET_REL
    try:
        if os.path.lexists(target):
            return None  # present (even as a dangling link): bkit has a target
        target.parent.mkdir(parents=True, exist_ok=True)
        # O_EXCL: if anything appeared between the check and here, leave it alone.
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        return None
    except OSError as exc:
        print(f"WARNING: could not seed bkit target {target} ({exc}); bkit's "
              "SessionStart migration may move the h-mad state file away. "
              "The state write itself is unaffected.", file=sys.stderr)
        return None
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write("{}\n")
    except OSError as exc:
        print(f"WARNING: could not finish seeding bkit target {target} ({exc})",
              file=sys.stderr)
        return None
    return target


def seed(state_file: Path) -> Path | None:
    """Seed bkit's target beside a canonical state file; no-op for any other shape."""
    root = project_root(state_file)
    return None if root is None else seed_root(root)


def _read_orchestrator_state(target: Path) -> dict | None:
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    records = data.get("orchestrator_state")
    return records if isinstance(records, dict) else None


def holds_orchestrator_state(state_file: Path) -> Path | None:
    """bkit's target when it parses and carries a non-empty `orchestrator_state`."""
    target = bkit_target(state_file)
    if target is None:
        return None
    return target if _read_orchestrator_state(target) else None


def migrated_record(state_file: Path, feature: str) -> Path | None:
    """bkit's target when it holds a record for `feature`; None on any doubt."""
    target = bkit_target(state_file)
    if target is None:
        return None
    records = _read_orchestrator_state(target)
    if not records or not isinstance(records.get(feature), dict) or not records[feature]:
        return None
    return target


def restore_hint(state_file: Path, target: Path) -> str:
    return (f"bkit's SessionStart migration moved the h-mad state file to {target}. "
            f"Restore it by COPY, not move, so bkit keeps a target and does not "
            f"migrate it again: cp {target} {state_file}")
