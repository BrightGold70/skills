"""Doc-tests for the TDD dispatch verification-discipline prompts."""

from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]  # h-mad/ — never outside the skill dir
IMPLEMENTER = SKILL_ROOT / "references" / "codex-implementer-prompt.md"
VERIFIER = SKILL_ROOT / "references" / "codex-verifier-prompt.md"
SKILL = SKILL_ROOT / "SKILL.md"


def _norm(text: str) -> str:
    """Collapse runs of whitespace so a literal survives reflow/indentation."""
    return " ".join(text.split())


def test_red_acceptance_evidence_present() -> None:
    body = _norm(IMPLEMENTER.read_text(encoding="utf-8"))
    literals = (
        "For each FAILING test: does the failure message name the property under test?",
        "For each PASSING test: would it still pass if the behaviour it names were deleted?",
        "For each behavioural test: name the method actually invoked, and confirm it is the one that contains the behaviour under test.",
    )
    for literal in literals:
        assert _norm(literal) in body, f"implementer prompt missing RED evidence question: {literal!r}"


def test_green_named_evasions_present() -> None:
    body = _norm(IMPLEMENTER.read_text(encoding="utf-8"))
    for literal in (
        "restructure a string literal, identifier, or import",
        "outside the task's stated scope",
    ):
        assert _norm(literal) in body, f"implementer prompt missing named evasion: {literal!r}"


def test_skill_revert_test_definition_present() -> None:
    body = _norm(SKILL.read_text(encoding="utf-8"))
    for literal in (
        "revert production only",
        "RED split returns EXACTLY",
        "executing the symbol",
        "never by grepping",
    ):
        assert _norm(literal) in body, f"SKILL.md missing revert-test instruction: {literal!r}"


def test_verifier_points_to_skill_not_restates() -> None:
    verifier = _norm(VERIFIER.read_text(encoding="utf-8"))
    implementer = _norm(IMPLEMENTER.read_text(encoding="utf-8"))
    assert _norm("Perform the revert test defined in SKILL.md §5e.") in verifier

    # Single-source: the FR-2 revert-test MECHANISM is authored only in SKILL.md;
    # the verifier and implementer only reference it. Assert the specific
    # instruction LITERALS are absent from those two files — NOT a global count of
    # a common token like "grepping" (SKILL.md legitimately uses that word in
    # unrelated §5e/§6a-prime prose, and an occurrence-count assertion over a whole
    # file is exactly the over-constraint FR-3 warns against — assert the call form).
    mechanism_literals = (
        "revert production only",
        "RED split returns EXACTLY",
        "never by grepping the source",
    )
    for lit in mechanism_literals:
        assert _norm(lit) not in verifier, f"verifier restates FR-2 mechanism: {lit!r}"
        assert _norm(lit) not in implementer, f"implementer restates FR-2 mechanism: {lit!r}"


def test_skill_author_callform_rule_present() -> None:
    body = _norm(SKILL.read_text(encoding="utf-8"))
    literal = "assert the call form, not an occurrence count over a whole method"
    assert _norm(literal) in body


def test_skill_pin_reverify_rule_present() -> None:
    body = _norm(SKILL.read_text(encoding="utf-8"))
    assert _norm("Re-verify every impl-plan pin") in body
