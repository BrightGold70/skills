#!/usr/bin/env python3
"""h_mad_state_validate.py - two-tier validation of orchestrator_state.

The v2.2 schema governs records written from now on. It was never enforced at
write time and forbade extra properties, so established stores drifted into
many one-off shapes and whole-store validation always failed - which made the
documented check useless, so it went unrun.

Two tiers make the check meaningful again:

  STRICT      - conforms to h_mad_state_schema.json (v2.2). Required of new
                records; pass --strict-only after writing one.
  HISTORICAL  - conforms to h_mad_state_schema_historical.json: the three
                fields every observed record carries, extras allowed.
  INVALID     - conforms to neither. Genuinely broken; worth a human look.

Signalling follows the audit gate: print a verdict token and exit 0. A
non-zero exit is reserved for operational errors (missing file, bad JSON,
unknown feature) so a FAIL verdict never registers as a tool failure.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft7Validator
except ImportError:  # pragma: no cover - dependency guard
    print("ERROR: jsonschema is required", file=sys.stderr)
    sys.exit(2)

SCRIPT_DIR = Path(__file__).resolve().parent
STRICT_SCHEMA = SCRIPT_DIR / "h_mad_state_schema.json"
HISTORICAL_SCHEMA = SCRIPT_DIR / "h_mad_state_schema_historical.json"

_validators: dict[str, Draft7Validator] = {}


def _validator(path: Path) -> Draft7Validator:
    key = str(path)
    if key not in _validators:
        _validators[key] = Draft7Validator(json.loads(path.read_text(encoding="utf-8")))
    return _validators[key]


def classify(record: object) -> str:
    """Return 'strict', 'historical', or 'invalid' for one feature record."""
    if not isinstance(record, dict):
        return "invalid"
    if _validator(STRICT_SCHEMA).is_valid(record):
        return "strict"
    if _validator(HISTORICAL_SCHEMA).is_valid(record):
        return "historical"
    return "invalid"


def classify_store(records: dict, strict_only: bool = False) -> dict:
    """Classify every record; verdict is FAIL if any record misses its bar."""
    tiers = {"strict": [], "historical": [], "invalid": []}
    for feature, record in records.items():
        tiers[classify(record)].append(feature)

    failing = list(tiers["invalid"])
    if strict_only:
        failing += tiers["historical"]

    return {
        "verdict": "FAIL" if failing else "PASS",
        "strict": tiers["strict"],
        "historical": tiers["historical"],
        "invalid": tiers["invalid"],
        "failing": sorted(failing),
    }


def main(argv: list[str] | None = None) -> int:
    """Run the state validation CLI."""
    parser = argparse.ArgumentParser(description="H-MAD orchestrator_state validator")
    parser.add_argument("state_file", type=Path)
    parser.add_argument(
        "--feature",
        help="Validate only this feature's record (use after writing it).",
    )
    parser.add_argument(
        "--strict-only",
        action="store_true",
        help="Require v2.2. Historical records count as failures.",
    )
    args = parser.parse_args(argv)

    try:
        state = json.loads(args.state_file.read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: {args.state_file}: {exc}", file=sys.stderr)
        return 2

    records = state.get("orchestrator_state") or {}
    if not isinstance(records, dict):
        print("ERROR: orchestrator_state is not an object", file=sys.stderr)
        return 2

    if args.feature:
        if args.feature not in records:
            print(f"ERROR: no such feature: {args.feature}", file=sys.stderr)
            return 2
        records = {args.feature: records[args.feature]}

    result = classify_store(records, strict_only=args.strict_only)
    print(
        f"STATE: {result['verdict']}"
        f" strict={len(result['strict'])}"
        f" historical={len(result['historical'])}"
        f" invalid={len(result['invalid'])}"
    )
    for feature in result["failing"]:
        tier = classify(records[feature])
        print(f"  {tier}: {feature}")
    scope = args.feature or "store"
    print(f"[H-MAD] {scope} state {result['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
