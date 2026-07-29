"""Phase-5e anti-gaming VERIFIER prompt template is bundled and wired.

The 5e flow already ships an implementer prompt (`codex-implementer-prompt.md`)
and a spec-reviewer prompt (`agy-spec-reviewer-prompt.md`), but the independent
post-GREEN *anti-gaming verification* — module count, test-discrimination audit,
property-quote-from-source, full-suite-vs-reference, and the content-crosscheck
that catches an agent quoting fabricated numbers under a `STATUS: DONE` — had no
bundled template; it lived only in an ad-hoc scratchpad prompt. These tests pin
the template's existence, its load-bearing literal instructions, and its wiring
into SKILL.md's 5e phase, so the recipe cannot silently drift out of the skill.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VERIFIER = REPO_ROOT / "h-mad" / "references" / "codex-verifier-prompt.md"
SKILL = REPO_ROOT / "h-mad" / "SKILL.md"


def _norm(text: str) -> str:
    """Collapse runs of whitespace so a literal survives reflow/indentation."""
    return " ".join(text.split())


def test_verifier_prompt_reference_exists() -> None:
    assert VERIFIER.is_file(), f"missing bundled verifier template: {VERIFIER}"


# Each entry is a load-bearing literal instruction; asserting the literal (not a
# pair of component words) means deleting the guidance fails the test.
VERIFIER_LITERALS = [
    "Run the module tests and report the count",
    "Anti-gaming audit",
    "quote the line",
    "The orchestrator runs the full suite itself",
    "reference",
    "Cross-check every count you report against",
    "STATUS: DONE",
    "<INLINE_",
]


@pytest.mark.parametrize("literal", VERIFIER_LITERALS)
def test_verifier_prompt_carries_literal(literal: str) -> None:
    body = _norm(VERIFIER.read_text(encoding="utf-8"))
    assert _norm(literal) in body, f"verifier template dropped instruction: {literal!r}"


def test_verifier_prompt_pins_single_status_contract() -> None:
    body = VERIFIER.read_text(encoding="utf-8")
    for value in ("DONE", "DONE_WITH_CONCERNS", "BLOCKED"):
        assert f"STATUS: {value}" in body, f"verifier template missing STATUS: {value}"


def test_skill_5e_wires_the_verifier_reference() -> None:
    body = _norm(SKILL.read_text(encoding="utf-8"))
    assert "references/codex-verifier-prompt.md" in body, (
        "SKILL.md does not reference the bundled verifier template — the 5e "
        "anti-gaming verify would drift back to an ad-hoc scratchpad prompt"
    )
