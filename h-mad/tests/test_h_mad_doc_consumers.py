"""`h_mad_doc_consumers.py` names the tests that parse a document.

Skill-candidates row "name the tests that PARSE a document you are about to edit":
a doc-derived test lives beside its consumer, never beside the document, so a
targeted slice misses it and the full suite goes red after the push. The script
names them; the advisory `pre-commit` hook prints them for staged documents.
"""
from __future__ import annotations

import os
import platform
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

HMAD = Path(__file__).resolve().parents[1]
SCRIPT = HMAD / "scripts" / "h_mad_doc_consumers.py"
HOOK = HMAD / "git-hooks" / "pre-commit"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, env=ENV, capture_output=True)


def _repo(tmp_path: Path) -> Path:
    """skill-a/SKILL.md is parsed by a sibling test and by one in another skill;
    skill-b/SKILL.md shares the basename and must not pull skill-a's readers in."""
    repo = tmp_path / "repo"
    files = {
        "skill-a/SKILL.md": "# a\n",
        "skill-b/SKILL.md": "# b\n",
        "skill-a/tests/test_a_docs.py": 'SKILL = HERE.parent / "SKILL.md"\n',
        "skill-a/tests/test_a_logic.py": "def test(): pass\n",
        "skill-b/tests/test_b_reads_a.py": 'A = ROOT / "skill-a" / "SKILL.md"\n',
        "skill-c/tests/test_c_other.py": 'X = ROOT / "skill-c" / "SKILL.md"\n',
    }
    for rel, body in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    return repo


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True,
                          text=True, cwd=str(repo))


def test_names_the_sibling_reader_and_the_cross_skill_reader(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    proc = _run(repo, "skill-a/SKILL.md")

    assert proc.returncode == 0, proc.stderr
    assert "CONSUMERS: skill-a/SKILL.md n=2" in proc.stdout, proc.stdout
    assert "skill-a/tests/test_a_docs.py" in proc.stdout
    assert "skill-b/tests/test_b_reads_a.py" in proc.stdout
    assert "test_a_logic.py" not in proc.stdout, "does not read the document"
    assert "test_c_other.py" not in proc.stdout, "reads a different SKILL.md"
    assert proc.stdout.rstrip().splitlines()[-1] == (
        "RUN: python3 -m pytest -q skill-a/tests/test_a_docs.py skill-b/tests/test_b_reads_a.py")


def test_staged_documents_are_used_and_code_is_skipped(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / "skill-a" / "SKILL.md").write_text("# a, edited\n", encoding="utf-8")
    (repo / "skill-a" / "tests" / "test_a_logic.py").write_text("def test(): 1\n", encoding="utf-8")
    _git(repo, "add", "-A")

    proc = _run(repo, "--staged")

    assert "CONSUMERS: skill-a/SKILL.md n=2" in proc.stdout, proc.stdout
    assert "CONSUMERS: skill-a/tests" not in proc.stdout, "a test file is not a document"


def test_a_document_nobody_reads_prints_zero_and_no_run_line(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / "notes.md").write_text("x\n", encoding="utf-8")

    proc = _run(repo, "notes.md")

    assert "CONSUMERS: notes.md n=0" in proc.stdout, proc.stdout
    assert "RUN:" not in proc.stdout


def test_outside_git_says_unknown_not_zero(tmp_path: Path) -> None:
    proc = subprocess.run([sys.executable, str(SCRIPT), "x.md"], capture_output=True,
                          text=True, cwd=str(tmp_path),
                          env={**os.environ, "GIT_CEILING_DIRECTORIES": str(tmp_path.parent)})

    assert proc.returncode == 0
    assert "CONSUMERS: UNKNOWN" in proc.stdout, proc.stdout
    assert "n=0" not in proc.stdout


def test_pre_commit_hook_prints_consumers_and_never_blocks(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    hooks = repo / ".git" / "hooks"
    shutil.copy(HOOK, hooks / "pre-commit")
    (hooks / "pre-commit").chmod(0o755)
    (repo / "skill-a" / "SKILL.md").write_text("# a, edited\n", encoding="utf-8")
    _git(repo, "add", "-A")

    proc = subprocess.run(["git", "-C", str(repo), "commit", "-m", "edit"], env={
        **ENV, "HMAD_DOC_CONSUMERS": str(SCRIPT)}, capture_output=True, text=True)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "skill-b/tests/test_b_reads_a.py" in proc.stderr, proc.stderr


def test_installer_ships_the_pre_commit_hook() -> None:
    install = (HMAD / "git-hooks" / "install.sh").read_text(encoding="utf-8")
    assert "HOOKS=(pre-push pre-commit)" in install


def test_pre_commit_hook_warns_of_live_runs_and_never_blocks(tmp_path: Path) -> None:
    """The live-run warning (skill-candidates row "check for a live run before merging a
    shared skill change") rides the same advisory hook."""
    repo = _repo(tmp_path)
    hooks = repo / ".git" / "hooks"
    shutil.copy(HOOK, hooks / "pre-commit")
    (hooks / "pre-commit").chmod(0o755)
    stub = tmp_path / "live_runs_stub.py"
    stub.write_text('print("LIVE-RUNS: 1 checked=3")\nprint("  live: /lanes/x · batch-18 · owner sess-abc")\n',
                    encoding="utf-8")
    (repo / "skill-a" / "SKILL.md").write_text("# a, edited\n", encoding="utf-8")
    _git(repo, "add", "-A")

    proc = subprocess.run(["git", "-C", str(repo), "commit", "-m", "edit"], env={
        **ENV, "HMAD_DOC_CONSUMERS": str(SCRIPT), "HMAD_LIVE_RUNS": str(stub)},
        capture_output=True, text=True)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "live: /lanes/x · batch-18" in proc.stderr, proc.stderr


def test_pre_commit_hook_is_quiet_when_nothing_is_live(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    hooks = repo / ".git" / "hooks"
    shutil.copy(HOOK, hooks / "pre-commit")
    (hooks / "pre-commit").chmod(0o755)
    stub = tmp_path / "live_runs_stub.py"
    stub.write_text('print("LIVE-RUNS: NONE checked=3")\n', encoding="utf-8")
    (repo / "notes.md").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "-A")

    proc = subprocess.run(["git", "-C", str(repo), "commit", "-m", "edit"], env={
        **ENV, "HMAD_DOC_CONSUMERS": str(SCRIPT), "HMAD_LIVE_RUNS": str(stub)},
        capture_output=True, text=True)

    assert "LIVE-RUNS" not in proc.stderr, proc.stderr


# --- `--run`: execute the consumers the RUN: line names (skill-candidates row
# "`h_mad_doc_consumers.py --run`"). The RUN: line was copied into pytest by hand
# in every session that used it; once it was skipped and a 15-minute suite
# surfaced 25 failures a consumer run reproduces in seconds.

_LOGGING_TEST = '''import os, sys
DOC = {doc!r}


def test_reads():
    with open(os.environ["DOC_RUN_LOG"], "a", encoding="utf-8") as fh:
        fh.write(os.path.basename(__file__) + " " + sys.executable + "\\n")
{extra}'''


def _run_repo(tmp_path: Path, extra_b: str = "", extra_files: dict | None = None) -> Path:
    """Consumers that are REAL tests, each logging that it ran and under which
    interpreter. `test_a_logic.py` logs too but reads no document, so it must
    never run."""
    repo = tmp_path / "repo"
    files = {
        **(extra_files or {}),
        "skill-a/SKILL.md": "# a\n",
        "skill-b/SKILL.md": "# b\n",
        "notes.md": "nobody reads this\n",
        "skill-a/tests/test_a_docs.py": _LOGGING_TEST.format(doc="SKILL.md", extra=""),
        "skill-b/tests/test_b_reads_a.py": _LOGGING_TEST.format(doc="skill-a/SKILL.md", extra=extra_b),
        "skill-a/tests/test_a_logic.py": _LOGGING_TEST.format(doc="logic", extra=""),
    }
    for rel, body in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    return repo


def _run_flag(repo: Path, *args: str, python: str = sys.executable,
              path_prefix: str = "") -> subprocess.CompletedProcess:
    env = {**os.environ, "DOC_RUN_LOG": str(repo.parent / "ran.log")}
    if path_prefix:
        env["PATH"] = path_prefix + os.pathsep + env.get("PATH", "")
    return subprocess.run([python, str(SCRIPT), *args], capture_output=True, text=True,
                          cwd=str(repo), env=env)


def _ran(repo: Path) -> list[str]:
    log = repo.parent / "ran.log"
    return log.read_text(encoding="utf-8").splitlines() if log.exists() else []


def test_run_executes_union_once_and_reports_PASS(tmp_path: Path) -> None:
    repo = _run_repo(tmp_path)
    # test_b_reads_a.py consumes BOTH documents: the union runs it once.
    proc = _run_flag(repo, "skill-a/SKILL.md", "skill-b/SKILL.md", "--run")

    assert proc.returncode == 0, proc.stdout + proc.stderr
    lines = proc.stdout.rstrip().splitlines()
    assert lines[-1] == "CONSUMERS-RUN: PASS files=2 passed=2", proc.stdout
    run_line = next(line for line in lines if line.startswith("RUN: "))
    named = sorted(Path(f).name for f in run_line.split()[5:])
    ran = sorted(entry.split(" ", 1)[0] for entry in _ran(repo))
    assert ran == named == ["test_a_docs.py", "test_b_reads_a.py"], (ran, named)


def test_run_failure_exits_1_and_names_ids(tmp_path: Path) -> None:
    repo = _run_repo(tmp_path, extra_b="\n\ndef test_broken():\n    assert False\n")
    proc = _run_flag(repo, "skill-a/SKILL.md", "--run")

    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "CONSUMERS-RUN: FAIL files=2 failed=1" in proc.stdout, proc.stdout
    assert "  FAILED skill-b/tests/test_b_reads_a.py::test_broken" in proc.stdout, proc.stdout
    assert "PASS" not in proc.stdout


def test_run_with_no_consumers_is_NONE_exit0(tmp_path: Path) -> None:
    repo = _run_repo(tmp_path)
    proc = _run_flag(repo, "notes.md", "--run")

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout.rstrip().splitlines()[-1] == "CONSUMERS-RUN: NONE", proc.stdout
    assert "PASS" not in proc.stdout
    assert _ran(repo) == [], "nothing may run when nothing reads the document"


def test_run_without_pytest_is_UNREADABLE_not_PASS(tmp_path: Path) -> None:
    """The interpreter stub is a venv with no pytest: what a bare `python3` that
    resolves to an interpreter without pytest looks like."""
    venv = tmp_path / "nopytest"
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv)], check=True,
                   capture_output=True)
    stub = venv / "bin" / "python"
    assert subprocess.run([str(stub), "-c", "import pytest"], capture_output=True).returncode != 0
    repo = _run_repo(tmp_path)

    proc = _run_flag(repo, "skill-a/SKILL.md", "--run", python=str(stub))

    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "CONSUMERS-RUN: UNREADABLE reason=pytest-missing" in proc.stdout, proc.stdout
    assert "PASS" not in proc.stdout


def test_run_uses_sys_executable_not_bare_python3(tmp_path: Path) -> None:
    trap = tmp_path / "trap"
    trap.mkdir()
    (trap / "python3").write_text(f'#!/bin/sh\ntouch "{trap}/used"\nexit 3\n', encoding="utf-8")
    (trap / "python3").chmod(0o755)
    repo = _run_repo(tmp_path)

    proc = _run_flag(repo, "skill-a/SKILL.md", "--run", path_prefix=str(trap))

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert not (trap / "used").exists(), "a bare `python3` from PATH ran the consumers"
    assert {entry.split(" ", 1)[1] for entry in _ran(repo)} == {sys.executable}


def test_run_without_a_summary_line_is_UNREADABLE_even_on_exit_0(tmp_path: Path) -> None:
    """A consumer that kills the interpreter mid-run leaves pytest exit 0 and no
    summary: nothing was measured, so it must not read as PASS."""
    repo = _run_repo(tmp_path, extra_b="\n\ndef test_dies():\n    os._exit(0)\n")
    proc = _run_flag(repo, "skill-a/SKILL.md", "--run")

    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "CONSUMERS-RUN: UNREADABLE reason=no-summary" in proc.stdout, proc.stdout
    assert "PASS" not in proc.stdout


def test_run_outside_git_is_UNREADABLE_not_PASS(tmp_path: Path) -> None:
    proc = subprocess.run([sys.executable, str(SCRIPT), "x.md", "--run"], capture_output=True,
                          text=True, cwd=str(tmp_path),
                          env={**os.environ, "GIT_CEILING_DIRECTORIES": str(tmp_path.parent)})

    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "CONSUMERS: UNKNOWN" in proc.stdout
    assert "CONSUMERS-RUN: UNREADABLE reason=unknown-docs" in proc.stdout, proc.stdout


def test_run_with_no_or_missing_documents_is_UNREADABLE(tmp_path: Path) -> None:
    """No document, or a mistyped one, is not 'nothing reads it': NONE would
    pass a typo."""
    repo = _run_repo(tmp_path)
    for args in (["--run"], ["skill-a/SKILLL.md", "--run"]):
        proc = _run_flag(repo, *args)
        assert proc.returncode == 2, (args, proc.stdout + proc.stderr)
        assert "CONSUMERS-RUN: UNREADABLE reason=unknown-docs" in proc.stdout, (args, proc.stdout)
    assert _ran(repo) == []


def test_default_output_unchanged_without_flag(tmp_path: Path) -> None:
    """Without `--run` the output is byte-identical to the pre-flag script: the
    advisory pre-commit hook parses it and must never block."""
    repo = _repo(tmp_path)
    proc = _run(repo, "skill-a/SKILL.md", "skill-b/SKILL.md")

    assert proc.returncode == 0
    assert proc.stderr == ""
    assert proc.stdout == (
        "CONSUMERS: skill-a/SKILL.md n=2\n"
        "  skill-a/tests/test_a_docs.py\n"
        "  skill-b/tests/test_b_reads_a.py\n"
        "CONSUMERS: skill-b/SKILL.md n=1\n"
        "  skill-b/tests/test_b_reads_a.py\n"
        "RUN: python3 -m pytest -q skill-a/tests/test_a_docs.py skill-b/tests/test_b_reads_a.py\n")
    missing = _run(repo, "skill-a/SKILLL.md")
    assert (missing.returncode, missing.stdout) == (0, "CONSUMERS: skill-a/SKILLL.md n=0\n")


# --- review of abb20c7c: the fixes below each close a path that read as PASS,
# or as FAIL with no cause, on a run that measured nothing.

def test_run_refuses_a_document_path_outside_the_repo(tmp_path: Path) -> None:
    """An absolute path (another checkout's copy of the document) passed the
    is-file check and PASSed against THIS repo's unedited copy."""
    repo = _run_repo(tmp_path)
    other = tmp_path / "other" / "skill-a" / "SKILL.md"
    other.parent.mkdir(parents=True)
    other.write_text("BROKEN\n", encoding="utf-8")
    for doc in (str(other), str(repo / "skill-a" / "SKILL.md"), "../other/skill-a/SKILL.md"):
        proc = _run_flag(repo, doc, "--run")
        assert proc.returncode == 2, (doc, proc.stdout + proc.stderr)
        assert "CONSUMERS-RUN: UNREADABLE reason=unknown-docs" in proc.stdout, (doc, proc.stdout)
        assert "PASS" not in proc.stdout
    assert _ran(repo) == []


def test_run_with_only_skipped_consumers_is_UNREADABLE_not_PASS(tmp_path: Path) -> None:
    repo = _run_repo(tmp_path, extra_files={
        "skill-c/GUIDE.md": "# c\n",
        "skill-c/tests/test_c_skip.py": "import pytest\nDOC = 'GUIDE.md'\n\n\n"
                                        "def test_s():\n    pytest.skip('nothing measured')\n",
    })
    proc = _run_flag(repo, "skill-c/GUIDE.md", "--run")

    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert 'CONSUMERS-RUN: UNREADABLE reason=incomplete rc=0 summary="1 skipped"' in proc.stdout, proc.stdout
    assert "PASS" not in proc.stdout and "FAIL" not in proc.stdout


def test_run_nonzero_exit_with_passing_summary_is_UNREADABLE(tmp_path: Path) -> None:
    """pytest says `1 passed` but exits 3: something outside the tests broke."""
    repo = _run_repo(tmp_path, extra_files={
        "skill-d/NOTE.md": "# d\n",
        "skill-d/tests/test_d.py": "DOC = 'NOTE.md'\n\n\ndef test_ok():\n    pass\n",
        "skill-d/tests/conftest.py": "def pytest_sessionfinish(session, exitstatus):\n"
                                     "    session.exitstatus = 3\n",
    })
    proc = _run_flag(repo, "skill-d/NOTE.md", "--run")

    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert 'CONSUMERS-RUN: UNREADABLE reason=incomplete rc=3 summary="1 passed"' in proc.stdout, proc.stdout
    assert "PASS" not in proc.stdout


def test_run_streams_pytest_output_to_stderr(tmp_path: Path) -> None:
    """A 77-file run takes minutes: the operator sees pytest's progress as it
    happens, and stdout stays the CONSUMERS lines plus the token."""
    repo = _run_repo(tmp_path)
    proc = _run_flag(repo, "skill-a/SKILL.md", "--run")

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "2 passed in " in proc.stderr, proc.stderr
    assert "2 passed in " not in proc.stdout, proc.stdout


def test_run_times_out_as_UNREADABLE(tmp_path: Path) -> None:
    repo = _run_repo(tmp_path, extra_b="\n\ndef test_hangs():\n    import time\n    time.sleep(120)\n")
    start = time.monotonic()
    proc = _run_flag(repo, "skill-a/SKILL.md", "--run", "--timeout", "4")

    assert time.monotonic() - start < 60, "the timeout did not stop the run"
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "CONSUMERS-RUN: UNREADABLE reason=timeout" in proc.stdout, proc.stdout
    assert "PASS" not in proc.stdout


def test_run_interrupted_is_UNREADABLE_not_a_traceback(tmp_path: Path) -> None:
    repo = _run_repo(tmp_path, extra_b="\n\ndef test_hangs():\n    import time\n    time.sleep(120)\n")
    env = {**os.environ, "DOC_RUN_LOG": str(repo.parent / "ran.log")}
    proc = subprocess.Popen([sys.executable, str(SCRIPT), "skill-a/SKILL.md", "--run"], cwd=str(repo),
                            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    deadline = time.monotonic() + 60
    while len(_ran(repo)) < 2 and time.monotonic() < deadline:
        time.sleep(0.1)
    time.sleep(0.5)
    os.kill(proc.pid, signal.SIGINT)
    out, err = proc.communicate(timeout=60)

    assert proc.returncode == 2, out + err
    assert "CONSUMERS-RUN: UNREADABLE reason=interrupted" in out, out + err
    assert "Traceback" not in err, err


def test_run_names_the_interpreter_it_executes(tmp_path: Path) -> None:
    """The RUN line says `python3`; under `--run` the interpreter actually used
    is printed, so a PASS records what produced it."""
    repo = _run_repo(tmp_path)
    proc = _run_flag(repo, "skill-a/SKILL.md", "--run")

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert f"RUN-WITH: {sys.executable} (Python {platform.python_version()})" in proc.stdout, proc.stdout


def test_run_survives_non_utf8_child_output(tmp_path: Path) -> None:
    repo = _run_repo(tmp_path, extra_files={
        "skill-e/README.md": "# e\n",
        "skill-e/tests/test_e.py": "DOC = 'README.md'\n\n\ndef test_ok():\n    pass\n",
        "skill-e/tests/conftest.py": "import os\n\n\ndef pytest_unconfigure(config):\n"
                                     "    os.write(1, b'raw \\xff\\xfe bytes\\n')\n",
    })
    proc = _run_flag(repo, "skill-e/README.md", "--run")

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout.rstrip().splitlines()[-1] == "CONSUMERS-RUN: PASS files=1 passed=1", proc.stdout
