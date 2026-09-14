"""No renderer-substituted argument token may appear in this repo's OWN skill bodies.

## What the renderer actually does

Decoded from the installed Claude Code binary (2.1.270), the slash-command
argument expander matches exactly one alternation:

    \\$ARGUMENTS\\[\\d+\\]|\\$ARGUMENTS|\\$\\d+(?!\\w)

Three alternatives: an indexed `$ARGUMENTS[n]`, a bare `$ARGUMENTS`, and `$`
followed by digits not continuing into a word. Nothing else.

## Why a match in the BODY is a defect here specifically

The regex is not only a substituter, it is a MODE SWITCH, and both `handoff` and
`h-mad` route on the mode it does not take. Observed directly in a live session
on 2026-09-14, comparing three skill bodies as they arrived:

  * `/loop` -- body contains a placeholder -> the argument was spliced INLINE at
    the placeholder, and no trailer was appended.
  * `/handoff read` and `/caveman ultra` -- body contains no placeholder -> the
    body arrived unchanged with `ARGUMENTS: read` / `ARGUMENTS: ultra` appended
    as a trailing line.

`handoff/SKILL.md` parses its mode (`read` / `takeover` / flags) off that
trailer, and `h-mad/SKILL.md` its verb (`do` / `status` / `reset`). So a single
stray `$1` or `$ARGUMENTS` anywhere in either body does not merely corrupt the
line it sits on -- it flips the renderer to inline mode, the trailer is never
appended, and the mode routing silently reads no arguments at all. The failure is
total and it is invisible in the file on disk.

## The measured incident

`$0` inside the INDEX-cleanup snippet in `handoff/SKILL.md` was measured twice
arriving as `...": "read}` under `/handoff read` and `...": "takeover}` under
`/handoff takeover`, while the file on disk held `$0`. That is the empirical
anchor; the decoded regex above is its corroboration, and `$0` is exactly what
`\\$\\d+(?!\\w)` predicts.

## The `$@` / `$*` negative -- measured, so it does not resurface

A backlog row proposed "close the `$@`/`$*` half of the positional-arg lint".
**The premise is false and this is where that is recorded.** The expander's
alternation contains no `@` and no `*`, and a census of the whole 2.1.270 image
on 2026-09-14 found `\\$\\*` zero times and `\\$@` five times, every one of them
inside a syntax-HIGHLIGHTING grammar for C#/F# verbatim interpolated strings
(`$@"`), not an argument handler. `h-mad/SKILL.md` documents `main "$@"; exit $?`
and that line is SAFE -- linting it would have been a change made against the
tool's actual behaviour.

## Scope

This repo's own authored bodies only. The ~300 vendored skills use `$ARGUMENTS`
deliberately and correctly; linting them would be a false positive per file.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import claudebinary

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The expander, transcribed from the binary. `test_the_regex_is_still_the_one_
#: the_binary_ships` re-derives it on every run so this cannot go stale silently.
RENDERER_ARG_SOURCE = r"\$ARGUMENTS\[\d+\]|\$ARGUMENTS|\$\d+(?!\w)"
RENDERER_ARG_RE = re.compile(RENDERER_ARG_SOURCE)

#: The bodies this repo authors and routes on. Not the vendored ones.
OWN_SKILL_BODIES = (
    REPO_ROOT / "handoff" / "SKILL.md",
    REPO_ROOT / "h-mad" / "SKILL.md",
)


def renderer_arg_hits(text: str) -> list[tuple[int, str, str]]:
    """Every token the renderer would substitute, as `(line, token, line text)`."""
    lines = text.splitlines()
    out = []
    for m in RENDERER_ARG_RE.finditer(text):
        ln = text.count("\n", 0, m.start()) + 1
        out.append((ln, m.group(0), lines[ln - 1].strip()[:120]))
    return out


class TestTheLintIsCalibrated:
    """Calibrate against strings that MUST fire before trusting a clean body.

    The lint this replaces was written after the offending `$0` had already been
    removed, so it had never once fired -- a detector whose only evidence is that
    it is quiet on a file already known to be clean is not evidence at all.
    """

    @pytest.mark.parametrize(
        "sample",
        ["$0", "$1", "$9", "$12", "$ARGUMENTS", "$ARGUMENTS[0]", "$ARGUMENTS[27]",
         'echo "$1"', "python3 - $2 <<'EOF'",
         # The alternation is ASYMMETRIC and this row is why it is listed:
         # `\\$\\d+` carries `(?!\\w)` and `\\$ARGUMENTS` carries nothing, so
         # `$ARGUMENTSX` IS rewritten (to `<args>X`) while `$1abc` is not. This
         # entry was first written into the must-NOT-fire list below from the
         # obvious symmetric guess, and the calibration pass refuted it.
         "$ARGUMENTSX"],
    )
    def test_it_fires_on_what_the_renderer_rewrites(self, sample: str) -> None:
        assert RENDERER_ARG_RE.search(sample), f"lint blind to {sample!r}"

    def test_the_two_alternatives_guard_word_boundaries_differently(self) -> None:
        """Pinned as a property, not just as two rows that happen to differ."""
        assert RENDERER_ARG_RE.search("$ARGUMENTSX"), "a word-boundary guard appeared on $ARGUMENTS"
        assert not RENDERER_ARG_RE.search("$1abc"), "the (?!\\w) guard on $<digits> is gone"

    @pytest.mark.parametrize(
        "sample",
        ['main "$@"; exit $?', "$*", "$@", "$?", "$!", "${HOME}", "$HOME",
         "$1abc", "${1:-x}", "RC=$?", 'HP="${CLAUDE_SKILLS_ROOT:-$HOME}"'],
    )
    def test_it_stays_silent_on_what_the_renderer_leaves_alone(self, sample: str) -> None:
        """A false positive here costs a real, correct line of documentation."""
        assert not RENDERER_ARG_RE.search(sample), f"lint over-fires on {sample!r}"

    def test_dollar_at_is_specifically_not_a_hit(self) -> None:
        """Pinned on its own because a backlog row asked for the opposite."""
        assert "@" not in RENDERER_ARG_SOURCE
        assert "*" not in RENDERER_ARG_SOURCE.replace(r"\[\d+\]", "")


class TestOurOwnSkillBodiesAreClean:
    @pytest.mark.parametrize("body", OWN_SKILL_BODIES, ids=lambda p: p.parent.name)
    def test_no_renderer_substituted_token_survives(self, body) -> None:
        assert body.is_file(), f"{body} is gone -- the lint would pass vacuously"
        hits = renderer_arg_hits(body.read_text(encoding="utf-8"))
        assert not hits, (
            f"{body.relative_to(REPO_ROOT)} contains tokens the slash-command "
            f"renderer rewrites, which also suppresses the `ARGUMENTS:` trailer "
            f"this skill routes on: {hits}"
        )

    def test_both_bodies_are_actually_covered(self) -> None:
        """The old lint read ONE file; that gap is the other half of this fix."""
        names = {b.parent.name for b in OWN_SKILL_BODIES}
        assert names == {"handoff", "h-mad"}


class TestAgainstTheLiveBinary:
    """Re-derive the expander rather than trusting the transcription above."""

    def test_the_blob_is_the_binary_not_an_empty_fallback(self) -> None:
        """The negative assertions below are only meaningful on a real read.

        `assert X not in blob` passes on an empty string, so a `blob()` that
        degraded to `""` instead of skipping would certify the `$*` negative
        against nothing at all. Asserting a floor is what makes the SKIP the only
        other outcome: verified, or declared unverifiable — never quietly clean.
        """
        assert len(claudebinary.blob()) > 10_000_000, (
            "the binary blob is too small to be the Claude Code image — a "
            "truncated or empty read would make every `not in blob` assertion "
            "pass vacuously"
        )

    def test_the_regex_is_still_the_one_the_binary_ships(self) -> None:
        blob = claudebinary.blob()
        assert RENDERER_ARG_SOURCE in blob, (
            "the slash-command argument regex is no longer in the binary verbatim "
            "-- re-decode it before trusting this lint's scope"
        )

    def test_the_binary_has_no_star_argument_handler(self) -> None:
        r"""`\$\*` appeared zero times in the whole 2.1.270 image."""
        blob = claudebinary.blob()
        assert r"\$\*" not in blob, (
            r"a `\$\*` regex now exists in the binary -- the $* negative recorded "
            "in this module's docstring may no longer hold; re-census before "
            "trusting it"
        )


class TestTheSharedConstantHelper:
    """`claudebinary.assert_constant` — the re-derivation shape, factored once.

    Two tests in this directory now re-derive a transcribed constant from the
    installed binary, and both used to carry their own `which` + `readlink` +
    decode. That is the shape that drifts: a fix to one locator leaves the other
    reading a binary that moved, and the ~208MB decode was being paid once per
    ASSERTION rather than once per session.
    """

    def test_it_confirms_a_constant_that_is_really_there(self) -> None:
        claudebinary.assert_constant(r"var \w+=(25000),", 25000)

    def test_an_int_and_its_string_spelling_both_pass(self) -> None:
        """`"25000" == 25000` is silently False, which would fail toward RED and
        get the whole re-derivation deleted as flaky."""
        claudebinary.assert_constant(r"var \w+=(25000),", "25000")

    def test_a_pattern_that_no_longer_matches_fails_loudly(self) -> None:
        with pytest.raises(AssertionError, match="no longer matches"):
            claudebinary.assert_constant(r"var \w+=(31337810),", 31337810)

    def test_a_changed_value_names_both_numbers(self) -> None:
        with pytest.raises(AssertionError, match="transcribed"):
            claudebinary.assert_constant(r"var \w+=(25000),", 24999)

    def test_the_blob_is_read_once_per_session(self) -> None:
        """The cache is the reason this helper exists at all."""
        claudebinary.blob()
        before = claudebinary._blob_or_error.cache_info()
        claudebinary.blob()
        after = claudebinary._blob_or_error.cache_info()
        assert after.hits > before.hits, "the binary is being re-read per call"
        assert after.misses == before.misses, "a second read happened"
