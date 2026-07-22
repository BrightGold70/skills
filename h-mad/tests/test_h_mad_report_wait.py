"""Tests for the standalone report-file poller (monitoring H3).

The script is the wrapper-independent half of `hmad-dispatch report-wait`: it can
be invoked directly with `python3 h_mad_report_wait.py <path> …`, so the
coordinator can poll for a dropped report WITHOUT re-parsing hmad-dispatch.sh
while a dispatched implementer is mid-edit on that wrapper.
"""
import subprocess
import sys
from pathlib import Path

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
