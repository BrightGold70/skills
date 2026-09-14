"""Tests for `h_mad_check_memory_index.py`.

`TestAgainstTheLiveBinary` re-derives all four constants from the installed
Claude Code binary on every run, and SKIPS — never passes — when the binary
cannot be read. Every other test runs off fixtures, because the live index is a
moving target and a test that reads it would change its verdict whenever someone
writes a memory.

The load-bearing case is `TestTheWorstDimensionWins`: a byte-only check reports
OK on an index that is over on LINES, and the loader scores both and takes the
worse. That asymmetry is the reason this is not a `wc -c` one-liner.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from h_mad_check_memory_index import (  # noqa: E402
    BYTE_CAP,
    LINE_CAP,
    TARGET_FRAC,
    WARN_FRAC,
    assess,
    check,
    default_indexes,
    dropped_text,
    measure,
    render_kb,
)

SCRIPT = SCRIPTS / "h_mad_check_memory_index.py"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
    )


def _claude_binary() -> Path | None:
    which = subprocess.run(["which", "claude"], capture_output=True, text=True)
    if which.returncode != 0 or not which.stdout.strip():
        return None
    resolved = subprocess.run(
        ["readlink", "-f", which.stdout.strip()], capture_output=True, text=True
    )
    target = (resolved.stdout.strip() if resolved.returncode == 0 else "") or which.stdout.strip()
    p = Path(target)
    return p if p.is_file() else None


class TestAgainstTheLiveBinary:
    """Re-derive the contract rather than trusting the transcription.

    Matched on VALUES in their declaring context, never on the minified names
    (`F2`, `hD`, `Ams`, `xZn`) — those are regenerated per build and pinning them
    goes red on a rename that changed nothing.
    """

    def _blob(self) -> str:
        binary = _claude_binary()
        if binary is None:
            pytest.skip("claude binary not found — cannot verify, and will not pass")
        try:
            return binary.read_bytes().decode("utf-8", "replace")
        except OSError as exc:
            pytest.skip(f"claude binary unreadable ({exc}) — cannot verify")

    def test_the_warn_and_target_fractions_still_match(self) -> None:
        """Both live in one `var` declaration next to the cap machinery."""
        blob = self._blob()
        m = re.search(r"var (\w+)=0\.8,(\w+)=0\.7;", blob)
        assert m, "the 0.8/0.7 declaration pair is no longer in the binary"
        assert (WARN_FRAC, TARGET_FRAC) == (0.8, 0.7)

    def test_the_byte_cap_is_still_the_splice_cap_in_the_size_warning(self) -> None:
        """`${Ot(d)} (limit: ${Ot(F2)})` — the byte limit the loader reports."""
        blob = self._blob()
        m = re.search(r"var (\w+)=25000,", blob)
        assert m, "25000 is no longer declared — BYTE_CAP may be stale"
        assert BYTE_CAP == 25000

    def test_the_line_cap_is_still_two_hundred(self) -> None:
        blob = self._blob()
        assert re.search(r"=200;?\}?function|,(\w+)=200\b", blob), "200 not found"
        assert LINE_CAP == 200

    def test_the_silent_drop_wording_still_describes_this_failure(self) -> None:
        """If this sentence goes, the premise of the whole script should be re-checked:
        it is the only statement that the overflow is dropped at LOAD, not at write."""
        blob = self._blob()
        # The binary stores this sentence TWICE and one copy is wide-encoded
        # (`i s   s i l e n t l y …`), so a plain substring search finds only the
        # narrow copy and would go red on a build that kept just the wide one.
        # Collapsing whitespace matches either.
        flat = re.sub(r"\s+", " ", re.sub(r"[^\x20-\x7e]", " ", blob))
        assert "is silently dropped each time the index is loaded" in flat, (
            "the load-time drop wording is gone — re-verify the failure mode "
            "before trusting this script's premise"
        )


class TestTheWorstDimensionWins:
    """The reason this is not `wc -c`."""

    def test_over_on_lines_while_comfortably_under_on_bytes(self) -> None:
        a = assess(size_bytes=5_000, line_count=LINE_CAP + 1)
        assert a["dimension"] == "lines"
        assert a["verdict"] == "OVER"

    def test_over_on_bytes_while_comfortably_under_on_lines(self) -> None:
        a = assess(size_bytes=BYTE_CAP + 1, line_count=10)
        assert a["dimension"] == "bytes"
        assert a["verdict"] == "OVER"

    def test_the_higher_fraction_is_reported_even_when_neither_is_over(self) -> None:
        """80% of lines beats 40% of bytes — a reader needs the binding one."""
        a = assess(size_bytes=int(BYTE_CAP * 0.4), line_count=int(LINE_CAP * 0.8))
        assert a["dimension"] == "lines"
        assert a["verdict"] == "WARN"


class TestTheBoundaries:
    def test_exactly_at_the_cap_is_not_over(self) -> None:
        """The loader's own test is `size > cap`, not `>=`."""
        assert assess(BYTE_CAP, 1)["verdict"] != "OVER"
        assert assess(1, LINE_CAP)["verdict"] != "OVER"

    def test_one_byte_past_the_cap_is_over(self) -> None:
        assert assess(BYTE_CAP + 1, 1)["verdict"] == "OVER"

    def test_exactly_at_the_warn_fraction_warns(self) -> None:
        assert assess(int(BYTE_CAP * WARN_FRAC), 1)["verdict"] == "WARN"

    def test_just_below_the_warn_fraction_is_ok(self) -> None:
        assert assess(int(BYTE_CAP * WARN_FRAC) - 1, 1)["verdict"] == "OK"

    def test_the_compaction_target_is_seventy_percent_of_the_binding_cap(self) -> None:
        assert assess(BYTE_CAP + 1, 1)["target"] == 17500
        assert assess(1, LINE_CAP + 1)["target"] == 140


class TestDroppedText:
    def test_it_returns_exactly_the_bytes_past_the_cap(self, tmp_path: Path) -> None:
        p = tmp_path / "MEMORY.md"
        p.write_bytes(b"x" * BYTE_CAP + b"THIS IS INVISIBLE")
        assert dropped_text(p) == "THIS IS INVISIBLE"

    def test_an_index_under_the_cap_drops_nothing(self, tmp_path: Path) -> None:
        p = tmp_path / "MEMORY.md"
        p.write_bytes(b"x" * 100)
        assert dropped_text(p) == ""

    def test_an_index_exactly_at_the_cap_drops_nothing(self, tmp_path: Path) -> None:
        p = tmp_path / "MEMORY.md"
        p.write_bytes(b"x" * BYTE_CAP)
        assert dropped_text(p) == ""


class TestLineCounting:
    def test_a_final_line_without_a_newline_still_counts(self) -> None:
        """`wc -l` counts newlines and would report 1 here. A loader splitting on
        newline sees two lines, and the cap is the loader's."""
        import tempfile

        with tempfile.NamedTemporaryFile("wb", suffix=".md", delete=False) as fh:
            fh.write(b"one\ntwo")
            p = Path(fh.name)
        assert measure(p)[1] == 2

    def test_a_trailing_newline_does_not_invent_a_line(self, tmp_path: Path) -> None:
        p = tmp_path / "MEMORY.md"
        p.write_bytes(b"one\ntwo\n")
        assert measure(p)[1] == 2

    def test_an_empty_file_is_zero_and_zero(self, tmp_path: Path) -> None:
        p = tmp_path / "MEMORY.md"
        p.write_bytes(b"")
        assert measure(p) == (0, 0)


class TestRendering:
    def test_the_cap_renders_the_way_the_warning_spells_it(self) -> None:
        """25000 must read as 24.4KB, or this script and the hook disagree about
        the same number and a reader cannot reconcile them."""
        assert render_kb(BYTE_CAP) == "24.4KB"

    def test_the_target_renders_as_the_warning_spells_it(self) -> None:
        assert render_kb(int(BYTE_CAP * TARGET_FRAC)) == "17.1KB"


class TestUnreadableIsNotClean:
    def test_a_missing_index_reports_unreadable(self, tmp_path: Path) -> None:
        verdict, line = check(tmp_path / "nope.md")
        assert verdict == "UNREADABLE"
        assert "UNREADABLE" in line

    def test_the_cli_exits_two_on_an_unreadable_index(self, tmp_path: Path) -> None:
        assert run_cli(str(tmp_path / "nope.md")).returncode == 2


class TestCLI:
    def _write(self, tmp_path: Path, size: int) -> Path:
        p = tmp_path / "MEMORY.md"
        p.write_bytes(b"x" * size)
        return p

    def test_a_clean_index_exits_zero(self, tmp_path: Path) -> None:
        r = run_cli(str(self._write(tmp_path, 100)))
        assert r.returncode == 0
        assert "OK" in r.stdout

    def test_an_over_index_exits_one(self, tmp_path: Path) -> None:
        r = run_cli(str(self._write(tmp_path, BYTE_CAP + 50)))
        assert r.returncode == 1
        assert "OVER" in r.stdout
        assert "dropped=50" in r.stdout

    def test_a_warning_index_exits_one_too(self, tmp_path: Path) -> None:
        """WARN is actionable: it is the last moment a compaction is cheap."""
        r = run_cli(str(self._write(tmp_path, int(BYTE_CAP * 0.85))))
        assert r.returncode == 1
        assert "WARN" in r.stdout

    def test_show_dropped_prints_the_invisible_text(self, tmp_path: Path) -> None:
        p = tmp_path / "MEMORY.md"
        p.write_bytes(b"x" * BYTE_CAP + b"\nLOST ENTRY")
        r = run_cli(str(p), "--show-dropped")
        assert "LOST ENTRY" in r.stdout
        assert "DROPPED on every load" in r.stdout

    def test_show_dropped_is_silent_for_a_clean_index(self, tmp_path: Path) -> None:
        r = run_cli(str(self._write(tmp_path, 100)), "--show-dropped")
        assert "DROPPED" not in r.stdout

    def test_one_bad_index_among_several_good_ones_still_exits_one(
        self, tmp_path: Path
    ) -> None:
        good, bad = tmp_path / "a.md", tmp_path / "b.md"
        good.write_bytes(b"x" * 100)
        bad.write_bytes(b"x" * (BYTE_CAP + 1))
        assert run_cli(str(good), str(bad), str(good)).returncode == 1


class TestInodeDedup:
    def test_hardlinked_indexes_are_reported_once(self, tmp_path: Path, monkeypatch) -> None:
        """Those project dirs are symlinks onto ONE store — measured 40+ paths,
        one inode. Without the de-dup a single problem prints dozens of times and
        the reader cannot tell one index from many."""
        projects = tmp_path / ".claude" / "projects"
        real = projects / "a" / "memory"
        real.mkdir(parents=True)
        (real / "MEMORY.md").write_bytes(b"x" * 100)
        for name in ("b", "c"):
            d = projects / name / "memory"
            d.mkdir(parents=True)
            (d / "MEMORY.md").hardlink_to(real / "MEMORY.md")
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        assert len(default_indexes()) == 1

    def test_distinct_indexes_are_all_reported(self, tmp_path: Path, monkeypatch) -> None:
        """The discriminating half: a de-dup that collapses everything would pass
        the test above and hide every index but one."""
        projects = tmp_path / ".claude" / "projects"
        for name in ("a", "b", "c"):
            d = projects / name / "memory"
            d.mkdir(parents=True)
            (d / "MEMORY.md").write_bytes(b"x" * 100)
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        assert len(default_indexes()) == 3
