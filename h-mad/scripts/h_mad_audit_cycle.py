#!/usr/bin/env python3
"""h_mad_audit_cycle.py - combine and render H-MAD audit pass verdicts."""
from __future__ import annotations

import argparse
import os
import re
import subprocess
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


def _done_path(report_path: Path) -> Path:
    return Path(str(report_path) + ".done")


def _has_complete_report(report_path: Path) -> bool:
    return (
        report_path.exists()
        and report_path.stat().st_size > 0
        and _done_path(report_path).exists()
    )


def _copy_collected_report(report_path: Path, collected_path: Path) -> Path:
    collected_path.parent.mkdir(parents=True, exist_ok=True)
    collected_path.write_bytes(report_path.read_bytes())
    if not collected_path.exists() or collected_path.stat().st_size <= 0:
        raise OperationalError(f"collected report was empty after copy: {collected_path}")
    return collected_path


def _run_report_wait(report_path: Path, grace: float) -> bool:
    """True iff a non-empty body arrived. rc 1 means no report."""
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(_script("h_mad_report_wait.py")),
                str(report_path),
                "--timeout",
                str(grace),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise OperationalError(f"report_wait failed for {report_path}: {exc}") from exc

    if result.returncode == 0:
        return report_path.exists() and report_path.stat().st_size > 0
    if result.returncode == 1:
        return False
    detail = _one_line(result.stderr or result.stdout)
    if detail:
        raise OperationalError(
            f"report_wait exited {result.returncode} for {report_path}: {detail}"
        )
    raise OperationalError(f"report_wait exited {result.returncode} for {report_path}")


def _run_extract_report(
    out_path: Path, *, feature: str, phase: str, cycle: int
) -> str:
    """Report text, or '' when nothing is there."""
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(_script("h_mad_extract_report.py")),
                str(out_path),
                "--feature",
                feature,
                "--phase",
                phase,
                "--cycle",
                str(cycle),
                "--after-marker",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise OperationalError(f"extract_report failed for {out_path}: {exc}") from exc

    if result.returncode == 0:
        return result.stdout
    if result.returncode == 2:
        return ""
    detail = _one_line(result.stderr or result.stdout)
    if detail:
        raise OperationalError(
            f"extract_report exited {result.returncode} for {out_path}: {detail}"
        )
    raise OperationalError(f"extract_report exited {result.returncode} for {out_path}")


def _write_collected_report(report_text: str, collected_path: Path) -> Path:
    collected_path.parent.mkdir(parents=True, exist_ok=True)
    collected_path.write_text(report_text, encoding="utf-8")
    if not collected_path.exists() or not collected_path.read_text(encoding="utf-8"):
        raise OperationalError(f"collected report was empty after write: {collected_path}")
    return collected_path


def collect(
    spec: PassSpec,
    *,
    grace: float,
    project_root: Path,
    feature: str,
    phase: str,
    cycle: int,
) -> tuple[str, Path | None]:
    """Return ('report-file'|'none', collected_path|None) for one audit pass."""
    collected_path = _collected_path(
        project_root=project_root,
        feature=feature,
        phase=phase,
        cycle=cycle,
        index=spec.index,
    )

    if _has_complete_report(spec.report_path):
        return "report-file", _copy_collected_report(spec.report_path, collected_path)

    if _run_report_wait(spec.report_path, grace):
        return "report-file", _copy_collected_report(spec.report_path, collected_path)

    report_text = _run_extract_report(
        spec.out_path, feature=feature, phase=phase, cycle=cycle
    )
    if report_text:
        return "out", _write_collected_report(report_text, collected_path)

    return "none", None


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
