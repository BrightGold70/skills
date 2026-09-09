"""#153, generalised — every parsed-verdict prompt ends with its verdict line.

The agy template asked for "a final line" and then kept talking for three
paragraphs; three dispatches returned no `ASSESSMENT:` at all — and two more did
after the position was fixed, because the FORM was not (see below). The two codex
prompts had the same shape — the `STATUS:` fence sat ~28 lines from the end of one
and a whole `## Report file` section followed "end with exactly one line" in the
other — read by the same last-match extractor. The assembler substitutes slots in
place and appends nothing, so the template's tail IS the prompt's tail.

2026-09-09: the agy case's expected tail CHANGED, and this test is why it had
to. #153 fixed the verdict's position and this file then pinned its FORM as
``["```", "ASSESSMENT: <A | B | C>", "```"]`` — a fenced schema, asserted three
lines under prose the same test requires to say "no code fence around it". Two
further dispatches died on it. So this assertion pinned the defect, and
adjusting it is the fix rather than a weakening; the replacement is stricter,
not looser. See tests/test_h_mad_verdict_exemplar.py.
"""

from pathlib import Path

import pytest

REFS = Path(__file__).resolve().parents[1] / "references"

# The expected TAIL of each template, as its final lines in order.
#
# agy ends on three LITERAL verdict lines with no fence; the two codex templates
# still end on the fenced schema. The asymmetry is deliberate and is not a
# half-finished migration. The fenced schema is MEASURED to fail on agy — five
# dispatches omitted the line, two of them on 2026-09-09 writing
# `**Assessment**: YES` after reading 11 and 19 files — and is NOT measured to
# fail on codex, which emits its STATUS line reliably in this repo's record.
# Rewriting a prompt that demonstrably works, because it shares a shape with one
# that does not, is the failure mode this repo documents elsewhere.
CASES = [
    (
        "agy-architectural-reviewer-prompt.md",
        ["ASSESSMENT: READY_TO_MERGE", "ASSESSMENT: WITH_FIXES", "ASSESSMENT: NO"],
    ),
    (
        "codex-implementer-prompt.md",
        ["```", "STATUS: <DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT>", "```"],
    ),
    (
        "codex-verifier-prompt.md",
        ["```", "STATUS: <DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT>", "```"],
    ),
]


@pytest.mark.parametrize("name,expected_tail", CASES)
def test_the_verdict_is_the_last_thing_in_the_template(name, expected_tail):
    tail = (REFS / name).read_text(encoding="utf-8").rstrip().splitlines()[-len(expected_tail) :]
    assert tail == expected_tail, (name, tail)


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
