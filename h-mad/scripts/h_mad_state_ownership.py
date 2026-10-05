#!/usr/bin/env python3
"""h_mad_state_ownership.py — one answer to "is this feature's owner still live?".

The feature claim is advisory, and two components act on it: the resume router
(`h_mad_resume_decision.py`) decides whether to hand a feature to a new session,
and the writer (`h_mad_state_write.py --claim`) decides whether to let that
session record ownership. Read and write must agree, or the router authorises
work the writer then refuses.

They did not agree. The router treated a claim older than two hours as
abandoned; the writer had no staleness allowance at all, so a 19.6h-dead session
still blocked the claim and `--force` was the only way through (observed
2026-08-02). The cost is not the extra flag — it is what the flag came to mean.
`--force` is the verb for stealing a claim from a LIVE session, and routing the
routine "the previous session crashed" case through it trains an operator to
reach for it reflexively, wearing out the one guard that protects a live run.

This module is the single source of truth so the two cannot drift again. It is
deliberately tiny and stdlib-only: both callers are standalone scripts invoked
with a bare `python3`.

`liveness_evidence` sits beside the gate, not in it: the heartbeat-only rule
above still decides `--claim`, and the four-clock reading is what an operator
reads before forcing, releasing or calling a lane quiet (row 1406).
"""
from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Two hours. Long enough that an operator stepping away mid-phase does not lose
# the feature, short enough that a crashed session does not hold it overnight.
OWNERSHIP_STALE_AFTER_SECONDS = 2 * 60 * 60

# Set (to anything non-empty) and every host clock reader returns "could not
# read" without touching `ps`, `git` or the transcript store. It can only
# withhold evidence, so a reading under it is LIVE on a fresh heartbeat and
# UNKNOWN otherwise, never QUIET. The test suite sets it in conftest so no test
# reads the real host by accident; tests of the readers unset it.
CLOCKS_OFF_ENV = "H_MAD_LIVENESS_CLOCKS_OFF"

# Bound on each `ps`/`git` reader. Measured `ps` at 0.056 s; ten seconds stops a
# hung reader without misreading a slow one. Readers run outside the store lock.
READER_TIMEOUT_SECONDS = 10


def parse_ts(value) -> "datetime | None":
    """An ISO-8601 timestamp as an aware datetime, or None if unreadable.

    Naive input is read as UTC: every producer here stamps UTC, and guessing a
    local zone would silently shift a heartbeat across the staleness boundary.
    """
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def owner_is_live(heartbeat_ts, now: str | None = None) -> bool:
    """True when a claim stamped `heartbeat_ts` still counts as held.

    Fails CLOSED — an absent or unparseable heartbeat reads as live. "Held, with
    no evidence of when" is not evidence of abandonment, and the safe error is
    to leave a possibly-running session in possession rather than to hand its
    feature to a second one.

    The boundary is inclusive: age exactly equal to the window is still live, so
    a claim becomes stale only once it is strictly older.
    """
    heartbeat = parse_ts(heartbeat_ts)
    if heartbeat is None:
        return True
    reference = parse_ts(now) or datetime.now(timezone.utc)
    age = (reference - heartbeat).total_seconds()
    return age <= OWNERSHIP_STALE_AFTER_SECONDS


def liveness_evidence(record, lane, now: str | None = None, *, transcript_mtime=None,
                      commit_ts=None, ps_commands=None, minted_owner=None) -> str:
    """One `LIVENESS:` line for a claim, read from four clocks.

    Not four independent clocks: for a Claude owner the transcript also
    records its own beats and commits, so what the transcript cannot subsume
    is `ps` and other people's commits. That is harmless for an any-fresh
    disjunction, which only needs each clock to be a real sign of life.

    `owner_is_live` reads the heartbeat alone, and that one clock misread a
    working lane as dead four times (skill-candidates row
    "gate-on-two-independent-clocks"): cold for 92-153 min while the lane
    shipped three tasks, a day old while the owner's transcript was seconds
    old, and once cold enough that a `--force` claim collided with a live run.
    So this reads the heartbeat, the owner's transcript mtime, the lane's
    newest commit, and `ps` argv naming the owner session, each against the
    same window `owner_is_live` uses:

      * `LIVENESS: LIVE evidence=<clocks> heartbeat_age=Ns` — any clock fresh;
      * `LIVENESS: QUIET heartbeat_age=… transcript_age=… commit_age=… window=…`
        — every clock readable and cold;
      * `LIVENESS: UNKNOWN reason=<clocks>` — nothing fresh and some clock
        could not be read. Never QUIET on a partial read: that is the same
        fail-closed rule `owner_is_live` applies to a missing heartbeat.

    `ps` is positive-only. A session id is in argv only for resumed or
    explicit-id launches, so a match proves life and its absence proves
    nothing — it never contributes an age. It still counts as unreadable when
    `ps` itself fails, because then a live process could not have been seen.

    A Codex or agy owner's id is minted by h-mad into the lane's git dir
    (`h-mad-session-id.<feature>`), so it can never have a Claude transcript.
    For such an owner the transcript clock does not exist (`transcript_age=n/a`)
    rather than being unreadable, or a crashed Codex claim could never read
    QUIET. A Claude owner whose transcript is missing stays UNKNOWN.

    The four readers are injectable; by default they are this module's
    `read_transcript_mtime`, `read_commit_ts`, `read_ps_commands` and
    `read_minted_owner`, looked up at call time. `owner_is_live` and its callers
    are unchanged: this is the evidence an operator reads, not the gate
    `--claim` applies.
    """
    transcript_mtime = transcript_mtime or read_transcript_mtime
    commit_ts = commit_ts or read_commit_ts
    ps_commands = ps_commands or read_ps_commands
    minted_owner = minted_owner or read_minted_owner
    record = record if isinstance(record, dict) else {}
    owner = record.get("owner_session_id")
    owner = owner if isinstance(owner, str) and owner.strip() else None
    reference = (parse_ts(now) or datetime.now(timezone.utc)).timestamp()

    def age(epoch):
        return None if epoch is None else reference - epoch

    beat = parse_ts(record.get("owner_heartbeat_ts"))
    ages = {
        "transcript": age(transcript_mtime(owner)) if owner else None,
        "commit": age(commit_ts(lane)),
        "heartbeat": age(beat.timestamp()) if beat else None,
    }
    commands = ps_commands() if owner else None
    seen = commands is not None and any(_argv_names(command, owner) for command in commands)
    minted = bool(owner) and ages["transcript"] is None and minted_owner(lane, owner) is True

    def shown(seconds):
        return "unreadable" if seconds is None else f"{int(seconds)}s"

    window = OWNERSHIP_STALE_AFTER_SECONDS
    fresh = (["ps"] if seen else []) + [
        f"{clock}:{shown(seconds)}" for clock, seconds in ages.items()
        if seconds is not None and seconds <= window
    ]
    if fresh:
        return f"LIVENESS: LIVE evidence={','.join(fresh)} heartbeat_age={shown(ages['heartbeat'])}"
    unreadable = ["heartbeat"] if ages["heartbeat"] is None else []
    if not owner:
        unreadable.append("owner")
    elif ages["transcript"] is None and not minted:
        unreadable.append("transcript")
    if ages["commit"] is None:
        unreadable.append("commit")
    if owner and commands is None:
        unreadable.append("ps")
    if unreadable:
        return f"LIVENESS: UNKNOWN reason={','.join(unreadable)}"
    return (f"LIVENESS: QUIET heartbeat_age={shown(ages['heartbeat'])} "
            f"transcript_age={'n/a' if minted else shown(ages['transcript'])} "
            f"commit_age={shown(ages['commit'])} window={window}s")


def _argv_names(command: str, session_id: str) -> bool:
    """True when argv passes `session_id` as a session flag's value.

    `--resume ID`, `--resume=ID`, `-r ID` or `--session-id ID`, and the whole id,
    not a prefix of a longer one. A bare mention is not enough: the shell
    running this very check, a `grep` or a `tail -f` of the transcript all name
    the id, and each read a dead owner LIVE.
    """
    pattern = (r"(?<![\w-])(?:--resume|--session-id|-r)(?:=|\s+)"
               + re.escape(session_id) + r"(?![\w-])")
    return re.search(pattern, command) is not None


def _clocks_off() -> bool:
    return bool(os.environ.get(CLOCKS_OFF_ENV))


def read_transcript_mtime(session_id: str) -> "float | None":
    """Newest mtime of the session's transcripts, or None if none can be read.

    Under `<config>/projects/*/`: `<session_id>.jsonl` and its subagents'
    `<session_id>/subagents/*.jsonl` — an owner waiting on a long subagent
    writes only the latter. `<config>` is `$CLAUDE_CONFIG_DIR`, else
    `~/.claude`. An id that could escape the glob is refused, not expanded.
    """
    if _clocks_off():
        return None
    if not session_id or not re.fullmatch(r"[\w.-]+", session_id) or session_id.startswith("."):
        return None
    root = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "projects"
    try:
        mtimes = [path.stat().st_mtime
                  for pattern in (f"*/{session_id}.jsonl", f"*/{session_id}/subagents/*.jsonl")
                  for path in root.glob(pattern)]
    except OSError:
        return None
    return max(mtimes) if mtimes else None


def read_commit_ts(lane) -> "int | None":
    """Committer time of the newest non-merge commit touching the lane, or None.

    `git log -1 --no-merges -- .` run in the lane: a merge of main into the lane
    branch is not the owner working, and a lane nested in a larger repo must
    not inherit that repo's HEAD. A lane that IS a shared checkout still reads
    every session's commits; that clock is the lane's, not the owner's.
    """
    if _clocks_off():
        return None
    try:
        run = subprocess.run(["git", "-C", str(lane), "log", "-1", "--no-merges",
                              "--format=%ct", "--", "."],
                             capture_output=True, text=True, timeout=READER_TIMEOUT_SECONDS)
        return int(run.stdout.strip()) if run.returncode == 0 else None
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def read_ps_commands() -> "list[str] | None":
    """Every other process's command line (`ps -ww -eo pid,command`), or None."""
    if _clocks_off():
        return None
    try:
        run = subprocess.run(["ps", "-ww", "-eo", "pid,command"],
                             capture_output=True, text=True, timeout=READER_TIMEOUT_SECONDS)
    except (OSError, subprocess.SubprocessError):
        return None
    return parse_ps(run.stdout, os.getpid()) if run.returncode == 0 else None


def read_minted_owner(lane, session_id: str) -> bool:
    """True when the lane's git dir holds an `h-mad-session-id.*` naming `session_id`.

    That is how the Codex and agy runtimes mint an owner id (no host session id
    exists there). Anything unreadable is False, which keeps the transcript
    clock required — the fail-closed direction.
    """
    if _clocks_off():
        return False
    try:
        run = subprocess.run(["git", "-C", str(lane), "rev-parse", "--absolute-git-dir"],
                             capture_output=True, text=True, timeout=READER_TIMEOUT_SECONDS)
        if run.returncode != 0:
            return False
        for path in Path(run.stdout.strip()).glob("h-mad-session-id.*"):
            if path.read_text(encoding="utf-8").strip() == session_id:
                return True
    except (OSError, subprocess.SubprocessError, UnicodeDecodeError):
        return False
    return False


def parse_ps(text: str, own_pid: int) -> "list[str]":
    """Commands from `ps -eo pid,command` output, minus the header and `own_pid`."""
    commands = []
    for line in text.splitlines()[1:]:
        pid, _, command = line.strip().partition(" ")
        if pid.isdigit() and int(pid) != own_pid:
            commands.append(command.strip())
    return commands
