"""Backlog-row TDD cycle driver (row 2661, plan backlog-row-cycle.plan.md).

Only the CLI is prescribed, so tests execute the script. The driver composes
sibling tools by path (assemble_tdd, doc_consumers, mutation_harness, census);
each test copies the driver into a throwaway skills layout where those siblings
are stubs that record their argv. The census is the REAL one, copied in, so the
pipe-escape test proves the store actually accepts the line.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "h_mad_backlog_cycle.py"
CENSUS = ROOT.parent / "handoff" / "scripts" / "skill_candidates_census.py"

STUB = r'''
import json, os, sys
tool = __TOOL__
with open(os.environ["BCYCLE_TRACE"], "a") as stream:
    stream.write(json.dumps({"tool": tool, "argv": sys.argv[1:]}) + "\n")
out = os.environ.get("STUB_" + tool.upper() + "_OUT")
if out:
    print(out)
raise SystemExit(int(os.environ.get("STUB_" + tool.upper() + "_RC", "0")))
'''

STORE = """# Skill candidates

- **alpha row** (2026-10-18): first thing — recurrence: 2 — candidate: yes

- **beta row** (2026-10-18): second thing — recurrence: 2 — candidate: yes

- **twin row** (2026-10-18): one — recurrence: 2 — candidate: yes

- **twin row** (2026-10-18): two — recurrence: 2 — candidate: yes
"""


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


@pytest.fixture
def layout(tmp_path: Path):
    assert SCRIPT.exists(), f"driver not written yet: {SCRIPT}"
    skills = tmp_path / "skills"
    scripts = skills / "h-mad" / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy(SCRIPT, scripts / SCRIPT.name)
    for tool, filename in (("assemble", "h_mad_assemble_tdd.py"),
                           ("consumers", "h_mad_doc_consumers.py"),
                           ("harness", "h_mad_mutation_harness.py")):
        (scripts / filename).write_text(STUB.replace("__TOOL__", repr(tool)))
    census_dir = skills / "handoff" / "scripts"
    census_dir.mkdir(parents=True)
    shutil.copy(CENSUS, census_dir / CENSUS.name)

    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    (repo / "docs").mkdir()
    (repo / "docs" / "skill-candidates.md").write_text(STORE)
    (repo / "docs" / "guide.md").write_text("guide\n")
    (repo / "src").mkdir()
    (repo / "src" / "shared.py").write_text("X = 1\n")
    (repo / "src" / "other.py").write_text("Y = 1\n")
    (repo / "tests").mkdir()
    (repo / ".gitignore").write_text(".h-mad/*\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    _git(repo, "remote", "add", "origin", str(remote))
    _git(repo, "push", "-q", "-u", "origin", "main")
    return {"repo": repo, "remote": remote, "driver": scripts / SCRIPT.name,
            "trace": tmp_path / "trace.jsonl"}


def _run(layout, *args: str, **env: str) -> subprocess.CompletedProcess:
    full_env = {**os.environ, "BCYCLE_TRACE": str(layout["trace"]), **env}
    return subprocess.run([sys.executable, str(layout["driver"]), *args],
                          cwd=layout["repo"], capture_output=True, text=True,
                          env=full_env, timeout=120)


def _calls(layout, tool: str) -> list[list[str]]:
    if not layout["trace"].exists():
        return []
    rows = [json.loads(line) for line in layout["trace"].read_text().splitlines()]
    return [row["argv"] for row in rows if row["tool"] == tool]


def _last(result: subprocess.CompletedProcess) -> str:
    lines = result.stdout.strip().splitlines()
    return lines[-1] if lines else ""


def _committed_paths(repo: Path, rev: str = "HEAD") -> set[str]:
    return set(_git(repo, "show", "--name-only", "--format=", rev).splitlines())


def _red(layout, row: str, test: str, *extra: str) -> subprocess.CompletedProcess:
    (layout["repo"] / test).write_text("def test_x():\n    assert False\n")
    return _run(layout, "red", "--row", row, "--paths", test, *extra)


# 1
def test_red_commits_only_declared_tests_and_forwards_passthrough(layout) -> None:
    repo = layout["repo"]
    (repo / "src" / "other.py").write_text("Y = 2  # unrelated dirty edit\n")

    result = _red(layout, "alpha row", "tests/test_alpha.py",
                  "--", "--feature", "f", "--task", "T1")

    assert result.returncode == 0, result.stdout + result.stderr
    assert _last(result).startswith("CYCLE: RED committed=")
    assert _committed_paths(repo) == {"tests/test_alpha.py"}
    assert "src/other.py" in _git(repo, "status", "--porcelain")
    [argv] = _calls(layout, "assemble")
    assert argv[argv.index("--phase") + 1] == "red"
    assert argv[-4:] == ["--feature", "f", "--task", "T1"]


# 2
def test_green_refuses_a_path_claimed_by_another_active_cycle(layout) -> None:
    repo = layout["repo"]
    assert _red(layout, "alpha row", "tests/test_alpha.py").returncode == 0
    (repo / "src" / "shared.py").write_text("X = 2\n")
    first = _run(layout, "green", "--row", "alpha row", "--paths", "src/shared.py")
    assert first.returncode == 0, first.stdout + first.stderr

    assert _red(layout, "beta row", "tests/test_beta.py").returncode == 0
    head = _git(repo, "rev-parse", "HEAD")
    (repo / "src" / "shared.py").write_text("X = 3\n")
    second = _run(layout, "green", "--row", "beta row", "--paths", "src/shared.py")

    assert second.returncode != 0
    assert "CYCLE: REFUSED reason=path-claimed-by=alpha" in _last(second)
    assert _git(repo, "rev-parse", "HEAD") == head


# 3
def test_green_refuses_nothing_to_commit_on_an_unchanged_path(layout) -> None:
    repo = layout["repo"]
    assert _red(layout, "alpha row", "tests/test_alpha.py").returncode == 0
    head = _git(repo, "rev-parse", "HEAD")

    result = _run(layout, "green", "--row", "alpha row", "--paths", "src/shared.py")

    assert result.returncode != 0
    assert _last(result) == "CYCLE: REFUSED reason=nothing-to-commit path=src/shared.py"
    assert _git(repo, "rev-parse", "HEAD") == head


def _cycle_through_green(layout, row: str, *impl: tuple[str, str]) -> None:
    assert _red(layout, row, "tests/test_cycle.py").returncode == 0
    for rel, text in impl:
        (layout["repo"] / rel).write_text(text)
    green = _run(layout, "green", "--row", row, "--paths", *[rel for rel, _ in impl])
    assert green.returncode == 0, green.stdout + green.stderr


# 4
def test_land_with_no_changed_documents_skips_consumers_explicitly(layout) -> None:
    _cycle_through_green(layout, "alpha row", ("src/shared.py", "X = 2\n"))

    result = _run(layout, "land", "--row", "alpha row",
                  "--status", "**LANDED** 2026-10-18 done", "--no-push")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "CONSUMERS: SKIPPED reason=no-documents" in result.stdout
    assert "MUTATION: SKIPPED reason=no-specs" in result.stdout
    assert _calls(layout, "consumers") == []
    assert _calls(layout, "harness") == []


# 5
def test_land_halts_before_census_when_consumers_are_unreadable(layout) -> None:
    repo = layout["repo"]
    _cycle_through_green(layout, "alpha row", ("docs/guide.md", "guide v2\n"))
    store_before = (repo / "docs" / "skill-candidates.md").read_text()
    head = _git(repo, "rev-parse", "HEAD")

    result = _run(layout, "land", "--row", "alpha row",
                  "--status", "**LANDED** 2026-10-18 done", "--no-push",
                  STUB_CONSUMERS_RC="2",
                  STUB_CONSUMERS_OUT="CONSUMERS-RUN: UNREADABLE reason=unknown-docs")

    assert result.returncode != 0
    [argv] = _calls(layout, "consumers")
    assert "--run" in argv and "docs/guide.md" in argv
    assert (repo / "docs" / "skill-candidates.md").read_text() == store_before
    assert _git(repo, "rev-parse", "HEAD") == head


# 6
def test_pipe_in_status_is_escaped_and_accepted_by_the_real_census(layout) -> None:
    repo = layout["repo"]
    _cycle_through_green(layout, "alpha row", ("src/shared.py", "X = 2\n"))

    result = _run(layout, "land", "--row", "alpha row",
                  "--status", "**LANDED** 2026-10-18 `abc` — a | b", "--no-push")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "APPLY: inserted=1" in result.stdout
    store = (repo / "docs" / "skill-candidates.md").read_text()
    assert "  — **LANDED** 2026-10-18 `abc` — a | b\n" in store
    assert _committed_paths(repo) == {"docs/skill-candidates.md"}


# 7
@pytest.mark.parametrize("row, reason", [("nope row", "no-match"),
                                         ("twin row", "ambiguous")])
def test_row_must_match_exactly_one_open_row(layout, row: str, reason: str) -> None:
    head = _git(layout["repo"], "rev-parse", "HEAD")

    result = _red(layout, row, "tests/test_x.py")

    assert result.returncode != 0
    assert _last(result) == f"CYCLE: REFUSED reason={reason} row={row}"
    assert _calls(layout, "assemble") == []
    assert _git(layout["repo"], "rev-parse", "HEAD") == head


# 8
def test_no_push_leaves_the_remote_and_default_push_never_forces(layout, tmp_path: Path) -> None:
    repo, remote = layout["repo"], layout["remote"]
    _cycle_through_green(layout, "alpha row", ("src/shared.py", "X = 2\n"))
    remote_before = _git(remote, "rev-parse", "main")

    quiet = _run(layout, "land", "--row", "alpha row",
                 "--status", "**LANDED** 2026-10-18 done", "--no-push")
    assert quiet.returncode == 0, quiet.stdout + quiet.stderr
    assert _git(remote, "rev-parse", "main") == remote_before

    # Diverge the remote: a forced push would overwrite this commit.
    other = tmp_path / "other"
    subprocess.run(["git", "clone", "-q", str(remote), str(other)], check=True)
    _git(other, "config", "user.email", "o@example.com")
    _git(other, "config", "user.name", "o")
    (other / "foreign.txt").write_text("theirs\n")
    _git(other, "add", "foreign.txt")
    _git(other, "commit", "-q", "-m", "foreign")
    _git(other, "push", "-q", "origin", "main")
    foreign = _git(remote, "rev-parse", "main")

    _cycle_through_green(layout, "beta row", ("src/other.py", "Y = 2\n"))
    pushed = _run(layout, "land", "--row", "beta row",
                  "--status", "**LANDED** 2026-10-18 done")

    assert pushed.returncode != 0
    assert "PUSH: REJECTED" in _last(pushed)
    assert _git(remote, "rev-parse", "main") == foreign
