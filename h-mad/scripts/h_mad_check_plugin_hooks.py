#!/usr/bin/env python3
"""Replay Claude Code's own `hooks.json` key validator, offline.

Why this exists at all: the warning it reproduces is rendered once, at session
start, in the TUI. There is no command that re-renders it and no log that keeps
it, so "did the patch work?" was answerable only by restarting Claude Code and
watching. That makes the check un-runnable from inside a session, un-runnable in
CI, and impossible to run as a *negative control* — which is the run that
matters, because a clean result from a check that silently does nothing looks
exactly like a clean result from a check that works.

Replaying the validator turns a visual, once-per-session, un-scriptable signal
into a function over a file. `findings()` builds the same list Claude Code's
emitter builds; an EMPTY list is the whole point — that is the emitter's early
return, and an early return is why no warning appears.

The constants are transcribed from the 2.1.270 binary (the minified names are
per-build and are recorded only to make the transcription auditable):

    yko = new Set(["description","hooks","modules","surface"])   # top level
    _ko = new Set(["matcher","hooks"])                           # matcher level
    bko = 5    (max keys listed before "and N more")
    npn = 40   (key-name truncation)

`tests/test_h_mad_check_plugin_hooks.py` re-greps the live binary for the two
SET CONTENTS on every run and fails when they drift, so this docstring is not
the thing being trusted. If the binary cannot be found the test SKIPS rather
than passes: "I could not check" and "the check said yes" must not be spelled
the same way.

Usage:
    h_mad_check_plugin_hooks.py <label>=<path> [<label>=<path> ...]

Exit 0 when every named file is CLEAN or ABSENT, 1 when any is WARN or
UNREADABLE. UNREADABLE is deliberately NOT clean — a file that will not parse
is the absence of evidence, not evidence of absence.
"""
from __future__ import annotations

import json
import pathlib
import sys

TOP = {"description", "hooks", "modules", "surface"}
MATCHER = {"matcher", "hooks"}
MAXKEYS, TRUNC = 5, 40


def _truncate(key: str) -> str:
    """`opn` — long key names are elided, and the ellipsis is part of the text."""
    return key if len(key) <= TRUNC else key[:TRUNC] + "..."


def _quote(key: str) -> str:
    return f'"{_truncate(key)}"'


def findings(cfg: object) -> list[str]:
    """The exact list the emitter builds. An empty list means NO warning."""
    if not isinstance(cfg, dict):
        return []
    out = [_quote(k) for k in cfg.keys() if k not in TOP]
    hooks = cfg.get("hooks")
    if isinstance(hooks, dict):
        for event, arr in hooks.items():
            if not isinstance(arr, list):
                continue
            for i, matcher in enumerate(arr):
                if not isinstance(matcher, dict):
                    continue
                site = f"hooks.{_truncate(event)}[{i}]"
                out += [
                    f"{_quote(k)} in {site}" for k in matcher.keys() if k not in MATCHER
                ]
    return out


def message(found: list[str]) -> str | None:
    """The rendered line, or None for the emitter's early return."""
    if not found:
        return None
    shown = found[:MAXKEYS]
    more = len(found) - len(shown)
    plural = "key" if len(found) == 1 else "keys"
    tail = f" and {more} more" if more > 0 else ""
    return f"hooks.json: unknown {plural} {', '.join(shown)}{tail} ignored"


def check(path: str | pathlib.Path, label: str) -> tuple[str, str, str | None]:
    p = pathlib.Path(path)
    if not p.is_file():
        return ("ABSENT", label, None)
    try:
        cfg = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:  # unreadable is NOT clean
        return ("UNREADABLE", label, str(exc))
    rendered = message(findings(cfg))
    return ("WARN" if rendered else "CLEAN", label, rendered)


def main(argv: list[str]) -> int:
    if not argv:
        print(
            "usage: h_mad_check_plugin_hooks.py <label>=<path> [...]", file=sys.stderr
        )
        return 2
    worst = 0
    for arg in argv:
        if "=" not in arg:
            print(f"bad argument (want <label>=<path>): {arg}", file=sys.stderr)
            return 2
        label, path = arg.split("=", 1)
        state, lab, msg = check(path, label)
        print(f"{state:<10} {lab}")
        if msg:
            print(f"           -> Plugin {lab}: {msg}")
        if state in ("WARN", "UNREADABLE"):
            worst = 1
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
