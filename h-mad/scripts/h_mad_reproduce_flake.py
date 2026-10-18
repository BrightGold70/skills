#!/usr/bin/env python3
"""Reproduce a pytest flake across signal disposition and machine load."""

import argparse
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile


CELLS = tuple(f"{disposition}-{load}" for disposition in ("fg", "bg")
              for load in ("idle", "cpu", "fork"))
CPU_LOAD = "while True: pass"
FORK_LOAD = "import subprocess\nwhile True: subprocess.run(['/usr/bin/true'])"


class Unreadable(Exception):
    """The requested experiment could not be measured."""


def _interrupt(signum, frame):
    raise KeyboardInterrupt


def _ignore_sigint():
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def _stop(child):
    # Kill the entire group even if its leader has already exited.
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    child.wait()


def _run(command, cwd, timeout, background=False):
    child = subprocess.Popen(
        command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, errors="replace", start_new_session=True,
        preexec_fn=_ignore_sigint if background else None,
    )
    try:
        try:
            output, _ = child.communicate(timeout=timeout)
            return child.returncode, output
        except subprocess.TimeoutExpired:
            _stop(child)
            output, _ = child.communicate()
            return 1, output + "\nFLAKE timeout\n"
    finally:
        _stop(child)
        if child.stdout is not None:
            child.stdout.close()


def _measure(args, cells, log_dir):
    pytest = [args.python, "-m", "pytest"]
    code, _ = _run(pytest + ["--version"], args.cwd, args.timeout)
    if code != 0:
        raise Unreadable("pytest_missing")
    code, output = _run(pytest + [args.nodeid, "--collect-only", "-q", "-p",
                                 "no:cacheprovider"], args.cwd, args.timeout)
    if code != 0 or "no tests collected" in output.lower():
        raise Unreadable("collection_failed")

    failed_cells = []
    for cell in cells:
        disposition, load = cell.split("-")
        helpers = []
        try:
            count = (os.cpu_count() or 1) if load == "cpu" else int(load == "fork")
            for _ in range(count):
                helpers.append(subprocess.Popen(
                    [sys.executable, "-c", CPU_LOAD if load == "cpu" else FORK_LOAD],
                    start_new_session=True, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                ))
            failures = 0
            for index in range(1, args.runs + 1):
                code, output = _run(
                    pytest + [args.nodeid, "-q", "-p", "no:cacheprovider"],
                    args.cwd, args.timeout, background=disposition == "bg",
                )
                if code not in (0, 1):
                    raise Unreadable("pytest_interrupted_or_unreadable")
                if code != 0:
                    failures += 1
                    (log_dir / f"{cell}-{index}.log").write_text(output, encoding="utf-8")
            print(f"FLAKE: {cell} fails={failures}/{args.runs}", flush=True)
            if failures:
                failed_cells.append(cell)
        finally:
            for helper in helpers:
                _stop(helper)

    if failed_cells:
        print(f"FLAKE-VERDICT: REPRODUCED cells={','.join(failed_cells)} logs={log_dir}")
    else:
        print(f"FLAKE-VERDICT: NOT_REPRODUCED runs={len(cells) * args.runs}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("nodeid")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--log-dir", type=Path)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--cells", default=",".join(CELLS))
    args = parser.parse_args(argv)
    cells = args.cells.split(",")
    if args.runs < 1 or not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("runs and timeout must be positive and finite")
    if any(cell not in CELLS for cell in cells) or len(set(cells)) != len(cells):
        parser.error("cells must be distinct fg/bg-idle/cpu/fork names")

    previous = {sig: signal.signal(sig, _interrupt)
                for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        log_dir = args.log_dir or Path(tempfile.mkdtemp(prefix="h-mad-flake-"))
        log_dir.mkdir(parents=True, exist_ok=True)
        print(f"FLAKE-LOGS: {log_dir}", flush=True)
        _measure(args, cells, log_dir)
        return 0
    except KeyboardInterrupt:
        print("FLAKE-VERDICT: UNREADABLE reason=interrupted")
        return 2
    except (Unreadable, OSError) as error:
        reason = str(error).replace("\n", " ")
        print(f"FLAKE-VERDICT: UNREADABLE reason={reason}")
        return 2
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


if __name__ == "__main__":
    sys.exit(main())
