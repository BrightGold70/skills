"""Direct RED tests for the Grok log-region readers in hmad-dispatch."""

import json
import shlex

import pytest

from grokfixtures import (
    ac_4_10_stream,
    f0_text,
    f_decoy,
    f_deep,
    f_notools,
    f_notooltext,
    f_sep,
    f_trunc,
    farm_env,
    usr_bin_farm,
    wrapper_fn_in_env,
)
from test_hmad_dispatch import _bindir, run_fn


def _log(tmp_path, contents):
    path = tmp_path / "grok.ndjson"
    path.write_text(contents, encoding="utf-8")
    return path


def _call(tmp_path, function, contents, pre=0, *, env=None):
    path = _log(tmp_path, contents)
    command = f"{function} {shlex.quote(str(path))} {pre}"
    return run_fn(command, env={"HMAD_STUB_HOSTILE": "all", **(env or {})})


def _assert_reader(r, property_name):
    assert r.returncode == 0, f"{property_name}: {r.stderr}"
    assert "command not found" not in r.stderr, f"{property_name}: reader must exist"


def test_grok_final_message_on_f0(tmp_path):
    r = _call(tmp_path, "_grok_final_message", f0_text())
    _assert_reader(r, "final message from F0")
    assert r.stdout.strip() == "STATUS: DONE", "final message must return F0's last text segment"


@pytest.mark.parametrize("closer", ["usage", "tool_call", "tool_call_update"])
def test_grok_final_message_per_closer(tmp_path, closer):
    r = _call(tmp_path, "_grok_final_message", f_sep(closer))
    _assert_reader(r, f"{closer} closes a text segment")
    assert r.stdout.strip() == "STATUS: DONE", f"{closer} alone must close text segments"


def test_grok_final_message_ignores_thought_decoy(tmp_path):
    r = _call(tmp_path, "_grok_final_message", f_decoy())
    _assert_reader(r, "thought decoy is transparent to text")
    assert r.stdout.strip() == "All done.", "thought data must not replace or close text"


def test_grok_final_message_keeps_a_multiline_segment(tmp_path):
    stream = ''.join(json.dumps(event) + "\n" for event in (
        {"type": "text", "data": "a\nb"}, {"type": "end"},
    ))
    r = _call(tmp_path, "_grok_final_message", stream)
    _assert_reader(r, "multiline text segment")
    assert r.stdout == "a\nb\n", "one text event's embedded newline must survive intact"


def test_grok_region_starts_after_pre(tmp_path):
    r = _call(tmp_path, "_grok_region", f0_text() + f0_text(), pre=110)
    _assert_reader(r, "region starts after 110 existing lines")
    assert r.stdout == f0_text(), "region must contain exactly the second F0 copy"


@pytest.mark.parametrize("name,stream,expected", [
    ("f0", f0_text(), "complete"),
    ("f_trunc", f_trunc(), "truncated"),
    ("empty", "", "truncated"),
    ("deep65_end", '{"type":"end","n":' + "[" * 65 + "]" * 65 + "}\n", "truncated"),
], ids=["f0", "f_trunc", "empty", "deep65_end"])
def test_grok_region_state_words(tmp_path, name, stream, expected):
    r = _call(tmp_path, "_grok_region_state", stream)
    _assert_reader(r, f"{name} region state")
    assert r.stdout.strip() == expected, f"{name} region must report {expected}"


def test_grok_region_state_reports_jq_failure(tmp_path):
    bindir = _bindir(tmp_path, [])
    jq = bindir / "jq"
    if jq.exists() or jq.is_symlink():
        jq.unlink()
    jq.write_text("#!/bin/sh\nexit 5\n", encoding="utf-8")
    jq.chmod(0o755)
    r = _call(tmp_path, "_grok_region_state", f0_text(), env={"_BINDIR": str(bindir)})
    _assert_reader(r, "jq execution failure state")
    assert r.stdout.strip() == "jqfail", "jq exit 5 must be distinct from missing jq"


def test_grok_region_state_without_jq(tmp_path):
    farm = usr_bin_farm(tmp_path, absent=("jq",), stubs=())
    path = _log(tmp_path, f0_text())
    r = wrapper_fn_in_env(
        f"_grok_region_state {shlex.quote(str(path))} 0",
        farm_env(farm, HMAD_STUB_HOSTILE="all"),
    )
    _assert_reader(r, "missing jq state")
    assert r.stdout.strip() == "nojq", "missing jq must report nojq"


def test_grok_region_state_survives_a_sigpipe_sized_region(tmp_path):
    stream = '{"type":"end"}\n' + '{"type":"thought","data":"hostile * [x] `echo no`"}\n' * 20_000
    r = _call(tmp_path, "_grok_region_state", stream)
    _assert_reader(r, "complete state after 20,000 trailing events")
    assert r.stdout.strip() == "complete", "reader must consume the whole region without SIGPIPE"


def test_grok_stop_reason_on_f0(tmp_path):
    r = _call(tmp_path, "_grok_stop_reason", f0_text())
    _assert_reader(r, "F0 stop reason")
    assert r.stdout.strip() == "end_turn", "last end event must supply its stopReason"


@pytest.mark.parametrize("name,stream,expected", [
    ("f0", f0_text(), "2 tool calls completed; last tool: search_replace completed"),
    ("f_notools", f_notools(), "0 tool calls completed; last tool: search_replace pending"),
    ("ac_4_10", ac_4_10_stream(), "0 tool calls completed; last tool: search_replace pending"),
    ("f_notooltext", f_notooltext(), ""),
], ids=["f0", "f_notools", "ac_4_10", "f_notooltext"])
def test_grok_last_tool_lines(tmp_path, name, stream, expected):
    r = _call(tmp_path, "_grok_last_tool", stream)
    _assert_reader(r, f"{name} last tool summary")
    assert r.stdout.strip() == expected, f"{name} must report distinct completed IDs and last status"


@pytest.mark.parametrize("depth,state,message,completed,reason", [
    (64, "complete", "DEEP", "3 tool calls completed", "deep"),
    (65, "truncated", "STATUS: DONE", "2 tool calls completed", ""),
], ids=["64", "65"])
def test_grok_depth_boundary_readers(tmp_path, depth, state, message, completed, reason):
    stream = f_deep(depth)
    for function, expected in (
        ("_grok_region_state", state),
        ("_grok_final_message", message),
        ("_grok_stop_reason", reason),
    ):
        r = _call(tmp_path, function, stream)
        _assert_reader(r, f"depth {depth} {function}")
        assert r.stdout.strip() == expected, f"depth {depth} {function} must ignore overdeep events"
    r = _call(tmp_path, "_grok_last_tool", stream)
    _assert_reader(r, f"depth {depth} last tool")
    assert r.stdout.startswith(completed), f"depth {depth} must count only accepted completed IDs"
