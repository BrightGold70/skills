"""FR-9 two-layer Axis B invariants: base (skill-shipped) + project (domain)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / "h-mad"
TEMPLATE = SKILL_DIR / "audit-prompt.template.md"
BASE = SKILL_DIR / "invariants.base.md"
EXAMPLE = SKILL_DIR / "invariants.example.md"
PROJECT_INVARIANTS = REPO_ROOT / ".h-mad" / "invariants.md"
SKILL_MD = SKILL_DIR / "SKILL.md"
SCRIPT_DIR = SKILL_DIR / "scripts"

_NOTE_START = "<!-- ORCHESTRATOR-NOTE:START"
_NOTE_END = "ORCHESTRATOR-NOTE:END -->"

_BASE_RULE_HEADINGS = (
    "Audit-gate signal discipline",
    "Single-source contract",
    "Standalone / no plugin dependency",
    "No new external dependency",
    "Doc-template superset compliance",
    "Operator-override preservation",
    "Backward compatibility",
    "Marker discipline",
)

sys.path.insert(0, str(SCRIPT_DIR))
from h_mad_audit_gate import classify  # noqa: E402


def _strip_orchestrator_note(template: str) -> str:
    """SKILL.md step 1: drop the leading orchestrator note before substitution."""
    if _NOTE_START not in template:
        return template
    head, _, rest = template.partition(_NOTE_START)
    _, _, tail = rest.partition(_NOTE_END)
    return head + tail.lstrip("\n")


def _assemble(template: str, base_text: str, project_text: str) -> str:
    return (
        _strip_orchestrator_note(template)
        .replace("<INLINE_BASE_INVARIANTS>", base_text)
        .replace("<INLINE_PROJECT_INVARIANTS>", project_text)
    )


def test_base_invariants_file_exists_with_workflow_rules():
    # AC-9.1
    assert BASE.is_file()
    text = BASE.read_text(encoding="utf-8")
    for heading in (
        "Audit-gate signal discipline",
        "Single-source contract",
        "Standalone",
        "Doc-template superset compliance",
        "Operator-override preservation",
        "Marker discipline",
    ):
        assert heading in text, f"base invariants missing rule: {heading}"


def test_template_has_both_slots_base_before_project():
    # AC-9.2 (structural): template exposes both slots, base before project
    tmpl = TEMPLATE.read_text(encoding="utf-8")
    assert "<INLINE_BASE_INVARIANTS>" in tmpl
    assert "<INLINE_PROJECT_INVARIANTS>" in tmpl
    assert tmpl.index("<INLINE_BASE_INVARIANTS>") < tmpl.index("<INLINE_PROJECT_INVARIANTS>")


def test_assembled_prompt_places_base_before_project():
    # AC-9.2 (behavioral): real substitution preserves base-then-project order
    tmpl = TEMPLATE.read_text(encoding="utf-8")
    out = _assemble(tmpl, "BASE_RULE_MARKER", "PROJECT_RULE_MARKER")
    assert "BASE_RULE_MARKER" in out and "PROJECT_RULE_MARKER" in out
    assert out.index("BASE_RULE_MARKER") < out.index("PROJECT_RULE_MARKER")


def test_base_present_when_project_empty():
    # AC-9.3 / AC-9.5: base survives an empty project layer
    tmpl = TEMPLATE.read_text(encoding="utf-8")
    out = _assemble(tmpl, BASE.read_text(encoding="utf-8"), "")
    assert "Audit-gate signal discipline" in out


def test_base_block_labeled_non_overridable():
    # AC-9.4 (structural): non-overridability + sidecar-still-applies stated
    tmpl = TEMPLATE.read_text(encoding="utf-8")
    base_segment = tmpl[
        tmpl.index("### Base invariants") : tmpl.index("### Project invariants")
    ]
    assert "non-overridable" in base_segment.lower()
    assert "acknowledged-not-fixed" in base_segment.lower()


def test_operator_sidecar_excludes_base_layer_item():
    # AC-9.4 (behavioral): a base-layer finding under the sidecar is excluded
    text = "\n".join(
        [
            "## Must-fix",
            "- base: marker discipline not emitted on halt",
            "## Acknowledged-not-fixed",
            "- base: marker discipline not emitted on halt",
            "",
        ]
    )
    result = classify(text, acknowledged={"base: marker discipline not emitted on halt"})
    assert result["must_count"] == 0
    assert result["verdict"] == "PASS"


def test_example_does_not_duplicate_base_rule_headings():
    # AC-7.1 / AC-9.6: the domain example must not re-teach base workflow rules
    example = EXAMPLE.read_text(encoding="utf-8")
    heading_lines = {
        line.lstrip("#").strip()
        for line in example.splitlines()
        if line.startswith("## ") or line.startswith("### ")
    }
    for base_heading in _BASE_RULE_HEADINGS:
        assert base_heading not in heading_lines, (
            f"invariants.example.md duplicates base rule heading: {base_heading}"
        )


# --- Slot-token hygiene -------------------------------------------------------
# Assembly is a literal whole-file string replace, so a *bracketed* slot mention in
# prose is indistinguishable from a real slot. Two regressions followed from that:
# the rubrics were inlined twice (the template's own header blockquote mentioned
# both slots bracketed), and a raw `<INLINE_BASE_INVARIANTS>` still reached the
# reviewer (invariants.base.md's header re-emitted the token *after* substitution).
# Rule: prose names a slot bare; only a real slot is bracketed.


def test_template_declares_each_invariant_slot_exactly_once():
    tmpl = TEMPLATE.read_text(encoding="utf-8")
    for slot in ("<INLINE_BASE_INVARIANTS>", "<INLINE_PROJECT_INVARIANTS>"):
        assert tmpl.count(slot) == 1, (
            f"{slot} appears {tmpl.count(slot)}x in the template; a bracketed prose "
            "mention gets substituted too and duplicates the whole rubric"
        )


def test_inlined_files_carry_no_bracketed_slot_tokens():
    # A bracketed token inside a file that is itself inlined survives substitution
    # and reaches the reviewer as an unfilled-looking placeholder.
    for path in (BASE, EXAMPLE, PROJECT_INVARIANTS):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        assert "<INLINE_" not in text, (
            f"{path.name} contains a bracketed <INLINE_…> token; write the slot name "
            "bare in prose or it survives assembly into the dispatched prompt"
        )


def test_assembled_prompt_has_no_residual_slot_token_and_no_duplicate_rubric():
    out = _assemble(
        TEMPLATE.read_text(encoding="utf-8"),
        BASE.read_text(encoding="utf-8"),
        PROJECT_INVARIANTS.read_text(encoding="utf-8")
        if PROJECT_INVARIANTS.is_file()
        else "",
    )
    for slot in ("<INLINE_BASE_INVARIANTS>", "<INLINE_PROJECT_INVARIANTS>"):
        assert slot not in out, f"{slot} survives assembly into the dispatched prompt"
    assert out.count("# H-MAD Base Invariants") == 1, "base rubric inlined more than once"
    if PROJECT_INVARIANTS.is_file():
        assert out.count("# H-MAD Project Invariants") == 1, (
            "project rubric inlined more than once"
        )


def test_orchestrator_note_is_fenced_and_stripped_before_dispatch():
    tmpl = TEMPLATE.read_text(encoding="utf-8")
    assert _NOTE_START in tmpl and _NOTE_END in tmpl, (
        "the orchestrator note must be fenced so assembly can drop it"
    )
    out = _assemble(tmpl, "BASE_RULE_MARKER", "PROJECT_RULE_MARKER")
    assert _NOTE_START not in out and _NOTE_END not in out
    assert "Audit Prompt Template" not in out, (
        "the reviewer must not be told it is reading a template"
    )
    assert out.lstrip().startswith("You are the agy audit reviewer")


def test_skill_documents_note_strip_and_residual_placeholder_preflight():
    skill = SKILL_MD.read_text(encoding="utf-8")
    assert "ORCHESTRATOR-NOTE:END" in skill, "step 1 must tell the orchestrator to strip the note"
    assert "unfilled_slot" in skill, "assembly must halt on a residual <INLINE_…> token"
