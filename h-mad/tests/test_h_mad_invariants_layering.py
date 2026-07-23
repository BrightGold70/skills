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
    "Mutation verification",
    "Incident replay",
    "Test discrimination",
    "Assumption verification",
    "Regression provenance",
    "Both halves of a doc change",
    "Reimplementation parity",
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


def test_base_rule_mutation_verification_states_the_literal_instruction():
    # Wave 4b candidate `verify-the-mutation-not-the-command` (recurrence 3).
    #
    # Asserted as a LITERAL sentence, not as component words. A Wave-4a doc test
    # for the `--base` guidance passed with that guidance deleted, because both
    # of its component words already appeared in unrelated prose nearby. A rule
    # that can vanish without failing a test is not in the rubric.
    # Whitespace-normalised so a markdown reflow cannot break the assertion:
    # the instruction is the literal sentence, not the line breaks in it.
    text = " ".join(BASE.read_text(encoding="utf-8").split())
    assert "## Mutation verification" in text
    assert "re-reading the resulting state" in text, (
        "the mutation-verification rule must say to re-read resulting STATE"
    )
    assert "exit code is not evidence that a mutation occurred" in text, (
        "the rule must name the specific fallacy it exists to block"
    )


def test_base_rule_incident_replay_states_the_literal_instruction():
    # Wave 4b candidate `replay-the-incident-against-the-fix` (recurrence 4),
    # reinforced by `replay-detector-against-history` (recurrence 3): 14
    # handcrafted cases passed while the real historical label was rejected.
    text = " ".join(BASE.read_text(encoding="utf-8").split())
    assert "## Incident replay" in text
    assert "replayed against the real artifacts already on disk" in text, (
        "the replay rule must require the historical artifacts, not synthetic cases"
    )
    assert "Synthetic cases alone are a violation" in text, (
        "the rule must state what counts as a violation, or it is advice"
    )


def test_base_rule_test_discrimination_states_the_literal_instruction():
    # Wave 4c: merges `mutation-test-every-guard` (recurrence 7 — the highest on
    # the list) with `discriminating-regression-test` (recurrence 3). Two framings
    # of one mechanism: a check that has never been observed failing has not been
    # shown to check anything.
    text = " ".join(BASE.read_text(encoding="utf-8").split())
    assert "## Test discrimination" in text
    assert "observed failing against the unfixed code" in text, (
        "the rule must require the test be SEEN to fail, not merely to exist"
    )
    assert "Zero failures is a finding, not a reassurance" in text, (
        "the rule must name what a silent suite means, or it reads as optional"
    )


def test_base_rule_assumption_verification_states_the_literal_instruction():
    # Wave 4c: `tracer-bullet-design-assumptions` (recurrence 4).
    text = " ".join(BASE.read_text(encoding="utf-8").split())
    assert "## Assumption verification" in text
    assert "executed as a throwaway command before it is written into the design" in text, (
        "the rule must require execution, not plausibility"
    )
    assert "cites the observed output" in text, (
        "an unevidenced assumption must be identifiable in review"
    )


def test_base_rule_regression_provenance_states_the_literal_instruction():
    # Candidate `test-pinned-the-defect check` (recurrence 3). When a fix breaks
    # an existing test, the reflex is to adjust the test -- but three tests this
    # session (J17 selector, J1 handle, J2 pin path) had asserted the DEFECT as an
    # acceptance criterion, so "make the test pass" would have preserved the bug.
    text = " ".join(BASE.read_text(encoding="utf-8").split())
    assert "## Regression provenance" in text
    assert "asserts current behaviour that the change is fixing" in text, (
        "the rule must name the failure: a test pinning the defect as correct"
    )
    assert "Changing an existing test to pass is a violation unless" in text, (
        "the rule must gate test edits, or it is advice"
    )


def test_base_rule_both_halves_states_the_literal_instruction():
    # Candidate `both-halves doc fix` (recurrence 2). Deleting an unexecutable
    # instruction (J11) is only half done; a test asserting ONLY its absence
    # passes for a deletion that lost the capability.
    text = " ".join(BASE.read_text(encoding="utf-8").split())
    assert "## Both halves of a doc change" in text
    assert "the executable replacement landed" in text, (
        "removing an instruction must assert the replacement, not just the removal"
    )


def test_base_rule_reimplementation_parity_states_the_literal_instruction():
    # Candidate `differential-validator-test` (recurrence 1). J4 replaced
    # `jsonschema` with a bundled validator; the only thing that made it
    # trustworthy was a test asserting verdict-equality with the real library.
    text = " ".join(BASE.read_text(encoding="utf-8").split())
    assert "## Reimplementation parity" in text
    assert "differential test asserting identical results against the original" in text, (
        "reimplementing a dependency must be pinned to the original's behaviour"
    )
    assert "real artifacts on disk" in text, (
        "parity on a synthetic corpus alone repeats the Incident-replay gap"
    )


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
