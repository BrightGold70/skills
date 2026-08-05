"""RED tests for the exec-path-hardening leaf units (Tasks 1--4)."""

import base64
import json
import os
import re
import shlex
import subprocess
import time
from pathlib import Path

import pytest

from test_hmad_dispatch import _bindir, run

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "hmad-dispatch.sh"


def _function(name: str) -> str:
    """Extract one top-level shell function, without sourcing the dispatch main."""
    source = SCRIPT.read_text()
    starts = list(re.finditer(r"(?m)^([A-Za-z_][A-Za-z0-9_]*)\(\) \{", source))
    for i, match in enumerate(starts):
        if match.group(1) == name:
            end = starts[i + 1].start() if i + 1 < len(starts) else len(source)
            return source[match.start():end]
    return ""


def _call(name, *args, env=None, stdin=None, extra=""):
    body = _function(name)
    command = f"{body}\n{extra}\n{name} {shlex.join([str(a) for a in args])}"
    e = dict(os.environ)
    if env:
        e.update({k: str(v) for k, v in env.items()})
    return subprocess.run(["bash", "-c", command], input=stdin, text=True,
                          capture_output=True, env=e)


def _payload(entries, truncated=False):
    return json.dumps({"ok": True, "result": {"truncated": truncated, "worktrees": entries}})


def _entry(path, selector, comment=None, active=False, omit_comment=False):
    value = {"path": path, "worktreeId": selector, "isActive": active}
    if not omit_comment:
        value["comment"] = comment
    return value


def _skill_doc() -> str:
    return (Path(__file__).resolve().parent.parent / "SKILL.md").read_text(encoding="utf-8")


def test_skill_docs_describe_exec_heartbeat_knob():
    """AC-12.1 MUST_FAIL: document the default heartbeat and disabling value."""
    doc = _skill_doc()
    match = re.search(r"HMAD_EXEC_HEARTBEAT_SEC", doc)
    assert match is not None
    window = doc[match.start() : match.start() + 400].lower()
    assert "120" in window
    assert re.search(r"\b0\b", window)
    assert "disabl" in window


def test_skill_docs_describe_log_append_without_codex_truncation_claim():
    """AC-12.2 MUST_FAIL: document append semantics and no codex truncation claim."""
    doc = _skill_doc()
    lowered = doc.lower()
    assert re.search(r"--log.{0,250}append|append.{0,250}--log", lowered, re.DOTALL)
    assert not re.search(
        r"codex.{0,180}--log.{0,180}(?:truncat|overwrite)|"
        r"--log.{0,180}codex.{0,180}(?:truncat|overwrite)",
        lowered,
        re.DOTALL,
    )


def test_skill_frontmatter_name_and_description_are_unchanged():
    """REGRESSION AC-12.3: skill identity metadata remains byte-for-byte unchanged."""
    frontmatter = _skill_doc().split("---", 2)[1]
    assert frontmatter == (
        "\n"
        "name: h-mad\n"
        "description: Orchestrate the 7-phase H-MAD (Hawk Multi-Agents Development) workflow "
        "end-to-end. Standalone — no external skill dependencies (spec-kit, b-mad, or pdca). "
        "All phase protocols are built-in. Project-agnostic; splices project-specific Axis B "
        "invariants from `<PROJECT_ROOT>/.h-mad/invariants.md` into audit prompts at dispatch "
        "time. Use when user invokes /h-mad \"<feature>\", /h-mad do \"<feature>\", /h-mad "
        "status, or /h-mad reset \"<feature>\".\n"
    )


STAMP = "h-mad: codex skills · running · 4m⟦/h-mad⟧"


def test_ac_1_1_empty_comment_emits_stamp():
    r = _call("_exec_comment_compose", "", STAMP)
    assert r.returncode == 0
    assert r.stdout == STAMP


def test_ac_1_2_human_comment_gets_one_appended_stamp():
    r = _call("_exec_comment_compose", "Fixing issue", STAMP)
    assert r.stdout == f"Fixing issue · {STAMP}"


def test_ac_1_3_handoff_text_is_preserved_byte_for_byte():
    handoff = "handoff: slug · state · next: x"
    r = _call("_exec_comment_compose", handoff, STAMP)
    assert handoff in r.stdout
    assert r.stdout.endswith(STAMP)


def test_ac_1_4_five_composes_replace_one_existing_span():
    comment = "human note"
    for state in ["start", "beat-1", "beat-2", "beat-3", "exit"]:
        stamp = f"h-mad: codex skills · {state}⟦/h-mad⟧"
        comment = _call("_exec_comment_compose", comment, stamp).stdout
    assert comment.count("h-mad: ") == 1
    assert comment.count("⟦/h-mad⟧") == 1
    assert len(comment) == len("human note · h-mad: codex skills · exit⟦/h-mad⟧")


def test_ac_1_5_embedded_span_is_replaced_in_place():
    r = _call("_exec_comment_compose", "pre h-mad: old⟦/h-mad⟧ post", STAMP)
    assert r.stdout == f"pre {STAMP} post"


def test_ac_1_6_malformed_half_span_is_preserved_and_stamp_appended():
    current = "pre h-mad: old without terminator"
    r = _call("_exec_comment_compose", current, STAMP)
    assert r.stdout == f"{current} · {STAMP}"


def test_ac_1_7_newlines_and_tabs_round_trip():
    current = "line one\n\tline two\nline three"
    r = _call("_exec_comment_compose", current, STAMP)
    assert r.stdout == f"{current} · {STAMP}"


def test_ac_2_2_stateful_orca_comment_round_trip(tmp_path):
    state = tmp_path / "orca.state"
    b = _bindir(tmp_path, ["orca"])
    e = {"_BINDIR": b, "HMAD_STUB_ORCA_STATE": state}
    first = run(["worktree-comment", "path:/x", "X"], substrate="orca", env=e)
    assert first.returncode == 0, first.stderr
    ps = run(["worktree-ps"], substrate="orca", env=e)
    assert ps.returncode == 0, ps.stderr
    assert json.loads(ps.stdout)["worktrees"][0]["comment"] == "X"


def test_ac_2_3_stateful_orca_preserves_newline_and_tab(tmp_path):
    state = tmp_path / "orca.state"
    b = _bindir(tmp_path, ["orca"])
    e = {"_BINDIR": b, "HMAD_STUB_ORCA_STATE": state}
    value = "line one\n\tline two"
    first = run(["worktree-comment", "path:/x", value], substrate="orca", env=e)
    assert first.returncode == 0, first.stderr
    ps = run(["worktree-ps"], substrate="orca", env=e)
    assert json.loads(ps.stdout)["worktrees"][0]["comment"] == value


def test_ac_2_4_stateful_orca_paths_are_isolated(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    a, z = tmp_path / "a.state", tmp_path / "z.state"
    for state, value in [(a, "A"), (z, "Z")]:
        e = {"_BINDIR": b, "HMAD_STUB_ORCA_STATE": state}
        assert run(["worktree-comment", "path:/x", value], substrate="orca", env=e).returncode == 0
    for state, value in [(a, "A"), (z, "Z")]:
        e = {"_BINDIR": b, "HMAD_STUB_ORCA_STATE": state}
        ps = run(["worktree-ps"], substrate="orca", env=e)
        assert json.loads(ps.stdout)["worktrees"][0]["comment"] == value


def _target(tmp_path, entries, cd, *, truncated=False, stdin=None, extra_env=None):
    b = _bindir(tmp_path, ["orca"])
    e = {"PATH": f"{b}:/usr/bin:/bin", "HMAD_STUB_ORCA_WT_PS_STDOUT": _payload(entries, truncated)}
    if extra_env:
        e.update(extra_env)
    # The future resolver uses _exec_run; this shim lets the leaf test exercise
    # its command shape while the RED implementation is still absent.
    shim = "_exec_run() { shift; \"$@\"; }"
    return _call("_exec_wt_target", cd, env=e, stdin=stdin, extra=shim)


def test_ac_3_1_exact_path_returns_selector_and_comment(tmp_path):
    comment = "current"
    r = _target(tmp_path, [_entry("/x/repo", "repo", comment)], "/x/repo")
    assert r.returncode == 0
    assert r.stdout.splitlines() == ["repo", base64.b64encode(comment.encode()).decode()]


def test_ac_3_2_subdirectory_resolves_enclosing_worktree(tmp_path):
    r = _target(tmp_path, [_entry("/x/repo", "repo", "c")], "/x/repo/src/deep")
    assert r.stdout.splitlines()[0] == "repo"


def test_ac_3_3_sibling_prefix_uses_boundary_match(tmp_path):
    entries = [_entry("/x/repo", "repo", "wrong"), _entry("/x/repo-other", "repo-other", "right")]
    r = _target(tmp_path, entries, "/x/repo-other")
    assert r.stdout.splitlines()[0] == "repo-other"


def test_ac_3_4_unmatched_cd_falls_back_to_active_entry(tmp_path):
    r = _target(tmp_path, [_entry("/x/other", "active-id", "active", active=True)], "/x/nope")
    assert r.stdout.splitlines()[0] == "active-id"


def test_ac_3_5_no_usable_entry_is_silent_failure(tmp_path):
    r = _target(tmp_path, [_entry("/x/other", "other", "c")], "/x/nope")
    assert r.returncode == 1
    assert r.stdout == ""


def test_ac_3_6_matching_entry_survives_truncated_payload(tmp_path):
    r = _target(tmp_path, [_entry("/x/repo", "repo", "c")], "/x/repo", truncated=True)
    assert r.returncode == 0


@pytest.mark.parametrize("entry", [
    _entry("/x/repo", "null-id", None),
    _entry("/x/repo", "absent-id", omit_comment=True),
])
def test_ac_3_7_null_or_absent_comment_decodes_empty(tmp_path, entry):
    r = _target(tmp_path, [entry], "/x/repo")
    assert r.returncode == 0
    assert base64.b64decode(r.stdout.splitlines()[1]).decode() == ""


def test_ac_3_8_comment_newline_and_tab_is_byte_exact(tmp_path):
    comment = "one\n\ttwo"
    r = _target(tmp_path, [_entry("/x/repo", "repo", comment)], "/x/repo")
    assert base64.b64decode(r.stdout.splitlines()[1]).decode() == comment


def test_ac_3_9_hanging_orca_read_is_bounded(tmp_path):
    started = time.monotonic()
    r = _target(tmp_path, [_entry("/x/repo", "repo", "c")], "/x/repo",
                extra_env={"HMAD_STUB_ORCA_SLEEP": "5"})
    assert time.monotonic() - started < 3
    assert r.returncode == 1


def test_ac_3_10_read_preserves_caller_stdin_and_gives_orca_eof(tmp_path):
    seen = tmp_path / "orca.stdin"
    sentinel = "caller sentinel must remain unread\n"
    r = _target(tmp_path, [_entry("/x/repo", "repo", "c")], "/x/repo",
                stdin=sentinel, extra_env={"HMAD_STUB_ORCA_STDIN_CAPTURE": seen})
    assert r.returncode == 0
    assert r.stdout.splitlines()[0] == "repo"
    assert r.stderr == ""
    assert seen.read_text() == ""


def _stamp(tmp_path, kind, *, target="repo\n\n", substrate="orca", extra_env=None,
          stdin=None, extra=""):
    b = _bindir(tmp_path, ["orca"])
    env = {"PATH": f"{b}:/usr/bin:/bin", "HMAD_SUBSTRATE": substrate,
           "HMAD_STUB_ORCA_EXIT": "0"}
    if extra_env:
        env.update(extra_env)
    stub = f"_exec_wt_target() {{ printf %s {shlex.quote(target)}; }}\n{extra}"
    return _call("_exec_stamp", kind, "codex", "skills", str(tmp_path),
                 "0", "DONE", env=env, stdin=stdin, extra=stub)


def test_ac_4_1_exit_stamp_contains_agent_rc_and_verdict(tmp_path):
    cap = tmp_path / "calls"
    r = _stamp(tmp_path, "exit", extra_env={"HMAD_STUB_CAPTURE": cap})
    assert r.returncode == 0
    assert r.stdout == ""
    text = cap.read_text() if cap.exists() else ""
    assert "codex" in text and "rc=0" in text and "DONE" in text


def test_ac_4_2_start_and_beat_contain_agent_and_label(tmp_path):
    for kind in ("start", "beat"):
        case_dir = tmp_path / kind
        case_dir.mkdir()
        cap = case_dir / "calls"
        r = _stamp(case_dir, kind, extra_env={"HMAD_STUB_CAPTURE": cap})
        assert r.returncode == 0
        assert r.stdout == ""
        text = cap.read_text() if cap.exists() else ""
        assert "codex" in text and "skills" in text


def test_ac_4_3_cmux_makes_zero_orca_calls(tmp_path):
    cap = tmp_path / "calls"
    r = _stamp(tmp_path, "start", substrate="cmux", extra_env={"HMAD_STUB_CAPTURE": cap})
    assert r.returncode == 0
    assert not cap.exists() or cap.read_text() == ""


def test_ac_4_4_orca_failure_is_silent_success(tmp_path):
    r = _stamp(tmp_path, "start", extra_env={"HMAD_STUB_ORCA_EXIT": "7"})
    assert r.returncode == 0
    assert r.stdout == "" and r.stderr == ""


def test_ac_4_5_hanging_orca_is_bounded_and_silent(tmp_path):
    started = time.monotonic()
    r = _stamp(tmp_path, "start", extra_env={"HMAD_STUB_ORCA_SLEEP": "5"})
    assert time.monotonic() - started < 3
    assert r.returncode == 0


def test_ac_4_6_stamp_writes_no_stdout(tmp_path):
    r = _stamp(tmp_path, "exit")
    assert r.returncode == 0
    assert r.stdout == ""


def test_ac_4_7_worktree_set_carries_comment(tmp_path):
    cap = tmp_path / "calls"
    r = _stamp(tmp_path, "exit", extra_env={"HMAD_STUB_CAPTURE": cap})
    assert r.returncode == 0
    text = cap.read_text() if cap.exists() else ""
    assert "worktree set" in text and "--comment" in text
    assert "codex" in text and "rc=0" in text and "DONE" in text


def test_ac_4_8_write_preserves_caller_stdin_and_gives_orca_eof(tmp_path):
    seen = tmp_path / "orca.stdin"
    r = _stamp(tmp_path, "start", stdin="write sentinel\n",
               extra_env={"HMAD_STUB_ORCA_STDIN_CAPTURE": seen})
    assert r.returncode == 0
    assert seen.read_text() == ""


# --- Task 6--10 wiring REDs -------------------------------------------------

def _exec_dispatch(tmp_path, *, substrate="orca", rc="0", last="STATUS: DONE",
                   sleep=None, timeout="6", state=None, capture=None, **extra):
    """Run the public exec path with only the test agent/substrate binaries."""
    names = ["codex", "orca"] if substrate == "orca" else ["codex", "cmux"]
    b = _bindir(tmp_path, names)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("wire test prompt")
    env = {"_BINDIR": b, "HMAD_STUB_CODEX_RC": rc,
           "HMAD_STUB_CODEX_LAST": last}
    if sleep is not None:
        env["HMAD_STUB_CODEX_SLEEP"] = sleep
    if state is not None:
        env["HMAD_STUB_ORCA_STATE"] = state
    env.update(extra)
    # The stateful Orca stub advertises its synthetic worktree at /x.
    # codex's stub does not require that directory to exist, so use that
    # advertised path to exercise the resolver's non-active target.
    cd_dir = "/x" if substrate == "orca" else str(tmp_path)
    args = ["exec", "codex", str(prompt), "--cd", cd_dir]
    if timeout is not None:
        args += ["--timeout", timeout]
    return run(args, substrate=substrate, env=env,
                capture=capture)


def _orca_calls(path):
    return path.read_text().splitlines() if path.exists() else []


def test_stamp_targets_the_cd_worktree_not_active(tmp_path):
    cap = tmp_path / "calls"
    entries = [_entry("/x/repo", "repo-id", "keep-me"),
               _entry("/x/other", "active", "active", active=True)]
    b = _bindir(tmp_path, ["orca"])
    env = {"PATH": f"{b}:/usr/bin:/bin", "HMAD_SUBSTRATE": "orca",
           "HMAD_STUB_ORCA_WT_PS_STDOUT": _payload(entries),
           "HMAD_STUB_CAPTURE": cap}
    # Keep the resolver and bounded runner intact: this is a call-site pin, not
    # a leaf test with a resolver shim.
    extra = _function("_exec_wt_target") + "\n" + _function("_exec_run")
    r = _call("_exec_stamp", "start", "codex", "skills", "/x/repo/src",
              env=env, extra=extra)
    assert r.returncode == 0, r.stderr
    sets = [line for line in _orca_calls(cap) if "worktree set" in line]
    assert sets, "_exec_stamp did not call worktree set"
    assert "--worktree repo-id" in sets[-1]
    assert "--worktree active" not in sets[-1]


def test_stamp_abandons_write_when_resolver_fails(tmp_path):
    cap = tmp_path / "calls"
    r = _stamp(tmp_path, "start", target="", extra_env={
        "HMAD_STUB_CAPTURE": cap})
    assert r.returncode == 0
    assert not [line for line in _orca_calls(cap) if "worktree set" in line]


def test_start_stamp_is_written_before_the_agent_runs(tmp_path):
    cap = tmp_path / "calls"
    state = tmp_path / "orca.state"
    r = _exec_dispatch(tmp_path, state=state, capture=cap)
    assert r.returncode == 0, r.stderr
    calls = _orca_calls(cap)
    worktree = next((i for i, line in enumerate(calls) if "worktree set" in line), None)
    codex = next((i for i, line in enumerate(calls) if line.startswith("codex ")), None)
    assert worktree is not None, "no pre-agent worktree set was recorded"
    assert codex is not None and worktree < codex


def test_start_stamp_is_silent_on_cmux(tmp_path):
    cap = tmp_path / "calls"
    r = _exec_dispatch(tmp_path, substrate="cmux", capture=cap)
    assert r.returncode == 0, r.stderr
    assert not any("worktree set" in line for line in _orca_calls(cap))


def test_exit_stamp_carries_agent_rc_and_verdict(tmp_path):
    cap = tmp_path / "calls"
    state = tmp_path / "orca.state"
    r = _exec_dispatch(tmp_path, state=state, capture=cap, rc="7", last="VERDICT: DONE")
    assert r.returncode == 7, r.stderr
    sets = [line for line in _orca_calls(cap) if "worktree set" in line]
    assert any("codex" in line and "rc=7" in line and "DONE" in line for line in sets)


def test_exit_stamp_is_written_for_empty_final_message(tmp_path):
    cap = tmp_path / "calls"
    state = tmp_path / "orca.state"
    r = _exec_dispatch(tmp_path, state=state, capture=cap, last="")
    assert r.returncode == 3, r.stderr
    assert any("worktree set" in line and "rc=3" in line for line in _orca_calls(cap))


def test_heartbeat_stamps_across_three_intervals(tmp_path):
    cap = tmp_path / "calls"
    state = tmp_path / "orca.state"
    r = _exec_dispatch(tmp_path, state=state, capture=cap, sleep="3.3",
                       HMAD_EXEC_HEARTBEAT_SEC="1")
    assert r.returncode == 0, r.stderr
    beats = [line for line in _orca_calls(cap) if "running" in line and "worktree set" in line]
    assert len(beats) >= 3, f"expected at least three heartbeat writes, got {beats!r}"


def test_heartbeat_elapsed_values_are_monotonic(tmp_path):
    cap = tmp_path / "calls"
    state = tmp_path / "orca.state"
    r = _exec_dispatch(tmp_path, state=state, capture=cap, sleep="3.2",
                       HMAD_EXEC_HEARTBEAT_SEC="1")
    assert r.returncode == 0, r.stderr
    values = [int(m.group(1)) for line in _orca_calls(cap)
              if "worktree set" in line and "running" in line
              for m in [re.search(r"running · (\d+)s", line)] if m]
    # `values == sorted(values)` alone is satisfied by a CONSTANT sequence, and that
    # is exactly how a hardcoded `running · 0m` shipped through a green suite, a
    # clean mutation sweep and five wire-scoped reverts: [0, 0, 0] is sorted. The
    # heartbeat exists to tell "still working" from "died", so the elapsed field must
    # actually advance — require strict growth across the run, not mere ordering.
    assert len(values) >= 3, values
    assert values == sorted(values), values
    assert values[-1] > values[0], values


def test_heartbeat_without_timeout_keeps_the_same_cadence(tmp_path):
    cap = tmp_path / "calls"
    state = tmp_path / "orca.state"
    r = _exec_dispatch(tmp_path, state=state, capture=cap, sleep="3.2",
                       timeout=None, HMAD_EXEC_HEARTBEAT_SEC="1")
    assert r.returncode == 0, r.stderr
    assert len([line for line in _orca_calls(cap)
                if "worktree set" in line and "running" in line]) >= 3


def test_zero_heartbeat_still_has_start_and_exit_but_no_beats(tmp_path):
    cap = tmp_path / "calls"
    state = tmp_path / "orca.state"
    r = _exec_dispatch(tmp_path, state=state, capture=cap, sleep="1.2",
                       HMAD_EXEC_HEARTBEAT_SEC="0")
    assert r.returncode == 0, r.stderr
    lines = _orca_calls(cap)
    writes = [line for line in lines if "worktree set" in line]
    # `running` cannot discriminate a beat from a start: the START stamp's own state
    # text is `running · 0m`, so an assertion that no write contains "running" fails
    # against a correct implementation. Count the writes instead — with the heartbeat
    # disabled there must be EXACTLY the two lifecycle stamps (start, exit), and a
    # single leaked beat pushes the count to 3 over this 1.2s run.
    assert len(writes) == 2, writes
    assert any("running" in line for line in writes), writes   # the start stamp
    assert any("rc=" in line for line in writes), writes        # the exit stamp


def test_heartbeat_preserves_handoff_and_one_span_after_three_beats(tmp_path):
    cap = tmp_path / "calls"
    state = tmp_path / "orca.state"
    state.write_text("handoff: keep-me")
    r = _exec_dispatch(tmp_path, state=state, capture=cap, sleep="3.3",
                       HMAD_EXEC_HEARTBEAT_SEC="1")
    assert r.returncode == 0, r.stderr
    comment = state.read_text()
    assert "handoff: keep-me" in comment
    assert comment.count("h-mad: ") == 1
    assert comment.count("⟦/h-mad⟧") == 1


def test_heartbeat_shorter_than_stamp_timeout_terminates(tmp_path):
    cap = tmp_path / "calls"
    state = tmp_path / "orca.state"
    started = time.monotonic()
    r = _exec_dispatch(tmp_path, state=state, capture=cap, sleep="1.3",
                       timeout="5", HMAD_EXEC_HEARTBEAT_SEC="1",
                       HMAD_EXEC_STAMP_TIMEOUT="2")
    assert time.monotonic() - started < 5
    assert r.returncode == 0, r.stderr
    assert any("running" in line for line in _orca_calls(cap))


def test_heartbeat_keeps_inherited_stdin_intact(tmp_path):
    cap = tmp_path / "calls"
    state = tmp_path / "orca.state"
    seen = tmp_path / "agent.stdin"
    r = _exec_dispatch(tmp_path, state=state, capture=cap, sleep="3.2",
                       HMAD_EXEC_HEARTBEAT_SEC="1", HMAD_STUB_STDIN_CAPTURE=seen)
    assert r.returncode == 0, r.stderr
    assert "wire test prompt" in seen.read_text()
    assert "===HMAD-DISPATCH-BOUNDARY===" in seen.read_text()
    assert any("running" in line for line in _orca_calls(cap))


def test_exec_run_without_heartbeat_never_stamps_from_environment(tmp_path):
    stamps = tmp_path / "stamps"
    extra = f'_exec_stamp() {{ printf x >> {shlex.quote(str(stamps))}; }}'
    body = _function("_exec_run")
    r = subprocess.run(["bash", "-c", f"{body}\n{extra}\n_exec_run '' bash -c 'sleep 3'"],
                       capture_output=True, text=True,
                       env={**os.environ, "HMAD_EXEC_HEARTBEAT_SEC": "1"})
    assert r.returncode == 0, r.stderr
    assert not stamps.exists() or stamps.read_text() == ""


def test_exit_notify_fires_once_with_rc(tmp_path):
    cap = tmp_path / "calls"
    b = _bindir(tmp_path, ["codex", "cmux"])
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("notify wire")
    r = run(["exec", "codex", str(prompt), "--cd", str(tmp_path)], substrate="cmux",
            env={"_BINDIR": b, "HMAD_STUB_CODEX_RC": "7",
                 "HMAD_STUB_CODEX_LAST": "VERDICT: DONE"}, capture=cap)
    assert r.returncode == 7, r.stderr
    notifies = [line for line in _orca_calls(cap) if line.startswith("cmux notify ")]
    assert len(notifies) == 1
    assert "rc=7" in notifies[0] and "DONE" in notifies[0]


def test_notify_failure_does_not_change_exec_rc_or_stdout(tmp_path):
    cap = tmp_path / "calls"
    b = _bindir(tmp_path, ["codex", "cmux"])
    failing = b / "cmux"
    failing.unlink()
    failing.write_text("#!/bin/sh\nprintf 'cmux %s\\n' \"$*\" >> \"$HMAD_STUB_CAPTURE\"\nexit 9\n")
    failing.chmod(0o755)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("notify failure")
    r = run(["exec", "codex", str(prompt), "--cd", str(tmp_path)], substrate="cmux",
            env={"_BINDIR": b, "HMAD_STUB_CODEX_RC": "4",
                 "HMAD_STUB_CODEX_LAST": "STATUS: DONE"}, capture=cap)
    assert r.returncode == 4
    assert r.stdout.strip() == "STATUS: DONE"
    assert any("cmux notify" in line for line in _orca_calls(cap))


# --- Spec FR-4 non-interference: the invariant the whole feature rests on. ------
# Phase 6a gap analysis found these three spec ACs only PARTIALLY covered: existing
# tests proved a stamp writes no stdout and that a failing notify preserves rc, but
# nothing compared a full dispatch's stdout byte-for-byte with the surfaces on vs
# off, and nothing swept every rc value with EVERY surface failing at once.

def _stdout_with_surfaces(tmp_path, sub_dir, *, substrate, rc="0", broken=False):
    """One dispatch; returns (stdout, returncode). `broken` fails every surface."""
    d = tmp_path / sub_dir
    d.mkdir()
    extra = {}
    if broken:
        # Make every observability surface fail: the orca CLI (both the resolver
        # read and the comment write) and the notifier.
        extra["HMAD_STUB_ORCA_RC"] = "9"
        extra["HMAD_STUB_CMUX_RC"] = "9"
    r = _exec_dispatch(d, substrate=substrate, rc=rc,
                       last="STATUS: DONE", timeout="6", **extra)
    return r.stdout, r.returncode


def test_ac_4_1_stdout_is_byte_identical_with_surfaces_on_and_off(tmp_path):
    """Spec AC-4.1: stdout is the verdict carrier; no surface may perturb it.

    `orca` present (surfaces active) vs `cmux` (surfaces are a no-op) must yield
    byte-identical stdout for the same agent output.
    """
    on, rc_on = _stdout_with_surfaces(tmp_path, "on", substrate="orca")
    off, rc_off = _stdout_with_surfaces(tmp_path, "off", substrate="cmux")
    assert on == off, (on, off)
    assert rc_on == rc_off == 0


def test_ac_4_2_empty_final_message_path_is_byte_identical(tmp_path):
    """Spec AC-4.2: the rc-3 recovery path is unperturbed by the surfaces."""
    on, rc_on = _stdout_with_surfaces(tmp_path, "on", substrate="orca", rc="0")
    off, rc_off = _stdout_with_surfaces(tmp_path, "off", substrate="cmux", rc="0")
    # Same agent behaviour on both; the surfaces differ. Neither stdout nor the
    # reserved exit code may differ because of them.
    assert on == off, (on, off)
    assert rc_on == rc_off


@pytest.mark.parametrize("agent_rc", ["0", "2", "7"])
def test_ac_4_3_agent_rc_survives_every_surface_failing(tmp_path, agent_rc):
    """Spec AC-4.3: with every surface stubbed failing, rc is still the AGENT's.

    A surface that leaked its own non-zero into `rc` would turn a successful
    dispatch into a phantom failure, or worse, mask a real one.
    """
    d = tmp_path / f"rc{agent_rc}"
    d.mkdir()
    # Two distinct failure shapes, because they reach DIFFERENT code paths:
    #   HMAD_STUB_ORCA_RC   -> the resolver read fails, stamp abandons early
    #   HMAD_STUB_ORCA_SET_RC -> the read succeeds and the comment WRITE fails,
    #                            which is the only path that can leak a surface rc
    for knob in ("HMAD_STUB_ORCA_RC", "HMAD_STUB_ORCA_SET_RC"):
        sub = d / knob
        sub.mkdir()
        # `state=` is load-bearing: without it the resolver has no payload, the
        # stamp abandons before writing, and the write-failure path this test exists
        # to cover is never reached -- the test then passes even with every guard
        # mutated out.
        r = _exec_dispatch(sub, substrate="orca", rc=agent_rc, last="STATUS: DONE",
                           timeout="6", state=sub / "orca.state", **{knob: "9"})
        assert r.returncode == int(agent_rc), (knob, r.returncode, r.stderr)


# --- Live-e2e regressions. Found by running a real dispatch under Orca, not by any
# stubbed test: the real worktree card had grown to 513 spans / 38,329 bytes.

def test_compose_replaces_a_span_containing_glob_metacharacters():
    """The span being replaced carries markdown; `*` and `[` are glob metacharacters.

    `prefix="${current%$rest}"` with $rest UNQUOTED makes bash treat it as a pattern,
    not a literal. Production verdicts embed the agent's markdown report -- links
    (`[x](y)`) and bold (`**x**`) -- so the suffix-strip silently fails, `prefix`
    stays equal to `current`, and the result is the whole comment twice. Every
    earlier test used short glob-free strings, so this never fired.
    """
    stamp = "h-mad: codex skills · running · 1s⟦/h-mad⟧"
    current = "handoff: keep · h-mad: rc=0 · see [rep.md](/tmp/x) **bold**⟦/h-mad⟧"
    out = _call("_exec_comment_compose", current, stamp).stdout
    assert out.count("h-mad: ") == 1, out
    assert out.count("⟦/h-mad⟧") == 1, out
    assert out.startswith("handoff: keep"), out


def test_compose_is_idempotent_against_a_glob_bearing_span():
    """Repeated composes over a markdown-bearing span must not grow the comment."""
    current = "handoff: keep · h-mad: rc=0 · [a](b) **c** *d*⟦/h-mad⟧"
    for i in range(5):
        stamp = f"h-mad: codex skills · running · {i}s⟦/h-mad⟧"
        current = _call("_exec_comment_compose", current, stamp).stdout
    assert current.count("h-mad: ") == 1, current
    assert len(current) < 200, len(current)


def test_exit_stamp_verdict_is_a_token_not_the_whole_final_message(tmp_path):
    """A worktree comment is a one-line card field, not a transcript sink.

    `_cmd_exec` passed the agent's ENTIRE final message as the verdict, so real
    cards carried multi-line reports complete with markdown. Cap it to the verdict
    token the contract defines.
    """
    cap = tmp_path / "calls"
    state = tmp_path / "orca.state"
    multiline = "Implemented tests only.\n\n- Full suite: `1051 passed`\n\nSTATUS: DONE"
    r = _exec_dispatch(tmp_path, state=state, capture=cap, last=multiline)
    assert r.returncode == 0, r.stderr
    writes = [l for l in _orca_calls(cap) if "worktree set" in l]
    assert writes, "no comment write recorded"
    exit_write = writes[-1]
    assert "\n" not in exit_write.split("--comment", 1)[-1][:400], exit_write
    assert "Full suite" not in exit_write, exit_write
