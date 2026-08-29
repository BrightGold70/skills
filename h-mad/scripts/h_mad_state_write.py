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

Property 1 has a corollary that took a live incident to find (J48). Validating
the merged record means a key that reached the store by some OTHER route — a
hand-edit, a record written before this module existed — makes that record
unwritable here forever: claim, release and halt-recording all refused, on a
feature halted mid-Phase-5, leaving the hand-edit as the only way out. A guard
whose only escape is the practice it exists to prevent is not finished. So the
refusal names the offending keys and distinguishes the ones the current write
introduced from the ones already there, and `drop_undeclared()` is the sanctioned
repair — removal, not a wider schema, because the keys that cause this are by
construction ones nothing reads.
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

from h_mad_state_ownership import owner_is_live  # noqa: E402
from h_mad_state_validate import classify, undeclared_keys  # noqa: E402


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


def _refusal(feature: str, record: dict, prior: dict) -> str:
    """Say which keys are wrong and, for a pre-existing one, how to get out.

    The old message said only "classified historical", which names a tier rather
    than a cause and leaves the operator no move but to read the JSON by hand —
    the one act the write path exists to prevent. Worse, it read as a complaint
    about the write being attempted when the offending keys were usually already
    on the record, so the write being blamed was innocent (J48).
    """
    unknown = undeclared_keys(record)
    if not unknown:
        return (
            f"record for {feature!r} would not validate "
            f"(classified {classify(record)}); refusing to write. "
            "The store is unchanged."
        )
    introduced = [key for key in unknown if key not in prior]
    preexisting = [key for key in unknown if key in prior]
    parts = [
        f"record for {feature!r} carries {len(unknown)} key(s) the schema does "
        f"not declare: {', '.join(unknown)}."
    ]
    if introduced:
        parts.append(
            f"This write introduces {', '.join(introduced)}. If the field is "
            "genuinely needed, declare it in h_mad_state_schema.json rather than "
            "writing it ad hoc."
        )
    if preexisting:
        parts.append(
            f"{', '.join(preexisting)} "
            f"{'was' if len(preexisting) == 1 else 'were'} already on the record "
            "before this write, so EVERY write to this feature is refused until "
            "it is gone — including --release, which is how a stale claim would "
            f"normally be cleared. Repair with: --feature {feature} "
            "--drop-undeclared (it names what it removes and validates what is "
            "left)."
        )
    parts.append("Refusing to write; the store is unchanged.")
    return " ".join(parts)


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
                if classify(record) != "strict":
                    raise StateWriteError(
                        _refusal(feature, record, records.get(feature, {}))
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


def drop_undeclared(state_file: Path, feature: str) -> tuple[dict, list[str]]:
    """Strip keys the strict schema does not declare. The sanctioned repair.

    The write guard is right to refuse an undeclared key, but it validates the
    whole merged record, so a key that reached the store by some other route —
    a hand-edit, a record predating the guard — makes the record permanently
    unwritable through the only tool allowed to write it. Claim, release and
    halt-recording were all refused on a feature halted mid-Phase-5, and the
    single documented remedy ("declare it in the schema") is the wrong one for
    a key nothing reads: it buys the record's mobility by permanently widening
    the schema for a field that was never real.

    So the repair is removal, and it is its own verb rather than a flag on the
    other writes. A caller asking to release a claim is not asking to discard
    fields, and the operator who repairs a record should see exactly which keys
    went. Returns `(record, removed)`; `removed` is empty when there was nothing
    to repair, which makes the call idempotent.

    What is left is validated like any other write, so a record that is broken
    for some other reason — a missing required field, a bad type — is still
    refused, and stripping cannot launder it into the store.
    """
    removed: list[str] = []

    def apply(records: dict):
        if feature not in records:
            raise StateWriteError(f"no such feature: {feature}")
        record = records[feature]
        removed.extend(undeclared_keys(record))
        if not removed:
            return None  # nothing to repair; leave the store byte-identical
        return {key: value for key, value in record.items() if key not in removed}

    return _mutate(state_file, feature, apply), removed


def claim(
    state_file: Path,
    feature: str,
    session_id: str,
    now: str | None = None,
    force: bool = False,
) -> dict:
    """Take ownership of a feature, refreshing the heartbeat.

    Advisory. A second session is refused while the current owner still looks
    live; once its heartbeat goes stale the claim is treated as abandoned and
    can be taken without `force`.

    That staleness allowance is not a convenience. It previously lived only in
    the resume router, so the router could return `enter_autonomous` on a
    19.6h-dead claim while this function refused the very same claim — leaving
    `force` as the only way through. `force` is the verb for taking a feature
    from a session that is still RUNNING; routing the routine crashed-session
    case through it teaches an operator to pass it by reflex, which is how the
    guard stops protecting the case it exists for. Both halves now read one
    window (`h_mad_state_ownership`) so they cannot disagree again.

    An absent or unreadable heartbeat counts as live, so this fails closed.
    """

    def apply(records: dict):
        if feature not in records:
            raise StateWriteError(f"no such feature: {feature}")
        record = records[feature]
        held_by = record.get("owner_session_id")
        if (
            held_by
            and held_by != session_id
            and not force
            and owner_is_live(record.get("owner_heartbeat_ts"), now)
        ):
            raise StateWriteError(
                f"{feature!r} is owned by session {held_by!r} "
                f"(last seen {record.get('owner_heartbeat_ts')}, still live). "
                "Coordinate, or pass force to take over."
            )
        return {
            **record,
            "owner_session_id": session_id,
            "owner_heartbeat_ts": now or _utc_now(),
        }

    return _mutate(state_file, feature, apply)


def release(
    state_file: Path,
    feature: str,
    session_id: str | None = None,
    force: bool = False,
) -> dict:
    """Give up ownership. Safe to call when unowned.

    Guarded on the SAME staleness window as `claim` (`h_mad_state_ownership`), and
    for the same reason. This function used to clear the owner unconditionally,
    which made `--release` + `--claim` a complete bypass of `claim`'s force guard:
    a live owner's in-flight feature changed hands with no `force` anywhere, exit 0
    at every step and no warning to anyone (J45). `claim`'s docstring already
    argues the principle — `force` is the verb for taking a feature from a session
    that is still RUNNING — and an unguarded release is that same erosion reached
    by a different route.

    Three cases stay free, so the guard cannot teach a force reflex:

      * unowned — nothing to protect;
      * a STALE owner — ordinary cleanup after a crashed session, which is exactly
        the case `claim` refuses to route through `force`;
      * `session_id` matching the live owner — a session releasing its OWN claim,
        which is the routine end of every piece of work.

    Only releasing a claim that is live AND someone else's is a takeover, and only
    that needs `force`. An unidentified caller on a live claim fails closed: that
    is the ad-hoc terminal case, which is where the accidental release happens, and
    the refusal names `--session-id` rather than `--force` so the routine remedy is
    the one an operator reaches for.
    """

    def apply(records: dict):
        if feature not in records:
            raise StateWriteError(f"no such feature: {feature}")
        record = records[feature]
        owner = record.get("owner_session_id")
        if owner and not force and owner != session_id:
            from h_mad_state_ownership import owner_is_live

            if owner_is_live(record.get("owner_heartbeat_ts")):
                who = (
                    f"you passed --session-id {session_id!r}"
                    if session_id else "you did not say which session you are"
                )
                raise StateWriteError(
                    f"{feature!r} is owned by session {owner!r} and still live "
                    f"({who}); refusing to release. If it is YOURS, pass "
                    f"--session-id {owner!r}. If you are taking it from a running "
                    "session, that is a takeover — pass force, and coordinate first."
                )
        return {
            **record,
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
    parser.add_argument(
        "--drop-undeclared", action="store_true",
        help="Remove keys the schema does not declare, naming each one. The "
             "repair for a record made unwritable by an ad-hoc key — including "
             "one that reached the store by hand-edit (J48). Runs before any "
             "other operation in the same invocation, so a bricked record can "
             "be repaired and released in one command.",
    )
    parser.add_argument("--claim", metavar="SESSION_ID", help="Take ownership of the feature")
    parser.add_argument("--release", action="store_true", help="Give up ownership")
    parser.add_argument(
        "--session-id", dest="session_id", default=None,
        help="With --release, who you are. A session releasing its OWN live claim "
             "needs this; a stale or unowned claim does not. Without it, releasing a "
             "LIVE claim is refused rather than silently taking it (J45).",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="With --claim, take over an existing claim. With --release, give up "
             "ANOTHER live session's claim — a takeover either way."
    )
    args = parser.parse_args(argv)

    try:
        if args.create:
            create_feature(args.state_file, args.feature, args.started_ts)
        if args.drop_undeclared:
            # Before the other operations: repairing and releasing a bricked
            # record in one command is the whole point of the verb.
            _, removed = drop_undeclared(args.state_file, args.feature)
            if removed:
                print(f"STATE-WRITE: DROPPED feature={args.feature} "
                      f"keys={len(removed)} {','.join(removed)}")
            else:
                print(f"STATE-WRITE: DROPPED feature={args.feature} keys=0")
        if args.claim:
            claim(args.state_file, args.feature, args.claim, force=args.force)
        if args.release:
            release(args.state_file, args.feature, args.session_id, args.force)
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
