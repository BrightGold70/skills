"""Row 2910: SKILL.md stays small, and each split section stays a pointer.

Every `/h-mad` invocation loads SKILL.md whole. Row 2910 moved three sections
(1,534 lines, ~146 KB) into `references/`, leaving a stub under each original
heading. These tests keep it that way: a moved section pasted back, a stub that
stops naming its reference, or a moved subheading that a `SKILL.md §"…"`
cross-reference can no longer find in SKILL.md all fail here.

Reads SKILL.md directly, never through `skill_corpus.skill_text()`, which
replaces the stubs this file exists to check.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from skill_corpus import SPLIT_REFERENCES, skill_text

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_MD = SKILL_DIR / "SKILL.md"

# Was 393,620 bytes before row 2910; 248,399 right after it.
BUDGET_BYTES = 260 * 1024
# The largest stub is ~1.5 KB. A pasted-back section is tens of KB.
STUB_MAX_BYTES = 4 * 1024

MARKER = re.compile(r'^<!-- h-mad split body: SKILL\.md §"(?P<heading>[^"\n]+)" -->$', re.M)


def _stub(skill: str, heading: str) -> str:
    start = skill.index(f"\n## {heading}\n") + 1
    nxt = re.compile(r"^## ", re.M).search(skill, start + 3)
    assert nxt, f"stub {heading!r} is not followed by another ## heading"
    return skill[start:nxt.start()]


def _heading_of(ref: str) -> str:
    m = MARKER.search((SKILL_DIR / ref).read_text(encoding="utf-8"))
    assert m, f"{ref} has no split-body marker"
    return m.group("heading")


def _subheadings(body: str) -> list[str]:
    out, fence = [], False
    for line in body.split("\n"):
        if line.startswith("```"):
            fence = not fence
        if not fence and re.match(r"^#{3,4} ", line):
            out.append(line.lstrip("#").strip())
    return out


def test_skill_md_fits_the_budget() -> None:
    size = SKILL_MD.stat().st_size
    assert size <= BUDGET_BYTES, (
        f"SKILL.md is {size:,} bytes, over the {BUDGET_BYTES:,} budget; it is loaded on every "
        "/h-mad invocation. Move a section to references/ rather than raising the budget."
    )


@pytest.mark.parametrize("ref", SPLIT_REFERENCES)
def test_each_stub_names_its_reference_and_stays_a_pointer(ref: str) -> None:
    skill = SKILL_MD.read_text(encoding="utf-8")
    heading = _heading_of(ref)
    stub = _stub(skill, heading)
    assert f"]({ref})" in stub, f"the {heading!r} stub must link {ref}"
    assert re.search(r"\bbefore\b", stub, re.I), f"the {heading!r} stub must say when to read it"
    size = len(stub.encode("utf-8"))
    assert size <= STUB_MAX_BYTES, (
        f"the {heading!r} stub is {size:,} bytes; its text belongs in {ref}, not SKILL.md"
    )


@pytest.mark.parametrize("ref", SPLIT_REFERENCES)
def test_every_moved_subheading_resolves_from_skill_md(ref: str) -> None:
    """A `SKILL.md §"<subheading>"` cross-reference must still find SKILL.md text."""
    stub = _stub(SKILL_MD.read_text(encoding="utf-8"), _heading_of(ref))
    body = (SKILL_DIR / ref).read_text(encoding="utf-8")
    missing = [h for h in _subheadings(body) if f'§"{h}"' not in stub]
    assert not missing, f"moved subheadings not listed in the stub: {missing}"


def test_skill_text_restores_each_section_in_place_of_its_stub() -> None:
    skill, full = SKILL_MD.read_text(encoding="utf-8"), skill_text()
    for ref in SPLIT_REFERENCES:
        heading = _heading_of(ref)
        body = (SKILL_DIR / ref).read_text(encoding="utf-8")
        verbatim = body[MARKER.search(body).end() + 1:]
        assert _stub(skill, heading) not in full, f"{heading!r}: the stub survived reconstruction"
        assert f"## {heading}\n{verbatim}" in full, f"{heading!r}: body not restored under its heading"


def test_skill_text_refuses_a_linked_reference_that_is_missing(tmp_path: Path) -> None:
    (tmp_path / "SKILL.md").write_text(
        "## A\n\nRead [x](references/phase5-substeps.md) before 5a.\n\n## B\n", encoding="utf-8"
    )
    with pytest.raises(FileNotFoundError, match="phase5-substeps.md"):
        skill_text(tmp_path)


def test_skill_text_is_identity_when_nothing_is_split(tmp_path: Path) -> None:
    text = "## A\n\nbody\n\n## B\n"
    (tmp_path / "SKILL.md").write_text(text, encoding="utf-8")
    assert skill_text(tmp_path) == text
