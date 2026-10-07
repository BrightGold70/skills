"""Run every published `# expect <N>` screen AT a freeze sha, not at HEAD.

Skill-candidates row "run every published `expect 0` screen at the freeze sha
before certifying 'no census moved'": three decision-sheet entries certified
that a tooling commit moved no scoped census while the design's own published
trip-wire read 8 at that commit; nobody ran it (#49w). The documents publish
these screens with their commands, so a freeze-certification step can execute
them. `h_mad_expect_screens.py` is that step.

The core property every test leans on: the screen is evaluated in a throwaway
detached worktree AT the named sha. The project root's working tree is never
used, so a dirty root, an untracked file, or a newer HEAD cannot change a
reading, and the throwaway worktree is always removed.
"""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "h-mad" / "scripts" / "h_mad_expect_screens.py"
FENCE = "```"
sys.path.insert(0, str(SCRIPT.parent))
import h_mad_expect_screens as hes  # noqa: E402


def _git(cwd, *args):
    return subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "-C", str(cwd), *args],
        check=True, capture_output=True, text=True).stdout.strip()


def _repo(tmp_path):
    """Two commits: `a.txt` has no BAD line at OLD and one at NEW."""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")
    _git(root, "config", "commit.gpgsign", "false")
    (root / "a.txt").write_text("ok\n")
    _git(root, "add", "a.txt")
    _git(root, "commit", "-q", "-m", "one")
    old = _git(root, "rev-parse", "HEAD")
    (root / "a.txt").write_text("ok\nBAD\n")
    _git(root, "commit", "-q", "-am", "two")
    new = _git(root, "rev-parse", "HEAD")
    return root, old, new


def _doc(tmp_path, body, name="doc.md"):
    path = tmp_path / name
    path.write_text(body)
    return path


def _tmpdir(tmp_path):
    d = tmp_path / "tmpd"
    d.mkdir(exist_ok=True)
    return d


def _argv(docs, root, sha, *extra):
    return [sys.executable, str(SCRIPT), *map(str, docs), f"--at={sha}",
            "--project-root", str(root), *extra]


def run(tmp_path, docs, root, sha, *extra, stdin_text=None, env_extra=None):
    env = dict(os.environ, TMPDIR=str(_tmpdir(tmp_path)), **(env_extra or {}))
    kwargs = {"input": stdin_text} if stdin_text is not None else {"stdin": subprocess.DEVNULL}
    return subprocess.run(_argv(docs, root, sha, *extra),
                          capture_output=True, text=True, timeout=120, env=env, **kwargs)


def _screens(out):
    return [line for line in out.splitlines() if line.startswith("screen: ")]


def _worktrees(root):
    return [line for line in _git(root, "worktree", "list", "--porcelain").splitlines()
            if line.startswith("worktree ")]


CORE = f"""# Screens

{FENCE}bash
W=BAD
grep -c "$W" a.txt \\
  | tr -d ' '   # expect 0
{FENCE}
"""


def test_a_screen_passes_at_the_old_sha_and_fails_at_the_new_one(tmp_path):
    root, old, new = _repo(tmp_path)
    doc = _doc(tmp_path, CORE)
    at_old = run(tmp_path, [doc], root, old)
    assert at_old.returncode == 0, at_old.stdout + at_old.stderr
    assert _screens(at_old.stdout) == [f"screen: {doc}:6 expect=0 got=0 PASS"]
    assert "EXPECT: PASS screens=1" in at_old.stdout
    at_new = run(tmp_path, [doc], root, new)
    assert at_new.returncode == 1, at_new.stdout + at_new.stderr
    assert _screens(at_new.stdout) == [f"screen: {doc}:6 expect=0 got=1 FAIL"]
    assert "EXPECT: FAIL screens=1 failed=1 unreadable=0" in at_new.stdout


def test_the_screen_reads_the_sha_not_the_dirty_root_and_leaves_the_root_untouched(tmp_path):
    root, old, _ = _repo(tmp_path)
    (root / "a.txt").write_text("BAD\nBAD\n")  # uncommitted: would read 2 in the root
    (root / "untracked.txt").write_text("x\n")
    before = _git(root, "status", "--porcelain")
    doc = _doc(tmp_path, f"""{FENCE}bash
touch made-by-screen
grep -c BAD a.txt   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert result.returncode == 0, result.stdout + result.stderr
    assert _screens(result.stdout) == [f"screen: {doc}:3 expect=0 got=0 PASS"]
    assert not (root / "made-by-screen").exists()
    assert (root / "a.txt").read_text() == "BAD\nBAD\n"
    assert _git(root, "status", "--porcelain") == before


def test_a_backslash_continuation_is_one_statement(tmp_path):
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
printf '%s\\n' a b \\
  c | wc -l | tr -d ' '   # expect 3
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [f"screen: {doc}:3 expect=3 got=3 PASS"], result.stdout
    assert result.returncode == 0


def test_the_published_backslash_then_leading_pipe_shape_is_one_statement(tmp_path):
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
printf 'a\\nb\\n' \\
  | grep -c . \\
  | tr -d ' '   # expect 2
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [f"screen: {doc}:4 expect=2 got=2 PASS"], result.stdout


def test_a_trailing_pipe_continuation_is_one_statement(tmp_path):
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
printf 'a\\nb\\n' |
  wc -l | tr -d ' '   # expect 2
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [f"screen: {doc}:3 expect=2 got=2 PASS"], result.stdout


def test_variables_from_the_preamble_reach_the_screen(tmp_path):
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
D=a.txt
STRIP='/ok/ {{ next }}
       {{ print }}'
awk "$STRIP" "$D" | wc -l | tr -d ' '   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [f"screen: {doc}:5 expect=0 got=0 PASS"], result.stdout


def test_other_comments_are_not_screens_and_annotations_after_the_integer_are(tmp_path):
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
echo 5   # NOT 0: classify each
echo 4   # expect 4 methods x 2
echo 0   # expect 0 (VACUOUS while BASE==HEAD)
echo 0   # expect 0, run IMMEDIATELY after M
# expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [
        f"screen: {doc}:4 expect=0 got=0 PASS",
        f"screen: {doc}:5 expect=0 got=0 PASS",
    ], result.stdout
    assert "EXPECT: PASS screens=2" in result.stdout


def test_untagged_and_non_shell_blocks_are_never_run(tmp_path):
    root, old, _ = _repo(tmp_path)
    sentinel = tmp_path / "ran"
    doc = _doc(tmp_path, f"""{FENCE}bash
touch {sentinel}
{FENCE}

{FENCE}python
open({str(sentinel)!r}, "w")  # expect 0
{FENCE}

~~~sh
echo 0   # expect 0
~~~
""")
    result = run(tmp_path, [doc], root, old)
    assert not sentinel.exists()
    assert _screens(result.stdout) == [f"screen: {doc}:10 expect=0 got=0 PASS"], result.stdout


def test_a_block_that_dies_inside_the_screen_is_unreadable_not_pass(tmp_path):
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
echo 0; exit 0   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert result.returncode == 1, result.stdout
    [line] = _screens(result.stdout)
    assert line.startswith(f"screen: {doc}:2 expect=0 got=UNREADABLE:") and line.endswith(" FAIL")
    assert "EXPECT: FAIL screens=1 failed=0 unreadable=1" in result.stdout


def test_a_screen_inside_a_loop_is_unreadable(tmp_path):
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
for i in 1 2; do
  echo 0   # expect 0
done
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert result.returncode == 1, result.stdout
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:markers_repeated FAIL"], result.stdout


def test_a_failing_pipeline_member_is_unreadable_even_when_the_count_is_zero(tmp_path):
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
grep BAD missing.txt | wc -l | tr -d ' '   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert result.returncode == 1, result.stdout
    assert _screens(result.stdout) == [
        f"screen: {doc}:2 expect=0 got=UNREADABLE:exit_status=2,0,0 FAIL"], result.stdout


def test_non_integer_and_empty_output_are_unreadable(tmp_path):
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
echo zero   # expect 0
true   # expect 0
printf '0\\n0\\n'   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert result.returncode == 1
    assert _screens(result.stdout) == [
        f"screen: {doc}:2 expect=0 got=UNREADABLE:non_integer FAIL",
        f"screen: {doc}:3 expect=0 got=UNREADABLE:empty_output FAIL",
        f"screen: {doc}:4 expect=0 got=UNREADABLE:non_integer FAIL",
    ], result.stdout
    assert "EXPECT: FAIL screens=3 failed=0 unreadable=3" in result.stdout


def test_a_timeout_is_unreadable_and_the_worktree_is_still_removed(tmp_path):
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
sleep 30; echo 0   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old, "--timeout", "1")
    assert result.returncode == 1, result.stdout + result.stderr
    assert _screens(result.stdout) == [f"screen: {doc}:2 expect=0 got=UNREADABLE:timeout FAIL"]
    assert len(_worktrees(root)) == 1
    assert list(_tmpdir(tmp_path).iterdir()) == []


def test_the_worktree_is_removed_after_every_run(tmp_path):
    root, old, new = _repo(tmp_path)
    doc = _doc(tmp_path, CORE)
    for sha in (old, new):
        result = run(tmp_path, [doc], root, sha)
        assert len(_screens(result.stdout)) == 1, result.stdout + result.stderr
        assert len(_worktrees(root)) == 1
        assert list(_tmpdir(tmp_path).iterdir()) == []
    admin = root / ".git" / "worktrees"
    assert not admin.exists() or list(admin.iterdir()) == []


def test_a_bad_sha_cannot_judge(tmp_path):
    root, _, _ = _repo(tmp_path)
    doc = _doc(tmp_path, CORE)
    blob = _git(root, "rev-parse", "HEAD:a.txt")
    for sha in ("deadbeef", blob, "-p"):
        result = run(tmp_path, [doc], root, sha)
        assert result.returncode == 2, (sha, result.stdout, result.stderr)
        assert f"EXPECT: CANNOT_JUDGE reason=not_a_commit sha={sha}" in result.stdout
        assert "EXPECT: PASS" not in result.stdout
    assert len(_worktrees(root)) == 1


def test_an_unreadable_doc_cannot_judge(tmp_path):
    root, old, _ = _repo(tmp_path)
    result = run(tmp_path, [tmp_path / "missing.md"], root, old)
    assert result.returncode == 2
    assert "EXPECT: CANNOT_JUDGE" in result.stdout


def test_no_tagged_screen_is_none_not_pass(tmp_path):
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
echo 0   # NOT 0: classify each
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert result.returncode == 3, result.stdout
    assert "EXPECT: NONE" in result.stdout
    assert "EXPECT: PASS" not in result.stdout


def test_a_subdirectory_root_runs_the_screens_in_that_subdirectory(tmp_path):
    root, _, _ = _repo(tmp_path)
    (root / "sub").mkdir()
    (root / "sub" / "f.txt").write_text("x\n")
    _git(root, "add", "sub/f.txt")
    _git(root, "commit", "-q", "-m", "sub")
    sha = _git(root, "rev-parse", "HEAD")
    doc = _doc(tmp_path, f"""{FENCE}bash
ls f.txt | wc -l | tr -d ' '   # expect 1
{FENCE}
""")
    result = run(tmp_path, [doc], root / "sub", sha)
    assert _screens(result.stdout) == [f"screen: {doc}:2 expect=1 got=1 PASS"], result.stdout


def test_screens_across_documents_are_all_counted(tmp_path):
    root, _, new = _repo(tmp_path)
    one = _doc(tmp_path, CORE, "one.md")
    two = _doc(tmp_path, f"""{FENCE}bash
echo 0   # expect 0
{FENCE}
""", "two.md")
    result = run(tmp_path, [one, two], root, new)
    assert _screens(result.stdout) == [
        f"screen: {one}:6 expect=0 got=1 FAIL",
        f"screen: {two}:2 expect=0 got=0 PASS",
    ]
    assert "EXPECT: FAIL screens=2 failed=1 unreadable=0" in result.stdout


def test_the_output_says_only_comment_tagged_screens_are_covered(tmp_path):
    root, old, _ = _repo(tmp_path)
    result = run(tmp_path, [_doc(tmp_path, CORE)], root, old)
    assert "coverage: only statements ending in a '# expect <N>' comment" in result.stdout


# --- review of 5cba8c6b: one test per finding, RED before the fix -----------------


def test_a_pipe_continued_after_a_trailing_comment_is_one_statement(tmp_path):
    """M1: `cmd |   # note` continues the pipeline; a marker there split it and read stdin."""
    root, _, new = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
grep BAD a.txt |   # filter the census
  grep -c BAD   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, new)
    assert _screens(result.stdout) == [f"screen: {doc}:3 expect=0 got=1 FAIL"], result.stdout
    assert result.returncode == 1


def test_a_pipe_continued_across_a_blank_line_is_one_statement(tmp_path):
    """M1: a blank line after a trailing `|` still continues the pipeline."""
    root, _, new = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
grep BAD a.txt |

  grep -c BAD   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, new)
    assert _screens(result.stdout) == [f"screen: {doc}:4 expect=0 got=1 FAIL"], result.stdout


def test_a_failed_assignment_before_the_screen_is_unreadable(tmp_path):
    """M2: an empty `$B` collapses `$B..HEAD` to `..HEAD`, which reads 0 and PASSED."""
    root, _, new = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
B=$(git rev-parse --verify --quiet nosuchref)
git log --oneline $B..HEAD | wc -l | tr -d ' '   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, new)
    assert result.returncode == 1, result.stdout
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:failed_command={doc}:2:1 FAIL"], result.stdout


def test_a_command_erroring_before_the_screen_is_unreadable(tmp_path):
    """M2: an exit >= 2 anywhere before the screen leaves its reading unreadable."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
grep BAD missing.txt
echo 0   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:failed_command={doc}:2:2 FAIL"], result.stdout


def test_a_no_match_inside_a_screen_does_not_poison_the_next(tmp_path):
    """The measured grep's exit 1 IS the reading (a count of 0): inside a screen it is judged
    by the screen's own per-member statuses, and it never poisons a later screen."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
grep -c BAD a.txt   # expect 0
echo 0   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [
        f"screen: {doc}:2 expect=0 got=0 PASS",
        f"screen: {doc}:3 expect=0 got=0 PASS",
    ], result.stdout


def test_sigterm_kills_the_block_and_removes_the_worktree(tmp_path):
    """M3: SIGTERM ran no `finally`; the worktree stayed registered and the block ran on."""
    root, old, _ = _repo(tmp_path)
    pidf, started = tmp_path / "child.pid", tmp_path / "started"
    doc = _doc(tmp_path, f"""{FENCE}bash
echo $$ > {pidf}
touch {started}
sleep 30; echo 0   # expect 0
{FENCE}
""")
    env = dict(os.environ, TMPDIR=str(_tmpdir(tmp_path)))
    proc = subprocess.Popen(_argv([doc], root, old), stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    deadline = time.time() + 30
    while not started.exists() and time.time() < deadline:
        time.sleep(0.1)
    assert started.exists()
    proc.send_signal(signal.SIGTERM)
    out, err = proc.communicate(timeout=60)
    assert proc.returncode == 2, (proc.returncode, out, err)
    assert "EXPECT: CANNOT_JUDGE reason=terminated" in out
    assert len(_worktrees(root)) == 1
    assert list(_tmpdir(tmp_path).iterdir()) == []
    child = int(pidf.read_text())
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            os.kill(child, 0)
        except ProcessLookupError:
            break
        time.sleep(0.2)
    else:
        raise AssertionError(f"block pid {child} still alive")


def test_another_worktrees_entry_survives_a_run(tmp_path):
    """M4: a repo-wide `worktree prune` deleted a moved-away worktree's entry."""
    root, old, _ = _repo(tmp_path)
    other = tmp_path / "other"
    _git(root, "worktree", "add", "-q", "--detach", str(other), old)
    other.rename(tmp_path / "moved")
    before = _worktrees(root)
    assert len(before) == 2
    result = run(tmp_path, [_doc(tmp_path, CORE)], root, old)
    assert result.returncode == 0, result.stdout + result.stderr
    assert _worktrees(root) == before


def test_a_block_that_deletes_its_worktree_still_leaves_no_entry(tmp_path):
    """M4's fallback: when `worktree remove` cannot, only this run's own entry is deleted."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
W=$(git rev-parse --show-toplevel)
case "$W" in *hmad-expect-*) cd /; rm -rf "$W";; esac
echo 0   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [f"screen: {doc}:4 expect=0 got=0 PASS"], result.stdout
    assert len(_worktrees(root)) == 1
    admin = root / ".git" / "worktrees"
    assert not admin.exists() or list(admin.iterdir()) == []
    assert list(_tmpdir(tmp_path).iterdir()) == []


def test_an_inherited_git_dir_does_not_redirect_the_reading(tmp_path):
    """M5: GIT_DIR from a hook made every screen read the caller's HEAD, not the sha."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
git log --oneline | wc -l | tr -d ' '   # expect 1
{FENCE}
""")
    result = run(tmp_path, [doc], root, old, env_extra={"GIT_DIR": str(root / ".git")})
    assert _screens(result.stdout) == [f"screen: {doc}:2 expect=1 got=1 PASS"], result.stdout


def test_a_heredoc_screen_reads_through_its_terminator(tmp_path):
    """S1: the end marker went into the heredoc body."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
wc -l <<'X' | tr -d ' '   # expect 2
a
b
X
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [f"screen: {doc}:2 expect=2 got=2 PASS"], result.stdout


def test_a_tagged_line_inside_a_heredoc_body_is_never_run_and_the_body_is_untouched(tmp_path):
    """S1: markers were written into the file the heredoc creates. Round 2: the body line is
    counted UNREADABLE:unparsed rather than dropped, and is never instrumented."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
cat > notes.txt <<'X'
x   # expect 0
X
wc -l < notes.txt | tr -d ' '   # expect 1
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unparsed FAIL",
        f"screen: {doc}:5 expect=1 got=1 PASS",
    ], result.stdout


def test_a_pipe_continued_after_a_heredoc_terminator_is_one_statement(tmp_path):
    """S1: `cat <<X |` continues the pipeline after the terminator line."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
cat <<'X' |
a
X
wc -l | tr -d ' '   # expect 1
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [f"screen: {doc}:5 expect=1 got=1 PASS"], result.stdout


def test_a_leading_pipe_without_a_backslash_is_unreadable(tmp_path):
    """S2: a leading `|` with no backslash is a bash syntax error, so it can never PASS."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
printf 'a\\nb\\n'
  | wc -l | tr -d ' '   # expect 2
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    [line] = _screens(result.stdout)
    assert "got=UNREADABLE:" in line and line.endswith(" FAIL"), result.stdout


def test_a_failed_worktree_add_cannot_judge(tmp_path):
    """S3: the worktree-add failure path had no test."""
    root, old, _ = _repo(tmp_path)
    (root / ".git" / "worktrees").write_text("not a directory\n")
    result = run(tmp_path, [_doc(tmp_path, CORE)], root, old)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "EXPECT: CANNOT_JUDGE reason=worktree_add_failed" in result.stdout
    assert list(_tmpdir(tmp_path).iterdir()) == []


def test_the_block_never_reads_the_callers_stdin(tmp_path):
    """S4: a screen's reading depended on what the caller piped in."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
wc -l | tr -d ' '   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old, stdin_text="a\nb\n")
    assert _screens(result.stdout) == [f"screen: {doc}:2 expect=0 got=0 PASS"], result.stdout


def test_the_output_states_the_absolute_path_residual(tmp_path):
    """S5: a block can leave the worktree by absolute path; the coverage line says so."""
    root, old, _ = _repo(tmp_path)
    result = run(tmp_path, [_doc(tmp_path, CORE)], root, old)
    assert "absolute path" in result.stdout.splitlines()[-1], result.stdout


def test_an_end_marker_without_statuses_is_unreadable():
    """N1: an end marker with no PIPESTATUS was read as a clean pipeline."""
    got, verdict = hes.read_screen("\nHMADB_n_0\n0\n\nHMADE_n_0 \n", "n", 0, 0)
    assert got.startswith("UNREADABLE:") and verdict == "FAIL"


def test_an_end_marker_without_a_begin_marker_is_labelled_mangled():
    """N2: begin=0, end=1 was reported as repeated markers."""
    got, verdict = hes.read_screen("\n0\n\nHMADE_n_0 0|\n", "n", 0, 0)
    assert (got, verdict) == ("UNREADABLE:markers_mangled", "FAIL")


def test_an_expect_inside_a_quoted_string_is_never_run(tmp_path):
    """N3: `echo "a # expect 0, b"` was run as a screen (got=non_integer). Round 2: it is
    counted UNREADABLE:unparsed rather than dropped, and never run."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
echo "a # expect 0, b"
echo 0   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [
        f"screen: {doc}:2 expect=0 got=UNREADABLE:unparsed FAIL",
        f"screen: {doc}:3 expect=0 got=0 PASS",
    ], result.stdout


def test_a_quoted_string_spanning_lines_is_one_statement(tmp_path):
    """M1/S1: a marker inserted inside a multi-line quoted string corrupted the string."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
printf '%s\\n' 'a
b' | wc -l | tr -d ' '   # expect 2
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [f"screen: {doc}:3 expect=2 got=2 PASS"], result.stdout


def test_an_erroring_member_before_a_no_match_count_is_unreadable(tmp_path):
    """M2's trap is disarmed inside screens: armed, it hid this member's exit 2."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
grep BAD missing.txt | grep -c x   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [
        f"screen: {doc}:2 expect=0 got=UNREADABLE:exit_status=2,1 FAIL"], result.stdout


def test_a_failure_between_screens_poisons_only_the_later_one(tmp_path):
    """M2: the trap is re-armed after each screen, and a failure counts only for later screens."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
echo 0   # expect 0
grep BAD missing.txt
echo 0   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [
        f"screen: {doc}:2 expect=0 got=0 PASS",
        f"screen: {doc}:4 expect=0 got=UNREADABLE:failed_command={doc}:3:2 FAIL",
    ], result.stdout


def test_an_end_marker_with_an_empty_status_field_is_unreadable():
    """N1: `HMADE_… |` carries no PIPESTATUS at all; it must not read as clean."""
    got, verdict = hes.read_screen("\nHMADB_n_0\n0\n\nHMADE_n_0 |\n", "n", 0, 0)
    assert got.startswith("UNREADABLE:") and verdict == "FAIL"


def test_a_block_that_locks_its_worktree_still_leaves_no_entry(tmp_path):
    """M4's fallback: `worktree remove --force` refuses a locked worktree; only this run's entry is deleted."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
git worktree lock --reason pinned "$(git rev-parse --show-toplevel)"
echo 0   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [f"screen: {doc}:3 expect=0 got=0 PASS"], result.stdout
    assert result.returncode == 0, result.stdout
    assert len(_worktrees(root)) == 1
    admin = root / ".git" / "worktrees"
    assert not admin.exists() or list(admin.iterdir()) == []


def test_a_failing_heredoc_command_is_reported_at_its_opening_line(tmp_path):
    """Calibration: bash reports a heredoc command at its terminator; the reason names the opener."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
./no-such-tool - <<'PY'
print(1)
PY
echo 0   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [
        f"screen: {doc}:5 expect=0 got=UNREADABLE:failed_command={doc}:2:127 FAIL"], result.stdout


# --- review round 2 of e8ccef63 ----------------------------------------------------

PASSING_BLOCK = f"""{FENCE}bash
echo 0   # expect 0
{FENCE}

"""


def test_a_heredoc_marker_inside_quotes_does_not_hide_later_screens(tmp_path):
    """R2-M1(a): `'<<EOF'` in a quoted grep pattern turned every later line into a heredoc body.
    (The blank after `EOF` keeps the delimiter a whole word, so a heredoc read in quotes
    would still match since round 10.)"""
    root, _, new = _repo(tmp_path)
    doc = _doc(tmp_path, PASSING_BLOCK + f"""{FENCE}bash
N=$(awk '/<<EOF /{{n++}} END{{print n+0}}' a.txt)
grep -c BAD a.txt   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, new)
    assert _screens(result.stdout) == [
        f"screen: {doc}:2 expect=0 got=0 PASS",
        f"screen: {doc}:7 expect=0 got=1 FAIL",
    ], result.stdout
    assert result.returncode == 1


def test_an_ansi_c_quote_does_not_hide_later_screens(tmp_path):
    """R2-M1(b): `$'it\\'s'` left the single-quote state open for the rest of the block."""
    root, _, new = _repo(tmp_path)
    doc = _doc(tmp_path, PASSING_BLOCK + f"""{FENCE}bash
SEP=$'it\\'s'
grep -c BAD a.txt   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, new)
    assert _screens(result.stdout) == [
        f"screen: {doc}:2 expect=0 got=0 PASS",
        f"screen: {doc}:7 expect=0 got=1 FAIL",
    ], result.stdout


def test_an_arithmetic_shift_is_not_a_heredoc(tmp_path):
    """R2-M1(c): `$((1<<n))` opened a heredoc named n."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
n=3; echo $((1<<n)) >/dev/null
echo 0   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [f"screen: {doc}:3 expect=0 got=0 PASS"], result.stdout


def test_a_screen_the_lexer_cannot_place_is_unreadable_not_dropped(tmp_path):
    """R2-M1 fail-closed: a published `# expect` the lexer did not accept is counted, never dropped."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, PASSING_BLOCK + f"""{FENCE}bash
echo "unterminated
echo 0   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [
        f"screen: {doc}:2 expect=0 got=0 PASS",
        f"screen: {doc}:7 expect=0 got=UNREADABLE:unparsed FAIL",
    ], result.stdout
    assert "EXPECT: FAIL screens=2 failed=0 unreadable=1" in result.stdout


def test_a_comment_after_a_semicolon_is_a_screen(tmp_path):
    """R2 nit: `echo 0;# expect 0` is a comment in bash; it was not counted."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
echo 0;# expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [f"screen: {doc}:2 expect=0 got=0 PASS"], result.stdout


def test_a_failure_inside_a_function_before_the_screen_is_unreadable(tmp_path):
    """R2-M2: the ERR trap did not fire inside function bodies (no errtrace)."""
    root, _, new = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
setup() {{ B=$(git rev-parse --verify --quiet nosuchref); echo ok; }}
setup >/dev/null
git log --oneline $B..HEAD | wc -l | tr -d ' '   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, new)
    assert _screens(result.stdout) == [
        f"screen: {doc}:4 expect=0 got=UNREADABLE:failed_command={doc}:2:1 FAIL"], result.stdout


def test_a_no_match_before_a_screen_is_unreadable(tmp_path):
    """R3: no status is judged benign from command text. A preamble grep that matches nothing
    (status 1) poisons the screens after it -- the accepted cost of failing closed."""
    root, old, _ = _repo(tmp_path)
    for n, line in enumerate(["MOVED=$(git ls-files | grep '\\.py$')",
                              "N=$(grep -c NOPE a.txt)",
                              'Q="$(grep NOPE a.txt)"',
                              "LC_ALL=C grep -c NOPE a.txt",
                              "X=$(grep -E 'a|b' missing-pattern-file.txt 2>/dev/null; grep -E 'NOPE|ALSO' a.txt)"]):
        doc = _doc(tmp_path, f"""{FENCE}bash
{line}
echo 0   # expect 0
{FENCE}
""", f"doc{n}.md")
        result = run(tmp_path, [doc], root, old)
        [screen] = _screens(result.stdout)
        assert screen.startswith(f"screen: {doc}:3 expect=0 got=UNREADABLE:failed_command={doc}:2:"), \
            (line, result.stdout)
        assert result.returncode == 1


def test_or_true_and_or_colon_are_refused(tmp_path):
    """R6: `|| true` / `|| :` mask EVERY status (git's 128 included) -- refused, in and out of `$( )`."""
    root, old, _ = _repo(tmp_path)
    for n, line in enumerate(["MOVED=$(git ls-files | grep '\\.py$' || true)",
                              "N=$(grep -c NOPE a.txt || :)",
                              "LC_ALL=C grep -c NOPE a.txt || true"]):
        doc = _doc(tmp_path, f"{FENCE}bash\n{line}\necho 0   # expect 0\n{FENCE}\n", f"t{n}.md")
        result = run(tmp_path, [doc], root, old)
        assert _screens(result.stdout) == [
            f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=||@{doc}:2 FAIL"], \
            (line, result.stdout)


def test_no_status_check_after_or_is_declared(tmp_path):
    """R8: no `||` is exempt -- the exact status-1 form included, and every look-alike."""
    root, old, _ = _repo(tmp_path)
    for n, tail in enumerate(["[ $? = 1 ]", "[ $? = 0 ]", ":", "[ 1 ]", "[ $? -ge 1 ]"]):
        doc = _doc(tmp_path, f"{FENCE}bash\nN=$(git ls-files | {{ grep NOPE || {tail}; }})\n"
                             f"echo 0   # expect 0\n{FENCE}\n", f"s{n}.md")
        result = run(tmp_path, [doc], root, old)
        assert _screens(result.stdout) == [
            f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=||@{doc}:2 FAIL"], \
            (tail, result.stdout)


def test_a_document_whose_only_screen_is_unparsed_is_fail_not_none(tmp_path):
    """R2-M1 fail-closed: an unparsed screen still counts, so the run is FAIL, never NONE."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
echo "unterminated
echo 0   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert result.returncode == 1, result.stdout
    assert _screens(result.stdout) == [f"screen: {doc}:3 expect=0 got=UNREADABLE:unparsed FAIL"]
    assert "EXPECT: NONE" not in result.stdout


# --- review round 3 of 9f51a5f7 ----------------------------------------------------


def test_an_errored_ref_collected_into_a_variable_is_unreadable(tmp_path):
    """R3-M1: the #49w trip-wire shape in a substitution; git's 128 was hidden behind grep's 1."""
    root, _, new = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
N=$(git diff --name-only nosuchref HEAD | grep -vc '^docs/')
echo "$N"   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, new)
    [screen] = _screens(result.stdout)
    assert screen.startswith(f"screen: {doc}:3 expect=0 got=UNREADABLE:failed_command={doc}:2:"), \
        result.stdout
    assert result.returncode == 1


def test_an_errored_ref_at_top_level_into_a_file_is_unreadable(tmp_path):
    """R3-M1, top level: ERR saw only grep's 1, so the errored git member was never recorded."""
    root, _, new = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
git diff --name-only nosuchref HEAD | grep -vc "^docs/" > n.txt
cat n.txt   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, new)
    [screen] = _screens(result.stdout)
    assert screen.startswith(f"screen: {doc}:3 expect=0 got=UNREADABLE:failed_command={doc}:2:"), \
        result.stdout


def test_an_errored_member_before_a_clean_one_is_seen_through_pipefail(tmp_path):
    """R3: without pipefail `git … | cat > f` exits 0 and the error is invisible."""
    root, _, new = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
git diff --name-only nosuchref HEAD | cat > n.txt
wc -l < n.txt | tr -d ' '   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, new)
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:failed_command={doc}:2:128 FAIL"], result.stdout


def test_a_backtick_assignment_that_failed_is_unreadable(tmp_path):
    """R3-M2(g): a backtick assignment fell through the env-prefix branch."""
    root, _, new = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
B=`git rev-parse --verify --quiet nosuchref`
git log --oneline $B..HEAD | wc -l | tr -d ' '   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, new)
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:failed_command={doc}:2:1 FAIL"], result.stdout


def test_an_interpolated_assignment_that_failed_is_unreadable(tmp_path):
    """R3-M2(h): `R="range: $(…)"` fell through the env-prefix branch."""
    root, _, new = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
R="range: $(git rev-parse --verify --quiet nosuchref)"
B=${{R#range: }}
git log --oneline $B..HEAD | wc -l | tr -d ' '   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, new)
    assert _screens(result.stdout) == [
        f"screen: {doc}:4 expect=0 got=UNREADABLE:failed_command={doc}:2:1 FAIL"], result.stdout


def test_a_sigpipe_is_unreadable_not_pass(tmp_path):
    """R3: `yes | head -1` ends `yes` with SIGPIPE (141). Fail closed: unreadable, before or in a screen."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
yes | head -1 | wc -l | tr -d ' '   # expect 1
{FENCE}

{FENCE}bash
yes | head -1 > /dev/null
echo 0   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [
        f"screen: {doc}:2 expect=1 got=UNREADABLE:exit_status=141,0,0,0 FAIL",
        f"screen: {doc}:7 expect=0 got=UNREADABLE:failed_command={doc}:6:141 FAIL",
    ], result.stdout


def test_an_assignment_whose_substitution_exits_non_zero_is_unreadable(tmp_path):
    """R3: only the assignment's own status shows this failure -- `exit` fires no ERR inside
    the substitution -- so it must be recorded whatever the statement's text. (R6: `|| exit 1`
    is now refused outright, so the pin uses a bare `exit`.)"""
    root, _, new = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
B=$(exit 1)
git log --oneline $B..HEAD | wc -l | tr -d ' '   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, new)
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:failed_command={doc}:2:1 FAIL"], result.stdout


# --- review round 4 of 6696f180: refuse what the ERR trap cannot see ----------------


def test_an_and_list_before_a_screen_is_refused(tmp_path):
    """R4 (p): bash runs no ERR trap for a non-final `&&` member; git's 128 read as PASS."""
    root, _, new = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
git diff --name-only nosuchref HEAD > list.txt && echo listed
wc -l < list.txt | tr -d ' '   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, new)
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=&&@{doc}:2 FAIL"], \
        result.stdout
    assert result.returncode == 1


def test_a_background_job_before_a_screen_is_refused(tmp_path):
    """R4 (r): a `&` job's status never reaches the trap, and a bare `wait` returns 0."""
    root, _, new = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
git diff --name-only nosuchref HEAD > list.txt &
wait
wc -l < list.txt | tr -d ' '   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, new)
    assert _screens(result.stdout) == [
        f"screen: {doc}:4 expect=0 got=UNREADABLE:unsupported_construct=&@{doc}:2 FAIL"], \
        result.stdout


def test_a_failed_cd_in_an_and_list_is_refused(tmp_path):
    """R4: `cd nosuchdir && …` is the same hole; a screen after it is refused."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
cd nosuchdir && echo moved
echo 0   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=&&@{doc}:2 FAIL"], \
        result.stdout


def test_an_or_list_that_is_not_a_declared_or_true_is_refused(tmp_path):
    """R4: `cmd || other` hides cmd's status just like `&&`; only `|| true`/`|| :` is declared."""
    root, _, new = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
git diff --name-only nosuchref HEAD > list.txt || echo failed > /dev/null
wc -l < list.txt | tr -d ' '   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, new)
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=||@{doc}:2 FAIL"], \
        result.stdout


def test_a_list_on_the_screens_own_line_is_refused(tmp_path):
    """R4: `false || echo 0   # expect 0` would PASS on the fallback branch."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
false || echo 0   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [
        f"screen: {doc}:2 expect=0 got=UNREADABLE:unsupported_construct=||@{doc}:2 FAIL"], \
        result.stdout


def test_an_and_list_inside_an_assignment_substitution_is_still_recorded(tmp_path):
    """R4: inside a single-line `NAME=$(…)` the list's status IS the assignment's, and the trap
    records it (probe: `X=$(grep x /nonexistent && echo y)` -> trap rc=2). Not refused."""
    root, _, new = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
B=$(git rev-parse --verify nosuchref 2>/dev/null && echo extra)
git log --oneline $B..HEAD | wc -l | tr -d ' '   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, new)
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:failed_command={doc}:2:128 FAIL"], result.stdout


def test_an_and_list_inside_a_non_assignment_substitution_is_refused(tmp_path):
    """R4: `echo "$(a && b)"` discards the substitution's status (probe: no trap), so refuse."""
    root, _, new = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
echo "$(git diff --name-only nosuchref HEAD && echo y)" > out.txt
grep -c . out.txt   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, new)
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=&&@{doc}:2 FAIL"], \
        result.stdout


def test_redirections_are_not_jobs(tmp_path):
    """R4: the `&` of `2>&1`, `>&2` and `&>` is a redirection, not a job.
    (`|&` is bash 4+; /bin/bash here is 3.2, where it is a syntax error.)"""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
ls a.txt > /dev/null 2>&1
ls a.txt &> /dev/null
echo note >&2
[ -n x ]
[ -n y ]
echo 0   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [f"screen: {doc}:7 expect=0 got=0 PASS"], result.stdout


def test_lists_inside_test_and_arithmetic_brackets_are_refused(tmp_path):
    """R9: no `[[ ]]` / `(( ))` exemption -- keyed on text, each could switch detection off
    (E1, E2). The over-refusal is accepted; write separate `[ ]` statements instead."""
    root, old, _ = _repo(tmp_path)
    for n, line in enumerate(["[[ -n x && -n y ]]", "n=$(( 1 && 1 ))", "[[ -n x || -n y ]]"]):
        doc, result = _one(tmp_path, root, old, f"{line}\necho 0   # expect 0", f"b{n}.md")
        kind = "||" if "||" in line else "&&"
        assert _screens(result.stdout) == [
            f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct={kind}@{doc}:2 FAIL"], \
            (line, result.stdout)


def test_a_list_after_the_screen_does_not_refuse_it(tmp_path):
    """R4: only constructs at or before a screen refuse it."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
echo 0   # expect 0
true && echo after
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [f"screen: {doc}:2 expect=0 got=0 PASS"], result.stdout


# --- review round 5 of e323c8d8 ----------------------------------------------------

SCREEN_LIST = "wc -l < list.txt | tr -d ' '   # expect 0"


def _one(tmp_path, root, sha, body, name="doc.md"):
    doc = _doc(tmp_path, f"{FENCE}bash\n{body}\n{FENCE}\n", name)
    return doc, run(tmp_path, [doc], root, sha)


def test_an_or_list_inside_an_assignment_substitution_is_refused(tmp_path):
    """R5 (x1): the substitution's status is `echo none`'s, so git's 128 never reaches the trap."""
    root, _, new = _repo(tmp_path)
    doc, result = _one(tmp_path, root, new,
                       "X=$(git diff --name-only nosuchref HEAD > list.txt || echo none)\n"
                       + SCREEN_LIST)
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=||@{doc}:2 FAIL"], \
        result.stdout


def test_an_and_list_then_more_inside_an_assignment_substitution_is_refused(tmp_path):
    """R5 (x2): `a && b; c` -- the substitution's status is c's."""
    root, _, new = _repo(tmp_path)
    doc, result = _one(tmp_path, root, new,
                       "X=$(git diff --name-only nosuchref HEAD > list.txt && echo listed; echo done)\n"
                       + SCREEN_LIST)
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=&&@{doc}:2 FAIL"], \
        result.stdout


def test_a_background_job_inside_an_assignment_substitution_is_refused(tmp_path):
    """R5 (x3): `a & wait` -- a bare `wait` returns 0."""
    root, _, new = _repo(tmp_path)
    doc, result = _one(tmp_path, root, new,
                       "X=$(git diff --name-only nosuchref HEAD > list.txt & wait)\n" + SCREEN_LIST)
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=&@{doc}:2 FAIL"], \
        result.stdout


REMEDY = ("MOVED=$(git diff --name-only \"$BASE\" HEAD | { grep '\\.py$' || [ $? = 1 ]; })\n"
          "printf '%s\\n' \"$MOVED\" | grep -c .   # expect 0")


def test_the_braced_status_one_form_is_refused_with_a_bad_base(tmp_path):
    """R8: the braced remedy is no longer an exception, so it is refused whatever the base."""
    root, _, new = _repo(tmp_path)
    doc, result = _one(tmp_path, root, new, "BASE=nosuchref\n" + REMEDY)
    assert _screens(result.stdout) == [
        f"screen: {doc}:4 expect=0 got=UNREADABLE:unsupported_construct=||@{doc}:3 FAIL"], \
        result.stdout


def test_the_braced_status_one_form_is_refused_with_a_clean_base(tmp_path):
    """R8: refused with a good base too -- a good base cannot be told from a bad one (V1/V7)."""
    root, _, new = _repo(tmp_path)
    doc, result = _one(tmp_path, root, new, "BASE=HEAD\n" + REMEDY)
    assert _screens(result.stdout) == [
        f"screen: {doc}:4 expect=0 got=UNREADABLE:unsupported_construct=||@{doc}:3 FAIL"], \
        result.stdout


def test_the_braced_status_one_form_at_the_end_of_a_top_level_pipeline_is_refused(tmp_path):
    """R8 (V1): `git … | { grep P || [ $? = 1 ]; } > list.txt` -- bash 3.2 runs no ERR trap for
    a pipeline that ends in that group, so git's 128 read PASS. Refused now."""
    root, _, new = _repo(tmp_path)
    doc, result = _one(tmp_path, root, new,
                       "git diff --name-only nosuchref HEAD | { grep '\\.py$' || [ $? = 1 ]; } > list.txt\n"
                       + SCREEN_LIST)
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=||@{doc}:2 FAIL"], \
        result.stdout


ZERO_ON_NO_MATCH = {
    "awk": ("MOVED=$(git diff --name-only \"$BASE\" HEAD | awk '/\\.py$/')\n"
            "printf '%s\\n' \"$MOVED\" | grep -c .   # expect 0"),
    "sed": ("MOVED=$(git diff --name-only \"$BASE\" HEAD | sed -n '/\\.py$/p')\n"
            "printf '%s\\n' \"$MOVED\" | grep -c .   # expect 0"),
    "awk-count": ("N=$(git diff --name-only \"$BASE\" HEAD | awk '/\\.py$/{n++} END{print n+0}')\n"
                  "echo \"$N\"   # expect 0"),
}


def test_a_filter_that_exits_zero_on_no_match_passes_a_clean_base(tmp_path):
    """R8 remedy: awk/sed exit 0 on no match, so no `||` is needed; a clean no-match PASSES."""
    root, _, new = _repo(tmp_path)
    for name, body in ZERO_ON_NO_MATCH.items():
        doc, result = _one(tmp_path, root, new, "BASE=HEAD\n" + body, f"ok-{name}.md")
        assert _screens(result.stdout) == [f"screen: {doc}:4 expect=0 got=0 PASS"], \
            (name, result.stdout)


def test_a_filter_that_exits_zero_on_no_match_surfaces_a_bad_base(tmp_path):
    """R8 remedy: the filter exits 0, so under pipefail git's 128 is the pipeline's status."""
    root, _, new = _repo(tmp_path)
    for name, body in ZERO_ON_NO_MATCH.items():
        doc, result = _one(tmp_path, root, new, "BASE=nosuchref\n" + body, f"bad-{name}.md")
        assert _screens(result.stdout) == [
            f"screen: {doc}:4 expect=0 got=UNREADABLE:failed_command={doc}:3:128 FAIL"], \
            (name, result.stdout)


def test_a_guard_that_exits_or_returns_is_refused(tmp_path):
    """R6 reverts R5 (o3, o4): `|| exit 0` / `|| return 0` mask the failure, so no guard is exempt."""
    root, old, _ = _repo(tmp_path)
    for n, line in enumerate(["cd . || exit 1", "go() { cd . || return 1; }"]):
        doc, result = _one(tmp_path, root, old, f"{line}\necho 0   # expect 0", f"g{n}.md")
        assert _screens(result.stdout) == [
            f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=||@{doc}:2 FAIL"], \
            (line, result.stdout)


def test_a_list_inside_a_condition_is_refused(tmp_path):
    """R6 reverts R5 (o2): no condition tracking; a list in a condition is refused like any other."""
    root, old, _ = _repo(tmp_path)
    doc, result = _one(tmp_path, root, old,
                       "if [ -f a.txt ] && [ -f nosuch ]; then echo yes; fi\necho 0   # expect 0")
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=&&@{doc}:2 FAIL"], \
        result.stdout


def test_an_or_echo_guard_is_still_refused(tmp_path):
    """R5 Should-A: only exit/return guards are exempt; `|| echo x` still hides the status."""
    root, old, _ = _repo(tmp_path)
    doc, result = _one(tmp_path, root, old, "cd . || echo x\necho 0   # expect 0")
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=||@{doc}:2 FAIL"], \
        result.stdout


def test_a_condition_ends_at_then_so_a_later_list_is_refused(tmp_path):
    """R5 Should-A: the condition exemption stops at `then`/`do`; a list after it is refused."""
    root, old, _ = _repo(tmp_path)
    doc, result = _one(tmp_path, root, old,
                       "if true; then cd . && echo moved; fi\necho 0   # expect 0")
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=&&@{doc}:2 FAIL"], \
        result.stdout


def test_the_output_discloses_the_child_shell_residual(tmp_path):
    """R5 Should-B (x7): a child shell's failures never reach this trap; every run says so."""
    root, old, _ = _repo(tmp_path)
    result = run(tmp_path, [_doc(tmp_path, CORE)], root, old)
    assert "child shell" in result.stdout.splitlines()[-1], result.stdout


# --- review round 6 of b78d837a: guards and conditions reverted ---------------------

ERRORED = "git diff --name-only nosuchref HEAD > list.txt"


def test_a_return_zero_guard_in_a_function_is_refused(tmp_path):
    """R6 (R1): `|| return 0` ends the function with 0 and masks git's 128."""
    root, _, new = _repo(tmp_path)
    doc, result = _one(tmp_path, root, new,
                       f"go() {{ {ERRORED} || return 0; }}\ngo\n{SCREEN_LIST}")
    assert _screens(result.stdout) == [
        f"screen: {doc}:4 expect=0 got=UNREADABLE:unsupported_construct=||@{doc}:2 FAIL"], \
        result.stdout


def test_an_exit_zero_guard_in_a_subshell_is_refused(tmp_path):
    """R6 (R2): `( … || exit 0 )` -- the subshell exits 0."""
    root, _, new = _repo(tmp_path)
    doc, result = _one(tmp_path, root, new, f"( {ERRORED} || exit 0 )\n{SCREEN_LIST}")
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=||@{doc}:2 FAIL"], \
        result.stdout


def test_an_exit_zero_guard_in_a_substitution_is_refused(tmp_path):
    """R6 (R3): `X=$(… || exit 0)` -- the substitution exits 0."""
    root, _, new = _repo(tmp_path)
    doc, result = _one(tmp_path, root, new, f"X=$({ERRORED} || exit 0)\n{SCREEN_LIST}")
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=||@{doc}:2 FAIL"], \
        result.stdout


def _after_condition(tmp_path, condition, name):
    root, _, new = _repo(tmp_path)
    doc, result = _one(tmp_path, root, new,
                       f"{condition}\n{ERRORED} && echo ok\n{SCREEN_LIST}", name)
    return doc, result


def test_a_list_after_a_subshell_condition_if_is_refused(tmp_path):
    """R6 (C2): `if (true) then …; fi` left the condition state open; the later `&&` slipped."""
    doc, result = _after_condition(tmp_path, "if (true) then echo y; fi", "c2.md")
    assert _screens(result.stdout) == [
        f"screen: {doc}:4 expect=0 got=UNREADABLE:unsupported_construct=&&@{doc}:3 FAIL"], \
        result.stdout


def test_a_list_after_a_subshell_condition_while_is_refused(tmp_path):
    """R6 (C4): `while (false) do :; done` -- the same leak through `do`."""
    doc, result = _after_condition(tmp_path, "while (false) do :; done", "c4.md")
    assert _screens(result.stdout) == [
        f"screen: {doc}:4 expect=0 got=UNREADABLE:unsupported_construct=&&@{doc}:3 FAIL"], \
        result.stdout


def test_a_list_after_a_group_condition_if_is_refused(tmp_path):
    """R6 (C7): `if { true; } then …; fi` -- the same leak through a group."""
    doc, result = _after_condition(tmp_path, "if { true; } then echo y; fi", "c7.md")
    assert _screens(result.stdout) == [
        f"screen: {doc}:4 expect=0 got=UNREADABLE:unsupported_construct=&&@{doc}:3 FAIL"], \
        result.stdout


# --- review round 7 of 111b522f: the remedy only in its braced form -----------------


def test_an_unbraced_status_one_check_in_a_substitution_is_refused(tmp_path):
    """R7 (N1): unbraced, `||` binds to the whole pipeline; pipefail yields grep's 1, so
    `[ $? = 1 ]` succeeds and git's 128 is swallowed."""
    root, _, new = _repo(tmp_path)
    doc, result = _one(tmp_path, root, new,
                       "MOVED=$(git diff --name-only nosuchref HEAD | grep '\\.py$' || [ $? = 1 ])\n"
                       "printf '%s\\n' \"$MOVED\" | grep -c .   # expect 0")
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=||@{doc}:2 FAIL"], \
        result.stdout


def test_an_unbraced_status_one_check_at_top_level_is_refused(tmp_path):
    """R7 (N2): the same at top level, redirected to a file."""
    root, _, new = _repo(tmp_path)
    doc, result = _one(tmp_path, root, new,
                       "git diff --name-only nosuchref HEAD | grep '\\.py$' > list.txt || [ $? = 1 ]\n"
                       + SCREEN_LIST)
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=||@{doc}:2 FAIL"], \
        result.stdout


def test_a_status_one_check_outside_a_piped_group_is_refused(tmp_path):
    """R7 (N3): a bare `cmd || [ $? = 1 ]` is not the prescribed `| { grep … || [ $? = 1 ]; }`."""
    root, _, new = _repo(tmp_path)
    doc, result = _one(tmp_path, root, new,
                       "git diff --name-only nosuchref HEAD > list.txt || [ $? = 1 ]\n" + SCREEN_LIST)
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=||@{doc}:2 FAIL"], \
        result.stdout


def test_a_braced_pipeline_with_a_status_one_check_is_refused(tmp_path):
    """R7: braces around the WHOLE pipeline bind `||` to it just as no braces do; only a
    group opened after `|` around one command is the declared form."""
    root, _, new = _repo(tmp_path)
    doc, result = _one(tmp_path, root, new,
                       "{ git diff --name-only nosuchref HEAD | grep '\\.py$' || [ $? = 1 ]; } > list.txt\n"
                       + SCREEN_LIST)
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=||@{doc}:2 FAIL"], \
        result.stdout


# --- review round 9 of 844ffd58 -----------------------------------------------------


def test_a_bracket_argument_does_not_switch_off_list_detection(tmp_path):
    """R9 (E1): `echo [[ ; … && …` -- `[[` is an argument, but the lexer opened a test and
    never saw `]]`, so the `&&` read PASS."""
    root, _, new = _repo(tmp_path)
    doc, result = _one(tmp_path, root, new,
                       "echo [[ ; git diff --name-only nosuchref HEAD > list.txt && echo ok\n"
                       + SCREEN_LIST)
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=&&@{doc}:2 FAIL"], \
        result.stdout


def test_a_nested_subshell_does_not_switch_off_list_detection(tmp_path):
    """R9 (E2): `((cmd) && …)` is two subshells, not arithmetic; the `&&` read PASS."""
    root, _, new = _repo(tmp_path)
    doc, result = _one(tmp_path, root, new,
                       "((git diff --name-only nosuchref HEAD > list.txt) && echo ok)\n" + SCREEN_LIST)
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=&&@{doc}:2 FAIL"], \
        result.stdout


def test_a_job_after_a_redirection_is_refused(tmp_path):
    """R9: the redirect exclusion covers only the `&` of `>&2`; a trailing `&` job is refused."""
    root, _, new = _repo(tmp_path)
    doc, result = _one(tmp_path, root, new,
                       "git diff --name-only nosuchref HEAD > list.txt 2>&1 >&2 &\nwait\n" + SCREEN_LIST)
    assert _screens(result.stdout) == [
        f"screen: {doc}:4 expect=0 got=UNREADABLE:unsupported_construct=&@{doc}:2 FAIL"], \
        result.stdout


def test_the_output_discloses_conditions_and_negation(tmp_path):
    """R9 Should-fix: `!`-negated commands and if/while/until conditions are neither refused nor
    recorded; every run's coverage line says so."""
    root, old, _ = _repo(tmp_path)
    result = run(tmp_path, [_doc(tmp_path, CORE)], root, old)
    coverage = result.stdout.splitlines()[-1]
    assert "if/while/until condition" in coverage and "!-negated" in coverage, coverage


def test_the_output_discloses_aliases_and_sourced_text(tmp_path):
    """R14 S1, R17 S4, task #14: both holes are now refused at run time; the coverage line
    says so, and names what the runtime guard still cannot see."""
    root, old, _ = _repo(tmp_path)
    result = run(tmp_path, [_doc(tmp_path, CORE)], root, old)
    coverage = result.stdout.splitlines()[-1]
    for part in ("every . or source, and aliases on at a screen",
                 "is refused at run time",
                 "aliases turned on and off again between screens",
                 "the guard (trap - RETURN, unset -f source) is not seen;"):
        assert part in coverage, (part, coverage)


# --- review round 10 of aa2b968a: the raw-text backstop -----------------------------
#
# Each lexer exemption keyed on text opened a hole the next round found. Round 10 found
# three more (H1, P1, K1/K2), all PASS over git's unrecorded 128. The backstop is a second
# reader of the raw text that refuses every `&&`, `||` and non-redirect `&` independently of
# the lexer; it skips only quoted-delimiter heredoc bodies, and a single-quoted span only
# where the lexer AND its own per-line scan both read the position as single-quoted.


def _refused(tmp_path, body, kind, line, name="doc.md"):
    root, _, new = _repo(tmp_path)
    doc, result = _one(tmp_path, root, new, body, name)
    screen = body.count("\n") + 2
    assert _screens(result.stdout) == [
        f"screen: {doc}:{screen} expect=0 got=UNREADABLE:unsupported_construct={kind}@{doc}:{line} "
        "FAIL"], result.stdout


def test_a_list_inside_an_unquoted_heredoc_substitution_is_refused(tmp_path):
    """R10 (H1): an unquoted heredoc body runs its `$(…)` in the parent shell, so a list there
    hides git's 128 -- the lexer skips body lines whole."""
    _refused(tmp_path, f"cat > note.txt <<NOTE\n$({ERRORED} && echo listed)\nNOTE\n" + SCREEN_LIST,
             "&&", 3)


def test_a_hash_inside_a_parameter_expansion_does_not_hide_a_list(tmp_path):
    """R10 (P1): ` #` inside `${…}` is not a comment; the lexer cut the line there."""
    _refused(tmp_path, f"X=${{PWD// #/}}; {ERRORED} && echo ok\n" + SCREEN_LIST, "&&", 2)


def test_an_escaped_ampersand_before_a_job_does_not_hide_it(tmp_path):
    """R10 (K1): `\\&&` is a literal `&` then a background `&`; the lexer read the raw `&`
    before it and excluded the job as a redirect."""
    _refused(tmp_path, f"{ERRORED} \\&& wait\n" + SCREEN_LIST, "&", 2)


def test_an_escaped_pipe_before_a_job_does_not_hide_it(tmp_path):
    """R10 (K2): `\\|&` is a literal `|` then a background `&`, not bash 4's `|&`."""
    _refused(tmp_path, f"{ERRORED} \\|& wait\n" + SCREEN_LIST, "&", 2)


def test_a_job_hidden_inside_the_assignment_chain_carve_out_is_refused(tmp_path):
    """R10: the lexer's misread `\\&&` left only `&&` in `X=$(…)`, so the one-chain carve-out
    applied -- yet bash backgrounds `git … && echo &` and the substitution ends on `true`. The
    backstop sees the job, so the carve-out is void and the line's first list is refused."""
    _refused(tmp_path, f"X=$({ERRORED} && echo \\&& true)\n" + SCREEN_LIST, "&&", 2)


def test_an_escaped_heredoc_delimiter_does_not_hide_a_later_list(tmp_path):
    """R10: the lexer does not recognise `<<\\NOTE`, read the body's apostrophe as a quote and
    carried it over the list. A `<<` the lexer did not read as a heredoc refuses."""
    _refused(tmp_path, f"cat > note.txt <<\\NOTE\nit's\nNOTE\n{ERRORED} && echo ok\necho \\'\n"
             + SCREEN_LIST, "<<", 2)


def test_a_span_only_the_backstop_reads_as_quoted_is_not_excluded(tmp_path):
    """R10: the backstop's per-line scan misreads `"$(echo "it's")"` and spans the list with
    `it's … 'z'`; the lexer, cut short by ` #` inside `${…}`, saw no quote there. One
    reader alone never excludes."""
    _refused(tmp_path, f"X=${{PWD// #/}}; echo \"$(echo \"it's\")\"; {ERRORED} && echo ok; "
             "echo 'z'\n" + SCREEN_LIST, "&&", 2)


def test_single_quoted_data_is_not_refused(tmp_path):
    """R10: a list in a single-quoted string both readers agree on is data, not code."""
    root, old, _ = _repo(tmp_path)
    doc, result = _one(tmp_path, root, old,
                       "printf '%s\\n' 'a && b || c & d' > data.txt\necho 0   # expect 0")
    assert _screens(result.stdout) == [f"screen: {doc}:3 expect=0 got=0 PASS"], result.stdout


def test_a_quoted_delimiter_heredoc_body_is_not_refused(tmp_path):
    """R10: a quoted-delimiter body expands nothing, so its text is data."""
    root, old, _ = _repo(tmp_path)
    doc, result = _one(tmp_path, root, old,
                       "cat > data.txt <<'NOTE'\na && b || c & d\nNOTE\necho 0   # expect 0")
    assert _screens(result.stdout) == [f"screen: {doc}:5 expect=0 got=0 PASS"], result.stdout


def test_an_unquoted_heredoc_body_is_over_refused(tmp_path):
    """R10: the accepted cost. An unquoted body is read raw, so prose `&` there refuses."""
    root, old, _ = _repo(tmp_path)
    doc, result = _one(tmp_path, root, old,
                       "cat > data.txt <<NOTE\nTom & Jerry\nNOTE\necho 0   # expect 0")
    assert _screens(result.stdout) == [
        f"screen: {doc}:5 expect=0 got=UNREADABLE:unsupported_construct=&@{doc}:3 FAIL"], \
        result.stdout


def test_a_quoted_delimiter_with_a_suffix_is_not_a_shorter_heredoc(tmp_path):
    """R10: bash's delimiter for `<<'true'x` is `truex`. Read as `true`, the lexer ran the body
    past bash's terminator, the backstop skipped it as data, and the terminator `true` ran
    clean. Now the delimiter must end the word, and the unread `<<` refuses."""
    _refused(tmp_path, f"cat > note.txt <<'true'x\ndata\ntruex\n{ERRORED} && echo ok\ntrue\n"
             + SCREEN_LIST, "<<", 2)


def test_a_quote_both_readers_lose_does_not_hide_a_list(tmp_path):
    """R10: the lexer cut ` #` inside `${…}` and lost the `'` after it; reset at every line, the
    first backstop lost it too, so both read line 3's `a'` as an OPENING quote and agreed that
    the list was data. The backstop now carries quotes across lines and has no comment in
    `${…}`, so its reading differs from the lexer's exactly where the lexer is wrong."""
    _refused(tmp_path, f"X=${{PWD// #/}}'\na'; {ERRORED} && echo ok; echo 'y'\necho \\'\n"
             + SCREEN_LIST, "&&", 3)


def test_an_escaped_blank_does_not_start_a_comment_that_hides_a_heredoc(tmp_path):
    """R10: `\\ #` is an escaped blank then a word -- bash reads the `<<E` after it. The lexer
    cut there and never saw the heredoc, so the body's apostrophe opened a quote in it."""
    _refused(tmp_path, f"echo \\ #<<E\nit's\nE\n{ERRORED} && echo ok; echo \\'\n" + SCREEN_LIST,
             "<<", 2)


def test_a_heredoc_the_backstop_reads_as_quoted_text_is_not_skipped(tmp_path):
    """R10: bash reads `<<'true'` inside a single-quoted string; the lexer, which lost that
    quote, read a heredoc and skipped its body, and the "terminator" `true` ran clean. The backstop skips a body only when it, too, is in
    code at the `<<`."""
    _refused(tmp_path, f"X=${{PWD// #/}}'\n<<'true'\n'; {ERRORED} && echo ok; echo \\'\ntrue\n"
             + SCREEN_LIST, "&&", 4)


def test_a_hash_after_the_carve_out_does_not_hide_a_list(tmp_path):
    """R10: the lexer reads `)#` as a comment, so `X=$(… && …)` looked whole and its carve-out
    applied -- but bash reads `)#` as one word, and the `&&` after it is a list."""
    _refused(tmp_path, f"X=$(true && echo y)#&& {ERRORED} && echo ok\n" + SCREEN_LIST, "&&", 2)


def test_a_nested_double_quote_does_not_fool_both_readers(tmp_path):
    """R10: the backstop has no model of `"$(…)"` and reads `it's` as an opening quote. The
    lexer does, so the two disagree and nothing is excluded. Without the lexer's model they
    would agree on a span that bash reads as code."""
    _refused(tmp_path, f"echo \"$(echo \"it's\")\"; {ERRORED} && echo ok; echo 'z'\n" + SCREEN_LIST,
             "&&", 2)


# --- review round 11 of 2e88d95b: bash's own parse as the third reader ----------------
# The lexer and the backstop share one quote and heredoc model, so seven constructs fooled
# both the same way (M1-M7). `bash -n` on a perturbed copy of the block is the reader that
# does not share it: a doubled operator fails to parse exactly where bash reads code. A
# position either reader would exclude is excluded only when bash agrees it is literal.


def test_a_dollar_dollar_quote_does_not_fool_all_readers(tmp_path):
    """R11 (M1): bash reads `$$` as the PID, so the `'` after it is a plain quote. Both models
    read `$'` there as an ANSI-C string and agreed the list was single-quoted."""
    _refused(tmp_path, f"echo $$'\\' 'a' ; {ERRORED} && echo '\\'\n" + SCREEN_LIST, "&&", 2)


def test_quotes_inside_code_backticks_do_not_fool_all_readers(tmp_path):
    """R11 (M2): bash 3.2 finds a backtick's closer without honouring `'` inside it."""
    _refused(tmp_path, f"echo `#'` 'a' ; {ERRORED} && echo '\\'\n" + SCREEN_LIST, "&&", 2)


def test_quotes_inside_a_double_quoted_expansion_do_not_fool_all_readers(tmp_path):
    """R11 (M3): in bash 3.2, quotes inside a `${…}` in double quotes are quotes."""
    _refused(tmp_path, f"x=; echo \"${{x:-'\"'}}\" ; {ERRORED} && echo '\\'\n" + SCREEN_LIST,
             "&&", 2)
    (tmp_path / "nested").mkdir()
    _refused(tmp_path / "nested", f"x=; echo \"${{x:-\"'\"}}\" ; {ERRORED} && echo '\\'\n"
             + SCREEN_LIST, "&&", 2)


def test_a_continued_heredoc_opener_does_not_fool_all_readers(tmp_path):
    """R11 (M4): bash joins `\\`-newline before tokenizing, so the body starts after the
    continued line; both models started it one line early and lost a quote."""
    _refused(tmp_path, f"true <<'E' \\\nE\nit's\nE\n{ERRORED} && echo '\\'\n" + SCREEN_LIST,
             "&&", 6)


def test_a_paren_in_a_heredoc_inside_a_substitution_does_not_fool_all_readers(tmp_path):
    """R11 (M5): bash 3.2 ends `$(` at a `)` inside a heredoc body, so the lines after it run
    as code; both models read them as a quoted-delimiter body."""
    _refused(tmp_path, f"E() {{ :; }}\nX=$(cat <<'E'\n)\n{ERRORED} && echo x\nE\n" + SCREEN_LIST,
             "&&", 5)


def test_an_old_style_arithmetic_shift_does_not_fool_all_readers(tmp_path):
    """R11 (M6): `$[1<<E ]` is a shift; the lexer read a heredoc whose "body" bash runs."""
    _refused(tmp_path, f"E() {{ :; }}\necho $[1<<E ]\necho '\nE\n' ; {ERRORED} && echo '\\'\n"
             + SCREEN_LIST, "&&", 6)


def test_the_assignment_carve_out_needs_a_statement_start(tmp_path):
    """R11 (M7): after `export \\`, `X=$(a && b)` is an argument whose status is export's 0."""
    _refused(tmp_path, f"export \\\nX=$({ERRORED} && echo x)\n" + SCREEN_LIST, "&&", 3)
    (tmp_path / "echo").mkdir()
    _refused(tmp_path / "echo", f"echo \\\nX=$({ERRORED} && echo x)\n" + SCREEN_LIST, "&&", 3)


def test_an_operator_quoted_inside_backticks_is_over_refused(tmp_path):
    """R11: the accepted cost. bash 3.2's backtick scan ignores `'`, so bash cannot vouch for
    a single-quoted operator inside backticks. Since round 13 `$(…)` is refused too:
    single-quote the text at top level."""
    root, old, _ = _repo(tmp_path)
    doc, result = _one(tmp_path, root, old, "echo `echo 'a && b'` > data.txt\necho 0   # expect 0")
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=&&@{doc}:2 FAIL"], \
        result.stdout


def test_a_quoted_heredoc_inside_a_substitution_is_over_refused(tmp_path):
    """R11: the accepted cost. bash 3.2 closes `$(` at a `)` in a heredoc body (M5), so a body
    inside a substitution is never vouched for. Write the heredoc at top level."""
    root, old, _ = _repo(tmp_path)
    doc, result = _one(tmp_path, root, old,
                       "X=$(cat <<'NOTE'\na && b\nNOTE\n)\necho 0   # expect 0")
    assert _screens(result.stdout) == [
        f"screen: {doc}:6 expect=0 got=UNREADABLE:unsupported_construct=&&@{doc}:3 FAIL"], \
        result.stdout


def test_bash_reads_a_block_without_running_it(tmp_path, monkeypatch):
    """The third reader is `bash -n`: a block that would escape a function wrapper and run
    `touch` (what `declare -f` would do) creates nothing."""
    monkeypatch.chdir(tmp_path)
    parse = hes.BashParse([":", "}", "touch PWNED && touch PWNED2", "__g() {", ":"])
    assert parse.code_at(2, 12, "&&") is True
    assert parse.starts_statement(2, 0) is False  # the block itself does not parse
    assert os.listdir(tmp_path) == []


def test_bash_reads_literal_and_code_positions(tmp_path):
    parse = hes.BashParse(["echo 'a && b'", "X=$(a && b)", "cat <<'E'", "a && b", "E"])
    assert parse.code_at(0, 8, "&&") is False
    assert parse.code_at(1, 6, "&&") is True
    assert parse.body_code_at(3, "&&", "E") is False
    assert parse.starts_statement(1, 0) is True
    assert hes.BashParse(["export \\", "X=$(a && b)"]).starts_statement(1, 0) is False


def test_bash_unavailable_fails_closed(monkeypatch):
    """No bash, no vouching: every excluded position reads as code, no carve-out applies."""
    monkeypatch.setenv("PATH", "")
    parse = hes.BashParse(["echo 'a && b'", "X=$(a && b)"])
    assert parse.code_at(0, 8, "&&") is True
    assert parse.starts_statement(1, 0) is False


def test_a_round_11_construct_inside_a_substitution_is_refused(tmp_path):
    """R11: bash 3.2 parses `$(…)` only at run time, so `bash -n` alone vouches for any text
    inside one. bash now vouches only where a probe proves single-quoted text at a level
    `-n` parses (round 13), and nothing inside `$(…)` is."""
    _refused(tmp_path, f"X=$(echo `#'` 'a' ; {ERRORED} && echo '\\')\n" + SCREEN_LIST, "&&", 2)


# The models' agreement is defence in depth under bash, not a step bash replaces: each R10
# misread below must still refuse when bash wrongly vouches for every position.


def _hits_if_bash_vouches(monkeypatch, body):
    monkeypatch.setattr(hes.BashParse, "code_at", lambda self, i, k, op: False)
    monkeypatch.setattr(hes.BashParse, "body_code_at", lambda self, i, op, term: False)
    monkeypatch.setattr(hes.BashParse, "starts_statement", lambda self, i, k: True)
    return hes.backstop(hes.lex(body.split("\n")))


def test_a_span_only_the_backstop_reads_as_quoted_needs_the_lexer_too(monkeypatch):
    body = f"X=${{PWD// #/}}; echo \"$(echo \"it's\")\"; {ERRORED} && echo ok; echo 'z'"
    assert (0, "&&") in _hits_if_bash_vouches(monkeypatch, body)


def test_a_span_only_the_lexer_reads_as_quoted_needs_the_backstop_too(monkeypatch):
    body = f"X=${{PWD// #/}}'\na'; {ERRORED} && echo ok; echo 'y'\necho \\'"
    assert (1, "&&") in _hits_if_bash_vouches(monkeypatch, body)


def test_an_unquoted_heredoc_body_is_counted_without_bash(monkeypatch):
    """R15: bash's `x\\` line now refuses an unquoted body on its own; the backstop's refusal
    stays as the reader that does not depend on it."""
    body = f"cat > note.txt <<NOTE\n$({ERRORED} && echo listed)\nNOTE"
    assert (1, "&&") in _hits_if_bash_vouches(monkeypatch, body)


def test_a_lexer_heredoc_the_backstop_reads_as_text_is_counted_without_bash(monkeypatch):
    body = f"X=${{PWD// #/}}'\n<<'true'\n'; {ERRORED} && echo ok; echo \\'\ntrue"
    assert (2, "&&") in _hits_if_bash_vouches(monkeypatch, body)


# --- review round 12 of 8e24635d -------------------------------------------------------


def test_a_later_backtick_does_not_reopen_a_top_level_hole(tmp_path):
    """R12 (M1): the closer's backtick paired with a later inert one (here in a comment), so
    the doubled operator sat in deferred text and bash vouched for round 11's M1 again."""
    _refused(tmp_path, f"echo $$'\\' 'a' ; {ERRORED} && echo '\\'\n# it`s\n" + SCREEN_LIST,
             "&&", 2)


def test_a_later_backtick_does_not_reopen_a_heredoc_paren_hole(tmp_path):
    """R12 (M1): round 11's M5, which needs no quote trick, plus a backtick in a comment."""
    _refused(tmp_path, f"E() {{ :; }}\nX=$(cat <<'E'\n)\n{ERRORED} && echo x\nE\n# see `notes\n"
             + SCREEN_LIST, "&&", 5)


def test_a_later_backtick_does_not_hide_a_list_inside_a_substitution(tmp_path):
    _refused(tmp_path, f"X=$(echo `#'` 'a' ; {ERRORED} && echo '\\')\n# it`s\n" + SCREEN_LIST,
             "&&", 2)


@pytest.mark.parametrize("body", [
    f"echo `echo $$'\\' 'a' ; {ERRORED} && echo '\\'`",
    f"echo `x=; echo \"${{x:-'\"'}}\" ; {ERRORED} && echo '\\'`",
    f"echo $(echo `x=; echo \"${{x:-'\"'}}\" ; {ERRORED} && echo '\\'`)",
    f"echo `echo \\`#'\\` 'a' ; {ERRORED} && echo '\\'`",
    f"X=$(echo `echo $$'\\' 'a' ; {ERRORED} && echo '\\'`)",
], ids=["M1-in-backticks", "M3-in-backticks", "M3-in-backticks-in-substitution",
        "M2-in-backticks", "M1-in-backticks-in-substitution"])
def test_a_round_11_construct_inside_backticks_is_refused(tmp_path, body):
    """R12: each read PASS over git's 128 on main. Backticks defer their text like `$(…)`,
    so no probe proves a quote inside them."""
    _refused(tmp_path, body + "\n" + SCREEN_LIST, "&&", 2)


def test_the_carve_out_needs_a_command_slot_not_a_one_word_slot(tmp_path):
    """R12 (M2): `then ` also breaks the parse where bash wants ONE word -- the `case`
    subject, a `[[ -n` operand -- and there the substitution's status is discarded. A start
    is where `then` breaks the parse AND a plain word does not."""
    _refused(tmp_path, f"case \\\nX=$({ERRORED} && echo x)\nin *) : ;; esac\n" + SCREEN_LIST,
             "&&", 3)
    (tmp_path / "dbrack").mkdir()
    _refused(tmp_path / "dbrack", f"[[ -n \\\nX=$({ERRORED} && echo x)\n]]\n" + SCREEN_LIST,
             "&&", 3)


def test_a_probe_that_cannot_run_vouches_for_nothing(monkeypatch):
    """R12 (M3): the block parsed, then the probe's own bash call timed out; the statement
    probe read that as `then` breaking the parse and applied the carve-out."""
    real = subprocess.run
    calls = []

    def first_only(*args, **kwargs):
        calls.append(args)
        if len(calls) == 1:
            return real(*args, **kwargs)
        raise subprocess.TimeoutExpired(args[0], 10)
    monkeypatch.setattr(hes.subprocess, "run", first_only)
    lexed = hes.lex(["export \\", f"X=$({ERRORED} && echo x)"])
    assert (1, "&&") in hes.backstop(lexed)
    calls.clear()
    assert hes.BashParse(["echo 'a && b'"]).code_at(0, 8, "&&") is True


def test_a_nul_byte_vouches_for_nothing():
    """R12 (N1): `subprocess` refuses a NUL byte with ValueError; that is no parse either."""
    assert hes.BashParse(["echo 'a && b\0'"]).code_at(0, 8, "&&") is True


def test_a_then_probe_that_cannot_run_is_no_statement_start(monkeypatch):
    """R12 (M3): each probe must answer definitely on its own; the word probe parsing does not
    stand in for a `then` probe that gave no answer."""
    real = hes.BashParse._parses
    monkeypatch.setattr(hes.BashParse, "_parses",
                        staticmethod(lambda text: None if "then X=" in text else real(text)))
    assert hes.BashParse(["X=$(a && b)"]).starts_statement(0, 0) is False
    lexed = hes.lex([f"X=$({ERRORED} && echo x)"])
    assert (0, "&&") in hes.backstop(lexed)


# --- review round 13 of cd8fba95 -------------------------------------------------------
# Closer runs push a position out of `$(…)` or backticks, but not out of an enclosing
# `"…"`, `${…}` or `$[…]`, where the doubled operator is still text; one later backtick then
# fooled the backtick run again (M1). No finite set of closers leaves every nesting, so bash
# now vouches only on positive evidence: a probe that proves the position is single-quoted
# text, or a heredoc body line, at a level `bash -n` parses.

LATER_TICK = "\n# it`s ) 5\" # \""


@pytest.mark.parametrize("body", [
    f"echo \"${{x:-'\"'}}$(echo a ; {ERRORED} && echo \\')\"\n# it`s ) 5\" # \"",
    f"echo \"${{x:-'\"'}}`echo a ; {ERRORED} && echo \\\\'`\"\n# it`s 5\" # \"",
], ids=["substitution-in-double-quotes", "backticks-in-double-quotes"])
def test_a_later_backtick_does_not_hide_a_list_in_a_double_quoted_substitution(tmp_path, body):
    """R13 (M1): each read PASS over git's 128 on main. Both models lose the `"` at `'"'`
    (round 11's M3); bash runs the list inside the substitution."""
    _refused(tmp_path, body + "\n" + SCREEN_LIST, "&&", 2)


@pytest.mark.parametrize("line", [
    "echo \"$(a && b)\"", "echo \"`a && b`\"", "echo ${x:-$(a && b)}",
    "echo \"${x:-$(a && b)}\"", "echo $[ $(a && b) ]",
    "echo \"${y:-\"${x:-$(a && b)}\"}\"",
], ids=["dq", "dq-backticks", "brace", "dq-brace", "old-arith", "nested"])
def test_bash_vouches_for_no_position_inside_an_enclosed_substitution(line):
    """R13 (M1): whatever encloses the substitution, and whatever backtick follows it."""
    for tail in ("", LATER_TICK, "\n# it`s"):
        parse = hes.BashParse((line + tail).split("\n"))
        assert parse.code_at(0, line.index("&&"), "&&") is True, tail


def test_a_quote_probe_that_breaks_the_parse_anyway_proves_nothing(tmp_path):
    """R13: after a `}` a quoted word is a syntax error whatever it holds, so the probe's own
    failure is no evidence; the `'x'` control fails too, and only a passing control proves the
    quote."""
    _refused(tmp_path, f"echo $$'\\' 'a' ; {{ {ERRORED}; }} && echo '\\'\n" + SCREEN_LIST,
             "&&", 2)


def test_an_escaped_operator_is_not_vouched_for():
    """R13: the single-quote probe's `'` after a live backslash is an escaped quote, so the
    probe would put the doubled operator in code and its control would still parse. bash runs
    `git \\&` and then a job here; a position right after a backslash is never vouched for."""
    line = "echo $$'\\' 'a' ; git \\&& echo '\\'"
    assert hes.BashParse([line]).code_at(0, line.index("&&"), "&&") is True


def test_bash_vouches_for_single_quoted_text_at_a_parsed_level():
    for line in ["echo 'a && b'", "[[ $x == 'a && b' ]]",
                 "case 'a && b' in *) :;; esac", "f() { echo 'a && b'; }"]:
        assert hes.BashParse([line]).code_at(0, line.index("&&"), "&&") is False, line
    assert hes.BashParse(["echo 'x", "a ; b'"]).code_at(1, 2, ";") is False


def test_an_operator_single_quoted_inside_a_substitution_is_over_refused(tmp_path):
    """R13: the accepted cost. `bash -n` defers `$(…)`, so nothing proves the quote there.
    Single-quote such text at top level, or write it to a file outside the block."""
    root, old, _ = _repo(tmp_path)
    doc, result = _one(tmp_path, root, old,
                       "echo $(echo 'a && b') > data.txt\necho 0   # expect 0")
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_construct=&&@{doc}:2 FAIL"], \
        result.stdout


def test_bash_vouches_for_a_heredoc_body_only_where_its_terminator_ends_it():
    assert hes.BashParse(["cat <<'E'", "a && b", "E"]).body_code_at(1, "&&", "E") is False
    assert hes.BashParse(["cat <<-'E'", "\ta && b", "\tE"]).body_code_at(1, "&&", "E") is False
    assert hes.BashParse(["cat <<'E'", "a && b", "E"]).body_code_at(1, "&&", "F") is True
    assert hes.BashParse(["X=$(cat <<'E'", "a && b", "E", ")"]).body_code_at(
        1, "&&", "E") is True
    assert hes.BashParse(["cat <<'E'", "a && b", "E"]).body_code_at(1, "&&", "E'") is True


def test_a_heredoc_probe_on_code_is_no_body():
    """R13: on a code line the probe's reopened heredoc swallows the rest, so its control
    parses; the doubled operator failing in place is what rules code out."""
    assert hes.BashParse(["git x && echo y", "E"]).body_code_at(0, "&&", "E") is True


def _only_failing(monkeypatch, marker, outcome):
    """Run bash for real, except the one call whose script contains `marker`."""
    real = subprocess.run

    def fake(args, **kwargs):
        if marker in args[-1]:
            if outcome == "raise":
                raise subprocess.TimeoutExpired(args, 10)
            return subprocess.CompletedProcess(args, outcome)
        return real(args, **kwargs)
    monkeypatch.setattr(hes.subprocess, "run", fake)


@pytest.mark.parametrize("outcome", ["raise", -9, 1])
def test_a_then_probe_with_no_answer_alone_is_no_statement_start(monkeypatch, outcome):
    """R13 (S1a, S2): only the `then` probe gives no answer -- a timeout, a bash killed by a
    signal, an exit status that is not bash's syntax error. The word probe still parses, so
    it cannot mask a `then` probe that wrongly reads as broken."""
    _only_failing(monkeypatch, "then X=", outcome)
    assert hes.BashParse(["export \\", "X=$(a && b)"]).starts_statement(1, 0) is False


@pytest.mark.parametrize("outcome", ["raise", -9, 1])
def test_a_word_probe_with_no_answer_alone_is_no_statement_start(monkeypatch, outcome):
    """R13 (S1b): only the plain-word probe gives no answer, in a one-word slot where `then`
    does break the parse."""
    _only_failing(monkeypatch, "x X=", outcome)
    assert hes.BashParse(["case \\", "X=$(a && b)", "in *) : ;; esac"]).starts_statement(
        1, 0) is False


@pytest.mark.parametrize("outcome", ["raise", -9, 1])
def test_a_control_with_no_answer_proves_nothing(monkeypatch, outcome):
    """R13: the probe really breaks the parse, but its `'x'` control gives no answer. Proof
    needs the control to parse, so a control that cannot run must not stand in for one."""
    _only_failing(monkeypatch, "'x'", outcome)
    assert hes.BashParse(["echo 'a && b'"]).code_at(0, 8, "&&") is True
    _only_failing(monkeypatch, "\nx\n", outcome)
    assert hes.BashParse(["cat <<'E'", "a && b", "E"]).body_code_at(1, "&&", "E") is True


@pytest.mark.parametrize("rc, answer", [(0, True), (2, False), (1, None), (-9, None)])
def test_only_bash_syntax_error_status_reads_as_no_parse(monkeypatch, rc, answer):
    """R13 (S2): bash -n exits 2 on a syntax error. Any other status is no answer."""
    monkeypatch.setattr(hes.subprocess, "run",
                        lambda args, **kw: subprocess.CompletedProcess(args, rc))
    assert hes.BashParse._parses(":") is answer


# --- review round 14 of the round-13 redesign -------------------------------------------


@pytest.mark.parametrize("wrap", [("{ ", " ; }"), ("( ", " )"), ("if :; then ", " ; fi")],
                         ids=["group", "subshell", "if"])
def test_a_probe_payload_does_not_join_a_heredoc_delimiter(tmp_path, wrap):
    """R14 (M1): `<<E'x'` and `<<E'&& &&'` are different delimiters, so the probe's body ran to
    EOF (the group never closed: rc 2) while the control's ended at `Ex` (rc 0), and a code
    `&&` was "proven" single-quoted. PASS over git's 128; main's closers refused it."""
    head, tail = wrap
    body = (f"{head}: \"${{x:-'\"'}}\" ; {ERRORED} <<E&& echo y\nEx\nE\necho \\'{tail}\n"
            + SCREEN_LIST)
    _refused(tmp_path, body, "&&", 2)


def test_bash_proves_nothing_where_the_payload_would_join_a_word():
    for lines in (["{ cat <<E&& b", "Ex", "E", "}"], ["( cat <<-E&& b", "Ex", "E", ")"]):
        assert hes.BashParse(lines).code_at(0, lines[0].index("&&"), "&&") is True, lines


@pytest.mark.parametrize("outcome", ["raise", -9, 1])
def test_a_heredoc_line_check_with_no_answer_is_no_body(monkeypatch, outcome):
    """R14 (S2), R16: on a code line the probes prove a body, so only the whole-line check
    keeps it code. That check giving no answer must refuse, not read as parsing."""
    _only_failing(monkeypatch, "&& &&\ngit x", outcome)
    assert hes.BashParse(["git x && echo y", "E"]).body_code_at(0, "&&", "E") is True


def test_the_accepted_heredoc_and_backslash_over_refusals():
    """R14 (S3): accepted costs, now listed. A body that is not the last heredoc on its opener
    line: the inserted terminator ends it, and the payload lands in the next body. An operator
    right after a backslash, even a literal one inside single quotes. And `$'…'`: neither model
    reads it as single-quoted, so it was never vouched for end to end (N2)."""
    parse = hes.BashParse(["cat <<'A' <<'B' > out.txt", "a && b", "A", "c && d", "B"])
    assert parse.body_code_at(1, "&&", "A") is True
    assert parse.body_code_at(3, "&&", "B") is False
    assert hes.BashParse(["echo 'a\\&& b'"]).code_at(0, 8, "&&") is True
    assert (0, "&&") in hes.backstop(hes.lex(["echo $'a && b'"]))


@pytest.mark.parametrize("lines", [["{ cat <<E\\&& b", "E x", "E&", "}"],
                                   ["( cat <<E\\&& b", "E x", "E&", ")"]],
                         ids=["group", "subshell"])
def test_a_backslash_before_the_payload_is_never_probed(lines):
    """R14: the blanks do not protect a payload after a live backslash, which escapes the first
    blank and joins the word: `<<E\\ 'x'` is the delimiter `E x`, so the control's body ends at
    the line `E x` while the probe's runs to EOF. That `&&` is code (doubled in place, it does
    not parse); only the backslash guard keeps it from being proven quoted."""
    assert hes.BashParse(lines).code_at(0, lines[0].index("&&"), "&&") is True



# --- review round 15 of the round-14 fixes ----------------------------------------------


def test_a_heredoc_hidden_from_both_models_is_not_proven_quoted(tmp_path):
    """R15 (M1): the models lose the `"` at `'"'` and miss the unquoted `<<E`, then read line
    2's `cat <<'E'` as a quoted opener. To bash line 2 is body text of `<<E`, whose `$(…)`
    runs line 3's list. A terminator alone proved only that a heredoc ends there; the `x\\`
    line proves it quoted. PASS over git's 128 on main."""
    body = (": \"${x:-'\"'}\" ; cat <<E > /dev/null\n' ; cat <<'E'\n"
            f"$({ERRORED} && echo y)\nE\n" + SCREEN_LIST)
    _refused(tmp_path, body, "&&", 4)


def test_bash_proves_a_heredoc_body_quoted():
    assert hes.BashParse(["cat <<E", "a && b", "E"]).body_code_at(1, "&&", "E") is True
    for lines in (["cat <<\"E\"", "a && b", "E"], ["{ cat <<'E'", "a && b", "E", "}"],
                  ["f() { cat <<'E'", "a && b", "E", "}"]):
        assert hes.BashParse(lines).body_code_at(1, "&&", "E") is False, lines


@pytest.mark.parametrize("line", ["x=( 'a && b' )", "cmd=( bash -c 'a && b' )"])
def test_a_quote_in_a_top_level_array_is_vouched_for(line):
    """R15 (S1): bash 3.2 exits 1, not 2, on a syntax error in a top-level `NAME=( … )`, so the
    probe gave no answer and the quote was refused. Inside a group it exits 2."""
    assert hes.BashParse([line]).code_at(0, line.index("&&"), "&&") is False


@pytest.mark.parametrize("outcome", ["raise", -9, 1])
def test_a_quote_probe_with_no_answer_alone_proves_nothing(monkeypatch, outcome):
    """R15 (S2): only the probe holding the doubled operator gives no answer; the control
    parses, so it cannot mask a probe that wrongly reads as broken."""
    _only_failing(monkeypatch, "'&& &&'", outcome)
    assert hes.BashParse(["git x && echo y"]).code_at(0, 6, "&&") is True



# --- review round 16 of the round-15 fixes ----------------------------------------------


@pytest.mark.parametrize("opener, closer", [("cat <<xE > /dev/null", "xE")], ids=["xE"])
def test_a_hidden_delimiter_the_join_would_end_is_not_proven_quoted(tmp_path, opener, closer):
    """R16 (M1): `x\\` + `E` reads `xE`, which ENDS a hidden `<<xE` -- and `<<x\\` then `E` is that
    delimiter too. `xx…E` now occurs nowhere in the block. PASS over git's 128 on main."""
    body = (f": \"${{x:-'\"'}}\" ; {opener}\n' ; cat <<'E'\n"
            f"$({ERRORED} && echo y)\nE\n{closer}\n" + SCREEN_LIST)
    _refused(tmp_path, body, "&&", 3 + opener.count("\n") + 1)


def test_a_continued_hidden_delimiter_is_not_proven_quoted():
    """R16 (M1): `<<x\\` then `E` is the delimiter `xE` though no `xE` is written, so the join
    reads the block with backslash-newlines removed. Here the hidden heredoc runs to EOF."""
    lines = [": \"${x:-'\"'}\" ; cat <<x\\", "E > /dev/null", "' ; cat <<'E'",
             "$(git x && echo y)", "E"]
    assert hes.BashParse(lines).body_code_at(3, "&&", "E") is True
    assert (3, "&&") in hes.backstop(hes.lex(lines))


def test_a_deferred_list_on_a_code_line_is_no_body(tmp_path):
    """R16 (M2): round 11's M5 puts the lines after a `)` in a heredoc body at top level, and
    `$(… && && …)` still parses there. A whole line of the doubled operator does not. Main's
    closers refused this; round 13's in-place check did not."""
    _refused(tmp_path, f"E() {{ :; }}\nX=$(cat <<'E'\n)\n: $({ERRORED} && echo x)\nE\n"
             + SCREEN_LIST, "&&", 5)
    parse = hes.BashParse(["E() { :; }", "X=$(cat <<'E'", ")", "`git x && echo :`", "E"])
    assert parse.body_code_at(3, "&&", "E") is True


def test_the_join_spells_no_word_in_the_block():
    lines = ["cat <<'E'", "a && b", "xE", "E"]
    assert hes.BashParse(lines).body_code_at(1, "&&", "E") is False


@pytest.mark.parametrize("tail", ["echo z \\", "cat <<'E'\nz", "cat <<-'E'\n\tz"],
                         ids=["trailing-backslash", "eof-heredoc", "eof-dash-heredoc"])
def test_a_quote_is_vouched_for_beside_a_block_end_the_group_would_break(tail):
    """R16 (S1): inside `{ … }` the `}` joins a last word ending in `\\` or becomes text of an
    EOF-ended heredoc, so the grouped probe and control both fail. The ungrouped proof
    stands."""
    assert hes.BashParse(["echo 'a && b'"] + tail.split("\n")).code_at(0, 8, "&&") is False



# --- review round 17 of the round-16 fixes ----------------------------------------------


def test_a_hidden_delimiter_that_only_ends_in_the_join_is_not_proven_quoted():
    """R17 (S1): a body line ending in `\\` joins in front of the join line, so a hidden
    `<<axE` ends at `a\\` + `x\\` + `E`. `xE` occurs in the block only inside the word `axE`:
    the join must avoid it anywhere, not only as a word."""
    lines = [": \"${x:-'\"'}\" ; cat <<axE > /dev/null", "' ; cat <<'E'", "a\\",
             "$(git x && echo y)", "E", "axE"]
    assert hes.BashParse(lines).body_code_at(3, "&&", "E") is True
    assert (3, "&&") in hes.backstop(hes.lex(lines))


def test_the_line_check_goes_before_the_body_line():
    """R17 (S2): after the line it would land in the `<<'F'` the code line opens, and parse."""
    lines = ["E() { :; }", "X=$(cat <<'E'", ")", ": $(git x && :) <<'F'", "F", "E"]
    assert hes.BashParse(lines).body_code_at(3, "&&", "E") is True
    assert (3, "&&") in hes.backstop(hes.lex(lines))


# --- task #14: the runtime guard for code no parse saw -----------------------------------
#
# `.`/`source` runs a body no reader parsed, and a block that turns on aliases runs text
# `bash -n` read with them off. Both are recorded at run time and refused. `run_block` and
# the parse oracle use one pinned interpreter (`BASH`, task #8), so PATH no longer chooses.

BASHES = [hes.BASH]


def _under(bash):
    return {}


def _runtime(tmp_path, bash, body, kind, line):
    root, _, new = _repo(tmp_path)
    doc = _doc(tmp_path, f"{FENCE}bash\n{body}\n{FENCE}\n")
    result = run(tmp_path, [doc], root, new, env_extra=_under(bash))
    screen = body.count("\n") + 2
    assert _screens(result.stdout) == [
        f"screen: {doc}:{screen} expect=0 got=UNREADABLE:unsupported_runtime={kind}@{doc}:{line} "
        "FAIL"], result.stdout


SOURCED_LIST = f"{ERRORED} && echo x\nE\n"


@pytest.mark.parametrize("bash", BASHES)
@pytest.mark.parametrize("opener", [". /dev/stdin <<'E'", "source /dev/stdin <<'E'",
                                    "builtin . /dev/stdin <<'E'", "command source /dev/stdin <<'E'",
                                    "set -o posix; . /dev/stdin <<'E'"],
                         ids=["dot", "source", "builtin-dot", "command-source", "posix-dot"])
def test_a_sourced_heredoc_is_refused_at_its_line(tmp_path, bash, opener):
    """S4: the quoted body is literal to every reader, yet runs in this shell, so the `&&`
    hides git's 128 and the empty list read 0 (PASS) before the guard."""
    _runtime(tmp_path, bash, f"{opener}\n{SOURCED_LIST}" + SCREEN_LIST, "source", 2)


@pytest.mark.parametrize("bash", BASHES)
def test_a_source_inside_a_function_is_refused_at_the_source_line(tmp_path, bash):
    body = f"f() {{\n. /dev/stdin <<'E'\n{SOURCED_LIST}}}\nf\n" + SCREEN_LIST
    _runtime(tmp_path, bash, body, "source", 3)


@pytest.mark.parametrize("bash", BASHES)
def test_a_sourced_file_is_refused_too(tmp_path, bash):
    """A tracked file's body is as unparsed as a heredoc's: every `.`/`source` is refused."""
    body = f"echo '{ERRORED} && echo x' > s.sh\n. ./s.sh\n" + SCREEN_LIST
    _runtime(tmp_path, bash, body, "source", 3)


@pytest.mark.parametrize("bash", BASHES)
@pytest.mark.parametrize("setup", ["shopt -s expand_aliases", "set -o posix",
                                   "alias q=echo", "POSIXLY_CORRECT=1"],
                         ids=["expand-aliases", "posix", "alias-defined", "posixly-correct"])
def test_an_alias_mode_is_refused_at_the_screen(tmp_path, bash, setup):
    """R14 S1: an alias holding a `'` moves run-time quoting the parse read with aliases off."""
    _runtime(tmp_path, bash, f"{setup}\n: > list.txt\n" + SCREEN_LIST, "aliases", 4)


@pytest.mark.parametrize("bash", BASHES)
def test_an_alias_hiding_a_list_reads_unreadable_not_pass(tmp_path, bash):
    """R14 S1 end to end: the `&&` is single-quoted when the parse reads the `alias` line,
    but `q` runs it as a list at run time, so git's 128 is unrecorded and the empty list
    read 0 (PASS) before the guard."""
    body = f"shopt -s expand_aliases\nalias q='{ERRORED} && echo'\nq\n" + SCREEN_LIST
    _runtime(tmp_path, bash, body, "aliases", 5)


@pytest.mark.parametrize("bash", BASHES)
def test_a_clean_block_still_passes_and_reads_its_pipestatus(tmp_path, bash):
    """Negative control: neither shadow nor trap fires without a source, and the RETURN trap
    leaves a screen's PIPESTATUS alone (`grep -c` exiting 1 still reads 0)."""
    root, old, _ = _repo(tmp_path)
    result = run(tmp_path, [_doc(tmp_path, CORE)], root, old, env_extra=_under(bash))
    assert "EXPECT: PASS screens=1" in result.stdout, result.stdout


@pytest.mark.parametrize("bash", BASHES)
def test_a_bash_env_alias_is_not_the_documents(tmp_path, bash):
    """`unalias -a` in the preamble: a BASH_ENV that defines an alias must not refuse an
    honest document."""
    rc = tmp_path / "rc.sh"
    rc.write_text("alias ll='ls -l'\n")
    root, old, _ = _repo(tmp_path)
    result = run(tmp_path, [_doc(tmp_path, CORE)], root, old,
                 env_extra={**_under(bash), "BASH_ENV": str(rc)})
    assert "EXPECT: PASS screens=1" in result.stdout, result.stdout


@pytest.mark.parametrize("bash", BASHES)
def test_aliases_turned_off_inside_the_screen_are_still_seen_at_its_begin(tmp_path, bash):
    """The begin marker samples before the screen's own line can turn aliases off again."""
    body = ("shopt -s expand_aliases\n: > list.txt\n"
            "shopt -u expand_aliases; wc -l < list.txt | tr -d ' '   # expect 0")
    root, _, new = _repo(tmp_path)
    doc = _doc(tmp_path, f"{FENCE}bash\n{body}\n{FENCE}\n")
    result = run(tmp_path, [doc], root, new, env_extra=_under(bash))
    assert _screens(result.stdout) == [
        f"screen: {doc}:4 expect=0 got=UNREADABLE:unsupported_runtime=aliases@{doc}:4 FAIL"], \
        result.stdout


@pytest.mark.parametrize("bash", BASHES)
def test_aliases_turned_on_inside_the_screen_are_seen_at_its_end(tmp_path, bash):
    """The end marker samples after the screen's own line turned aliases on."""
    body = ": > list.txt\nshopt -s expand_aliases; wc -l < list.txt | tr -d ' '   # expect 0"
    root, _, new = _repo(tmp_path)
    doc = _doc(tmp_path, f"{FENCE}bash\n{body}\n{FENCE}\n")
    result = run(tmp_path, [doc], root, new, env_extra=_under(bash))
    assert _screens(result.stdout) == [
        f"screen: {doc}:3 expect=0 got=UNREADABLE:unsupported_runtime=aliases@{doc}:3 FAIL"], \
        result.stdout



# --- task #8: one pinned interpreter, never PATH's first `bash` --------------------------


def _decoy_bash(tmp_path):
    """A `bash` that is not one: first on PATH, it exits 99 for anything it is asked."""
    decoy = tmp_path / "decoy-bin"
    decoy.mkdir()
    (decoy / "bash").write_text("#!/bin/sh\nexit 99\n")
    (decoy / "bash").chmod(0o755)
    return {"PATH": f"{decoy}:{os.environ['PATH']}"}


@pytest.mark.skipif(not os.path.exists("/bin/bash"), reason="the pin is /bin/bash")
def test_screens_run_under_the_pinned_bash_not_paths(tmp_path):
    """A decoy `bash` first on PATH would kill every block (markers missing) if the runner
    resolved `bash` by PATH."""
    root, old, _ = _repo(tmp_path)
    result = run(tmp_path, [_doc(tmp_path, CORE)], root, old, env_extra=_decoy_bash(tmp_path))
    assert "EXPECT: PASS screens=1" in result.stdout, result.stdout


@pytest.mark.skipif(not os.path.exists("/bin/bash"), reason="the pin is /bin/bash")
def test_the_parse_oracle_uses_the_pinned_bash_not_paths(tmp_path, monkeypatch):
    """The oracle's `bash -n` answers from the same interpreter the block runs under; a decoy
    first on PATH would answer 99, i.e. no proof."""
    monkeypatch.setenv("PATH", _decoy_bash(tmp_path)["PATH"])
    assert hes.BashParse(["echo 'a && b'"]).code_at(0, 8, "&&") is False
