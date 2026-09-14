"""Locate the installed Claude Code binary, once, for every test that reads it.

Two tests now re-derive a contract from the binary rather than trusting a
transcription of it: `test_h_mad_check_memory_index.py` (the memory-index caps)
and `test_skill_body_renderer_args.py` (the slash-command argument regex). They
had separate copies of the same four-line `which` + `readlink` dance, which is
exactly the shape that drifts: a fix to one locator leaves the other reading a
binary that moved.

The contract is fail-CLOSED and it is the whole point of the module. A binary
that cannot be found or cannot be read makes the caller SKIP with a reason --
never pass. "I could not check" and "the check said yes" lead to opposite correct
actions, so they must not produce the same test outcome.
"""

from __future__ import annotations

import functools
import re
import subprocess
from pathlib import Path

import pytest


def claude_binary() -> Path | None:
    """The resolved on-disk binary, or None when it cannot be located.

    `which claude` lands on a launcher shim (`~/.local/bin/claude`); the real
    208MB image is behind it, so the `readlink -f` is load-bearing rather than
    tidy -- reading the shim finds none of the strings these tests match on.
    """
    which = subprocess.run(["which", "claude"], capture_output=True, text=True)
    if which.returncode != 0 or not which.stdout.strip():
        return None
    resolved = subprocess.run(
        ["readlink", "-f", which.stdout.strip()], capture_output=True, text=True
    )
    target = (resolved.stdout.strip() if resolved.returncode == 0 else "") or which.stdout.strip()
    p = Path(target)
    return p if p.is_file() else None


@functools.lru_cache(maxsize=1)
def _blob_or_error() -> tuple[str | None, str | None]:
    """`(text, None)` on success, `(None, reason)` on failure. Cached per session.

    The cache is the point: the image is ~208MB and decoding it takes real time,
    so a suite with several constants to re-derive was paying that per ASSERTION.
    The failure is cached too -- a missing binary does not become findable by
    asking again, and re-running `which` per test only makes the skip slower.

    Returns a pair rather than raising so the cache holds an outcome instead of
    a `Skipped` exception; `blob()` is the one place that turns it into a skip.
    """
    binary = claude_binary()
    if binary is None:
        return None, "claude binary not found -- cannot verify, and will not pass"
    try:
        return binary.read_bytes().decode("utf-8", "replace"), None
    except OSError as exc:  # pragma: no cover - depends on the host
        return None, f"claude binary unreadable ({exc}) -- cannot verify"


def blob() -> str:
    """The binary decoded as lossy UTF-8, or a SKIP carrying the reason.

    Never returns an empty string on failure: an empty blob would make every
    `assert X in blob` fail and every `assert X not in blob` pass, which is the
    fail-open direction for exactly the negative assertions this is used for.
    """
    text, reason = _blob_or_error()
    if text is None:
        pytest.skip(reason)
    return text


def assert_constant(pattern: str, expected, group: int = 1) -> None:
    """Re-derive one transcribed constant from the binary, or SKIP saying why.

    Match on the VALUE in its declaring context, never on the minified name --
    `F2`, `hD`, `Ams` are regenerated every build, so pinning one goes red on a
    rename that changed nothing. Pass a pattern that contains the value and
    enough syntax around it to be unambiguous.

    `expected` is compared as a STRING against the captured group. A caller
    holding an int passes it directly and it is stringified here; comparing
    `"25000" == 25000` silently False is exactly the fail-toward-red that makes
    a re-derivation check get deleted as flaky.
    """
    m = re.search(pattern, blob())
    assert m, (
        f"pattern {pattern!r} no longer matches the installed binary -- the "
        f"constant it pins may have moved or changed; re-decode before trusting it"
    )
    got = m.group(group)
    assert got == str(expected), (
        f"the binary declares {got!r} where this repo has transcribed "
        f"{str(expected)!r} (pattern {pattern!r})"
    )
