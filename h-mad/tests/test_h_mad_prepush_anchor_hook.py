"""The push boundary was the one place anchor drift could still reach `main`.

Phase 5e sweeps sibling specs *inside a mutation run*, and `--check-anchors` is a
standalone diagnostic someone has to remember to invoke. Neither fires on an
ordinary refactor commit — which is precisely how anchors drift, since they break
as a side effect of unrelated edits. `git push` is the last boundary before the
drift is someone else's problem, and it was uncovered: this repository's
`.git/hooks` held nothing but samples while 19 specs sat in three directories.

Two properties are load-bearing and neither is obvious from reading the hook:

**It must be able to BLOCK, and it must be able to ALLOW, on the same input path.**
A hook that always exits 0 is indistinguishable from a correct one on a clean
tree, and it is the shape a `set -u` slip or a wrong `case` arm produces. Every
verdict below is asserted against a real harness invocation over a real temp git
repo, and the drift cases assert the blocking exit AND that the offending spec is
named — a block that cannot say what broke sends the reader back to a manual grep.

**"Nothing was measured" must never be spelled the same way as "nothing is wrong."**
Three distinct not-a-verdict states reach this hook — the harness is missing, the
sweep classified no spec (`ANCHORS_NOTHING_SWEPT`), and the harness produced no
`ANCHORS_*` token at all — and all three ALLOW the push, because blocking every
push in this clone on broken tooling is a worse failure than missing one drift.
Allowing silently would be a different bug, so each asserts its warning reaches
stderr. The one thing that legitimately says nothing is a repo with no candidate
JSON at all: nothing to guard is not a finding.

The specs in the temp repos are `git add`-ed deliberately. Discovery is
`git ls-files`, so an untracked spec is invisible to it — a fixture that forgot
the `git add` would exercise the empty-candidates path while appearing to test
drift detection, and would pass.
"""

import json
import os
import subprocess
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "git-hooks" / "pre-push"
INSTALLER = Path(__file__).resolve().parents[1] / "git-hooks" / "install.sh"
HARNESS = Path(__file__).resolve().parents[1] / "scripts" / "h_mad_mutation_harness.py"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, check=True,
    )


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "T")
    return repo


def _spec(repo: Path, rel: str, anchor: str, target_rel: str = "src/mod.py") -> Path:
    """A minimal, self-contained mutation spec whose anchor resolves in `repo`."""
    target = repo / target_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("def f():\n    return SENTINEL_VALUE\n", encoding="utf-8")

    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "root": os.path.relpath(repo, path.parent),
        "command": ["true"],
        "mutations": [{
            "name": "anchor-under-test",
            "file": target_rel,
            "find": anchor,
            "replace": "REPLACED",
        }],
    }, indent=2) + "\n", encoding="utf-8")
    return path


def _commit_all(repo: Path) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "specs")


def _run_hook(repo: Path, hook: Path = HOOK, **env_extra) -> subprocess.CompletedProcess:
    """Invoke the hook the way git does: cwd at the work tree, stdin closed."""
    env = dict(os.environ)
    env.pop("HMAD_MUTATION_SPEC_DIR", None)
    env.update({k: str(v) for k, v in env_extra.items()})
    return subprocess.run(
        [str(hook), "origin", "none"],
        cwd=str(repo), capture_output=True, text=True,
        stdin=subprocess.DEVNULL, env=env,
    )


class TestVerdicts:
    def test_clean_anchors_allow_and_stay_silent(self, tmp_path):
        repo = _init_repo(tmp_path)
        _spec(repo, "specs/ok.json", "SENTINEL_VALUE")
        _commit_all(repo)

        result = _run_hook(repo)

        assert result.returncode == 0
        # Silence is the contract on the happy path: a hook that narrates every
        # push trains the reader to skip its output on the one push that matters.
        assert result.stdout == ""
        assert result.stderr == ""

    def test_drifted_anchor_blocks_and_names_the_spec(self, tmp_path):
        repo = _init_repo(tmp_path)
        _spec(repo, "specs/drifted.json", "ANCHOR_THAT_CANNOT_MATCH")
        _commit_all(repo)

        result = _run_hook(repo)

        assert result.returncode == 1
        assert "pre-push BLOCKED" in result.stderr
        assert "drifted.json" in result.stderr
        assert "--no-verify" in result.stderr

    def test_one_drifted_spec_blocks_a_repo_of_clean_ones(self, tmp_path):
        """The sweep is over every spec, not the one you happened to touch."""
        repo = _init_repo(tmp_path)
        _spec(repo, "specs/ok.json", "SENTINEL_VALUE")
        _spec(repo, "other/bad.json", "ANCHOR_THAT_CANNOT_MATCH")
        _commit_all(repo)

        result = _run_hook(repo)

        assert result.returncode == 1
        assert "bad.json" in result.stderr


class TestNothingMeasuredAllows:
    """Three ways to measure nothing. All allow; none may do so silently."""

    def test_missing_harness_warns_and_allows(self, tmp_path):
        repo = _init_repo(tmp_path)
        _spec(repo, "specs/ok.json", "SENTINEL_VALUE")
        _commit_all(repo)

        # Copy the hook out of the skill so its self-relative harness lookup
        # fails, then point the documented fallback at an empty directory.
        detached = tmp_path / "pre-push"
        detached.write_bytes(HOOK.read_bytes())
        detached.chmod(0o755)
        empty_root = tmp_path / "no-skills"
        empty_root.mkdir()

        result = _run_hook(repo, hook=detached, CLAUDE_SKILLS_ROOT=empty_root)

        assert result.returncode == 0
        assert "mutation harness not found" in result.stderr

    def test_candidates_but_no_specs_warns_and_allows(self, tmp_path):
        repo = _init_repo(tmp_path)
        # Tracked JSON that is not a spec: the harness classifies and skips it,
        # leaving specs=0 -> ANCHORS_NOTHING_SWEPT.
        (repo / "package.json").write_text('{"name": "x"}\n', encoding="utf-8")
        _commit_all(repo)

        result = _run_hook(repo)

        assert result.returncode == 0
        assert "no mutation specs" in result.stderr
        assert "HMAD_MUTATION_SPEC_DIR" in result.stderr

    def test_no_candidate_json_at_all_is_silent(self, tmp_path):
        """Nothing to guard is not a finding — this is the only quiet allow."""
        repo = _init_repo(tmp_path)
        (repo / "README.md").write_text("hi\n", encoding="utf-8")
        _commit_all(repo)

        result = _run_hook(repo)

        assert result.returncode == 0
        assert result.stderr == ""

    def test_broken_harness_warns_and_allows(self, tmp_path):
        """No ANCHORS_* token at all is broken tooling, never drift."""
        repo = _init_repo(tmp_path)
        _spec(repo, "specs/ok.json", "SENTINEL_VALUE")
        _commit_all(repo)

        detached = tmp_path / "pre-push"
        detached.write_bytes(HOOK.read_bytes())
        detached.chmod(0o755)
        fake_root = tmp_path / "skills"
        fake_scripts = fake_root / "h-mad" / "scripts"
        fake_scripts.mkdir(parents=True)
        (fake_scripts / "h_mad_mutation_harness.py").write_text(
            "import sys\nsys.stderr.write('boom\\n')\nsys.exit(3)\n", encoding="utf-8")

        result = _run_hook(repo, hook=detached, CLAUDE_SKILLS_ROOT=fake_root)

        assert result.returncode == 0
        assert "no ANCHORS_* verdict" in result.stderr
        assert "Push ALLOWED" in result.stderr


class TestSpecResolution:
    def test_discovery_finds_specs_in_any_directory(self, tmp_path):
        """No naming convention, no configured directory — this is the point.

        A single spec-directory parameter is what this hook exists NOT to be:
        measured in the skills repo, the 19 specs live in three directories,
        one of them inside an unrelated skill.
        """
        repo = _init_repo(tmp_path)
        _spec(repo, "a/deep/nested/place/x.json", "ANCHOR_THAT_CANNOT_MATCH")
        _commit_all(repo)

        result = _run_hook(repo)

        assert result.returncode == 1
        assert "x.json" in result.stderr

    def test_untracked_spec_is_not_swept_under_discovery(self, tmp_path):
        """`git ls-files` is the discovery surface: a push publishes tracked work.

        This is asserted rather than merely true so the fixtures above cannot
        quietly stop testing what they claim — an un-added spec would otherwise
        exercise the empty-candidates path and still pass.
        """
        repo = _init_repo(tmp_path)
        (repo / "README.md").write_text("hi\n", encoding="utf-8")
        _commit_all(repo)
        _spec(repo, "specs/untracked.json", "ANCHOR_THAT_CANNOT_MATCH")  # never added

        result = _run_hook(repo)

        assert result.returncode == 0
        assert result.stderr == ""

    def test_env_override_sweeps_an_untracked_directory(self, tmp_path):
        """The escape hatch for exactly the case above."""
        repo = _init_repo(tmp_path)
        (repo / "README.md").write_text("hi\n", encoding="utf-8")
        _commit_all(repo)
        _spec(repo, "outside/untracked.json", "ANCHOR_THAT_CANNOT_MATCH")

        result = _run_hook(repo, HMAD_MUTATION_SPEC_DIR="outside")

        assert result.returncode == 1
        assert "untracked.json" in result.stderr

    def test_env_override_replaces_discovery_rather_than_adding_to_it(self, tmp_path):
        """An override that widened the sweep would be unable to narrow it."""
        repo = _init_repo(tmp_path)
        _spec(repo, "tracked/bad.json", "ANCHOR_THAT_CANNOT_MATCH")
        _spec(repo, "chosen/ok.json", "SENTINEL_VALUE")
        _commit_all(repo)

        result = _run_hook(repo, HMAD_MUTATION_SPEC_DIR="chosen")

        assert result.returncode == 0, result.stderr
        assert "bad.json" not in result.stderr

    def test_env_override_accepts_multiple_colon_separated_directories(self, tmp_path):
        repo = _init_repo(tmp_path)
        _spec(repo, "one/ok.json", "SENTINEL_VALUE")
        _spec(repo, "two/bad.json", "ANCHOR_THAT_CANNOT_MATCH")
        _commit_all(repo)

        result = _run_hook(repo, HMAD_MUTATION_SPEC_DIR="one:two")

        assert result.returncode == 1
        assert "bad.json" in result.stderr

    def test_absent_override_directory_does_not_crash_the_hook(self, tmp_path):
        repo = _init_repo(tmp_path)
        (repo / "README.md").write_text("hi\n", encoding="utf-8")
        _commit_all(repo)

        result = _run_hook(repo, HMAD_MUTATION_SPEC_DIR="nowhere")

        assert result.returncode == 0


class TestInstaller:
    def _install(self, repo: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [str(INSTALLER), *args],
            cwd=str(repo), capture_output=True, text=True,
            stdin=subprocess.DEVNULL,
        )

    def test_installs_a_symlink_and_smoke_tests_it(self, tmp_path):
        repo = _init_repo(tmp_path)
        _spec(repo, "specs/ok.json", "SENTINEL_VALUE")
        _commit_all(repo)

        result = self._install(repo)

        dest = repo / ".git" / "hooks" / "pre-push"
        assert result.returncode == 0, result.stderr
        assert dest.is_symlink()
        # A symlink, never a copy: a copied hook drifts from the skill silently.
        assert Path(os.readlink(dest)) == HOOK
        assert "verified" in result.stdout

    def test_reinstall_is_idempotent(self, tmp_path):
        repo = _init_repo(tmp_path)
        _spec(repo, "specs/ok.json", "SENTINEL_VALUE")
        _commit_all(repo)
        self._install(repo)

        result = self._install(repo)

        assert result.returncode == 0
        assert "already installed" in result.stdout

    def test_foreign_hook_is_backed_up_not_destroyed(self, tmp_path):
        repo = _init_repo(tmp_path)
        _spec(repo, "specs/ok.json", "SENTINEL_VALUE")
        _commit_all(repo)
        dest = repo / ".git" / "hooks" / "pre-push"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("#!/bin/sh\n# someone else's hook\nexit 0\n", encoding="utf-8")

        result = self._install(repo)

        assert result.returncode == 0, result.stderr
        backups = list(dest.parent.glob("pre-push.bak.*"))
        assert len(backups) == 1
        assert "someone else's hook" in backups[0].read_text(encoding="utf-8")

    def test_uninstall_leaves_a_foreign_hook_in_place(self, tmp_path):
        repo = _init_repo(tmp_path)
        (repo / "README.md").write_text("hi\n", encoding="utf-8")
        _commit_all(repo)
        dest = repo / ".git" / "hooks" / "pre-push"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

        result = self._install(repo, "--uninstall")

        assert result.returncode == 0
        assert "not our symlink" in result.stdout
        assert dest.exists()

    def test_uninstall_removes_our_symlink(self, tmp_path):
        repo = _init_repo(tmp_path)
        _spec(repo, "specs/ok.json", "SENTINEL_VALUE")
        _commit_all(repo)
        self._install(repo)

        result = self._install(repo, "--uninstall")

        assert result.returncode == 0
        assert "uninstalled" in result.stdout
        assert not (repo / ".git" / "hooks" / "pre-push").exists()

    def test_refuses_when_core_hookspath_is_set(self, tmp_path):
        """Git would read hooks from elsewhere; installing here is a no-op that
        reports success — the exact shape of a guard that never runs."""
        repo = _init_repo(tmp_path)
        (repo / "README.md").write_text("hi\n", encoding="utf-8")
        _commit_all(repo)
        _git(repo, "config", "core.hooksPath", str(tmp_path / "elsewhere"))

        result = self._install(repo)

        assert result.returncode == 1
        assert "core.hooksPath" in result.stderr
        assert not (repo / ".git" / "hooks" / "pre-push").exists()

    def test_repo_flag_targets_another_clone(self, tmp_path):
        """`--git-common-dir` alone returns a RELATIVE `.git`, so an installer
        that forgets `--path-format=absolute` links into the CALLER's repo and
        reports success about the wrong one."""
        target = _init_repo(tmp_path)
        _spec(target, "specs/ok.json", "SENTINEL_VALUE")
        _commit_all(target)
        caller = tmp_path / "caller"
        caller.mkdir()
        subprocess.run(["git", "-C", str(caller), "init", "-q"], check=True)

        result = subprocess.run(
            [str(INSTALLER), "--repo", str(target)],
            cwd=str(caller), capture_output=True, text=True, stdin=subprocess.DEVNULL,
        )

        assert result.returncode == 0, result.stderr
        assert (target / ".git" / "hooks" / "pre-push").is_symlink()
        assert not (caller / ".git" / "hooks" / "pre-push").exists()

    def test_installs_from_a_subdirectory_of_the_repo(self, tmp_path):
        """Where the operator happens to stand must not decide where the hook lands.

        From a subdirectory `git rev-parse --git-common-dir` returns `../../.git`;
        an installer that mishandles that creates `<subdir>/.git/hooks/`, reports
        `installed`, and arms nothing git will ever read.
        """
        repo = _init_repo(tmp_path)
        _spec(repo, "specs/ok.json", "SENTINEL_VALUE")
        (repo / "sub" / "deep").mkdir(parents=True)
        _commit_all(repo)

        result = subprocess.run(
            [str(INSTALLER)], cwd=str(repo / "sub" / "deep"),
            capture_output=True, text=True, stdin=subprocess.DEVNULL,
        )

        assert result.returncode == 0, result.stderr
        assert (repo / ".git" / "hooks" / "pre-push").is_symlink()
        assert not (repo / "sub" / "deep" / ".git").exists()

    def test_installs_from_a_linked_worktree_into_the_common_dir(self, tmp_path):
        """`install.sh`'s header claims one install covers every worktree.

        That is true only because the hook goes to the COMMON dir. Installing
        into a linked worktree's own gitdir would arm that worktree alone while
        the message says otherwise.
        """
        repo = _init_repo(tmp_path)
        _spec(repo, "specs/ok.json", "SENTINEL_VALUE")
        _commit_all(repo)
        linked = tmp_path / "linked"
        _git(repo, "worktree", "add", "-q", str(linked), "-b", "side")

        result = subprocess.run(
            [str(INSTALLER)], cwd=str(linked),
            capture_output=True, text=True, stdin=subprocess.DEVNULL,
        )

        assert result.returncode == 0, result.stderr
        assert (repo / ".git" / "hooks" / "pre-push").is_symlink()

    def test_smoke_test_reports_a_hook_that_would_block_every_push(self, tmp_path):
        """Installing a hook that blocks the current tree is the one outcome the
        operator must not discover on their next push."""
        repo = _init_repo(tmp_path)
        _spec(repo, "specs/bad.json", "ANCHOR_THAT_CANNOT_MATCH")
        _commit_all(repo)

        result = self._install(repo)

        assert result.returncode == 1
        assert "will block pushes" in result.stderr
        # It is still installed — the operator asked for it; the warning tells
        # them how to back out.
        assert (repo / ".git" / "hooks" / "pre-push").is_symlink()

    def test_refuses_outside_a_git_repository(self, tmp_path):
        plain = tmp_path / "plain"
        plain.mkdir()

        result = subprocess.run(
            [str(INSTALLER)], cwd=str(plain),
            capture_output=True, text=True, stdin=subprocess.DEVNULL,
        )

        assert result.returncode == 2
        assert "not inside a git repository" in result.stderr


def test_hook_and_installer_are_executable():
    """A committed hook without the mode bit installs fine and never runs."""
    assert os.access(HOOK, os.X_OK)
    assert os.access(INSTALLER, os.X_OK)


def test_harness_is_where_the_hook_looks_for_it():
    assert HARNESS.is_file()
