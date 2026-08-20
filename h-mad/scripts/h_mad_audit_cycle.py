#!/usr/bin/env python3
"""h_mad_audit_cycle.py - combine and render H-MAD audit pass verdicts."""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import namedtuple
from pathlib import Path


PassSpec = namedtuple("PassSpec", "index report_path out_path rc")
PassResult = namedtuple(
    "PassResult", "index delivered collected_path verdict must should findings"
)


class OperationalError(Exception):
    """The audit cycle could not form a trustworthy verdict."""


def _script(name: str) -> Path:
    """Return a sibling script path, with a test-only directory override."""
    override = os.environ.get("HMAD_AUDIT_CYCLE_SCRIPT_DIR")
    if override:
        return Path(override) / name
    return Path(__file__).resolve().parent / name


def _collected_path(
    *,
    project_root: Path,
    feature: str,
    phase: str,
    cycle: int,
    index: int,
) -> Path:
    """Return the collected audit report path for one audit pass."""
    audit_dirs = {
        "plan": Path("docs/01-plan/features"),
        "design": Path("docs/02-design/features"),
        "impl-plan": Path("docs/01-plan/features"),
    }
    return (
        project_root
        / audit_dirs[phase]
        / f"{feature}.{phase}.audit.v{cycle}.p{index}.md"
    )


def combine(results: list[PassResult]) -> tuple[str, str | None]:
    """Combine pass results into an audit-cycle verdict and reason."""
    for result in results:
        if result.delivered != "none" and result.verdict is None:
            raise OperationalError(
                f"missing GATE token for p{result.index} after delivered output"
            )

    for result in results:
        if result.delivered == "none":
            return "UNVERIFIED", f"no_report:p{result.index}"
        if result.verdict == "INVALID":
            return "UNVERIFIED", f"no_gate_sections:p{result.index}"

    for result in results:
        if result.verdict == "FAIL":
            return "FAIL", f"findings:p{result.index}"

    return "PASS", None


def _one_line(text: object) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


def premise_items(results: list[PassResult]) -> list[str]:
    """Format pass findings as premise checklist items without parsing them."""
    items: list[str] = []
    for result in results:
        for finding in result.findings:
            severity = finding.get("severity", "")
            text = _one_line(finding.get("text", ""))
            path = finding.get("path")
            line = finding.get("line")
            if path and line is not None:
                citation = f"{path}:{line}"
            else:
                citation = "(no citation)"
            items.append(f"p{result.index} {severity} {citation}: {text}")
    return items


def render(
    results: list[PassResult],
    verdict: str,
    reason: str | None,
    *,
    feature: str,
    size_status: str,
    passes: int,
) -> str:
    """Render the single AUDITCYCLE contract line and human premise checklist."""
    fields = [f"AUDITCYCLE: {verdict}"]
    if reason is not None:
        fields.append(f"reason={reason}")
    fields.extend([f"passes={passes}", f"size_status={size_status}"])

    if verdict != "UNVERIFIED":
        must = sum(result.must for result in results)
        should = sum(result.should for result in results)
        fields.extend([f"must={must}", f"should={should}"])
        fields.extend(f"p{result.index}={result.verdict}" for result in results)
    elif any(result.delivered != "none" for result in results):
        delivered = ",".join(f"p{result.index}:{result.delivered}" for result in results)
        fields.append(f"delivered={delivered}")

    lines = [" ".join(fields)]
    items = premise_items(results)
    if items:
        lines.append("Premise checklist:")
        lines.extend(f"- {item}" for item in items)
    else:
        lines.append("Premise checklist: empty")
    lines.append(f"[H-MAD] {feature} audit-cycle {verdict}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Run the audit-cycle helper."""
    parser = argparse.ArgumentParser(description="H-MAD audit cycle", allow_abbrev=False)
    parser.add_argument("--feature", required=True)
    parser.add_argument("--phase", required=True, choices=("plan", "design", "impl-plan"))
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--passes", type=int, required=True)
    parser.add_argument("--size-status", default="verified")
    parser.add_argument("--halt-reason")

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)

    if args.passes <= 0:
        print("ERROR: --passes must be positive", file=sys.stderr)
        return 2

    if not args.halt_reason:
        print("ERROR: exactly one audit-cycle mode is required", file=sys.stderr)
        return 2

    text = render(
        [],
        "UNVERIFIED",
        args.halt_reason,
        feature=args.feature,
        size_status=args.size_status,
        passes=args.passes,
    )
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
