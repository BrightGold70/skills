"""Pins #39 — `h_mad_do_preconditions` must not score a heading-less audit report.

`_count_must_fix` reached past `has_gate_sections()` into `classify()`, so a report
carrying **no** `## Must-fix` / `## Should-fix` headings scored `must_count=0` and
CLEARED the Phase-5 gate. It fails OPEN: a malformed or contract-less report was
indistinguishable from a clean one.

The guard already existed and the audit-gate CLI already used it — `h_mad_audit_gate.py`
returns `GATE: INVALID` (exit 2) on exactly the same file. Only this caller was blind,
which is why the fix routes through `has_gate_sections()` rather than re-deriving the
check: re-deriving is how the two drifted apart in the first place.

Reachable in practice because audit reports arrive from an agent CLI over a transport
documented to mangle or drop the output contract (see docs/skill-monitoring.md J28) —
every such drop lands as a heading-less file, which is precisely this input.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from h_mad_do_preconditions import check  # noqa: E402

FEATURE = "widget-plumbing"

# A report with real findings stated as prose and NO gate headings at all.
# This is the shape a dropped output contract produces.
HEADINGLESS = """# Audit Report

I reviewed the design and found two blocking problems.

1. The resolver is duplicated across two modules.
2. The cache key omits refs, so grounding is contaminated.
"""

CLEAN = """# Audit Report

## Must-fix

None

## Should-fix

None
"""

DIRTY = """# Audit Report

## Must-fix

- The resolver is duplicated across two modules.

## Should-fix

None
"""


def _repo(tmp_path: Path, *, plan_audit: str, design_audit: str) -> Path:
    plan_dir = tmp_path / "docs" / "01-plan" / "features"
    design_dir = tmp_path / "docs" / "02-design" / "features"
    plan_dir.mkdir(parents=True)
    design_dir.mkdir(parents=True)
    (plan_dir / f"{FEATURE}.plan.md").write_text("# plan\n")
    (design_dir / f"{FEATURE}.design.md").write_text("# design\n")
    (plan_dir / f"{FEATURE}.plan.audit.v1.md").write_text(plan_audit)
    (design_dir / f"{FEATURE}.design.audit.v1.md").write_text(design_audit)
    return tmp_path


def test_clean_audits_still_pass(tmp_path: Path) -> None:
    """Control: the fix must not break the ordinary clean path."""
    code, lines = check(_repo(tmp_path, plan_audit=CLEAN, design_audit=CLEAN), FEATURE)
    assert code == 0, lines
    assert lines == ["OK"]


def test_dirty_audit_still_fails(tmp_path: Path) -> None:
    """Control: a real Must-fix finding must still block, and still as DIRTY."""
    code, lines = check(_repo(tmp_path, plan_audit=DIRTY, design_audit=CLEAN), FEATURE)
    assert code == 1
    assert any(line.startswith("DIRTY:") for line in lines), lines


@pytest.mark.parametrize("slot", ["plan", "design"])
def test_headingless_audit_does_not_clear_the_gate(tmp_path: Path, slot: str) -> None:
    """#39 — the defect. A heading-less report must NOT score as zero findings."""
    repo = _repo(
        tmp_path,
        plan_audit=HEADINGLESS if slot == "plan" else CLEAN,
        design_audit=HEADINGLESS if slot == "design" else CLEAN,
    )
    code, lines = check(repo, FEATURE)
    assert code == 1, (
        f"heading-less {slot} audit CLEARED the Phase-5 gate (fails open) — got {lines}"
    )
    assert any(line.startswith("INVALID:") for line in lines), (
        f"expected an INVALID: line naming the unscoreable {slot} report, got {lines}"
    )


def test_invalid_is_distinct_from_dirty(tmp_path: Path) -> None:
    """An unscoreable report is not the same finding as a report with real Must-fix items.

    Collapsing the two would tell the operator to go fix findings in a file that never
    delivered any, which is the wrong remedy: the report needs re-obtaining, not editing.
    """
    repo = _repo(tmp_path, plan_audit=HEADINGLESS, design_audit=CLEAN)
    _, lines = check(repo, FEATURE)
    assert not any(line.startswith("DIRTY:") for line in lines), lines


def test_guard_routes_through_has_gate_sections(tmp_path: Path) -> None:
    """The refusal must come from the shared guard, not a re-derived local check.

    Mutation-style: neutralise `has_gate_sections` at the module under test. If the
    refusal survives, this caller grew its own copy of the check and the two can drift
    apart again — which is the whole defect.
    """
    import h_mad_do_preconditions as mod

    if not hasattr(mod, "has_gate_sections"):
        pytest.fail(
            "h_mad_do_preconditions does not reference has_gate_sections — "
            "the guard was re-derived locally instead of shared (#39)"
        )

    repo = _repo(tmp_path, plan_audit=HEADINGLESS, design_audit=CLEAN)
    original = mod.has_gate_sections
    try:
        mod.has_gate_sections = lambda text: True  # type: ignore[assignment]
        _, lines = check(repo, FEATURE)
    finally:
        mod.has_gate_sections = original  # type: ignore[assignment]

    assert not any(line.startswith("INVALID:") for line in lines), (
        "neutralising has_gate_sections did not remove the refusal — the check is "
        "duplicated locally rather than routed through the shared guard (#39)"
    )
