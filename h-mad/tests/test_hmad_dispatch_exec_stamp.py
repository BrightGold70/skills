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
