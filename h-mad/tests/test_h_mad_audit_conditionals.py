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

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / "h-mad"
TEMPLATE = SKILL_DIR / "audit-prompt.template.md"
SKILL_MD = SKILL_DIR / "SKILL.md"

AUDIT_TYPES = ("plan", "design", "impl-plan")
MARKER = re.compile(r"\{\{ONLY:([a-z,\-]+)\}\} ?")
END_ONLY = "{{END-ONLY}}"
LEGACY = ("{For plan and design audits:}", "{For design audit only:}",
          "{For impl-plan audit only:}", "{Design only")
NOTE_START = "<!-- ORCHESTRATOR-NOTE:START"
NOTE_END = "ORCHESTRATOR-NOTE:END -->"


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def resolve(text: str, audit_type: str) -> str:
    """Reference resolver for SKILL.md step 1.5."""
    lines = text.splitlines()
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        m = MARKER.search(line)
        if not m:
            out.append(line)
            i += 1
            continue

        applies = audit_type in m.group(1).split(",")
        stripped = MARKER.sub("", line, count=1)
        is_block = not stripped.strip()

        if is_block:
            j = i + 1
            while j < len(lines) and lines[j].strip() != END_ONLY:
                j += 1
            if j == len(lines):
                raise ValueError(f"unterminated block marker on line {i + 1}")
            if applies:
                out.extend(lines[i + 1 : j])
            i = j + 1
        else:
            base = _indent(line)
            j = i + 1
            while j < len(lines) and lines[j].strip() and _indent(lines[j]) > base:
                j += 1
            if applies:
                out.append(stripped)
                out.extend(lines[i + 1 : j])
            i = j
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def raw() -> str:
    return TEMPLATE.read_text(encoding="utf-8")


def tmpl() -> str:
    """The template as step 1.5 sees it — step 1 has already dropped the note.

    The note necessarily *documents* the convention (and quotes the legacy
    spellings it replaced), so scanning the raw file for markers would flag the
    documentation as the defect. Stripping first mirrors real assembly order.
    """
    text = raw()
    head, _, rest = text.partition(NOTE_START)
    _, _, tail = rest.partition(NOTE_END)
    return head + tail.lstrip("\n")


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

    def test_orchestrator_note_carries_the_convention_and_is_stripped(self):
        """The convention is orchestrator guidance, so it belongs in the note —
        which means it cannot leak to the reviewer even if it is verbose."""
        t = raw()
        note = t[: t.index(NOTE_END)]
        assert "{{ONLY:" in note and END_ONLY in note
        assert "{{" not in tmpl()[: tmpl().index("You are the agy audit reviewer")]
