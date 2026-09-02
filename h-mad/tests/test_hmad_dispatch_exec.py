"""`exec <codex|agy>` — the exit-code dispatch path (alternative to the pane REPL).

The pane path (send + wait + read) can't wait on an exit code: codex/agy are
long-lived TUI REPLs, so there is no process to reap — completion is inferred by
polling the buffer for idle and parsing a token. `exec` runs the agent HEADLESS as
a real subprocess, so it returns the agent's own exit code with no poll, and — being
pane-independent — sidesteps agent identity resolution (orca#9870) entirely.

  codex — `codex exec`, prompt via stdin, final message via --output-last-message.
          The 5d/5e IMPLEMENTER path (writes; default --sandbox workspace-write).
  agy   — `agy --print "<prompt>"`, response straight to stdout. The AUDIT/REVIEW
          path (Phases 3/4/5b + 5e-review); a headless replacement for agy `ask`.

Both keep the two signals separate: `$?` answers "did the CLI run", the stdout
token answers "did the WORK pass" (exit 0 never means the task passed — a caller
still pipes stdout into h_mad_extract_verdict.py).
"""
import os
import sys
import re
import shlex
import subprocess
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent
WRAPPER = SKILL / "scripts" / "hmad-dispatch.sh"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_hmad_dispatch import SKILL_MD_TEXT, _bindir, _git_repo, run  # noqa: E402


# J23: `exec` appends the same boundary `send` does, so verdict recovery can tell our
# echoed prompt from the agent's reply. Kept as a literal, NOT imported from the
# script — a test that derives the constant from the code under test cannot catch the
# code changing it.
_BOUNDARY = "===HMAD-DISPATCH-BOUNDARY==="


def _prompt(tmp_path, text="RED task: write a failing test."):
    p = tmp_path / "prompt.txt"
    p.write_text(text)
    return p


def _env(b, **extra):
    # exec is substrate-independent (a real subprocess), so no pane pins/receipt.
    e = {"_BINDIR": b}
    e.update(extra)
    return e


def _exec_run_function():
    """Extract only the timeout helper, avoiding dispatch's terminal main call."""
    source = WRAPPER.read_text()
    starts = list(re.finditer(r"(?m)^([A-Za-z_][A-Za-z0-9_]*)\(\) \{", source))
    for i, match in enumerate(starts):
        if match.group(1) == "_exec_run":
            end = starts[i + 1].start() if i + 1 < len(starts) else len(source)
            return source[match.start():end]
    return ""


def _call_exec_run(*args, extra="", env=None):
    body = _exec_run_function()
    cmd = f"{body}\n{extra}\n_exec_run {shlex.join([str(a) for a in args])}"
    e = dict(os.environ)
    if env:
        e.update({k: str(v) for k, v in env.items()})
    return subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, env=e)


def test_ac_5_6_exec_run_consumes_heartbeat_context_without_child_argv(tmp_path):
    plain = tmp_path / "plain.argv"
    headed = tmp_path / "headed.argv"
    child = 'printf "%s\\n" "$@" > "$HMAD_TEST_ARGV_PATH"'
    r0 = _call_exec_run("", "bash", "-c", child, "child", "payload",
                       env={"HMAD_TEST_ARGV_PATH": plain})
    r1 = _call_exec_run("--heartbeat", "codex", "skills", tmp_path, "60", "",
                       "bash", "-c", child, "child", "payload",
                       env={"HMAD_TEST_ARGV_PATH": headed})
    assert r0.returncode == 0, r0.stderr
    assert r1.returncode == 0, r1.stderr
    plain_argv = plain.read_text().splitlines()
    headed_argv = headed.read_text().splitlines()
    assert plain_argv == headed_argv
    assert all(token not in headed_argv for token in ("--heartbeat", "codex", "skills", "60"))


def test_ac_5_7_nested_exec_run_output_is_reaped_intact():
    extra = "_exec_stamp() { :; }"
    command = "outer=\"$(_exec_run --heartbeat codex skills /tmp 60 '' bash -c 'printf nested')\"; printf %s \"$outer\""
    # The nested call is deliberately inside a command substitution in the shell
    # frame, which is the reaping scenario this acceptance criterion protects.
    body = _exec_run_function()
    r = subprocess.run(["bash", "-c", f"{body}\n{extra}\n{command}"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert r.stdout == "nested"


def test_ac_5_8_exec_run_does_not_implicitly_read_heartbeat_env(tmp_path):
    stamps = tmp_path / "stamps"
    extra = f'_exec_stamp() {{ printf x >> {shlex.quote(str(stamps))}; }}'
    r = _call_exec_run("", "bash", "-c", "sleep 0.1", env={"HMAD_EXEC_HEARTBEAT_SEC": "1"},
                       extra=extra)
    assert r.returncode == 0, r.stderr
    assert not stamps.exists() or stamps.read_text() == ""


# --- codex backend ------------------------------------------------------------

def test_codex_exec_runs_headless_with_the_right_flags(tmp_path):
    b = _bindir(tmp_path, ["codex"])
    cap = tmp_path / "cap.txt"
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path)],
            env=_env(b), capture=cap)
    assert r.returncode == 0, r.stderr
    argv = cap.read_text()
    assert "codex exec" in argv
    assert f"--cd {tmp_path}" in argv
    assert "--sandbox workspace-write" in argv, "5d/5e writes; default must be workspace-write"
    assert "--output-last-message" in argv
    assert "--skip-git-repo-check" in argv


def test_codex_exec_stdout_is_last_message_not_transcript(tmp_path):
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path)],
            env=_env(b, HMAD_STUB_CODEX_LAST="STATUS: DONE",
                     HMAD_STUB_CODEX_STDOUT="[codex] thinking... running pytest..."))
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "STATUS: DONE"
    assert "[codex] thinking" not in r.stdout
    assert "[codex] thinking" in r.stderr


def test_codex_exec_propagates_exit_code(tmp_path):
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path)],
            env=_env(b, HMAD_STUB_CODEX_RC="7"))
    assert r.returncode == 7, r.stderr
    assert "codex exec rc=7" in r.stderr


def test_codex_exec_writes_last_message_to_out(tmp_path):
    b = _bindir(tmp_path, ["codex"])
    out = tmp_path / "reply.txt"
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--out", str(out)],
            env=_env(b, HMAD_STUB_CODEX_LAST="VERDICT: COMPLIANT"))
    assert r.returncode == 0, r.stderr
    assert out.read_text() == "VERDICT: COMPLIANT"


def test_codex_exec_log_streams_transcript_for_tailing(tmp_path):
    """--log captures the live transcript to a tailable file; verdict path intact.

    The --output-last-message file only lands at completion, so it is NOT tailable
    — the transcript is what a watcher follows. --log must not disturb the verdict
    (still from the last-message file on stdout) or the exit code.
    """
    b = _bindir(tmp_path, ["codex"])
    log = tmp_path / "run.log"
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--log", str(log)],
            env=_env(b, HMAD_STUB_CODEX_LAST="STATUS: DONE",
                     HMAD_STUB_CODEX_STDOUT="[codex] running pytest..."))
    assert r.returncode == 0, r.stderr
    assert "[codex] running pytest..." in log.read_text()   # transcript is tailable
    assert r.stdout.strip() == "STATUS: DONE"                # verdict still clean
    assert "[codex] running" not in r.stdout                 # transcript not on stdout


def test_codex_exec_log_preserves_exit_code(tmp_path):
    b = _bindir(tmp_path, ["codex"])
    log = tmp_path / "run.log"
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--log", str(log)],
            env=_env(b, HMAD_STUB_CODEX_RC="7"))
    assert r.returncode == 7, r.stderr


@pytest.mark.parametrize(
    ("backend", "transcript", "env_key"),
    [
        pytest.param("codex", "[codex] appended transcript...\n", "HMAD_STUB_CODEX_STDOUT",
                     id="AC-11.1-codex-MUST_FAIL"),
        pytest.param("agy", "VERDICT: COMPLIANT\n", "HMAD_STUB_AGY_RESP",
                     id="AC-11.2-agy-REGRESSION_PASS"),
    ],
)
def test_exec_log_preserves_caller_bytes_and_appends_transcript(
    tmp_path, backend, transcript, env_key
):
    """AC-11.1/11.2: both surfaces preserve the caller log byte-for-byte."""
    b = _bindir(tmp_path, [backend])
    log = tmp_path / f"{backend}.log"
    log.write_bytes(b"PRIOR")
    r = run(
        ["exec", backend, str(_prompt(tmp_path)), "--cd", str(tmp_path), "--log", str(log)],
        env=_env(b, **{env_key: transcript.rstrip("\n")}),
    )
    assert r.returncode == 0, r.stderr
    # The caller's bytes must survive UNTOUCHED at the head of the file — that is
    # the whole AC. What follows them is the backend's transcript, whose FORMAT
    # differs by backend: codex appends plain text, agy appends the NDJSON event
    # stream it now emits so the log is watchable while the dispatch runs. So the
    # invariant is asserted as a prefix plus a recoverable payload, not as an
    # exact concatenation that would silently re-pin agy to the un-tailable
    # text mode this test's own AC never asked for.
    written = log.read_bytes()
    assert written.startswith(b"PRIOR")
    assert transcript.strip() in written.decode()


def test_exec_without_log_keeps_auto_temp_path_and_removes_it_on_clean_path(tmp_path):
    """REGRESSION AC-11.4: auto-log naming and clean-path cleanup remain unchanged."""
    b = _bindir(tmp_path, ["codex"])
    r = run(
        ["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path)],
        env=_env(b, HMAD_STUB_CODEX_LAST="STATUS: CLEAN"),
    )
    assert r.returncode == 0, r.stderr
    transcript = next(
        (
            line.split("transcript -> ", 1)[1].strip()
            for line in r.stderr.splitlines()
            if "transcript -> " in line
        ),
        None,
    )
    assert transcript is not None
    assert Path(transcript).name.startswith("hmad_exec_log.")
    assert not Path(transcript).exists()


def test_dispatch_boundary_comment_states_append_contract():
    """AC-11.5: the boundary rationale explicitly documents surviving log content."""
    source = WRAPPER.read_text()
    comment = source.split("  # J23: append the SAME boundary", 1)[1].split(
        "  local boundary;", 1
    )[0]
    lowered = comment.lower()
    assert "append" in lowered
    assert "caller-supplied" in lowered
    assert "log" in lowered


# --- empty final-message recovery (RED: expected to fail until GREEN) --------

def test_codex_empty_last_message_returns_reserved_rc_and_retains_auto_log(tmp_path):
    """AC-1.2 / AC-5.1: exit 0 plus empty last-message is not silent success."""
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path)],
            env=_env(b, HMAD_STUB_CODEX_LAST="", HMAD_STUB_CODEX_STDOUT="STATUS: DONE"))
    assert r.returncode == 3, r.stderr
    assert "EMPTY final message" in r.stderr
    transcript = next((line.split("transcript -> ", 1)[1].strip()
                       for line in r.stderr.splitlines() if "transcript -> " in line), None)
    assert transcript and Path(transcript).is_file(), r.stderr


def test_codex_empty_last_message_exit_zero_is_reserved_rc3(tmp_path):
    """AC-5.1: the exit-0/empty combination specifically returns rc 3."""
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path)],
            env=_env(b, HMAD_STUB_CODEX_LAST=""))
    assert r.returncode == 3, r.stderr


def test_codex_empty_message_recovers_last_verdict_and_reports_tree_delta(tmp_path):
    """AC-3.1 / AC-4.1: recover the anchored verdict and report changed paths.

    J23: now runs with the stdin echo ON, because that is what real codex does — the
    prompt, then our boundary, then the agent's own output. Modelling the transcript
    without the echo let this test assert recovery from a log shape codex never emits.
    """
    repo = _git_repo(tmp_path)
    changed = repo / "landed.txt"
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(repo)],
            env=_env(b, HMAD_STUB_CODEX_LAST="", HMAD_STUB_CODEX_STDOUT="STATUS: DONE",
                     HMAD_STUB_CODEX_ECHO_STDIN="1",
                     HMAD_STUB_CODEX_TOUCH=str(changed)))
    assert r.returncode == 3, r.stderr
    assert r.stdout.strip() == "STATUS: DONE"
    assert "verdict recovered from log" in r.stderr


def test_codex_empty_message_uses_last_of_multiple_verdict_lines(tmp_path):
    """AC-3.4: stale earlier verdicts must not win recovery.

    J23: echo ON, as real codex does — so this also pins that "last wins" operates on
    the agent's region only, not on the echoed prompt that precedes the boundary.
    """
    b = _bindir(tmp_path, ["codex"])
    transcript = "reply with STATUS: INLINE\nSTATUS: FIRST\nVERDICT: LAST\n"
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path)],
            env=_env(b, HMAD_STUB_CODEX_LAST="", HMAD_STUB_CODEX_ECHO_STDIN="1",
                     HMAD_STUB_CODEX_STDOUT=transcript))
    assert r.returncode == 3, r.stderr
    assert r.stdout.strip() == "VERDICT: LAST"
    assert "INLINE" not in r.stdout


def test_codex_empty_message_reports_git_tree_delta(tmp_path):
    """AC-4.1 / AC-4.2: delta is counted in the requested --cd repository."""
    repo = _git_repo(tmp_path)
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(repo)],
            env=_env(b, HMAD_STUB_CODEX_LAST="", HMAD_STUB_CODEX_TOUCH=str(repo / "landed.txt")))
    assert r.returncode == 3, r.stderr
    assert "tree delta: 1 changed" in r.stderr


def test_agy_empty_response_recovers_verdict_from_caller_log(tmp_path):
    """AC-2.2 / AC-3.1: an empty agy response still recovers its transcript.

    Guards the DEGRADED recovery route specifically: the transcript here carries
    a bare verdict line and no `result` event, so the structured NDJSON read
    finds nothing and the line-oriented scan has to carry it. That is the shape
    an agy build without `--output-format` support would leave behind.
    """
    b = _bindir(tmp_path, ["agy"])
    log = tmp_path / "agy.log"
    r = run(["exec", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--log", str(log)],
            env=_env(b, HMAD_STUB_AGY_RESP="", HMAD_STUB_AGY_TRANSCRIPT_PATH=str(log),
                     HMAD_STUB_AGY_TRANSCRIPT="VERDICT: COMPLIANT"))
    assert r.returncode == 3, r.stderr
    assert r.stdout.strip() == "VERDICT: COMPLIANT"
    assert "verdict recovered from log" in r.stderr


def test_agy_degraded_recovery_ignores_content_written_before_this_dispatch(tmp_path):
    """J23, agy arm: the degraded scan must not read a PRIOR dispatch's echo.

    The codex arm refuses when its boundary is absent, because a truncated echo
    still carries the contract block. The agy arm has no boundary to expect and
    scanned the whole transcript -- but both arms append to a caller-supplied
    `--log` with `>>`, so a codex dispatch whose echo was truncated before the
    boundary landed leaves that contract block in a log a later agy dispatch then
    scans. `tail -1` returns its last option, deterministically NEEDS_CONTEXT,
    and the caller writes it to `--out`: the original laundering, reached through
    the other arm.

    `pre_lines` already records how much of the log predates this dispatch, and
    the structured NDJSON read has always honoured it. Only the fallback did not.
    """
    b = _bindir(tmp_path, ["agy"])
    log = tmp_path / "shared.log"
    log.write_text(
        "STATUS: DONE\nSTATUS: DONE_WITH_CONCERNS\n"
        "STATUS: BLOCKED\nSTATUS: NEEDS_CONTEXT\n"
    )
    r = run(["exec", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--log", str(log)],
            env=_env(b, HMAD_STUB_AGY_RESP=""))

    assert "NEEDS_CONTEXT" not in r.stdout, (
        "recovered a verdict from a PRIOR dispatch's echoed contract block"
    )
    assert "verdict recovered from log" not in r.stderr


def test_empty_message_crash_preserves_agent_rc(tmp_path):
    """AC-5.2: rc 3 is reserved for agent-exit-0 reporting failures."""
    b = _bindir(tmp_path, ["codex"])
    log = tmp_path / "crash.log"
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--log", str(log)],
            env=_env(b, HMAD_STUB_CODEX_LAST="", HMAD_STUB_CODEX_RC="2"))
    assert r.returncode == 2, r.stderr
    assert r.returncode != 3
    assert "EMPTY final message" in r.stderr


def test_empty_message_in_non_repo_reports_na_tree_delta_and_rc3(tmp_path):
    """AC-4.3: tree inspection is non-fatal outside a git work tree."""
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path)],
            env=_env(b, HMAD_STUB_CODEX_LAST=""))
    assert r.returncode == 3, r.stderr
    assert f"tree delta: n/a ({tmp_path} not a git repo)" in r.stderr


def test_clean_nonempty_exec_is_regression_guard(tmp_path):
    """REGRESSION AC-1.4 / AC-2.3 / AC-5.4: clean path stays rc 0 and payload-only."""
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path)],
            env=_env(b, HMAD_STUB_CODEX_LAST="STATUS: CLEAN"))
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "STATUS: CLEAN"


def test_caller_log_is_honored_and_not_deleted_regression_guard(tmp_path):
    """REGRESSION AC-1.3: an explicit transcript path remains caller-owned."""
    b = _bindir(tmp_path, ["codex"])
    log = tmp_path / "caller.log"
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--log", str(log)],
            env=_env(b, HMAD_STUB_CODEX_LAST="STATUS: CLEAN"))
    assert r.returncode == 0, r.stderr
    assert log.is_file()


def test_codex_exec_delivers_prompt_via_stdin(tmp_path):
    b = _bindir(tmp_path, ["codex"])
    seen = tmp_path / "stdin.txt"
    pf = _prompt(tmp_path, "a" * 20000)  # past the 8192 keystroke inline cap
    r = run(["exec", "codex", str(pf), "--cd", str(tmp_path)],
            env=_env(b, HMAD_STUB_STDIN_CAPTURE=str(seen)))
    assert r.returncode == 0, r.stderr
    # J23: the dispatch boundary is appended to whatever we deliver, so the prompt is
    # a PREFIX of stdin now, not the whole of it. The point of this test is unchanged:
    # the full 20k prompt survives the pipe.
    assert seen.read_text().startswith("a" * 20000)
    assert seen.read_text().rstrip().endswith(_BOUNDARY)


def test_codex_exec_delivers_stdin_even_through_the_timeout_path(tmp_path):
    # Regression: bash nul's a backgrounded command's stdin, so the --timeout path
    # (which backgrounds codex) once starved `codex exec -` of its piped prompt.
    b = _bindir(tmp_path, ["codex"])
    seen = tmp_path / "stdin.txt"
    pf = _prompt(tmp_path, "prompt through the watchdog")
    r = run(["exec", "codex", str(pf), "--cd", str(tmp_path), "--timeout", "30"],
            env=_env(b, HMAD_STUB_STDIN_CAPTURE=str(seen)))
    assert r.returncode == 0, r.stderr
    assert seen.read_text().startswith("prompt through the watchdog")
    # J23: the boundary must survive the backgrounded path too — if it were dropped
    # here, verdict recovery would silently fall back to grepping the echoed prompt.
    assert seen.read_text().rstrip().endswith(_BOUNDARY)


def test_codex_exec_passes_model(tmp_path):
    b = _bindir(tmp_path, ["codex"])
    cap = tmp_path / "cap.txt"
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--model", "gpt-5-codex"],
            env=_env(b), capture=cap)
    assert r.returncode == 0, r.stderr
    assert "--model gpt-5-codex" in cap.read_text()


def test_codex_exec_sandbox_override(tmp_path):
    b = _bindir(tmp_path, ["codex"])
    cap = tmp_path / "cap.txt"
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--sandbox", "read-only"],
            env=_env(b), capture=cap)
    assert r.returncode == 0, r.stderr
    assert "--sandbox read-only" in cap.read_text()
    assert "--sandbox workspace-write" not in cap.read_text()


def test_codex_exec_maps_effort_to_a_config_override(tmp_path):
    """Codex has no `--effort` flag; reasoning effort is `-c model_reasoning_effort`.
    A bare `--effort high` passed through verbatim would die as an unknown flag."""
    b = _bindir(tmp_path, ["codex"])
    cap = tmp_path / "cap.txt"
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--effort", "high"],
            env=_env(b), capture=cap)
    assert r.returncode == 0, r.stderr
    argv = cap.read_text()
    assert "-c model_reasoning_effort=high" in argv
    assert "--effort high" not in argv


def test_codex_exec_omits_the_effort_override_when_unset(tmp_path):
    """Unset must leave ~/.codex/config.toml's own default in force, not pin one."""
    b = _bindir(tmp_path, ["codex"])
    cap = tmp_path / "cap.txt"
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path)],
            env=_env(b), capture=cap)
    assert r.returncode == 0, r.stderr
    assert "model_reasoning_effort" not in cap.read_text()


# --- agy backend --------------------------------------------------------------

def test_agy_exec_runs_print_headless_prompt_as_last_arg(tmp_path):
    b = _bindir(tmp_path, ["agy"])
    cap = tmp_path / "cap.txt"
    r = run(["exec", "agy", str(_prompt(tmp_path, "audit this")), "--cd", str(tmp_path)],
            env=_env(b), capture=cap)
    assert r.returncode == 0, r.stderr
    argv = cap.read_text()
    assert "--dangerously-skip-permissions" in argv, "headless must auto-approve or it blocks on a tool request"
    # `--print` consumes the NEXT token as the prompt, so it must be IMMEDIATELY
    # followed by the prompt. A `--print` with a flag after it ate that flag as the
    # prompt and dropped the real one (verified live — agy just greeted).
    assert "--print audit this" in argv, f"--print must be adjacent to the prompt:\n{argv}"
    # J23: the prompt is still the last ARG; it now ends with the appended boundary.
    assert argv.rstrip().endswith(_BOUNDARY), f"prompt must be the last arg:\n{argv}"


def test_agy_exec_stdout_is_the_response(tmp_path):
    b = _bindir(tmp_path, ["agy"])
    r = run(["exec", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path)],
            env=_env(b, HMAD_STUB_AGY_RESP="VERDICT: DRIFT"))
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "VERDICT: DRIFT"


def test_agy_exec_propagates_exit_code(tmp_path):
    b = _bindir(tmp_path, ["agy"])
    r = run(["exec", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path)],
            env=_env(b, HMAD_STUB_AGY_RC="5"))
    assert r.returncode == 5, r.stderr
    assert "agy exec rc=5" in r.stderr


def test_agy_exec_writes_response_to_out(tmp_path):
    b = _bindir(tmp_path, ["agy"])
    out = tmp_path / "reply.txt"
    r = run(["exec", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--out", str(out)],
            env=_env(b, HMAD_STUB_AGY_RESP="VERDICT: COMPLIANT"))
    assert r.returncode == 0, r.stderr
    assert out.read_text().strip() == "VERDICT: COMPLIANT"


def test_agy_exec_log_streams_response_for_tailing(tmp_path):
    """--log streams agy's response to a tailable file AND the verdict stays clean.

    agy --print buffers under command substitution, so without --log there is
    nothing to tail. --log redirects the response (stdout only — no stderr noise)
    to the file, read back for the verdict; exit code preserved (direct redirect,
    not a pipe).
    """
    b = _bindir(tmp_path, ["agy"])
    log = tmp_path / "run.log"
    r = run(["exec", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--log", str(log)],
            env=_env(b, HMAD_STUB_AGY_RESP="VERDICT: COMPLIANT"))
    assert r.returncode == 0, r.stderr
    assert "VERDICT: COMPLIANT" in log.read_text()       # tailable
    assert r.stdout.strip() == "VERDICT: COMPLIANT"       # verdict still on stdout


def test_agy_exec_log_preserves_exit_code(tmp_path):
    b = _bindir(tmp_path, ["agy"])
    log = tmp_path / "run.log"
    r = run(["exec", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--log", str(log)],
            env=_env(b, HMAD_STUB_AGY_RC="5", HMAD_STUB_AGY_RESP="VERDICT: DRIFT"))
    assert r.returncode == 5, r.stderr


def test_agy_exec_passes_model_and_effort(tmp_path):
    b = _bindir(tmp_path, ["agy"])
    cap = tmp_path / "cap.txt"
    r = run(["exec", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--model", "gemini-3-pro", "--effort", "high"],
            env=_env(b), capture=cap)
    assert r.returncode == 0, r.stderr
    argv = cap.read_text()
    assert "--model gemini-3-pro" in argv
    assert "--effort high" in argv


def test_agy_exec_timeout_maps_to_print_timeout(tmp_path):
    b = _bindir(tmp_path, ["agy"])
    cap = tmp_path / "cap.txt"
    r = run(["exec", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--timeout", "90"],
            env=_env(b), capture=cap)
    assert r.returncode == 0, r.stderr
    assert "--print-timeout 90s" in cap.read_text()


def test_agy_exec_delivers_prompt_as_arg(tmp_path):
    b = _bindir(tmp_path, ["agy"])
    seen = tmp_path / "prompt_seen.txt"
    r = run(["exec", "agy", str(_prompt(tmp_path, "the whole audit prompt")), "--cd", str(tmp_path)],
            env=_env(b, HMAD_STUB_AGY_PROMPT_CAPTURE=str(seen)))
    assert r.returncode == 0, r.stderr
    assert seen.read_text().startswith("the whole audit prompt")
    assert seen.read_text().rstrip().endswith(_BOUNDARY)


def test_agy_exec_timeout_kills_and_returns_124(tmp_path):
    b = _bindir(tmp_path, ["agy"])
    r = run(["exec", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--timeout", "1"],
            env=_env(b, HMAD_STUB_AGY_SLEEP="6"))
    assert r.returncode == 124, f"expected 124 (timed out), got {r.returncode}\n{r.stderr}"


def test_agy_exec_errors_when_agy_absent(tmp_path):
    b = _bindir(tmp_path, [])  # no agy on PATH
    r = run(["exec", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path)], env=_env(b))
    assert r.returncode == 2
    assert "requires the agy CLI" in r.stderr


# --- shared / routing ---------------------------------------------------------

def test_exec_timeout_kills_codex_and_returns_124(tmp_path):
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--timeout", "1"],
            env=_env(b, HMAD_STUB_CODEX_SLEEP="6"))
    assert r.returncode == 124, f"expected 124 (timed out), got {r.returncode}\n{r.stderr}"


def test_exec_requires_an_agent(tmp_path):
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec"], env=_env(b))
    assert r.returncode != 0
    assert "missing required argument: agent" in r.stderr


def test_exec_rejects_unknown_agent(tmp_path):
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec", "claude", str(_prompt(tmp_path))], env=_env(b))
    assert r.returncode == 2
    assert "unknown agent" in r.stderr


def test_exec_requires_a_prompt(tmp_path):
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec", "codex"], env=_env(b))
    assert r.returncode != 0
    assert "missing required argument: promptfile" in r.stderr


def test_exec_missing_prompt_file_fails(tmp_path):
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec", "codex", str(tmp_path / "nope.txt"), "--cd", str(tmp_path)], env=_env(b))
    assert r.returncode == 2
    assert "no such prompt file" in r.stderr


def test_exec_rejects_unknown_flag(tmp_path):
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--sandbx", "read-only"],
            env=_env(b))
    assert r.returncode == 2
    assert "unknown option" in r.stderr.lower()
    assert "--sandbx" in r.stderr


# --- J23: the exec recovery path must not launder the prompt's own contract block -----

# The four legal STATUS values, as `references/codex-implementer-prompt.md` requires a
# dispatch prompt to state them: fenced, one per line. Real codex echoes the piped
# prompt into its transcript, so these land in $log verbatim.
_CONTRACT_BLOCK = """\
Finish by printing exactly one STATUS line:

```
STATUS: DONE
```
```
STATUS: DONE_WITH_CONCERNS
```
```
STATUS: BLOCKED
```
```
STATUS: NEEDS_CONTEXT
```
"""


def test_codex_failed_dispatch_does_not_launder_the_prompt_contract_as_a_verdict(tmp_path):
    """J23 defect 1: recovery grepped the WHOLE transcript, prompt echo included.

    Measured 2026-08-03 from a real Phase-5 dispatch that died on revoked Codex auth
    (401): the only four `STATUS:` lines in the 20,770-byte log were the prompt's own
    four fenced options at lines 268/271/274/277, so `tail -1` returned
    `STATUS: NEEDS_CONTEXT` deterministically and line 1930 wrote it to `--out`, where
    h_mad_extract_verdict.py accepts it without complaint. No agent-authored STATUS line
    existed; the agent never ran. The `key-must-start-the-line` guard does not help --
    the echoed contract lines do start the line.

    Silence is the only correct answer here. `send` has had this guard since it was
    written (see the boundary block in `_cmd_send`); `exec` did not.
    """
    b = _bindir(tmp_path, ["codex"])
    out = tmp_path / "verdict.out"
    r = run(["exec", "codex", str(_prompt(tmp_path, _CONTRACT_BLOCK)),
             "--cd", str(tmp_path), "--out", str(out)],
            env=_env(b, HMAD_STUB_CODEX_LAST="", HMAD_STUB_CODEX_RC="1",
                     HMAD_STUB_CODEX_ECHO_STDIN="1"))
    assert r.returncode == 1, "the agent's own exit code must survive"
    # The whole point: no verdict may be manufactured from the echoed prompt.
    assert "STATUS:" not in r.stdout, f"laundered a prompt line as a verdict: {r.stdout!r}"
    assert r.stdout.strip() == ""
    assert "verdict recovered from log" not in r.stderr
    # And the primary channel must stay empty rather than hold a contract-valid lie.
    assert not out.exists() or out.read_text().strip() == "", \
        f"--out holds a fabricated verdict: {out.read_text()!r}"


def test_codex_recovers_a_real_verdict_written_after_the_echoed_prompt(tmp_path):
    """J23, the other half: the guard must not silence a GENUINE verdict.

    Same echoed contract block, but this time the agent ran and answered. The real
    reply lands after the echo, so slicing past the boundary keeps it. Without this,
    the fix for the test above could simply be "never recover", which would break the
    recovery path the `EMPTY final message` branch exists for.
    """
    b = _bindir(tmp_path, ["codex"])
    out = tmp_path / "verdict.out"
    r = run(["exec", "codex", str(_prompt(tmp_path, _CONTRACT_BLOCK)),
             "--cd", str(tmp_path), "--out", str(out)],
            env=_env(b, HMAD_STUB_CODEX_LAST="", HMAD_STUB_CODEX_RC="1",
                     HMAD_STUB_CODEX_ECHO_STDIN="1",
                     HMAD_STUB_CODEX_STDOUT="ran the task\nSTATUS: BLOCKED"))
    assert r.returncode == 1, r.stderr
    assert r.stdout.strip() == "STATUS: BLOCKED", r.stdout
    assert "verdict recovered from log" in r.stderr
    assert out.read_text().strip() == "STATUS: BLOCKED"


def test_codex_tree_delta_counts_only_the_cd_subdir(tmp_path):
    """J23 defect 2: `git -C <subdir> status --porcelain` reports the WHOLE work tree.

    Measured: `--cd .../HemaSuite/hematology-paper-writer` reported `1 changed` while
    `git status --short .` there was empty -- the counted file was one directory ABOVE
    the --cd, pre-existing and unrelated. The recovery protocol reads a non-zero delta
    as "the work happened, only reporting failed", so a false non-zero argues against
    re-dispatching a task that never ran.
    """
    repo = _git_repo(tmp_path)
    sub = repo / "sub"
    sub.mkdir()                       # stays CLEAN — an empty dir is invisible to git
    (repo / "outside.txt").write_text("dirty, and ABOVE the --cd\n")
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(sub)],
            env=_env(b, HMAD_STUB_CODEX_LAST=""))
    assert r.returncode == 3, r.stderr
    assert "tree delta: 0 changed" in r.stderr, r.stderr


def test_codex_tree_delta_still_counts_changes_inside_the_cd_subdir(tmp_path):
    """J23 defect 2, the other half: scoping must not blind the counter.

    Pairs with the test above so the fix cannot be "always report 0" -- a dirty file
    INSIDE the --cd must still be counted, which is the signal the recovery protocol
    actually reads.
    """
    repo = _git_repo(tmp_path)
    sub = repo / "sub"
    sub.mkdir()
    (sub / "landed.txt").write_text("the agent's work\n")
    (repo / "outside.txt").write_text("dirty, and ABOVE the --cd\n")
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(sub)],
            env=_env(b, HMAD_STUB_CODEX_LAST=""))
    assert r.returncode == 3, r.stderr
    assert "tree delta: 1 changed" in r.stderr, r.stderr


def test_codex_truncated_echo_without_the_boundary_recovers_nothing(tmp_path):
    """J23 residual hole, found by replaying the real incident log against the fix.

    The 20,770-byte evidence transcript predates the boundary, so slicing alone still
    fabricated `STATUS: NEEDS_CONTEXT` from it — the "no boundary, grep everything"
    fallback let the defect straight back in. The same shape occurs post-fix whenever
    codex dies mid-echo: the contract block is already in the transcript, the trailing
    boundary is not.

    For codex the boundary is EXPECTED (it echoes stdin), so its absence means the echo
    is missing or truncated and nothing in the log can be trusted as agent-authored.
    Refuse. The agy path keeps the whole-log read — see the caller-log test above, which
    must stay green.
    """
    b = _bindir(tmp_path, ["codex"])
    out = tmp_path / "verdict.out"
    # The transcript must carry the truncation, NOT a pre-written --log: the codex
    # branch redirects with `> "$log"`, so it truncates a caller-supplied log before
    # writing. (Found by a surviving mutant — the first version of this test seeded
    # the log, watched the wrapper wipe it, and asserted against an empty file, so it
    # passed with the guard removed.) Driving it through the stub's stdout is what
    # actually puts a boundary-less contract block in front of the recovery code.
    r = run(["exec", "codex", str(_prompt(tmp_path, _CONTRACT_BLOCK)),
             "--cd", str(tmp_path), "--out", str(out)],
            env=_env(b, HMAD_STUB_CODEX_LAST="", HMAD_STUB_CODEX_RC="1",
                     HMAD_STUB_CODEX_STDOUT="[codex] booting\n" + _CONTRACT_BLOCK))
    assert r.returncode == 1, r.stderr
    assert "STATUS:" not in r.stdout, f"truncated echo laundered a verdict: {r.stdout!r}"
    assert "verdict recovered from log" not in r.stderr
    assert not out.exists() or out.read_text().strip() == ""


def test_codex_slices_past_the_LAST_boundary_not_the_first(tmp_path):
    """J23: which occurrence is load-bearing when the boundary appears twice.

    An agent that quotes its instructions back — or any transcript carrying a second
    copy — puts the marker in the log more than once. Slicing at the FIRST occurrence
    leaves everything between the two copies in the "agent-authored" region, and that
    span still contains the echoed contract block, so the laundering returns. Only the
    last occurrence bounds the region the agent could actually have written.

    Written because a mutant that swapped `tail -1` for `head -1` on the boundary
    lookup SURVIVED the rest of this file.
    """
    b = _bindir(tmp_path, ["codex"])
    out = tmp_path / "verdict.out"
    # The regions must actually DIFFER, or the test cannot tell the two apart: since
    # both slices end at EOF, `tail -1` returns the same line whenever the real verdict
    # is last. So put every STATUS line BETWEEN the two boundaries and let the agent
    # die silently after the second — which is what a quote-then-crash looks like.
    #   region after LAST  boundary -> empty        -> recover nothing (correct)
    #   region after FIRST boundary -> the block    -> recover NEEDS_CONTEXT (the bug)
    transcript = (
        f"[codex] starting\n{_BOUNDARY}\n"
        f"let me restate my instructions:\n{_CONTRACT_BLOCK}"
        f"{_BOUNDARY}\n"
    )
    r = run(["exec", "codex", str(_prompt(tmp_path, _CONTRACT_BLOCK)),
             "--cd", str(tmp_path), "--out", str(out)],
            env=_env(b, HMAD_STUB_CODEX_LAST="", HMAD_STUB_CODEX_RC="1",
                     HMAD_STUB_CODEX_STDOUT=transcript))
    assert r.returncode == 1, r.stderr
    assert "NEEDS_CONTEXT" not in r.stdout, \
        f"sliced at the first boundary and laundered the quoted block: {r.stdout!r}"
    assert r.stdout.strip() == ""
    assert not out.exists() or out.read_text().strip() == ""


def test_codex_recovers_a_verdict_written_after_a_quoted_boundary(tmp_path):
    """Pairs with the test above: slicing at the LAST boundary must not over-silence.

    Same quote-the-instructions-back transcript, but the agent then answers. The reply
    sits after the final boundary and must survive.
    """
    b = _bindir(tmp_path, ["codex"])
    out = tmp_path / "verdict.out"
    transcript = (
        f"[codex] starting\n{_BOUNDARY}\n"
        f"let me restate my instructions:\n{_CONTRACT_BLOCK}"
        f"{_BOUNDARY}\n"
        "ran the task\nSTATUS: DONE_WITH_CONCERNS\n"
    )
    r = run(["exec", "codex", str(_prompt(tmp_path, _CONTRACT_BLOCK)),
             "--cd", str(tmp_path), "--out", str(out)],
            env=_env(b, HMAD_STUB_CODEX_LAST="", HMAD_STUB_CODEX_RC="1",
                     HMAD_STUB_CODEX_STDOUT=transcript))
    assert r.returncode == 1, r.stderr
    assert r.stdout.strip() == "STATUS: DONE_WITH_CONCERNS", r.stdout
    assert out.read_text().strip() == "STATUS: DONE_WITH_CONCERNS"


# --- J29: the --out clobber guard ---------------------------------------------
#
# `--out` is last-writer-wins across concurrent dispatches, silently. Verified
# deliberately while chasing J28: two `exec agy` runs pointed at one `--out` both
# exited 0, and the file held only the SECOND responder's answer. Because both
# exited 0, nothing distinguished that from a dispatch that was never run.
# (`--log` is exempt by design -- both backends APPEND to a caller-supplied log,
# which is what let verdict recovery find the lost half.)
#
# The guard is WRITE-TIME and keyed on "changed under our watch", not a pre-flight
# `[ -s "$out" ]` refusal, and that choice is load-bearing. references/failure-
# recovery.md instructs the operator to RE-DISPATCH after a `<phase>:no_verdict`,
# and SKILL.md's --out paths are templated per feature+module
# (`/tmp/rev_<feature>_<module>.txt`) -- deterministic, so the retry lands on the
# SAME path, which the failed attempt already left non-empty with its short
# narration. A pre-flight refusal would refuse h-mad's own documented recovery.
# What is refused is narrower: the file changed BETWEEN dispatch start and the
# write, which only a second writer can cause.


def test_agy_exec_refuses_to_clobber_an_out_a_rival_wrote_while_it_ran(tmp_path):
    """J29 proper: the rival's verdict survives instead of being silently lost."""
    b = _bindir(tmp_path, ["agy"])
    out = tmp_path / "rev_feature_module.txt"          # the templated shared path
    rival = "VERDICT: NON_COMPLIANT — the other dispatch"
    r = run(["exec", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--out", str(out)],
            env=_env(b, HMAD_STUB_AGY_RESP="VERDICT: COMPLIANT",
                     HMAD_STUB_AGY_RIVAL_OUT=str(out), HMAD_STUB_AGY_RIVAL=rival))
    assert out.read_text().strip() == rival, \
        "the rival's verdict must survive — silently losing one is the J29 defect"
    assert "VERDICT: COMPLIANT" in r.stdout, \
        "our own verdict is not lost either: stdout is still the primary channel"
    assert "REFUSING to overwrite --out" in r.stderr
    # rc stays the AGENT's exit code. The function's contract is `$?` == "did the
    # CLI run"; _exec_stamp and _cmd_notify both consume it. The defect J29 records
    # is SILENCE, and stderr is what cures that.
    assert r.returncode == 0, r.stderr


def test_codex_exec_refuses_to_clobber_an_out_a_rival_wrote_while_it_ran(tmp_path):
    """Same guard on the codex write site (`cp` from the last-message file)."""
    b = _bindir(tmp_path, ["codex"])
    out = tmp_path / "exec_feature_module.txt"
    rival = "STATUS: BLOCKED — the other dispatch"
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--out", str(out)],
            env=_env(b, HMAD_STUB_CODEX_LAST="STATUS: DONE",
                     HMAD_STUB_CODEX_RIVAL_OUT=str(out), HMAD_STUB_CODEX_RIVAL=rival))
    assert out.read_text().strip() == rival
    assert r.stdout.strip() == "STATUS: DONE"
    assert "REFUSING to overwrite --out" in r.stderr
    assert r.returncode == 0, r.stderr


def test_exec_still_overwrites_a_stale_out_left_by_a_previous_attempt(tmp_path):
    """The guard must NOT refuse h-mad's own documented retry.

    failure-recovery.md's `<phase>:no_verdict` remedy is to re-dispatch, and the
    --out path is templated per feature+module, so attempt 2 arrives at a file
    attempt 1 already filled with exactly the shape that failed: a short narration
    with no sentinel. Unchanged since this dispatch started == nobody else wrote ==
    safe to overwrite. Without this test the guard could be "refuse whenever the
    file is non-empty", which passes the two tests above and breaks the protocol.
    """
    b = _bindir(tmp_path, ["agy"])
    out = tmp_path / "rev_feature_module.txt"
    out.write_text("narration naming real Must-fix items, no sentinel — the "
                   "no_verdict shape\n")
    r = run(["exec", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--out", str(out)],
            env=_env(b, HMAD_STUB_AGY_RESP="VERDICT: COMPLIANT"))
    assert r.returncode == 0, r.stderr
    assert out.read_text().strip() == "VERDICT: COMPLIANT", \
        "a stale --out from this caller's own failed attempt must still be replaced"
    assert "REFUSING" not in r.stderr


def test_codex_verdict_recovery_also_respects_the_clobber_guard(tmp_path):
    """The third write site — the EMPTY-final-message recovery path — is guarded too.

    Recovery is exactly when a rival is most likely to have finished first, and it
    is the site where a silent clobber is most damaging: it overwrites a real
    verdict with one salvaged from a transcript.
    """
    b = _bindir(tmp_path, ["codex"])
    out = tmp_path / "exec_feature_module.txt"
    rival = "STATUS: DONE — the other dispatch"
    r = run(["exec", "codex", str(_prompt(tmp_path, _CONTRACT_BLOCK)),
             "--cd", str(tmp_path), "--out", str(out)],
            env=_env(b, HMAD_STUB_CODEX_LAST="", HMAD_STUB_CODEX_RC="1",
                     HMAD_STUB_CODEX_ECHO_STDIN="1",
                     HMAD_STUB_CODEX_STDOUT="ran the task\nSTATUS: BLOCKED",
                     HMAD_STUB_CODEX_RIVAL_OUT=str(out), HMAD_STUB_CODEX_RIVAL=rival))
    assert r.returncode == 1, r.stderr
    assert "verdict recovered from log" in r.stderr, "recovery itself must still run"
    assert r.stdout.strip() == "STATUS: BLOCKED", "the recovered verdict reaches stdout"
    assert out.read_text().strip() == rival, "but it must not clobber the rival's"
    assert "REFUSING to overwrite --out" in r.stderr


def test_exec_without_out_is_unaffected_by_the_guard(tmp_path):
    """`--out` is optional; the guard must not fire (or crash) when it is absent."""
    b = _bindir(tmp_path, ["agy"])
    r = run(["exec", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path)],
            env=_env(b, HMAD_STUB_AGY_RESP="VERDICT: COMPLIANT"))
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "VERDICT: COMPLIANT"
    assert "REFUSING" not in r.stderr


def test_skill_md_documents_the_out_clobber_guard():
    """A guard the operator cannot read about is a guard they will work around.

    The anchor is asserted to match at least once BEFORE any content assertion:
    a zero-match anchor leaves the doc unpinned while the suite stays green, which
    is the failure mode that bit twice in the 2026-08-09 mutation runs.
    """
    anchor = "refuses to overwrite an `--out` whose content changed"
    assert SKILL_MD_TEXT.count(anchor) > 0, \
        f"anchor matched 0 times — SKILL.md does not document the J29 guard: {anchor!r}"
