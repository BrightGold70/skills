"""`h_mad_ac_census.py` re-derives a spec's AC count and checks the paired docs.

Skill-candidates row "an AC count in a paired doc goes stale every time an AC is
inserted": a plan's "All N ACs pass" drifted three times in one feature (38, 39,
40, 43), each caught by an auditor rather than a check, and twice the insertion
broke contiguous numbering (`AC-3.8b` before `AC-3.7`). Both are mechanical.
Calibrated on the committed corpus before wiring: the only drift it reports there
is a real one (`fanout-integrity-and-defects.plan.md` says 34, the spec has 35).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "h_mad_ac_census.py"

SPEC = """# Spec

## FR-1
  - AC-1.1: first
  - AC-1.2: second

## FR-2
  - AC-2.1: third
  - AC-2.2: fourth
  - AC-2.2b: inserted after its base
"""


def _run(*args: Path | str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                          capture_output=True, text=True)


def _token(out: str) -> str:
    return next((l for l in out.splitlines() if l.startswith("ACS:")), "")


def _write(tmp_path: Path, name: str, body: str) -> Path:
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


def test_ok_when_every_claim_matches_the_spec(tmp_path: Path) -> None:
    spec = _write(tmp_path, "f.spec.md", SPEC)
    plan = _write(tmp_path, "f.plan.md", "- All 5 ACs across FR-1–FR-2 pass.\n")

    proc = _run(spec, plan)

    assert proc.returncode == 0, proc.stderr
    assert _token(proc.stdout) == "ACS: OK count=5 frs=2", proc.stdout


def test_drift_names_the_doc_line_and_both_numbers(tmp_path: Path) -> None:
    spec = _write(tmp_path, "f.spec.md", SPEC)
    plan = _write(tmp_path, "f.plan.md", "intro\n- All 4 ACs pass automated tests.\n")

    proc = _run(spec, plan)

    assert proc.returncode == 0
    assert _token(proc.stdout).startswith("ACS: DRIFT count=5"), proc.stdout
    assert "CLAIM: f.plan.md:2 says 4, spec has 5" in proc.stdout, proc.stdout


def test_document_order_is_advisory_not_drift(tmp_path: Path) -> None:
    """Calibrated: four audited specs place an AC beside its topic rather than in
    numeric order, and none has a gap. Order alone must not flip the verdict."""
    spec = _write(tmp_path, "f.spec.md", SPEC.replace(
        "  - AC-1.1: first\n  - AC-1.2: second\n", "  - AC-1.2: second\n  - AC-1.1: first\n"))

    proc = _run(spec)

    assert _token(proc.stdout) == "ACS: OK count=5 frs=2", proc.stdout
    assert "ORDER (advisory): FR-1 AC-1.1 after AC-1.2" in proc.stdout, proc.stdout


def test_a_gap_in_numbering_is_drift(tmp_path: Path) -> None:
    spec = _write(tmp_path, "f.spec.md", SPEC.replace("  - AC-2.2: fourth\n", "  - AC-2.3: fourth\n")
                  .replace("AC-2.2b", "AC-2.3b"))

    proc = _run(spec)

    assert _token(proc.stdout).startswith("ACS: DRIFT"), proc.stdout
    assert "GAP: FR-2 has AC-2.3 but no AC-2.2" in proc.stdout, proc.stdout


def test_a_duplicate_ac_is_drift(tmp_path: Path) -> None:
    spec = _write(tmp_path, "f.spec.md", SPEC + "  - AC-2.1: again\n")

    proc = _run(spec)

    assert _token(proc.stdout).startswith("ACS: DRIFT"), proc.stdout
    assert "DUPLICATE: AC-2.1" in proc.stdout, proc.stdout


def test_a_lettered_ac_without_its_base_is_drift(tmp_path: Path) -> None:
    """The row's own case: `AC-3.8b` inserted where no `AC-3.8` precedes it."""
    spec = _write(tmp_path, "f.spec.md", SPEC.replace("  - AC-2.2b: inserted after its base\n",
                                                     "  - AC-2.3b: orphan\n"))

    proc = _run(spec)

    assert _token(proc.stdout).startswith("ACS: DRIFT"), proc.stdout
    assert "GAP: FR-2 has AC-2.3b but no AC-2.3" in proc.stdout, proc.stdout


def test_a_tagged_ac_is_still_counted(tmp_path: Path) -> None:
    """`AC-2.1 (layout):` and `AC-3.3 [OD-1]:` are real ACs; missing them undercounts
    and invents gaps (measured on codex-tdd-gate-defects.spec.md)."""
    spec = _write(tmp_path, "f.spec.md", SPEC.replace("AC-2.1: third", "AC-2.1 (layout): third")
                  .replace("AC-2.2: fourth", "AC-2.2 [OD-1]: fourth"))

    proc = _run(spec)

    assert _token(proc.stdout) == "ACS: OK count=5 frs=2", proc.stdout


def test_a_spec_with_no_acs_is_none_not_ok(tmp_path: Path) -> None:
    spec = _write(tmp_path, "f.spec.md", "# Spec\nno criteria here\n")

    proc = _run(spec)

    assert _token(proc.stdout) == "ACS: NONE count=0", proc.stdout


def test_an_unreadable_spec_exits_2(tmp_path: Path) -> None:
    proc = _run(tmp_path / "missing.spec.md")

    assert proc.returncode == 2
    assert _token(proc.stdout).startswith("ACS: UNREADABLE"), proc.stdout
