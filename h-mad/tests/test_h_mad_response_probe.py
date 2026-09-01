"""A probe that leaks panes is worse than no probe.

Leaked panes pollute the pane pool and the next `pin-agents` run, so cleanup is
the property under test here — not the tabulating, which is trivial. The three
escape routes a `trap` alone does not cover each get a pin: an exception, a
signal, and a create that never reported a handle.
"""

from __future__ import annotations

import json
import os
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "h_mad_response_probe.py"


def _sh(path: Path, body: str) -> str:
    path.write_text("#!/bin/sh\n" + body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return str(path)


def creator(tmp_path: Path, body: str) -> str:
    return _sh(tmp_path / "create", body)


def closer(tmp_path: Path, rc: int = 0) -> str:
    return _sh(tmp_path / "close", f'echo "$1" >> "{tmp_path}/closed.txt"\nexit {rc}\n')


def closed_handles(tmp_path: Path) -> list[str]:
    p = tmp_path / "closed.txt"
    return p.read_text(encoding="utf-8").split() if p.is_file() else []


def run(*args: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True, timeout=timeout)


OK = '''echo '{"result":{"terminal":{"handle":"h'"$1"'","paneKey":"k'"$1"'"}}}'\n'''


def test_it_measures_presence_and_closes_every_pane(tmp_path) -> None:
    c = creator(tmp_path, OK)
    r = run("--journal", str(tmp_path / "j.jsonl"), "--create", f"{c} {{i}}",
            "--field", "result.terminal.paneKey", "--close", f"{closer(tmp_path)} {{handle}}",
            "--n", "4")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "present=4/4" in r.stdout
    assert sorted(closed_handles(tmp_path)) == ["h0", "h1", "h2", "h3"]


def test_a_present_but_null_field_counts_as_absent(tmp_path) -> None:
    """The whole point of the measurement is presence. `"paneKey": null` is the
    shape the real omission takes, and reading it as present inverts the finding."""
    c = creator(tmp_path, '''echo '{"result":{"terminal":{"handle":"h'"$1"'","paneKey":null}}}'\n''')
    r = run("--journal", str(tmp_path / "j.jsonl"), "--create", f"{c} {{i}}",
            "--field", "result.terminal.paneKey", "--close", f"{closer(tmp_path)} {{handle}}",
            "--n", "3")
    assert "absent=3/3" in r.stdout, r.stdout


def test_a_create_that_fails_is_a_POSSIBLE_leak_not_a_clean_run(tmp_path) -> None:
    """The window a trap cannot close: the pane may exist, and this process never
    learned its handle. Reporting it is the only honest option."""
    c = creator(tmp_path, "exit 1\n")
    r = run("--journal", str(tmp_path / "j.jsonl"), "--create", f"{c} {{i}}",
            "--field", "result.terminal.paneKey", "--close", f"{closer(tmp_path)} {{handle}}",
            "--n", "2")
    assert "possible_leaks=2" in r.stdout, r.stdout
    assert r.returncode == 2
    assert "NOT CLEAN" in r.stderr


def test_a_close_that_fails_is_reported_and_the_run_is_not_clean(tmp_path) -> None:
    c = creator(tmp_path, OK)
    r = run("--journal", str(tmp_path / "j.jsonl"), "--create", f"{c} {{i}}",
            "--field", "result.terminal.paneKey",
            "--close", f"{closer(tmp_path, rc=1)} {{handle}}", "--n", "2")
    assert "failed=2" in r.stdout and r.returncode == 2
    assert "--resume" in r.stderr, "the recovery command must be named"


def test_resume_closes_what_an_earlier_run_left_open(tmp_path) -> None:
    j = tmp_path / "j.jsonl"
    j.write_text(json.dumps({"i": 0, "state": "creating"}) + "\n"
                 + json.dumps({"i": 0, "state": "created", "handle": "h0"}) + "\n",
                 encoding="utf-8")
    r = run("--journal", str(j), "--resume", "--close", f"{closer(tmp_path)} {{handle}}")
    assert r.returncode == 0, r.stdout
    assert closed_handles(tmp_path) == ["h0"]
    assert "closed=1" in r.stdout


def test_resume_is_idempotent(tmp_path) -> None:
    """A journal that records its own closes means a second resume is a no-op
    rather than a second close of a handle someone else may now own."""
    j = tmp_path / "j.jsonl"
    j.write_text(json.dumps({"i": 0, "state": "creating"}) + "\n"
                 + json.dumps({"i": 0, "state": "created", "handle": "h0"}) + "\n",
                 encoding="utf-8")
    cl = f"{closer(tmp_path)} {{handle}}"
    run("--journal", str(j), "--resume", "--close", cl)
    run("--journal", str(j), "--resume", "--close", cl)
    assert closed_handles(tmp_path) == ["h0"], "the second resume closed it again"


def test_a_signal_still_closes_what_was_created(tmp_path) -> None:
    """SIGTERM mid-run. A `finally` only fires if the signal becomes an exception,
    which is why the handlers are installed rather than left to the default."""
    c = creator(tmp_path, 'if [ "$1" = "1" ]; then sleep 10; fi\n' + OK)
    p = subprocess.Popen(
        [sys.executable, str(SCRIPT), "--journal", str(tmp_path / "j.jsonl"),
         "--create", f"{c} {{i}}", "--field", "result.terminal.paneKey",
         "--close", f"{closer(tmp_path)} {{handle}}", "--n", "3"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    deadline = time.time() + 10
    while time.time() < deadline and "h0" not in json.dumps(
            (tmp_path / "j.jsonl").read_text(encoding="utf-8") if (tmp_path / "j.jsonl").is_file() else ""):
        time.sleep(0.05)
    p.send_signal(signal.SIGTERM)
    p.communicate(timeout=30)
    assert "h0" in closed_handles(tmp_path), (
        "the pane created before the signal was left open: " + str(closed_handles(tmp_path)))
