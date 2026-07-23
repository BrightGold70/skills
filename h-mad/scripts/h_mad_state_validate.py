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

class _MiniDraft7:
    """A stdlib validator for exactly the Draft-07 subset these schemas use.

    J4/F8: `jsonschema` is absent from a stock Homebrew/PEP-668 `python3`, so
    every state call in a run exited 2 until the operator hand-substituted
    another interpreter -- hit twice in the first five minutes of one run. F8
    shipped a better *message*, which is not a fix for a missing dependency.

    Of the filed options, degrading to the historical tier when `jsonschema` is
    missing was rejected: silently validating against a weaker schema is the same
    class of defect as an unenforced guard. Bundling a validator removes the
    dependency instead, which is also what `invariants.base.md` §"No new external
    dependency" wants.

    Deliberately supports ONLY the constructs present in
    `h_mad_state_schema*.json` -- `type` (incl. lists), `enum`, `required`,
    `properties`, `additionalProperties` (bool or schema), `items`, `minimum`,
    `maximum`, `minLength`. An unknown keyword is IGNORED, matching Draft-07,
    rather than guessed at.

    `format` is ignored on purpose. Draft-07 treats it as an annotation unless a
    format checker is supplied and the production path supplies none, so
    `started_ts: "not-a-date"` is valid today. Enforcing it here would reject
    records the real validator accepts -- a regression dressed as an improvement.

    `jsonschema` still wins when importable; this only carries the run when it is
    not. `tests/test_h_mad_state_validate_fallback.py` asserts the two agree on
    every construct and on the live records, which is the only thing that makes a
    hand-rolled validator trustworthy.
    """

    _TYPES = {
        "object": dict, "array": list, "string": str,
        "number": (int, float), "boolean": bool,
    }

    def __init__(self, schema: dict) -> None:
        self.schema = schema

    def is_valid(self, instance: object) -> bool:
        return self._ok(self.schema, instance)

    @classmethod
    def _type_ok(cls, expected: object, value: object) -> bool:
        names = expected if isinstance(expected, list) else [expected]
        for name in names:
            if name == "null":
                if value is None:
                    return True
            elif name == "integer":
                # bool is a subclass of int in Python; JSON Schema treats them
                # as distinct types.
                if isinstance(value, int) and not isinstance(value, bool):
                    return True
            elif name == "boolean":
                if isinstance(value, bool):
                    return True
            elif name == "number":
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    return True
            else:
                py = cls._TYPES.get(str(name))
                if py is not None and isinstance(value, py):
                    return True
        return False

    def _ok(self, schema: object, value: object) -> bool:
        if not isinstance(schema, dict):
            return True
        if "type" in schema and not self._type_ok(schema["type"], value):
            return False
        if "enum" in schema and value not in schema["enum"]:
            return False
        if isinstance(value, str) and "minLength" in schema:
            if len(value) < schema["minLength"]:
                return False
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in schema and value < schema["minimum"]:
                return False
            if "maximum" in schema and value > schema["maximum"]:
                return False
        if isinstance(value, list) and "items" in schema:
            if not all(self._ok(schema["items"], item) for item in value):
                return False
        if isinstance(value, dict):
            props = schema.get("properties", {})
            for name in schema.get("required", []):
                if name not in value:
                    return False
            for name, sub in props.items():
                if name in value and not self._ok(sub, value[name]):
                    return False
            extra = schema.get("additionalProperties", True)
            if extra is not True:
                for name, item in value.items():
                    if name in props:
                        continue
                    if extra is False or not self._ok(extra, item):
                        return False
        return True


try:
    from jsonschema import Draft7Validator as _Draft7Validator
except ImportError:  # pragma: no cover - exercised by the fallback test
    _Draft7Validator = None

# Test seam: force the bundled path even where jsonschema is installed, so the
# differential tests can compare both backends in one process.
_FORCE_FALLBACK = False


def _make_validator(schema: dict):
    if _Draft7Validator is None or _FORCE_FALLBACK:
        return _MiniDraft7(schema)
    return _Draft7Validator(schema)

SCRIPT_DIR = Path(__file__).resolve().parent
STRICT_SCHEMA = SCRIPT_DIR / "h_mad_state_schema.json"
HISTORICAL_SCHEMA = SCRIPT_DIR / "h_mad_state_schema_historical.json"

_validators: dict = {}


def _validator(path: Path):
    key = str(path)
    if key not in _validators:
        _validators[key] = _make_validator(json.loads(path.read_text(encoding="utf-8")))
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
