#!/usr/bin/env python3
"""h_mad_wire_registry.py — Phase-5d registry schema and JSONL loader."""
from __future__ import annotations

import json
import re
import subprocess
import sys
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


def partition(
    records: list[dict], collected: set[str]
) -> tuple[list[dict], list[dict], list[dict]]:
    """-> (resolving, missing, unverified_renames). Pure; no subprocess, no git."""
    resolving: list[dict] = []
    missing: list[dict] = []
    unverified_renames: list[dict] = []
    for record in records:
        if record.get("status", "active") == "active":
            if record["pin"] in collected:
                resolving.append(record)
            else:
                missing.append(record)
            continue
        if record.get("removal_provenance") != "renamed":
            continue
        successor = record["successor_pin"]
        if successor in collected:
            resolved = dict(record)
            resolved["pin"] = successor
            resolving.append(resolved)
        else:
            unverified_renames.append(record)
    return resolving, missing, unverified_renames


def collect(rootdir: Path) -> set[str]:
    """Collect pytest node ids under rootdir."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=rootdir,
        capture_output=True,
        text=True,
        check=False,
    )
    node_ids: set[str] = set()
    for line in result.stdout.splitlines():
        line = line.strip()
        if "::" in line and not line.endswith(" tests collected"):
            node_ids.add(line)
    return node_ids


def run_pins(resolving: list[dict], rootdir: Path) -> tuple[list[dict], list[dict]]:
    """Run resolving pytest pins and return (verified, broken)."""
    if not resolving:
        return [], []
    pins = [record["pin"] for record in resolving]
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-rA", *pins],
        cwd=rootdir,
        capture_output=True,
        text=True,
        check=False,
    )
    passed: set[str] = set()
    failed: set[str] = set()
    for line in result.stdout.splitlines():
        match = re.match(r"^(PASSED|FAILED)\s+(\S+)", line.strip())
        if not match:
            continue
        (passed if match.group(1) == "PASSED" else failed).add(match.group(2))

    verified: list[dict] = []
    broken: list[dict] = []
    for record in resolving:
        pin = record["pin"]
        if pin in failed:
            broken.append(record)
            print(f"BROKEN {record['owning_feature']}: {pin}")
        elif pin in passed:
            verified.append(record)
        else:
            print(f"INTERNAL INCONSISTENCY: unclassified pin {pin}")
    return verified, broken
