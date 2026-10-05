"""A throwaway repository carrying the LIVE conftest, for the suite-lock tests.

`h-mad/tests/conftest.py` takes the working-tree lock and digests the tree for
the whole pytest session, so the only honest way to test it is to run a real
second session over a real git toplevel. Each tree is a scratch repo holding
copies of the live conftest and the two scripts it loads, plus one probe test
whose behaviour is steered by environment variables.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

LIVE = Path(__file__).resolve().parents[2]
SCRIPTS = LIVE / "h-mad" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from h_mad_mutation_harness import _lock_path  # noqa: E402

# The contract the harness exports to its children, pinned here as a literal.
HOLDER_ENV = "H_MAD_TREE_LOCK_HELD"


def busy_exit() -> int:
    from h_mad_audit_gate import SUITE_BUSY_EXIT
    return SUITE_BUSY_EXIT

PROBE = '''\
import os, pathlib, time
ROOT = pathlib.Path(__file__).resolve().parents[2]

def test_probe():
    gate = os.environ.get("PROBE_WAIT_FOR")
    if gate:
        deadline = time.time() + 60
        while not pathlib.Path(gate).exists() and time.time() < deadline:
            time.sleep(0.05)
    for rel in filter(None, os.environ.get("PROBE_WRITE", "").split(",")):
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        before = path.read_bytes() if path.exists() else None
        path.write_text("written mid-session\\n")
        if os.environ.get("PROBE_REVERT"):
            if before is None:
                path.unlink()
            else:
                path.write_bytes(before)
'''


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True,
                          capture_output=True, text=True).stdout.strip()


def make_tree(base: Path, name: str = "repo") -> Path:
    """A committed repo whose h-mad/tests/conftest.py is the live one."""
    root = base / name
    (root / "h-mad" / "tests").mkdir(parents=True)
    (root / "h-mad" / "scripts").mkdir(parents=True)
    for part, files in (("tests", ("conftest.py", "leak_reaper.py", "tree_lock_plugin.py")),
                        ("scripts", ("h_mad_mutation_harness.py", "h_mad_audit_gate.py"))):
        for file in files:
            if (LIVE / "h-mad" / part / file).is_file():
                shutil.copy(LIVE / "h-mad" / part / file, root / "h-mad" / part / file)
    # The live ignore rules, the live root conftest and the live pytest.ini (its
    # exact `testpaths`), so every entry point is measured against the files the
    # real suite runs under rather than against ones written for the test.
    shutil.copy(LIVE / ".gitignore", root / ".gitignore")
    shutil.copy(LIVE / "pytest.ini", root / "pytest.ini")
    if (LIVE / "conftest.py").is_file():
        shutil.copy(LIVE / "conftest.py", root / "conftest.py")
    (root / "notes.txt").write_text("tracked\n", encoding="utf-8")
    (root / "h-mad" / "tests" / "test_probe.py").write_text(PROBE, encoding="utf-8")
    for probe in ("handoff/tests/test_handoff_probe.py", "handoff/scripts/test_script_probe.py"):
        (root / probe).parent.mkdir(parents=True, exist_ok=True)
        (root / probe).write_text(PROBE, encoding="utf-8")
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@t")
    git(root, "config", "user.name", "t")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "seed")
    return Path(git(root, "rev-parse", "--show-toplevel"))


def session_env(*, keep_holder: bool = False, **extra: str) -> dict[str, str]:
    """The current environment, minus the outer suite's own holder token unless kept."""
    env = dict(os.environ)
    if not keep_holder:
        env.pop(HOLDER_ENV, None)
    env.update(extra)
    return env


def session_argv(root: Path, basetemp: Path, *args: str) -> list[str]:
    return [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
            "--basetemp", str(basetemp), *(args or ("h-mad/tests/test_probe.py",))]


def run_session(root: Path, basetemp: Path, env: dict[str, str] | None = None,
                *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(session_argv(root, basetemp, *args), cwd=cwd or root,
                          env=env if env is not None else session_env(),
                          capture_output=True, text=True, timeout=180)


def start_blocking_session(root: Path, basetemp: Path, release: Path,
                           preexec_fn=None) -> subprocess.Popen:
    """A session that holds the tree until `release` exists. Returns once it holds it."""
    proc = subprocess.Popen(session_argv(root, basetemp), cwd=root,
                            env=session_env(PROBE_WAIT_FOR=str(release)),
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                            preexec_fn=preexec_fn)
    lock = _lock_path(root)
    deadline = time.time() + 60
    while time.time() < deadline:
        if lock.is_file():
            try:
                if json.loads(lock.read_text(encoding="utf-8")).get("pid") == proc.pid:
                    return proc
            except ValueError:
                pass
        if proc.poll() is not None:
            raise AssertionError(f"the holding session exited early: {proc.stdout.read()}")
        time.sleep(0.05)
    proc.kill()
    raise AssertionError("the holding session never took the tree lock")


def finish(proc: subprocess.Popen, release: Path) -> str:
    release.write_text("go", encoding="utf-8")
    out, _ = proc.communicate(timeout=120)
    return out


def write_holder(root: Path, pid, spec: str = "pytest-session") -> Path:
    lock = _lock_path(root)
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(json.dumps({"pid": pid, "spec": spec, "root": str(root),
                                "started": time.time()}), encoding="utf-8")
    return lock


def dead_pid() -> int:
    from h_mad_mutation_harness import _process_alive
    for candidate in range(999_999, 900_000, -1):
        if not _process_alive(candidate):
            return candidate
    raise AssertionError("could not find a dead pid to test with")
