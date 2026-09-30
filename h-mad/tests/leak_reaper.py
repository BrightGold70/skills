"""Find and reap processes a test run leaked, keyed on the run's own tmp tree.

Used by `conftest.py` at session end. A process is a leak of THIS run when its
argv names the run's pytest basetemp: every wrapper, stub and sleeper the suite
starts is pointed at a `tmp_path` path, and no process outside the run is. The
reaper never matches its own process or any ancestor, so it cannot kill the
pytest that is running it.
"""
from __future__ import annotations

import os
import signal
import subprocess
import time


def _ancestry() -> set[int]:
    pids, pid = {os.getpid()}, os.getppid()
    while pid > 1 and pid not in pids:
        pids.add(pid)
        out = subprocess.run(["ps", "-o", "ppid=", "-p", str(pid)],
                             capture_output=True, text=True, check=False).stdout.strip()
        if not out.isdigit():
            break
        pid = int(out)
    return pids


def find_leaked(markers: list[str]) -> list[tuple[int, str]]:
    """(pid, command) of every process whose argv contains any marker."""
    markers = [m for m in markers if m]
    if not markers:
        return []
    listing = subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True,
                             text=True, check=False).stdout
    skip = _ancestry()
    leaked = []
    for line in listing.splitlines():
        pid_text, _, command = line.strip().partition(" ")
        if not pid_text.isdigit() or int(pid_text) in skip:
            continue
        if any(marker in command for marker in markers):
            leaked.append((int(pid_text), command.strip()))
    return leaked


def reap(pids: list[int], grace_s: float = 2.0) -> int:
    """TERM, wait up to grace_s, then KILL. Returns how many were signalled."""
    signalled = []
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
            signalled.append(pid)
        except (ProcessLookupError, PermissionError):
            pass
    deadline = time.monotonic() + grace_s
    alive = list(signalled)
    while alive and time.monotonic() < deadline:
        time.sleep(0.05)
        alive = [pid for pid in alive if _alive(pid)]
    for pid in alive:
        try:
            os.kill(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    return len(signalled)


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True
