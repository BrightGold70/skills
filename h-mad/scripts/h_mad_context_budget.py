#!/usr/bin/env python3
"""Price an `advisor()` call before making it, from the orchestrator's own transcript.

`advisor()` forwards the WHOLE conversation to a second model and bills it into the
same turn's input, so the turn costs ~2x the current context. Nothing at the call
site shows that: the visible payload is ~4KB of advice. The cost scales with session
age, which makes the identical call free in Phase 1 and fatal in Phase 6 -- and Phase
6 is exactly where the tool's own "call before declaring done" guidance points.

This emits a `CTXBUDGET:` token so the decision is mechanical rather than a vibe.

Three ways a naive version of this reads the wrong number, all of which fail toward
a FALSE OK (the direction that ends a run):

  1. summing across turns. `cache_read_input_tokens` is the whole prompt replayed
     each turn, not a delta -- adding turns up inflates by ~the turn count. Take the
     LAST assistant turn only.
  2. counting `output_tokens` as context. It is not part of the forwarded prompt
     accounting we care about here; the input triple is.
  3. reading a SUBAGENT's usage. Subagent turns are written into the same JSONL with
     `isSidechain: true`, and a subagent's context is a fraction of the parent's, so
     the newest usage line can report 8k while the orchestrator sits at 500k. Skip
     sidechain lines.

The number is a FLOOR, not the live value: the last recorded usage predates the
current turn's own growth (tool results already in flight are not in it). Treat the
ceiling as a margin over a floor, which is why it is 45 and not 50.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_WINDOW = 1_000_000
DEFAULT_CEILING = 45.0
# The RUN ceiling is a different question from the advisor ceiling and deliberately
# not derived from it. 45 is a margin under 50 because advisor forwards a second full
# copy; 80 asks "is this session about to die mid-phase", where the remedy is to halt
# and hand off while stopping is still cheap. An overflow mid-phase is unrecoverable,
# and compacting afterwards recovers nothing.
RUN_CEILING = 80.0
# advisor forwards one extra full copy; measured 2.00-2.03x on session 97490faf.
ADVISOR_MULTIPLIER = 2.0


def _project_dir(cwd: Path) -> Path:
    """Claude Code stores transcripts under a slug of the absolute cwd."""
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(cwd))
    return Path.home() / ".claude" / "projects" / slug


def resolve_transcript(explicit: str | None, cwd: Path) -> Path | None:
    """Find THIS session's JSONL, in descending order of certainty.

    The session id is preferred over any path-derived guess for two reasons, both
    of which bit the first version of this script:

      * the cwd slug is the SESSION's project root, not the process's cwd. Run from
        `<repo>/h-mad` (or any subdirectory, or a linked worktree) the slug names a
        directory that does not exist, and the tool reports `UNKNOWN` forever --
        safe, but useless by default, which is how a check stops being run;
      * newest-mtime picks the most recently WRITTEN session in the project, which
        is not necessarily yours. With two Claude sessions open on one repo, that
        silently measures the other one -- and a fresh sibling session reads small,
        so the failure is toward a false OK.

    The slug walk survives only as the last resort for a session id that is not
    exported (older CLIs, a subprocess that dropped the environment).
    """
    if explicit:
        p = Path(explicit).expanduser()
        return p if p.is_file() else None
    env = os.environ.get("CLAUDE_TRANSCRIPT_PATH")
    if env and Path(env).is_file():
        return Path(env)

    session = os.environ.get("CLAUDE_CODE_SESSION_ID", "").strip()
    # A session id is a path component here; refuse anything that could escape.
    if session and not set(session) - set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"):
        hits = glob.glob(str(Path.home() / ".claude" / "projects" / "*" / f"{session}.jsonl"))
        if hits:
            return Path(max(hits, key=os.path.getmtime))

    cwd = cwd.resolve() if cwd.is_absolute() else Path(os.getcwd(), cwd).resolve()
    for candidate in (cwd, *cwd.parents):
        d = _project_dir(candidate)
        if not d.is_dir():
            continue
        files = glob.glob(str(d / "*.jsonl"))
        if files:
            return Path(max(files, key=os.path.getmtime))
    return None


def last_context_tokens(transcript: Path) -> int | None:
    """Input triple of the newest NON-sidechain assistant turn, or None."""
    found = None
    try:
        with transcript.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    obj = json.loads(line)
                except (ValueError, TypeError):
                    continue
                if not isinstance(obj, dict) or obj.get("isSidechain"):
                    continue
                msg = obj.get("message")
                usage = msg.get("usage") if isinstance(msg, dict) else None
                if not isinstance(usage, dict):
                    continue
                total = 0
                for key in (
                    "input_tokens",
                    "cache_creation_input_tokens",
                    "cache_read_input_tokens",
                ):
                    val = usage.get(key)
                    if isinstance(val, (int, float)):
                        total += int(val)
                if total > 0:
                    found = total
    except OSError:
        return None
    return found


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--transcript", help="session JSONL (default: newest for cwd)")
    ap.add_argument("--cwd", default=os.getcwd(), help="project dir used to find it")
    ap.add_argument(
        "--window",
        type=int,
        default=int(os.environ.get("HMAD_CONTEXT_WINDOW", DEFAULT_WINDOW)),
    )
    ap.add_argument(
        "--mode",
        choices=("advisor", "run"),
        default="advisor",
        help="advisor: price an advisor() call (default). run: price the RUN itself.",
    )
    # Resolved after parsing so the default can depend on --mode while an explicit
    # --ceiling still wins in either mode.
    ap.add_argument("--ceiling", type=float, default=None)
    args = ap.parse_args(argv)
    ceiling = args.ceiling
    if ceiling is None:
        ceiling = RUN_CEILING if args.mode == "run" else DEFAULT_CEILING

    if args.window <= 0:
        print("ERROR: --window must be positive", file=sys.stderr)
        print("CTXBUDGET: UNKNOWN reason=bad_window")
        return 2

    transcript = resolve_transcript(args.transcript, Path(args.cwd))
    if transcript is None:
        print("ERROR: no readable session transcript", file=sys.stderr)
        print("CTXBUDGET: UNKNOWN reason=no_transcript")
        return 2

    used = last_context_tokens(transcript)
    if used is None:
        print(f"ERROR: no usage record in {transcript}", file=sys.stderr)
        print("CTXBUDGET: UNKNOWN reason=no_usage")
        return 2

    pct = used * 100.0 / args.window
    if args.mode == "run":
        # HALT, not DENY. `hooks/h-mad-advisor-warn.sh` speaks on the glob
        # `*"CTXBUDGET: DENY"*`, so reusing that word would make a run-ceiling breach
        # indistinguishable from an advisor refusal to every existing consumer -- and
        # they prescribe different actions. `projected` is omitted for the same
        # reason: it is `used * 2` because advisor forwards a copy, and a run cap
        # forwards nothing, so printing it would invite exactly that conflation.
        verdict = "OK" if pct <= ceiling else "HALT"
        print(
            f"CTXBUDGET: {verdict} mode=run used={used} window={args.window} "
            f"pct={pct:.1f} ceiling={ceiling:g}"
        )
        return 0

    projected = int(used * ADVISOR_MULTIPLIER)
    verdict = "OK" if pct <= ceiling else "DENY"
    print(
        f"CTXBUDGET: {verdict} used={used} window={args.window} "
        f"pct={pct:.1f} projected={projected} ceiling={ceiling:g}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
