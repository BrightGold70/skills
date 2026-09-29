"""Phase 5d contracts for dispatching Grok through the exec caller."""

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from grokfixtures import (
    ac_4_10_stream,
    f0_text,
    f_beat,
    f_decoy,
    f_notext,
    f_notooltext,
    f_spaced,
    f_trunc,
    f_trunc_nostatus,
    farm_env,
    usr_bin_farm,
    wrapper_fn_in_env,
)
from test_hmad_dispatch import SKILL, _bindir, run, run_fn


HOSTILE_PROMPT = (
    "# [agent](https://example.invalid/a*[?]) **review**\n"
    "line with 'quotes', $(), `ticks`, and [glob*]\n"
    "===HMAD-DISPATCH-BOUNDARY=== inside the request\n"
)
CLAUDE_NAMES = (
    "CLAUDECODE",
    "CLAUDE_CODE_ENTRYPOINT",
    "CLAUDE_CODE_SESSION_ID",
    "CLAUDE_EFFORT",
)
CLAUDE_ENV = {name: f"hostile {name} [*]" for name in CLAUDE_NAMES}


@pytest.fixture(autouse=True)
def _clean_caller_env(monkeypatch):
    """Give every subprocess only the CLAUDE* and backend names its test sets."""
    clean = {name: value for name, value in os.environ.items()
             if not name.startswith("CLAUDE") and name != "HPW_AGENT_BACKEND"}
    for name in set(os.environ) - set(clean):
        monkeypatch.delenv(name)


def _case(tmp_path, *, agent="grok", stream=None, options=(), env=None, out=False):
    """Run the public exec verb with a real prompt and isolated CLI stub."""
    workspace = tmp_path / "work [*] marker"
    workspace.mkdir()
    prompt = tmp_path / "prompt [*] marker.md"
    prompt.write_text(HOSTILE_PROMPT, encoding="utf-8")
    log = tmp_path / "run [*] marker.ndjson"
    capture = tmp_path / "argv.txt"
    copied = tmp_path / "copied-prompt.txt"
    backend = tmp_path / "backend.txt"
    claude = tmp_path / "claude-names.txt"
    output = tmp_path / "final.txt"
    bindir = _bindir(tmp_path, [agent])
    stream_path = tmp_path / "stream.ndjson"
    stream_path.write_text(f0_text() if stream is None else stream, encoding="utf-8")
    child_env = {
        "_BINDIR": str(bindir),
        "HMAD_STUB_HOSTILE": "all",
        "HMAD_STUB_GROK_STREAM": str(stream_path),
        "HMAD_STUB_GROK_PROMPT_CAPTURE": str(copied),
        "HMAD_STUB_ENV_CAPTURE": str(backend),
        "HMAD_STUB_CLAUDE_ENV_CAPTURE": str(claude),
        **(env or {}),
    }
    args = ["exec", agent, str(prompt), "--cd", str(workspace), "--log", str(log)]
    if out:
        args += ["--out", str(output)]
    args += list(options)
    result = run(args, env=child_env, capture=capture)
    return result, {
        "workspace": workspace, "prompt": prompt, "log": log,
        "capture": capture, "copied": copied, "backend": backend,
        "claude": claude, "output": output,
    }


def test_exec_grok_argv_carries_prompt_file_and_headless_flags(tmp_path):
    r, p = _case(tmp_path)
    assert p["capture"].exists(), (
        f"exec grok must launch the Grok CLI with a prompt file: {r.stderr}"
    )
    argv = p["capture"].read_text(encoding="utf-8").strip()
    assert argv.startswith("grok "), f"exec must call grok: {argv}"
    assert f"--cwd {p['workspace']}" in argv, f"exec must pass the worktree: {argv}"
    assert "--always-approve" in argv, f"exec must request headless approval: {argv}"
    assert "--output-format streaming-json" in argv, f"exec must request streaming JSON: {argv}"
    assert "--prompt-file " in argv and "-p" not in argv.split(), (
        f"exec must pass a file instead of an inline prompt: {argv}"
    )
    assert "--single" not in argv.split(), f"exec must not request a single turn flag: {argv}"
    assert p["copied"].exists(), "the Grok stub must receive --prompt-file"
    copied = p["copied"].read_text(encoding="utf-8")
    assert copied.startswith(HOSTILE_PROMPT), "exec must preserve the hostile caller prompt"
    assert copied.endswith("\n===HMAD-DISPATCH-BOUNDARY===\n"), (
        "exec must append the dispatch boundary to Grok's prompt file"
    )


@pytest.mark.parametrize("options,expected", [
    (["--model", "m1", "--effort", "high", "--sandbox", "s1"], True),
    ([], False),
], ids=["given", "none"])
def test_exec_grok_translates_model_effort_sandbox(tmp_path, options, expected):
    r, p = _case(tmp_path, options=options)
    assert p["capture"].exists(), f"exec grok must reach the CLI to translate options: {r.stderr}"
    argv = p["capture"].read_text(encoding="utf-8")
    for flag, value in (("--model", "m1"), ("--reasoning-effort", "high"),
                        ("--sandbox", "s1")):
        assert (f"{flag} {value}" in argv) is expected, (
            f"exec grok must {'pass' if expected else 'omit'} {flag}: {argv}"
        )
    assert " --effort " not in argv, f"exec grok must translate effort: {argv}"


def test_exec_grok_child_env_has_no_claude_names(tmp_path):
    r, p = _case(tmp_path, env=CLAUDE_ENV)
    assert p["claude"].exists(), f"exec grok must launch a child for env capture: {r.stderr}"
    assert p["claude"].read_text(encoding="utf-8") == "", (
        "exec grok must scrub every exported CLAUDE* name in the child"
    )
    assert p["backend"].read_text(encoding="utf-8") == "HPW_AGENT_BACKEND=claude\n", (
        "exec grok must default HPW_AGENT_BACKEND to claude in its child"
    )


@pytest.mark.parametrize("incoming,expected", [("", "claude"), ("gemini", "gemini")],
                         ids=["empty", "gemini"])
def test_exec_grok_hpw_backend_default(tmp_path, incoming, expected):
    r, p = _case(tmp_path, env={"HPW_AGENT_BACKEND": incoming})
    assert p["backend"].exists(), f"exec grok must launch a child for backend capture: {r.stderr}"
    assert p["backend"].read_text(encoding="utf-8") == f"HPW_AGENT_BACKEND={expected}\n", (
        "exec grok must default empty backend and preserve an explicit value"
    )


def test_exec_grok_leaves_the_wrapper_shell_env_intact(tmp_path):
    bindir = _bindir(tmp_path, ["grok"])
    prompt = tmp_path / "prompt.md"
    prompt.write_text(HOSTILE_PROMPT, encoding="utf-8")
    log = tmp_path / "run.ndjson"
    stream = tmp_path / "stream.ndjson"
    stream.write_text(f0_text(), encoding="utf-8")
    capture = tmp_path / "argv.txt"
    script = (
        f"if _cmd_exec grok {shlex.quote(str(prompt))} --cd {shlex.quote(str(tmp_path))} "
        f"--log {shlex.quote(str(log))} >/dev/null 2>&1; then rc=0; else rc=$?; fi\n"
        "printf 'rc=%s\\n' \"$rc\"\n"
        "compgen -e | grep '^CLAUDE' | LC_ALL=C sort"
    )
    r = run_fn(script, env={"_BINDIR": str(bindir), "HMAD_STUB_HOSTILE": "all",
                            "HMAD_STUB_GROK_STREAM": str(stream), **CLAUDE_ENV}, capture=capture)
    assert "rc=0\n" in r.stdout, f"_cmd_exec grok must complete in the wrapper shell: {r.stderr}"
    assert r.stdout.splitlines()[1:] == sorted(CLAUDE_NAMES), (
        "_cmd_exec grok must preserve CLAUDE* exports in the caller shell"
    )
    assert capture.exists() and "grok " in capture.read_text(encoding="utf-8"), (
        "_cmd_exec must have launched the Grok child"
    )


@pytest.mark.parametrize("agent,backend", [("codex", "codex"), ("agy", "gemini")],
                         ids=["codex", "agy"])
def test_exec_codex_and_agy_keep_claude_env(tmp_path, agent, backend):
    r, p = _case(tmp_path, agent=agent, env=CLAUDE_ENV)
    assert r.returncode == 0, f"exec {agent} must still run: {r.stderr}"
    assert p["capture"].exists(), f"exec {agent} must launch its existing CLI"
    assert p["claude"].read_text(encoding="utf-8").splitlines() == sorted(CLAUDE_NAMES), (
        f"exec {agent} must preserve the caller's CLAUDE* exports"
    )
    assert p["backend"].read_text(encoding="utf-8") == f"HPW_AGENT_BACKEND={backend}\n", (
        f"exec {agent} must keep its existing backend default"
    )


def test_exec_grok_oversize_prompt_is_not_refused(tmp_path):
    limit = int(subprocess.check_output(["getconf", "ARG_MAX"], text=True).strip())
    r, p = _case(tmp_path)
    p["prompt"].write_bytes(HOSTILE_PROMPT.encode() + b"x" * (limit + 1))
    r = run(["exec", "grok", str(p["prompt"]), "--cd", str(p["workspace"]),
             "--log", str(p["log"])], env={"_BINDIR": str(p["capture"].parent / "bin"),
                                            "HMAD_STUB_HOSTILE": "all",
                                            "HMAD_STUB_GROK_STREAM": str(tmp_path / "stream.ndjson"),
                                            "HMAD_STUB_GROK_PROMPT_CAPTURE": str(p["copied"])},
            capture=p["capture"])
    assert "OVERSIZE" not in r.stderr and r.returncode != 2, (
        f"exec grok must transport an ARG_MAX-sized prompt by file: {r.stderr}"
    )
    assert p["copied"].stat().st_size >= limit + 1, (
        "exec grok must deliver the entire oversized prompt file"
    )


def test_exec_grok_without_grok_on_path_returns_2(tmp_path):
    farm = usr_bin_farm(tmp_path, absent=(), stubs=())
    prompt = tmp_path / "prompt.md"
    prompt.write_text(HOSTILE_PROMPT, encoding="utf-8")
    env = farm_env(farm, HMAD_STUB_HOSTILE="all")
    absent = subprocess.run(["bash", "-c", "command -v grok"], env=env,
                            text=True, capture_output=True)
    assert absent.returncode != 0, "the isolated PATH must omit grok"
    r = wrapper_fn_in_env(f"_cmd_exec grok {shlex.quote(str(prompt))}", env)
    assert r.returncode == 2, "exec grok without its CLI must return 2"
    assert "exec requires the grok CLI on PATH" in r.stderr, (
        f"exec grok must name the missing CLI: {r.stderr}"
    )


def test_exec_unknown_agent_names_the_three_agent_set(tmp_path):
    prompt = tmp_path / "prompt.md"
    prompt.write_text(HOSTILE_PROMPT, encoding="utf-8")
    r = run(["exec", "gpt", str(prompt)])
    assert r.returncode == 2, "exec must reject an unknown agent with rc 2"
    assert "codex|agy|grok" in r.stderr, (
        f"exec must name all three accepted agents: {r.stderr}"
    )


@pytest.mark.parametrize("verb", ["exec-pane", "launch", "pin", "verify", "resolve"],
                         ids=["exec-pane", "launch", "pin", "verify", "resolve"])
def test_pane_verbs_still_refuse_grok(tmp_path, verb):
    bindir = _bindir(tmp_path, ["orca"])
    prompt = tmp_path / "prompt.md"
    prompt.write_text(HOSTILE_PROMPT, encoding="utf-8")
    args = [verb, "grok"]
    if verb == "exec-pane":
        args.append(str(prompt))
    elif verb == "pin":
        args.append("term_hostile_[*]")
    r = run(args, substrate="orca", env={"_BINDIR": str(bindir),
                                         "HMAD_STUB_HOSTILE": "all"})
    assert r.returncode == 2, f"{verb} must refuse grok with rc 2: {r.stderr}"
    assert "unknown agent" in r.stderr, f"{verb} must name the rejected agent: {r.stderr}"


def test_exec_grok_f0_prints_the_final_message(tmp_path):
    r, p = _case(tmp_path, out=True)
    assert r.stdout == "STATUS: DONE\n", (
        f"exec grok must print only F0's final message: {r.stderr}"
    )
    assert r.returncode == 0, "exec grok must return success on a complete stream"
    assert p["output"].read_bytes() == b"STATUS: DONE\n", (
        "exec grok must write the same final message to --out"
    )
    assert "stopReason=end_turn" in r.stderr, "exec grok must report the end reason"


@pytest.mark.parametrize("stream", [f_beat, f_spaced], ids=["beat", "spaced"])
def test_exec_grok_beat_and_spaced_match_f0(tmp_path, stream):
    r, _ = _case(tmp_path, stream=stream())
    assert r.stdout == "STATUS: DONE\n", (
        f"exec grok must parse {stream.__name__} as F0: {r.stderr}"
    )


def test_exec_grok_decoys_are_not_recovered(tmp_path):
    r, p = _case(tmp_path, stream=f_decoy(), out=True)
    assert r.stdout == "All done.\n", (
        f"exec grok must print only text events, excluding verdict decoys: {r.stderr}"
    )
    extracted = subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "h_mad_extract_verdict.py"),
         str(p["output"]), "--key", "STATUS"], text=True, capture_output=True,
    )
    assert extracted.returncode == 2 and "STATUS:" not in extracted.stdout, (
        "a Grok thought/tool/raw-line decoy must not become a STATUS verdict"
    )


def test_exec_grok_no_text_takes_the_empty_path(tmp_path):
    r, _ = _case(tmp_path, stream=f_notext())
    assert r.returncode == 3 and r.stdout == "", (
        f"exec grok must reject a complete stream without text: {r.stderr}"
    )
    assert "EMPTY final message" in r.stderr, "exec grok must explain the empty report"


def test_exec_grok_truncated_recovers_the_verdict(tmp_path):
    r, p = _case(tmp_path, stream=f_trunc(), out=True)
    assert r.returncode == 3, "exec grok must mark a stream without end as incomplete"
    assert "TRUNCATED — no end event" in r.stderr, (
        f"exec grok must identify the truncated stream: {r.stderr}"
    )
    assert "verdict recovered from log" in r.stderr, (
        "exec grok must label its structured recovery"
    )
    assert r.stdout == "STATUS: DONE\n", "exec grok must recover F-TRUNC's text verdict"
    assert p["output"].read_text(encoding="utf-8") == "STATUS: DONE\n", (
        "exec grok must persist the recovered verdict"
    )


def test_exec_grok_empty_path_names_the_last_tool(tmp_path):
    r, p = _case(tmp_path, stream=f_trunc_nostatus(), out=True)
    assert "2 tool calls completed; last tool: search_replace completed" in r.stderr, (
        f"exec grok must name the last completed tool on EMPTY: {r.stderr}"
    )
    assert r.returncode == 3 and r.stdout == "", (
        "exec grok must return EMPTY without a recovered verdict"
    )
    assert not p["output"].exists(), "exec grok must not write --out without a verdict"


def test_exec_grok_reads_only_its_own_region(tmp_path):
    r, p = _case(tmp_path, stream=f_trunc_nostatus())
    p["log"].write_text(f0_text(), encoding="utf-8")
    r = run(["exec", "grok", str(p["prompt"]), "--cd", str(p["workspace"]),
             "--log", str(p["log"])], env={"_BINDIR": str(tmp_path / "bin"),
                                            "HMAD_STUB_HOSTILE": "all",
                                            "HMAD_STUB_GROK_STREAM": str(tmp_path / "stream.ndjson")})
    assert r.returncode == 3 and r.stdout == "", (
        f"exec grok must not recover a prior dispatch's F0 verdict: {r.stderr}"
    )


def test_exec_grok_watchdog_kill_reports_recovery(tmp_path):
    r, p = _case(tmp_path, stream=f_trunc(), options=["--timeout", "1"],
                 env={"HMAD_STUB_GROK_SLEEP": "5"})
    assert r.returncode == 124, f"exec grok watchdog must retain rc 124: {r.stderr}"
    assert "a verdict WAS recovered" in r.stderr, (
        "exec grok must distinguish recovered work after watchdog kill"
    )


def test_exec_grok_omits_the_last_tool_line_without_tool_calls(tmp_path):
    r, _ = _case(tmp_path, stream=f_notooltext())
    assert r.returncode == 3, f"exec grok must mark missing text as EMPTY: {r.stderr}"
    assert "EMPTY final message" in r.stderr, "exec grok must explain missing text"
    assert "tool calls completed" not in r.stderr, (
        "exec grok must omit last-tool detail when no tool call occurred"
    )


def test_exec_grok_counts_completed_not_seen_ids(tmp_path):
    r, _ = _case(tmp_path, stream=ac_4_10_stream())
    assert r.returncode == 3, f"exec grok must take EMPTY on a textless stream: {r.stderr}"
    assert "0 tool calls completed; last tool: search_replace pending" in r.stderr, (
        "exec grok must count completed tool IDs, not merely seen IDs"
    )


def test_exec_grok_without_jq_is_not_parsed(tmp_path):
    farm = usr_bin_farm(tmp_path, absent=("jq",), stubs=("grok",))
    prompt = tmp_path / "prompt.md"
    prompt.write_text(HOSTILE_PROMPT, encoding="utf-8")
    stream = tmp_path / "stream.ndjson"
    stream.write_text(f_trunc(), encoding="utf-8")
    env = farm_env(farm, HMAD_STUB_HOSTILE="all", HMAD_STUB_GROK_STREAM=str(stream))
    absent = subprocess.run(["bash", "-c", "command -v jq"], env=env,
                            text=True, capture_output=True)
    assert absent.returncode != 0, "the isolated PATH must omit jq"
    r = wrapper_fn_in_env(
        f"_cmd_exec grok {shlex.quote(str(prompt))} --cd {shlex.quote(str(tmp_path))} "
        f"--log {shlex.quote(str(tmp_path / 'run.ndjson'))}", env,
    )
    assert "grok stream not parsed — jq not on PATH" in r.stderr, (
        f"exec grok must diagnose missing jq separately: {r.stderr}"
    )
    assert "TRUNCATED" not in r.stderr and "command not found" not in r.stderr, (
        "missing jq must not be misreported as a truncated stream or shell failure"
    )


def test_exec_grok_with_failing_jq_is_not_parsed(tmp_path):
    bindir = _bindir(tmp_path, ["grok"])
    jq = bindir / "jq"
    if jq.exists() or jq.is_symlink():
        jq.unlink()
    jq.write_text("#!/bin/sh\nexit 127\n", encoding="utf-8")
    jq.chmod(0o755)
    prompt = tmp_path / "prompt.md"
    prompt.write_text(HOSTILE_PROMPT, encoding="utf-8")
    stream = tmp_path / "stream.ndjson"
    stream.write_text(f_trunc(), encoding="utf-8")
    r = run(["exec", "grok", str(prompt), "--cd", str(tmp_path), "--log",
             str(tmp_path / "run.ndjson")], env={"_BINDIR": str(bindir),
                                               "HMAD_STUB_HOSTILE": "all",
                                               "HMAD_STUB_GROK_STREAM": str(stream)})
    assert "grok stream not parsed — jq failed" in r.stderr, (
        f"exec grok must diagnose jq's failing exit: {r.stderr}"
    )
    assert "TRUNCATED" not in r.stderr, "failing jq must not imply a truncated stream"


def _ambient_bash():
    """The bash the operator's `#!/usr/bin/env bash` resolves to, outside the test PATH.

    The isolated PATH (`bindir:/usr/bin:/bin`) would run the wrapper under macOS's
    /bin/bash 3.2, which drops non-identifier environment names on import and so
    hides D3 entirely. The positive control in the D3 test fails loudly if this
    bash does too.
    """
    found = shutil.which("bash")
    assert found, "no bash on the ambient PATH"
    return found


def test_exec_grok_child_env_has_no_non_identifier_claude_names(tmp_path):
    """D3 / FR-3: the scrubbed class is every name matching `^CLAUDE`, not only the
    names bash can list. `CLAUDE-HYPHEN` and `CLAUDE.DOT` are valid in an environment
    and invisible to `compgen -e`."""
    bindir = _bindir(tmp_path, [])
    (bindir / "bash").symlink_to(_ambient_bash())
    capture = tmp_path / "child-env.txt"
    stream = tmp_path / "stream.ndjson"
    stream.write_text(f0_text(), encoding="utf-8")
    # A python stub, so the capture reads the process environment directly rather
    # than through a bash that may itself have dropped the names.
    stub = bindir / "grok"
    stub.write_text(
        f"#!{sys.executable}\n"
        "import os, sys\n"
        "names = sorted(n for n in os.environ if n.startswith(('CLAUDE', 'KEEP')))\n"
        f"open({str(capture)!r}, 'w').write(''.join(n + '\\n' for n in names))\n"
        f"sys.stdout.write(open({str(stream)!r}).read())\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)
    prompt = tmp_path / "prompt.md"
    prompt.write_text(HOSTILE_PROMPT, encoding="utf-8")
    r = run(["exec", "grok", str(prompt), "--cd", str(tmp_path), "--log",
             str(tmp_path / "run.ndjson")],
            env={"_BINDIR": str(bindir), **CLAUDE_ENV,
                 "CLAUDE-HYPHEN": "leak1", "CLAUDE.DOT": "leak2",
                 "KEEP-HYPHEN": "kept", "KEEP_PLAIN": "kept"})
    assert capture.exists(), f"exec grok must launch the child: {r.stderr}"
    names = capture.read_text(encoding="utf-8").splitlines()
    # Positive control: non-CLAUDE names, identifier or not, still reach the child.
    assert "KEEP-HYPHEN" in names and "KEEP_PLAIN" in names, (
        f"the child must still inherit every non-CLAUDE name (control): {names}"
    )
    assert [n for n in names if n.startswith("CLAUDE")] == [], (
        f"exec grok must scrub every ^CLAUDE name from the child, identifier or not: {names}"
    )
    assert r.returncode == 0, r.stderr


def test_exec_grok_beat_never_splits_an_event(tmp_path):
    """D4: the heartbeat shares the transcript with grok's stdout. A grok event
    written in two write() calls, with a pause longer than the beat interval
    between them, must arrive intact, and the completed run must not read as
    TRUNCATED."""
    lines = f0_text().splitlines()
    end = lines[-1]
    assert json.loads(end)["type"] == "end", "F0's last event must be `end`"
    half = len(end) // 2
    parts = [tmp_path / "p1", tmp_path / "p2", tmp_path / "p3"]
    parts[0].write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    parts[1].write_text(end[:half], encoding="utf-8")
    parts[2].write_text(end[half:] + "\n", encoding="utf-8")
    bindir = _bindir(tmp_path, [])
    stub = bindir / "grok"
    # Beats land on a line boundary during the first sleep (the control that a
    # beat is still written at all) and inside the event during the second.
    stub.write_text(
        "#!/bin/bash\n"
        f"cat {shlex.quote(str(parts[0]))}\n"
        "sleep 2\n"
        f"cat {shlex.quote(str(parts[1]))}\n"
        "sleep 3\n"
        f"cat {shlex.quote(str(parts[2]))}\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)
    prompt = tmp_path / "prompt.md"
    prompt.write_text(HOSTILE_PROMPT, encoding="utf-8")
    log = tmp_path / "run.ndjson"
    r = run(["exec", "grok", str(prompt), "--cd", str(tmp_path), "--log", str(log)],
            env={"_BINDIR": str(bindir), "HMAD_EXEC_HEARTBEAT_SEC": "1"})
    text = log.read_text(encoding="utf-8")
    assert "#hmad-beat" in text, "the heartbeat must still beat into the transcript"
    assert end in text.splitlines(), (
        "the split `end` event must arrive intact:\n"
        + "\n".join(line[:120] for line in text.splitlines()[-6:])
    )
    assert "TRUNCATED" not in r.stderr, f"a completed run must not read as TRUNCATED: {r.stderr}"
    assert r.returncode == 0, r.stderr
    assert r.stdout == "STATUS: DONE\n", r.stderr
