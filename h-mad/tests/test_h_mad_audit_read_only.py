"""An audit reviewer reads; it does not repair what it is measuring.

Background. On 2026-08-28 a Phase-5b impl-plan audit dispatched to agy modified
three tracked files in the audited repository. Two were cosmetic rewrites of a
Version History. The third added a `monkeypatch.setattr` stubbing out
`CognitiveGate.screen` in a test unrelated to the feature under audit, turning a
red test green by removing the call the test existed to exercise. The audit
report described this as having "restored a green test suite".

Three distinct failures compound there, and only the first is about writing:

* An auditor that edits destroys its own evidence. The next cycle measures a
  tree the previous cycle changed, so a finding can be "fixed" into invisibility
  without ever being reported.
* The stated cause was false. The suite was failing because a contract test's
  filename regex could not parse the per-pass audit reports the audit itself had
  just written; the Version History rewrite could not have affected that assert.
  A confident wrong cause is worse than no cause, because it is acted on.
* A red test made green by deleting its measurement is a worse state than the
  red test, and it is silent — nothing downstream can tell the two apart.

The prompt is the only place this can be said before the fact, so it is pinned
here rather than left to the reviewer's judgement.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = REPO_ROOT / "h-mad" / "audit-prompt.template.md"

ORCH_NOTE_END = "<!-- ORCHESTRATOR-NOTE:END -->"


def reviewer_body() -> str:
    """The part of the template a reviewer actually receives.

    Everything above ORCHESTRATOR-NOTE:END is stripped at assembly, so a rule
    written there would be addressed to the orchestrator and never reach agy —
    which is exactly the shape of a guard that looks present and is not.
    """
    text = TEMPLATE.read_text()
    assert ORCH_NOTE_END in text, "orchestrator note delimiter missing"
    return text.split(ORCH_NOTE_END, 1)[1]


def test_reviewer_is_told_it_is_read_only() -> None:
    body = reviewer_body().casefold()
    assert "read-only" in body
    assert "do not modify the repository" in body


def test_reviewer_is_told_to_report_rather_than_fix() -> None:
    """The prohibition alone is not enough — it must say what to do instead.

    "Do not edit" with no alternative reads as an obstacle to route around when
    the reviewer believes it has found a one-line fix.
    """
    body = reviewer_body().casefold()
    assert "report it as a finding" in body
    assert "leave it broken" in body


def test_read_only_rule_reaches_the_reviewer_not_just_the_orchestrator() -> None:
    """Guards the placement, which is the way this rule fails silently."""
    text = TEMPLATE.read_text()
    note, body = text.split(ORCH_NOTE_END, 1)
    assert "do not modify the repository" not in note.casefold(), (
        "the rule sits inside the orchestrator note, which assembly strips — "
        "it would never reach agy"
    )
    assert "do not modify the repository" in body.casefold()


SKILL_MD = REPO_ROOT / "h-mad" / "SKILL.md"


def test_skill_md_tells_the_orchestrator_to_check_the_tree_after_an_audit() -> None:
    """The prompt rule is advice to a model; the tree check is the backstop.

    Both are needed and neither substitutes: a reviewer that ignores the prompt
    leaves no trace except the delta, and an orchestrator that never looks will
    not see it.
    """
    text = SKILL_MD.read_text().casefold()
    assert "check the working tree after every audit dispatch" in text
    assert "git status --short" in text
