#!/usr/bin/env python3
"""h_mad_audit_cycle.py - combine and render H-MAD audit pass verdicts."""
from __future__ import annotations

import argparse
import contextlib
import math
import os
import re
import subprocess
import sys
from collections import namedtuple
from pathlib import Path

from h_mad_extract_report import DISPATCH_BOUNDARY
from h_mad_review_evidence import scan


# `log_path` defaults to None so a four-field caller — every existing one — keeps
# constructing a valid spec. Effort reporting is additive by design.
PassSpec = namedtuple("PassSpec", "index report_path out_path rc log_path",
                      defaults=(None,))
PassResult = namedtuple(
    "PassResult",
    "index delivered collected_path verdict must should findings effort rc",
    defaults=(0,),
)

# The report-file delivery contract itself costs two successful tool calls: write
# the report, then create the `.done` marker. At or below that floor a pass cannot
# have successfully read anything, which is the J49 signature -- cycle 24
# double-cleaned with exactly these two calls and no reads, and cycle 21 pass A
# made zero calls and still returned "CLEAN PASS" on a defective plan.
#
# Derived from the CONTRACT, never from tool names. `h_mad_review_evidence.scan`
# knows no tool names on purpose: the first probe of that defect hardcoded
# `view_file|grep_search` and reported a false zero when agy switched to
# `run_command`. Classifying calls as reads-vs-writes here would re-create it.
DELIVERY_FLOOR = 2

# `timeout(1)` exits 124 when it kills the command. `_cmd_exec agy` wraps the
# dispatch in it, so this is the rc a pass that ran out of wall-clock carries.
TIMEOUT_RC = 124
GATE_RE = re.compile(r"^GATE:\s+(\S+)\s+must=(\d+)\s+should=(\d+)\s*$")
SURFACE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
PASS_INDEX_RE = re.compile(r"^p\d+$")

# A report can be complete -- non-empty, marker present -- and still not be a
# scorable audit. Orchestrator errors #49o/#49q, 2026-09-05: two agents were
# handed one REPORT path, the re-dispatched leg was told to "write early so a
# partial result survives", and its stub -- `IN PROGRESS`, `None` in all three
# finding sections, `Evidence: 0 files opened, 0 greps run` -- landed after the
# original leg's finished 137-grep report, overwrote it, and was collected,
# committed and pushed as that leg's gating result. `None` in every section is
# byte-for-byte what an auditor that read everything and found nothing writes, so
# no consumer downstream of collect could tell them apart.
#
# The scope of each screen is load-bearing, and both were calibrated against the
# corpus that had already passed rather than argued for (test_h_mad_unscorable_
# report.py::test_calibration_no_committed_report_is_refused). At `a9e6998`: 1001
# committed `*.audit.v*.md`, 64 carrying an evidence line, 0 refused.
#
#  - HEAD-scoped for the sentinel, because a real report DESCRIBES the stub in its
#    body (`doc-block-exec.impl-plan.audit.v46.teammate.md:84`) and a whole-file
#    match refuses it -- the GRAMMAR species (#49g) applied to this gate itself.
#  - The evidence screen fires only on a stated zero. An ABSENT evidence line is
#    the pre-Effort-contract shape (937 of the 1001) and is not this gate's
#    business; refusing it would fail every report written before the contract.
UNSCORABLE_HEAD_LINES = 15
UNSCORABLE_PREFIX = "unscorable:"
IN_PROGRESS_RE = re.compile(r"\bIN[ -]PROGRESS\b", re.IGNORECASE)
EVIDENCE_COUNT_RE = re.compile(r"Evidence:\s*~?(\d+)\b", re.IGNORECASE)


class OperationalError(Exception):
    """The audit cycle could not form a trustworthy verdict."""


class CollectConflict(OperationalError):
    """A collected audit report exists with different bytes."""

    def __init__(self, collected: Path, delivered: str) -> None:
        super().__init__(f"collected report conflict for {delivered}: {collected}")
        self.collected = collected
        self.delivered = delivered


def validate_surface(surface: str) -> str:
    """Return a validated audit surface token."""
    if not SURFACE_RE.match(surface) or PASS_INDEX_RE.match(surface):
        raise ValueError(f"invalid surface token: {surface!r}")
    return surface


@contextlib.contextmanager
def _fs_errors(what: str):
    """Convert filesystem failures into collector operational failures."""
    try:
        yield
    except OSError as exc:
        raise OperationalError(f"{what}: {exc}") from exc


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
    surface: str | None = None,
) -> Path:
    """Return the collected audit report path for one audit pass."""
    audit_dirs = {
        "plan": Path("docs/01-plan/features"),
        "design": Path("docs/02-design/features"),
        "impl-plan": Path("docs/01-plan/features"),
    }
    suffix = f"p{index}" if surface is None else validate_surface(surface)
    return (
        project_root
        / audit_dirs[phase]
        / f"{feature}.{phase}.audit.v{cycle}.{suffix}.md"
    )


def _done_path(report_path: Path) -> Path:
    return Path(str(report_path) + ".done")


def _unscorable_reason(report_path: Path) -> str | None:
    """Return why a complete-looking report must not be SCORED, or None.

    Narrow on purpose: only what is provably not a finished audit. An unreadable
    file returns None rather than a refusal, because `_copy_collected_report`
    raises on it a moment later -- "I could not read it" must not be spelled the
    same way as "I read it and it is bad".
    """
    try:
        text = report_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return _unscorable_reason_text(text)


def _unscorable_reason_text(text: str) -> str | None:
    """The same screen over report TEXT, for the `--out` extraction path.

    Closing the class rather than the instance: the stub arrives the same way
    whether the leg wrote a report file or the orchestrator extracted one from a
    transcript, and a gate on only the first spelling is the defect wearing the
    other hat.
    """
    head = "\n".join(text.splitlines()[:UNSCORABLE_HEAD_LINES])
    if IN_PROGRESS_RE.search(head):
        return "in-progress-sentinel"
    evidence = EVIDENCE_COUNT_RE.search(text)
    if evidence is not None and int(evidence.group(1)) == 0:
        return "zero-evidence"
    return None


def is_unscorable(delivered: str) -> bool:
    """True for the `unscorable:<reason>` delivery token."""
    return delivered.startswith(UNSCORABLE_PREFIX)


def _deliver_report_file(
    report_path: Path, collected_path: Path, *, overwrite: bool, copy: bool = True
) -> tuple[str, Path | None]:
    """Deliver a complete report unless it is unscorable.

    The refusal happens BEFORE the copy: an unscorable report that reached the
    docs store is the #49q defect, and a later refusal cannot un-write it. The
    `.done` marker is left alone for the same reason -- the leg has not finished.
    """
    reason = _unscorable_reason(report_path)
    if reason is not None:
        return f"{UNSCORABLE_PREFIX}{reason}", None
    if not copy:
        return "report-file", collected_path
    return "report-file", _copy_collected_report(
        report_path, collected_path, overwrite=overwrite
    )


def _has_complete_report(report_path: Path) -> bool:
    return (
        report_path.exists()
        and report_path.stat().st_size > 0
        and _done_path(report_path).exists()
    )


def _readback_equal(path: Path, data: bytes) -> bool:
    try:
        return path.read_bytes() == data
    except OSError:
        return False


def _finalize_write(collected_path: Path, data: bytes) -> Path:
    collected_path.unlink(missing_ok=True)
    collected_path.write_bytes(data)
    if not _readback_equal(collected_path, data):
        raise OperationalError(f"readback mismatch after write: {collected_path}")
    return collected_path


def _copy_collected_report(
    report_path: Path, collected_path: Path, *, overwrite: bool = True
) -> Path:
    with _fs_errors("copy collected report"):
        data = report_path.read_bytes()
        if not data:
            raise OperationalError(
                f"report is empty: {report_path}; "
                f"collected report was empty after copy: {collected_path}"
            )
        if report_path.resolve() == collected_path.resolve():
            marker = _done_path(report_path)
            marker.unlink(missing_ok=True)
            if marker.exists():
                raise OperationalError(
                    f"readback mismatch after marker removal: {marker}"
                )
            return collected_path
        collected_path.parent.mkdir(parents=True, exist_ok=True)
        if collected_path.exists():
            existing = collected_path.read_bytes()
            if existing == data:
                return collected_path
            if not overwrite:
                raise CollectConflict(collected_path, "report-file")
        try:
            return _finalize_write(collected_path, data)
        except OperationalError:
            if not collected_path.exists() or collected_path.stat().st_size <= 0:
                raise OperationalError(
                    f"collected report was empty after copy: {collected_path}"
                )
            raise


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
    """Report text, or '' when nothing is there.

    `--after-marker` is passed ONLY when the file actually carries the dispatch
    boundary, and that condition is the whole of #16.

    The boundary is written by the PANE transport, where the prompt is echoed into
    the scrape and the reader must skip past it — otherwise the sentinel pair
    extracted is the one inside the prompt, not the agent's answer. An `exec`
    dispatch has no echo, so its `--out` file has no boundary. Passing the flag
    unconditionally therefore made `extract_report` exit 2 on every `exec` `--out`
    file, which this function turns into `""` — and the fallback that the whole
    verb "always arms" was structurally DEAD for the transport it is armed on.

    Measured: a codex pass wrote a 0-byte report file plus its `.done` marker while
    `--out` held the complete sentinel report; collection answered
    `COLLECT: MISSING delivered=none` and the report had to be recovered by hand.
    Reproduced end-to-end before this fix.

    Dropping the flag entirely would be wrong in the other direction — it is what
    stops a pane scrape yielding the prompt's own sentinel — so the condition is
    the boundary's presence, which is exactly what distinguishes the two
    transports. `extract` already takes the LAST BEGIN/END pair, so a file with no
    boundary is still read from its end rather than its echo.
    """
    try:
        has_boundary = DISPATCH_BOUNDARY in out_path.read_text(
            encoding="utf-8", errors="replace"
        )
    except OSError:
        has_boundary = False

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
                *(["--after-marker"] if has_boundary else []),
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


def _write_collected_report(
    report_text: str, collected_path: Path, *, overwrite: bool = True
) -> Path:
    with _fs_errors("write collected report"):
        data = report_text.encode("utf-8")
        collected_path.parent.mkdir(parents=True, exist_ok=True)
        if collected_path.exists():
            existing = collected_path.read_bytes()
            if existing == data:
                return collected_path
            if not overwrite:
                raise CollectConflict(collected_path, "out")
        return _finalize_write(collected_path, data)


def collect(
    spec: PassSpec,
    *,
    grace: float,
    project_root: Path,
    feature: str,
    phase: str,
    cycle: int,
    surface: str | None = None,
    overwrite: bool = True,
) -> tuple[str, Path | None]:
    """Return ('report-file'|'none', collected_path|None) for one audit pass."""
    with _fs_errors("collect"):
        return _collect_unguarded(
            spec,
            grace=grace,
            project_root=project_root,
            feature=feature,
            phase=phase,
            cycle=cycle,
            surface=surface,
            overwrite=overwrite,
        )


def _collect_unguarded(
    spec: PassSpec,
    *,
    grace: float,
    project_root: Path,
    feature: str,
    phase: str,
    cycle: int,
    surface: str | None,
    overwrite: bool,
) -> tuple[str, Path | None]:
    collected_path = _collected_path(
        project_root=project_root,
        feature=feature,
        phase=phase,
        cycle=cycle,
        index=spec.index,
        surface=surface,
    )

    if spec.report_path.resolve() == collected_path.resolve():
        if _has_complete_report(spec.report_path) or (
            grace > 0 and _run_report_wait(spec.report_path, grace)
        ):
            return _deliver_report_file(
                spec.report_path, collected_path, overwrite=overwrite
            )
        return "none", None

    empty_matching_pair = False
    if spec.report_path.exists() and collected_path.exists():
        report_bytes = spec.report_path.read_bytes()
        collected_bytes = collected_path.read_bytes()
        if report_bytes == collected_bytes:
            if report_bytes:
                return _deliver_report_file(
                    spec.report_path, collected_path, overwrite=overwrite, copy=False
                )
            empty_matching_pair = True

    if empty_matching_pair:
        overwrite = True

    if _has_complete_report(spec.report_path):
        return _deliver_report_file(
            spec.report_path, collected_path, overwrite=overwrite
        )

    if _run_report_wait(spec.report_path, grace):
        return _deliver_report_file(
            spec.report_path, collected_path, overwrite=overwrite
        )

    if spec.out_path is not None:
        report_text = _run_extract_report(
            spec.out_path, feature=feature, phase=phase, cycle=cycle
        )
        if report_text:
            reason = _unscorable_reason_text(report_text)
            if reason is not None:
                return f"{UNSCORABLE_PREFIX}{reason}", None
            return "out", _write_collected_report(
                report_text, collected_path, overwrite=overwrite
            )

    return "none", None


def measure_effort(log_path: Path | None) -> dict | None:
    """Reasoning effort for one pass, or None when there is nothing to report.

    Returns `{"readable": False}` for a log that was named but could not be read.
    That is deliberately NOT a zero: `tools=0` is precisely what a hollow pass
    looks like, so rendering an unread log as zeros would manufacture the very
    finding this exists to surface (the mode-15 lesson -- assert existence and
    content as two separate columns).
    """
    if log_path is None:
        return None
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"readable": False, "shape": "missing"}
    if not text.strip():
        # `readable` stays False so the RENDER keeps saying "unreadable" rather
        # than printing a row of zeros — see the note above, which is about
        # rendering and is unchanged. `shape` is what the VERDICT routes on, and
        # the two answers differ: an empty file is what a dispatch that died
        # instantly leaves behind, so there is nothing to go and find and the
        # remedy is to re-dispatch.
        return {"readable": False, "shape": "empty"}
    counts = scan(text)
    counts["readable"] = True
    # A file that was read, is not blank, and carries no NDJSON object at all is
    # not this pass's transcript — a stray `--log`, a shell wrapper's stdout, the
    # wrong path. `tools=0` there means "not measured", not "measured as zero",
    # and the remedy is to find the right file rather than to re-dispatch.
    counts["shape"] = "parsed" if any(
        line.lstrip().startswith("{") for line in text.splitlines()
    ) else "unparseable"
    return counts


def _effort_items(results: list[PassResult]) -> list[str]:
    """One human line per pass that carried a log.

    This function renders; it never decides. Since #13 `combine()` reads the same
    counts and does decide, in one direction — scope any "never a verdict" claim to
    the rendering, which is all this was ever about.
    """
    items: list[str] = []
    for result in results:
        effort = result.effort
        if effort is None:
            continue
        if not effort.get("readable"):
            items.append(f"p{result.index} unreadable (log named but not readable)")
            continue
        line = (f"p{result.index} tools={effort['tools']} ok={effort['ok']} "
                f"failed={effort['failed']} thinking={effort['thinking']}")
        if effort["ok"] <= DELIVERY_FLOOR:
            line += (f" low-evidence (<= the {DELIVERY_FLOOR} calls the report-file "
                     "contract itself costs, so possibly no reads)")
        items.append(line)
    return items


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
        if (
            result.delivered != "none"
            and not is_unscorable(result.delivered)
            and result.verdict is None
        ):
            raise OperationalError(
                f"missing GATE token for p{result.index} after delivered output"
            )

    for result in results:
        # A refused report is NOT a missing one, and the two prescribe opposite
        # next moves: `no_report` says re-dispatch, `unscorable_report` says the
        # leg is still writing (or wrote nothing it read) and the path may have a
        # second writer. Collapsing them into one reason is the #61 defect --
        # `COLLECT: MISSING` read as evidence the auditor failed.
        if is_unscorable(result.delivered):
            return "UNVERIFIED", f"unscorable_report:p{result.index}"
        if result.delivered == "none":
            return "UNVERIFIED", f"no_report:p{result.index}"
        if result.verdict == "INVALID":
            return "UNVERIFIED", f"no_gate_sections:p{result.index}"

    for result in results:
        if result.verdict == "FAIL":
            return "FAIL", f"findings:p{result.index}"

    # A pass whose dispatch did not exit cleanly did not finish, so its report is
    # at best partial and cannot certify anything. Checked AFTER the FAIL loop on
    # purpose: findings a truncated pass did manage to write are still findings,
    # and FAIL is the direction that never falsely gates. What this closes is the
    # other direction -- an agy leg killed at `--timeout` (rc 124) that had already
    # written a GATE line scored a clean PASS, because rc was carried in PassSpec
    # and read by nobody. Observed live on cycle 27 of manuscript-model-provenance:
    # `EMPTY final message`, 0 tools, verdict PASS. Raising --timeout removed the
    # phantom, which is what a real timeout looks like.
    #
    # UNVERIFIED, not a new verdict word: every consumer that already branches on
    # UNVERIFIED keeps working. Adding a word here would silently un-guard each of
    # them.
    for result in results:
        if result.rc:
            token = (
                "dispatch_timeout"
                if result.rc == TIMEOUT_RC
                else f"dispatch_rc{result.rc}"
            )
            return "UNVERIFIED", f"{token}:p{result.index}"

    # A pass that cannot have read anything cannot certify anything (#13).
    #
    # This REVERSES the rule that stood here until 2026-09-04 ("the effort block
    # reports; it must never decide"), by operator decision and on measured
    # evidence rather than taste. What changed is not the scoring but what the
    # scoring was found to predict:
    #
    #   - Over HemaSuite `#18` c45-75 the agy leg produced 6 fabricated must-fixes
    #     of 11 while codex produced 0 of 25 -- so its verdicts are not
    #     interchangeable with the other surface's.
    #   - Its low-evidence passes never found anything, in either direction. In one
    #     round its design pass ran 58 tool calls and found a real defect BOTH
    #     teammate passes missed, while its plan pass ran 2 -- this floor exactly --
    #     and returned a clean worth nothing. Same surface, same round, opposite
    #     value, and the tool count sorted them.
    #   - On one feature the second surface was hollow in 21 of 22 passes, so the
    #     union that the two-surface gate is built on was carried by one leg while
    #     reporting as two.
    #
    # The old rule's defence was that a 2-call pass "honoured the delivery contract
    # exactly as asked". True, and beside the point: honouring the delivery contract
    # is not evidence of having read the tree, and a gate cannot tell "there is
    # nothing to find" from "this pass looked at nothing". That is the same
    # cannot-judge this file already refuses to score anywhere else.
    #
    # It is deliberately NOT a FAIL: nothing was found to be wrong. It is also
    # checked AFTER the FAIL loop, so findings a hollow pass did manage to write
    # still count -- the direction that never falsely gates. And `UNVERIFIED`
    # rather than a new word, for the reason the rc guard above already gives.
    for result in results:
        if result.effort is None:
            # No log was named for this pass, so nothing was measured. That is the
            # ordinary shape of a codex leg and of every `Agent()` teammate pass,
            # and scoring absence-of-measurement as hollowness would flip almost
            # every honest pass to UNVERIFIED. Absence of evidence about evidence
            # is not evidence of absence.
            continue
        # Route on the log's SHAPE, because "I could not measure this" and "I
        # measured it and it is hollow" have opposite remedies -- find the right
        # file, versus re-dispatch the pass -- and the first cut of this routed
        # two of the four shapes to the other one's remedy. Neither could produce
        # a false clean, but a wrong hint sends the reader somewhere there is
        # nothing to find.
        shape = result.effort.get("shape")
        if shape is None:
            # An effort dict built by hand, or by an older caller, carries no
            # shape. Fall back to the pre-#13-followup reading rather than
            # dropping through to the floor check, which would score an
            # unreadable log as hollow.
            shape = "parsed" if result.effort.get("readable") else "missing"
        if shape in ("missing", "unparseable"):
            return "UNVERIFIED", f"low_evidence_unmeasurable:p{result.index}"
        if shape == "empty":
            return "UNVERIFIED", f"low_evidence:p{result.index}"
        if result.effort.get("ok", 0) <= DELIVERY_FLOOR:
            return "UNVERIFIED", f"low_evidence:p{result.index}"

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
        lines = [" ".join(fields)]
        # The Effort block renders HERE too, and that is load-bearing rather than
        # cosmetic. Since #13 a low-evidence pass can itself produce the UNVERIFIED
        # verdict, so the counts are the evidence FOR the verdict — this branch used
        # to return before reaching them, which would have printed
        # `reason=low_evidence:p1` with nothing to justify it and sent the reader
        # back to the raw NDJSON, the exact hand-opening the Effort block exists to
        # replace.
        effort = _effort_items(results)
        if effort:
            lines.append("Effort:")
            lines.extend(f"- {item}" for item in effort)
        lines.append(f"[H-MAD] {feature} audit-cycle {verdict}")
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
    # Beside the verdict, never INSIDE it. The AUDITCYCLE line is a machine contract
    # parsed positionally by consumers, so the counts stay out of the token itself.
    # Since #13 `combine()` does read the same numbers, in one direction only: a pass
    # at or below the delivery floor cannot certify a clean. It still cannot
    # manufacture a FAIL, and `tools=`/`low-evidence` still never appear in the
    # token — only the `reason=low_evidence:pN` field does.
    effort = _effort_items(results)
    if effort:
        lines.append("Effort:")
        lines.extend(f"- {item}" for item in effort)
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
    """Parse `i:<report>:<out>:<rc>[:<log>]`.

    The log is OPTIONAL and LAST. Optional because every existing four-field caller
    must keep working — a required fifth field would break the verb the moment this
    script was upgraded. Last because `split(":", 4)` leaves everything after the
    fourth colon in the final piece, so a log path containing a colon arrives whole
    while `rc` stays a clean integer.
    """
    parts = value.split(":", 4)
    if len(parts) not in (4, 5):
        raise argparse.ArgumentTypeError("--pass must be i:<report>:<out>:<rc>[:<log>]")
    index, report_path, out_path, rc = parts[:4]
    log = parts[4] if len(parts) == 5 else ""
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
        log_path=Path(log) if log else None,
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
                if delivered != "none" and not is_unscorable(delivered):
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
                        effort=measure_effort(spec.log_path),
                        rc=spec.rc,
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
