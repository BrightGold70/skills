"""Row 2364 — a failure SET diffed against a clean control, in one command.

A suite failure on a branch has two readings with opposite consequences: the
change caused it, or the tree it runs on fails that way anyway. Seven sessions
settled it by hand — `git worktree add --detach <scratch> <base>`, rerun, diff
the FAILED node ids — and on 10-05 `test_hmad_dispatch_audit_cycle.py` needed it
again, because main failed the same 1-3 tests under load.

What these tests pin:
  * the three-way split: failures only on the subject (the change), on both
    (pre-existing or environmental), only on the control (fixed);
  * a test that fails in SOME runs of a side is FLAKY, listed apart, and never
    lands in any of the three attributed sets;
  * fail closed: a crash, a collection error, a refused (`SUITE: BUSY`) session,
    a missing summary or a FAILED count that disagrees with it is UNREADABLE,
    never "no new failures";
  * the control worktree is gone afterwards on every path, and it is a separate
    git toplevel, so it takes its own tree lock and never contends with the
    subject's.
"""

import json
import os
import select
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "h_mad_failure_diff.py"

SUMMARY_HEADER = "=========================== short test summary info ============================"


# --- helpers ----------------------------------------------------------------

def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True,
    ).stdout.strip()


def _commit_all(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=t@e.com", "-c", "user.name=T", "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _write(repo: Path, rel: str, text: str) -> None:
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


PASSING = "def test_ok():\n    assert True\n"
FAILING = "def test_broken():\n    assert 0, 'deliberate'\n"
# Fails on the 1st, 3rd, ... run in ITS OWN directory, passes on the 2nd, 4th:
# a deliberate flake whose schedule is per tree, so the subject and the control
# keep separate counts.
FLAKY = """\
import hashlib, os, pathlib

def test_flaky():
    here = str(pathlib.Path(__file__).resolve().parent)
    counter = pathlib.Path(os.environ["FD_COUNTER_DIR"]) / hashlib.sha1(here.encode()).hexdigest()
    n = int(counter.read_text()) + 1 if counter.exists() else 1
    counter.write_text(str(n))
    assert n % 2 == 0, f"flaky run {n}"
"""
# A tiny conftest that takes the REAL tree lock the h-mad suite takes, the same
# way, and refuses with the same `SUITE: BUSY` line and exit code.
LOCKING_CONFTEST = """\
import contextlib, os, sys
from pathlib import Path
import pytest
sys.path.insert(0, os.environ["FD_SCRIPTS"])
import h_mad_audit_gate as gate
import h_mad_mutation_harness as harness

ROOT = Path(__file__).resolve().parent
_S = {}

def pytest_sessionstart(session):
    if harness.held_by_an_enclosing_run(ROOT):
        return
    stack = contextlib.ExitStack()
    try:
        path = stack.enter_context(harness.tree_lock(ROOT, "pytest-session"))
    except harness.TreeBusy as busy:
        line = f"SUITE: BUSY holder={busy.holder.get('pid')} age=0s what=x lock={busy.holder.get('lock')}"
        print(line, flush=True)
        pytest.exit(line, returncode=gate.SUITE_BUSY_EXIT)
    log = os.environ.get("FD_LOCK_LOG")
    if log:
        with open(log, "a") as fh:
            fh.write(f"{path}\\n")
    _S["stack"] = stack

def pytest_sessionfinish(session):
    stack = _S.pop("stack", None)
    if stack is not None:
        stack.close()
"""


def _repo(tmp_path: Path, base_files: dict, subject_files: dict,
          subject_removes: tuple = ()) -> Path:
    """`main` holds `base_files`; branch `feature` adds/overwrites `subject_files`."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _write(repo, ".gitignore", ".h-mad/\n__pycache__/\n")
    for rel, text in base_files.items():
        _write(repo, rel, text)
    _commit_all(repo, "base")
    _git(repo, "checkout", "-q", "-b", "feature")
    for rel, text in subject_files.items():
        _write(repo, rel, text)
    for rel in subject_removes:
        (repo / rel).unlink()
    _commit_all(repo, "change")
    return repo


def _env(tmp_path: Path, **extra: str) -> dict:
    counters = tmp_path / "counters"
    counters.mkdir(exist_ok=True)
    # The tool keeps each run's log under the temp dir; keep it inside this test.
    (tmp_path / "tmp").mkdir(exist_ok=True)
    return {**os.environ, "FD_COUNTER_DIR": str(counters), "FD_SCRIPTS": str(SCRIPTS),
            "TMPDIR": str(tmp_path / "tmp"), **extra}


def _diff_run(repo: Path, tmp_path: Path, *selection: str, repeat: int = 1,
              python: str = sys.executable, env: dict | None = None,
              base: str = "main", extra: tuple = (),
              subject: str | None = None) -> subprocess.CompletedProcess:
    parent = tmp_path / "controls"
    parent.mkdir(exist_ok=True)
    return subprocess.run(
        [sys.executable, str(SCRIPT), "run", "--subject", subject or str(repo),
         "--base", base, "--repeat", str(repeat), "--python", python,
         "--control-parent", str(parent), *extra, "--", *selection],
        capture_output=True, text=True, env=env or _env(tmp_path), timeout=300,
    )


def _token(out: str) -> str:
    lines = [line for line in out.splitlines() if line.strip()]
    assert lines, "no output"
    return lines[-1]


def _fields(token: str) -> dict:
    return dict(part.split("=", 1) for part in token.split()[2:] if "=" in part)


def _tagged(out: str, tag: str) -> list[str]:
    return [line[len(tag) + 1:].split(" subject=")[0]
            for line in out.splitlines() if line.startswith(tag + " ")]


def _no_control_left(repo: Path, tmp_path: Path) -> None:
    worktrees = [line for line in _git(repo, "worktree", "list", "--porcelain").splitlines()
                 if line.startswith("worktree ")]
    assert len(worktrees) == 1, worktrees
    parent = tmp_path / "controls"
    assert not parent.exists() or list(parent.iterdir()) == [], list(parent.iterdir())


def _log(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def _logs(tmp_path: Path, run: str, control: str, control_name: str = "control.log"):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "logs",
         "--run", str(_log(tmp_path, "run.log", run)),
         "--control", str(_log(tmp_path, control_name, control))],
        capture_output=True, text=True, timeout=60,
    )


def _pytest_log(failed: list[str], passed: int = 5, errors: list[str] = ()) -> str:
    lines = ["." * passed + "F" * len(failed)]
    if failed or errors:
        lines.append(SUMMARY_HEADER)
        lines += [f"FAILED {node} - AssertionError: boom" for node in failed]
        lines += [f"ERROR {node} - RuntimeError: setup" for node in errors]
    counts = [f"{len(failed)} failed"] if failed else []
    counts.append(f"{passed} passed")
    if errors:
        counts.append(f"{len(errors)} errors")
    lines.append(", ".join(counts) + " in 1.23s")
    return "\n".join(lines) + "\n"


# --- logs mode: two existing readings ---------------------------------------

def test_same_set_reads_SAME_exit0(tmp_path):
    ids = ["tests/test_a.py::test_one", "tests/test_b.py::test_two"]
    r = _logs(tmp_path, _pytest_log(ids), _pytest_log(list(reversed(ids))))
    token = _token(r.stdout)
    assert token.startswith("FAILDIFF: SAME "), r.stdout
    assert _fields(token)["both"] == "2" and _fields(token)["subject_only"] == "0"
    assert r.returncode == 0, r.stdout + r.stderr


def test_new_failure_named_exit1(tmp_path):
    shared = "tests/test_a.py::test_one"
    new = "tests/test_c.py::test_three"
    r = _logs(tmp_path, _pytest_log([shared, new]), _pytest_log([shared]))
    token = _token(r.stdout)
    assert token.startswith("FAILDIFF: NEW "), r.stdout
    assert _fields(token)["subject_only"] == "1"
    assert _tagged(r.stdout, "SUBJECT_ONLY") == [new]
    assert _tagged(r.stdout, "BOTH") == [shared]
    assert r.returncode == 1, r.stdout + r.stderr


def test_fixed_only_is_informational_exit0(tmp_path):
    shared = "tests/test_a.py::test_one"
    fixed = "tests/test_d.py::test_four"
    r = _logs(tmp_path, _pytest_log([shared]), _pytest_log([shared, fixed]))
    token = _token(r.stdout)
    assert token.startswith("FAILDIFF: FIXED_ONLY "), r.stdout
    assert _tagged(r.stdout, "CONTROL_ONLY") == [fixed]
    assert r.returncode == 0, r.stdout + r.stderr


def test_no_summary_line_is_UNREADABLE_not_SAME(tmp_path):
    # A killed run: progress dots and a FAILED line, but pytest never got to the
    # summary. Its FAILED set is a prefix of the truth, not the truth.
    truncated = "..F\n" + SUMMARY_HEADER + "\nFAILED tests/test_a.py::test_one - x\n"
    r = _logs(tmp_path, truncated, _pytest_log(["tests/test_a.py::test_one"]))
    assert _token(r.stdout) == "FAILDIFF: UNREADABLE reason=no-summary side=run", r.stdout
    assert r.returncode == 2, r.stdout + r.stderr


def test_interrupted_or_collection_error_is_UNREADABLE(tmp_path):
    interrupted = (
        SUMMARY_HEADER + "\n"
        "ERROR tests/test_a.py - SyntaxError: invalid syntax\n"
        "!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!\n"
        "1 error in 0.12s\n"
    )
    r = _logs(tmp_path, _pytest_log([]), interrupted)
    assert _token(r.stdout) == "FAILDIFF: UNREADABLE reason=collection-error side=control", r.stdout
    assert r.returncode == 2, r.stdout + r.stderr


def test_failed_lines_disagree_with_summary_count(tmp_path):
    # Summary says 2 failed, one FAILED line survived: the set is incomplete.
    short = _pytest_log(["tests/test_a.py::test_one", "tests/test_b.py::test_two"])
    short = short.replace("FAILED tests/test_b.py::test_two - AssertionError: boom\n", "")
    r = _logs(tmp_path, short, _pytest_log(["tests/test_a.py::test_one"]))
    assert _token(r.stdout) == "FAILDIFF: UNREADABLE reason=count-mismatch side=run", r.stdout
    assert r.returncode == 2, r.stdout + r.stderr


def test_failed_text_in_captured_output_is_not_a_failure(tmp_path):
    # A test that prints a pytest log of its own puts `FAILED <id>` lines in the
    # FAILURES section. Only the short test summary names this run's failures.
    noisy = (
        "F.\n=================================== FAILURES ===================================\n"
        "----------------------------- Captured stdout call -----------------------------\n"
        "FAILED tests/inner.py::test_not_ours - printed by a test\n"
        + SUMMARY_HEADER + "\n"
        "FAILED tests/test_a.py::test_one - assert 0\n"
        "1 failed, 1 passed in 0.10s\n"
    )
    r = _logs(tmp_path, noisy, _pytest_log(["tests/test_a.py::test_one"]))
    token = _token(r.stdout)
    assert token.startswith("FAILDIFF: SAME "), r.stdout
    assert "tests/inner.py::test_not_ours" not in r.stdout


def test_disjoint_id_sets_refused_as_root_mismatch(tmp_path):
    # Same failures collected from two different roots: no id in common.
    r = _logs(tmp_path, _pytest_log(["h-mad/tests/test_a.py::test_one"]),
              _pytest_log(["tests/test_a.py::test_one"]))
    assert _token(r.stdout) == "FAILDIFF: UNREADABLE reason=disjoint-ids side=both", r.stdout
    assert r.returncode == 2, r.stdout + r.stderr


def test_id_list_control_file(tmp_path):
    ids = ["tests/test_a.py::test_one", "tests/test_b.py::test_p[x y-1]"]
    id_list = "# baseline_failures.txt\n" + "\n".join(ids) + "\n\n"
    r = _logs(tmp_path, _pytest_log(ids + ["tests/test_c.py::test_new"]), id_list,
              control_name="baseline_failures.txt")
    token = _token(r.stdout)
    assert token.startswith("FAILDIFF: NEW "), r.stdout
    assert _tagged(r.stdout, "SUBJECT_ONLY") == ["tests/test_c.py::test_new"]
    assert sorted(_tagged(r.stdout, "BOTH")) == sorted(ids)


def test_parametrized_ids_with_brackets_and_spaces(tmp_path):
    ids = ["tests/test_p.py::test_p[a b]", "tests/test_p.py::test_p[c]d]",
           "tests/test_p.py::test_p[x - y]"]
    run = "FFF\n" + SUMMARY_HEADER + "\n" + "".join(
        f"FAILED {node} - AssertionError: [1] - x\n" for node in ids) + "3 failed in 0.01s\n"
    r = _logs(tmp_path, run, "\n".join(ids[:2]) + "\n")
    assert _tagged(r.stdout, "SUBJECT_ONLY") == ["tests/test_p.py::test_p[x - y]"], r.stdout
    assert sorted(_tagged(r.stdout, "BOTH")) == sorted(ids[:2])


# --- run mode: subject vs a throwaway control worktree ----------------------

def test_run_names_a_failure_only_the_subject_has(tmp_path):
    repo = _repo(tmp_path, {"tests/test_ok.py": PASSING},
                 {"tests/test_new.py": FAILING})
    r = _diff_run(repo, tmp_path, "tests")
    token = _token(r.stdout)
    assert token.startswith("FAILDIFF: NEW "), r.stdout + r.stderr
    assert _tagged(r.stdout, "SUBJECT_ONLY") == ["tests/test_new.py::test_broken"]
    assert r.returncode == 1, r.stdout + r.stderr
    _no_control_left(repo, tmp_path)


def test_run_failure_on_both_sides_is_preexisting_not_new(tmp_path):
    repo = _repo(tmp_path, {"tests/test_old.py": FAILING},
                 {"tests/test_ok.py": PASSING})
    r = _diff_run(repo, tmp_path, "tests")
    token = _token(r.stdout)
    assert token.startswith("FAILDIFF: SAME "), r.stdout + r.stderr
    fields = _fields(token)
    assert (fields["subject_only"], fields["both"], fields["control_only"],
            fields["flaky"]) == ("0", "1", "0", "0")
    assert _tagged(r.stdout, "BOTH") == ["tests/test_old.py::test_broken"]
    assert r.returncode == 0, r.stdout + r.stderr


def test_run_control_only_failure_is_FIXED_ONLY(tmp_path):
    repo = _repo(tmp_path, {"tests/test_fix.py": FAILING},
                 {"tests/test_fix.py": "def test_broken():\n    assert True\n"})
    r = _diff_run(repo, tmp_path, "tests")
    assert _token(r.stdout).startswith("FAILDIFF: FIXED_ONLY "), r.stdout + r.stderr
    assert _tagged(r.stdout, "CONTROL_ONLY") == ["tests/test_fix.py::test_broken"]


def test_repeat_flaky_test_is_FLAKY_never_attributed(tmp_path):
    # The change adds a test that fails on run 1 and passes on run 2. Reading
    # run 1 alone would call it a new failure; it is neither new nor fixed.
    repo = _repo(tmp_path, {"tests/test_ok.py": PASSING},
                 {"tests/test_flaky.py": FLAKY})
    r = _diff_run(repo, tmp_path, "tests", repeat=2)
    token = _token(r.stdout)
    assert token.startswith("FAILDIFF: FLAKY "), r.stdout + r.stderr
    assert _fields(token)["subject_only"] == "0" and _fields(token)["flaky"] == "1"
    assert _tagged(r.stdout, "FLAKY") == ["tests/test_flaky.py::test_flaky"]
    assert _tagged(r.stdout, "SUBJECT_ONLY") == []
    assert "subject=1/2 control=0/2" in r.stdout
    assert r.returncode == 3, r.stdout + r.stderr
    _no_control_left(repo, tmp_path)


def test_flaky_on_both_sides_beside_a_real_new_failure(tmp_path):
    # A flake the base already has is still not attributed, and it does not hide
    # a real new failure next to it.
    repo = _repo(tmp_path, {"tests/test_flaky.py": FLAKY},
                 {"tests/test_new.py": FAILING})
    r = _diff_run(repo, tmp_path, "tests", repeat=2)
    token = _token(r.stdout)
    assert token.startswith("FAILDIFF: NEW "), r.stdout + r.stderr
    assert _tagged(r.stdout, "SUBJECT_ONLY") == ["tests/test_new.py::test_broken"]
    assert _tagged(r.stdout, "FLAKY") == ["tests/test_flaky.py::test_flaky"]
    assert _tagged(r.stdout, "BOTH") == []


def test_crashed_run_is_UNREADABLE_and_control_removed(tmp_path):
    crash = "import os, signal\n\ndef test_dies():\n    os.kill(os.getpid(), signal.SIGKILL)\n"
    repo = _repo(tmp_path, {"tests/test_ok.py": PASSING}, {"tests/test_crash.py": crash})
    r = _diff_run(repo, tmp_path, "tests")
    token = _token(r.stdout)
    assert token.startswith("FAILDIFF: UNREADABLE reason=crashed side=subject "), r.stdout
    assert r.returncode == 2, r.stdout + r.stderr
    _no_control_left(repo, tmp_path)


def test_unlaunchable_runner_is_UNREADABLE_and_control_removed(tmp_path):
    repo = _repo(tmp_path, {"tests/test_ok.py": PASSING}, {"tests/test_new.py": FAILING})
    r = _diff_run(repo, tmp_path, "tests", python=str(tmp_path / "no-such-python"))
    assert _token(r.stdout).startswith("FAILDIFF: UNREADABLE reason=launch-failed "), r.stdout
    _no_control_left(repo, tmp_path)


def test_collection_error_on_subject_is_UNREADABLE(tmp_path):
    repo = _repo(tmp_path, {"tests/test_ok.py": PASSING},
                 {"tests/test_bad.py": "def test_x(:\n    pass\n"})
    r = _diff_run(repo, tmp_path, "tests")
    assert _token(r.stdout).startswith(
        "FAILDIFF: UNREADABLE reason=collection-error side=subject "), r.stdout
    _no_control_left(repo, tmp_path)


def test_bad_base_ref_is_UNREADABLE(tmp_path):
    repo = _repo(tmp_path, {"tests/test_ok.py": PASSING}, {"tests/test_new.py": FAILING})
    r = _diff_run(repo, tmp_path, "tests", base="no-such-ref")
    assert _token(r.stdout) == "FAILDIFF: UNREADABLE reason=bad-base side=control", r.stdout
    assert r.returncode == 2, r.stdout + r.stderr
    _no_control_left(repo, tmp_path)


def test_suite_busy_on_subject_is_UNREADABLE_not_a_result(tmp_path):
    # Another live run holds the subject's tree lock. The refused session
    # measured nothing; it must not read as SAME (no failures) or as NEW.
    repo = _repo(tmp_path, {"conftest.py": LOCKING_CONFTEST, "tests/test_ok.py": PASSING},
                 {"tests/test_new.py": FAILING})
    holder = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
    try:
        lock = repo / ".h-mad" / "mutation.lock"
        lock.parent.mkdir()
        lock.write_text(json.dumps({"pid": holder.pid, "spec": "foreign-suite",
                                    "started": time.time()}))
        r = _diff_run(repo, tmp_path, "tests")
    finally:
        holder.kill()
        holder.wait()
    assert _token(r.stdout).startswith(
        "FAILDIFF: UNREADABLE reason=suite-busy side=subject "), r.stdout + r.stderr
    assert r.returncode == 2, r.stdout + r.stderr
    _no_control_left(repo, tmp_path)


def test_control_takes_its_own_tree_lock(tmp_path):
    # The control is its own git toplevel: its session locks ITS tree, not the
    # subject's, so a control never waits on (or blocks) the subject.
    repo = _repo(tmp_path, {"conftest.py": LOCKING_CONFTEST, "tests/test_ok.py": PASSING},
                 {"tests/test_new.py": FAILING})
    lock_log = tmp_path / "locks.log"
    r = _diff_run(repo, tmp_path, "tests", env=_env(tmp_path, FD_LOCK_LOG=str(lock_log)))
    assert _token(r.stdout).startswith("FAILDIFF: NEW "), r.stdout + r.stderr
    taken = lock_log.read_text().split()
    assert len(taken) == 2, taken
    subject_lock, control_lock = (Path(p).resolve() for p in taken)
    assert subject_lock == (repo / ".h-mad" / "mutation.lock").resolve()
    assert control_lock != subject_lock
    assert str(control_lock).startswith(str((tmp_path / "controls").resolve()))
    _no_control_left(repo, tmp_path)


def test_removal_touches_only_its_own_worktree_entry(tmp_path):
    # Another session's worktree whose directory is absent right now (an
    # unmounted volume, a sibling mid-move) must keep its registration: cleanup
    # deletes this run's entry, never by a repo-wide `git worktree prune`.
    repo = _repo(tmp_path, {"tests/test_ok.py": PASSING}, {"tests/test_new.py": FAILING})
    other = tmp_path / "someone-elses-worktree"
    _git(repo, "worktree", "add", "--detach", "--quiet", str(other), "main")
    for path in sorted(other.rglob("*"), reverse=True):
        path.unlink() if path.is_file() or path.is_symlink() else path.rmdir()
    other.rmdir()
    r = _diff_run(repo, tmp_path, "tests")
    assert _token(r.stdout).startswith("FAILDIFF: NEW "), r.stdout + r.stderr
    listed = _git(repo, "worktree", "list", "--porcelain")
    assert f"worktree {other}" in listed.splitlines() or \
        f"worktree {other.resolve()}" in listed.splitlines(), listed
    assert ".h-mad-control-" not in listed, listed


def test_sigterm_mid_run_removes_the_control(tmp_path):
    slow = "import time\n\ndef test_slow():\n    time.sleep(60)\n"
    repo = _repo(tmp_path, {"tests/test_slow.py": slow}, {"tests/test_new.py": FAILING})
    parent = tmp_path / "controls"
    parent.mkdir()
    proc = subprocess.Popen(
        [sys.executable, str(SCRIPT), "run", "--subject", str(repo), "--base", "main",
         "--control-parent", str(parent), "--", "tests"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=_env(tmp_path))
    try:
        deadline = time.time() + 30
        while time.time() < deadline and not any(parent.glob(".h-mad-control-*/tests")):
            time.sleep(0.1)
        assert any(parent.glob(".h-mad-control-*/tests")), "control never appeared"
        time.sleep(1)
        proc.terminate()
        out, err = proc.communicate(timeout=60)
    finally:
        proc.kill()
    assert _token(out) == "FAILDIFF: UNREADABLE reason=interrupted side=both", out + err
    _no_control_left(repo, tmp_path)


def test_exit_code_disagreeing_with_summary_is_UNREADABLE(tmp_path):
    # The session failed (exit 1) while the summary lists no failure: something
    # outside the tests went wrong, and an empty set would read as "no failures".
    forced = "def pytest_sessionfinish(session):\n    session.exitstatus = 1\n"
    repo = _repo(tmp_path, {"conftest.py": forced, "tests/test_ok.py": PASSING},
                 {"tests/test_more.py": PASSING.replace("test_ok", "test_more")})
    r = _diff_run(repo, tmp_path, "tests")
    assert _token(r.stdout).startswith(
        "FAILDIFF: UNREADABLE reason=count-mismatch side=subject "), r.stdout
    _no_control_left(repo, tmp_path)


def test_usage_error_is_UNREADABLE_by_its_exit(tmp_path):
    repo = _repo(tmp_path, {"tests/test_ok.py": PASSING}, {"tests/test_new.py": FAILING})
    r = _diff_run(repo, tmp_path, "--no-such-pytest-flag", "tests")
    assert _token(r.stdout).startswith(
        "FAILDIFF: UNREADABLE reason=usage-error side=subject "), r.stdout
    _no_control_left(repo, tmp_path)


# --- review of 8d2901be: findings M1-M4, S1-S6, N2-N4 -------------------------

SETUP_ERROR = """\
import pytest

@pytest.fixture
def broken():
    raise RuntimeError("fixture broke")

def test_k(broken):
    pass
"""


def test_exit_first_selection_is_UNREADABLE_stopped_early(tmp_path):
    # M1: `-x` stops at the first failure on BOTH sides, so each set is a prefix
    # and the new failure behind it is never reached. Read as SAME, it hides it.
    repo = _repo(tmp_path, {"tests/test_a.py": FAILING.replace("test_broken", "test_old")},
                 {"tests/test_b.py": FAILING.replace("test_broken", "test_new")})
    r = _diff_run(repo, tmp_path, "-x", "tests")
    assert _token(r.stdout).startswith(
        "FAILDIFF: UNREADABLE reason=stopped-early side=subject "), r.stdout + r.stderr
    assert r.returncode == 2, r.stdout + r.stderr
    _no_control_left(repo, tmp_path)


def test_stopped_early_log_is_UNREADABLE(tmp_path):
    stopped = (
        "F\n" + SUMMARY_HEADER + "\n"
        "FAILED tests/test_a.py::test_one - assert 0\n"
        "!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
        "1 failed in 0.01s\n"
    )
    r = _logs(tmp_path, stopped, _pytest_log(["tests/test_a.py::test_one"]))
    assert _token(r.stdout) == "FAILDIFF: UNREADABLE reason=stopped-early side=run", r.stdout


def test_signal_during_cleanup_still_removes_control_and_ends_on_token(tmp_path):
    # M2: a SIGTERM that lands while the control is being removed must neither
    # leak the control nor leave a traceback as the last line.
    repo = _repo(tmp_path, {"tests/test_ok.py": PASSING}, {"tests/test_new.py": FAILING})
    parent = tmp_path / "controls"
    parent.mkdir()
    driver = (
        "import os, signal, sys\n"
        f"sys.path.insert(0, {str(SCRIPTS)!r})\n"
        "import h_mad_failure_diff as m\n"
        "original = m._remove_control\n"
        "def interrupted(*a):\n"
        "    os.kill(os.getpid(), signal.SIGTERM)\n"
        "    return original(*a)\n"
        "m._remove_control = interrupted\n"
        f"sys.exit(m.main(['run', '--subject', {str(repo)!r}, '--base', 'main',"
        f" '--control-parent', {str(parent)!r}, '--', 'tests']))\n"
    )
    r = subprocess.run([sys.executable, "-c", driver], capture_output=True, text=True,
                       env=_env(tmp_path), timeout=120)
    assert "Traceback" not in r.stdout + r.stderr, r.stdout + r.stderr
    assert _token(r.stdout).startswith("FAILDIFF: "), r.stdout + r.stderr
    _no_control_left(repo, tmp_path)


PKG_TEST = "import pkg\n\ndef test_val():\n    assert pkg.VALUE == 1\n"


def test_absolute_pythonpath_into_subject_is_rewritten_for_control(tmp_path):
    # M3: an exported absolute PYTHONPATH into the subject would make the
    # control import the SUBJECT's code; both sides then agree, and agree wrongly.
    repo = _repo(tmp_path, {"src/pkg/__init__.py": "VALUE = 1\n", "tests/test_v.py": PKG_TEST},
                 {"src/pkg/__init__.py": "VALUE = 2\n"})
    r = _diff_run(repo, tmp_path, "tests",
                  env=_env(tmp_path, PYTHONPATH=str(repo.resolve() / "src")))
    assert _token(r.stdout).startswith("FAILDIFF: NEW "), r.stdout + r.stderr
    assert _tagged(r.stdout, "SUBJECT_ONLY") == ["tests/test_v.py::test_val"]
    _no_control_left(repo, tmp_path)


def test_control_importing_subject_code_is_UNREADABLE(tmp_path):
    # M3: a .pth file (the shape of an editable install) puts the subject on the
    # control's sys.path where no environment rewrite can reach it.
    repo = _repo(tmp_path, {"src/pkg/__init__.py": "VALUE = 1\n", "tests/test_v.py": PKG_TEST},
                 {"src/pkg/__init__.py": "VALUE = 2\n"})
    env = _env(tmp_path, PYTHONUSERBASE=str(tmp_path / "userbase"))
    site_dir = subprocess.run(
        [sys.executable, "-c", "import site; print(site.getusersitepackages())"],
        capture_output=True, text=True, env=env, check=True).stdout.strip()
    Path(site_dir).mkdir(parents=True)
    (Path(site_dir) / "subject_editable.pth").write_text(f"{repo.resolve() / 'src'}\n")
    r = _diff_run(repo, tmp_path, "tests", env=env)
    assert _token(r.stdout).startswith(
        "FAILDIFF: UNREADABLE reason=control-imports-subject side=control"), r.stdout + r.stderr
    assert r.returncode == 2, r.stdout + r.stderr
    _no_control_left(repo, tmp_path)


def test_setup_error_only_on_subject_is_SUBJECT_ONLY(tmp_path):
    # M4: a change that breaks a fixture makes a test ERROR, not FAIL. It is the
    # change's failure all the same and must never be dropped.
    repo = _repo(tmp_path, {"tests/test_ok.py": PASSING}, {"tests/test_e.py": SETUP_ERROR})
    r = _diff_run(repo, tmp_path, "tests")
    assert _token(r.stdout).startswith("FAILDIFF: NEW "), r.stdout + r.stderr
    assert _tagged(r.stdout, "SUBJECT_ONLY") == ["tests/test_e.py::test_k"]
    _no_control_left(repo, tmp_path)


ORDER_CONFTEST = """\
import os, time
from pathlib import Path

def _note(what):
    log = os.environ.get("FD_ORDER_LOG")
    if log:
        with open(log, "a") as fh:
            fh.write(f"{Path(__file__).resolve().parent} {what} {time.time()}\\n")

def pytest_sessionstart(session):
    _note("start")

def pytest_sessionfinish(session):
    _note("end")
"""
SLOW_PASS = "import time\n\ndef test_slow():\n    time.sleep(0.5)\n"


def test_sides_run_serially_never_overlapping(tmp_path):
    # S1: the h-mad conftest sweeps shared /tmp files at session end, so two
    # sessions at once race even on separate toplevels. Sides must not overlap.
    repo = _repo(tmp_path, {"conftest.py": ORDER_CONFTEST, "tests/test_slow.py": SLOW_PASS},
                 {"tests/test_new.py": FAILING})
    log = tmp_path / "order.log"
    r = _diff_run(repo, tmp_path, "tests", repeat=2,
                  env=_env(tmp_path, FD_ORDER_LOG=str(log)))
    assert _token(r.stdout).startswith("FAILDIFF: NEW "), r.stdout + r.stderr
    events = [line.split() for line in log.read_text().splitlines()]
    assert [what for _, what, _ in events] == ["start", "end"] * 4, events
    roots = [root for root, what, _ in events if what == "start"]
    subject = str(repo.resolve())
    assert [root == subject for root in roots] == [True, False, True, False], roots
    times = [float(t) for _, _, t in events]
    assert times == sorted(times), events


def test_failure_turned_into_setup_error_is_attributed_to_subject(tmp_path):
    # S2: the base FAILS this test; the change makes it ERROR at setup. The ids
    # match, but the failure is a different one and the change caused it.
    repo = _repo(tmp_path, {"tests/test_k.py": "def test_k():\n    assert 0\n"},
                 {"tests/test_k.py": SETUP_ERROR})
    r = _diff_run(repo, tmp_path, "tests")
    assert _token(r.stdout).startswith("FAILDIFF: NEW "), r.stdout + r.stderr
    assert "SUBJECT_ONLY tests/test_k.py::test_k subject=ERROR control=FAILED" in r.stdout, r.stdout
    assert _tagged(r.stdout, "BOTH") == []


def test_subject_not_a_repo_is_UNREADABLE(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    r = _diff_run(plain, tmp_path, "tests")
    assert _token(r.stdout) == "FAILDIFF: UNREADABLE reason=no-subject-repo side=subject", r.stdout
    assert r.returncode == 2, r.stdout + r.stderr


def test_worktree_add_failure_is_UNREADABLE(tmp_path):
    repo = _repo(tmp_path, {"tests/test_ok.py": PASSING}, {"tests/test_new.py": FAILING})
    admin = repo / ".git" / "worktrees"
    admin.mkdir()
    admin.chmod(0o500)
    try:
        r = _diff_run(repo, tmp_path, "tests")
    finally:
        admin.chmod(0o700)
    assert _token(r.stdout).startswith(
        "FAILDIFF: UNREADABLE reason=worktree-add-failed side=control"), r.stdout + r.stderr
    assert r.returncode == 2, r.stdout + r.stderr
    _no_control_left(repo, tmp_path)


HANG_WITH_GRANDCHILD = """\
import os, pathlib, subprocess, time

def test_hang():
    child = subprocess.Popen(["sleep", "300"])
    pathlib.Path(os.environ["FD_GRANDCHILD"]).write_text(str(child.pid))
    time.sleep(300)
"""


def _dead(pid: int, within: float = 10.0) -> bool:
    deadline = time.time() + within
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.1)
    return False


def test_timeout_is_UNREADABLE_and_kills_the_process_group(tmp_path):
    # S3 + S6: a hung run is cannot-judge, and what pytest started is killed with
    # it — a SIGKILLed pytest never reaches the conftest's leak reaper.
    repo = _repo(tmp_path, {"tests/test_ok.py": PASSING}, {"tests/test_hang.py": HANG_WITH_GRANDCHILD})
    pidfile = tmp_path / "grandchild.pid"
    r = _diff_run(repo, tmp_path, "tests", extra=("--timeout", "5"),
                  env=_env(tmp_path, FD_GRANDCHILD=str(pidfile)))
    assert _token(r.stdout).startswith(
        "FAILDIFF: UNREADABLE reason=timeout side=subject "), r.stdout + r.stderr
    pid = int(pidfile.read_text())
    try:
        assert _dead(pid), f"grandchild {pid} survived the timeout"
    finally:
        try:
            os.kill(pid, 9)
        except ProcessLookupError:
            pass
    _no_control_left(repo, tmp_path)


STICKY = """\
import os, pathlib

def test_sticky():
    tree = pathlib.Path(__file__).resolve().parents[1]
    if str(tree) != os.environ["FD_SUBJECT"]:
        stuck = tree / "stuck"
        stuck.mkdir()
        (stuck / "f").write_text("x")
        stuck.chmod(0o500)
"""


def test_control_that_cannot_be_removed_is_UNREADABLE(tmp_path):
    repo = _repo(tmp_path, {"tests/test_sticky.py": STICKY}, {"tests/test_new.py": FAILING})
    try:
        r = _diff_run(repo, tmp_path, "tests",
                      env=_env(tmp_path, FD_SUBJECT=str(repo.resolve())))
        assert _token(r.stdout).startswith(
            "FAILDIFF: UNREADABLE reason=control-not-removed side=control"), r.stdout + r.stderr
        assert r.returncode == 2, r.stdout + r.stderr
    finally:
        for stuck in (tmp_path / "controls").glob(".h-mad-control-*/stuck"):
            stuck.chmod(0o700)
        for left in (tmp_path / "controls").glob(".h-mad-control-*"):
            shutil.rmtree(left)
        _git(repo, "worktree", "prune")


def test_control_path_is_printed_before_the_run_ends(tmp_path):
    # S4: a caller killed by an outer timeout must already hold the control's
    # path to clean it up, so the header lines are flushed as they are written.
    slow = "import time\n\ndef test_slow():\n    time.sleep(30)\n"
    repo = _repo(tmp_path, {"tests/test_slow.py": slow}, {"tests/test_new.py": FAILING})
    parent = tmp_path / "controls"
    parent.mkdir()
    proc = subprocess.Popen(
        [sys.executable, str(SCRIPT), "run", "--subject", str(repo), "--base", "main",
         "--control-parent", str(parent), "--", "tests"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0, env=_env(tmp_path))
    seen = ""
    try:
        deadline = time.time() + 20
        while time.time() < deadline and "CONTROL: path=" not in seen:
            ready, _, _ = select.select([proc.stdout], [], [], 0.5)
            if ready:
                seen += os.read(proc.stdout.fileno(), 65536).decode()
        assert "CONTROL: path=" in seen and proc.poll() is None, seen
    finally:
        proc.terminate()
        proc.communicate(timeout=60)
    _no_control_left(repo, tmp_path)


def test_each_run_log_is_kept_and_named(tmp_path):
    # S5: an attributed id is investigated from the run that produced it, not
    # from a rerun, so each run's full output is kept and its path printed.
    repo = _repo(tmp_path, {"tests/test_ok.py": PASSING}, {"tests/test_new.py": FAILING})
    r = _diff_run(repo, tmp_path, "tests", extra=("--log-dir", str(tmp_path / "logs")))
    run_lines = [line for line in r.stdout.splitlines() if line.startswith("RUN: ")]
    assert len(run_lines) == 2, r.stdout
    logs = {line.split(" side=")[1].split()[0]: Path(line.split(" log=")[1]) for line in run_lines}
    assert "deliberate" in logs["subject"].read_text(), logs
    assert "deliberate" not in logs["control"].read_text(), logs
    assert logs["subject"].parent == tmp_path / "logs"


def test_interrupted_text_in_captured_output_is_not_a_collection_error(tmp_path):
    # N2: like FAILED lines, an `Interrupted:` banner a test printed belongs to
    # that test's captured output, not to this run.
    noisy = (
        "F.\n=================================== FAILURES ===================================\n"
        "----------------------------- Captured stdout call -----------------------------\n"
        "!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!\n"
        + SUMMARY_HEADER + "\n"
        "FAILED tests/test_a.py::test_one - assert 0\n"
        "1 failed, 1 passed in 0.10s\n"
    )
    r = _logs(tmp_path, noisy, _pytest_log(["tests/test_a.py::test_one"]))
    assert _token(r.stdout).startswith("FAILDIFF: SAME "), r.stdout


def test_all_skipped_selection_reads_all_skipped(tmp_path):
    skipped = "import pytest\n\n@pytest.mark.skip\ndef test_s():\n    pass\n"
    repo = _repo(tmp_path, {"tests/test_s.py": skipped}, {"tests/test_t.py": skipped.replace("test_s", "test_t")})
    r = _diff_run(repo, tmp_path, "tests")
    assert _token(r.stdout).startswith(
        "FAILDIFF: UNREADABLE reason=all-skipped side=subject "), r.stdout + r.stderr


def test_help_says_selection_is_relative_to_toplevel():
    r = subprocess.run([sys.executable, str(SCRIPT), "run", "--help"],
                       capture_output=True, text=True, timeout=60)
    assert "relative to the subject's toplevel" in " ".join(r.stdout.split()), r.stdout


# --- review round 2 of 8d2901be: R2-M1, R2-S1, R2-S2, R2-N1..N3 ---------------

def test_in_tree_venv_interpreter_is_not_refused(tmp_path):
    # R2-M1: a gitignored `.venv` inside the subject is the interpreter, not the
    # subject's code; its own site-packages on sys.path must not read as
    # "the control imports the subject".
    repo = _repo(tmp_path, {"tests/test_ok.py": PASSING}, {"tests/test_new.py": FAILING})
    subprocess.run([sys.executable, "-m", "venv", "--system-site-packages", "--without-pip",
                    str(repo / ".venv")], check=True, timeout=120)
    (repo / ".gitignore").write_text(".h-mad/\n__pycache__/\n.venv/\n")
    _commit_all(repo, "ignore venv")
    r = _diff_run(repo, tmp_path, "tests", python=str(repo / ".venv" / "bin" / "python"))
    assert _token(r.stdout).startswith("FAILDIFF: NEW "), r.stdout + r.stderr
    assert _tagged(r.stdout, "SUBJECT_ONLY") == ["tests/test_new.py::test_broken"]
    _no_control_left(repo, tmp_path)


EDITABLE_FINDER = """\
import importlib.util, sys
MAPPING = {{"pkg": {target!r}}}

class _Finder:
    @classmethod
    def find_spec(cls, name, path=None, target=None):
        if name in MAPPING:
            return importlib.util.spec_from_file_location(
                name, MAPPING[name] + "/__init__.py", submodule_search_locations=[MAPPING[name]])
        return None

def install():
    sys.meta_path.append(_Finder)
"""


def test_pep660_editable_finder_into_subject_is_UNREADABLE(tmp_path):
    # R2-S1: a PEP 660 editable install maps the package to the subject through
    # an import hook, with no subject path on sys.path. The control would import
    # the subject's package and both sides would agree.
    repo = _repo(tmp_path, {"src/pkg/__init__.py": "VALUE = 1\n", "tests/test_v.py": PKG_TEST},
                 {"src/pkg/__init__.py": "VALUE = 2\n"})
    env = _env(tmp_path, PYTHONUSERBASE=str(tmp_path / "userbase"))
    site_dir = Path(subprocess.run(
        [sys.executable, "-c", "import site; print(site.getusersitepackages())"],
        capture_output=True, text=True, env=env, check=True).stdout.strip())
    site_dir.mkdir(parents=True)
    (site_dir / "__editable___pkg_0_finder.py").write_text(
        EDITABLE_FINDER.format(target=str(repo.resolve() / "src" / "pkg")))
    (site_dir / "__editable__.pkg-0.pth").write_text(
        "import __editable___pkg_0_finder; __editable___pkg_0_finder.install()\n")
    r = _diff_run(repo, tmp_path, "tests", env=env)
    assert _token(r.stdout).startswith(
        "FAILDIFF: UNREADABLE reason=control-imports-subject side=control"), r.stdout + r.stderr
    assert "__editable___pkg_0_finder.py" in r.stdout, r.stdout
    _no_control_left(repo, tmp_path)


def test_subject_inside_the_interpreter_prefix_is_still_checked(tmp_path):
    # Round 3: the prefix exemption must not cover a subject that lives INSIDE
    # the interpreter's prefix (a repo under a conda env or venv directory), or
    # every subject path, an editable .pth included, is exempt and reads SAME.
    env_dir = tmp_path / "env"
    subprocess.run([sys.executable, "-m", "venv", "--system-site-packages", "--without-pip",
                    str(env_dir)], check=True, timeout=120)
    (env_dir / "work").mkdir()
    repo = _repo(env_dir / "work", {"src/pkg/__init__.py": "VALUE = 1\n",
                                    "tests/test_v.py": PKG_TEST},
                 {"src/pkg/__init__.py": "VALUE = 2\n"})
    python = env_dir / "bin" / "python"
    site_dir = Path(subprocess.run(
        [str(python), "-c", "import site; print(site.getsitepackages()[0])"],
        capture_output=True, text=True, check=True).stdout.strip())
    (site_dir / "subject_src.pth").write_text(f"{repo.resolve() / 'src'}\n")
    r = _diff_run(repo, tmp_path, "tests", python=str(python))
    assert _token(r.stdout).startswith(
        "FAILDIFF: UNREADABLE reason=control-imports-subject side=control"), r.stdout + r.stderr
    _no_control_left(repo, tmp_path)


def test_unreadable_import_probe_is_UNREADABLE(tmp_path):
    # The import check fails closed: an interpreter whose probe output cannot be
    # read is not taken as "imports nothing from the subject".
    repo = _repo(tmp_path, {"tests/test_ok.py": PASSING}, {"tests/test_new.py": FAILING})
    fake = tmp_path / "fakepy"
    fake.write_text(f'#!/bin/sh\nif [ "$1" = "-c" ]; then echo not-json; exit 0; fi\n'
                    f'exec {sys.executable} "$@"\n')
    fake.chmod(0o755)
    r = _diff_run(repo, tmp_path, "tests", python=str(fake))
    assert _token(r.stdout) == "FAILDIFF: UNREADABLE reason=probe-failed side=control", r.stdout + r.stderr
    _no_control_left(repo, tmp_path)


def _classify_in_process(subject_runs, control_runs, runs):
    code = (
        "import json, sys\n"
        f"sys.path.insert(0, {str(SCRIPTS)!r})\n"
        "import h_mad_failure_diff as m\n"
        "s, c, n = json.loads(sys.argv[1])\n"
        "sys.exit(m.classify(s, c, n))\n"
    )
    return subprocess.run([sys.executable, "-c", code,
                           json.dumps([subject_runs, control_runs, runs])],
                          capture_output=True, text=True, timeout=60)


def test_kind_that_flips_across_a_sides_runs_is_FLAKY_not_NEW():
    # R2-S2: failing every run of both sides, but FAILED then ERROR on the
    # subject: an unstable failure mode is a flake, not the change's breakage.
    node = "t.py::test_x"
    r = _classify_in_process([{node: "FAILED"}, {node: "ERROR"}],
                             [{node: "FAILED"}, {node: "FAILED"}], 2)
    token = _token(r.stdout)
    assert token.startswith("FAILDIFF: FLAKY "), r.stdout + r.stderr
    assert _tagged(r.stdout, "FLAKY") == [node]
    assert _tagged(r.stdout, "SUBJECT_ONLY") == []


def test_kind_change_constant_on_each_side_is_still_SUBJECT_ONLY():
    node = "t.py::test_x"
    r = _classify_in_process([{node: "ERROR"}, {node: "ERROR"}],
                             [{node: "FAILED"}, {node: "FAILED"}], 2)
    assert _token(r.stdout).startswith("FAILDIFF: NEW "), r.stdout + r.stderr
    assert f"SUBJECT_ONLY {node} subject=ERROR control=FAILED" in r.stdout


def test_uncreatable_log_dir_is_named_log_dir(tmp_path):
    # R2-N1: the reason names what failed.
    repo = _repo(tmp_path, {"tests/test_ok.py": PASSING}, {"tests/test_new.py": FAILING})
    blocker = tmp_path / "a-file"
    blocker.write_text("x")
    r = _diff_run(repo, tmp_path, "tests", extra=("--log-dir", str(blocker / "logs")))
    assert _token(r.stdout) == "FAILDIFF: UNREADABLE reason=log-dir side=both", r.stdout + r.stderr
    _no_control_left(repo, tmp_path)


def test_signal_between_spawn_and_tracking_still_kills_pytest(tmp_path):
    # R2-N2: a signal that lands after Popen but before the child is recorded
    # must still stop pytest, not wait out the run (or a 3600 s timeout).
    slow = "import time\n\ndef test_slow():\n    time.sleep(60)\n"
    repo = _repo(tmp_path, {"tests/test_slow.py": slow}, {"tests/test_new.py": FAILING})
    parent = tmp_path / "controls"
    parent.mkdir()
    driver = (
        "import os, signal, subprocess, sys\n"
        f"sys.path.insert(0, {str(SCRIPTS)!r})\n"
        "import h_mad_failure_diff as m\n"
        "real = subprocess.Popen\n"
        "class Racing(real):\n"
        "    def __init__(self, *a, **k):\n"
        "        super().__init__(*a, **k)\n"
        "        if 'pytest' in a[0]:\n"
        "            os.kill(os.getpid(), signal.SIGTERM)\n"
        "m.subprocess.Popen = Racing\n"
        f"sys.exit(m.main(['run', '--subject', {str(repo)!r}, '--base', 'main',"
        f" '--control-parent', {str(parent)!r}, '--', 'tests']))\n"
    )
    started = time.time()
    r = subprocess.run([sys.executable, "-c", driver], capture_output=True, text=True,
                       env=_env(tmp_path), timeout=120)
    assert _token(r.stdout) == "FAILDIFF: UNREADABLE reason=interrupted side=both", r.stdout + r.stderr
    assert time.time() - started < 40, "pytest ran on after the signal"
    _no_control_left(repo, tmp_path)


def test_main_in_process_with_a_plain_stdout(tmp_path):
    # R2-N3: an in-process caller that redirects stdout to a StringIO.
    ids = ["tests/test_a.py::test_one"]
    run, control = _log(tmp_path, "r.log", _pytest_log(ids)), _log(tmp_path, "c.log", _pytest_log(ids))
    code = (
        "import contextlib, io, sys\n"
        f"sys.path.insert(0, {str(SCRIPTS)!r})\n"
        "import h_mad_failure_diff as m\n"
        "buf = io.StringIO()\n"
        "with contextlib.redirect_stdout(buf):\n"
        f"    rc = m.main(['logs', '--run', {str(run)!r}, '--control', {str(control)!r}])\n"
        "print(buf.getvalue().splitlines()[-1])\n"
    )
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.strip().startswith("FAILDIFF: SAME "), r.stdout + r.stderr
