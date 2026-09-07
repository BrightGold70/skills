"""Phase 7f — the merge step Phase 7 never had.

5c creates `feature/NNN-<slug>`; Phase 7 is telemetry, report, archive, commit,
push; and `references/phase-table.md` states the exit as "Push to origin/main
succeeds". Nothing in between merges the branch, so the stated commands cannot
reach the stated exit — on a feature branch `git push origin main` pushes nothing
of the feature. The merge was done by hand every time and carried between
sessions as a handoff Next Step.

Every test builds a real repository. A fake git cannot answer the questions this
script asks (ancestry, tree hashes, worktree shape), and a fixture that models
them would be modelling the thing under test.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "h_mad_phase7_integrate.py"
sys.path.insert(0, str(SCRIPTS))

import h_mad_phase7_integrate as it  # noqa: E402


def git(repo: Path, *args: str) -> str:
    run = subprocess.run(["git", "-C", str(repo), *args],
                         capture_output=True, text=True, check=True)
    return run.stdout.strip()


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "t@example.com")
    git(root, "config", "user.name", "T")
    (root / "a.txt").write_text("one\n", encoding="utf-8")
    git(root, "add", "a.txt")
    git(root, "commit", "-qm", "base")
    return root


def feature(repo: Path, name: str = "feature/1-demo", *, commits: int = 1) -> str:
    git(repo, "checkout", "-q", "-b", name)
    for i in range(commits):
        (repo / f"f{i}.txt").write_text(f"{i}\n", encoding="utf-8")
        git(repo, "add", f"f{i}.txt")
        git(repo, "commit", "-qm", f"feat {i}")
    return name


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True)


def token(out: str) -> str:
    lines = [l for l in out.splitlines() if l.startswith("INTEGRATE:")]
    assert len(lines) == 1, f"expected exactly one verdict line, got {lines!r}"
    return lines[0]


class TestPlanIsTheDefault:
    """A merge is the one hard-to-undo step in the phase; it needs `--apply`."""

    def test_plans_without_touching_the_tree(self, repo: Path) -> None:
        branch = feature(repo)
        before = git(repo, "rev-parse", "main")
        result = run("--repo-root", str(repo), "--feature", "demo")
        assert result.returncode == 0, result.stderr
        assert token(result.stdout).startswith(
            f"INTEGRATE: PLANNED route=merge base=main branch={branch} ahead=1 identity=y")
        assert git(repo, "rev-parse", "main") == before, "planning moved main"
        assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == branch

    def test_the_plan_prints_the_exact_commands(self, repo: Path) -> None:
        branch = feature(repo)
        out = run("--repo-root", str(repo), "--feature", "demo").stdout
        assert f"git checkout main && git merge --no-ff {branch}" in out


class TestIdentity:
    """Superpowers reruns the suite on the merged result. When the base is
    strictly behind, the merged tree IS the branch tip's tree, so the run you
    already have covers the merge by identity — a proof, not a re-measurement."""

    def test_a_base_that_has_not_moved_yields_identity(self, repo: Path) -> None:
        feature(repo)
        assert "identity=y" in token(run("--repo-root", str(repo), "--feature", "d").stdout)

    def test_a_base_that_moved_does_not(self, repo: Path) -> None:
        branch = feature(repo)
        git(repo, "checkout", "-q", "main")
        (repo / "b.txt").write_text("moved\n", encoding="utf-8")
        git(repo, "add", "b.txt")
        git(repo, "commit", "-qm", "main moves")
        git(repo, "checkout", "-q", branch)
        out = run("--repo-root", str(repo), "--feature", "d").stdout
        assert "identity=n" in token(out)
        assert "re-run the suite" in out

    def test_apply_reports_identity_from_the_REAL_trees(self, repo: Path) -> None:
        """The plan PREDICTS from ancestry; the apply RE-READS the trees. This
        builds the case where the two disagree, because a test where they agree
        cannot tell a re-read from a prediction repeated back — the mutation that
        swaps one for the other survived exactly that test.

        Base moves with a change the branch already contains verbatim, so ancestry
        says behind=1 (identity predicted `n`) while the merged tree is in fact
        identical to the branch tip (`y`).
        """
        branch = feature(repo)
        (repo / "shared.txt").write_text("same\n", encoding="utf-8")
        git(repo, "add", "shared.txt")
        git(repo, "commit", "-qm", "branch adds shared")
        git(repo, "checkout", "-q", "main")
        (repo / "shared.txt").write_text("same\n", encoding="utf-8")
        git(repo, "add", "shared.txt")
        git(repo, "commit", "-qm", "main adds the same content")
        git(repo, "checkout", "-q", branch)

        planned = run("--repo-root", str(repo), "--feature", "d")
        assert "identity=n" in token(planned.stdout), "the PREDICTION must say n here"

        result = run("--repo-root", str(repo), "--feature", "d", "--apply")
        assert result.returncode == 0, result.stderr
        assert "identity=y" in token(result.stdout), (
            "after the merge the trees are identical, and the report must say so "
            "from the trees themselves, not from the prediction")
        assert git(repo, "rev-parse", "main^{tree}") == git(
            repo, "rev-parse", f"{branch}^{{tree}}")


class TestApply:
    def test_merges_no_ff_onto_the_base(self, repo: Path) -> None:
        branch = feature(repo, commits=2)
        result = run("--repo-root", str(repo), "--feature", "demo", "--apply")
        assert token(result.stdout).startswith("INTEGRATE: MERGED base=main")
        assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "main"
        assert branch in git(repo, "branch", "--merged", "main")
        # --no-ff: the merge is a commit of its own, not a fast-forward
        assert len(git(repo, "rev-list", "--merges", "main").splitlines()) == 1

    def test_merge_refuses_a_base_that_is_not_a_local_branch(self, repo: Path) -> None:
        """THE counterexample to the identity claim, and it is not in the merge
        algorithm: `git checkout <tag>` DETACHES, so the merge lands on nothing,
        the base ref never moves, the merge commit is unreferenced — and the
        verdict said MERGED at exit 0 while the plan had predicted identity=y.
        """
        branch = feature(repo)
        git(repo, "tag", "v1", "main")
        before = git(repo, "rev-parse", "main")

        result = run("--repo-root", str(repo), "--feature", "d", "--base", "v1", "--apply")
        assert "MERGED" not in result.stdout, result.stdout
        assert "base_not_a_local_branch:v1" in token(result.stdout)
        assert git(repo, "rev-parse", "main") == before, "the base moved"
        assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == branch, "HEAD detached"

    def test_the_api_refuses_a_non_branch_base_even_when_reached_directly(
            self, repo: Path) -> None:
        """The gate is in `merge()` as well as in `plan()`: a caller that reaches
        the function directly must not be able to detach the tree."""
        branch = feature(repo)
        git(repo, "tag", "v1", "main")
        with pytest.raises(it.GitError):
            it.merge(repo, "v1", branch, "m")
        assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == branch

    def test_never_pushes_and_never_deletes_the_branch(self, repo: Path) -> None:
        branch = feature(repo)
        run("--repo-root", str(repo), "--feature", "demo", "--apply")
        assert branch in git(repo, "branch", "--list", branch), "7f deleted a branch"


class TestBlockers:
    """Every blocker is a verdict about the world, so it exits 0 and names itself."""

    def test_a_dirty_tracked_tree_blocks(self, repo: Path) -> None:
        feature(repo)
        (repo / "a.txt").write_text("dirty\n", encoding="utf-8")
        result = run("--repo-root", str(repo), "--feature", "demo")
        assert result.returncode == 0
        assert "BLOCKED reason=dirty_tree:1_tracked_changes" in token(result.stdout)

    def test_untracked_done_markers_do_NOT_block(self, repo: Path) -> None:
        """The audit markers are untracked by design and counted, not committed."""
        feature(repo)
        (repo / "x.audit.v1.md.done").write_text("", encoding="utf-8")
        assert "PLANNED" in token(run("--repo-root", str(repo), "--feature", "d").stdout)

    def test_a_detached_head_blocks(self, repo: Path) -> None:
        feature(repo)
        git(repo, "checkout", "-q", "--detach")
        assert "detached_head" in token(run("--repo-root", str(repo), "--feature", "d").stdout)

    def test_being_on_the_base_blocks_the_merge_route(self, repo: Path) -> None:
        assert "base_is_the_feature_branch:main" in token(
            run("--repo-root", str(repo), "--feature", "d").stdout)

    def test_a_branch_with_nothing_new_blocks(self, repo: Path) -> None:
        feature(repo, commits=0)
        assert "nothing_to_integrate" in token(
            run("--repo-root", str(repo), "--feature", "d").stdout)

    def test_an_unknown_base_is_BLOCKED_not_unreadable(self, repo: Path) -> None:
        """git answered, and the answer was 'no such ref' — a fact, not a
        cannot-judge. The two must not take the same branch."""
        feature(repo)
        result = run("--repo-root", str(repo), "--feature", "d", "--base", "no-such")
        assert result.returncode == 0
        assert "BLOCKED reason=unknown_base:no-such" in token(result.stdout)

    def test_no_resolvable_default_base_is_BLOCKED(self, repo: Path) -> None:
        """A repo whose trunk is neither main nor master, with no origin/HEAD:
        git answered, so this is a fact about the world, not a cannot-judge."""
        git(repo, "branch", "-m", "main", "trunk")
        git(repo, "checkout", "-q", "-b", "feature/1-demo")
        (repo / "f.txt").write_text("f\n", encoding="utf-8")
        git(repo, "add", "f.txt")
        git(repo, "commit", "-qm", "feat")
        result = run("--repo-root", str(repo), "--feature", "d")
        assert result.returncode == 0, result.stderr
        assert "BLOCKED reason=no_default_base" in token(result.stdout)

    def test_a_default_base_comes_from_origin_HEAD_when_it_is_set(self, repo: Path) -> None:
        """Not a hardcoded `main`: the repo's own default wins."""
        git(repo, "branch", "-m", "main", "trunk")
        git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk")
        git(repo, "checkout", "-q", "-b", "feature/1-demo")
        (repo / "f.txt").write_text("f\n", encoding="utf-8")
        git(repo, "add", "f.txt")
        git(repo, "commit", "-qm", "feat")
        assert "base=trunk" in token(run("--repo-root", str(repo), "--feature", "d").stdout)

    def test_a_blocked_plan_moves_nothing(self, repo: Path) -> None:
        branch = feature(repo)
        (repo / "a.txt").write_text("dirty\n", encoding="utf-8")
        before = git(repo, "rev-parse", "main")
        run("--repo-root", str(repo), "--feature", "d", "--apply")
        assert git(repo, "rev-parse", "main") == before
        assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == branch


class TestRoutes:
    """Phase 7 is autonomous, so the route is RECORDED, never asked: a blocking
    three-option menu would break that contract."""

    def test_keep_integrates_nothing_and_is_not_a_failure(self, repo: Path) -> None:
        feature(repo)
        branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
        result = run("--repo-root", str(repo), "--feature", "d", "--route", "keep")
        assert token(result.stdout).startswith("INTEGRATE: KEPT route=keep")
        # `git branch --merged main` always lists main itself, so the discriminating
        # question is whether the FEATURE branch joined it.
        merged = {b.strip().lstrip("* ") for b in
                  git(repo, "branch", "--merged", "main").splitlines()}
        assert branch not in merged, f"keep merged {branch}"

    def test_keep_on_the_base_itself_is_still_KEPT(self, repo: Path) -> None:
        """A base-relative blocker must not make the honest no-op look failed."""
        assert "KEPT" in token(
            run("--repo-root", str(repo), "--feature", "d", "--route", "keep").stdout)

    def test_nothing_about_the_tree_blocks_keep(self, repo: Path) -> None:
        """`keep` performs nothing, so no fact about the tree can stop it. An
        earlier draft blocked it on a dirty tree while its own comment argued the
        opposite — the contradiction was pinned by a test rather than resolved."""
        feature(repo)
        (repo / "a.txt").write_text("dirty\n", encoding="utf-8")
        assert "KEPT" in token(
            run("--repo-root", str(repo), "--feature", "d", "--route", "keep").stdout)

    def test_a_dirty_tree_still_blocks_pr(self, repo: Path) -> None:
        """`pr` implies pushing a branch, which a dirty tree misrepresents."""
        feature(repo)
        (repo / "a.txt").write_text("dirty\n", encoding="utf-8")
        assert "dirty_tree" in token(
            run("--repo-root", str(repo), "--feature", "d", "--route", "pr").stdout)

    def test_pr_reports_the_real_commit_count(self, repo: Path) -> None:
        """It printed a hardcoded 0 for every branch: the counts were computed on
        the merge route alone."""
        feature(repo, commits=3)
        out = run("--repo-root", str(repo), "--feature", "d", "--route", "pr").stdout
        assert "3 commit(s) ahead" in out, out


class TestWorktreesAreReportedNeverRemoved:
    def test_a_MERGED_sibling_worktree_is_named_with_its_command(
            self, repo: Path, tmp_path: Path) -> None:
        sibling = tmp_path / "wt"
        # Branched from main with no commits of its own, so it IS merged into the
        # base — which is what makes it removable.
        git(repo, "worktree", "add", "-q", "-b", "feature/2-other", str(sibling), "main")
        feature(repo)
        out = run("--repo-root", str(repo), "--feature", "d").stdout
        assert "feature/2-other" in out and "git worktree remove" in out
        assert sibling.is_dir(), "7f removed a worktree"

    def test_an_UNMERGED_sibling_worktree_is_not_offered_for_removal(
            self, repo: Path, tmp_path: Path) -> None:
        """Merged-ness is checked, not assumed: an earlier draft listed every
        worktree but the current one and advised deleting a branch holding work."""
        branch = feature(repo)
        sibling = tmp_path / "wt"
        git(repo, "worktree", "add", "-q", "-b", "feature/3-live", str(sibling), branch)
        out = run("--repo-root", str(repo), "--feature", "d").stdout
        assert "feature/3-live" not in out

    def test_the_worktree_holding_the_base_blocks_rather_than_being_offered(
            self, repo: Path, tmp_path: Path) -> None:
        """Orca's sibling layout: the base is checked out in the primary worktree,
        so `git checkout <base>` dies. Say so up front instead of failing the merge
        after the plan said identity=y."""
        branch = feature(repo)
        sibling = tmp_path / "wt2"
        git(repo, "worktree", "add", "-q", str(sibling), "main")
        result = run("--repo-root", str(repo), "--feature", "d")
        assert "base_checked_out_elsewhere" in token(result.stdout), result.stdout
        assert "git worktree remove" not in result.stdout or "main" not in result.stdout


class TestCannotJudge:
    def test_a_non_repo_is_unreadable_and_exits_2(self, tmp_path: Path) -> None:
        result = run("--repo-root", str(tmp_path), "--feature", "d")
        assert result.returncode == 2
        assert token(result.stdout) == "INTEGRATE: UNREADABLE reason=not_a_repo", (
            "the reason must classify the failure; `giterror` is a constant the "
            "implementation cannot vary, so it diagnoses nothing")
        assert "base=" not in result.stdout, "a cannot-judge must carry no findings"


class TestDocumented:
    """A gate nobody is obliged to run is documentation, not a gate."""

    def _skill(self) -> str:
        return (SCRIPTS.parent / "SKILL.md").read_text(encoding="utf-8")

    def test_the_skill_routes_phase_7_through_7f(self) -> None:
        assert "h_mad_phase7_integrate.py" in self._skill()

    def test_the_skill_says_to_read_the_token(self) -> None:
        text = self._skill()
        assert "INTEGRATE:" in text
        after = text.split("h_mad_phase7_integrate.py", 1)[1][:1200]
        assert "never `$?`" in after

    def test_the_phase_table_lists_7f(self) -> None:
        table = (SCRIPTS.parent / "references" / "phase-table.md").read_text(encoding="utf-8")
        assert "7f" in table

    def test_no_step_stages_the_whole_tree(self) -> None:
        """`git add -A` stages the untracked audit `.done` markers — 88 of them in
        this repository at the time of writing — which every handoff for weeks
        carried a manual "do not commit" warning about. Gitignoring them is the
        wrong fix: `hmad-dispatch` COUNTS them (`^?? .*\\.done$`) for its tree
        delta, so ignoring them would blind a different measurement."""
        for name in ("SKILL.md", "references/phase-table.md"):
            text = (SCRIPTS.parent / name).read_text(encoding="utf-8")
            # Match the COMMAND FORM, not any line containing the substring: the
            # earlier line-scoped check passed only because the explanatory prose
            # shared a physical line with the corrected command, so reflowing that
            # paragraph would have turned it red with no behaviour change.
            # A STEP, not a mention: the prose deliberately quotes the bare bad
            # form to explain it, and no syntax rule separates that from an
            # instruction. What distinguishes a step is that it goes on to
            # commit — `git add -A … && git commit …` — so scope the check to
            # code spans carrying both verbs.
            steps = [span for span in re.findall(r"`([^`\n]*git add -A[^`\n]*)`", text)
                     if "git commit" in span]
            assert steps, f"{name}: no `git add -A … && git commit` step found at all"
            for command in steps:
                assert it.MARKER_EXCLUDE in command, (
                    f"{name}: `git add -A` without {it.MARKER_EXCLUDE!r}: {command[:120]}")
                assert it.ROOT_PATHSPEC in command, (
                    f"{name}: the sweep is CWD-relative, so from a subdirectory it "
                    f"stages only that subtree: {command[:120]}")
                assert it.TRACKED_SWEEP in command, (
                    f"{name}: no `git add -u` follow-up, so a TRACKED `.done` "
                    f"file's real modification is suppressed forever: {command[:120]}")
