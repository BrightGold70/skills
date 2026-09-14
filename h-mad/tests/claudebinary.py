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


def blob() -> str:
    """The binary decoded as lossy UTF-8, or a SKIP carrying the reason.

    Never returns an empty string on failure: an empty blob would make every
    `assert X in blob` fail and every `assert X not in blob` pass, which is the
    fail-open direction for exactly the negative assertions this is used for.
    """
    binary = claude_binary()
    if binary is None:
        pytest.skip("claude binary not found -- cannot verify, and will not pass")
    try:
        return binary.read_bytes().decode("utf-8", "replace")
    except OSError as exc:  # pragma: no cover - depends on the host
        pytest.skip(f"claude binary unreadable ({exc}) -- cannot verify")
