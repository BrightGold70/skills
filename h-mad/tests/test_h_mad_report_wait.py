"""Tests for the standalone report-file poller (monitoring H3).

The script is the wrapper-independent half of `hmad-dispatch report-wait`: it can
be invoked directly with `python3 h_mad_report_wait.py <path> …`, so the
coordinator can poll for a dropped report WITHOUT re-parsing hmad-dispatch.sh
while a dispatched implementer is mid-edit on that wrapper.
"""
import io
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from h_mad_report_wait import report_wait  # noqa: E402

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "h_mad_report_wait.py"


def run(args):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True)


def test_emits_file_when_marker_present(tmp_path):
    report = tmp_path / "audit.md"
    report.write_text("## Must-fix\nNone\n")
    (tmp_path / "audit.md.done").write_text("")
    r = run([str(report), "--timeout", "2", "--interval", "0"])
    assert r.returncode == 0
    assert "## Must-fix" in r.stdout


def test_times_out_without_marker(tmp_path):
    report = tmp_path / "audit.md"
    report.write_text("partial...")
    r = run([str(report), "--timeout", "0", "--interval", "0"])
    assert r.returncode == 1
    assert "timed out" in r.stderr


def test_ignores_marker_when_report_empty(tmp_path):
    # Race guard: .done landed before content → empty file must NOT be read.
    report = tmp_path / "audit.md"
    report.write_text("")
    (tmp_path / "audit.md.done").write_text("")
    r = run([str(report), "--timeout", "0", "--interval", "0"])
    assert r.returncode == 1


def test_rejects_flag_in_path_slot():
    # `report-wait --timeout 600` with the path omitted must fail fast, not poll
    # for a file literally named "--timeout".
    r = run(["--timeout", "600"])
    assert r.returncode == 2
    assert "looks like a flag" in r.stderr


def test_missing_path_arg():
    r = run([])
    assert r.returncode == 2


def test_wrapper_independent_no_hmad_dispatch_reference():
    # The whole point of H3: this poller must not depend on hmad-dispatch.sh, so
    # a half-saved wrapper can't break a poll. Guard that the script never shells
    # out at all (no subprocess/os.system/os.popen) — it polls the filesystem
    # directly with stdlib only.
    src = SCRIPT.read_text()
    assert "subprocess" not in src
    assert "os.system" not in src and "os.popen" not in src
    assert "import os" in src and "import sys" in src  # stdlib only


class TestNoDoneMarker:
    """The `exec --out` case: a file that IS its own completion signal.

    `report-wait` exists for an agent that writes a report and then drops
    `<path>.done`, and the marker is the whole point — it is what makes a
    half-written report unreadable. `exec --out` has no marker: the file is copied
    into place once the agent has finished, so its appearance is the signal.

    Waiting on that was written ~25 times in one session as
    `for i in 1 2 3; do hmad-dispatch run --timeout 110 -- sleep 105; done` plus a
    `test -f <out>` — a sleep ladder whose arithmetic, when wrong, silently wastes
    wall-clock and whose purpose is invisible to the next reader.

    `--no-done-marker` is opt-IN, and deliberately so: defaulting to
    existence-as-completion would silently weaken every existing `report-wait`
    caller, turning the marker contract off for people who never asked.
    """

    def test_a_file_without_a_marker_is_returned(self, tmp_path):
        path = tmp_path / "out.txt"
        path.write_text("VERDICT: ok\n", encoding="utf-8")
        out, err = io.StringIO(), io.StringIO()

        rc = report_wait(str(path), timeout=1, interval=0, out=out, err=err,
                         require_marker=False)

        assert rc == 0
        assert out.getvalue() == "VERDICT: ok\n"

    def test_an_empty_file_is_still_not_complete(self, tmp_path):
        """Non-emptiness is the only integrity check left once the marker is gone,
        so it must not be dropped with it."""
        path = tmp_path / "out.txt"
        path.write_text("", encoding="utf-8")
        out, err = io.StringIO(), io.StringIO()

        rc = report_wait(str(path), timeout=0, interval=0, out=out, err=err,
                         require_marker=False)

        assert rc == 1
        assert out.getvalue() == ""

    def test_the_default_still_requires_the_marker(self, tmp_path):
        """The regression that would matter most: existing callers rely on the
        marker to keep a half-written report unreadable."""
        path = tmp_path / "out.txt"
        path.write_text("half a rep", encoding="utf-8")
        out, err = io.StringIO(), io.StringIO()

        rc = report_wait(str(path), timeout=0, interval=0, out=out, err=err)

        assert rc == 1, "a file with no .done marker must not be read by default"
        assert out.getvalue() == ""

    def test_the_timeout_message_names_the_right_condition(self, tmp_path):
        """With no marker there is no marker to report missing; saying so would
        send the reader looking for a file that was never part of the contract."""
        path = tmp_path / "out.txt"
        out, err = io.StringIO(), io.StringIO()

        report_wait(str(path), timeout=0, interval=0, out=out, err=err,
                    require_marker=False)

        assert ".done" not in err.getvalue(), err.getvalue()

    def test_cli_exposes_the_flag(self, tmp_path):
        path = tmp_path / "out.txt"
        path.write_text("VERDICT: ok\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(path), "--timeout", "1",
             "--interval", "0", "--no-done-marker"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        assert "VERDICT: ok" in result.stdout
