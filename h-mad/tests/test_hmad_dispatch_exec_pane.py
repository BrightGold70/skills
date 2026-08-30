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
import threading
import time
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
    # Isolate the slot registry PER TEST. Without this the default location is
    # `<git-root>/.h-mad/panes`, and the suite wrote `term_NEW.busy` / `term_SPLIT.cd`
    # into the real repo -- invisible to `git status` because `.h-mad/` is ignored,
    # and able to hand a PRODUCTION dispatch a handle that only ever existed in a
    # stub. Caught by looking for the leak rather than by any assertion.
    env.setdefault("HMAD_PANE_SLOT_DIR", str(Path(bindir).parent / "slots"))
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


def test_effort_is_forwarded_for_codex_too(tmp_path):
    """exec-pane only wraps `exec`, which now maps codex effort to
    `-c model_reasoning_effort`. Refusing it here would make the pane path the
    only one that cannot run a 5d/5e dispatch at its pinned effort."""
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["codex"], cap)
    r = run(["exec-pane", "codex", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--effort", "high"], env=_env(b))
    assert r.returncode == 0, r.stderr
    assert "--effort 'high'" in _pane_cmd(cap)


def test_unknown_agent_and_missing_prompt_are_refused(tmp_path):
    b = _bindir(tmp_path, ["agy"], tmp_path / "orca.txt")
    assert run(["exec-pane", "gemini", str(_prompt(tmp_path))], env=_env(b)).returncode == 2
    assert run(["exec-pane", "agy", str(tmp_path / "nope.md")], env=_env(b)).returncode == 2


def repr_sh(x):
    """Single-quote a JSON blob for a bash `echo`."""
    return "'" + x + "'"


# --------------------------------------------------------------------------
# the slot pool — reuse an idle h-mad pane instead of piling up tabs
# --------------------------------------------------------------------------

def _slots(env):
    return Path(env["HMAD_PANE_SLOT_DIR"])


def _orca_with_live(tmp_path, live_handles, capture):
    """An orca stub whose `terminal list` reports the given live handles."""
    b = tmp_path / "bin"
    b.mkdir(exist_ok=True)
    d = b / "agy"; d.write_text((STUBS / "agy").read_text()); d.chmod(0o755)
    terms = ",".join('{"handle":"%s"}' % h for h in live_handles)
    script = "\n".join([
        "#!/usr/bin/env bash",
        'printf "%s\\n" "$*" >> ' + str(capture),
        'case "$1 $2" in',
        '  "terminal list")   echo ' + repr_sh('{"ok":true,"result":{"terminals":[' + terms + ']}}') + ' ;;',
        '  "terminal send")   echo ' + repr_sh('{"ok":true,"result":{}}') + ' ;;',
        '  "terminal split")  echo ' + repr_sh('{"ok":true,"result":{"split":{"handle":"term_SPLIT"}}}') + ' ;;',
        '  "terminal create") echo ' + repr_sh('{"ok":true,"result":{"terminal":{"handle":"term_NEW"}}}') + ' ;;',
        '  *) echo ' + repr_sh('{"ok":true,"result":{}}') + ' ;;',
        'esac',
        'exit 0',
        '',
    ])
    (b / "orca").write_text(script)
    (b / "orca").chmod(0o755)
    return b


def test_a_new_pane_registers_itself_as_a_busy_slot(tmp_path):
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    env = _env(b)
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path)], env=env)
    assert r.returncode == 0, r.stderr
    d = _slots(env)
    assert (d / "term_NEW.busy").is_dir()
    assert (d / "term_NEW.cd").read_text() == str(tmp_path)


def test_an_idle_slot_is_reused_instead_of_creating_a_tab(tmp_path):
    """The whole point: one h-mad pane per worktree, reused -- not a new tab per
    dispatch piling up until a human closes them by hand."""
    cap = tmp_path / "orca.txt"
    b = _orca_with_live(tmp_path, ["term_IDLE"], cap)
    env = _env(b)
    d = _slots(env); d.mkdir(parents=True, exist_ok=True)
    (d / "term_IDLE.idle").write_text("")
    (d / "term_IDLE.cd").write_text(str(tmp_path))
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path)], env=env)
    assert r.returncode == 0, r.stderr
    calls = _orca_calls(cap)
    assert "terminal send" in calls and "--terminal term_IDLE" in calls
    assert "terminal create" not in calls
    assert "--enter" in calls
    assert r.stdout.strip() == "term_IDLE"
    assert "reused idle pane" in r.stderr
    assert not (d / "term_IDLE.idle").exists()
    assert (d / "term_IDLE.busy").is_dir()


def test_a_slot_for_a_different_worktree_is_not_reused(tmp_path):
    """A pane's cwd is its worktree; dispatching one repo's audit into another
    repo's pane would run in the wrong tree."""
    cap = tmp_path / "orca.txt"
    b = _orca_with_live(tmp_path, ["term_IDLE"], cap)
    env = _env(b)
    d = _slots(env); d.mkdir(parents=True, exist_ok=True)
    (d / "term_IDLE.idle").write_text("")
    (d / "term_IDLE.cd").write_text("/somewhere/else")
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path)], env=env)
    assert r.returncode == 0, r.stderr
    assert "terminal create" in _orca_calls(cap)


def test_a_slot_whose_pane_is_gone_is_reaped_not_dispatched_into(tmp_path):
    """Panes get closed. Sending into a dead handle looks like a dispatch that
    silently never ran, and nothing else would ever clean the entry up."""
    cap = tmp_path / "orca.txt"
    b = _orca_with_live(tmp_path, ["term_SOMETHING_ELSE"], cap)
    env = _env(b)
    d = _slots(env); d.mkdir(parents=True, exist_ok=True)
    (d / "term_DEAD.idle").write_text("")
    (d / "term_DEAD.cd").write_text(str(tmp_path))
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path)], env=env)
    assert r.returncode == 0, r.stderr
    calls = _orca_calls(cap)
    assert "--terminal term_DEAD" not in calls
    assert "terminal create" in calls
    assert not (d / "term_DEAD.idle").exists(), "stale slot was not reaped"
    assert not (d / "term_DEAD.cd").exists()


def test_a_busy_slot_is_never_handed_out(tmp_path):
    cap = tmp_path / "orca.txt"
    b = _orca_with_live(tmp_path, ["term_BUSY"], cap)
    env = _env(b)
    d = _slots(env); d.mkdir(parents=True, exist_ok=True)
    (d / "term_BUSY.busy").mkdir()
    (d / "term_BUSY.cd").write_text(str(tmp_path))
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path)], env=env)
    assert r.returncode == 0, r.stderr
    assert "--terminal term_BUSY" not in _orca_calls(cap)
    assert "terminal create" in _orca_calls(cap)


def test_two_dispatches_cannot_claim_the_same_slot(tmp_path):
    """Phase 5 parallel fanout dispatches concurrently, so this race is real. The
    claim is `mkdir`, which is atomic; a check-then-write would send two different
    dispatches into ONE pane and the second would overwrite the first."""
    cap = tmp_path / "orca.txt"
    b = _orca_with_live(tmp_path, ["term_IDLE"], cap)
    env = _env(b)
    d = _slots(env); d.mkdir(parents=True, exist_ok=True)
    (d / "term_IDLE.idle").write_text("")
    (d / "term_IDLE.cd").write_text(str(tmp_path))
    procs = [subprocess.Popen(
        ["bash", str(WRAPPER), "exec-pane", "agy", str(_prompt(tmp_path, f"p{i}.md")),
         "--cd", str(tmp_path)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env) for i in range(2)]
    outs = [p.communicate() for p in procs]
    assert all(p.returncode == 0 for p in procs), outs
    reused = [o for o, e in outs if o.strip() == "term_IDLE"]
    assert len(reused) == 1, f"slot handed out {len(reused)} times"


def test_the_pane_releases_its_own_slot_when_it_finishes(tmp_path):
    """Release is the pane's job because only the pane knows when it is done, and
    it must come LAST -- releasing before the DONE marker prints would let the next
    dispatch overwrite a verdict a human is still reading."""
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    env = _env(b)
    run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path)], env=env)
    cmd = _pane_cmd(cap)
    assert "ORCA_TERMINAL_HANDLE" in cmd
    assert ".idle" in cmd and ".busy" in cmd
    assert cmd.index("HMAD-PANE-DONE") < cmd.index('"$ORCA_TERMINAL_HANDLE".idle')


def test_no_reuse_forces_a_fresh_pane(tmp_path):
    cap = tmp_path / "orca.txt"
    b = _orca_with_live(tmp_path, ["term_IDLE"], cap)
    env = _env(b)
    d = _slots(env); d.mkdir(parents=True, exist_ok=True)
    (d / "term_IDLE.idle").write_text("")
    (d / "term_IDLE.cd").write_text(str(tmp_path))
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path), "--no-reuse"], env=env)
    assert r.returncode == 0, r.stderr
    assert "terminal create" in _orca_calls(cap)
    assert "terminal send" not in _orca_calls(cap)


def test_explicit_split_bypasses_the_pool(tmp_path):
    """--split names a surface on purpose; silently redirecting to a pooled pane
    would put the dispatch somewhere the caller did not ask for."""
    cap = tmp_path / "orca.txt"
    b = _orca_with_live(tmp_path, ["term_IDLE"], cap)
    env = _env(b)
    d = _slots(env); d.mkdir(parents=True, exist_ok=True)
    (d / "term_IDLE.idle").write_text("")
    (d / "term_IDLE.cd").write_text(str(tmp_path))
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--split", "term_TARGET"], env=env)
    assert r.returncode == 0, r.stderr
    assert "terminal split" in _orca_calls(cap)
    assert "terminal send" not in _orca_calls(cap)


def test_a_finishing_slot_is_waited_for_and_then_reused(tmp_path):
    """THE window this closes.

    `--wait` returns when the rc file lands, ~1-2s before the pane finishes
    rendering and releases its slot. A caller dispatching again in that gap used
    to create a second pane. Now the claim waits for a slot that announced it is
    finishing -- which costs no VERDICT latency, because it happens before the
    dispatch starts rather than after it ends.
    """
    cap = tmp_path / "orca.txt"
    b = _orca_with_live(tmp_path, ["term_IDLE"], cap)
    env = _env(b)
    d = _slots(env); d.mkdir(parents=True, exist_ok=True)
    (d / "term_IDLE.busy").mkdir()
    (d / "term_IDLE.cd").write_text(str(tmp_path))
    (d / "term_IDLE.finishing").write_text("")

    # the pane frees its slot shortly after the dispatch starts looking
    def free_it():
        time.sleep(1.5)
        (d / "term_IDLE.finishing").unlink()
        (d / "term_IDLE.busy").rmdir()
        (d / "term_IDLE.idle").write_text("")
    t = threading.Thread(target=free_it); t.start()
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--reuse-wait", "15"], env=env)
    t.join()
    assert r.returncode == 0, r.stderr
    assert "reused idle pane" in r.stderr
    assert "terminal create" not in _orca_calls(cap)
    assert r.stdout.strip() == "term_IDLE"


def test_a_genuinely_busy_slot_is_not_waited_for(tmp_path):
    """The other half, and the reason the marker exists at all. Phase 5 parallel
    fanout dispatches concurrently into panes that are really working; waiting on
    those would add the reuse-wait to every parallel dispatch for nothing. No
    `.finishing` marker means no wait."""
    cap = tmp_path / "orca.txt"
    b = _orca_with_live(tmp_path, ["term_BUSY"], cap)
    env = _env(b)
    d = _slots(env); d.mkdir(parents=True, exist_ok=True)
    (d / "term_BUSY.busy").mkdir()
    (d / "term_BUSY.cd").write_text(str(tmp_path))
    t0 = time.time()
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--reuse-wait", "30"], env=env)
    elapsed = time.time() - t0
    assert r.returncode == 0, r.stderr
    assert "terminal create" in _orca_calls(cap)
    assert elapsed < 10, f"waited {elapsed:.1f}s on a slot that never claimed to be finishing"


def test_waiting_gives_up_and_creates_rather_than_hanging(tmp_path):
    """A pane can die between dropping the marker and releasing. The dispatch must
    still happen -- a stuck marker cannot become an indefinite stall."""
    cap = tmp_path / "orca.txt"
    b = _orca_with_live(tmp_path, ["term_STUCK"], cap)
    env = _env(b)
    d = _slots(env); d.mkdir(parents=True, exist_ok=True)
    (d / "term_STUCK.busy").mkdir()
    (d / "term_STUCK.cd").write_text(str(tmp_path))
    (d / "term_STUCK.finishing").write_text("")
    t0 = time.time()
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--reuse-wait", "3"], env=env)
    elapsed = time.time() - t0
    assert r.returncode == 0, r.stderr
    assert "did not free within 3s" in r.stderr
    assert "terminal create" in _orca_calls(cap)
    assert elapsed < 20


def test_a_finishing_slot_whose_pane_died_stops_the_wait_early(tmp_path):
    """If the pane is gone, the slot is never coming. Burning the full reuse-wait
    on it delays a dispatch that was always going to need a new pane."""
    cap = tmp_path / "orca.txt"
    b = _orca_with_live(tmp_path, ["term_SOMETHING_ELSE"], cap)
    env = _env(b)
    d = _slots(env); d.mkdir(parents=True, exist_ok=True)
    (d / "term_GONE.busy").mkdir()
    (d / "term_GONE.cd").write_text(str(tmp_path))
    (d / "term_GONE.finishing").write_text("")
    t0 = time.time()
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--reuse-wait", "30"], env=env)
    elapsed = time.time() - t0
    assert r.returncode == 0, r.stderr
    assert "terminal create" in _orca_calls(cap)
    assert elapsed < 10, f"waited {elapsed:.1f}s for a dead pane's slot"


def test_the_pane_marks_itself_finishing_as_soon_as_rc_lands(tmp_path):
    """The marker has to go down with the rc write, inside the same subshell --
    not after the final render, which is the very interval it exists to cover."""
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    env = _env(b)
    run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path)], env=env)
    cmd = _pane_cmd(cap)
    assert ".finishing" in cmd
    subshell = cmd.split("&", 1)[0]
    assert "echo $? >" in subshell and ".finishing" in subshell, subshell[:300]
    # and it is cleared on release, before the slot goes idle
    assert cmd.index('"$ORCA_TERMINAL_HANDLE".finishing 2>/dev/null; rmdir') < cmd.index('.idle')


def test_reuse_wait_zero_disables_the_wait(tmp_path):
    cap = tmp_path / "orca.txt"
    b = _orca_with_live(tmp_path, ["term_IDLE"], cap)
    env = _env(b)
    d = _slots(env); d.mkdir(parents=True, exist_ok=True)
    (d / "term_IDLE.busy").mkdir()
    (d / "term_IDLE.cd").write_text(str(tmp_path))
    (d / "term_IDLE.finishing").write_text("")
    t0 = time.time()
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--reuse-wait", "0"], env=env)
    assert r.returncode == 0, r.stderr
    assert "terminal create" in _orca_calls(cap)
    assert time.time() - t0 < 10


def test_reuse_wait_rejects_a_non_integer(tmp_path):
    b = _bindir(tmp_path, ["agy"], tmp_path / "orca.txt")
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--reuse-wait", "soon"], env=_env(b))
    assert r.returncode == 2
    assert "must be an integer" in r.stderr


def _orca_live_from_file(tmp_path, live_file, capture):
    """orca stub that reads its live-handle list from a file at CALL time.

    A static stub cannot express "the pane was alive when we started waiting and
    died while we waited", which is the only path the give-up check covers -- a
    pane that was already dead is rejected before the loop is ever entered. Two
    surviving mutants hid behind exactly that gap.
    """
    b = tmp_path / "bin"
    b.mkdir(exist_ok=True)
    d = b / "agy"; d.write_text((STUBS / "agy").read_text()); d.chmod(0o755)
    script = "\n".join([
        "#!/usr/bin/env bash",
        'printf "%s\\n" "$*" >> ' + str(capture),
        'case "$1 $2" in',
        '  "terminal list")',
        '    hs=""',
        '    while read -r h; do [ -n "$h" ] && hs="$hs{\\"handle\\":\\"$h\\"},"; done < ' + str(live_file),
        '    echo "{\\"ok\\":true,\\"result\\":{\\"terminals\\":[${hs%,}]}}" ;;',
        '  "terminal send")   echo ' + repr_sh('{"ok":true,"result":{}}') + ' ;;',
        '  "terminal create") echo ' + repr_sh('{"ok":true,"result":{"terminal":{"handle":"term_NEW"}}}') + ' ;;',
        '  *) echo ' + repr_sh('{"ok":true,"result":{}}') + ' ;;',
        'esac',
        'exit 0',
        '',
    ])
    (b / "orca").write_text(script)
    (b / "orca").chmod(0o755)
    return b


def test_a_pane_that_dies_DURING_the_wait_stops_it_early(tmp_path):
    """The give-up check reads the live-handle list, which is captured once before
    the loop. Against that stale list a pane that dies mid-wait still looks alive,
    its `.finishing` marker is never cleared by anyone, and the loop burns the full
    --reuse-wait. Only a stub whose liveness CHANGES can catch that."""
    cap = tmp_path / "orca.txt"
    live_file = tmp_path / "live.txt"
    live_file.write_text("term_DYING\n")
    b = _orca_live_from_file(tmp_path, live_file, cap)
    env = _env(b)
    d = _slots(env); d.mkdir(parents=True, exist_ok=True)
    (d / "term_DYING.busy").mkdir()
    (d / "term_DYING.cd").write_text(str(tmp_path))
    (d / "term_DYING.finishing").write_text("")

    def kill_it():
        time.sleep(2.5)
        live_file.write_text("term_OTHER\n")     # the pane is gone; slot never frees
    t = threading.Thread(target=kill_it); t.start()
    t0 = time.time()
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--reuse-wait", "40"], env=env)
    elapsed = time.time() - t0
    t.join()
    assert r.returncode == 0, r.stderr
    assert "terminal create" in _orca_calls(cap)
    assert elapsed < 25, f"waited {elapsed:.1f}s for a pane that died mid-wait"


def test_a_dead_panes_finishing_marker_is_reaped(tmp_path):
    """Nothing else ever clears it, so leaving it makes EVERY later dispatch in
    this worktree pay the full --reuse-wait for a slot that cannot arrive."""
    cap = tmp_path / "orca.txt"
    b = _orca_with_live(tmp_path, ["term_ALIVE"], cap)
    env = _env(b)
    d = _slots(env); d.mkdir(parents=True, exist_ok=True)
    (d / "term_GONE.busy").mkdir()
    (d / "term_GONE.cd").write_text(str(tmp_path))
    (d / "term_GONE.finishing").write_text("")
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path)], env=env)
    assert r.returncode == 0, r.stderr
    assert not (d / "term_GONE.finishing").exists(), "dead marker survived"
    assert not (d / "term_GONE.busy").exists()
    assert not (d / "term_GONE.cd").exists()


def test_a_finishing_slot_in_another_worktree_is_not_waited_for(tmp_path):
    """It can never be claimed by this dispatch, so waiting on it is pure delay --
    and it would delay EVERY dispatch in every other worktree."""
    cap = tmp_path / "orca.txt"
    b = _orca_with_live(tmp_path, ["term_OTHERWT"], cap)
    env = _env(b)
    d = _slots(env); d.mkdir(parents=True, exist_ok=True)
    (d / "term_OTHERWT.busy").mkdir()
    (d / "term_OTHERWT.cd").write_text("/a/different/worktree")
    (d / "term_OTHERWT.finishing").write_text("")
    t0 = time.time()
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--reuse-wait", "30"], env=env)
    elapsed = time.time() - t0
    assert r.returncode == 0, r.stderr
    assert "terminal create" in _orca_calls(cap)
    assert elapsed < 10, f"waited {elapsed:.1f}s on another worktree's slot"


def test_wait_polls_the_rc_file_sub_second(tmp_path):
    """The complaint that started this: a dispatch finished and the result was
    picked up seconds-to-minutes later. `exec` itself returns within ~1s of the
    agent's result (measured), so any perceptible delay is the WAIT, not the work.
    A 2s rc poll was adding more than the whole rest of the tail."""
    src = WRAPPER.read_text()
    body = src.split("_cmd_exec_pane()", 1)[1]
    assert "sleep 0.5" in body, "the rc poll is no longer sub-second"
    assert "sleep 2;" not in body


def test_wait_timeout_is_still_measured_in_seconds(tmp_path):
    """The poll counter switched to half-seconds; if the timeout comparison did not
    switch with it, --wait-timeout 20 would fire after 10s and report a timeout on
    a dispatch that was working fine."""
    cap = tmp_path / "orca.txt"
    b = _bindir(tmp_path, ["agy"], cap)
    import time as _t
    t0 = _t.time()
    r = run(["exec-pane", "agy", str(_prompt(tmp_path)), "--cd", str(tmp_path),
             "--wait", "--wait-timeout", "6"], env=_env(b))
    elapsed = _t.time() - t0
    assert r.returncode == 124
    assert elapsed >= 5.0, f"timed out after only {elapsed:.1f}s; unit mismatch"


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
