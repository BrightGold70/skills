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


BOUNDARY = "===HMAD-DISPATCH-BOUNDARY==="

# The exact shape that produced a false STATUS: DONE: the dispatched prompt
# quotes its own output contract, the agent emitted nothing, and the buffer holds
# only the echoed prompt. Without slicing, the contract's `STATUS: DONE` line is
# read back as the agent's verdict.
ECHOED_CONTRACT = (
    "codex> follow the instructions\n"
    "Report exactly one of:\n"
    "  STATUS: DONE\n"
    "  or STATUS: DONE_WITH_CONCERNS\n"
    "  or STATUS: BLOCKED\n"
    "  or STATUS: NEEDS_CONTEXT\n"
    f"{BOUNDARY}\n"
    "codex> \n"
)


class TestBoundarySlice:
    def test_echoed_contract_only_raises_when_sliced(self):
        """Silent agent: buffer is pure prompt echo below the boundary."""
        with pytest.raises(ev.VerdictError, match="no STATUS"):
            ev.extract_verdict(ECHOED_CONTRACT, "STATUS", after=BOUNDARY)

    def test_without_slice_the_echo_wins_documenting_the_bug(self):
        """The pre-fix behaviour, pinned: no slice ⇒ the echo reads as DONE.

        Only `STATUS: DONE` starts its line; the `or STATUS: …` alternatives
        have `or ` before the key so the anchor skips them. The canonical form
        the contract lists first is exactly what wins — the observed false DONE.
        """
        assert ev.extract_verdict(ECHOED_CONTRACT, "STATUS") == "DONE"

    def test_real_verdict_after_boundary_wins(self):
        scrape = ECHOED_CONTRACT + "...ran the suite...\nSTATUS: BLOCKED\n"
        assert ev.extract_verdict(scrape, "STATUS", after=BOUNDARY) == "BLOCKED"

    def test_verdict_above_boundary_is_ignored(self):
        """A prior cycle's real DONE sits above this dispatch's boundary."""
        scrape = "STATUS: DONE\n" + ECHOED_CONTRACT + "STATUS: BLOCKED\n"
        assert ev.extract_verdict(scrape, "STATUS", after=BOUNDARY) == "BLOCKED"

    def test_absent_boundary_fails_closed(self):
        with pytest.raises(ev.VerdictError, match="boundary marker"):
            ev.extract_verdict("STATUS: DONE\n", "STATUS", after=BOUNDARY)

    def test_last_boundary_is_the_anchor(self):
        """Two dispatches in scrollback: only the most recent reply counts."""
        scrape = (
            f"STATUS: DONE\n{BOUNDARY}\nSTATUS: COMPLIANT_OLD\n"
            f"{BOUNDARY}\nSTATUS: BLOCKED\n"
        )
        assert ev.extract_verdict(scrape, "STATUS", after=BOUNDARY) == "BLOCKED"


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


class TestConcernContent:
    @pytest.mark.parametrize(
        "scrape",
        [
            "STATUS: DONE_WITH_CONCERNS\nConcerns: flaky integration test\n",
            "STATUS: DONE_WITH_CONCERNS\nWorking-tree concern: generated file is untracked\n",
            "STATUS: DONE_WITH_CONCERNS\nConcerns / blockers: flaky integration test\n",
            "STATUS: DONE_WITH_CONCERNS\n## Concerns\nThe fixture needs review.\n",
            "STATUS: DONE_WITH_CONCERNS\n**Concerns:** the report is incomplete\n",
            "STATUS: DONE_WITH_CONCERNS\nConcerns: none of the tests cover submodules, which is a real gap\n",
        ],
    )
    def test_substantive_concern_is_detected(self, scrape):
        assert ev.concern_stated(scrape)

    @pytest.mark.parametrize(
        "scrape",
        [
            "STATUS: DONE_WITH_CONCERNS\n",
            "STATUS: DONE_WITH_CONCERNS\nNo relevant section here.\n",
            "STATUS: DONE_WITH_CONCERNS\nConcerns: none\n",
            "STATUS: DONE_WITH_CONCERNS\nConcerns: None\n",
            "STATUS: DONE_WITH_CONCERNS\nConcerns: NONE\n",
            "STATUS: DONE_WITH_CONCERNS\nConcerns: n/a\n",
            "STATUS: DONE_WITH_CONCERNS\nConcerns:\n- none\n",
            "STATUS: DONE_WITH_CONCERNS\nConcerns / blockers / context needed:\n- None.\n",
            "STATUS: DONE_WITH_CONCERNS\n## Concerns\nNone\n",
        ],
    )
    def test_missing_or_negated_concern_is_rejected(self, scrape):
        assert not ev.concern_stated(scrape)


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

    def test_contentless_done_with_concerns_exits_2_without_verdict(self, tmp_path):
        r = self.run("STATUS: DONE_WITH_CONCERNS\nConcerns: none\n", "--key", "STATUS", tmp_path=tmp_path)
        assert r.returncode == 2
        assert r.stdout.strip() == ""
        assert "but the report names no concern" in r.stderr
        assert "no STATUS" not in r.stderr

    @pytest.mark.parametrize(
        ("key", "value"),
        [
            ("STATUS", "DONE"),
            ("STATUS", "BLOCKED"),
            ("STATUS", "NEEDS_CONTEXT"),
            ("VERDICT", "COMPLIANT"),
            ("VERDICT", "DRIFT"),
            ("ASSESSMENT", "READY_TO_MERGE"),
        ],
    )
    def test_other_contracts_are_unaffected_without_concerns(self, key, value, tmp_path):
        r = self.run(f"{key}: {value}\n", "--key", key, tmp_path=tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == f"{key}: {value}"

    def test_emits_hmad_marker_when_asked(self, tmp_path):
        # J26: the marker goes to STDERR. This script differs in kind from its
        # siblings — theirs print a report to be READ, this one prints a value to
        # be CAPTURED — so its stdout must carry the verdict and nothing else.
        r = self.run(
            "STATUS: DONE\n",
            "--key", "STATUS", "--feature", "myfeat", "--phase", "5e",
            tmp_path=tmp_path,
        )
        assert "[H-MAD] myfeat phase5e" in r.stderr

    def test_stdout_is_only_the_verdict_so_a_bare_capture_is_safe(self, tmp_path):
        """J26, the defect this pins: the marker used to land on stdout, so the
        obvious `V=$(... )` yielded TWO lines and `h_mad_state_write.py` refused
        the malformed value. Observed live on gate-blindness-hardening's own
        6a-prime — the write was rejected and the read-back reported `None`.

        Asserting `in r.stdout` is not enough: the bug was an EXTRA line, so only
        an exact single-line equality can catch it.
        """
        r = self.run(
            "ASSESSMENT: READY_TO_MERGE\n",
            "--key", "ASSESSMENT", "--feature", "myfeat", "--phase", "6a-prime",
            tmp_path=tmp_path,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == "ASSESSMENT: READY_TO_MERGE"
        assert r.stdout.strip().count("\n") == 0
        assert "[H-MAD]" not in r.stdout

    def test_after_marker_bare_flag_slices_echo(self, tmp_path):
        r = self.run(ECHOED_CONTRACT, "--key", "STATUS", "--after-marker",
                     tmp_path=tmp_path)
        assert r.returncode == 2
        assert r.stdout.strip() == ""
        assert "no STATUS" in r.stderr

    def test_after_marker_absent_boundary_exits_2(self, tmp_path):
        r = self.run("STATUS: DONE\n", "--key", "STATUS", "--after-marker",
                     tmp_path=tmp_path)
        assert r.returncode == 2
        assert "boundary marker" in r.stderr

    def test_after_marker_passes_real_verdict(self, tmp_path):
        scrape = ECHOED_CONTRACT + "STATUS: DONE\n"
        r = self.run(scrape, "--key", "STATUS", "--after-marker",
                     tmp_path=tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == "STATUS: DONE"

    def test_missing_file_exits_2(self, tmp_path):
        r = subprocess.run(
            [sys.executable, str(SCRIPT), str(tmp_path / "nope.txt"),
             "--key", "STATUS"],
            capture_output=True, text=True,
        )
        assert r.returncode == 2


class TestTheConcernShapeIsSpelled:
    """#152 — the extractor refused a DONE_WITH_CONCERNS whose concern was in prose.

    The refusal is right (the parser keys on a label), but neither codex prompt said
    so and the error message did not either, so the agent could not have complied
    and the operator could not tell why a report with a visible concern was
    "contentless". Both prompts and the error now spell the label.
    """

    REFS = Path(__file__).resolve().parents[1] / "references"

    def test_prose_only_concern_is_still_rejected_and_the_error_names_the_label(self, tmp_path):
        scrape = tmp_path / "out.txt"
        scrape.write_text(
            "Work is complete. I am not sure the timeout path is exercised by the\n"
            "wire test, which worries me.\n\nSTATUS: DONE_WITH_CONCERNS\n",
            encoding="utf-8",
        )
        r = subprocess.run([sys.executable, str(SCRIPT), str(scrape), "--key", "STATUS"],
                           capture_output=True, text=True)
        assert r.returncode == 2
        assert "Concerns:" in r.stderr, r.stderr

    def test_a_labelled_concern_is_accepted(self, tmp_path):
        scrape = tmp_path / "out.txt"
        scrape.write_text(
            "Work is complete.\n\nConcerns: the timeout path is not exercised by the wire test.\n"
            "\nSTATUS: DONE_WITH_CONCERNS\n",
            encoding="utf-8",
        )
        r = subprocess.run([sys.executable, str(SCRIPT), str(scrape), "--key", "STATUS"],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        assert r.stdout.strip() == "STATUS: DONE_WITH_CONCERNS"

    @pytest.mark.parametrize("name", ["codex-implementer-prompt.md", "codex-verifier-prompt.md"])
    def test_both_codex_prompts_spell_the_label(self, name):
        text = (self.REFS / name).read_text(encoding="utf-8")
        assert "`Concerns:`" in text, f"{name} does not tell the agent the label the parser keys on"
        after = text.split("`Concerns:`", 1)[1]
        assert "prose" in after and "contentless" in after, (
            f"{name} names the label but not that prose-only is rejected")
