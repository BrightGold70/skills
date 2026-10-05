"""One measured pytest run per working tree, and a report when the tree moved.

Registered by BOTH the repository's root `conftest.py` and `h-mad/tests/conftest.py`
(`register`, idempotent by name). The root one is what makes the lock structural:
pytest loads a rootdir conftest up front for EVERY invocation under the rootdir —
bare `pytest`, `pytest handoff/tests`, one `handoff/scripts` file, `pytest .` —
whereas a conftest under `h-mad/tests` is an initial conftest only when that
directory is named up front, so its `pytest_sessionstart` silently never ran for
the rest (review M1 of a9ad4d22). The h-mad one covers the install-path run
(`pytest ~/.claude/skills/h-mad/tests/`), which sees no root conftest above it.

Rows 1391/2361: two pytest runs over one tree produced 6 and 3 failures in
DIFFERENT sets, and 0 when the file ran alone; two full suites produced 11
phantom failures in a file that passes 40/40 alone; a mutation harness ran under
a full suite and was harmless only by luck. So a session takes the SAME lock the
mutation harness takes (`tree_lock`, one per git toplevel) and a second session
refuses with `SUITE: BUSY` and exit `SUITE_BUSY_EXIT`. The harness's own inner
pytest is exempt through the holder token it exports, or every spec run would
refuse itself. Separate worktrees are separate toplevels and never contend ON THE
LOCK; tests that share fixed `/tmp` paths can still collide across worktrees.

Row 745: the session digests the non-ignored tree at start and end and prints
`SUITE: TREE_MOVED paths=… n=K` when the two differ — the pass count above it
describes bytes that no longer exist. It reports; it never refuses an edit.

Hooks rather than a fixture: the refusal must land before collection, and the
end digest after every session fixture's teardown. If a LATER plugin's
`pytest_sessionstart` raises after this one took the lock, pytest skips
`pytest_sessionfinish`; the lock then lives until the process exits and the next
run's stale-take recovers it.
"""
from __future__ import annotations

import contextlib
import importlib.util
import os
import signal
import sys
import time
from pathlib import Path

import pytest

PLUGIN_NAME = "h_mad_tree_lock"
REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
_SUITE: dict = {}


def register(config) -> None:
    """Register this module once per session, whichever conftest asks first."""
    if not config.pluginmanager.has_plugin(PLUGIN_NAME):
        config.pluginmanager.register(sys.modules[__name__], PLUGIN_NAME)


def _script(name: str):
    """Load a sibling script by path, under a private name, without touching sys.path.

    None when it is not there: a conftest copied on its own into a scratch
    directory (the leak-reaper end-to-end test does that) has no tree to lock.
    """
    path = _SCRIPTS / f"{name}.py"
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location(f"_suite_conftest_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _say(config, line: str) -> None:
    reporter = config.pluginmanager.get_plugin("terminalreporter")
    if reporter is not None:
        reporter.write_line(line)
    else:
        print(line, flush=True)


def _release() -> None:
    stack = _SUITE.pop("lock", None)
    if stack is not None:
        stack.close()
    previous = _SUITE.pop("sigterm", None)
    if previous is not None:
        with contextlib.suppress(ValueError, OSError):
            signal.signal(signal.SIGTERM, previous)


def _on_sigterm(signum, frame) -> None:
    """SIGTERM is how a backgrounded suite is stopped; release, then die of it."""
    previous = _SUITE.get("sigterm")
    _release()
    if callable(previous):
        previous(signum, frame)
        return
    signal.signal(signum, signal.SIG_DFL)
    os.kill(os.getpid(), signum)


def pytest_sessionstart(session):
    harness, gate = _script("h_mad_mutation_harness"), _script("h_mad_audit_gate")
    if harness is None or gate is None:
        return
    _SUITE["harness"] = harness
    if not harness.held_by_an_enclosing_run(REPO_ROOT):
        stack = contextlib.ExitStack()
        try:
            stack.enter_context(harness.tree_lock(REPO_ROOT, "pytest-session"))
        except harness.TreeBusy as busy:
            holder = busy.holder
            pid = holder.get("pid")
            started = holder.get("started")
            age = (f"{time.time() - started:.0f}s" if isinstance(started, (int, float))
                   else "unknown")
            line = (f"SUITE: BUSY holder={pid if isinstance(pid, int) else 'unparseable'} "
                    f"age={age} what={holder.get('spec') or 'unknown'} lock={holder.get('lock')}")
            _say(session.config, line)
            _say(session.config, "  another pytest session or mutation run holds this "
                 "working tree; a second run over it measures a tree being rewritten. "
                 "Nothing was measured — wait for the holder. An unparseable lock can be a "
                 "holder caught mid-write: retry in a second before anything else, and "
                 "delete the lock file only if you are certain no run is in flight.")
            pytest.exit(line, returncode=gate.SUITE_BUSY_EXIT)
        except OSError as exc:
            # A read-only checkout, or `.h-mad` existing as a file: the lock cannot
            # be written. Losing the whole suite to an INTERNALERROR is worse than
            # running unlocked, so say so and run.
            _say(session.config, f"SUITE: LOCK_UNAVAILABLE reason={exc.__class__.__name__} "
                 f"lock={harness._lock_path(REPO_ROOT)} — running unlocked: {exc}")
        else:
            _SUITE["lock"] = stack
            # A session started with SIGTERM IGNORED (`trap '' TERM`) keeps
            # ignoring it: installing a handler would make it die (review R2-N2).
            with contextlib.suppress(ValueError, OSError):
                if signal.getsignal(signal.SIGTERM) is not signal.SIG_IGN:
                    _SUITE["sigterm"] = signal.signal(signal.SIGTERM, _on_sigterm)
    _SUITE["digest"] = harness.tree_digest(REPO_ROOT)


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session):
    harness = _SUITE.get("harness")
    if harness is not None and "digest" in _SUITE:
        _SUITE["moved"] = harness.moved_paths(_SUITE.pop("digest"),
                                              harness.tree_digest(REPO_ROOT))
    _release()


def pytest_terminal_summary(terminalreporter):
    moved = _SUITE.pop("moved", None)
    if moved:
        shown = ",".join(moved[:10]) + (",…" if len(moved) > 10 else "")
        terminalreporter.write_line(f"SUITE: TREE_MOVED paths={shown} n={len(moved)}",
                                    yellow=True)
