#!/usr/bin/env python3
"""h_mad_audit_cycle.py - combine and render H-MAD audit pass verdicts."""
from __future__ import annotations

import argparse
import math
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
GATE_RE = re.compile(r"^GATE:\s+(\S+)\s+must=(\d+)\s+should=(\d+)\s*$")


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
    collected_path.unlink(missing_ok=True)
    collected_path.write_bytes(report_path.read_bytes())
    if not collected_path.exists() or collected_path.stat().st_size <= 0:
        raise OperationalError(f"collected report was empty after copy: {collected_path}")
    return collected_path


def _run_report_wait(report_path: Path, grace: float) -> bool:
    """True iff a non-empty body arrived. rc 1 means no report."""
    timeout = str(max(1, math.ceil(grace))) if math.isfinite(grace) else "1"
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(_script("h_mad_report_wait.py")),
                str(report_path),
                "--timeout",
                timeout,
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
    collected_path.unlink(missing_ok=True)
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


def _gate_token(stdout: str, collected: Path) -> tuple[str, int, int]:
    """Return the final GATE token from gate stdout."""
    matched: tuple[str, int, int] | None = None
    for line in stdout.splitlines():
        match = GATE_RE.match(line)
        if match:
            matched = (
                match.group(1),
                int(match.group(2)),
                int(match.group(3)),
            )
    if matched is None:
        raise OperationalError(f"missing GATE token for {collected}")
    return matched


def _must_findings_from_gate_parser(text: str, acknowledged: set[str]) -> list[dict]:
    """Enumerate Must-fix findings with h_mad_audit_gate's parser primitives."""
    from h_mad_audit_gate import _BULLET_MARKERS, _payload

    must_lines: list[str] = []
    in_must = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "## Must-fix":
            in_must = True
            continue
        if stripped.startswith("## "):
            in_must = False
            continue
        if in_must and stripped:
            must_lines.append(line)

    bullets = [
        _payload(line)
        for line in must_lines
        if any(line.strip().startswith(marker) for marker in _BULLET_MARKERS)
        and _payload(line)
        and _payload(line).lower() != "none"
        and _payload(line) not in acknowledged
    ]
    if bullets:
        payloads = bullets
    else:
        non_none = [
            _payload(line)
            for line in must_lines
            if _payload(line) and _payload(line).lower() != "none"
        ]
        joined = " ".join(payload for payload in non_none if payload)
        payloads = [joined] if joined and joined not in acknowledged else []

    return [
        {"severity": "must", "text": payload, "path": None, "line": None}
        for payload in payloads
    ]


def gate(collected: Path, *, ack_file: Path | None) -> tuple[str | None, int, int, list[dict]]:
    """(verdict, must, should, must_fix_bullets).

    INVALID returns ("INVALID", 0, 0, []) immediately: counts are discarded and the
    in-process read is skipped, so the assertion below cannot fire on a verdict
    whose counts were never measured.
    """
    command = [sys.executable, str(_script("h_mad_audit_gate.py")), str(collected)]
    if ack_file is not None:
        command.extend(["--ack-file", str(ack_file)])
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise OperationalError(f"audit_gate failed for {collected}: {exc}") from exc

    # Axis B, audit-gate signal discipline: the exit code answers "did the script run
    # at all" and the token answers "what did it decide" — read BOTH, as every other
    # composed call here does. Without this, a crashing gate that still emitted a
    # well-formed GATE line would be scored as a verdict.
    #
    # 2 is allowed on purpose and must stay allowed: `h_mad_audit_gate.py` prints
    # `GATE: INVALID` and returns 2 deliberately, so that "no report" can never read
    # as "no findings". Narrowing this to `!= 0` converts that correct UNVERIFIED into
    # an operational error — `test_gate_invalid_exits_two_and_is_still_a_verdict` pins it.
    if result.returncode not in (0, 2):
        detail = (result.stderr or result.stdout or "").strip().splitlines()
        raise OperationalError(
            f"audit_gate exited {result.returncode} for {collected}"
            + (f": {detail[-1]}" if detail else "")
        )

    verdict, must, should = _gate_token(result.stdout, collected)
    if verdict == "INVALID":
        return "INVALID", 0, 0, []

    try:
        from h_mad_audit_gate import _acknowledged_from_text, _read_ack_file

        text = collected.read_text(encoding="utf-8")
        acknowledged = _acknowledged_from_text(text)
        if ack_file is not None:
            acknowledged.update(_read_ack_file(ack_file))
    except OSError as exc:
        raise OperationalError(f"gate in-process read failed for {collected}: {exc}") from exc

    findings = _must_findings_from_gate_parser(text, acknowledged)
    if len(findings) != must:
        raise OperationalError(
            f"gate count mismatch for {collected}: findings={len(findings)} must={must}"
        )
    return verdict, must, should, findings


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
    if verdict == "UNVERIFIED":
        fields = [f"AUDITCYCLE: {verdict}"]
        if reason is not None:
            fields.append(f"reason={reason}")
        fields.append(f"passes={passes}")
        if results:
            delivered = ",".join(result.delivered for result in results)
            fields.append(f"delivered={delivered}")
        fields.append(f"size_status={size_status}")
        lines = [" ".join(fields), f"[H-MAD] {feature} audit-cycle {verdict}"]
        return "\n".join(lines) + "\n"

    fields = [f"AUDITCYCLE: {verdict}"]
    if verdict != "UNVERIFIED":
        must = sum(result.must for result in results)
        should = sum(result.should for result in results)
        fields.extend([f"must={must}", f"should={should}"])
        fields.append(f"passes={passes}")
        fields.extend(f"p{result.index}={result.must}/{result.should}" for result in results)
        if results:
            delivered = ",".join(result.delivered for result in results)
            fields.append(f"delivered={delivered}")
        fields.append(f"size_status={size_status}")

    lines = [" ".join(fields)]
    items = premise_items(results)
    if items:
        lines.append("Premise checklist:")
        lines.extend(f"- {item}" for item in items)
    else:
        lines.append("Premise checklist: empty")
    if verdict != "UNVERIFIED":
        reports = [str(result.collected_path) for result in results if result.collected_path]
        lines.append("reports: " + " ".join(reports))
        lines.append(
            "note: must=/should= are sums across passes and may double-count a finding both passes reported"
        )
    lines.append(f"[H-MAD] {feature} audit-cycle {verdict}")
    return "\n".join(lines) + "\n"


def _parse_pass_spec(value: str) -> PassSpec:
    parts = value.split(":", 3)
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("--pass must be i:<report>:<out>:<rc>")
    index, report_path, out_path, rc = parts
    try:
        parsed_index = int(index)
        parsed_rc = int(rc)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--pass index and rc must be integers") from exc
    return PassSpec(
        index=parsed_index,
        report_path=Path(report_path),
        out_path=Path(out_path),
        rc=parsed_rc,
    )


def main(argv: list[str] | None = None) -> int:
    """Run the audit-cycle helper."""
    parser = argparse.ArgumentParser(description="H-MAD audit cycle", allow_abbrev=False)
    parser.add_argument("--feature", required=True)
    parser.add_argument("--phase", required=True, choices=("plan", "design", "impl-plan"))
    parser.add_argument("--cycle", type=int, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--passes", type=int, required=True)
    parser.add_argument("--size-status", default="verified")
    parser.add_argument("--halt-reason")
    parser.add_argument("--pass", dest="pass_specs", action="append", type=_parse_pass_spec)
    parser.add_argument("--grace", type=float, default=30.0)
    parser.add_argument("--ack-file", type=Path)

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)

    if args.passes <= 0:
        print("ERROR: --passes must be positive", file=sys.stderr)
        return 2

    pass_specs = args.pass_specs or []
    if bool(args.halt_reason) == bool(pass_specs):
        print("ERROR: exactly one audit-cycle mode is required", file=sys.stderr)
        return 2

    if pass_specs:
        try:
            results: list[PassResult] = []
            for spec in pass_specs:
                delivered, collected_path = collect(
                    spec,
                    grace=args.grace,
                    project_root=args.project_root,
                    feature=args.feature,
                    phase=args.phase,
                    cycle=args.cycle,
                )
                if delivered != "none":
                    if collected_path is None:
                        raise OperationalError(
                            f"missing collected path after delivered output for p{spec.index}"
                        )
                    verdict, must, should, findings = gate(
                        collected_path,
                        ack_file=args.ack_file,
                    )
                else:
                    verdict, must, should, findings = None, 0, 0, []
                results.append(
                    PassResult(
                        index=spec.index,
                        delivered=delivered,
                        collected_path=collected_path,
                        verdict=verdict,
                        must=must,
                        should=should,
                        findings=findings,
                    )
                )
            verdict, reason = combine(results)
            text = render(
                results,
                verdict,
                reason,
                feature=args.feature,
                size_status=args.size_status,
                passes=args.passes,
            )
        except OperationalError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 4
        print(text, end="")
        return 0

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
