"""Phase 6a must separate code-vs-design from design-vs-spec.

An unmet AC has two very different causes that present identically:

  - the code diverged from the design  -> implementation defect, fix the code
  - the design diverged from the spec  -> reconciliation decision, escalate

Observed: verifiers briefed to distrust the design and check code against spec
reported three ACs as implementation defects and recommended deleting the tests
covering them. All three were deliberate design narrowings with recorded
rationale, one reached only after 68 test regressions across 6 files and a
second attempt that broke 7 more. Acting on that recommendation would have
repeated work the design had already tried and abandoned with measured cost.

Checking against one document cannot tell the two apart, and the classification
determines both who decides and what changes.
"""

from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
PROTOCOLS = SKILL_DIR / "references" / "inline-protocols.md"


def phase6() -> str:
    """The Phase 6 section only — 6b iterate is a separate protocol."""
    text = PROTOCOLS.read_text(encoding="utf-8")
    start = text.index("## Phase 6 — Gap Analysis")
    end = text.index("## Phase 6b")
    return text[start:end]


class TestTwoAxesRequired:
    def test_protocol_names_both_axes(self):
        low = phase6().lower()
        assert "code-vs-design" in low
        assert "design-vs-spec" in low

    def test_defines_a_classification_per_unmet_ac(self):
        low = phase6().lower()
        for label in ("code-vs-design", "design-vs-spec", "both"):
            assert label in low, f"missing classification: {label}"

    def test_classification_drives_a_different_action(self):
        """The distinction is only useful if it changes what happens next."""
        low = phase6().lower()
        assert "escalate" in low or "operator" in low
        assert "fix the code" in low or "implementation defect" in low

    def test_requires_reading_the_design_rationale_before_concluding(self):
        """A narrowing usually carries its reasoning; the analyst has to look
        for it rather than infer a defect from the diff alone."""
        low = phase6().lower()
        assert "rationale" in low or "reasoning" in low

    def test_warns_that_a_design_narrowing_can_look_like_a_defect(self):
        low = phase6().lower()
        assert "narrow" in low


class TestMatchRateUnchanged:
    """The measurement is against the spec either way — classification changes
    the remedy, not the arithmetic."""

    def test_formula_still_present(self):
        assert "Match rate formula" in phase6()

    def test_partial_credit_still_zero(self):
        low = phase6().lower()
        assert "partial credit" in low


class TestVerdictReflectsClassification:
    def test_verdict_distinguishes_iterate_from_reconcile(self):
        """A design-vs-spec finding is not iterable — 6b is a mechanical fix
        loop and cannot decide which document is right."""
        low = phase6().lower()
        assert "reconcil" in low
