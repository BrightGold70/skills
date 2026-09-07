"""#153, generalised — every parsed-verdict prompt ends with its verdict line.

The agy template asked for "a final line" and then kept talking for three
paragraphs; three dispatches returned no `ASSESSMENT:` at all. The two codex
prompts had the same shape — the `STATUS:` fence sat ~28 lines from the end of one
and a whole `## Report file` section followed "end with exactly one line" in the
other — read by the same last-match extractor. The assembler substitutes slots in
place and appends nothing, so the template's tail IS the prompt's tail.
"""

from pathlib import Path

import pytest

REFS = Path(__file__).resolve().parents[1] / "references"

CASES = [
    ("agy-architectural-reviewer-prompt.md", "ASSESSMENT: <READY_TO_MERGE | WITH_FIXES | NO>"),
    ("codex-implementer-prompt.md", "STATUS: <DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT>"),
    ("codex-verifier-prompt.md", "STATUS: <DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT>"),
]


@pytest.mark.parametrize("name,verdict_line", CASES)
def test_the_verdict_fence_is_the_last_thing_in_the_template(name, verdict_line):
    tail = (REFS / name).read_text(encoding="utf-8").rstrip().splitlines()[-3:]
    assert tail == ["```", verdict_line, "```"], (name, tail)


@pytest.mark.parametrize("name,_", CASES)
def test_the_template_says_last_line_of_your_reply_and_nothing_after(name, _):
    text = (REFS / name).read_text(encoding="utf-8")
    assert "very last line of your reply" in text, name
    assert "nothing" in text and "after it" in text, name
    assert "no code fence around it" in text, name


@pytest.mark.parametrize("name,_", CASES)
def test_no_heading_follows_the_last_line_section(name, _):
    text = (REFS / name).read_text(encoding="utf-8")
    marker = "## Report Format" if "agy" in name else "## The last line"
    after = text.split(marker, 1)[1]
    assert "\n## " not in after and "\n### " not in after, (name, "a section follows the verdict")
