"""The `wiring` task shape and its wire-scoped revert are wired through Phase 5.

Two consecutive wiring tasks shipped their single load-bearing design decision
untested. Every audit cycle passed it and so did the RED phase; only a mutation
scoped to the connection caught it — twice. That is structural, not bad luck:
every Phase-5 gate is scoped to the CALLEE while a wiring task's deliverable is
the CONNECTION. RED goes red because the callee is absent; the 5e revert test
removes both sides, so its RED split returns identically for a wired and an
unwired build; the anti-gaming audit finds a callee-scoped unit test perfectly
discriminating; and 6a-prime sees a call site that is present.

These tests pin the four places the counter-measure lives — the impl-plan's
`Task shape`/`WIRE`/`WIRE-PIN` fields, 5d's failure-mode check, 5e's wire-scoped
revert, and the halt routes — so the recipe cannot drift back out of the skill.

Every assertion is a distinctive contiguous literal, whitespace-normalised, and
scoped to the ONE file it is about: a doc test asserting component words passed
once with the documented guidance deleted, because both words already appeared
in unrelated prose nearby.
"""

from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL = SKILL_DIR / "SKILL.md"
PROTOCOLS = SKILL_DIR / "references" / "inline-protocols.md"
IMPLEMENTER = SKILL_DIR / "references" / "codex-implementer-prompt.md"
VERIFIER = SKILL_DIR / "references" / "codex-verifier-prompt.md"
RECOVERY = SKILL_DIR / "references" / "failure-recovery.md"
BASE = SKILL_DIR / "invariants.base.md"


def _norm(path: Path) -> str:
    """Collapse whitespace so a markdown reflow cannot break an assertion."""
    return " ".join(path.read_text(encoding="utf-8").split())


# (file, literal, why it is load-bearing)
GUIDANCE = [
    (
        PROTOCOLS,
        "**Task shape**: `new-behaviour` | `refactor` | `wiring`",
        "the impl-plan template must make every task declare its shape",
    ),
    (
        PROTOCOLS,
        "**WIRE-PIN** (`wiring` shape only): `<test id that fails when ONLY the wire "
        "is removed, callee intact>`",
        "the pin must be named in the impl-plan — 5b is the last gate that can require it",
    ),
    (
        PROTOCOLS,
        "every `wiring`-shaped task carries both `WIRE` and `WIRE-PIN`",
        "the quality bar must state the obligation, or the template field reads as optional",
    ),
    (
        SKILL,
        "The third task shape is `wiring`, and counts cannot gate it.",
        "5d gates on counts; a wire is invisible to a count, so the shape needs its own rule",
    ),
    (
        SKILL,
        "failure mode per test, not only the count",
        "the failure MODE is the only signal at 5d that distinguishes a wire test",
    ),
    (
        SKILL,
        "`wiring` task the whole-module revert is not sufficient",
        "5e's revert test must not be read as covering the connection",
    ),
    (
        SKILL,
        "Revert the **connection only**",
        "the counter-measure is a narrower revert, not more of the same review",
    ),
    (
        IMPLEMENTER,
        "this is a `wiring` task and the pin is its single load-bearing test",
        "the implementer must know the pin is the deliverable, not an extra test",
    ),
    (
        VERIFIER,
        "Wire-scoped revert",
        "the anti-gaming pass is where the mutation becomes a gate rather than a habit",
    ),
    (
        VERIFIER,
        "<INLINE_WIRE_PIN>",
        "the orchestrator must have a slot to pass the pin into the verify dispatch",
    ),
]


@pytest.mark.parametrize(
    "path,literal,why",
    GUIDANCE,
    ids=[f"{p.name}:{lit[:40]}" for p, lit, _ in GUIDANCE],
)
def test_wiring_guidance_literal_present(path: Path, literal: str, why: str) -> None:
    assert " ".join(literal.split()) in _norm(path), f"{path.name} dropped guidance: {why}"


# Halt tokens are the executable half: guidance with no halt route is advice.
HALT_TOKENS = [
    "step5d:no_wire_pin:<module>",
    "step5d:red_wrong_reason:<module>",
    "step5e:wire_unenforced:<module>",
]


@pytest.mark.parametrize("token", HALT_TOKENS)
def test_halt_route_documented_in_recovery_table(token: str) -> None:
    assert token in _norm(RECOVERY), (
        f"{token} has no recovery row — a halt an operator cannot look up is a dead end"
    )


@pytest.mark.parametrize("token", HALT_TOKENS)
def test_halt_route_is_raised_by_the_phase_that_owns_it(token: str) -> None:
    assert token in _norm(SKILL), (
        f"{token} is documented in failure-recovery.md but no Phase-5 step raises it; "
        "both halves of a doc change must land together"
    )


def test_skill_cites_the_connection_enforcement_invariant() -> None:
    # The audit layers could not see the defect because no rubric rule covered it.
    # The Phase-5 steps must point at the rule that now does, so a reader of 5d/5e
    # reaches the rationale rather than treating the extra revert as ceremony.
    assert '§"Connection enforcement"' in _norm(SKILL), (
        "SKILL.md Phase 5 must cite invariants.base.md §\"Connection enforcement\""
    )
    assert "## Connection enforcement" in _norm(BASE), (
        "the cited invariant does not exist — the citation would be a dangling reference"
    )
