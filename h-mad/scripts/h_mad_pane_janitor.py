#!/usr/bin/env python3
"""h_mad_pane_janitor.py — close the panes a live probe created, or refuse.

After a live orchestration probe the panes it started have to be cleaned up.
That pipeline was hand-rolled seven times, and the dangerous part is not the
closing — it is deciding WHICH panes are the probe's. Panes started by
`orca orchestration worker-start` inherit the worktree name as their title, so
they are indistinguishable from the operator's own agent pane by title, and each
hand-run re-typed the keep-list from memory. Getting it wrong closes the
operator's own session.

So the keep-list is recorded rather than remembered:

    h_mad_pane_janitor.py snapshot --worktree <path> --out <file>   # before
    ...run the probe...
    h_mad_pane_janitor.py plan  --baseline <file>                   # dry run
    h_mad_pane_janitor.py clean --baseline <file> --apply           # closes

A candidate is a pane that is in the baseline's worktree, absent from the
baseline, and not this process's own pane. Everything else is out of scope by
construction, including every pane in another worktree — measured 2026-08-25,
a second agent session was live in a sibling worktree while this was written.

Panes are only half of it. An unsettled dispatch wedges its terminal
permanently: `worker-abandon` and `worker-stop` both answer `dispatch_not_found`
for one (upstream stablyai/orca#13005), so a janitor that closes a pane without
settling its dispatch leaves the Run dirty in a way nothing can later repair.
Each candidate is therefore looked up in `orca orchestration worker-list`, whose
rows carry `agentTerminalHandle` -> `taskId` + `dispatchStatus`, and an unsettled
one is settled with `task-update --status completed` BEFORE its pane is closed.
A settle that fails means the pane is left alone and reported: a wedged terminal
you can still see beats one you cannot.

Two live footguns this exists to not step on, both verified on a real install:

  * `orca terminal close` takes `--terminal` OPTIONALLY, and with no handle it
    closes the CALLER'S OWN pane. Every close this emits carries an explicit
    handle, and a test pins that.
  * `orca terminal show` with no `--terminal` returns the caller's own pane.
    That is the self-identification, and the run REFUSES rather than proceeding
    when it cannot get one — without it there is nothing stopping the janitor
    from closing the session running it.

    JANITOR: PLANNED|CLEANED|NOTHING candidates=N settled=J closed=K skipped=S
    JANITOR: REFUSED reason=<reason>

exit 0 on a verdict, 2 on a refusal. Dry run unless `--apply`. Stdlib-only.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

TOKEN = "JANITOR"
SETTLED = {"completed", "failed", "cancelled", "canceled"}
DEFAULT_MAX = 10


class Refusal(Exception):
    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(reason)
        self.reason = reason
        self.detail = detail


def orca_json(orca: str, args: list[str]) -> dict:
    """Run an orca subcommand with --json and return its `result`, or refuse."""
    try:
        proc = subprocess.run(
            [orca, *args, "--json"], capture_output=True, text=True
        )
    except OSError as exc:
        raise Refusal("orca_unavailable", f"{orca}: {exc}") from None
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        raise Refusal("orca_unparseable", " ".join(args)) from None
    if not payload.get("ok"):
        error = (payload.get("error") or {}).get("code", "unknown")
        raise Refusal("orca_error", f"{' '.join(args)}: {error}")
    return payload.get("result") or {}


def list_panes(orca: str) -> list[dict]:
    return orca_json(orca, ["terminal", "list"]).get("terminals") or []


def self_handle(orca: str) -> str:
    """This process's own pane. A run without one must not close anything."""
    terminal = orca_json(orca, ["terminal", "show"]).get("terminal") or {}
    handle = terminal.get("handle")
    if not handle:
        raise Refusal("cannot_identify_self")
    return handle


def worker_rows(orca: str) -> dict[str, dict]:
    """agentTerminalHandle -> worker row.

    `worker-list` is used rather than `task-list` because the latter needs a
    bound Run and answers `run_required` otherwise — a janitor that only works
    inside a bound Run cannot clean up after a probe that left one unbound.
    """
    rows = orca_json(orca, ["orchestration", "worker-list"]).get("workers") or []
    return {r["agentTerminalHandle"]: r for r in rows if r.get("agentTerminalHandle")}


def take_snapshot(orca: str, worktree: str) -> dict:
    panes = list_panes(orca)
    scoped = [p for p in panes if p.get("worktreePath") == worktree]
    return {
        "worktree": worktree,
        "self": self_handle(orca),
        "handles": sorted(p["handle"] for p in scoped),
    }


def candidates(orca: str, baseline: dict) -> list[dict]:
    """Panes in the baseline's worktree that were not there when it was taken."""
    worktree = baseline["worktree"]
    known = set(baseline["handles"])
    # Re-read the caller's own handle rather than trusting the snapshot's: the
    # janitor may run from a different pane than the one that took it, and the
    # only pane it must never close is the one it is running in NOW.
    me = self_handle(orca)
    known.add(me)
    known.add(baseline.get("self", ""))
    return [
        pane for pane in list_panes(orca)
        if pane.get("worktreePath") == worktree and pane["handle"] not in known
    ]


def settle_and_close(
    orca: str, pane: dict, workers: dict[str, dict], *, apply: bool
) -> dict:
    """Settle a candidate's dispatch, then close its pane. Never the reverse."""
    handle = pane["handle"]
    row = workers.get(handle)
    outcome = {"handle": handle, "title": pane.get("title", ""), "settled": False,
               "closed": False, "skipped": None}

    if row and str(row.get("dispatchStatus", "")).lower() not in SETTLED:
        task_id = row.get("taskId")
        if not task_id:
            outcome["skipped"] = "worker row carries no taskId to settle"
            return outcome
        if apply:
            try:
                orca_json(orca, ["orchestration", "task-update",
                                 "--id", task_id, "--status", "completed"])
            except Refusal as exc:
                # A pane whose dispatch would not settle is left LIVE on
                # purpose. Closing it wedges the terminal permanently, and a
                # wedged terminal you can still see beats one you cannot.
                outcome["skipped"] = f"settle failed ({exc.reason}); pane left open"
                return outcome
        outcome["settled"] = True

    if apply:
        # `--terminal` is optional to the CLI and an omitted handle closes the
        # caller's own pane, so it is always explicit here.
        orca_json(orca, ["terminal", "close", "--terminal", handle])
    outcome["closed"] = True
    return outcome


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Close the panes a live probe created")
    sub = ap.add_subparsers(dest="verb", required=True)

    snap = sub.add_parser("snapshot", help="record the keep-list BEFORE the probe")
    snap.add_argument("--worktree", required=True)
    snap.add_argument("--out", required=True, type=Path)

    for name, help_text in (("plan", "show what would be closed"),
                            ("clean", "close them")):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--baseline", required=True, type=Path)
        p.add_argument("--max", type=int, default=DEFAULT_MAX,
                       help=f"refuse to touch more than this many panes (default {DEFAULT_MAX})")
        if name == "clean":
            p.add_argument("--apply", action="store_true",
                           help="actually settle and close; without it this is a dry run")

    for p in sub.choices.values():
        p.add_argument("--orca", default="orca", help="orca CLI to use")

    args = ap.parse_args(argv)

    try:
        if args.verb == "snapshot":
            snapshot = take_snapshot(args.orca, args.worktree)
            args.out.write_text(json.dumps(snapshot, indent=1) + "\n", encoding="utf-8")
            print(f"{TOKEN}: SNAPSHOT worktree={args.worktree} "
                  f"handles={len(snapshot['handles'])} out={args.out}")
            print(f"[H-MAD] pane-janitor snapshot {len(snapshot['handles'])}")
            return 0

        try:
            baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise Refusal("baseline_unreadable", f"{args.baseline}: {exc}") from None
        if not isinstance(baseline.get("handles"), list) or not baseline.get("worktree"):
            raise Refusal("baseline_malformed", str(args.baseline))

        found = candidates(args.orca, baseline)
        if len(found) > args.max:
            # A baseline taken against the wrong worktree, or a stale one, turns
            # every pane into a candidate. Refuse rather than act on a set that
            # large without the operator having said so.
            raise Refusal(
                "too_many_candidates",
                f"{len(found)} candidates exceeds --max {args.max}; check the baseline",
            )
        if not found:
            print(f"{TOKEN}: NOTHING candidates=0 settled=0 closed=0 skipped=0")
            print("[H-MAD] pane-janitor nothing")
            return 0

        apply = bool(getattr(args, "apply", False))
        workers = worker_rows(args.orca)
        outcomes = [settle_and_close(args.orca, pane, workers, apply=apply)
                    for pane in found]

        settled = sum(1 for o in outcomes if o["settled"])
        closed = sum(1 for o in outcomes if o["closed"])
        skipped = [o for o in outcomes if o["skipped"]]
        verdict = "CLEANED" if apply else "PLANNED"
        # A dry run reports what it WOULD do under different field names. A
        # `PLANNED` line carrying `settled=1 closed=1` reads as work that
        # happened, which is the same cannot-judge-looks-like-done failure the
        # gate tokens elsewhere are shaped to avoid.
        settle_key, close_key = ("settled", "closed") if apply else ("would_settle", "would_close")
        print(f"{TOKEN}: {verdict} candidates={len(found)} {settle_key}={settled} "
              f"{close_key}={closed} skipped={len(skipped)}")
        for o in outcomes:
            mark = ("closed" if apply else "would close") if o["closed"] else "SKIPPED"
            note = f" — {o['skipped']}" if o["skipped"] else ""
            settle_note = " (settled first)" if o["settled"] else ""
            print(f"  {mark}: {o['handle']} {o['title']!r}{settle_note}{note}")
        if not apply:
            print("  dry run — nothing was settled or closed. Re-run `clean --apply`.")
        print(f"[H-MAD] pane-janitor {verdict.lower()} {closed}")
        return 0

    except Refusal as exc:
        print(f"{TOKEN}: REFUSED reason={exc.reason}")
        if exc.detail:
            print(f"  {exc.detail}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
