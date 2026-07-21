"""Tests for h_mad_extract_verdict.py — verdict-line extraction from a scrape.

Three dispatch contracts end in a machine-parsed line:

    STATUS:     DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT   (5d/5e codex)
    VERDICT:    COMPLIANT | DRIFT                                     (5e-review agy)
    ASSESSMENT: READY_TO_MERGE | WITH_FIXES | NO                      (6a-prime agy)

Each is read off a scraped pane, so each carries the two failures #2 fixed for
audits: a prior module's verdict still in scrollback, and an agent that went
idle without emitting anything. The second is the dangerous one — with no
verdict line at all, a naive grep finds nothing and the caller must not read
that as "no problems".
"""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "h_mad_extract_verdict.py"
sys.path.insert(0, str(SCRIPTS))

import h_mad_extract_verdict as ev  # noqa: E402

CODEX_VALUES = ["DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"]


class TestExtractVerdict:
    def test_reads_a_simple_verdict(self):
        assert ev.extract_verdict("STATUS: DONE\n", "STATUS") == "DONE"

    def test_ignores_surrounding_chatter(self):
        scrape = "codex> running pytest...\n8 passed\nSTATUS: DONE\ncodex> \n"
        assert ev.extract_verdict(scrape, "STATUS") == "DONE"

    def test_tolerates_leading_whitespace(self):
        assert ev.extract_verdict("   STATUS: BLOCKED\n", "STATUS") == "BLOCKED"

    def test_tolerates_no_space_after_colon(self):
        assert ev.extract_verdict("STATUS:DONE\n", "STATUS") == "DONE"

    def test_takes_the_last_occurrence(self):
        """A previous module's verdict is still in scrollback above this one."""
        scrape = "STATUS: DONE\ncodex> next module\nSTATUS: BLOCKED\n"
        assert ev.extract_verdict(scrape, "STATUS") == "BLOCKED"

    def test_prior_module_verdict_cannot_win(self):
        scrape = (
            "STATUS: DONE\n"
            "codex> module 2 of 3\n"
            "...work...\n"
            "STATUS: NEEDS_CONTEXT\n"
            "codex> \n"
        )
        assert ev.extract_verdict(scrape, "STATUS") == "NEEDS_CONTEXT"

    def test_key_must_start_the_line(self):
        """Prose mentioning the key must not be mistaken for the verdict."""
        scrape = "I will emit STATUS: DONE when finished\nSTATUS: BLOCKED\n"
        assert ev.extract_verdict(scrape, "STATUS") == "BLOCKED"

    def test_other_contracts_work_the_same(self):
        assert ev.extract_verdict("VERDICT: DRIFT\n", "VERDICT") == "DRIFT"
        assert (
            ev.extract_verdict("ASSESSMENT: READY_TO_MERGE\n", "ASSESSMENT")
            == "READY_TO_MERGE"
        )

    def test_a_different_key_is_not_matched(self):
        with pytest.raises(ev.VerdictError):
            ev.extract_verdict("VERDICT: DRIFT\n", "STATUS")


class TestAllowedValues:
    def test_accepts_a_listed_value(self):
        got = ev.extract_verdict("STATUS: DONE\n", "STATUS", allowed=CODEX_VALUES)
        assert got == "DONE"

    def test_rejects_an_unlisted_value(self):
        with pytest.raises(ev.VerdictError, match="not one of"):
            ev.extract_verdict("STATUS: FINISHED\n", "STATUS", allowed=CODEX_VALUES)

    def test_last_occurrence_is_the_one_validated(self):
        scrape = "STATUS: DONE\nSTATUS: FINISHED\n"
        with pytest.raises(ev.VerdictError, match="not one of"):
            ev.extract_verdict(scrape, "STATUS", allowed=CODEX_VALUES)


class TestSilentFailureModes:
    """The whole point: silence must never read as success."""

    def test_no_verdict_line_raises(self):
        with pytest.raises(ev.VerdictError, match="no STATUS"):
            ev.extract_verdict("codex> ran some tests\n8 passed\n", "STATUS")

    def test_empty_scrape_raises(self):
        """Dispatched, went idle, produced nothing."""
        with pytest.raises(ev.VerdictError, match="no STATUS"):
            ev.extract_verdict("", "STATUS")

    def test_whitespace_only_scrape_raises(self):
        with pytest.raises(ev.VerdictError):
            ev.extract_verdict("\n   \n\n", "STATUS")

    def test_bare_prompt_scrape_raises(self):
        """The observed shape: agent returned to its prompt with no report."""
        with pytest.raises(ev.VerdictError):
            ev.extract_verdict("agy> \nagy> \n", "VERDICT")

    def test_empty_value_raises(self):
        with pytest.raises(ev.VerdictError, match="empty"):
            ev.extract_verdict("STATUS:\n", "STATUS")


class TestCli:
    def run(self, text, *args, tmp_path):
        src = tmp_path / "scrape.txt"
        src.write_text(text)
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(src), *args],
            capture_output=True,
            text=True,
        )

    def test_prints_verdict_and_exits_0(self, tmp_path):
        r = self.run("STATUS: DONE\n", "--key", "STATUS", tmp_path=tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == "STATUS: DONE"

    def test_allowed_list_enforced(self, tmp_path):
        r = self.run(
            "STATUS: FINISHED\n",
            "--key", "STATUS", "--allowed", ",".join(CODEX_VALUES),
            tmp_path=tmp_path,
        )
        assert r.returncode == 2
        assert "not one of" in r.stderr

    def test_missing_verdict_exits_2_and_prints_nothing(self, tmp_path):
        r = self.run("codex> idle\n", "--key", "STATUS", tmp_path=tmp_path)
        assert r.returncode == 2
        assert r.stdout.strip() == ""
        assert "no STATUS" in r.stderr

    def test_emits_hmad_marker_when_asked(self, tmp_path):
        r = self.run(
            "STATUS: DONE\n",
            "--key", "STATUS", "--feature", "myfeat", "--phase", "5e",
            tmp_path=tmp_path,
        )
        assert "[H-MAD] myfeat phase5e" in r.stdout

    def test_missing_file_exits_2(self, tmp_path):
        r = subprocess.run(
            [sys.executable, str(SCRIPT), str(tmp_path / "nope.txt"),
             "--key", "STATUS"],
            capture_output=True, text=True,
        )
        assert r.returncode == 2
