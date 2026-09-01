#!/usr/bin/env python3
"""Measure a response SHAPE over N calls, and guarantee the panes get closed.

Hand-rolled eight times in one session to decide whether a guard was dormant, and
the tabulating was never the hard part. Two things were:

**N has to be cheap or the conclusion is wrong.** The measurement that produced
the `paneKey` finding read 5/5 one way and the 8th the opposite. Anything that
makes a bigger N expensive buys a confident wrong answer.

**A probe that leaks panes is worse than no probe.** Leaked panes pollute the pane
pool and the next `pin-agents` run — so cleanup is the design here, not an
afterthought. A `trap` alone is not enough: it does not survive SIGKILL, and it
cannot help at all with the window between "the pane exists" and "this process
learned its handle". So every attempt is JOURNALLED to disk before the create is
issued and updated with the handle immediately after, cleanup runs from `finally`
and from SIGINT/SIGTERM, and `--resume <journal>` closes what an earlier run could
not. A journal line with no handle is reported as a POSSIBLE leak rather than
silently dropped: something may exist that this process never got to name.

Deliberately command-agnostic. It takes the create/close/list commands as argv
templates, so it is testable without a runtime and is not welded to one verb.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import signal
import subprocess
import sys
from pathlib import Path

MISSING = object()


def dig(payload, path: str):
    """`a.b.c` through dicts. MISSING is distinct from a present null."""
    cur = payload
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return MISSING
        cur = cur[part]
    return cur


class Journal:
    """Append-only record of every pane this probe may have created.

    Written BEFORE the create so a crash mid-call still leaves a trace, and
    completed after it. Nothing here is buffered: a flush that never happens is
    the same as a journal that was never written.
    """

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _append(self, rec: dict) -> None:
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            os.fsync(fh.fileno())

    def intent(self, i: int) -> None:
        self._append({"i": i, "state": "creating"})

    def created(self, i: int, handle: str) -> None:
        self._append({"i": i, "state": "created", "handle": handle})

    def closed(self, handle: str) -> None:
        self._append({"handle": handle, "state": "closed"})

    def outstanding(self) -> tuple[list[str], list[int]]:
        """(handles not yet closed, indices that never reported a handle)."""
        if not self.path.is_file():
            return [], []
        open_handles: dict[str, None] = {}
        pending: dict[int, None] = {}
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("state") == "creating":
                pending[rec["i"]] = None
            elif rec.get("state") == "created":
                pending.pop(rec["i"], None)
                open_handles[rec["handle"]] = None
            elif rec.get("state") == "closed":
                open_handles.pop(rec["handle"], None)
        return list(open_handles), list(pending)


def run(argv: list[str], timeout: int = 60) -> tuple[int, str]:
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout
    except (OSError, subprocess.SubprocessError):
        return 127, ""


def close_all(journal: Journal, close_tpl: str) -> tuple[int, list[str]]:
    handles, _ = journal.outstanding()
    closed, failed = 0, []
    for h in handles:
        rc, _ = run(shlex.split(close_tpl.replace("{handle}", h)))
        if rc == 0:
            journal.closed(h)
            closed += 1
        else:
            failed.append(h)
    return closed, failed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--journal", required=True)
    ap.add_argument("--close", required=True, help="argv template containing {handle}")
    ap.add_argument("--create", help="argv template, may contain {i}")
    ap.add_argument("--field", help="dotted path whose PRESENCE is measured")
    ap.add_argument("--handle-path", default="result.terminal.handle")
    ap.add_argument("--n", type=int, default=1)
    ap.add_argument("--resume", action="store_true",
                    help="close what an earlier run left open, and measure nothing")
    a = ap.parse_args(argv)

    if "{handle}" not in a.close:
        sys.exit("--close must contain {handle}")
    journal = Journal(Path(a.journal))

    if a.resume:
        closed, failed = close_all(journal, a.close)
        _, pending = journal.outstanding()
        print(f"CLEANUP: closed={closed} failed={len(failed)} possible_leaks={len(pending)}")
        return 0 if not failed and not pending else 2

    if not a.create or not a.field:
        sys.exit("--create and --field are required unless --resume")

    present = absent = errors = 0
    rows = []
    try:
        for i in range(a.n):
            journal.intent(i)
            rc, out = run(shlex.split(a.create.replace("{i}", str(i))))
            if rc != 0:
                errors += 1
                rows.append((i, "ERR", ""))
                continue
            try:
                payload = json.loads(out)
            except json.JSONDecodeError:
                errors += 1
                rows.append((i, "UNPARSEABLE", ""))
                continue
            handle = dig(payload, a.handle_path)
            if handle is not MISSING and isinstance(handle, str):
                journal.created(i, handle)
            value = dig(payload, a.field)
            if value is MISSING or value is None:
                absent += 1
                rows.append((i, "absent", handle if isinstance(handle, str) else ""))
            else:
                present += 1
                rows.append((i, "present", handle if isinstance(handle, str) else ""))
    finally:
        # `finally` covers the exception path; the handlers below cover a signal,
        # and `--resume` covers a kill that outruns both.
        closed, failed = close_all(journal, a.close)
        _, pending = journal.outstanding()
        for i, state, h in rows:
            print(f"  {i:3d} {state:12s} {h}")
        print(f"PROBE: field={a.field} present={present}/{a.n} absent={absent}/{a.n} errors={errors}")
        print(f"CLEANUP: closed={closed} failed={len(failed)} possible_leaks={len(pending)}")
        if failed or pending:
            print(f"CLEANUP: NOT CLEAN — rerun with --resume --journal {a.journal}",
                  file=sys.stderr)
    return 0 if not errors and not failed and not pending else 2


def _on_signal(signum, _frame):  # pragma: no cover - exercised by the signal test
    raise SystemExit(128 + signum)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)
    raise SystemExit(main())
