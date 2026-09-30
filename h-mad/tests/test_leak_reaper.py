"""The session-end reaper that closes leaked test subprocesses at the source.

A test that times out kills only its direct child: `subprocess.run(timeout=...)`
signals the wrapper `bash`, and whatever that wrapper started is re-parented to
PID 1 and keeps running. One such `hmad-dispatch.sh exec-pane agy` spun `sleep 1`
for 22 h against a pytest tmpdir that no longer existed (docs/skill-candidates.md,
"reap LEAKED exec-pane wrapper processes"). Every such process names the run's
tmp tree in its argv, which is the positive identifier the reaper keys on.
"""
from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from leak_reaper import find_leaked, reap


def _orphan(marker_dir: Path) -> subprocess.Popen:
    # $0 of the loop is a path under marker_dir, so the marker is in its argv,
    # exactly as a leaked wrapper's --cd / prompt path is.
    script = marker_dir / "leaky wrapper.sh"
    return subprocess.Popen(
        ["bash", "-c", "while :; do sleep 1; done", str(script)],
        start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _gone(pid: int, within: float = 5.0) -> bool:
    deadline = time.monotonic() + within
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.05)
    return False


def test_finds_and_reaps_a_process_rooted_in_the_marker(tmp_path):
    marker = tmp_path / "run-marker"
    marker.mkdir()
    leaked = _orphan(marker)
    try:
        time.sleep(0.2)
        found = find_leaked([str(marker)])
        assert leaked.pid in {pid for pid, _ in found}, found
        assert reap([pid for pid, _ in found]) >= 1
        leaked.wait(timeout=5)
        assert _gone(leaked.pid), "the leaked loop survived the reaper"
    finally:
        if leaked.poll() is None:
            leaked.kill()


def test_ignores_processes_outside_the_marker_and_its_own_ancestry(tmp_path):
    marker = tmp_path / "run-marker"
    marker.mkdir()
    other_dir = tmp_path / "unrelated"
    other_dir.mkdir()
    bystander = _orphan(other_dir)
    try:
        time.sleep(0.2)
        pids = {pid for pid, _ in find_leaked([str(marker)])}
        assert bystander.pid not in pids, "matched a process that does not name the marker"
        assert os.getpid() not in pids and os.getppid() not in pids, "matched its own ancestry"
    finally:
        bystander.kill()
        bystander.wait(timeout=5)


def test_matches_either_spelling_of_a_symlinked_tmp_root(tmp_path):
    # macOS: /var -> /private/var. A process may carry either spelling.
    marker = tmp_path / "run-marker"
    marker.mkdir()
    leaked = _orphan(marker)
    try:
        time.sleep(0.2)
        other = str(marker.resolve())
        spellings = [str(marker)] if other == str(marker) else [str(marker), other]
        assert leaked.pid in {pid for pid, _ in find_leaked(spellings)}
    finally:
        leaked.kill()
        leaked.wait(timeout=5)


def test_conftest_finalizer_reaps_a_leak_at_session_end(tmp_path):
    """End to end: a child pytest session whose test leaves an orphan behind.
    The session-end fixture in conftest.py must report it and kill it."""
    import shutil
    import sys

    here = Path(__file__).resolve().parent
    suite = tmp_path / "suite"
    suite.mkdir()
    for name in ("conftest.py", "leak_reaper.py"):
        shutil.copy(here / name, suite / name)
    pidfile = tmp_path / "orphan.pid"
    (suite / "test_leaks.py").write_text(
        "import subprocess\n"
        "def test_leaks(tmp_path):\n"
        "    p = subprocess.Popen(['bash', '-c', 'while :; do sleep 1; done', str(tmp_path / 'w.sh')],\n"
        "                         start_new_session=True)\n"
        f"    open({str(pidfile)!r}, 'w').write(str(p.pid))\n",
        encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(suite),
         "--basetemp", str(tmp_path / "bt")],
        capture_output=True, text=True, cwd=suite, timeout=120, check=False)
    pid = int(pidfile.read_text())
    try:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "[leak-reaper] reaped 1 process(es)" in result.stdout, result.stdout
        assert f"pid {pid}:" in result.stdout, result.stdout
        assert _gone(pid), "the conftest finalizer did not reap the leaked orphan"
    finally:
        if not _gone(pid, within=0.1):
            os.kill(pid, 9)


def test_never_matches_its_own_process_or_an_ancestor_that_names_the_marker(tmp_path):
    """The run's own pytest can carry the basetemp in argv (e.g. --basetemp).
    A caller whose parent AND self both name the marker must match neither."""
    import sys

    marker = tmp_path / "run-marker"
    marker.mkdir()
    here = Path(__file__).resolve().parent
    probe = ("import sys; sys.path.insert(0, sys.argv[1]); from leak_reaper import find_leaked; "
             "import os; print(os.getpid(), os.getppid()); "
             "print(' '.join(str(p) for p, _ in find_leaked([sys.argv[2]])))")
    # bash (argv names the marker) -> python (argv names the marker) -> find_leaked
    result = subprocess.run(
        ["bash", "-c", 'exec 3>&1; "$1" -c "$2" "$3" "$4"; :', str(marker / "parent.sh"),
         sys.executable, probe, str(here), str(marker)],
        capture_output=True, text=True, timeout=60, check=True)
    ids, found = result.stdout.splitlines()[0].split(), result.stdout.splitlines()[1].split()
    self_pid, parent_pid = ids
    assert self_pid not in found, f"matched its own process: {result.stdout}"
    assert parent_pid not in found, f"matched its own marker-carrying parent: {result.stdout}"
