"""`exec` — the exit-code dispatch path (Phase 5d/5e alternative to the pane REPL).

The pane path (send + wait + read) can't wait on an exit code: codex/agy are
long-lived TUI REPLs, so there is no process to reap — completion is inferred by
polling the buffer for idle and parsing a token. `exec` runs codex HEADLESS
(`codex exec`) as a real subprocess, so it returns codex's own exit code with no
poll. It captures the agent's final message via `--output-last-message` and echoes
it to stdout (the STATUS:/VERDICT: carrier, mirroring `ask`); the streamed run
transcript goes to stderr.

Both signals stay separate on purpose: `$?` answers "did the CLI run", the stdout
token answers "did the WORK pass" (exit 0 never means the TDD task passed — a
caller still pipes stdout into h_mad_extract_verdict.py).
"""
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_hmad_dispatch import _bindir, run  # noqa: E402


def _prompt(tmp_path, text="RED task: write a failing test."):
    p = tmp_path / "prompt.txt"
    p.write_text(text)
    return p


def _env(b, tmp_path, **extra):
    # exec is substrate-independent (a real subprocess), so no pane pins/receipt.
    e = {"_BINDIR": b}
    e.update(extra)
    return e


def test_exec_runs_codex_headless_with_the_right_flags(tmp_path):
    b = _bindir(tmp_path, ["codex"])
    cap = tmp_path / "cap.txt"
    r = run(["exec", str(_prompt(tmp_path)), "--cd", str(tmp_path)],
            env=_env(b, tmp_path), capture=cap)
    assert r.returncode == 0, r.stderr
    argv = cap.read_text()
    assert "codex exec" in argv
    assert f"--cd {tmp_path}" in argv
    assert "--sandbox workspace-write" in argv, "5d/5e needs writes; default must be workspace-write"
    assert "--output-last-message" in argv
    assert "--skip-git-repo-check" in argv


def test_exec_stdout_is_the_last_message_not_the_transcript(tmp_path):
    # stdout must be exactly the verdict carrier so it pipes into the extractor;
    # the streamed transcript is noise and must stay on stderr.
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec", str(_prompt(tmp_path)), "--cd", str(tmp_path)],
            env=_env(b, tmp_path,
                     HMAD_STUB_CODEX_LAST="STATUS: DONE",
                     HMAD_STUB_CODEX_STDOUT="[codex] thinking... running pytest..."))
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "STATUS: DONE"
    assert "[codex] thinking" not in r.stdout
    assert "[codex] thinking" in r.stderr


def test_exec_propagates_codex_exit_code(tmp_path):
    # The whole point: a non-zero codex exit reaches the caller as $?.
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec", str(_prompt(tmp_path)), "--cd", str(tmp_path)],
            env=_env(b, tmp_path, HMAD_STUB_CODEX_RC="7"))
    assert r.returncode == 7, r.stderr
    assert "codex exec rc=7" in r.stderr


def test_exec_writes_last_message_to_out_file(tmp_path):
    b = _bindir(tmp_path, ["codex"])
    out = tmp_path / "reply.txt"
    r = run(["exec", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--out", str(out)],
            env=_env(b, tmp_path, HMAD_STUB_CODEX_LAST="VERDICT: COMPLIANT"))
    assert r.returncode == 0, r.stderr
    assert out.read_text() == "VERDICT: COMPLIANT"


def test_exec_delivers_the_prompt_via_stdin(tmp_path):
    # No keystroke cap, no injection: the prompt file goes in on stdin, whole.
    b = _bindir(tmp_path, ["codex"])
    seen = tmp_path / "stdin.txt"
    pf = _prompt(tmp_path, "a" * 20000)  # far past the 8192 keystroke inline cap
    r = run(["exec", str(pf), "--cd", str(tmp_path)],
            env=_env(b, tmp_path, HMAD_STUB_STDIN_CAPTURE=str(seen)))
    assert r.returncode == 0, r.stderr
    assert seen.read_text() == "a" * 20000


def test_exec_delivers_stdin_even_through_the_timeout_path(tmp_path):
    # Regression: bash nul's a backgrounded command's stdin, so the --timeout path
    # (which backgrounds codex) once starved `codex exec -` of its piped prompt.
    # The prompt must arrive whether or not a timeout is set.
    b = _bindir(tmp_path, ["codex"])
    seen = tmp_path / "stdin.txt"
    pf = _prompt(tmp_path, "prompt through the watchdog")
    r = run(["exec", str(pf), "--cd", str(tmp_path), "--timeout", "30"],
            env=_env(b, tmp_path, HMAD_STUB_STDIN_CAPTURE=str(seen)))
    assert r.returncode == 0, r.stderr
    assert seen.read_text() == "prompt through the watchdog"


def test_exec_passes_model_through(tmp_path):
    b = _bindir(tmp_path, ["codex"])
    cap = tmp_path / "cap.txt"
    r = run(["exec", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--model", "gpt-5-codex"],
            env=_env(b, tmp_path), capture=cap)
    assert r.returncode == 0, r.stderr
    assert "--model gpt-5-codex" in cap.read_text()


def test_exec_sandbox_override(tmp_path):
    b = _bindir(tmp_path, ["codex"])
    cap = tmp_path / "cap.txt"
    r = run(["exec", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--sandbox", "read-only"],
            env=_env(b, tmp_path), capture=cap)
    assert r.returncode == 0, r.stderr
    assert "--sandbox read-only" in cap.read_text()
    assert "--sandbox workspace-write" not in cap.read_text()


def test_exec_timeout_kills_and_returns_124(tmp_path):
    # macOS has no `timeout`; the portable watchdog must fire and return 124.
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--timeout", "1"],
            env=_env(b, tmp_path, HMAD_STUB_CODEX_SLEEP="6"))
    assert r.returncode == 124, f"expected 124 (timed out), got {r.returncode}\n{r.stderr}"


def test_exec_missing_prompt_file_fails(tmp_path):
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec", str(tmp_path / "nope.txt"), "--cd", str(tmp_path)],
            env=_env(b, tmp_path))
    assert r.returncode == 2
    assert "no such prompt file" in r.stderr


def test_exec_requires_a_prompt_arg(tmp_path):
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec"], env=_env(b, tmp_path))
    assert r.returncode != 0
    assert "missing required argument" in r.stderr


def test_exec_rejects_unknown_flag(tmp_path):
    b = _bindir(tmp_path, ["codex"])
    r = run(["exec", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--sandbx", "read-only"],
            env=_env(b, tmp_path))
    assert r.returncode == 2
    assert "unknown option" in r.stderr.lower()
    assert "--sandbx" in r.stderr


def test_exec_errors_when_codex_absent(tmp_path):
    # No codex stub on PATH -> a clear operational error, not a crash.
    b = _bindir(tmp_path, [])  # empty bindir, no codex symlink
    r = run(["exec", str(_prompt(tmp_path)), "--cd", str(tmp_path)],
            env=_env(b, tmp_path))
    assert r.returncode == 2
    assert "requires the codex CLI" in r.stderr
