"""A complete-looking audit report can still be UNSCORABLE.

Orchestrator errors #49o and #49q, 2026-09-05. Two agents were handed one REPORT
path; the re-dispatched leg was told to "write early so a partial result
survives"; its stub -- `IN PROGRESS`, `None` in all three finding sections,
`Evidence: 0 files opened, 0 greps run` -- landed after the original leg's
finished 137-grep report and overwrote it. The stub was then collected, committed
and PUSHED as that leg's gating result, under a commit message describing the
report it had replaced. Nothing in the collect path could tell the two apart:
`None` in every section is byte-for-byte what an auditor that read everything and
found nothing writes.

The gate is deliberately narrow. `_unscorable_reason` refuses only what is
provably not a scorable audit -- an in-progress sentinel in the report's HEAD, or
a stated evidence line of zero -- because a gate that fails a clean report is not
a gate. `test_calibration_no_committed_report_is_refused` is that claim made
mechanical against the corpus that already passed.
"""
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "h-mad" / "scripts"
COLLECT_CLI = SCRIPT_DIR / "h_mad_collect_report.py"

# The stub as it was actually written, 2026-09-05, to
# docs/01-plan/features/doc-block-exec.impl-plan.audit.v46.teammate.md.
IN_PROGRESS_STUB = """# impl-plan c46 -- teammate leg

IN PROGRESS -- written incrementally so a partial result survives.

## Summary
Evidence: 0 files opened, 0 greps run.

## Must-fix
None

## Should-fix
None

## Notes
None
"""

GOOD_REPORT = """# impl-plan c46 -- teammate leg

## Summary
Evidence: 27 files opened, 152 greps run.

## Must-fix
None

## Should-fix
None

## Notes
None
"""

# The real v46 report describes the stub in its file-integrity note at :84. A
# whole-file match refuses it; the head scope is what keeps it collectable.
DESCRIBES_THE_STUB = GOOD_REPORT + """
## File integrity
Between 11:29 and 11:33 this path held a stub reading `IN PROGRESS` with `None`
in all three finding sections and `Evidence: 0 files opened, 0 greps run`.
"""

ZERO_EVIDENCE_ONLY = """# design c95 -- teammate leg

## Summary
Evidence: 0 files opened, 0 greps run.

## Must-fix
None

## Should-fix
None

## Notes
None
"""


def audit_cycle():
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    return importlib.import_module("h_mad_audit_cycle")


def write_report(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    Path(str(path) + ".done").touch()
    return path


def collect_one(ac, report: Path, project_root: Path, *, grace: float = 0.0):
    spec = ac.PassSpec(index=1, report_path=report, out_path=None, rc=0)
    return ac.collect(
        spec,
        grace=grace,
        project_root=project_root,
        feature="f",
        phase="plan",
        cycle=8,
        surface="teammate",
    )


def collected_path(project_root: Path) -> Path:
    return project_root / "docs/01-plan/features/f.plan.audit.v8.teammate.md"


# --- the predicate, both directions -----------------------------------------


@pytest.mark.parametrize(
    "text,expected",
    [
        (GOOD_REPORT, None),
        (DESCRIBES_THE_STUB, None),
        (IN_PROGRESS_STUB, "in-progress-sentinel"),
        (ZERO_EVIDENCE_ONLY, "zero-evidence"),
    ],
    ids=["good", "describes-the-stub", "in-progress-head", "zero-evidence"],
)
def test_unscorable_reason_discriminates(tmp_path: Path, text: str, expected) -> None:
    ac = audit_cycle()
    report = tmp_path / "r.md"
    report.write_text(text, encoding="utf-8")

    assert ac._unscorable_reason(report) == expected


def test_in_progress_matches_both_spellings_only_in_the_head(tmp_path: Path) -> None:
    ac = audit_cycle()
    for spelling in ("IN PROGRESS", "in-progress", "In Progress"):
        report = tmp_path / "r.md"
        report.write_text(f"# t\n\n{spelling} -- partial\n", encoding="utf-8")
        assert ac._unscorable_reason(report) == "in-progress-sentinel", spelling

    buried = tmp_path / "buried.md"
    buried.write_text(
        "# t\n" + "\n".join(f"line {i}" for i in range(40)) + "\nIN PROGRESS\n",
        encoding="utf-8",
    )
    assert ac._unscorable_reason(buried) is None


def test_nonzero_and_absent_evidence_lines_are_scorable(tmp_path: Path) -> None:
    ac = audit_cycle()
    for line in (
        "Evidence: 27 files opened, 152 greps run.",
        "Evidence: ~165 greps run.",
        "**Evidence:** 28 files and git blobs opened, ~165 greps run.",
        "Evidence: 1 file opened, 0 greps run.",
    ):
        report = tmp_path / "r.md"
        report.write_text(f"# t\n\n## Summary\n{line}\n", encoding="utf-8")
        assert ac._unscorable_reason(report) is None, line

    # No evidence line at all is the pre-Effort-contract shape: 937 of the 1001
    # committed reports. It is not this gate's business.
    report = tmp_path / "old.md"
    report.write_text("# t\n\n## Must-fix\nNone\n", encoding="utf-8")
    assert ac._unscorable_reason(report) is None


# --- the collect path --------------------------------------------------------


def test_collect_refuses_the_stub_and_does_not_write_the_collected_path(
    tmp_path: Path,
) -> None:
    ac = audit_cycle()
    report = write_report(tmp_path / "work" / "r.md", IN_PROGRESS_STUB)

    delivered, path = collect_one(ac, report, tmp_path)

    assert delivered == "unscorable:in-progress-sentinel"
    assert path is None
    assert not collected_path(tmp_path).exists(), (
        "an unscorable report must not reach the docs store"
    )


def test_collect_still_delivers_a_real_report(tmp_path: Path) -> None:
    ac = audit_cycle()
    report = write_report(tmp_path / "work" / "r.md", GOOD_REPORT)

    delivered, path = collect_one(ac, report, tmp_path)

    assert delivered == "report-file"
    assert path == collected_path(tmp_path)
    assert path.read_text(encoding="utf-8") == GOOD_REPORT


def test_collect_refuses_an_unscorable_report_already_at_the_collected_path(
    tmp_path: Path,
) -> None:
    """The same-path branch is how a leg writing straight into docs/ arrives."""
    ac = audit_cycle()
    report = write_report(collected_path(tmp_path), IN_PROGRESS_STUB)

    delivered, path = collect_one(ac, report, tmp_path)

    assert delivered == "unscorable:in-progress-sentinel"
    assert path is None
    assert Path(str(report) + ".done").exists(), (
        "a refusal must not consume the marker -- the leg has not finished"
    )


def collect_via_out(ac, monkeypatch, tmp_path: Path, extracted: str):
    """Drive the `--out` extraction rung: no report file, transcript only."""
    report = tmp_path / "work" / "r.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    out = tmp_path / "work" / "r.out"
    out.write_text("transcript bytes", encoding="utf-8")
    monkeypatch.setattr(ac, "_run_report_wait", lambda *a, **k: False)
    monkeypatch.setattr(ac, "_run_extract_report", lambda *a, **k: extracted)
    spec = ac.PassSpec(index=1, report_path=report, out_path=out, rc=0)
    return ac.collect(
        spec,
        grace=0.0,
        project_root=tmp_path,
        feature="f",
        phase="plan",
        cycle=8,
        surface="teammate",
    )


def test_collect_refuses_an_unscorable_out_extraction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The stub arrives the same way whether a leg wrote a report file or the
    orchestrator extracted one from a transcript. A gate on only the first
    spelling is the defect wearing the other hat.
    """
    ac = audit_cycle()

    delivered, path = collect_via_out(ac, monkeypatch, tmp_path, IN_PROGRESS_STUB)

    assert delivered == "unscorable:in-progress-sentinel"
    assert path is None
    assert not collected_path(tmp_path).exists()


def test_collect_still_delivers_a_scorable_out_extraction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ac = audit_cycle()

    delivered, path = collect_via_out(ac, monkeypatch, tmp_path, GOOD_REPORT)

    assert delivered == "out"
    assert path == collected_path(tmp_path)
    assert path.read_text(encoding="utf-8") == GOOD_REPORT


def test_unscorable_pass_combines_to_unverified_not_clean() -> None:
    ac = audit_cycle()
    result = ac.PassResult(
        index=1,
        delivered="unscorable:zero-evidence",
        collected_path=None,
        verdict=None,
        must=0,
        should=0,
        findings=[],
        effort=None,
        rc=0,
    )

    verdict, reason = ac.combine([result])

    assert verdict == "UNVERIFIED"
    assert reason == "unscorable_report:p1"


def test_cli_prints_invalid_with_its_reason(tmp_path: Path) -> None:
    report = write_report(tmp_path / "work" / "r.md", IN_PROGRESS_STUB)

    proc = subprocess.run(
        [
            sys.executable,
            str(COLLECT_CLI),
            "--feature", "f",
            "--phase", "plan",
            "--cycle", "8",
            "--surface", "teammate",
            "--report", str(report),
            "--project-root", str(tmp_path),
            "--grace", "0",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    contract = [ln for ln in proc.stdout.splitlines() if ln.startswith("COLLECT: ")]
    markers = [ln for ln in proc.stdout.splitlines() if ln.startswith("[H-MAD] ")]
    assert contract == [
        f"COLLECT: INVALID reason=in-progress-sentinel path={report}"
    ], proc.stdout
    assert markers == ["[H-MAD] f collect INVALID"], proc.stdout
    assert not collected_path(tmp_path).exists()


# --- calibration -------------------------------------------------------------


def test_calibration_no_committed_report_is_refused() -> None:
    """Every detector filed as hard on first cut in this repo fired 48-104 times
    on documents that had already survived 74-83 audit cycles. A gate that fails
    a clean artifact is not a gate, so this one is measured against the corpus
    that already passed rather than argued for. Measured at `a9e6998`: 1001
    committed reports, 0 refused.
    """
    ac = audit_cycle()
    listing = subprocess.run(
        ["git", "ls-files", "docs/**/*.audit.v*.md"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if listing.returncode != 0:
        pytest.skip(f"not a git work tree: {listing.stderr.strip()}")
    reports = [REPO_ROOT / p for p in listing.stdout.split()]
    if not reports:
        pytest.skip("no committed audit reports in this checkout")

    refused = {
        str(p.relative_to(REPO_ROOT)): ac._unscorable_reason(p)
        for p in reports
        if p.is_file() and ac._unscorable_reason(p) is not None
    }

    assert refused == {}, (
        f"the gate refuses {len(refused)} of {len(reports)} reports that already "
        f"passed a gating cycle: {refused}"
    )
