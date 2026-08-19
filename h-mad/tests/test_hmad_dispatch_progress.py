"""Headless `exec` must be WATCHABLE while it runs.

The defect these guard: `exec` is h-mad's default dispatch path because the pane
path could not resolve agy/codex surfaces reliably — but headless traded that
away for total blindness. A foreground `exec` prints nothing until it exits, so
a 15-minute audit was a blank screen indistinguishable from a wedged one.

The two backends were NOT equally blind, and the docs claimed they were:
  * codex wrote its transcript to `--log` live (measured on a real run: the file
    grew 811 -> 1446 bytes mid-flight).
  * agy captured `--print` to a private temp file and appended to `--log` only
    AFTER the process exited, so agy's `--log` held zero bytes for the entire
    run and `tail -f` on it showed nothing until the end.

So these tests come in two halves: agy's transcript must now stream, and both
backends must be observable through a bounded, non-blocking `progress` verb —
because `tail -f` never returns and an orchestrating agent cannot run it.
"""

import json
import os
import subprocess
import time
from pathlib import Path

import pytest

WRAPPER = Path(__file__).resolve().parent.parent / "scripts" / "hmad-dispatch.sh"
STUBS = Path(__file__).resolve().parent / "stubs"

jq_required = pytest.mark.skipif(
    subprocess.run(["which", "jq"], capture_output=True).returncode != 0,
    reason="progress digest and NDJSON extraction need jq",
)


def _bindir(tmp_path, names):
    b = tmp_path / "bin"
    b.mkdir(exist_ok=True)
    for n in names:
        dst = b / n
        dst.write_text((STUBS / n).read_text())
        dst.chmod(0o755)
    return b


def _env(bindir, **extra):
    env = dict(os.environ)
    env["PATH"] = f"{bindir}:{env['PATH']}"
    env["HMAD_SUBSTRATE"] = "none"
    env.update({k: str(v) for k, v in extra.items()})
    return env


def _prompt(tmp_path, text="do the work"):
    p = tmp_path / "prompt.md"
    p.write_text(text)
    return p


def run(args, env=None, **kw):
    return subprocess.run(
        ["bash", str(WRAPPER), *args],
        capture_output=True, text=True, env=env, timeout=120, **kw,
    )


# --------------------------------------------------------------------------
# agy transcript liveness
# --------------------------------------------------------------------------

def test_agy_exec_requests_the_streaming_output_format(tmp_path):
    """The live channel exists only because this flag is sent. Pin it."""
    b = _bindir(tmp_path, ["agy"])
    cap = tmp_path / "cap.txt"
    r = run(["exec", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path)],
            env=_env(b, HMAD_STUB_CAPTURE=str(cap)))
    assert r.returncode == 0, r.stderr
    assert "--output-format stream-json" in cap.read_text()


def test_agy_streaming_flag_precedes_print_and_prompt_stays_last(tmp_path):
    """`--print` eats the NEXT token as its prompt.

    A `--output-format` placed after `--print` would be consumed AS the prompt
    and the real prompt silently dropped — the exact failure the wrapper's own
    comment records from a live run (agy just greeted). Order is load-bearing,
    so assert the order, not merely the presence.
    """
    b = _bindir(tmp_path, ["agy"])
    cap = tmp_path / "cap.txt"
    r = run(["exec", "agy", str(_prompt(tmp_path, "PROMPT-BODY")), "--cd", str(tmp_path)],
            env=_env(b, HMAD_STUB_CAPTURE=str(cap)))
    assert r.returncode == 0, r.stderr
    argv = cap.read_text()
    assert argv.index("--output-format stream-json") < argv.index("--print")
    # The prompt argument is the body plus the dispatch boundary the wrapper
    # appends (J23), so it is the tail of argv rather than a bare equality — but
    # it must still be what FOLLOWS --print, with no flag wedged between.
    after_print = argv.split("--print", 1)[1]
    assert after_print.lstrip().startswith("PROMPT-BODY")
    assert "--" not in after_print.split("PROMPT-BODY", 1)[0]


@jq_required
def test_agy_log_is_ndjson_and_carries_step_events(tmp_path):
    """The log must hold the STEP stream, not just the final answer.

    An operator watching a dispatch needs to see which tool is running now; a
    log that only ever gains the final response tells them nothing until the
    moment they no longer need it.
    """
    b = _bindir(tmp_path, ["agy"])
    log = tmp_path / "run.log"
    r = run(["exec", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--log", str(log)],
            env=_env(b, HMAD_STUB_AGY_RESP="VERDICT: COMPLIANT"))
    assert r.returncode == 0, r.stderr
    events = [json.loads(l) for l in log.read_text().splitlines()
              if l.startswith("{")]
    kinds = [e["event"] for e in events]
    assert "init" in kinds
    assert "result" in kinds
    tools = [e for e in events
             if e["event"] == "step_update"
             and e["step_update"].get("step_type") == "tool"]
    assert tools, "no tool step events in the transcript"


@jq_required
def test_agy_transcript_is_written_DURING_the_run_not_after(tmp_path):
    """THE regression under repair.

    Before the fix agy's --log was empty for the whole run and filled only at
    exit. Sample the file mid-flight and require content: a `tail -f` that shows
    nothing until completion is the operator-visible bug.
    """
    b = _bindir(tmp_path, ["agy"])
    log = tmp_path / "run.log"
    proc = subprocess.Popen(
        ["bash", str(WRAPPER), "exec", "agy", str(_prompt(tmp_path)),
         "--cd", str(tmp_path), "--log", str(log)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        env=_env(b, HMAD_STUB_AGY_RESP="VERDICT: COMPLIANT",
                 HMAD_STUB_AGY_SLEEP="6"),
    )
    mid = ""
    try:
        deadline = time.time() + 5
        while time.time() < deadline:
            if log.exists() and log.stat().st_size > 0:
                mid = log.read_text()
                break
            time.sleep(0.2)
    finally:
        proc.wait(timeout=60)
    assert proc.returncode == 0
    assert mid, "transcript was still empty while the agent was running"
    assert '"event":"init"' in mid


@jq_required
def test_agy_verdict_contract_is_unchanged_by_the_format_switch(tmp_path):
    """stdout and --out stay the RESPONSE TEXT. Only the log's format moved.

    Everything downstream — h_mad_extract_verdict.py, the --out templating, the
    J29 fingerprint — reads those two channels. If the NDJSON leaked into either,
    the whole verdict path breaks silently.
    """
    b = _bindir(tmp_path, ["agy"])
    out = tmp_path / "v.txt"
    log = tmp_path / "run.log"
    r = run(["exec", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--out", str(out), "--log", str(log)],
            env=_env(b, HMAD_STUB_AGY_RESP="ASSESSMENT: READY_TO_MERGE"))
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "ASSESSMENT: READY_TO_MERGE"
    assert out.read_text().strip() == "ASSESSMENT: READY_TO_MERGE"
    assert '"event"' not in r.stdout
    assert '"event"' not in out.read_text()


@jq_required
def test_multi_line_response_survives_extraction_whole(tmp_path):
    """A verdict is line ONE of a report; a truncating extractor loses it.

    Caught live during development: a per-line jq read emitted the response as
    separate lines and a `tail -1` kept only the last, turning
    "ASSESSMENT: READY_TO_MERGE\\nSome detail" into "Some detail" — an
    unextractable verdict from a run that passed.
    """
    b = _bindir(tmp_path, ["agy"])
    out = tmp_path / "v.txt"
    body = "ASSESSMENT: READY_TO_MERGE\nDetail line two.\nDetail line three."
    r = run(["exec", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--out", str(out)],
            env=_env(b, HMAD_STUB_AGY_RESP=body))
    assert r.returncode == 0, r.stderr
    assert out.read_text().strip() == body
    assert r.stdout.splitlines()[0] == "ASSESSMENT: READY_TO_MERGE"


@jq_required
def test_a_prior_dispatchs_result_in_a_reused_log_cannot_be_read_as_this_ones(tmp_path):
    """Scope, mutually discriminated.

    failure-recovery's no_verdict remedy re-dispatches to the SAME templated
    paths, so a reused --log routinely holds a previous run's stream. If this
    run produces no verdict, the previous run's `result` must not be promoted
    into --out as though it were the answer.
    """
    b = _bindir(tmp_path, ["agy"])
    log = tmp_path / "run.log"
    log.write_text(json.dumps({
        "event": "result",
        "result": {"status": "OK", "response": "ASSESSMENT: STALE_FROM_PRIOR_RUN"},
    }) + "\n")
    out = tmp_path / "v.txt"
    r = run(["exec", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--out", str(out), "--log", str(log)],
            env=_env(b, HMAD_STUB_AGY_RESP=""))
    assert r.returncode == 3, r.stderr
    assert "STALE_FROM_PRIOR_RUN" not in r.stdout
    assert not out.exists() or "STALE_FROM_PRIOR_RUN" not in out.read_text()
    # ...and the prior bytes are still there, untouched.
    assert "STALE_FROM_PRIOR_RUN" in log.read_text()


# --------------------------------------------------------------------------
# the `progress` verb
# --------------------------------------------------------------------------

@jq_required
def test_progress_digests_an_agy_stream_one_line_per_event(tmp_path):
    b = _bindir(tmp_path, ["agy"])
    log = tmp_path / "run.log"
    run(["exec", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--log", str(log)],
        env=_env(b, HMAD_STUB_AGY_RESP="VERDICT: COMPLIANT"))
    r = run(["progress", str(log)])
    assert r.returncode == 0, r.stderr
    assert "format: agy-ndjson" in r.stdout
    assert "tool run_command" in r.stdout
    assert "RESULT status=OK" in r.stdout
    # the digest is a DIGEST: no raw NDJSON leaks through
    assert '{"event"' not in r.stdout


def test_progress_reports_liveness_from_transcript_age(tmp_path):
    """"Is it alive?" is the question a watcher actually has.

    A live agent keeps touching its transcript; a dead one does not. Age since
    last write is what separates "thinking hard" from "died", so it is reported
    before any content.
    """
    log = tmp_path / "run.log"
    log.write_text('{"event":"init","init":{"cwd":"/x"}}\n')
    fresh = run(["progress", str(log)])
    assert fresh.returncode == 0
    assert "LIVE" in fresh.stdout

    old = time.time() - 9999
    os.utime(log, (old, old))
    stale = run(["progress", str(log)])
    assert stale.returncode == 0
    assert "STALE" in stale.stdout


def test_progress_returns_immediately_and_is_bounded(tmp_path):
    """`tail -f` is why this verb exists: it never returns, so an orchestrating
    agent cannot run it — it burns the whole shell timeout and yields nothing.
    `progress` must be pollable, which means fast and small."""
    log = tmp_path / "run.log"
    log.write_text("".join(
        json.dumps({"event": "step_update", "step_update": {
            "step_type": "tool", "state": "DONE", "tool_name": f"t{i}",
            "duration_seconds": 1}}) + "\n" for i in range(500)))
    t0 = time.time()
    r = run(["progress", str(log), "--lines", "10"])
    assert r.returncode == 0, r.stderr
    assert time.time() - t0 < 20
    assert len(r.stdout.splitlines()) <= 15


def test_progress_distinguishes_missing_from_empty(tmp_path):
    """"never started" and "started, silent so far" demand different actions —
    re-dispatch versus wait. Collapsing them is how a watcher re-dispatches a
    run that was working fine."""
    missing = run(["progress", str(tmp_path / "nope.log")])
    assert missing.returncode == 0
    assert "format: missing" in missing.stdout

    empty = tmp_path / "e.log"
    empty.write_text("")
    r = run(["progress", str(empty)])
    assert r.returncode == 0
    assert "format: empty" in r.stdout

    # The header codes are for a caller grepping; the BODY is what a human reads,
    # and it has to say what to DO — surfaced by a mutation that collapsed the two
    # body messages while leaving both headers intact, which no assertion caught.
    assert "not started" in missing.stdout or "--log not passed" in missing.stdout
    assert "nothing emitted yet" in r.stdout


def test_progress_on_a_codex_transcript_drops_framework_noise(tmp_path):
    """codex interleaves `hook:` bookkeeping ~2:1 with real events. Unfiltered,
    a 25-line window shows mostly hooks."""
    log = tmp_path / "cx.log"
    log.write_text(
        # A real codex transcript always opens with the echoed prompt and our
        # boundary; the digest renders only what follows it.
        "user\nthe prompt\n===HMAD-DISPATCH-BOUNDARY===\n"
        "hook: PreToolUse\nhook: PreToolUse Completed\n"
        "exec\n/bin/zsh -lc 'pytest -q'\nhook: PostToolUse\n succeeded in 12ms:\n"
    )
    r = run(["progress", str(log)])
    assert r.returncode == 0, r.stderr
    assert "format: codex-text" in r.stdout
    assert "pytest -q" in r.stdout
    assert "hook: " not in r.stdout


def test_progress_on_codex_never_shows_the_echoed_prompt_as_agent_output(tmp_path):
    """J23, by a new route.

    `codex exec -` echoes its stdin, and a dispatch prompt lists its legal STATUS
    values one per line. Measured live: a codex progress poll 14s into a 45s run
    showed `STATUS: CLEAN` — our own contract block, before the agent had run a
    single command. A watcher reading that as an arrived verdict is exactly the
    misreading `_verdict_after_boundary` exists to prevent, and a progress view
    that reintroduces it is worse than none: it fabricates confidence.
    """
    log = tmp_path / "cx.log"
    log.write_text(
        "user\nReply with one of:\nSTATUS: CLEAN\nSTATUS: NEEDS_CONTEXT\n"
        "===HMAD-DISPATCH-BOUNDARY===\n"
        "exec\n/bin/zsh -lc 'pytest -q'\n succeeded in 12ms:\n"
    )
    r = run(["progress", str(log)])
    assert r.returncode == 0, r.stderr
    assert "STATUS: CLEAN" not in r.stdout
    assert "STATUS: NEEDS_CONTEXT" not in r.stdout
    assert "pytest -q" in r.stdout


def test_progress_says_so_while_the_codex_prompt_is_still_echoing(tmp_path):
    """Before the boundary lands, every byte in the file is OURS. Showing it back
    would present the prompt as though it were progress."""
    log = tmp_path / "cx.log"
    log.write_text("user\nReply with one of:\nSTATUS: CLEAN\n")
    r = run(["progress", str(log)])
    assert r.returncode == 0, r.stderr
    assert "STATUS: CLEAN" not in r.stdout
    assert "still echoing" in r.stdout


def test_progress_reports_pid_state_when_given_one(tmp_path):
    log = tmp_path / "run.log"
    log.write_text('{"event":"init","init":{"cwd":"/x"}}\n')
    r = run(["progress", str(log), "--pid", "999999"])
    assert r.returncode == 0, r.stderr
    assert "exited" in r.stdout


def test_progress_never_branches_on_exit_code(tmp_path):
    """`progress` REPORTS liveness; it does not gate.

    A non-zero exit would invite `progress ... && continue`, which is the
    `$?`-branching habit the audit-gate signal discipline forbids. Every
    observable state exits 0 so the caller has to read the line.
    """
    missing = run(["progress", str(tmp_path / "nope.log")])
    empty = tmp_path / "e.log"
    empty.write_text("")
    stale_log = tmp_path / "s.log"
    stale_log.write_text('{"event":"init","init":{"cwd":"/x"}}\n')
    old = time.time() - 9999
    os.utime(stale_log, (old, old))
    for r in (missing, run(["progress", str(empty)]), run(["progress", str(stale_log)])):
        assert r.returncode == 0, r.stdout + r.stderr


def test_progress_requires_a_logfile(tmp_path):
    r = run(["progress"])
    assert r.returncode != 0


@jq_required
def test_heartbeat_writes_a_beat_line_into_the_transcript(tmp_path):
    """Without a beat in the LOG, a long silent tool call and a dead process are
    indistinguishable — the transcript simply stops growing in both cases. The
    worktree comment already beats, but that is the mobile channel, not the one
    a terminal watcher or `progress` reads."""
    b = _bindir(tmp_path, ["agy"])
    log = tmp_path / "run.log"
    r = run(["exec", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--log", str(log)],
            env=_env(b, HMAD_STUB_AGY_RESP="VERDICT: COMPLIANT",
                     HMAD_STUB_AGY_SLEEP="4", HMAD_EXEC_HEARTBEAT_SEC="1"))
    assert r.returncode == 0, r.stderr
    assert "#hmad-beat" in log.read_text()
    # a beat must not corrupt the stream it shares
    assert r.stdout.strip() == "VERDICT: COMPLIANT"
