"""The section bound is structural, and the fence is the part that gets dropped.

Every mutant of this helper is silent: a section that ends early still returns a
plausible string, and a positive assertion that happens to land before the cut
still passes. So the pins here are (a) a fixture whose `# comment` sits at column
zero inside a fenced block, and (b) the real document, because the 24k truncation
was found in `h-mad/SKILL.md` and not in any fixture anyone had written.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from docsections import section_from, titled_section

SKILL_MD = Path(__file__).resolve().parents[1] / "SKILL.md"

FIXTURE = """\
# Title

## Alpha

before the block

```bash
# this comment is a heading to a fence-blind bound
echo hi
```

after the block

### Alpha's own subsection

still inside Alpha

## Beta

not Alpha
"""


def test_a_fenced_comment_does_not_end_the_section() -> None:
    """The discriminating case. A fence-blind bound stops at the `# this comment`
    line and returns a section that ends before `after the block`."""
    alpha = titled_section(FIXTURE, "Alpha")
    assert "before the block" in alpha
    assert "after the block" in alpha, "the bound stopped inside a fenced block"


def test_a_section_owns_its_subsections() -> None:
    alpha = titled_section(FIXTURE, "Alpha")
    assert "still inside Alpha" in alpha


def test_the_section_stops_at_the_next_same_level_heading() -> None:
    alpha = titled_section(FIXTURE, "Alpha")
    assert "not Alpha" not in alpha


def test_a_missing_heading_fails_loudly() -> None:
    """Returning '' would make every later assertion vacuous."""
    with pytest.raises(AssertionError):
        titled_section(FIXTURE, "Gamma")


def test_section_from_bounds_an_offset_anchored_pin() -> None:
    body = section_from(FIXTURE, FIXTURE.index("before the block"))
    assert "after the block" in body and "still inside Alpha" in body
    assert "not Alpha" not in body


# --- the regression that produced this module, pinned on the REAL file --------


def test_the_live_phase5_section_extends_past_its_fenced_blocks() -> None:
    """Measured 2026-09-01: a fence-blind bound ended this section 24,270
    characters early, so three tests in `test_h_mad_wire_registry.py` were reading
    roughly two thirds of what they believed they covered.

    Pinned against the committed document rather than a fixture, because a
    fixture written from the tight case is green on the bug — the same reason
    `docs/skill-candidates.md` carries `pin-a-doc-lint-against-the-real-file`.
    """
    text = SKILL_MD.read_text(encoding="utf-8")
    phase5 = titled_section(text, "Phase 5 (Implementation) sub-steps")
    assert "```" in phase5, "the section must still contain the fenced blocks"
    # A landmark from the far end of the section: present only if the bound did
    # not stop at the first fenced `#` comment.
    assert "Dispatch channels and their guarantees" in phase5, (
        "the Phase 5 section was truncated at a fenced comment: "
        f"{len(phase5)} chars extracted"
    )


def test_docsections_delegates_to_the_authoritative_bounder() -> None:
    """Pin the shared import and both callers, including start/level propagation."""
    import importlib
    import json
    import os
    import subprocess
    import sys
    import types

    import docsections

    env = {k: v for k, v in os.environ.items() if not k.startswith("HMAD_STUB_")}
    env["HMAD_STUB_HOSTILE"] = "all"
    result = subprocess.run(
        ["bash", str(Path(__file__).with_name("stubs") / "orca"), "worktree", "set"],
        env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)["result"]["worktree"]["comment"]
    heading = "Section " + payload.splitlines()[0]
    text = f"## {heading}\n```\n# not a heading\n{payload}\n```\nanchor\n## Next\n"
    calls = []
    # Sentinel results deliberately differ from the real heading/boundary. This
    # proves propagation, not just that both callee names were mentioned.
    start, level, end = text.index("anchor"), 4, text.index("## Next")

    def rec_find(document, requested):
        calls.append(("find_heading", document, requested))
        return start, level

    def rec_end(document, offset, requested_level):
        calls.append(("fence_aware_end", document, offset, requested_level))
        return end

    fake = types.ModuleType("h_mad_doc_block_exec")
    fake.find_heading = rec_find
    fake.fence_aware_end = rec_end
    saved = sys.modules.get(fake.__name__)
    saved_path = sys.path[:]
    sys.modules[fake.__name__] = fake
    try:
        importlib.reload(docsections)
        titled = docsections.titled_section(text, heading)
        offset = text.index("not a heading")
        anchored = docsections.section_from(text, offset, 3)
    finally:
        if saved is None:
            sys.modules.pop(fake.__name__, None)
        else:
            sys.modules[fake.__name__] = saved
        try:
            importlib.reload(docsections)
        finally:
            sys.path[:] = saved_path

    assert [c[0] for c in calls] == [
        "find_heading", "fence_aware_end", "fence_aware_end"
    ], f"docsections did not delegate both the section start and its end: {calls!r}"
    assert calls == [
        ("find_heading", text, heading),
        ("fence_aware_end", text, start, level),
        ("fence_aware_end", text, offset, 3),
    ], "docsections must propagate the returned start/level and its own offset"
    assert titled == text[start:end], "titled_section must use both callee results"
    assert anchored == text[offset:end], "section_from must use the callee boundary"
