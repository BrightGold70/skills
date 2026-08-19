"""`exec-pane` runs a headless dispatch inside a VISIBLE Orca zsh pane.

The pane is a VIEWPORT, never a transport: nothing reads it to decide anything,
the verdict still comes from `--out`, and completion still comes from a file. That
distinction is what keeps this from being the pane dispatch path that failed on
agent identity resolution (orca#9870), tui-idle false-idle, and TUI scraping.

The verb exists mostly to make three measured traps unreachable by construction:

  1. a pane running `exec` bare is BLIND -- `exec` redirects the stream into
     `--log`, so the pane shows the echoed command and nothing more until the run
     ends (measured: t+14s, pane held one line, log held three events);
  2. `orca terminal wait --for exit` reported exitCode 0 for a command that exited
     9, so anything built on it reads every failure as a success;
  3. `wait --for exit` has no usable completion shape at all -- it either kills the
     shell (losing the scrollback) or times out.

So these tests are mostly negative: they assert the blind shape and the lying
signal CANNOT be produced, not merely that the happy path works.
"""

import os
import re
import subprocess
from pathlib import Path

import pytest

WRAPPER = Path(__file__).resolve().parent.parent / "scripts" / "hmad-dispatch.sh"
STUBS = Path(__file__).resolve().parent / "stubs"


def _bindir(tmp_path, names, orca_capture=None):
    b = tmp_path / "bin"
    b.mkdir(exist_ok=True)
    for n in names:
        dst = b / n
        dst.write_text((STUBS / n).read_text())
        dst.chmod(0o755)
    # An `orca` stub that records the command line and answers create/split with a
    # well-formed envelope. Recording argv is the point: the pane COMMAND is this
    # verb's real output, and it is what the traps live in.
    orca = b / "orca"
    orca.write_text(f'''#!/usr/bin/env bash
printf '%s\\n' "$*" >> {orca_capture or "/dev/null"}
# Stand in for the pane actually running: write the rc file the verb polls for.
if [ -n "${{HMAD_STUB_ORCA_RC_FILE:-}}" ]; then
  ( sleep 1; printf '%s\\n' "${{HMAD_STUB_ORCA_RC:-0}}" > "$HMAD_STUB_ORCA_RC_FILE" ) &
fi
case "$1 $2" in
  "terminal split")
    echo '{{"ok":true,"result":{{"split":{{"handle":"term_SPLIT","tabId":"tab1"}}}}}}' ;;
  "terminal create")
    echo '{{"ok":true,"result":{{"terminal":{{"handle":"term_NEW","tabId":"tab2","surface":"visible"}}}}}}' ;;
  *) echo '{{"ok":true,"result":{{}}}}' ;;
esac
exit 0
''')
    orca.chmod(0o755)
    return b


def _env(bindir, **extra):
    env = dict(os.environ)
    env["PATH"] = f"{bindir}:{env['PATH']}"
    env["HMAD_SUBSTRATE"] = "orca"
    env.pop("ORCA_TERMINAL_HANDLE", None)
    env.update({k: str(v) for k, v in extra.items()})
    return env


def _prompt(tmp_path, name="prompt.md"):
    p = tmp_path / name
    p.write_text("do the work")
    return p


def run(args, env=None):
    return subprocess.run(["bash", str(WRAPPER), *args],
                          capture_output=True, text=True, env=env, timeout=120)


def _pane_cmd(capture: Path) -> str:
    """The --command text handed to Orca. That string IS the deliverable."""
    assert capture.exists(), "orca was never invoked at all"
    txt = capture.read_text()
    assert "--command" in txt, txt
    return txt


def _orca_calls(capture: Path) -> str:
    """Whatever orca was asked to do -- empty string if it was never called.

    Existence and content are asserted SEPARATELY on purpose. `capture.read_text()`
    on a path that was never created raises, and the naive repair (treat a missing
    file as empty) makes "orca was never invoked" indistinguishable from "orca was
    invoked and did not do X" -- so a negative assertion would pass for the wrong
    reason. Callers that need "never invoked" assert on this returning "".
    """
    return capture.read_text() if capture.exists() else ""


# --------------------------------------------------------------------------
# trap 1 — the blind pane must be unreachable
# --------------------------------------------------------------------------

def test_pane_command_always_digests_the_log(tmp_path):
    """Blindness is the default shape, so it must be impossible to ask for it."""
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path)], env=_env(b))
    assert r.returncode == 0, r.stderr
    cmd = _pane_cmd(cap)
    assert " progress " in cmd, "pane never renders a digest -> blind pane"
    assert "kill -0" in cmd, "no liveness loop -> digest renders once and stops"


def test_a_log_is_provisioned_even_when_the_caller_omits_one(tmp_path):
    """Without a log there is nothing to digest, so `--log` cannot be optional."""
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path)], env=_env(b))
    assert r.returncode == 0, r.stderr
    assert "--log" in _pane_cmd(cap)
    assert "transcript ->" in r.stderr


# --------------------------------------------------------------------------
# traps 2 and 3 — the lying completion signal must never be consulted
# --------------------------------------------------------------------------

def test_never_calls_terminal_wait(tmp_path):
    """`terminal wait --for exit` reported exitCode 0 for `exit 9`. Consulting it
    anywhere in this verb would convert every failure into a pass."""
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path)], env=_env(b))
    assert r.returncode == 0, r.stderr
    assert "terminal wait" not in cap.read_text()


def test_rc_is_written_by_the_dispatch_itself(tmp_path):
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    out = tmp_path / "v.txt"
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--out", str(out)], env=_env(b))
    assert r.returncode == 0, r.stderr
    cmd = _pane_cmd(cap)
    assert "echo $? >" in cmd
    assert f"{out}.rc" in cmd
    assert f"rc={out}.rc" in r.stderr


def test_rc_capture_does_not_depend_on_wait_reaping_the_job(tmp_path):
    """The poll loop may observe the job exit before a `wait` runs; zsh can then
    error on the reaped job and the recorded rc would be the shell's, not the
    dispatch's. Writing rc inside the same subshell removes the race."""
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path)], env=_env(b))
    cmd = _pane_cmd(cap)
    body = cmd.split("--command", 1)[1]
    assert re.search(r"\{.*echo \$\? >.*\} *&", body), body[:400]


# --------------------------------------------------------------------------
# placement
# --------------------------------------------------------------------------

def test_default_is_a_new_tab_not_a_guessed_pane(tmp_path):
    """Guessing which pane to split would reopen identity resolution and could
    drop a shell into an AGENT's tab."""
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path)], env=_env(b))
    assert r.returncode == 0, r.stderr
    assert "terminal create" in cap.read_text()
    assert "terminal split" not in cap.read_text()
    assert r.stdout.strip() == "term_NEW"


def test_bare_split_uses_this_terminal(tmp_path):
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--split"],
            env=_env(b, ORCA_TERMINAL_HANDLE="term_ME"))
    assert r.returncode == 0, r.stderr
    assert "terminal split" in cap.read_text()
    assert "--terminal term_ME" in cap.read_text()
    assert r.stdout.strip() == "term_SPLIT"


def test_bare_split_refuses_when_this_terminal_is_unknown(tmp_path):
    """Silently falling back to a new tab would put the dispatch on a different
    surface than asked for, which is the one thing --split is for."""
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--split"],
            env=_env(b))
    assert r.returncode == 2
    assert "ORCA_TERMINAL_HANDLE" in r.stderr
    # Refused BEFORE touching Orca: no capture file at all, which `_orca_calls`
    # reports as "" rather than raising or pretending it was an empty invocation.
    assert _orca_calls(cap) == ""


def test_placement_line_names_each_handle_once(tmp_path):
    """`${v:+a}${v:-b}` expands BOTH halves when v is set (":-" substitutes only on
    UNSET), so the source handle was printed twice. Cosmetic, but the line exists
    to tell an operator which pane was split -- printed twice it reads like two."""
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--split", "term_SRC"], env=_env(b))
    assert r.returncode == 0, r.stderr
    line = next(l for l in r.stderr.splitlines() if "in pane" in l)
    assert line.count("term_SRC") == 1, line
    assert "split of term_SRC" in line

    r2 = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path)], env=_env(b))
    line2 = next(l for l in r2.stderr.splitlines() if "in pane" in l)
    assert "new tab" in line2 and "split of" not in line2


def test_split_followed_by_a_flag_does_not_eat_it_as_the_handle(tmp_path):
    """`--split` takes an OPTIONAL value, which is the parsing shape most likely
    to swallow the next flag. Eating `--poll` as a terminal handle would dispatch
    into a pane that does not exist AND silently drop the poll interval."""
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--split", "--poll", "11"], env=_env(b, ORCA_TERMINAL_HANDLE="term_ME"))
    assert r.returncode == 0, r.stderr
    calls = _orca_calls(cap)
    assert "--terminal term_ME" in calls, "the bare --split did not fall to this terminal"
    assert "--poll" not in calls.split("--command", 1)[0]
    assert "sleep 11" in _pane_cmd(cap), "--poll was swallowed"


def test_split_at_end_of_argv_is_still_bare(tmp_path):
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--split"],
            env=_env(b, ORCA_TERMINAL_HANDLE="term_ME"))
    assert r.returncode == 0, r.stderr
    assert "--terminal term_ME" in _orca_calls(cap)


def test_split_and_new_tab_are_mutually_exclusive(tmp_path):
    b = _bindir(tmp_path, ["agy"], tmp_path / "orca.txt")
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--split", "term_X", "--new-tab"],
            env=_env(b))
    assert r.returncode == 2
    assert "mutually exclusive" in r.stderr


def test_explicit_split_handle_is_used(tmp_path):
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--split", "term_OTHER", "--direction", "vertical"], env=_env(b))
    assert r.returncode == 0, r.stderr
    assert "--terminal term_OTHER" in cap.read_text()
    assert "--direction vertical" in cap.read_text()


# --------------------------------------------------------------------------
# quoting — a path with a space must not split the command line
# --------------------------------------------------------------------------

def test_paths_with_spaces_and_quotes_survive_interpolation(tmp_path):
    """The pane command is assembled as TEXT and run by a shell. An unquoted path
    with a space silently truncates the dispatch into a different command."""
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    weird = tmp_path / "a dir with spaces"
    weird.mkdir()
    prompt = weird / "it's a prompt.md"
    prompt.write_text("work")
    out = weird / "the out.txt"
    r = run(["exec-pane", "agy", str(prompt), "--cd", str(weird), "--out", str(out)],
            env=_env(b))
    assert r.returncode == 0, r.stderr
    cmd = _pane_cmd(cap)
    assert "'it'\\''s a prompt.md'" in cmd or "it'\\''s a prompt.md" in cmd
    # and the whole thing must still parse as a shell command
    check = subprocess.run(["bash", "-n", "-c", cmd.split("--command ", 1)[1]],
                           capture_output=True, text=True)
    assert check.returncode == 0, check.stderr


def test_pane_invokes_this_wrapper_by_absolute_path(tmp_path):
    """A login shell's `hmad-dispatch` need not be this file when the skill is
    installed under several roots."""
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path)], env=_env(b))
    assert str(WRAPPER) in _pane_cmd(cap)


# --------------------------------------------------------------------------
# guards
# --------------------------------------------------------------------------

def test_refuses_outside_orca_rather_than_running_headless(tmp_path):
    """A silent headless fallback leaves the caller watching for a pane that never
    appears -- the same blindness, with a success exit code on top."""
    b = _bindir(tmp_path, ["agy"], tmp_path / "orca.txt")
    env = _env(b); env["HMAD_SUBSTRATE"] = "cmux"
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path)], env=env)
    assert r.returncode == 2
    assert "substrate" in r.stderr


@pytest.mark.parametrize("args,msg", [
    (["--direction", "sideways"], "horizontal|vertical"),
    (["--poll", "zero"], "must be an integer"),
    (["--poll", "0"], "must be >= 1"),
])
def test_rejects_bad_pane_options(tmp_path, args, msg):
    b = _bindir(tmp_path, ["agy"], tmp_path / "orca.txt")
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), *args], env=_env(b))
    assert r.returncode == 2
    assert msg in r.stderr


def test_focus_with_split_is_refused_not_silently_dropped(tmp_path):
    """`terminal split` has no focus flag. Accepting --focus and ignoring it is
    the silent flag drop this wrapper bans everywhere else -- the caller believes
    they asked for focus and never learns otherwise."""
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--split", "term_X", "--focus"], env=_env(b))
    assert r.returncode == 2
    assert "--focus" in r.stderr and "new tab only" in r.stderr
    assert _orca_calls(cap) == ""


def test_focus_reaches_terminal_create_on_the_new_tab_path(tmp_path):
    """The other half of the same guard: refusing it on split is only defensible
    if it actually does something on the path it belongs to."""
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--focus"],
            env=_env(b))
    assert r.returncode == 0, r.stderr
    assert "--focus" in _orca_calls(cap)


def test_effort_is_agy_only(tmp_path):
    b = _bindir(tmp_path, ["codex"], tmp_path / "orca.txt")
    r = run(["exec-pane", "codex", str(_prompt(tmp_path)), "--effort", "high"], env=_env(b))
    assert r.returncode == 2
    assert "agy-only" in r.stderr


def test_unknown_agent_and_missing_prompt_are_refused(tmp_path):
    b = _bindir(tmp_path, ["agy"], tmp_path / "orca.txt")
    assert run(["exec-pane", "gemini", str(_prompt(tmp_path))], env=_env(b)).returncode == 2
    assert run(["exec-pane", "agy", str(tmp_path / "nope.md")], env=_env(b)).returncode == 2


def test_wait_blocks_on_the_rc_file_and_returns_that_code(tmp_path):
    """--wait must adopt `exec`'s contract: stdout is the response, rc is the
    dispatch's own -- taken from the file, never from `terminal wait`.

    The rc file is written by the STUB, standing in for the pane, because the verb
    deliberately clears any pre-existing rc before waiting (see the stale-rc test).
    Pre-creating it here would have tested nothing but the clear.
    """
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    out = tmp_path / "v.txt"
    out.write_text("ASSESSMENT: READY_TO_MERGE\n")
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--out", str(out), "--wait", "--wait-timeout", "40"],
            env=_env(b, HMAD_STUB_ORCA_RC_FILE=str(tmp_path / "v.txt.rc"),
                     HMAD_STUB_ORCA_RC="5"))
    assert r.returncode == 5, r.stderr
    assert r.stdout.strip() == "ASSESSMENT: READY_TO_MERGE"


def test_a_stale_rc_from_a_previous_dispatch_cannot_satisfy_wait(tmp_path):
    """`--out` paths are templated per feature+module and the documented
    no_verdict remedy re-dispatches to the SAME path, so a leftover rc is the
    normal case, not the exotic one. If it survived, `--wait` would return the
    PREVIOUS run's exit code instantly while the new pane was still working."""
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    out = tmp_path / "v.txt"
    rc_file = tmp_path / "v.txt.rc"
    rc_file.write_text("0\n")          # a previous dispatch's success
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--out", str(out), "--wait", "--wait-timeout", "4"], env=_env(b))
    assert r.returncode == 124, r.stderr      # timed out, did NOT return the stale 0
    assert not rc_file.exists() or rc_file.read_text().strip() == ""


def test_wait_times_out_without_claiming_the_dispatch_failed(tmp_path):
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--wait", "--wait-timeout", "4"], env=_env(b))
    assert r.returncode == 124
    assert "still live" in r.stderr
