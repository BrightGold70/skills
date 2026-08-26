"""Doc-rule pins for the 2026-08-25 candidate batch.

Seven candidate rows whose own text said the fix was a documented rule rather
than code. A rule that lives only in a backlog row is not a rule, so each one is
pinned here: present, in the section it belongs to, and carrying the specific
claim that makes it actionable rather than a restatement of its heading.

The last point is the whole risk with doc tests. A test asserting two common
words passes with the guidance deleted, because both words already appear in
nearby prose — that has happened in this repo. So every assertion below is
scoped to ONE section's text and keyed on a phrase that exists nowhere else, and
`TestTheseTestsCanFail` proves the scoping actually bites.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[1]
INVARIANTS = SKILL_DIR / "invariants.base.md"
SKILL = SKILL_DIR / "SKILL.md"


def section_text(path: Path, name: str) -> str:
    """The body of `## <name>`, bounded by the next `## ` heading.

    Scoped rather than whole-file on purpose: a whole-file `in` check is
    satisfied by any other section that happens to use the same words.
    """
    lines = path.read_text().split("\n")
    heads = [i for i, l in enumerate(lines) if l.strip() == f"## {name}"]
    assert len(heads) == 1, f"{path.name} §{name}: expected 1 heading, found {len(heads)}"
    start = heads[0] + 1
    end = start
    while end < len(lines) and not lines[end].startswith("## "):
        end += 1
    return "\n".join(lines[start:end])


def flat(text: str) -> str:
    """Collapse wrapping so a phrase split across lines still matches."""
    return " ".join(text.split())


# (file, section, phrase that appears nowhere else, why it is the load-bearing part)
RULES = [
    (INVARIANTS, "Assumption verification", "the controlled PAIR",
     "a repro confirms the symptom, never the cause"),
    (INVARIANTS, "Assumption verification", "Re-run the MEASUREMENT as well as the claim",
     "a brief's conclusion can be right while its method is wrong"),
    (INVARIANTS, "Test discrimination", "must model the step the real system CONSUMES",
     "the fixture lying, as distinct from the assertion being wrong"),
    (INVARIANTS, "Test discrimination", "Cardinality is part of the model",
     "a fake writing a path once where production writes it twice"),
    (INVARIANTS, "Mutation verification", "vary one field and keep the anchor shared",
     "one mutation per separable part of a failure"),
    (INVARIANTS, "Mutation verification", "four distinct causes",
     "survived collapses missing guard / equivalent mutant / weak test / never ran"),
    (INVARIANTS, "Verifying a review finding", "facts, concern, prescription",
     "the three parts fail independently"),
    (INVARIANTS, "Verifying a review finding", "applying it as a mutation and reverting",
     "how a prescription gets tested rather than trusted"),
    (SKILL, "Audit prompt assembly", "sweep the corrected VALUE",
     "the step between revising and re-auditing"),
    (SKILL, "Audit prompt assembly", "RELOCATES it",
     "closing a class in one document of a pair moves it rather than fixing it"),
    (SKILL, "Phase 5 (Implementation) sub-steps", "does the running binary emit what the design says",
     "the fixed question, since there is no fixed command"),
    (SKILL, "Editing this skill while a run is in flight", "insertion-only before committing",
     "distinguishes a clean splice from a slice that ate a section"),
    (SKILL, "Helper scripts (all in `~/.claude/skills/h-mad/scripts/`)", "OFFCONTRACT: NONE|FOUND|UNREADABLE",
     "the scanner that closes J30 was tested and mutation-pinned but absent from the docs, so "
     "no orchestrator following SKILL.md could ever reach it"),
]


@pytest.mark.parametrize(
    "path,section,phrase,why",
    RULES,
    ids=[f"{p.stem}:{s}:{ph[:28]}" for p, s, ph, why in RULES],
)
def test_the_rule_is_present_in_its_own_section(
    path: Path, section: str, phrase: str, why: str
) -> None:
    assert phrase in flat(section_text(path, section)), (
        f"{path.name} §{section} no longer carries {phrase!r} — {why}"
    )


class TestTheseTestsCanFail:
    """A doc test that cannot fail is decoration (§"Test discrimination")."""

    @pytest.mark.parametrize(
        "path,section,phrase,why", RULES,
        ids=[f"{p.stem}:{s}:{ph[:28]}" for p, s, ph, why in RULES],
    )
    def test_each_phrase_is_unique_to_its_section(
        self, path: Path, section: str, phrase: str, why: str
    ) -> None:
        """Scoping only bites if the phrase is absent from the rest of the file.

        Otherwise deleting the rule leaves the assertion passing on unrelated
        prose — the exact way a documentation test in this repo passed with its
        documented guidance removed.
        """
        whole = flat(path.read_text())
        inside = flat(section_text(path, section))
        assert whole.count(phrase) == inside.count(phrase) == 1, (
            f"{phrase!r} occurs {whole.count(phrase)}x in {path.name}; "
            "a deleted rule would still satisfy the pin"
        )

    def test_a_deleted_rule_is_detected(self) -> None:
        """Drive the detector by hand over text with the rule removed."""
        path, section, phrase, _ = RULES[0]
        body = section_text(path, section)
        assert phrase in flat(body)
        assert phrase not in flat(body.replace(phrase, ""))


class TestBatchProvenance:
    def test_the_new_section_is_a_real_heading_not_prose(self) -> None:
        """`Verifying a review finding` was cited by a backlog row as an
        existing Axis-B rule. It did not exist; this is that section."""
        headings = re.findall(r"^## (.+)$", INVARIANTS.read_text(), re.MULTILINE)
        assert headings.count("Verifying a review finding") == 1

    def test_no_section_was_emptied_by_the_batch(self) -> None:
        """Every section these rules landed in still has other content too."""
        for path, section, phrase, _ in RULES:
            body = flat(section_text(path, section))
            assert len(body) > len(phrase) * 3, f"{path.name} §{section} looks truncated"
