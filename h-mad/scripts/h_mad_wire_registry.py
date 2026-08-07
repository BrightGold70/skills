#!/usr/bin/env python3
"""h_mad_wire_registry.py — Phase-5d registry schema and JSONL loader."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

VALID_KINDS: frozenset[str] = frozenset({"wire"})
VALID_PROVENANCE: frozenset[str] = frozenset({"superseded", "pinned-a-defect", "renamed"})
DEFAULT_REGISTRY = ".h-mad/wires.jsonl"


class RegistryError(Exception):
    """Malformed registry content — a cannot-judge, never a verdict."""


def validate_record(record: dict) -> dict:
    """Return the record, or raise RegistryError naming the offending field."""
    if not isinstance(record, dict):
        raise RegistryError("record must be an object")
    required = ("kind", "id", "caller", "callee", "pin", "owning_feature", "registered_ts")
    for field in required:
        if field not in record or record[field] in (None, ""):
            raise RegistryError(f"missing required field: {field}")
    if record["kind"] not in VALID_KINDS:
        raise RegistryError(f"invalid kind: {record['kind']!r}")
    if record.get("status", "active") == "removed":
        provenance = record.get("removal_provenance")
        if provenance not in VALID_PROVENANCE:
            raise RegistryError("missing or invalid removal_provenance")
        if not record.get("removed_by_feature"):
            raise RegistryError("missing removed_by_feature")
        if provenance == "superseded" and not record.get("superseding_feature"):
            raise RegistryError("missing superseding_feature")
        if provenance == "renamed" and not record.get("successor_pin"):
            raise RegistryError("missing successor_pin")
    return record


def load(path: Path) -> list[dict]:
    """Parse JSONL. Raises RegistryError naming the 1-based line number on a bad line."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    records: list[dict] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise RegistryError(f"invalid registry line {line_number}: {exc}") from exc
    return records


def register(entries: list[dict], path: Path) -> list[dict]:
    """Write a batch, then re-read and compare the stored records."""
    records = load(path)
    for entry in entries:
        if not isinstance(entry, dict):
            raise RegistryError("record must be an object")
        record = dict(entry)
        record["registered_ts"] = datetime.now(timezone.utc).isoformat()
        record.setdefault("status", "active")
        validate_record(record)
        for index, existing in enumerate(records):
            if existing["id"] == record["id"]:
                records[index] = record
                break
        else:
            records.append(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")
    try:
        stored = load(path)
    except (OSError, RegistryError) as exc:
        raise RegistryError(f"registry read-back failed: {exc}") from exc
    if stored != records:
        raise RegistryError("registry read-back mismatch")
    return stored
