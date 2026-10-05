"""Protect real session state from the test suite.

Every test isolates its pin file by passing `HMAD_ORCA_PIN_FILE`. That isolation
is honoured by ONE branch in `_pin_file`, and J2 made the fallback resolve to the
enclosing repository rather than the cwd — so if that branch ever stops working,
writes land on the developer's live `<repo>/.h-mad/orca-pins.env` instead of a
temp path.

That is not hypothetical. Mutation-testing `_pin_file`'s override branch (the
practice `invariants.base.md` §"Test discrimination" mandates) deleted exactly
that branch and redirected the whole suite's pin writes onto the real file,
replacing two live agent handles with `term_live`/`term_explicit`. The suite
reported 642 passed while doing it: from the tests' point of view nothing was
wrong, because they never assert where the file is NOT.

So the protection belongs here rather than in any single test — snapshot the real
file before the session and restore it after if anything moved it, loudly.
"""
import os
import re
import subprocess
from pathlib import Path

import pytest

# No test reads the host's real `ps`, `git` lane history or `~/.claude` transcripts
# through `h_mad_state_ownership`'s liveness readers (row 1406 review, SF5). Set at
# import, before any test module builds an `env={**os.environ, ...}`, so CLI
# subprocesses inherit it too. Tests of the readers themselves unset it.
os.environ["H_MAD_LIVENESS_CLOCKS_OFF"] = "1"

REPO_ROOT = Path(__file__).resolve().parents[2]


def _live_pin_file() -> Path:
    """The same path `_pin_file` resolves to for an unset override, from here."""
    try:
        root = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return REPO_ROOT / ".h-mad" / "orca-pins.env"
    return Path(root) / ".h-mad" / "orca-pins.env"


@pytest.fixture(scope="session", autouse=True)
def _protect_live_pin_file():
    target = _live_pin_file()
    before = target.read_bytes() if target.is_file() else None
    yield
    after = target.read_bytes() if target.is_file() else None
    # J18 pin-file guard mutation anchor. Distinct from the wire-registry anchor
    # below because `if after == before:` appears once per guard, and the mutation
    # harness refuses any anchor it cannot match exactly once.
    if after == before:
        return
    # Restore first, complain second: a developer's live agent handles matter
    # more than the tidiness of this message.
    if before is None:
        try:
            target.unlink()
        except FileNotFoundError:
            pass
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(before)
    pytest.fail(
        f"the test suite modified the live pin file {target} and it has been "
        "restored. Some test is not isolating HMAD_ORCA_PIN_FILE, or a mutation "
        "disabled the override branch in _pin_file. Re-run `hmad-dispatch env` "
        "to confirm your agent handles.",
        pytrace=False,
    )


def _live_wire_registry_file() -> Path:
    """The repository's real wire registry, independent of the test cwd."""
    try:
        root = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return REPO_ROOT / ".h-mad" / "wires.jsonl"
    return Path(root) / ".h-mad" / "wires.jsonl"


@pytest.fixture(scope="session", autouse=True)
def _protect_live_wire_registry():
    target = _live_wire_registry_file()
    before = target.read_bytes() if target.is_file() else None
    yield
    after = target.read_bytes() if target.is_file() else None
    # J18 guard mutation anchor.
    if after == before:
        return
    if before is None:
        try:
            target.unlink()
        except FileNotFoundError:
            pass
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(before)
    pytest.fail(
        f"the test suite modified the live wire registry {target} and it has been "
        "restored. Some test is not isolating its registry path, or a mutation "
        "disabled the path-redirection branch in the wire registry writer.",
        pytrace=False,
    )


import os

_AMBIENT_HOST_KEYS = ("HPW_AGENT_BACKEND", "HMAD_HOST", "HMAD_CONTEXT_WINDOW")


@pytest.fixture
def hermetic_env():
    """Build a subprocess environment carrying no ambient Claude or host markers."""
    def make(**extra: str) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items()
               if not k.startswith("CLAUDE") and k not in _AMBIENT_HOST_KEYS}
        env.update(extra)
        return env
    return make


@pytest.fixture(autouse=True)
def _hermetic_report_path_claims(monkeypatch, tmp_path):
    """`h_mad_assemble_audit.py --report-file` claims each report path once under
    `$XDG_CACHE_HOME/h-mad/handed` (default `~/.cache/h-mad/handed`), and nothing
    releases a claim. A test that reached the real cache would permanently refuse
    that path for the developer, so every test gets its own."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg-cache"))


@pytest.fixture(autouse=True)
def _hermetic_host_skill_roots(monkeypatch, tmp_path):
    monkeypatch.setenv("HMAD_AGENTS_SKILLS_DIR", str(tmp_path / "absent-agents-skills"))
    monkeypatch.setenv("HMAD_AGY_SKILLS_DIR", str(tmp_path / "absent-agy-skills"))


# `audit-cycle` mints a fresh `/tmp/audit_<feature>_<phase>_cycle<N>_run<ts>-<pid>`
# stem per invocation (claim once, never re-hand a report path), so the verb tests
# no longer overwrite one fixed set of /tmp files: each run leaves new ones, about
# 900 per full suite. Remove the ones THIS session created, and only for the
# synthetic feature names the tests use -- /tmp is shared with live audit runs.
_TEST_RUN_FILE = re.compile(
    r"^audit_(cycle-red|cycle-status|cycle-clear|cycle-docs-.+?|size_status=unverified"
    r"|surf\d+|grok-stale-.+?|handed-.+?|demo)_(plan|design|impl-plan)_cycle[^_]+"
    r"_run\d{8}T\d{6}Z-\d+_p\d+\."
)


def _test_run_files() -> set[Path]:
    return {p for p in Path("/tmp").glob("audit_*_run*") if _TEST_RUN_FILE.match(p.name)}


@pytest.fixture(scope="session", autouse=True)
def _remove_fresh_stem_files_this_run_created():
    before = _test_run_files()
    yield
    for path in _test_run_files() - before:
        path.unlink(missing_ok=True)


@pytest.fixture(scope="session", autouse=True)
def _reap_processes_leaked_by_this_run(tmp_path_factory, request):
    """Reap, at session end, every process whose argv names this run's tmp tree.

    A timed-out `subprocess.run` kills only its direct child; what that child
    started is re-parented to PID 1 and keeps running. One leaked
    `hmad-dispatch.sh exec-pane agy` spun for 22 h against a deleted pytest
    tmpdir (docs/skill-candidates.md, "reap LEAKED exec-pane wrapper
    processes"). The run's basetemp is the positive identifier: the suite points
    every wrapper and stub at a tmp_path, and nothing outside the run does.
    Reaped processes are reported, not hidden — each one is a test that leaked.
    """
    from leak_reaper import find_leaked, reap

    yield
    base = tmp_path_factory.getbasetemp()
    markers = sorted({str(base), str(base.resolve())})
    leaked = find_leaked(markers)
    if not leaked:
        return
    reap([pid for pid, _ in leaked])
    reporter = request.config.pluginmanager.get_plugin("terminalreporter")
    lines = [f"[leak-reaper] reaped {len(leaked)} process(es) leaked under {base}:"]
    lines += [f"[leak-reaper]   pid {pid}: {command[:200]}" for pid, command in leaked]
    for line in lines:
        if reporter is not None:
            reporter.write_line(line, yellow=True)
        else:
            print(line)


# --- one measured run per working tree, and a report when the tree moved ------
#
# Rows 1391/2361: two pytest runs over one tree produced 6 and 3 failures in
# DIFFERENT sets, and 0 when the file ran alone; two full suites produced 11
# phantom failures in a file that passes 40/40 alone; a mutation harness ran
# under a full suite and was harmless only by luck. "Never run two suites" was
# prose, so the session now takes the SAME lock the mutation harness takes
# (`tree_lock`, one per git toplevel) and a second session refuses with
# `SUITE: BUSY` and exit `SUITE_BUSY_EXIT`. The harness's own inner pytest is
# exempt through the holder token it exports, or every spec run would refuse
# itself. Separate worktrees are separate toplevels and never contend.
#
# Row 745: the session digests the non-ignored tree at start and end and prints
# `SUITE: TREE_MOVED paths=… n=K` when the two differ — the pass count above it
# describes bytes that no longer exist. It reports; it never refuses an edit.
#
# Hooks rather than a fixture: the refusal must land before collection, and the
# end digest after every session fixture's teardown.
import contextlib
import importlib.util
import sys
import time

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
_SUITE: dict = {}


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
                 "Nothing was measured — wait for the holder. Delete the lock file only "
                 "if you are certain no run is in flight.")
            pytest.exit(line, returncode=gate.SUITE_BUSY_EXIT)
        _SUITE["lock"] = stack
    _SUITE["digest"] = harness.tree_digest(REPO_ROOT)


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session):
    harness = _SUITE.get("harness")
    if harness is not None and "digest" in _SUITE:
        _SUITE["moved"] = harness.moved_paths(_SUITE.pop("digest"),
                                              harness.tree_digest(REPO_ROOT))
    stack = _SUITE.pop("lock", None)
    if stack is not None:
        stack.close()


def pytest_terminal_summary(terminalreporter):
    moved = _SUITE.pop("moved", None)
    if moved:
        shown = ",".join(moved[:10]) + (",…" if len(moved) > 10 else "")
        terminalreporter.write_line(f"SUITE: TREE_MOVED paths={shown} n={len(moved)}",
                                    yellow=True)
