"""Every token the oracle can return must be CLASSIFIED by HANDOVER Step 2.

The skill routes ownership decisions on `h_mad_resume_decision.py`'s answer, and its
list of safe tokens is deliberately CLOSED: anything unlisted must STOP the caller.
A closed list is only as good as its membership, and nothing checked the membership.

`complete` was missing for the life of the file. The oracle returns it whenever
`last_completed_phase >= 7`, so a feature that had simply *finished* fell through to
the `anything else` branch and halted HANDOVER and TAKEOVER outright. That is the
inverse of the failure the closed list was built for — not a stale token read as
permission, but a live token read as danger, firing on the work most likely to be
ready to move. Found by a resume on 2026-09-14, by reading both sides; no test could
have reported it, because no test read the oracle at all.

So the guard here is a CROSS-FILE one. Asserting that the prose mentions `complete`
would pass on a copy of today's text and go stale the next time the oracle grows a
token — the precise decay that produced this bug. Instead the oracle's own source is
the corpus: every `return "<token>"` it can emit must appear, classified, in the
skill. A new token added there fails this test until the skill says what to do with it.

The second guard pins the REASON. `complete` is safe only because `_owned_elsewhere`
is evaluated before every `complete` return, so the token is unreachable while a live
session holds the feature. Move that check below the phase checks and `complete`
silently becomes the fail-open the closed list exists to prevent, while the skill goes
on calling it safe. The ordering is load-bearing, so it is pinned rather than trusted.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "handoff" / "SKILL.md"
ORACLE = REPO / "h-mad" / "scripts" / "h_mad_resume_decision.py"


def _norm(text: str) -> str:
    """Collapse whitespace so a markdown reflow cannot break a literal."""
    return " ".join(text.split())


BODY = SKILL.read_text(encoding="utf-8")
FLAT = _norm(BODY)
ORACLE_SRC = ORACLE.read_text(encoding="utf-8")


def _oracle_tokens() -> set[str]:
    """Every token `decide()` can return, read from the oracle's own source.

    Read from `return "..."` literals rather than from a list in this file: a
    hand-kept copy is what went stale in the skill, and duplicating it here would
    reproduce that defect one directory over.
    """
    return set(re.findall(r'return\s+"([a-z_]+)"', ORACLE_SRC))


class TestTheOracleIsReadable:
    """Fail LOUDLY rather than vacuously if the corpus moves.

    An empty token set would make every assertion below pass while checking
    nothing — the same "could not read" / "found nothing" collapse the skill
    warns about everywhere else.
    """

    def test_the_oracle_exists(self) -> None:
        assert ORACLE.is_file(), f"oracle not at {ORACLE} — this test checks nothing"

    def test_tokens_were_actually_extracted(self) -> None:
        tokens = _oracle_tokens()
        assert len(tokens) >= 5, f"extracted only {tokens!r} — the return-literal scan broke"

    def test_the_known_tokens_are_among_them(self) -> None:
        """Pins the extractor against the tokens the oracle documents at its top."""
        assert {"start_fresh", "resume_manual", "enter_autonomous", "halted", "complete",
                "owned_elsewhere", "cannot_judge"} <= _oracle_tokens()


class TestEveryTokenIsClassified:
    def test_no_token_is_unmentioned_by_the_skill(self) -> None:
        missing = sorted(t for t in _oracle_tokens() if f"`{t}`" not in FLAT)
        assert not missing, (
            f"HANDOVER Step 2 classifies neither as safe nor as STOP: {missing}. "
            "An unlisted token takes the `anything else` branch and halts the caller, "
            "which is correct for an UNKNOWN token and wrong for one the oracle "
            "documents. Decide which bullet it belongs in."
        )

    def test_complete_is_on_the_safe_side(self) -> None:
        """The specific regression: `complete` must not be left to `anything else`."""
        safe = re.search(
            r"(?m)^- \*\*one of (.+?)\*\* → no live owner\. Safe to proceed\.", BODY
        )
        assert safe, "the safe-to-proceed bullet has been reworded — re-point this test"
        assert "`complete`" in safe.group(1), (
            "`complete` is not in the safe-to-proceed bullet, so a FINISHED feature "
            "halts HANDOVER and TAKEOVER"
        )

    def test_the_stop_tokens_stayed_stopping(self) -> None:
        """Guard the fix's blast radius: widening the safe set must not swallow these."""
        safe = re.search(
            r"(?m)^- \*\*one of (.+?)\*\* → no live owner\. Safe to proceed\.", BODY
        )
        assert safe
        for token in ("owned_elsewhere", "cannot_judge"):
            assert f"`{token}`" not in safe.group(1), (
                f"`{token}` was moved into the safe set; it must STOP the caller"
            )

    def test_the_list_is_still_closed(self) -> None:
        """The catch-all must remain fail-closed; the defect was membership, not the rule."""
        assert "This list is deliberately CLOSED" in FLAT
        assert "**anything else** → STOP and surface the token" in FLAT


class TestTheReasonIsPinnedNotJustAsserted:
    def test_liveness_is_checked_before_complete_is_returned(self) -> None:
        """`complete` is safe ONLY because it cannot be reached past a live owner."""
        owned = ORACLE_SRC.index('return "owned_elsewhere"')
        completes = [m.start() for m in re.finditer(r'return "complete"', ORACLE_SRC)]
        assert completes, "no `complete` return found — the extractor or oracle moved"
        assert all(owned < pos for pos in completes), (
            "a `complete` return now precedes the `owned_elsewhere` check, so `complete` "
            "can be returned for a feature a LIVE session holds. It is no longer safe to "
            "proceed on; move it back to the STOP bullets in handoff/SKILL.md."
        )

    def test_the_skill_states_that_reason(self) -> None:
        """An unexplained exception to a safety gate is the thing a later reader deletes."""
        assert "_owned_elsewhere" in FLAT and "before" in FLAT
