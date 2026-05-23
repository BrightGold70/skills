#!/usr/bin/env python3
"""h_mad_telemetry.py — record/query /h-mad per-feature cycle telemetry.

Telemetry rows live at <PROJECT>/.h-mad/telemetry.jsonl (one JSON object per line,
newest appended last). The orchestrator calls `record` from Phase 7 closure
(before Phase 7 archive); operators can call `summary` anytime to inspect drift.

Usage:
  python3 h_mad_telemetry.py record --feature <slug> [--state PATH] [--out PATH]
  python3 h_mad_telemetry.py summary [--input PATH] [--limit N]

Exit codes:
  0 = success
  2 = feature not present in state (record only)
  3 = malformed state file (record only)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone


def cmd_record(args: argparse.Namespace) -> int:
    state_path = pathlib.Path(args.state)
    out_path = pathlib.Path(args.out)

    if not state_path.is_file():
        print(f"WARN: state file not found at {state_path} — skipping telemetry record", file=sys.stderr)
        return 2

    try:
        state = json.loads(state_path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        print(f"WARN: malformed state file: {e} — skipping telemetry record", file=sys.stderr)
        return 3

    orchestrator_state = state.get("orchestrator_state") or {}
    feat_state = orchestrator_state.get(args.feature)
    if not feat_state:
        print(f"WARN: feature '{args.feature}' not found in state — skipping telemetry record", file=sys.stderr)
        return 2

    audit_cycles = feat_state.get("audit_cycles") or {}
    row = {
        "feature": args.feature,
        "recorded_ts": datetime.now(timezone.utc).isoformat(),
        "started_ts": feat_state.get("started_ts"),
        "last_completed_phase": feat_state.get("last_completed_phase", 0),
        "audit_cycles": {
            "plan": audit_cycles.get("plan", 0),
            "design": audit_cycles.get("design", 0),
            "impl_plan": audit_cycles.get("impl_plan", 0),
        },
        "iterate_cycles": feat_state.get("iterate_cycles", 0),
        "halt_reason": feat_state.get("halt_reason"),
    }

    # Compute elapsed if started_ts is available
    if row["started_ts"]:
        try:
            start = datetime.fromisoformat(row["started_ts"].replace("Z", "+00:00"))
            elapsed = datetime.now(timezone.utc) - start
            row["elapsed_min"] = round(elapsed.total_seconds() / 60, 1)
        except (ValueError, TypeError):
            pass

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a") as f:
        f.write(json.dumps(row) + "\n")

    print(f"Telemetry recorded to {out_path}: feature={args.feature}, "
          f"audit_cycles={row['audit_cycles']}, iterate_cycles={row['iterate_cycles']}")
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    in_path = pathlib.Path(args.input)
    if not in_path.is_file():
        print(f"No telemetry file at {in_path}")
        return 0

    rows = []
    for line in in_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    if not rows:
        print("No telemetry rows found.")
        return 0

    tail = rows[-args.limit:]
    print(f"=== /h-mad telemetry — last {len(tail)} of {len(rows)} records ===\n")
    print(f"{'feature':<30} {'phase':>5} {'plan_a':>6} {'des_a':>6} {'impl_a':>6} {'iter':>5} {'elapsed':>8}")
    print("-" * 75)
    for r in tail:
        ac = r.get("audit_cycles") or {}
        print(
            f"{r.get('feature', '?'):<30}"
            f"{r.get('last_completed_phase', 0):>5}"
            f"{ac.get('plan', 0):>7}"
            f"{ac.get('design', 0):>7}"
            f"{ac.get('impl_plan', 0):>7}"
            f"{r.get('iterate_cycles', 0):>6}"
            f"{str(r.get('elapsed_min', '?')) + 'm':>9}"
        )

    n_high_audit = sum(
        1 for r in tail
        if any(int(v or 0) > 3 for v in (r.get("audit_cycles") or {}).values())
    )
    n_high_iter = sum(1 for r in tail if int(r.get("iterate_cycles", 0) or 0) > 3)
    if n_high_audit or n_high_iter:
        print()
        if n_high_audit:
            print(f"WARN: {n_high_audit} feature(s) hit audit_cycles > 3 — possible plan/design quality drift")
        if n_high_iter:
            print(f"WARN: {n_high_iter} feature(s) hit iterate_cycles > 3 — possible implementation drift")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="h_mad_telemetry.py",
        description="Record/query /h-mad per-feature cycle telemetry.",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_record = sub.add_parser("record", help="append a feature's cycle counts to telemetry log")
    p_record.add_argument("--feature", required=True)
    p_record.add_argument("--state", default="docs/.bkit-memory.json")
    p_record.add_argument("--out", default=".h-mad/telemetry.jsonl")

    p_summary = sub.add_parser("summary", help="print recent telemetry rows + drift signal")
    p_summary.add_argument("--input", default=".h-mad/telemetry.jsonl")
    p_summary.add_argument("--limit", type=int, default=20)

    args = ap.parse_args(argv)
    if args.cmd == "record":
        return cmd_record(args)
    return cmd_summary(args)


if __name__ == "__main__":
    sys.exit(main())
