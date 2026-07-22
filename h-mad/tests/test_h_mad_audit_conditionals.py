"""`{{ONLY:…}}` applicability markers: one convention, mechanically resolvable.

Background. The template carried three different spellings of "this bit applies only
to some audit types" — `{For plan and design audits:}`, `{For design audit only:}`,
`{Design only — cross-doc:}` — and never said whether a non-applicable construct
should be dropped or merely blanked. Assembly is manual, so the ambiguity resolved
differently every run: measured across the 69 staged prompts on disk,
`{Design only — cross-doc:}` survived into **69 of 69** (telling every plan and
impl-plan audit to perform a design-only cross-doc check), while the doc-slot lines
were dropped in some runs and shipped with a raw `<INLINE_PAIRED_PLAN>` in others.

The convention is now single and machine-checkable: a marker is an assembly
directive, it never reaches the reviewer, and nothing containing `{{` may survive
into a dispatched prompt. `resolve()` below is the reference implementation of the
rule stated in the template's orchestrator note and SKILL.md step 1.5.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / "h-mad"
TEMPLATE = SKILL_DIR / "audit-prompt.template.md"
SKILL_MD = SKILL_DIR / "SKILL.md"

sys.path.insert(0, str(SKILL_DIR / "scripts"))
# The resolver is imported, never re-implemented here. A test copy of the rule
# would let the shipped assembler and the rule these tests pin drift apart --
# exactly the "single-source contract" the base invariants forbid, and the
# drift would be invisible because both sides would still pass.
from h_mad_assemble_audit import (  # noqa: E402
    END_ONLY,
    MARKER,
    NOTE_END,
    NOTE_START,
    PHASES as AUDIT_TYPES,
    resolve,
    strip_orchestrator_note,
)

LEGACY = ("{For plan and design audits:}", "{For design audit only:}",
          "{For impl-plan audit only:}", "{Design only")


def raw() -> str:
    return TEMPLATE.read_text(encoding="utf-8")


def tmpl() -> str:
    """The template as step 1.5 sees it — step 1 has already dropped the note.

    The note necessarily *documents* the convention (and quotes the legacy
    spellings it replaced), so scanning the raw file for markers would flag the
    documentation as the defect. Stripping first mirrors real assembly order.
    """
    return strip_orchestrator_note(raw())


class TestTemplateMarkersAreWellFormed:
    def test_no_legacy_marker_spellings_remain(self):
        t = tmpl()
        found = [m for m in LEGACY if m in t]
        assert not found, f"legacy applicability markers still in template: {found}"

    def test_every_marker_names_only_known_audit_types(self):
        for audiences in MARKER.findall(tmpl()):
            for aud in audiences.split(","):
                assert aud in AUDIT_TYPES, f"unknown audit type in marker: {aud!r}"

    def test_template_actually_uses_the_convention(self):
        assert MARKER.search(tmpl()), "template declares no {{ONLY:…}} markers"

    def test_block_markers_are_balanced(self):
        lines = tmpl().splitlines()
        opens = sum(
            1 for ln in lines if MARKER.search(ln) and not MARKER.sub("", ln).strip()
        )
        closes = sum(1 for ln in lines if ln.strip() == END_ONLY)
        assert opens == closes, f"{opens} block markers vs {closes} {END_ONLY}"


class TestResolutionLeavesNoResidue:
    def test_no_marker_survives_for_any_audit_type(self):
        for audit_type in AUDIT_TYPES:
            out = resolve(tmpl(), audit_type)
            assert "{{" not in out, f"{audit_type}: marker survived resolution"
            assert END_ONLY not in out

    def test_inapplicable_slot_lines_are_dropped_whole_not_blanked(self):
        """A blanked label reads to the reviewer as a *missing* document."""
        plan = resolve(tmpl(), "plan")
        assert "<INLINE_PAIRED_PLAN>" not in plan
        assert "Paired audited plan:" not in plan, "label kept without its document"
        assert "<INLINE_PAIRED_DESIGN>" not in plan
        assert "Paired audited design:" not in plan

    def test_applicable_slot_lines_survive_with_the_marker_stripped(self):
        design = resolve(tmpl(), "design")
        assert "Paired audited plan: <INLINE_PAIRED_PLAN>" in design
        assert "Source spec: <INLINE_PAIRED_SPEC>" in design
        assert "Paired audited design:" not in design


class TestAxisCScoping:
    def test_axis_c_reaches_plan_and_design_audits(self):
        for audit_type in ("plan", "design"):
            assert "Axis C" in resolve(tmpl(), audit_type)

    def test_axis_c_is_absent_from_impl_plan_audits(self):
        """It contracts against the design, not the spec. Previously the whole
        section shipped and told the reviewer to skip itself."""
        out = resolve(tmpl(), "impl-plan")
        assert "Axis C" not in out
        assert "implemented-as-written" not in out

    def test_axis_b_survives_every_audit_type(self):
        """Scoping Axis C must not take the always-on invariant rubric with it."""
        for audit_type in AUDIT_TYPES:
            out = resolve(tmpl(), audit_type)
            assert "<INLINE_BASE_INVARIANTS>" in out
            assert "Axis B" in out


class TestCrossDocBulletScoping:
    def test_cross_doc_bullet_only_reaches_design_audits(self):
        design = resolve(tmpl(), "design")
        assert "does the design implement what the plan promised?" in design
        assert "Flag silent drift" in design, "bullet continuation lines were dropped"
        for audit_type in ("plan", "impl-plan"):
            out = resolve(tmpl(), audit_type)
            assert "what the plan promised" not in out
            assert "Flag silent drift" not in out, (
                "continuation lines outlived their marked bullet"
            )


class TestConventionIsDocumented:
    def test_skill_md_states_the_resolution_rule(self):
        s = SKILL_MD.read_text(encoding="utf-8")
        assert "{{ONLY:" in s
        assert "unresolved_conditional" in s, "preflight must halt on a surviving marker"

    def test_duplication_check_does_not_hardcode_the_project_rubric_heading(self):
        """The project invariants heading is project-authored -- HemaSuite's reads
        '# HPW Project Axis B Invariants'. A hardcoded needle reports a false 0
        everywhere except this repo, which reads as 'no project layer inlined'."""
        s = SKILL_MD.read_text(encoding="utf-8")
        preflight = s[s.index("Residual-placeholder preflight") :][:2500]
        assert "head -1" in preflight, (
            "derive the duplication needle from the invariants file's own first line"
        )
        assert "grep -c 'H-MAD Project Invariants" not in preflight, (
            "hardcoded project rubric heading is repo-specific"
        )

    def test_orchestrator_note_carries_the_convention_and_is_stripped(self):
        """The convention is orchestrator guidance, so it belongs in the note —
        which means it cannot leak to the reviewer even if it is verbose."""
        t = raw()
        note = t[: t.index(NOTE_END)]
        assert "{{ONLY:" in note and END_ONLY in note
        assert "{{" not in tmpl()[: tmpl().index("You are the agy audit reviewer")]
