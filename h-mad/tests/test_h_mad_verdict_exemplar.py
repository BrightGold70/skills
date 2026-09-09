"""The verdict exemplar a parsed-verdict prompt shows must be COPYABLE.

#153 fixed the verdict's POSITION — the line is now the last thing in each
template — and left its FORM alone. `test_h_mad_prompt_tails.py` then froze the
broken form as an assertion:

    assert tail == ["```", "ASSESSMENT: <READY_TO_MERGE | WITH_FIXES | NO>", "```"]

Two defects are pinned by that one line.

1. **The exemplar is a schema, not a literal.** `<A | B | C>` has to be
   TRANSFORMED before it can be emitted, and `<...>` is the same grammar the very
   same file uses for orchestrator-filled slots (`<INLINE_FEATURE>`,
   `<INLINE_BASE_SHA>`). So the one place the template shows the line it wants
   reads as a slot somebody else fills in.
2. **The exemplar is fenced, three lines under prose forbidding a fence.** The
   template says "no code fence around it" and then shows its only example inside
   one.

Measured, `#18 gateway-consolidation` 6a-prime, 2026-09-09, two consecutive
dispatches of the staged prompt:

    c1  EVIDENCE: PASS tools=11 ok=11 failed=0 thinking=5119   no ASSESSMENT line
    c2  EVIDENCE: PASS tools=19 ok=19 failed=0 thinking=7270   no ASSESSMENT line

Both read the tree and both wrote, near the TOP of the reply:

    **Assessment**: YES, with minor non-blocking architectural drift in the test suite.

`YES` is not one of the three words, it was not alone on its line, and it was not
last. `h_mad_archreview_cycle.py score` returned `ARCHREVIEW: NO_VERDICT` both
times and recorded nothing, which is correct and which cost two full cycles.
SKILL.md already records three earlier dispatches omitting this line; these are
four and five.

**Scope — agy only, deliberately.** The two codex templates share the shape and
are NOT changed here: codex emits its `STATUS:` line reliably in this repo's
record, and rewriting a prompt that demonstrably works, on the theory that it
shares a shape with one that does not, is the failure this repo documents
elsewhere. The shape is recorded as a monitoring row instead.

**Residual, stated exactly.** A copyable exemplar does not make an agent emit it.
This pins what the TEMPLATE contains; the enforcement that a reply actually
carries the line remains `h_mad_archreview_cycle.py score`, which already fails
closed. This test cannot detect a model that ignores a perfectly-formed exemplar.
"""

from pathlib import Path

REFS = Path(__file__).resolve().parents[1] / "references"
AGY = "agy-architectural-reviewer-prompt.md"
ALLOWED = ("READY_TO_MERGE", "WITH_FIXES", "NO")


def _text() -> str:
    return (REFS / AGY).read_text(encoding="utf-8")


def _tail_lines() -> list[str]:
    return _text().rstrip().splitlines()


def test_the_last_line_is_a_literal_verdict_not_a_schema():
    """The final line must be emittable verbatim, with no transformation."""
    last = _tail_lines()[-1]
    assert last.startswith("ASSESSMENT: "), last
    word = last[len("ASSESSMENT: ") :].strip()
    assert word in ALLOWED, (
        f"the template's final line is {last!r}; a reviewer cannot copy that. "
        f"It must end in one of {ALLOWED}."
    )


def test_the_final_exemplar_is_not_inside_a_code_fence():
    """The prose forbids a fence; the example must not contradict it."""
    tail = _tail_lines()
    assert tail[-1] != "```", "the template ends on a fence, not on the verdict"
    # walk back over the exemplar block and confirm no fence opened it
    assert "```\nASSESSMENT:" not in _text(), (
        "the verdict exemplar is wrapped in a code fence, three lines below prose "
        "that says 'no code fence around it'"
    )


def test_no_angle_bracket_schema_form_of_the_verdict_survives():
    """`<A | B | C>` collides with the file's own `<INLINE_*>` slot grammar."""
    text = _text()
    assert "ASSESSMENT: <" not in text, (
        "an angle-bracket verdict form remains; it reads as an orchestrator-filled "
        "slot like <INLINE_FEATURE>, not as text the reviewer writes"
    )


def test_every_allowed_word_appears_as_a_complete_copyable_line():
    """All three verdicts are shown in full, so none needs to be constructed."""
    lines = {ln.strip() for ln in _text().splitlines()}
    for word in ALLOWED:
        assert f"ASSESSMENT: {word}" in lines, (
            f"ASSESSMENT: {word} is never shown as a complete line of its own"
        )


def test_the_word_set_is_declared_closed_and_the_observed_wrong_words_are_named():
    """A literal exemplar was not enough on its own — measured.

    With the three literals in place, the next dispatch DID emit the token and
    still invented its word: `DRIFTED`, under a markdown heading marker, borrowed
    from the 5e spec reviewer's `VERDICT: COMPLIANT | DRIFT` contract. Showing the
    right answer does not preclude writing a different one, so the template also
    has to say the set is closed and name the words that were actually tried.

    Naming them is the part that dates: this pins that the closing happened, not
    that the list is exhaustive. A model can always invent a word nobody has seen,
    which is why `score` remains the enforcement.
    """
    text = _text()
    assert "CLOSED set" in text, "the template never says the three words are closed"
    for wrong in ("DRIFTED", "COMPLIANT", "YES"):
        assert wrong in text, f"the observed wrong word {wrong} is not named"
    assert "WITH_FIXES` — which is what every one of those refused replies was" in text, (
        "the template names wrong words without routing them to the right one"
    )


def test_the_position_guarantee_from_153_still_holds():
    """Regression guard: the verdict stays the last thing in the template.

    This is the property #153 shipped. It passed before this change and must
    keep passing after it — the fix here is to the exemplar's FORM, and a fix
    that moved the line would trade one defect for the other.
    """
    text = _text()
    after = text.split("## Report Format", 1)[1]
    assert "\n## " not in after and "\n### " not in after
    assert "very last line of your reply" in text
    assert "no code fence around it" in text
