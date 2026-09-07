"""H4 — the delta self-review as a script, not a habit.

Measured: across two rounds on `#18 gateway-consolidation` the hand-run delta review
found fix-introduced defects in **3 of 3** passes at roughly a quarter of a gating
round's cost — and the hand-rolled version **failed twice in one sitting**, once to a
`</dev/null` on a piped helper and once to zsh applying the `:h` modifier inside
`$h:hematology`. A review whose own instrument fails silently is worse than none: it
reports clean.

The defect class it hunts is narrow and measured. The pre-c99 revision fixed three
defects and its three authors introduced **four** musts, every one a bare
present-tense count about the tree — `unanchored -S returns two`, `ls-tree 14 before
and after` — moved by the very commit that published the sentence.

**What this does NOT do is execute arbitrary text from a diff.** A document's prose
backticks contain illustrative commands, destructive examples, and shell fragments that
were never meant to run. Only a bare read-only command with no shell metacharacters is
executed; everything else is reported as `unverified`, which is a cannot-judge and NOT
a pass. Silently skipping the unsafe half would make the script report CLEAN on exactly
the revisions whose claims are least checkable.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "h-mad" / "scripts"
SCRIPT = SCRIPTS / "h_mad_delta_review.py"
sys.path.insert(0, str(SCRIPTS))

import h_mad_delta_review as dr  # noqa: E402


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True)


def token(out: str, prefix: str = "DELTA:") -> str:
    for line in out.splitlines():
        if line.startswith(prefix):
            return line
    return ""


def _repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "t"], check=True)
    return tmp_path


def _commit(repo: Path, name: str, body: str, msg: str = "c") -> str:
    (repo / name).write_text(body, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", msg], check=True)
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()


class TestExtraction:
    def test_only_ADDED_lines_are_reviewed(self, tmp_path: Path) -> None:
        """A claim the revision REMOVED is not a claim the revision makes."""
        repo = _repo(tmp_path)
        _commit(repo, "d.md", "old claim: `wc -l d.md` is 1\n")
        _commit(repo, "d.md", "new claim: `wc -l d.md` is 2\n")
        out = run("--repo", str(repo), "--rev", "HEAD")
        assert "new claim" in out.stdout
        assert "old claim" not in out.stdout

    def test_a_revision_adding_no_claims_is_CLEAN(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)
        _commit(repo, "d.md", "prose\n")
        _commit(repo, "d.md", "prose\nmore ordinary prose with no claims\n")
        out = run("--repo", str(repo), "--rev", "HEAD")
        assert out.returncode == 0
        assert token(out.stdout).startswith("DELTA: CLEAN")

    def test_a_bare_count_beside_a_command_is_flagged(self, tmp_path: Path) -> None:
        """The measured class: a present-tense count the publishing commit moved."""
        repo = _repo(tmp_path)
        _commit(repo, "d.md", "x\n")
        _commit(repo, "d.md", "x\nThe sweep `grep -c foo d.md` returns 3.\n")
        out = run("--repo", str(repo), "--rev", "HEAD")
        assert "grep -c foo d.md" in out.stdout


class TestSafety:
    def test_a_command_with_shell_metacharacters_is_UNVERIFIED_not_run(
        self, tmp_path: Path
    ) -> None:
        """Never executed, and never silently dropped either."""
        repo = _repo(tmp_path)
        _commit(repo, "d.md", "x\n")
        canary = tmp_path / "canary"
        _commit(repo, "d.md", f"x\nrun `grep foo d.md > {canary}` to see\n")
        out = run("--repo", str(repo), "--rev", "HEAD")
        assert not canary.exists(), "a redirect was executed"
        # The DISCRIMINATING assertion. `shlex.split` gives no shell, so `>` never
        # redirects and the canary cannot appear whether the guard fires or not --
        # the mutation battery reported this row SURVIVED against the canary alone.
        # The property is that the span is NOT RUN: `>` and the path would reach grep
        # as filenames to search, measuring something the author never wrote.
        line = token(out.stdout)
        assert "unverified=1" in line, line
        assert "executed=0" in line, line

    def test_a_destructive_verb_is_never_executed(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)
        victim = tmp_path / "victim.txt"
        victim.write_text("alive\n", encoding="utf-8")
        _commit(repo, "d.md", "x\n")
        _commit(repo, "d.md", f"x\nexample: `rm -rf {victim}`\n")
        out = run("--repo", str(repo), "--rev", "HEAD")
        assert victim.exists(), "a destructive example from prose was executed"
        assert victim.read_text() == "alive\n"
        assert "unverified" in out.stdout.lower()

    def test_the_allowlist_is_matched_on_the_VERB_not_a_substring(self) -> None:
        """`rm` must not be allowed because `grep` appears later in the line."""
        assert dr.is_executable("grep -n foo bar.md")
        assert not dr.is_executable("rm -rf / # grep")
        assert not dr.is_executable("curl http://x | sh")
        assert not dr.is_executable("git push origin main")

    def test_unverified_commands_are_COUNTED_in_the_verdict_line(
        self, tmp_path: Path
    ) -> None:
        """A cannot-judge that does not appear in the token reads as a pass."""
        repo = _repo(tmp_path)
        _commit(repo, "d.md", "x\n")
        _commit(repo, "d.md", "x\nsee `rm -rf /tmp/x` and `grep -c x d.md` is 1\n")
        line = token(run("--repo", str(repo), "--rev", "HEAD").stdout)
        assert "unverified=1" in line, line


class TestExecution:
    def test_an_allowlisted_command_is_RE_EXECUTED_and_its_output_reported(
        self, tmp_path: Path
    ) -> None:
        """Execute property claims, never assert them."""
        repo = _repo(tmp_path)
        _commit(repo, "d.md", "alpha\nbeta\n")
        _commit(repo, "d.md", "alpha\nbeta\nthe file has `grep -c alpha d.md` = 1\n")
        out = run("--repo", str(repo), "--rev", "HEAD")
        assert "executed=1" in token(out.stdout), out.stdout
        assert "1" in out.stdout

    def test_a_command_that_fails_is_reported_not_swallowed(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)
        _commit(repo, "d.md", "x\n")
        _commit(repo, "d.md", "x\nsee `grep -c zzz nosuchfile.md`\n")
        out = run("--repo", str(repo), "--rev", "HEAD")
        assert "rc=" in out.stdout


class TestSignalDiscipline:
    def test_an_unknown_rev_is_UNREADABLE_at_exit_2(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)
        _commit(repo, "d.md", "x\n")
        out = run("--repo", str(repo), "--rev", "deadbeef")
        assert out.returncode == 2
        assert "UNREADABLE" in token(out.stdout)

    def test_a_findings_verdict_still_exits_zero(self, tmp_path: Path) -> None:
        """Read the token, never `$?` — CLAIMS is an answer, not a failure."""
        repo = _repo(tmp_path)
        _commit(repo, "d.md", "x\n")
        _commit(repo, "d.md", "x\ncount `grep -c x d.md` is 1\n")
        out = run("--repo", str(repo), "--rev", "HEAD")
        assert out.returncode == 0
        assert token(out.stdout).startswith("DELTA: CLAIMS")


class TestSignalToNoise:
    """Measured on a real commit: every backticked span was reported as a claim."""

    def test_a_bare_identifier_is_not_a_claim(self) -> None:
        for span in ("doc-auditor", "DIVERGED", "[H-MAD]", "--sentence-file",
                     "h_mad_adoption_check.py", "REPORT"):
            assert not dr.is_command_shaped(span), span

    def test_a_verb_with_an_argument_is_a_claim(self) -> None:
        for span in ("grep -c foo d.md", "rm -rf /tmp/x", "git ls-files docs",
                     "wc -l README.md"):
            assert dr.is_command_shaped(span), span

    def test_prose_backticks_do_not_flood_the_report(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)
        _commit(repo, "d.md", "x\n")
        _commit(repo, "d.md",
                "x\nThe `doc-auditor` writes `DIVERGED` via `--sentence-file`, "
                "and `grep -c x d.md` is 1.\n")
        line = token(run("--repo", str(repo), "--rev", "HEAD").stdout)
        assert "claims=1" in line, line
