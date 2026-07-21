"""Axis C: design audits must reconcile against the spec's ACs by number.

Background. The audit chain pairs each document with its immediate predecessor
— design audits receive the plan, impl-plan audits receive the design — so the
spec drops out of every audit prompt after Phase 3. Measured on a real feature:
the spec carried 43 AC references and the paired plan carried 5, all incidental
prose in risk and rationale tables. The design audit therefore had no AC list to
reconcile against.

The consequence: five consecutive audit cycles gated `must=0 should=0` (plan 2,
design 3) while the design silently restated three ACs to weaker forms and
omitted a fourth entirely — including one naming a production function that was
consequently never touched. A document read only for internal consistency cannot
distinguish a faithful restatement from a narrowing, because a well-argued
narrowing reads as prose either way. Read against `AC-N.M` by identifier, it is
mechanical.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / "h-mad"
TEMPLATE = SKILL_DIR / "audit-prompt.template.md"
SKILL_MD = SKILL_DIR / "SKILL.md"

sys.path.insert(0, str(SKILL_DIR / "scripts"))


def tmpl() -> str:
    return TEMPLATE.read_text(encoding="utf-8")


def skill() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


class TestSpecSlot:
    """The spec has to reach the prompt before anything can check it."""

    def test_template_exposes_a_paired_spec_slot(self):
        assert "<INLINE_PAIRED_SPEC>" in tmpl()

    def test_spec_slot_is_distinct_from_the_paired_plan_slot(self):
        """Design audits receive both: the plan is the contract, the spec is
        the source of truth for ACs. Collapsing them loses the AC list."""
        t = tmpl()
        assert "<INLINE_PAIRED_PLAN>" in t
        assert "<INLINE_PAIRED_SPEC>" in t

    def test_substitution_reaches_the_assembled_prompt(self):
        out = tmpl().replace("<INLINE_PAIRED_SPEC>", "SPEC_MARKER_AC_1_1")
        assert "SPEC_MARKER_AC_1_1" in out
        assert "<INLINE_PAIRED_SPEC>" not in out

    def test_existing_invariant_slots_still_ordered(self):
        """Adding Axis C must not disturb the base-before-project ordering."""
        t = tmpl()
        assert t.index("<INLINE_BASE_INVARIANTS>") < t.index(
            "<INLINE_PROJECT_INVARIANTS>"
        )


class TestAxisCContent:
    def test_template_declares_a_spec_reconciliation_axis(self):
        t = tmpl()
        assert "Axis C" in t
        low = t.lower()
        assert "spec" in low and "reconcil" in low

    def test_requires_enumeration_by_identifier(self):
        """The whole point: by number, not by impression."""
        t = tmpl()
        assert "AC-" in t, "template must reference the AC-N.M identifier form"
        low = t.lower()
        assert "enumerate" in low or "every ac" in low or "each ac" in low

    def test_defines_the_three_classifications(self):
        low = tmpl().lower()
        for verdict in ("implemented-as-written", "restated", "absent"):
            assert verdict in low, f"Axis C missing classification: {verdict}"

    def test_restatement_requires_quoting_both_forms(self):
        """A restatement is only auditable if both wordings are visible."""
        low = tmpl().lower()
        assert "quote" in low

    def test_divergence_is_a_blocking_finding(self):
        """The design may win the argument, but not silently — the spec has to
        be amended before the gate clears."""
        low = tmpl().lower()
        assert "must-fix" in low

    def test_axis_c_is_scoped_to_the_audits_that_derive_from_the_spec(self):
        """Impl-plan audits contract against the design, not the spec."""
        t = tmpl()
        idx = t.find("Axis C")
        assert idx != -1
        section = t[idx : idx + 2000].lower()
        assert "design" in section


class TestAssemblyStepsWired:
    """A slot nothing fills is worse than no slot — it renders literally."""

    def test_skill_md_instructs_inlining_the_spec(self):
        assert "<INLINE_PAIRED_SPEC>" in skill()

    def test_spec_inlining_is_ordered_with_the_other_slot_steps(self):
        s = skill()
        assert s.index("<INLINE_PAIRED_SPEC>") > s.index("<INLINE_TARGET_DOC>")

    def test_every_template_slot_has_an_assembly_instruction(self):
        """Guard against the class of bug this issue is: a template that asks
        for something the assembly steps never provide."""
        import re

        slots = set(re.findall(r"<INLINE_[A-Z_]+>", tmpl()))
        s = skill()
        missing = sorted(slot for slot in slots if slot not in s)
        assert not missing, f"template slots with no assembly step: {missing}"


class TestSizeConstraintDocumented:
    """Axis C enlarges an already-large prompt past a measured silent-output
    cliff. Shipping it without saying so would trade a silent audit gap for a
    silent audit failure."""

    def test_skill_md_warns_about_prompt_size(self):
        s = skill().lower()
        assert "prompt size" in s
        assert "53" in s or "49" in s, "cite the measured cliff, not a vague warning"

    def test_skill_md_rejects_trimming_the_design(self):
        """The obvious size fix breaks the axis: filtering the design to its
        AC-bearing sections makes `absent` undetectable."""
        s = skill().lower()
        assert "absent" in s and "trimming the design" in s

    def test_skill_md_names_the_safe_failure_mode(self):
        """An over-long prompt must halt, not pass — that is what makes
        shipping this acceptable despite the size risk."""
        s = skill()
        assert "h_mad_extract_report.py" in s
