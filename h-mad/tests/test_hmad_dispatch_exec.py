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
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_hmad_dispatch import _bindir, _git_repo, run  # noqa: E402


def _prompt(tmp_path, text="RED task: write a failing test."):
    p = tmp_path / "prompt.txt"
    p.write_text(text)
    return p


def _env(b, **extra):
    # exec is substrate-independent (a real subprocess), so no pane pins/receipt.
    e = {"_BINDIR": b}
    e.update(extra)
    return e


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
    """AC-3.1 / AC-4.1: recover the anchored verdict and report changed paths."""
    repo = _git_repo(tmp_path)
    changed = repo / "landed.txt"
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(repo)],
            env=_env(b, HMAD_STUB_CODEX_LAST="", HMAD_STUB_CODEX_STDOUT="STATUS: DONE",
                     HMAD_STUB_CODEX_TOUCH=str(changed)))
    assert r.returncode == 3, r.stderr
    assert r.stdout.strip() == "STATUS: DONE"
    assert "verdict recovered from log" in r.stderr


def test_codex_empty_message_uses_last_of_multiple_verdict_lines(tmp_path):
    """AC-3.4: stale earlier verdicts must not win recovery."""
    b = _bindir(tmp_path, ["codex"])
    transcript = "reply with STATUS: INLINE\nSTATUS: FIRST\nVERDICT: LAST\n"
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path)],
            env=_env(b, HMAD_STUB_CODEX_LAST="", HMAD_STUB_CODEX_STDOUT=transcript))
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
    """AC-2.2 / AC-3.1: an empty agy response still recovers its transcript."""
    b = _bindir(tmp_path, ["agy"])
    log = tmp_path / "agy.log"
    r = run(["exec", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--log", str(log)],
            env=_env(b, HMAD_STUB_AGY_RESP="", HMAD_STUB_AGY_TRANSCRIPT_PATH=str(log),
                     HMAD_STUB_AGY_TRANSCRIPT="VERDICT: COMPLIANT"))
    assert r.returncode == 3, r.stderr
    assert r.stdout.strip() == "VERDICT: COMPLIANT"
    assert "verdict recovered from log" in r.stderr


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
    assert seen.read_text() == "a" * 20000


def test_codex_exec_delivers_stdin_even_through_the_timeout_path(tmp_path):
    # Regression: bash nul's a backgrounded command's stdin, so the --timeout path
    # (which backgrounds codex) once starved `codex exec -` of its piped prompt.
    b = _bindir(tmp_path, ["codex"])
    seen = tmp_path / "stdin.txt"
    pf = _prompt(tmp_path, "prompt through the watchdog")
    r = run(["exec", "codex", str(pf), "--cd", str(tmp_path), "--timeout", "30"],
            env=_env(b, HMAD_STUB_STDIN_CAPTURE=str(seen)))
    assert r.returncode == 0, r.stderr
    assert seen.read_text() == "prompt through the watchdog"


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


def test_codex_exec_rejects_agy_only_effort_flag(tmp_path):
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--effort", "high"],
            env=_env(b))
    assert r.returncode == 2
    assert "--effort is agy-only" in r.stderr


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
    assert argv.rstrip().endswith("audit this"), f"prompt must be the last arg:\n{argv}"


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
    assert seen.read_text() == "the whole audit prompt"


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
