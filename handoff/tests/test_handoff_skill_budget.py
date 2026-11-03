"""handoff/SKILL.md stays small, and each split mode body stays a pointer.

Every `/handoff` invocation loads SKILL.md whole, and `/handoff read` starts
most sessions: measured 2026-11-03, a session opened with it carried ~41k
tokens of handoff body in its first turn. The split moved the READ, HANDOVER
and TAKEOVER bodies (74,102 bytes) into `references/`, so a WRITE no longer
loads modes it does not run. These tests keep it that way: a moved body pasted
back, a stub that stops naming its reference or saying when to read it, or a
moved subheading a `SKILL.md §"…"` cross-reference can no longer find all fail.

Reads SKILL.md directly, never through `handoff_corpus.skill_text()`, which
replaces the stubs this file exists to check.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from handoff_corpus import SPLIT_REFERENCES, skill_text  # noqa: E402

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_MD = SKILL_DIR / "SKILL.md"

# Was 122,469 bytes before the split; 50,641 right after it.
BUDGET_BYTES = 56 * 1024
STUB_MAX_BYTES = 4 * 1024

# Each stub must say WHEN its reference is read, in words that cover every entry
# point: READ has several spellings, HANDOVER runs as WRITE's subroutine, and
# TAKEOVER is reached from READ Step 3.5 as well as by name.
TRIGGERS = {
    "references/read-mode.md": ("in full before Step 0a, on every READ entry point",),
    "references/handover-mode.md": ("in full before running HANDOVER",
                                    "invokes it as a subroutine"),
    "references/takeover-mode.md": ("in full before adopting a brief",
                                    "from READ Step 3.5"),
}

MARKER = re.compile(r'^<!-- handoff split body: SKILL\.md §"(?P<heading>[^"\n]+)" -->$', re.M)


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
        f"handoff/SKILL.md is {size:,} bytes, over the {BUDGET_BYTES:,} budget; it is loaded on "
        "every /handoff invocation. Move a section to references/ rather than raising the budget."
    )


def test_every_split_reference_has_a_trigger() -> None:
    assert set(TRIGGERS) == set(SPLIT_REFERENCES)


@pytest.mark.parametrize("ref", SPLIT_REFERENCES)
def test_each_stub_names_its_reference_and_says_when_to_read_it(ref: str) -> None:
    skill = SKILL_MD.read_text(encoding="utf-8")
    heading = _heading_of(ref)
    stub = _stub(skill, heading)
    assert f"]({ref})" in stub, f"the {heading!r} stub must link {ref}"
    flat = " ".join(stub.split())
    for phrase in TRIGGERS[ref]:
        assert phrase in flat, f"the {heading!r} stub must say when to read it: {phrase!r}"
    size = len(stub.encode("utf-8"))
    assert size <= STUB_MAX_BYTES, f"the {heading!r} stub is {size:,} bytes; its text belongs in {ref}"


@pytest.mark.parametrize("ref", SPLIT_REFERENCES)
def test_each_stub_says_to_load_its_reference_with_the_read_tool(ref: str) -> None:
    # Measured 2026-11-03 on the first live `/handoff read` after the split: the
    # agent ran `cat references/read-mode.md` (38.8 KB), Bash returned a ~2 KB
    # preview over its inline-output limit, and only a second `Read` call
    # recovered the procedure. An agent that accepts the preview runs READ
    # without Steps 0a-5 and nothing reports it.
    stub = " ".join(_stub(SKILL_MD.read_text(encoding="utf-8"), _heading_of(ref)).split())
    assert "with the `Read` tool, not `cat`" in stub, (
        f"the stub for {ref} must say to load it with the Read tool; a shell read of a "
        "reference this size returns a truncated preview"
    )


@pytest.mark.parametrize("ref", SPLIT_REFERENCES)
def test_every_moved_subheading_resolves_from_skill_md(ref: str) -> None:
    stub = _stub(SKILL_MD.read_text(encoding="utf-8"), _heading_of(ref))
    body = (SKILL_DIR / ref).read_text(encoding="utf-8")
    missing = [h for h in _subheadings(body) if f'§"{h}"' not in stub]
    assert not missing, f"moved subheadings not listed in the stub: {missing}"


def test_skill_text_restores_each_mode_body_in_place_of_its_stub() -> None:
    skill, full = SKILL_MD.read_text(encoding="utf-8"), skill_text()
    for ref in SPLIT_REFERENCES:
        heading = _heading_of(ref)
        body = (SKILL_DIR / ref).read_text(encoding="utf-8")
        verbatim = body[MARKER.search(body).end() + 1:]
        assert _stub(skill, heading) not in full, f"{heading!r}: the stub survived reconstruction"
        assert f"## {heading}\n{verbatim}" in full, f"{heading!r}: body not restored under its heading"


def test_mode_routing_stays_in_the_core() -> None:
    """Routing decides which reference to read, so it can never move out."""
    skill = SKILL_MD.read_text(encoding="utf-8")
    assert "## Mode routing — decide first" in skill
    for mode in ("**WRITE**", "**READ**", "**LEARN**", "**HANDOVER**", "**TAKEOVER**"):
        assert mode in skill, mode
