"""Tests for h_mad_extract_report.py — sentinel-delimited report extraction.

`hmad-dispatch read` scrapes a live pane, so the capture routinely contains
the previous cycle's report sitting above the new prompt. Extracting on the
first `## Summary` therefore picked up a stale verdict and the gate scored the
wrong cycle. The skill warned about this and it still happened, because the
warning had no mechanism behind it.

The reviewer now brackets its report in a per-cycle sentinel and extraction
takes the LAST complete pair, so an older report in scrollback cannot win.
"""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "h_mad_extract_report.py"
sys.path.insert(0, str(SCRIPTS))

import h_mad_extract_report as er  # noqa: E402

SENTINEL = "AUDIT-myfeat-plan-v2"


def framed(body: str, sentinel: str = SENTINEL) -> str:
    return f"{sentinel}-BEGIN\n{body}\n{sentinel}-END"


REPORT_V2 = "## Summary\nThe fresh one.\n\n## Must-fix\nNone\n\n## Should-fix\nNone"
REPORT_V1 = "## Summary\nThe stale one.\n\n## Must-fix\n- an old finding — reason"


class TestExtract:
    def test_extracts_a_single_framed_report(self):
        assert er.extract(framed(REPORT_V2), SENTINEL) == REPORT_V2

    def test_ignores_chatter_around_the_frame(self):
        scrape = f"agy> reading file...\n{framed(REPORT_V2)}\nagy> \n"
        assert er.extract(scrape, SENTINEL) == REPORT_V2

    def test_takes_the_last_pair_when_the_sentinel_repeats(self):
        """A retry within the same cycle reuses the sentinel; newest wins."""
        scrape = f"{framed('stale body')}\nagy> \n{framed(REPORT_V2)}"
        assert er.extract(scrape, SENTINEL) == REPORT_V2

    def test_a_prior_cycles_report_cannot_win(self):
        """The exact regression: v1's report is still in scrollback above v2's."""
        scrape = (
            f"{framed(REPORT_V1, 'AUDIT-myfeat-plan-v1')}\n"
            f"agy> \n"
            f"{framed(REPORT_V2, SENTINEL)}"
        )
        out = er.extract(scrape, SENTINEL)
        assert out == REPORT_V2
        assert "stale" not in out

    def test_unframed_summary_above_is_not_picked_up(self):
        scrape = f"## Summary\nan unframed stale report\n\n{framed(REPORT_V2)}"
        assert er.extract(scrape, SENTINEL) == REPORT_V2

    def test_body_preserves_internal_blank_lines(self):
        assert "\n\n" in er.extract(framed(REPORT_V2), SENTINEL)


class TestFailureModes:
    """Absent or empty output must fail loudly, never yield a scored verdict."""

    def test_missing_sentinel_raises(self):
        with pytest.raises(er.ExtractionError, match="no complete"):
            er.extract("agy> just a prompt, no report\n", SENTINEL)

    def test_begin_without_end_raises(self):
        with pytest.raises(er.ExtractionError, match="no complete"):
            er.extract(f"{SENTINEL}-BEGIN\n{REPORT_V2}\n", SENTINEL)

    def test_empty_body_raises(self):
        """The 'dispatched, went idle, produced nothing' case."""
        with pytest.raises(er.ExtractionError, match="empty"):
            er.extract(framed("   \n  \n"), SENTINEL)

    def test_empty_scrape_raises(self):
        with pytest.raises(er.ExtractionError):
            er.extract("", SENTINEL)

    def test_wrong_sentinel_raises(self):
        with pytest.raises(er.ExtractionError):
            er.extract(framed(REPORT_V2, "AUDIT-other-v9"), SENTINEL)


class TestSentinelFor:
    def test_builds_a_per_cycle_sentinel(self):
        assert er.sentinel_for("myfeat", "plan", 2) == "AUDIT-myfeat-plan-v2"

    def test_distinct_cycles_differ(self):
        assert er.sentinel_for("f", "plan", 1) != er.sentinel_for("f", "plan", 2)

    def test_distinct_phases_differ(self):
        assert er.sentinel_for("f", "plan", 1) != er.sentinel_for("f", "design", 1)


class TestCli:
    def run(self, scrape_text, *args, tmp_path):
        src = tmp_path / "scrape.txt"
        src.write_text(scrape_text)
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(src), *args],
            capture_output=True,
            text=True,
        )

    def test_writes_report_to_stdout(self, tmp_path):
        r = self.run(framed(REPORT_V2), "--sentinel", SENTINEL, tmp_path=tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == REPORT_V2

    def test_builds_sentinel_from_parts(self, tmp_path):
        r = self.run(
            framed(REPORT_V2),
            "--feature", "myfeat", "--phase", "plan", "--cycle", "2",
            tmp_path=tmp_path,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == REPORT_V2

    def test_missing_report_exits_2_and_writes_nothing(self, tmp_path):
        r = self.run("agy> nothing here", "--sentinel", SENTINEL, tmp_path=tmp_path)
        assert r.returncode == 2
        assert r.stdout.strip() == ""
        assert "no complete" in r.stderr.lower()

    def test_missing_file_exits_2(self, tmp_path):
        r = subprocess.run(
            [sys.executable, str(SCRIPT), str(tmp_path / "nope.txt"),
             "--sentinel", SENTINEL],
            capture_output=True, text=True,
        )
        assert r.returncode == 2
