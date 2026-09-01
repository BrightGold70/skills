"""`resolved-model` answers from evidence or refuses — it never guesses.

With no model pinned, `exec` inherits the agent's own configuration, so this is
the only evidence of what a 5d/5e dispatch ran. A wrong answer is worse than no
answer: a model that cannot execute a tool still writes prose and returns a
well-formed `STATUS: BLOCKED` indistinguishable from a task verdict.

The two agy pins below are the ones that matter, because both were measured
against the real 620-log corpus on 2026-09-01 and both defeat the extractor as it
was written in prose: the log tears mid-line under concurrent writers, and the
newest log by mtime is a different session from the newest by name.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "h_mad_resolved_model.py"

CODEX_LOG = """\
OpenAI Codex v0.151.0
--------
workdir: /repo
model: gpt-5.6-sol
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR]
reasoning effort: high
reasoning summaries: none
session id: 01a05a82-06ec-77d0-be50-c10daf007d16
--------
user
"""

LABEL = 'model_config_manager.go:311] Propagating selected model override to backend: label="%s"\n'
# A real torn line from the corpus: a concurrent writer splices a log line into
# the middle of the quoted value, so a greedy `[^"]+` swallows it and reports it
# as the model.
TORN = ('I0828 12:57:46 model_config_manager.go:311] Propagating selected model override to '
        'backend: label="Gemin\nERROR: logging before google.Init: I0828 12:57:46.469040 247 '
        'http_helpers.go:246] URL: https://example/v1internal:fetchAvailableModels\n')


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True)


def _agy_dir(tmp_path: Path, *files: tuple[str, str, float]) -> Path:
    d = tmp_path / "agylog"
    d.mkdir()
    import os
    for name, body, mtime in files:
        p = d / name
        p.write_text(body, encoding="utf-8")
        os.utime(p, (mtime, mtime))
    return d


# --- codex ------------------------------------------------------------------


def test_codex_reads_the_resolved_model_out_of_its_session_header(tmp_path) -> None:
    log = tmp_path / "exec.log"
    log.write_text(CODEX_LOG, encoding="utf-8")
    r = run("codex", "--log", str(log))
    assert r.returncode == 0, r.stderr
    assert "model=gpt-5.6-sol" in r.stdout and "effort=high" in r.stdout
    assert "resolved=1" in r.stdout, "a log is proof of what ran"


def test_codex_without_a_log_says_configured_not_resolved(tmp_path) -> None:
    """The distinction is the whole point: a config says what WILL run."""
    cfg = tmp_path / "config.toml"
    cfg.write_text('model = "gpt-5.6-sol"\nmodel_reasoning_effort = "high"\n', encoding="utf-8")
    r = run("codex", "--config", str(cfg))
    assert r.returncode == 0, r.stderr
    assert "configured=1" in r.stdout
    assert "resolved=1" not in r.stdout, "a config is not evidence of what ran"


def test_codex_refuses_a_log_without_a_header(tmp_path) -> None:
    log = tmp_path / "exec.log"
    log.write_text("not a codex log\n" * 40, encoding="utf-8")
    r = run("codex", "--log", str(log))
    assert r.returncode == 2
    assert "UNKNOWN" in r.stderr
    assert "model=" not in r.stdout


def test_codex_refuses_a_missing_log(tmp_path) -> None:
    r = run("codex", "--log", str(tmp_path / "nope.log"))
    assert r.returncode == 2 and r.stdout.strip() == ""


# --- agy: the two measured defeats of the prose extractor --------------------


def test_a_torn_log_line_is_not_reported_as_a_model(tmp_path) -> None:
    """Measured: 8 fragments like `GeminERROR: logging before google.Init: ...`
    across 620 real logs. A greedy capture reports one of them as the model.

    Honest note: this case does NOT discriminate on its own — a greedy pattern
    finds no closing quote here either, so it refuses for a different reason and
    this pin stays green. Its discriminating sibling is the next test, where a
    good label follows the tear and a greedy capture swallows it. Kept because it
    is the shape a reader will look for, and mutation coverage lives next door."""
    d = _agy_dir(tmp_path, ("cli-1.log", TORN, 1000.0))
    r = run("agy", "--agy-log-dir", str(d))
    assert r.returncode == 2, r.stdout
    assert "torn" in r.stderr
    assert "ERROR" not in r.stdout


def test_a_torn_line_does_not_hide_a_good_one(tmp_path) -> None:
    d = _agy_dir(tmp_path, ("cli-1.log", TORN + LABEL % "Gemini 3.1 Pro (High)", 1000.0))
    r = run("agy", "--agy-log-dir", str(d))
    assert r.returncode == 0, r.stderr
    assert "model=Gemini 3.1 Pro (High)" in r.stdout


def test_two_recent_logs_disagreeing_refuses_instead_of_picking(tmp_path) -> None:
    """Measured: several agy processes log concurrently — a long-lived pane and a
    short `exec agy` run — so the newest file by mtime and by name were DIFFERENT
    sessions. When they disagree about the model, no log can be attributed."""
    d = _agy_dir(tmp_path,
                 ("cli-newer.log", LABEL % "Gemini 3.1 Pro (Low)", 2000.0),
                 ("cli-older.log", LABEL % "Gemini 3.1 Pro (High)", 1999.0))
    r = run("agy", "--agy-log-dir", str(d))
    assert r.returncode == 2, r.stdout
    assert "ambiguous" in r.stderr
    assert "model=" not in r.stdout


def test_agreement_between_the_two_newest_is_answerable(tmp_path) -> None:
    d = _agy_dir(tmp_path,
                 ("cli-newer.log", LABEL % "Gemini 3.1 Pro (High)", 2000.0),
                 ("cli-older.log", LABEL % "Gemini 3.1 Pro (High)", 1999.0))
    r = run("agy", "--agy-log-dir", str(d))
    assert r.returncode == 0, r.stderr
    assert "model=Gemini 3.1 Pro (High)" in r.stdout
    assert "cli-newer.log" in r.stdout, "the file that answered must be named"


def test_agy_refuses_a_stream_json_dispatch_log(tmp_path) -> None:
    """`exec agy --log` is stream-json and carries no model field. Falling back to
    the cli dir would answer about a different process while looking like an
    answer about this dispatch."""
    log = tmp_path / "rev.log"
    log.write_text('{"type":"result"}\n', encoding="utf-8")
    r = run("agy", "--log", str(log))
    assert r.returncode == 2
    assert "stream-json" in r.stderr and "model=" not in r.stdout


def test_an_empty_log_dir_refuses(tmp_path) -> None:
    d = tmp_path / "agylog"; d.mkdir()
    r = run("agy", "--agy-log-dir", str(d))
    assert r.returncode == 2 and r.stdout.strip() == ""
