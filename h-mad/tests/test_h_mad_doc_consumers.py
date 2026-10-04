"""`h_mad_doc_consumers.py` names the tests that parse a document.

Skill-candidates row "name the tests that PARSE a document you are about to edit":
a doc-derived test lives beside its consumer, never beside the document, so a
targeted slice misses it and the full suite goes red after the push. The script
names them; the advisory `pre-commit` hook prints them for staged documents.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
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
