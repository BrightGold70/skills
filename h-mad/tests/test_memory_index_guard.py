"""`memory-index-guard.sh` — the hook that makes the index check RUN by itself.

The check existed and was correct. It ran only when somebody read the step that
documents it in `handoff/references/auto-memories.md`, so the index sat at 100%
of its cap for a day with two entries already invisible and nothing said so. A
documented rule is not an enforced one.

**Calibrated against indexes that genuinely breach, through the REAL checker.**
Every fixture below is a real file of the right size and the verdict comes from
`h_mad_check_memory_index.py` itself, reached through a one-line shim that appends
the fixture path. A stub emitting the four verdict strings would have tested this
module's `case` arms against text this repo wrote twice — which is how a detector
ends up calibrated to its own expectations rather than to the tool. The one thing
stubbed is WHICH index is looked at, because the hook deliberately takes no path.

The contract that decides every branch: **it exits 0 on every path.** A block
would have to be right about someone's memory write, and being wrong costs a
refused write the user cannot complete; being wrong the other way costs a line of
text. Both hook events place stdout into the session as context, so an advisory
is READ and not merely logged — the property the documented step never had.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
HOOK = REPO / "h-mad" / "hooks" / "memory-index-guard.sh"
CHECKER = REPO / "h-mad" / "scripts" / "h_mad_check_memory_index.py"

BYTE_CAP = 25000
WARN_AT = int(BYTE_CAP * 0.8)


def _index(path: Path, size: int, lines: int = 150) -> Path:
    """A real MEMORY.md of exactly `size` bytes across exactly `lines` lines.

    BOTH dimensions are controlled, and that is not fussiness. The checker scores
    bytes and lines and the WORSE one binds, so a fixture built only to a byte
    target lands wherever its row length puts it on lines: the first draft used
    short rows and produced 479 lines against a cap of 200, which the checker
    correctly called OVER at `frac=240%` while the test was asking for WARN. The
    fixture tripped the very property the checker's mutation spec calls its
    load-bearing row.

    ASCII on purpose too — the real index uses an em dash, and slicing a
    multi-byte row by CHARACTER to hit a BYTE target overshoots (25900 asked,
    26630 written).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    head = "# Memory Index\n"
    per = (size - len(head)) // lines
    assert per > 40, "rows too short to look like an index; raise size or drop lines"
    row = "- [An entry](project_an_entry.md) - hook "
    body = head + "".join(
        (row + "x" * per)[: per - 1] + "\n" for _ in range(lines)
    )
    body += "y" * (size - len(body))
    path.write_text(body, encoding="utf-8")
    assert path.stat().st_size == size, "fixture is not the size it claims"
    return path


def _shim(tmp_path: Path, target: Path) -> Path:
    """A checker that IS the real checker, pinned to one index.

    Written as a PYTHON file on purpose. The hook runs the checker as
    `"$PY" "$CHECKER"` and uses that same `$PY` to parse the PreToolUse JSON, so
    a shell shim would have silently broken the path filter in every test that
    used one — a test harness that disables the thing under test. The shim adds
    exactly one fact (which index to look at); the verdict is the real checker's.
    """
    s = tmp_path / "checker_shim.py"
    s.write_text(
        "import runpy, sys\n"
        f"sys.argv = [{str(CHECKER)!r}] + sys.argv[1:] + [{str(target)!r}]\n"
        f"runpy.run_path({str(CHECKER)!r}, run_name='__main__')\n",
        encoding="utf-8",
    )
    return s


def _run(checker: Path, *args: str, stdin: str = "") -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["HMAD_MEMORY_INDEX_CHECKER"] = str(checker)
    env["HMAD_PYTHON"] = sys.executable
    return subprocess.run(
        ["bash", str(HOOK), *args],
        input=stdin, capture_output=True, text=True, env=env,
    )


def _write_payload(path: Path) -> str:
    return json.dumps({"tool_input": {"file_path": str(path)}})


class TestItFiresOnAnIndexThatBreaches:
    """The half a clean-index smoke test cannot reach."""

    def test_OVER_is_reported_and_names_what_is_invisible(self, tmp_path: Path) -> None:
        idx = _index(tmp_path / "m" / "MEMORY.md", BYTE_CAP + 900)
        out = _run(_shim(tmp_path, idx), "--session-start")
        assert out.returncode == 0, out.stderr
        assert "OVER CAP" in out.stdout, out.stdout
        assert "invisible" in out.stdout
        # The dropped TEXT, not just a count: `dropped=900` is a number, the
        # entries it is deleting are the finding.
        assert "An entry" in out.stdout

    def test_WARN_is_reported_while_compaction_is_still_cheap(self, tmp_path: Path) -> None:
        idx = _index(tmp_path / "m" / "MEMORY.md", WARN_AT + 500)
        out = _run(_shim(tmp_path, idx), "--session-start")
        assert out.returncode == 0
        assert "WARN" in out.stdout, out.stdout
        assert "OVER CAP" not in out.stdout

    def test_UNREADABLE_is_not_reported_as_clean(self, tmp_path: Path) -> None:
        """`I could not check` and `the check said OK` take opposite branches."""
        missing = tmp_path / "m" / "gone" / "MEMORY.md"
        missing.parent.mkdir(parents=True, exist_ok=True)
        out = _run(_shim(tmp_path, missing), "--session-start")
        assert out.returncode == 0
        assert "UNREADABLE" in out.stdout, out.stdout
        assert "NOT a\nclean result" in out.stdout or "NOT a" in out.stdout

    def test_a_healthy_index_says_NOTHING(self, tmp_path: Path) -> None:
        """Every session start pays for this line, so it must not exist."""
        idx = _index(tmp_path / "m" / "MEMORY.md", 5_000, lines=40)
        out = _run(_shim(tmp_path, idx), "--session-start")
        assert out.returncode == 0
        assert out.stdout.strip() == "", out.stdout


class TestThePreToolUsePathFilter:
    def test_it_fires_on_the_index_itself(self, tmp_path: Path) -> None:
        idx = _index(tmp_path / "m" / "MEMORY.md", BYTE_CAP + 900)
        out = _run(_shim(tmp_path, idx), stdin=_write_payload(
            Path("/anywhere/projects/p/memory/MEMORY.md")))
        assert "OVER CAP" in out.stdout, out.stdout

    def test_a_TOPIC_file_write_is_ignored(self, tmp_path: Path) -> None:
        """Topic files are uncapped; firing on them is noise on the commonest
        memory write there is, and noise is what gets a hook disabled."""
        idx = _index(tmp_path / "m" / "MEMORY.md", BYTE_CAP + 900)
        out = _run(_shim(tmp_path, idx), stdin=_write_payload(
            Path("/anywhere/projects/p/memory/project_thing.md")))
        assert out.stdout.strip() == "", out.stdout

    def test_an_unrelated_write_is_ignored(self, tmp_path: Path) -> None:
        idx = _index(tmp_path / "m" / "MEMORY.md", BYTE_CAP + 900)
        out = _run(_shim(tmp_path, idx), stdin=_write_payload(Path("/src/app.py")))
        assert out.stdout.strip() == ""

    def test_unparseable_stdin_does_not_fire_and_does_not_crash(
        self, tmp_path: Path
    ) -> None:
        idx = _index(tmp_path / "m" / "MEMORY.md", BYTE_CAP + 900)
        out = _run(_shim(tmp_path, idx), stdin="{not json")
        assert out.returncode == 0
        assert out.stdout.strip() == ""


class TestItNeverBlocks:
    """A hook that can fail the session is a hook people disable."""

    @pytest.mark.parametrize(
        "size,lines",
        [(5_000, 40), (WARN_AT + 500, 150), (BYTE_CAP + 900, 150)],
        ids=["ok", "warn", "over"],
    )
    def test_every_verdict_still_exits_zero(
        self, tmp_path: Path, size: int, lines: int
    ) -> None:
        idx = _index(tmp_path / "m" / "MEMORY.md", size, lines=lines)
        assert _run(_shim(tmp_path, idx), "--session-start").returncode == 0

    def test_a_missing_checker_is_silent_rather_than_noisy(self, tmp_path: Path) -> None:
        """Printing 'I could not check' into EVERY session start would train the
        reader to ignore this hook, which disarms the other paths too."""
        absent = tmp_path / "nope"
        out = _run(absent, "--session-start")
        assert out.returncode == 0
        assert out.stdout.strip() == ""

    def test_an_unrecognised_verdict_is_surfaced_not_swallowed(
        self, tmp_path: Path
    ) -> None:
        """A renamed token is how a guard goes quiet while appearing to run."""
        weird = tmp_path / "weird_checker.py"
        weird.write_text("print('SPLENDID /x/MEMORY.md all good')\n", encoding="utf-8")
        out = _run(weird, "--session-start")
        assert out.returncode == 0
        assert "unrecognised verdict" in out.stdout, out.stdout


class TestTheHookIsInstallable:
    def test_it_is_executable(self) -> None:
        assert HOOK.is_file() and HOOK.stat().st_mode & 0o111

    def test_it_documents_both_events_it_is_wired_to(self) -> None:
        body = HOOK.read_text(encoding="utf-8")
        assert "--session-start" in body
        assert "PreToolUse" in body and "SessionStart" in body

    def test_it_states_why_it_advises_rather_than_blocks(self) -> None:
        """An unexplained exception to enforcement is what a later reader deletes."""
        body = HOOK.read_text(encoding="utf-8")
        assert "ADVISORY, never a block" in body
