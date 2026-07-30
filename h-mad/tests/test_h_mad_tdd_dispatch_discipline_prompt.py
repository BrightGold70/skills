"""Doc-tests for the TDD dispatch verification-discipline prompts."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
IMPLEMENTER = REPO_ROOT / "h-mad" / "references" / "codex-implementer-prompt.md"
VERIFIER = REPO_ROOT / "h-mad" / "references" / "codex-verifier-prompt.md"
SKILL = REPO_ROOT / "h-mad" / "SKILL.md"


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
    assert _norm("Perform the revert test defined in SKILL.md §5e.") in verifier

    mechanism_phrases = ("revert production", "executing the symbol", "grepping")
    assert all(phrase not in verifier for phrase in mechanism_phrases)

    all_prompt_text = "\n".join(
        path.read_text(encoding="utf-8") for path in (SKILL, VERIFIER, IMPLEMENTER)
    )
    for phrase in mechanism_phrases:
        assert all_prompt_text.count(phrase) == 1, (
            f"mechanism phrase must have exactly one authoritative occurrence: {phrase!r}"
        )


def test_skill_author_callform_rule_present() -> None:
    body = _norm(SKILL.read_text(encoding="utf-8"))
    literal = "assert the call form, not an occurrence count over a whole method"
    assert _norm(literal) in body


def test_skill_pin_reverify_rule_present() -> None:
    body = _norm(SKILL.read_text(encoding="utf-8"))
    assert _norm("Re-verify every impl-plan pin") in body
