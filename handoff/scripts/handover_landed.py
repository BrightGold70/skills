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
  2. the target worktree's comment is no longer the sender's `handover:` stamp
  3. the target branch carries commits of its own, or has merged

(2) deliberately does NOT require the words `taken over:`. Measured 2026-09-01: a
handover that was picked up, fixed, tested and merged as `282a3a5` reported
NOT_YET, because the receiver never wrote a claim (its worktree had its own
`docs/.bkit-memory.json`) and had already replaced the stamp with its own
completion note. Both signals failed honestly and the verdict was still the one
that costs something — the prescribed response to NOT_YET is to re-deliver, which
there meant re-dispatching work already on `main`. Visible completion now outranks
the expected prefix. (3) exists for the same case from the other side: a receiver
who just does the work, claiming nothing and stamping nothing.

A fourth signal — the receiving pane's own output — is deliberately NOT
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
import re
import shutil
import subprocess
import sys
from pathlib import Path

TAKEN = "taken over:"
HANDED = "handover:"
# A WRITE closeout stamp. It is worktree-scoped and written by whichever session
# closes out on that worktree — including a SIBLING session that never saw the
# brief. Measured 2026-09-05 (#100 defect A): the skills main worktree carried
# `handoff: doc-block-exec-rounds-fifteen-sixteen …` and a brief nobody had picked
# up (no Taken-Over-By, no claim) was reported LANDED on that comment alone.
CLOSEOUT = "handoff:"


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


def _names_slug(comment: str, slug: str) -> bool:
    """True when *comment* names *slug* at a slug boundary.

    The LEFT boundary is strict and the RIGHT one is not, because the two real
    comments differ on exactly that side:

      * a receiver that picks the brief up and closes out writes its own WRITE
        stamp, whose slug EXTENDS the brief's — `handoff: audit-loop-evidence-
        shipped · next: merge`. A whole-token test rejects it and the sender
        re-delivers merged work (the 2026-09-01 defect);
      * a lane whose slug merely CONTAINS the brief's as a later word, or a
        different slug entirely, must not match — hence the strict left side.

    A right-extension shares the brief's slug as its leading component, which is
    what a receiver's own follow-on work looks like and what a foreign lane's
    slug does not. `--slug doc-block-exec` therefore does match
    `doc-block-exec-rounds-fifteen-sixteen`: that IS the same feature's lane, and
    a slug is only ever passed when it is the brief's own.
    """
    return re.search(rf"(?<![A-Za-z0-9_-]){re.escape(slug)}(?![A-Za-z0-9_])", comment) is not None


def comment_signal(worktree_path: str | None, dispatch: str,
                   slug: str | None = None) -> tuple[str, str]:
    """(verdict, detail) over the target worktree's checkpoint stamp.

    `slug` is the brief's slug when the caller has it: a replacement comment that
    names it is pickup evidence whatever prefix it carries.
    """
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
            # `in`, not `startswith`: HANDOVER Step 4 PRESERVES a human note by
            # appending (`<existing> - handover: ...`), so the sender's own stamp
            # legitimately sits mid-string and a prefix test would miss it.
            if TAKEN in comment:
                return "taken", f"comment reads {comment[:80]!r}"
            if HANDED in comment:
                return "not_yet", "comment still carries the sender's `handover:` stamp"
            if slug and _names_slug(comment, slug):
                return "taken", f"comment names the brief: {comment[:80]!r}"
            if slug and CLOSEOUT in comment:
                # A `handoff:` stamp is a session's OWN WRITE closeout, and this
                # one does not name the brief. It says A session worked on this
                # worktree; it does not say that session saw the brief — a
                # sibling lane closing out on the same worktree writes exactly
                # this (#100 defect A, measured 2026-09-05 on the skills main
                # worktree: `handoff: doc-block-exec-rounds-fifteen-sixteen …`
                # for a brief nobody had picked up). Neither pickup nor absence.
                #
                # Gated on `slug` because without it there is NO discriminator:
                # a receiver who picks the brief up and closes out writes a
                # `handoff:` stamp too, and calling that `unknown` would resurrect
                # the 2026-09-01 false NOT_YET this tool exists to prevent. With
                # no slug the older rule stands — visible completion outranks the
                # expected prefix — and the verdict line says the check was
                # unavailable.
                return "unknown", (f"comment is a session closeout stamp that does not name "
                                   f"the brief, so it may be a sibling lane's: {comment[:80]!r}")
            if comment.strip():
                # Neither stamp, but SOMETHING is there. Step 4 left `handover:`
                # on this worktree, so its absence means the receiver overwrote
                # it -- which is receiver-produced evidence even though it does
                # not use the word. Measured 2026-09-01: a completed handover
                # whose receiver replaced the stamp with `Complete: SIGPIPE wait
                # gates fixed; main @ 282a3a5` was reported NOT_YET, and the
                # prescribed response to NOT_YET is to re-deliver work that had
                # already merged. Visible completion outranks the expected prefix.
                return "taken", f"stamp was overwritten by the receiver: {comment[:80]!r}"
            return "not_yet", "comment is empty -- no receiver stamp"
    return "unknown", f"no worktree at {worktree_path} in worktree-ps"


def _git(repo: str, *args: str) -> tuple[int, str]:
    try:
        r = subprocess.run(["git", "-C", repo, *args], capture_output=True,
                           text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, exc.__class__.__name__
    return r.returncode, r.stdout.strip()


def branch_signal(repo: str | None, branch: str | None) -> tuple[str, str]:
    """(verdict, detail) over commits the RECEIVER made on the target branch.

    The third receiver-produced signal, and the one that survives when the
    receiver never wrote a claim and never re-stamped the worktree -- it just
    did the work. Deliberately narrow: an ABSENT branch is `unknown`, never
    `not_yet`, because the commonest reason a handover branch is gone is that
    it merged and was deleted, which is the opposite conclusion.
    """
    if not repo or not branch:
        return "unknown", "no --repo/--branch given"
    rc, _ = _git(repo, "rev-parse", "--git-dir")
    if rc != 0:
        return "unknown", f"{repo} is not a git work tree"
    rc, _ = _git(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}")
    if rc != 0:
        return "unknown", (f"branch {branch!r} does not exist -- it may have merged "
                           "and been deleted, which is pickup, not absence")
    rc, default = _git(repo, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    default = default.split("/", 1)[-1] if rc == 0 and default else "main"
    rc, out = _git(repo, "rev-list", "--count", f"{default}..{branch}")
    if rc != 0:
        return "unknown", f"could not compare {branch} against {default}"
    if out.isdigit() and int(out) > 0:
        return "taken", f"{out} commit(s) on {branch} not on {default}"
    # Zero ahead is AMBIGUOUS, and `git branch --merged` cannot break the tie:
    # it lists a branch that merged AND a branch that never committed, because
    # both are ancestors of the default. Reporting either as pickup invents
    # evidence; reporting either as absence is the false NOT_YET this whole tool
    # exists to avoid. So this signal can only ever ADD evidence of pickup --
    # it never manufactures absence.
    return "unknown", (f"{branch} is level with {default}: that is what a merged-and-"
                       "finished branch AND an untouched one both look like")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--state", required=True)
    ap.add_argument("--feature", required=True)
    ap.add_argument("--sender-session", required=True)
    ap.add_argument("--worktree-path")
    ap.add_argument("--repo", help="target repo, for the branch signal")
    ap.add_argument("--branch", help="target branch, for the branch signal")
    ap.add_argument("--hmad-dispatch", default="hmad-dispatch")
    ap.add_argument("--slug", help="the brief's slug; a replacement comment naming it is pickup")
    a = ap.parse_args(argv)

    owner_v, owner_d = owner_signal(a.state, a.feature, a.sender_session)
    comment_v, comment_d = comment_signal(a.worktree_path, a.hmad_dispatch, a.slug)
    branch_v, branch_d = branch_signal(a.repo, a.branch)
    print(f"  claim:   {owner_v.upper():8s} {owner_d}")
    print(f"  comment: {comment_v.upper():8s} {comment_d}")
    print(f"  branch:  {branch_v.upper():8s} {branch_d}")

    signals = (owner_v, comment_v, branch_v)
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
