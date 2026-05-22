#!/usr/bin/env python3
"""h_mad_telemetry.py — record/query /h-mad per-feature cycle telemetry.

Telemetry rows live at <PROJECT>/.h-mad/telemetry.jsonl (one JSON object per line,
newest appended last). The orchestrator calls `record` from Phase 7 closure
(before /pdca archive); operators can call `summary` anytime to inspect drift.

Usage:
  python3 h_mad_telemetry.py record --feature <slug> [--state PATH] [--out PATH]
  python3 h_mad_telemetry.py summary [--in PATH] [--limit N]

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


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _elapsed_min(started: str | None, completed: str) -> float | None:
    if not started:
        return None
    try:
        t0 = datetime.fromisoformat(started.replace("Z", "+00:00"))
        t1 = datetime.fromisoformat(completed.replace("Z", "+00:00"))
    except ValueError:
        return None
    return round((t1 - t0).total_seconds() / 60.0, 1)


def cmd_record(args: argparse.Namespace) -> int:
    state_path = pathlib.Path(args.state)
    out_path = pathlib.Path(args.out)
    try:
        state = json.loads(state_path.read_text())
    except FileNotFoundError:
        sys.stderr.write(f"state file not found: {state_path}\n")
        return 3
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"malformed state file: {exc}\n")
        return 3

    feat_state = state.get("orchestrator_state", {}).get(args.feature)
    if feat_state is None:
        sys.stderr.write(f"feature not found in orchestrator_state: {args.feature}\n")
        return 2

    completed_ts = _utcnow_iso()
    started_ts = feat_state.get("started_ts")
    entry = {
        "feature": args.feature,
        "started_ts": started_ts,
        "completed_ts": completed_ts,
        "elapsed_min": _elapsed_min(started_ts, completed_ts),
        "audit_cycles": feat_state.get("audit_cycles", {}) or {},
        "iterate_cycles": feat_state.get("iterate_cycles", 0),
        "last_completed_phase": feat_state.get("last_completed_phase"),
        "halt_reason": feat_state.get("halt_reason"),
        "schema_version": 1,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    print(f"recorded: {entry['feature']} → {out_path}")
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    in_path = pathlib.Path(args.input)
    if not in_path.is_file():
        print(f"no telemetry yet ({in_path}).")
        return 0
    rows: list[dict] = []
    for line in in_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if not rows:
        print("no telemetry entries.")
        return 0

    tail = rows[-args.limit:]
    header = f"{'feature':<35} {'plan':>4} {'des':>4} {'impl':>4} {'iter':>4} {'min':>6} {'status':<10}"
    print(header)
    print("-" * len(header))
    for r in tail:
        ac = r.get("audit_cycles") or {}
        plan = int(ac.get("plan", 0) or 0)
        design = int(ac.get("design", 0) or 0)
        impl = int(ac.get("impl_plan", 0) or 0)
        it = int(r.get("iterate_cycles", 0) or 0)
        elapsed = r.get("elapsed_min")
        elapsed_s = f"{elapsed:.0f}" if isinstance(elapsed, (int, float)) else "?"
        status = "halted" if r.get("halt_reason") else "complete"
        feat = str(r.get("feature", "?"))[:34]
        print(f"{feat:<35} {plan:>4} {design:>4} {impl:>4} {it:>4} {elapsed_s:>6} {status:<10}")

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
