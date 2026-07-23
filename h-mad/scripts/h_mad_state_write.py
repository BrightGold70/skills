#!/usr/bin/env python3
"""h_mad_state_write.py - the write path for orchestrator_state.

There was none. `h_mad_resume_decision.py` reads state, `h_mad_telemetry.py`
reads it, and the orchestrator wrote it by following prose in SKILL.md. That is
why an established store drifted to 38 record shapes over 53 distinct keys
against a 13-key schema, and why the two-tier validator could only ever be
documentation: nothing sat between an invented key and the file.

This module is that seam. Three properties, in order of importance:

1. **Validate before the bytes land.** A record that fails the strict v2.2
   schema is rejected and the file is left byte-identical. An invented key
   cannot reach disk, so "never invent a key" stops being a rule the writer has
   to remember and becomes one it cannot break.
2. **Atomic replace.** Write a sibling temp file, `os.replace` it over the
   target. A crash mid-write leaves the previous store intact rather than a
   truncated one.
3. **Exclusive lock for the read-modify-write.** Two sessions writing different
   features must not clobber each other, which is the foundation the
   feature-level concurrency guard needs.

Only the record being written is validated. Real stores hold legacy records
that predate v2.2; validating the whole store on every write would make the
writer unusable on any project with history.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from h_mad_state_validate import classify  # noqa: E402


class StateWriteError(Exception):
    """The write was refused. The store is unchanged."""


_NEW_RECORD_DEFAULTS: dict[str, Any] = {
    "last_completed_phase": 0,
    "current_phase": 0,
    "phase": None,
    "autonomous_entry_ts": None,
    "audit_cycles": {"plan": 0, "design": 0, "impl_plan": 0},
    "iterate_cycles": 0,
    "halt_reason": None,
    "halt_ts": None,
}


def _load(state_file: Path) -> dict:
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
    except OSError as exc:
        raise StateWriteError(f"cannot read state file: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise StateWriteError(f"state file is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise StateWriteError("state file root is not an object")
    data.setdefault("orchestrator_state", {})
    if not isinstance(data["orchestrator_state"], dict):
        raise StateWriteError("orchestrator_state is not an object")
    return data


def _atomic_write(state_file: Path, data: dict) -> None:
    """Replace the store in one step, leaving no partial file behind."""
    fd, tmp = tempfile.mkstemp(
        dir=str(state_file.parent), prefix=f".{state_file.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, state_file)
    except BaseException:
        # Never leave a stray temp file behind on any failure path.
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _mutate(state_file: Path, feature: str, apply) -> dict:
    """Locked read-modify-write. `apply(records)` returns the new record.

    The lock is held on a sidecar rather than the store itself, because the
    store is replaced by `os.replace` and a lock on the old inode would not
    cover the new one.
    """
    state_file = Path(state_file)
    if not state_file.is_file():
        raise StateWriteError(f"no such state file: {state_file}")

    lock_path = state_file.with_suffix(state_file.suffix + ".lock")
    with open(lock_path, "w", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            data = _load(state_file)
            records = data["orchestrator_state"]
            record = apply(records)
            if record is not None:
                verdict = classify(record)
                if verdict != "strict":
                    raise StateWriteError(
                        f"record for {feature!r} would not validate "
                        f"(classified {verdict}); refusing to write. "
                        "If a new field is genuinely needed, declare it in "
                        "h_mad_state_schema.json rather than writing it ad hoc."
                    )
                records[feature] = record
                _atomic_write(state_file, data)
            return records.get(feature, {})
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def create_feature(state_file: Path, feature: str, started_ts: str | None = None) -> dict:
    """Create a v2.2 record. Idempotent — an existing record is left alone."""

    def apply(records: dict):
        if feature in records:
            return None  # already present; do not clobber
        record = dict(_NEW_RECORD_DEFAULTS)
        record["feature"] = feature
        record["started_ts"] = started_ts or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return record

    return _mutate(state_file, feature, apply)


def set_fields(state_file: Path, feature: str, **fields: Any) -> dict:
    """Merge `fields` into an existing record, validating before writing."""

    def apply(records: dict):
        if feature not in records:
            raise StateWriteError(f"no such feature: {feature}")
        return {**records[feature], **fields}

    return _mutate(state_file, feature, apply)


def claim(
    state_file: Path,
    feature: str,
    session_id: str,
    now: str | None = None,
    force: bool = False,
) -> dict:
    """Take ownership of a feature, refreshing the heartbeat.

    Advisory. A second session is refused unless `force` — which must exist,
    because a session that crashes mid-feature would otherwise hold it forever.
    Staleness is judged at read time by the resume decision, not here: this only
    records who and when.
    """

    def apply(records: dict):
        if feature not in records:
            raise StateWriteError(f"no such feature: {feature}")
        record = records[feature]
        held_by = record.get("owner_session_id")
        if held_by and held_by != session_id and not force:
            raise StateWriteError(
                f"{feature!r} is owned by session {held_by!r} "
                f"(last seen {record.get('owner_heartbeat_ts')}). "
                "Coordinate, or pass force to take over."
            )
        return {
            **record,
            "owner_session_id": session_id,
            "owner_heartbeat_ts": now or _utc_now(),
        }

    return _mutate(state_file, feature, apply)


def release(state_file: Path, feature: str) -> dict:
    """Give up ownership. Safe to call when unowned."""

    def apply(records: dict):
        if feature not in records:
            raise StateWriteError(f"no such feature: {feature}")
        return {
            **records[feature],
            "owner_session_id": None,
            "owner_heartbeat_ts": None,
        }

    return _mutate(state_file, feature, apply)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_value(raw: str) -> Any:
    """`phase=null` -> None, `current_phase=5` -> 5, everything else a string."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def main(argv: list[str] | None = None) -> int:
    """Run the state write CLI."""
    parser = argparse.ArgumentParser(description="H-MAD orchestrator_state writer")
    parser.add_argument("state_file", type=Path)
    parser.add_argument("--feature", required=True)
    parser.add_argument("--create", action="store_true", help="Create the record if absent")
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Field to set. Values are parsed as JSON when possible, else kept "
        "as strings — so phase=null writes null and current_phase=5 writes 5.",
    )
    parser.add_argument("--started-ts", help="started_ts for --create")
    parser.add_argument("--claim", metavar="SESSION_ID", help="Take ownership of the feature")
    parser.add_argument("--release", action="store_true", help="Give up ownership")
    parser.add_argument(
        "--force", action="store_true", help="With --claim, take over an existing claim"
    )
    args = parser.parse_args(argv)

    try:
        if args.create:
            create_feature(args.state_file, args.feature, args.started_ts)
        if args.claim:
            claim(args.state_file, args.feature, args.claim, force=args.force)
        if args.release:
            release(args.state_file, args.feature)
        fields = {}
        for item in args.set:
            if "=" not in item:
                print(f"ERROR: --set expects KEY=VALUE, got {item!r}", file=sys.stderr)
                return 2
            key, _, raw = item.partition("=")
            fields[key.strip()] = _parse_value(raw)
        if fields:
            set_fields(args.state_file, args.feature, **fields)
    except StateWriteError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    written = sorted(f.partition("=")[0].strip() for f in args.set)
    print(
        f"STATE-WRITE: OK feature={args.feature} "
        f"keys={len(written)}{' ' + ','.join(written) if written else ''}"
    )
    print(f"[H-MAD] {args.feature} state written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
