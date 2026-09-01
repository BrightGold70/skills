#!/usr/bin/env python3
"""Check ONCE whether a handover was picked up. Not a watch.

HANDOVER §Step 5 already says the delivery receipt proves nothing about pickup:
`accepted: true, bytesWritten: <n>` is the write succeeding into a live pty, and
is non-zero into a pane that is wedged, mid-redraw, or running something else.
§Step 6 then says stop monitoring. Both are right, and together they leave a real
gap — *watching* a receiver is supervision and belongs to the `orchestration`
skill, but *asking once, later, whether they took it* is three read-only lookups
and a different question. This answers the second one and nothing more.

Pickup is only ever proven by something the RECEIVER produced:

  1. the feature's `owner_session_id` moved to a session that is not the sender
  2. the target worktree's comment flipped from `handover:` to `taken over:`

A third signal — the receiving pane's own output — is deliberately NOT
implemented. No wrapper verb reads an arbitrary terminal handle (`hmad-dispatch
read` resolves a PINNED agent through `_resolve_target`), and this skill does not
call `orca` directly. It is also the weakest of the three: a pane can echo a
prompt it never acted on. The missing verb is filed as the first half of the
`positive pane ID via terminal read` candidate.

Fail closed, in the direction that matters here: "I could not check" must never
render as "they did not take it", because the sender has already let go and a
false NOT_YET invites them to re-deliver work that is already in progress.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

TAKEN = "taken over:"
HANDED = "handover:"


def owner_signal(state_path: str, feature: str, sender: str) -> tuple[str, str]:
    """(verdict, detail) over the advisory claim. Verdicts: taken/not_yet/unknown."""
    p = Path(state_path)
    if not p.is_file():
        return "unknown", f"no state file at {state_path}"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return "unknown", f"state file unreadable ({exc.__class__.__name__})"
    record = (data.get("orchestrator_state") or {}).get(feature)
    if record is None:
        # The sender released and nobody created a record. That is a real answer:
        # nothing holds it. It is NOT "unknown" — the file was readable.
        return "not_yet", f"no record for {feature!r}: released, and unclaimed since"
    owner = record.get("owner_session_id")
    if not owner:
        return "not_yet", f"{feature} has no owner (released, still unclaimed)"
    if owner == sender:
        return "not_yet", f"{feature} is still owned by the sender ({sender})"
    return "taken", f"{feature} is owned by {owner} (heartbeat {record.get('owner_heartbeat_ts')})"


def comment_signal(worktree_path: str | None, dispatch: str) -> tuple[str, str]:
    """(verdict, detail) over the target worktree's checkpoint stamp."""
    if not worktree_path:
        return "unknown", "no --worktree-path given"
    if shutil.which(dispatch) is None and not Path(dispatch).is_file():
        return "unknown", f"{dispatch} not on PATH (no Orca runtime here)"
    try:
        out = subprocess.run([dispatch, "worktree-ps"], capture_output=True,
                             text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        return "unknown", f"worktree-ps failed ({exc.__class__.__name__})"
    if out.returncode != 0:
        return "unknown", f"worktree-ps exited {out.returncode}"
    try:
        payload = json.loads(out.stdout)
    except json.JSONDecodeError:
        return "unknown", "worktree-ps output was not JSON"
    if "worktrees" not in payload:
        # Asserted, never `.get(..., [])`: a wrong key and an empty list are the
        # same value and opposite answers.
        return "unknown", "worktree-ps payload has no `worktrees` container"
    target = worktree_path.rstrip("/")
    for w in payload["worktrees"]:
        if (w.get("path") or "").rstrip("/") == target:
            comment = w.get("comment") or ""
            if comment.startswith(TAKEN):
                return "taken", f"comment reads {comment[:80]!r}"
            if comment.startswith(HANDED):
                return "not_yet", "comment still carries the sender's `handover:` stamp"
            return "not_yet", f"comment does not say taken over: {comment[:60]!r}"
    return "unknown", f"no worktree at {worktree_path} in worktree-ps"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--state", required=True)
    ap.add_argument("--feature", required=True)
    ap.add_argument("--sender-session", required=True)
    ap.add_argument("--worktree-path")
    ap.add_argument("--hmad-dispatch", default="hmad-dispatch")
    a = ap.parse_args(argv)

    owner_v, owner_d = owner_signal(a.state, a.feature, a.sender_session)
    comment_v, comment_d = comment_signal(a.worktree_path, a.hmad_dispatch)
    print(f"  claim:   {owner_v.upper():8s} {owner_d}")
    print(f"  comment: {comment_v.upper():8s} {comment_d}")

    signals = (owner_v, comment_v)
    if "taken" in signals:
        # One receiver-produced signal is proof. The other being `unknown` is the
        # normal case off Orca, and demanding both would make this useless there.
        print("HANDOVER: LANDED — a receiver-produced signal says it was picked up")
        return 0
    if all(s == "unknown" for s in signals):
        print("HANDOVER: UNKNOWN — nothing was checkable, which is NOT evidence "
              "it was dropped. Do not re-deliver on this.")
        return 2
    print("HANDOVER: NOT_YET — every checkable signal says nobody has taken it")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
