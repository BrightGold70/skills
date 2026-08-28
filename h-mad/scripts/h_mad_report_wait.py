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


def report_wait(path, timeout, interval, *, out=sys.stdout, err=sys.stderr,
                sleep=time.sleep, require_marker=True):
    if path is None or path == "":
        print("h_mad_report_wait: missing required argument: report-path", file=err)
        return 2
    if path.startswith("-"):
        print(f"h_mad_report_wait: report-path looks like a flag: {path} "
              f"(pass the path first)", file=err)
        return 2
    # `require_marker=False` is the `exec --out` case: that file has no marker
    # because it is COPIED into place once the agent has finished, so its
    # appearance is the completion signal. Opt-IN, never the default — flipping it
    # would silently turn the marker contract off for every existing caller, and
    # the marker is the only thing standing between them and a half-written report.
    #
    # It is sound only because `hmad-dispatch exec` writes `--out` atomically
    # (temp + os.replace). A plain `cp` there would put a truncated file under this
    # poller's nose and a truncated verdict reads exactly like a real one — the
    # failure the marker was invented to prevent, re-entered by another door.
    marker = path + ".done"
    tick = interval if interval >= 1 else 1
    elapsed = 0
    while elapsed <= timeout:
        marker_ok = os.path.isfile(marker) if require_marker else True
        if marker_ok and os.path.isfile(path) and os.path.getsize(path) > 0:
            with open(path, "r") as f:
                out.write(f.read())
            return 0
        if interval > 0:
            sleep(interval)
        elapsed += tick
    missing = f"missing {marker} or empty {path}" if require_marker else f"missing or empty {path}"
    print(f"[H-MAD] report-wait timed out after {timeout}s ({missing})", file=err)
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
    p.add_argument(
        "--no-done-marker", dest="require_marker", action="store_false",
        help="treat the file's own appearance as completion, with no .done marker. "
             "For `exec --out`, which is copied into place at completion. Opt-in: the "
             "marker is what keeps a half-written report unreadable for everyone else.",
    )
    args = p.parse_args(argv)
    return report_wait(args.path, args.timeout, args.interval,
                       require_marker=args.require_marker)


if __name__ == "__main__":
    sys.exit(main())
