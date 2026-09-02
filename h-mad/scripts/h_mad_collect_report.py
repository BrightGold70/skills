#!/usr/bin/env python3
"""Collect one H-MAD audit report into the docs audit path."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from h_mad_audit_cycle import (
    CollectConflict,
    OperationalError,
    PassSpec,
    _collected_path,
    collect,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature", required=True)
    parser.add_argument("--phase", choices=("plan", "design", "impl-plan"), required=True)
    parser.add_argument("--cycle", type=int, required=True)
    parser.add_argument("--surface", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--out")
    parser.add_argument("--grace", type=float, default=5.0)
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
    except SystemExit:
        print("[H-MAD] unknown collect usage_error")
        return 2

    try:
        return _run(args)
    except (OperationalError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        reason = "readback_failed" if str(exc).startswith("readback") else "operational_error"
        print(f"[H-MAD] {args.feature} collect {reason}")
        return 2


def _run(args: argparse.Namespace) -> int:
    if args.cycle < 1:
        raise ValueError(f"invalid cycle: {args.cycle}")

    project_root = Path(args.project_root)
    if not project_root.is_dir():
        raise OperationalError(f"project root is not a directory: {project_root}")

    report_path = Path(args.report)
    out_path = Path(args.out) if args.out else None
    collected_path = _collected_path(
        project_root=project_root,
        feature=args.feature,
        phase=args.phase,
        cycle=args.cycle,
        index=1,
        surface=args.surface,
    )
    collected_path.parent.mkdir(parents=True, exist_ok=True)
    if not collected_path.parent.is_dir():
        raise OperationalError(f"collected report parent is not a directory: {collected_path.parent}")

    same_report_path = report_path.resolve() == collected_path.resolve()
    spec = PassSpec(index=1, report_path=report_path, out_path=out_path, rc=0)
    forced = False

    try:
        delivered, path = collect(
            spec,
            grace=args.grace,
            project_root=project_root,
            feature=args.feature,
            phase=args.phase,
            cycle=args.cycle,
            surface=args.surface,
            overwrite=False,
        )
    except CollectConflict as conflict:
        if not args.force:
            print(f"COLLECT: CONFLICT path={conflict.collected} delivered={conflict.delivered}")
            print(f"[H-MAD] {args.feature} collect CONFLICT")
            return 0
        delivered, path = collect(
            spec,
            grace=args.grace,
            project_root=project_root,
            feature=args.feature,
            phase=args.phase,
            cycle=args.cycle,
            surface=args.surface,
            overwrite=True,
        )
        forced = True

    verdict = "OK" if path is not None else "MISSING"
    printed_path = path if path is not None else collected_path
    line = f"COLLECT: {verdict} path={printed_path} delivered={delivered}"
    if forced:
        line += " forced=1"
    print(line)
    if same_report_path and delivered == "report-file":
        print(f"marker: removed {report_path}.done")
    print(f"[H-MAD] {args.feature} collect {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
