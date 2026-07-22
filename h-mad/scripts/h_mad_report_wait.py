#!/usr/bin/env python3
"""Poll for a dropped report file and emit it — standalone, stdlib-only.

This is the wrapper-independent half of `hmad-dispatch report-wait`. A dispatched
agent writes its full report to <report-path> and signals completion by creating
<report-path>.done; this script polls the marker and prints the file.

Why a standalone script and not only the bash verb: when the dispatched implementer
is editing `hmad-dispatch.sh` ITSELF (e.g. adding a verb), a concurrent
`hmad-dispatch report-wait …` re-parses that half-written wrapper and can die with
a transient `syntax error` (monitoring H3). Polling with this script instead —
`python3 h_mad_report_wait.py <path> …` — never touches the wrapper, so the
coordinator's poll is immune to the implementer's in-flight edits. `_cmd_report_wait`
also delegates here, so the two can never drift.

Contract (identical to the former bash loop):
- The `.done` marker (not mere file existence) is the completion signal, so a
  half-written report is never read; the report file must also be non-empty.
- A path that looks like a flag (starts with '-') is rejected — catches
  `report-wait --timeout 600` with the path omitted.
- exit 0 + file contents on stdout when the marker appears and the file is non-empty;
  exit 1 (stderr note) on timeout; exit 2 (stderr) on a usage error.
"""
import argparse
import os
import sys
import time


def report_wait(path, timeout, interval, *, out=sys.stdout, err=sys.stderr, sleep=time.sleep):
    if path is None or path == "":
        print("h_mad_report_wait: missing required argument: report-path", file=err)
        return 2
    if path.startswith("-"):
        print(f"h_mad_report_wait: report-path looks like a flag: {path} "
              f"(pass the path first)", file=err)
        return 2
    marker = path + ".done"
    tick = interval if interval >= 1 else 1
    elapsed = 0
    while elapsed <= timeout:
        if os.path.isfile(marker) and os.path.isfile(path) and os.path.getsize(path) > 0:
            with open(path, "r") as f:
                out.write(f.read())
            return 0
        if interval > 0:
            sleep(interval)
        elapsed += tick
    print(f"[H-MAD] report-wait timed out after {timeout}s "
          f"(missing {marker} or empty {path})", file=err)
    # A missing report is not a verdict. It has been caused by the dispatch never
    # arriving (a rotated handle: the pane shows `terminal_handle_stale`) and by
    # the agent stopping mid-run with correct work already on disk
    # (`Selected model is at capacity`). Treating silence as either pass or fail
    # has been wrong in both directions -- read the pane, then check the tree.
    print("[H-MAD] a missing report is neither pass nor fail. Before concluding the "
          "agent failed, read its pane for `terminal_handle_stale` (the dispatch "
          "never landed) or `Selected model is at capacity` (it stopped after "
          "working), and check the working tree for work it completed but never "
          "reported.", file=err)
    return 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    # Reject a flag in the path slot BEFORE argparse, so `--timeout 600` with the
    # path omitted is a clear usage error rather than "unrecognized arguments".
    if argv and argv[0].startswith("-"):
        print(f"h_mad_report_wait: report-path looks like a flag: {argv[0]} "
              f"(pass the path first)", file=sys.stderr)
        return 2
    p = argparse.ArgumentParser(prog="h_mad_report_wait")
    p.add_argument("path", help="report file path (its .done marker is the signal)")
    p.add_argument("--timeout", type=int, default=300)
    default_interval = int(os.environ.get("HMAD_REPORT_POLL_INTERVAL", "2"))
    p.add_argument("--interval", type=int, default=default_interval)
    args = p.parse_args(argv)
    return report_wait(args.path, args.timeout, args.interval)


if __name__ == "__main__":
    sys.exit(main())
