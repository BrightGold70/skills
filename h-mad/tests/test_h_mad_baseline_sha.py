"""J41 — the 5c baseline sha was derived by a command that returns the wrong commit.

Phase 6a-prime reviews `BASE = 5c sha`, and 5f takes `--base <5c sha>`. Neither had
a way to obtain that value, so it was obtained by hand — and the recorded attempt
used `git merge-base main <branch>`, which returns 5c's PARENT. 5c is defined as
`git checkout -b …; commit impl-plan + audit files`, so the 5c commit is the
branch's FIRST commit and the merge-base is the commit it forked from. Measured on
the feature that filed the row: merge-base `b5c8f41`, real 5c `730cc16`, and the
313 lines between them are the impl-plan and its audits — which then enter the
review diff as newly-added content, when the contract makes them a separate input.

The original was "verified" by re-running the command that produced it, so this
file's first duty is MUTUAL DISCRIMINATION: the derived value must be provably
different from the merge-base on a branch where the two differ. A test that only
asserts "returns a sha" passes for both answers.

The second duty is the property that decided store-vs-derive. A stored sha cannot
tell you it is wrong; this derivation can, because "the branch's first commit is
5c" is a protocol invariant with an observable consequence — that commit touches
an impl-plan. So a cannot-verify is a real verdict here, and it must not be
reachable by a caller pattern-matching for a value: `OK` carries `sha=`, and every
other outcome carries no `sha=` at all.
"""

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "h_mad_baseline_sha.py"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True,
    ).stdout.strip()


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args, "--repo", str(repo)],
        capture_output=True, text=True,
    )


def _commit(repo: Path, rel: str, text: str, message: str) -> str:
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=t@e.com", "-c", "user.name=T", "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _repo_with_feature_branch(tmp_path: Path, first_commit_is_impl_plan: bool = True):
    """A trunk with history, then a 5c-shaped branch on top of it."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _commit(repo, "src/mod.py", "x = 1\n", "trunk 1")
    fork_point = _commit(repo, "src/mod.py", "x = 2\n", "trunk 2")

    _git(repo, "checkout", "-q", "-b", "feature/1-thing")
    if first_commit_is_impl_plan:
        five_c = _commit(
            repo, "docs/01-plan/features/thing.impl-plan.md", "# plan\n",
            "docs: Phase 5a/5b impl-plan for thing",
        )
    else:
        five_c = _commit(repo, "src/other.py", "y = 1\n", "chore: something before 5c")
    _commit(repo, "src/mod.py", "x = 3\n", "feat: task 1 GREEN")
    _commit(repo, "src/mod.py", "x = 4\n", "feat: task 2 GREEN")
    return repo, fork_point, five_c


class TestDerivation:
    def test_derives_the_branchs_first_commit(self, tmp_path):
        repo, _fork, five_c = _repo_with_feature_branch(tmp_path)

        result = _run(repo, "--branch", "feature/1-thing", "--trunk", "main")

        assert result.returncode == 0, result.stderr
        assert "BASELINE: OK" in result.stdout
        assert f"sha={five_c}" in result.stdout

    def test_the_derived_sha_is_not_the_merge_base(self, tmp_path):
        """The whole defect. Without this the suite passes for the wrong answer.

        `git merge-base main <branch>` returns the fork point; the 5c commit is the
        one AFTER it. The two differ by exactly the impl-plan commit, which is what
        made the original mistake invisible — both are real shas on the right branch.
        """
        repo, fork_point, five_c = _repo_with_feature_branch(tmp_path)
        assert fork_point != five_c, "fixture is degenerate — the two must differ"
        merge_base = _git(repo, "merge-base", "main", "feature/1-thing")
        assert merge_base == fork_point, "fixture assumption about git changed"

        result = _run(repo, "--branch", "feature/1-thing", "--trunk", "main")

        assert f"sha={five_c}" in result.stdout
        assert fork_point not in result.stdout

    def test_survives_a_rebase_that_rewrites_the_5c_sha(self, tmp_path):
        """The property that decided store-vs-derive.

        A rebase gives 5c a new sha. A stored value then points at the old, orphaned
        object; the derivation recomputes and finds the new first commit, which is
        still 5c semantically.
        """
        repo, _fork, five_c_before = _repo_with_feature_branch(tmp_path)
        _git(repo, "checkout", "-q", "main")
        _commit(repo, "src/trunk_moved.py", "z = 1\n", "trunk 3")
        _git(repo, "checkout", "-q", "feature/1-thing")
        _git(repo, "-c", "user.email=t@e.com", "-c", "user.name=T", "rebase", "-q", "main")

        five_c_after = _git(repo, "rev-list", "--first-parent", "feature/1-thing",
                            "--not", "main")
        five_c_after = five_c_after.splitlines()[-1]
        assert five_c_after != five_c_before, "rebase did not rewrite the sha"

        result = _run(repo, "--branch", "feature/1-thing", "--trunk", "main")

        assert result.returncode == 0
        assert f"sha={five_c_after}" in result.stdout


    def test_a_merged_side_branch_cannot_supply_an_older_first_commit(self, tmp_path):
        """`--first-parent` is load-bearing, and only a merge can show it.

        Without it, `rev-list` walks into a merged side branch whose commits are
        older than 5c and are also absent from trunk — so the oldest one wins and
        the baseline silently moves BEFORE the impl-plan, which is the same class
        of error as the merge-base bug it replaces.
        """
        repo = tmp_path / "repo"
        repo.mkdir()
        _git(repo, "init", "-q", "-b", "main")
        _commit(repo, "src/mod.py", "x = 1\n", "trunk 1")

        # A side branch forked from trunk, with commits older than 5c.
        _git(repo, "checkout", "-q", "-b", "side")
        _commit(repo, "src/side.py", "s = 1\n", "side: older than 5c")

        _git(repo, "checkout", "-q", "main")
        _git(repo, "checkout", "-q", "-b", "feature/1-thing")
        five_c = _commit(
            repo, "docs/01-plan/features/thing.impl-plan.md", "# plan\n",
            "docs: Phase 5a/5b impl-plan for thing",
        )
        _git(repo, "-c", "user.email=t@e.com", "-c", "user.name=T",
             "merge", "-q", "--no-ff", "-m", "merge side", "side")

        result = _run(repo, "--branch", "feature/1-thing", "--trunk", "main")

        assert result.returncode == 0, result.stdout
        assert f"sha={five_c}" in result.stdout, result.stdout


class TestSelfVerification:
    def test_ok_only_when_the_first_commit_touches_an_impl_plan(self, tmp_path):
        repo, _fork, _five_c = _repo_with_feature_branch(tmp_path)
        result = _run(repo, "--branch", "feature/1-thing", "--trunk", "main")
        assert "BASELINE: OK" in result.stdout

    def test_unverified_when_something_was_committed_before_5c(self, tmp_path):
        """The assumption is a protocol invariant, so its violation is reportable
        rather than silent — which is the one thing a stored sha cannot do."""
        repo, _fork, _first = _repo_with_feature_branch(tmp_path, first_commit_is_impl_plan=False)

        result = _run(repo, "--branch", "feature/1-thing", "--trunk", "main")

        assert result.returncode == 0, "a checked-and-failed assumption is a verdict"
        assert "BASELINE: UNVERIFIED" in result.stdout
        assert "reason=no_impl_plan" in result.stdout

    def test_unverified_names_the_candidate_but_never_as_a_sha(self, tmp_path):
        """A caller scraping `sha=` must not silently receive an unvouched value.

        This is the discrimination the whole row is about: the original defect was a
        wrong value that looked exactly like a right one.
        """
        repo, _fork, first = _repo_with_feature_branch(tmp_path, first_commit_is_impl_plan=False)

        result = _run(repo, "--branch", "feature/1-thing", "--trunk", "main")

        assert "sha=" not in result.stdout
        assert f"candidate={first}" in result.stdout


class TestCannotJudge:
    def test_a_branch_with_no_commits_beyond_trunk_is_none(self, tmp_path):
        repo, _fork, _five_c = _repo_with_feature_branch(tmp_path)
        _git(repo, "checkout", "-q", "-b", "feature/empty", "main")

        result = _run(repo, "--branch", "feature/empty", "--trunk", "main")

        assert result.returncode == 0
        assert "BASELINE: NONE" in result.stdout
        assert "sha=" not in result.stdout

    def test_unknown_ref_is_an_operational_error_carrying_no_sha(self, tmp_path):
        repo, _fork, _five_c = _repo_with_feature_branch(tmp_path)

        result = _run(repo, "--branch", "feature/does-not-exist", "--trunk", "main")

        assert result.returncode == 2, "no verdict exists — this is not a judgement"
        assert "BASELINE: UNREADABLE" in result.stdout
        assert "sha=" not in result.stdout

    def test_outside_a_git_repository_is_unreadable(self, tmp_path):
        plain = tmp_path / "plain"
        plain.mkdir()

        result = _run(plain, "--branch", "main", "--trunk", "main")

        assert result.returncode == 2
        assert "BASELINE: UNREADABLE" in result.stdout

    def test_every_non_ok_verdict_omits_sha(self, tmp_path):
        """Swept rather than spot-checked: one new outcome that forgets this
        re-opens the exact hole — a cannot-judge that reads as a value."""
        repo, _fork, _five_c = _repo_with_feature_branch(tmp_path, first_commit_is_impl_plan=False)
        _git(repo, "checkout", "-q", "-b", "feature/empty", "main")

        outputs = [
            _run(repo, "--branch", "feature/1-thing", "--trunk", "main").stdout,
            _run(repo, "--branch", "feature/empty", "--trunk", "main").stdout,
            _run(repo, "--branch", "nope", "--trunk", "main").stdout,
        ]
        for out in outputs:
            assert "BASELINE: OK" not in out
            assert "sha=" not in out, out


def test_emits_the_h_mad_marker(tmp_path):
    repo, _fork, _five_c = _repo_with_feature_branch(tmp_path)
    result = _run(repo, "--branch", "feature/1-thing", "--trunk", "main")
    assert "[H-MAD]" in result.stdout


def test_skill_documents_the_derivation_and_forbids_merge_base():
    """The row's real fix is the contract, not the script: the wrong command is the
    one an operator reaches for, so SKILL.md must name it as wrong."""
    skill = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")
    assert "h_mad_baseline_sha.py" in skill
    assert "BASELINE:" in skill
    # BOTH consumption sites, not just one. 5f and 6a-prime each take a 5c sha and
    # each is read in isolation, so a warning present at only one of them leaves the
    # `merge-base` reflex intact wherever the reader happened to land.
    assert skill.count("never `git merge-base`") >= 2, (
        "the wrong command must be named as wrong at BOTH 5f and 6a-prime"
    )
