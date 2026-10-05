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
    """R2-M1(a): `'<<EOF'` in a quoted grep pattern turned every later line into a heredoc body."""
    root, _, new = _repo(tmp_path)
    doc = _doc(tmp_path, PASSING_BLOCK + f"""{FENCE}bash
N=$(grep -c '<<EOF' a.txt || true)
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


def test_an_explicit_or_true_states_that_no_match_is_intended(tmp_path):
    """R3's remedy: the author writes `|| true` (or `|| :`) and the published screen says so."""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
MOVED=$(git ls-files | grep '\\.py$' || true)
N=$(grep -c NOPE a.txt || :)
LC_ALL=C grep -c NOPE a.txt || true
echo 0   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [f"screen: {doc}:5 expect=0 got=0 PASS"], result.stdout


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
    """R3: only the assignment's own status shows this failure -- `|| exit 1` fires no ERR
    inside the substitution -- so it must be recorded whatever the statement's text."""
    root, _, new = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
B=$(git rev-parse --verify --quiet nosuchref || exit 1)
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


def test_tests_arithmetic_and_redirections_are_not_lists(tmp_path):
    """R4: `&&` inside `[[ ]]` or `(( ))`, `2>&1` and `&>` are not lists or jobs.
    (`|&` is bash 4+; /bin/bash here is 3.2, where it is a syntax error.)"""
    root, old, _ = _repo(tmp_path)
    doc = _doc(tmp_path, f"""{FENCE}bash
[[ -n x && -n y ]]
n=$(( 1 && 1 ))
ls a.txt > /dev/null 2>&1
ls a.txt &> /dev/null
echo 0   # expect 0
{FENCE}
""")
    result = run(tmp_path, [doc], root, old)
    assert _screens(result.stdout) == [f"screen: {doc}:6 expect=0 got=0 PASS"], result.stdout


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


def test_the_status_one_only_remedy_surfaces_a_bad_base(tmp_path):
    """R5 Must-B (x8): grep's 1 is absorbed, git's 128 is not -- pipefail carries it out."""
    root, _, new = _repo(tmp_path)
    doc, result = _one(tmp_path, root, new, "BASE=nosuchref\n" + REMEDY)
    assert _screens(result.stdout) == [
        f"screen: {doc}:4 expect=0 got=UNREADABLE:failed_command={doc}:3:128 FAIL"], result.stdout


def test_the_status_one_only_remedy_passes_a_clean_no_match(tmp_path):
    """R5 Must-B (x9): a good base whose diff matches nothing reads 0 and PASSES."""
    root, _, new = _repo(tmp_path)
    doc, result = _one(tmp_path, root, new, "BASE=HEAD\n" + REMEDY)
    assert _screens(result.stdout) == [f"screen: {doc}:4 expect=0 got=0 PASS"], result.stdout


def test_a_guard_that_exits_or_returns_is_not_refused(tmp_path):
    """R5 Should-A (o3, o4): `|| exit [N]` / `|| return [N]` end with a non-zero status the trap sees."""
    root, old, _ = _repo(tmp_path)
    doc, result = _one(tmp_path, root, old,
                       "cd . || exit 1\n"
                       "go() { cd . || return 1; }\n"
                       "go || exit\n"
                       "echo 0   # expect 0")
    assert _screens(result.stdout) == [f"screen: {doc}:5 expect=0 got=0 PASS"], result.stdout


def test_a_list_inside_a_condition_is_not_refused(tmp_path):
    """R5 Should-A (o2): conditions are left as written, `&&`/`||` in them included."""
    root, old, _ = _repo(tmp_path)
    doc, result = _one(tmp_path, root, old,
                       "if [ -f a.txt ] && [ -f nosuch ]; then echo yes; fi\n"
                       "while false || false; do :; done\n"
                       "until true && true; do :; done\n"
                       "echo 0   # expect 0")
    assert _screens(result.stdout) == [f"screen: {doc}:5 expect=0 got=0 PASS"], result.stdout


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
