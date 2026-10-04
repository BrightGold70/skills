"""A "recognise X" contract needs a REAL X before any gate scores it clean.

Skill-candidates row "live-shape-probe-before-the-gate": `pin-agents-tail-banner`
passed 2663 tests, 49 mutations and 53 impl-plan audit cycles while `_agent_tail_re`
matched 0 of 5 real agent banners; all 12 corpus positives were idealised. The rule was
recorded only in the backlog, which no dispatch reads. It belongs in the invariants,
which every audit prompt splices in.
"""
from __future__ import annotations

from pathlib import Path

INVARIANTS = Path(__file__).resolve().parents[1] / "invariants.base.md"
FLAT = " ".join(INVARIANTS.read_text(encoding="utf-8").split())


def test_invariants_require_a_captured_sample_for_a_recognise_contract() -> None:
    assert "captured from the running system" in FLAT
    assert "0 of 5 real" in FLAT, "the rule must carry its measured case"


def test_the_rule_names_what_an_auditor_checks() -> None:
    assert "an idealised fixture is not a sample" in FLAT
