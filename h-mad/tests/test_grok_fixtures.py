"""Contracts for the in-skill Grok fixture builders and CLI stubs."""

import collections
import hashlib
import importlib
import json
import os
import re
import subprocess
from pathlib import Path

import pytest


TESTS = Path(__file__).resolve().parent
STUBS = TESTS / "stubs"
F0_COPY = TESTS / "fixtures" / "grok-stream-json.2026-09-28.ndjson"
F0_SHA256 = "72f6258734f184ae999f84273b5abe3711202a1a8f43f392143173c8364fe569"


def _fixtures():
    # Import inside each test so the absent new module yields individual RED items.
    return importlib.import_module("grokfixtures")


def _json_events(stream):
    return [json.loads(line) for line in stream.splitlines()]


def _stub_env(**extra):
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith(("HMAD_STUB_", "CLAUDE")) and key not in {"BASH_ENV", "ENV"}
    }
    env.update(extra)
    return env


def test_grok_fixture_copy_hash():
    assert F0_COPY.is_file(), "in-skill F0 copy is missing"
    assert hashlib.sha256(F0_COPY.read_bytes()).hexdigest() == F0_SHA256, (
        "in-skill F0 copy has the wrong sha256"
    )


def test_f0_type_counts_match_the_spec(tmp_path, monkeypatch):
    fixtures = _fixtures()
    assert fixtures.F0_COPY == F0_COPY
    assert fixtures.F0_SHA256 == F0_SHA256
    assert re.fullmatch(r"[0-9a-f]{40}", fixtures.BASE_SHA), (
        "BASE_SHA must be the pinned 40-hex fork commit"
    )
    lines = fixtures.f0_lines()
    assert len(lines) == 110, "F0 must have 110 events"
    assert all(line.startswith('{"type":"') for line in lines)
    assert collections.Counter(json.loads(line)["type"] for line in lines) == {
        "thought": 70,
        "text": 21,
        "available_commands": 9,
        "usage": 3,
        "tool_call_update": 4,
        "tool_call": 2,
        "end": 1,
    }
    assert fixtures.f0_text() == "\n".join(lines) + "\n"
    corrupted = tmp_path / "corrupted.ndjson"
    corrupted.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(fixtures, "F0_COPY", corrupted)
    with pytest.raises(AssertionError):
        fixtures.f0_lines()


def test_derived_fixture_line_counts():
    f = _fixtures()
    original = f.f0_lines()
    assert len(f.f_notooltext().splitlines()) == 83
    assert len(f.ac_4_10_stream().splitlines()) == 89
    assert {kind: len(f.f_sep(kind).splitlines()) for kind in (
        "usage", "tool_call", "tool_call_update"
    )} == {"usage": 104, "tool_call": 103, "tool_call_update": 105}
    assert f.f_trunc().splitlines() == original[:-1]
    assert len(f.f_trunc().splitlines()) == 109

    assert f.f_trunc_nostatus().splitlines() == [
        line for i, line in enumerate(original[:-1])
        if i not in [j for j, item in enumerate(original) if json.loads(item)["type"] == "text"][-3:]
    ]
    no_tools = _json_events(f.f_notools())
    assert [e["status"] for e in no_tools if e["type"] == "tool_call_update"] == [None] * 4
    assert [e for e in no_tools if e["type"] != "tool_call_update"] == [
        json.loads(line) for line in original if json.loads(line)["type"] != "tool_call_update"
    ]
    assert f.f_notext().splitlines() == [
        line for line in original if json.loads(line)["type"] != "text"
    ]
    assert f.f_notooltext().splitlines() == [
        line for line in original
        if json.loads(line)["type"] not in {"tool_call", "tool_call_update", "text"}
    ]
    assert f.ac_4_10_stream().splitlines() == [
        line for line in f.f_notools().splitlines() if json.loads(line)["type"] != "text"
    ]
    for kept in ("usage", "tool_call", "tool_call_update"):
        assert f.f_sep(kept).splitlines() == [
            line for line in original if json.loads(line)["type"] not in (
                {"usage", "tool_call", "tool_call_update"} - {kept}
            )
        ]

    decoy_lines = f.f_decoy().splitlines()
    decoy_events = [json.loads(line) for line in decoy_lines if line.startswith("{")]
    final_segment = [e for e in decoy_events if e.get("data") in ("All ", "STATUS: DONE", "done.")]
    assert [(e["type"], e["data"]) for e in final_segment[-3:]] == [
        ("text", "All "), ("thought", "STATUS: DONE"), ("text", "done.")
    ]
    assert any(e["type"] == "tool_call" and "STATUS: DONE" in json.dumps(e["rawInput"])
               for e in decoy_events)
    assert "STATUS: DONE" in decoy_lines, "F-DECOY needs a bare verdict decoy"
    assert f.f_decoy().endswith("\n")

    beat = f.f_beat().splitlines()
    assert "#hmad-beat 2026-09-28T00:00:00Z grok running 120s" in beat
    assert "" in beat
    assert [line for line in beat if line.startswith("{")] == original
    assert f.f_spaced().splitlines() == [json.dumps(json.loads(line)) for line in original]
    assert f.f_shared() == f.f0_text() + f.f_trunc()
    assert f.f_twomodel().splitlines()[:-1] == original[:-1]
    assert set(_json_events(f.f_twomodel())[-1]["modelUsage"]) == {
        "grok-4.7-build", "grok-4.7-mini"
    }
    assert f.f_second_model().splitlines()[:110] == original
    assert set(_json_events(f.f_second_model())[-1]["modelUsage"]) == {"grok-other-build"}

    completed = _json_events(f.f0_with_completed(3))
    assert len(completed) == 112
    assert completed[-1] == json.loads(original[-1])
    assert [(e["type"], e["toolCallId"]) for e in completed[-3:-1]] == [
        ("tool_call", "call-extra-3"), ("tool_call_update", "call-extra-3")
    ]
    assert completed[-3]["toolName"] == "search_replace"
    assert completed[-2]["status"] == "completed"

    agy = _json_events(f.agy_transcript())
    assert [e["step_update"]["state"] for e in agy] == ["ACTIVE", "DONE"]
    assert all(e["step_update"]["tool_name"] == "view_file" for e in agy)
    assert f.mixed_agy_f0() == f.agy_transcript() + f.f0_text()
    assert f.agy_init_f0() == '{"event":"init"}\n' + f.f0_text()
    assert f.banner_then_f0() == "OpenAI Codex v0.145.0\n" + f.f0_text()
    assert f.window_edge_log() == "x" * 4095 + "\n" + f.banner_then_f0()
    assert f.deep_line_200k() == f.depth_line(200_000)
    for stream in (f.f_notooltext(), f.ac_4_10_stream(), f.f_spaced(),
                   f.f_twomodel(), f.f_shared(), f.f_second_model()):
        assert stream.endswith("\n") and not stream.endswith("\n\n")


def test_depth_line_builder_gives_the_requested_depth():
    f = _fixtures()
    for depth in (64, 65):
        line = f.depth_line(depth)
        assert line.startswith('{"type":"text","data":"x","n":')
        assert line.endswith("}\n")
        value = json.loads(line)["n"]
        for _ in range(depth - 1):
            assert isinstance(value, list) and len(value) == 1
            value = value[0]
        assert value == [], "depth_line must contain exactly the requested list depth"

        deep_lines = f.f_deep(depth).splitlines()
        assert deep_lines[:109] == f.f_trunc().splitlines()
        assert len(deep_lines) == 112
        events = [json.loads(line) for line in deep_lines[-3:]]
        assert [(e["type"], e.get("data"), e.get("toolCallId"), e.get("stopReason"))
                for e in events] == [
                    ("text", "DEEP", None, None),
                    ("tool_call_update", None, "deep", None),
                    ("end", None, None, "deep"),
                ]
        assert events[1]["status"] == "completed"
        for event in events:
            nested = event["n"]
            for _ in range(depth - 1):
                assert isinstance(nested, list) and len(nested) == 1
                nested = nested[0]
            assert nested == []


def test_grok_stub_replays_the_stream_and_copies_the_prompt_file(tmp_path):
    stub = STUBS / "grok"
    assert stub.is_file(), "grok stub must replay the stream and copy the prompt file"
    assert os.access(stub, os.X_OK), "grok stub must be executable"
    prompt = tmp_path / "prompt.txt"
    hostile_prompt = "# [agent](x) **status** ⟦/h-mad⟧\nsecond\tline * [\n"
    prompt.write_text(hostile_prompt, encoding="utf-8")
    stream = tmp_path / "stream.ndjson"
    stream.write_text('{"type":"text","data":"hello"}\n', encoding="utf-8")
    capture = tmp_path / "argv.txt"
    copied = tmp_path / "prompt-copy.txt"
    backend = tmp_path / "backend.txt"
    env = _stub_env(HMAD_STUB_CAPTURE=str(capture),
                    HMAD_STUB_ENV_CAPTURE=str(backend),
                    HMAD_STUB_GROK_PROMPT_CAPTURE=str(copied),
                    HMAD_STUB_GROK_STREAM=str(stream), HMAD_STUB_HOSTILE="all",
                    HPW_AGENT_BACKEND="grok")
    result = subprocess.run([str(stub), "--prompt-file", str(prompt)],
                            env=env, text=True, capture_output=True)
    assert result.returncode == 0
    assert result.stdout == stream.read_text(encoding="utf-8")
    assert copied.read_bytes() == prompt.read_bytes(), "grok stub changed hostile prompt bytes"
    assert capture.read_text(encoding="utf-8") == f"grok --prompt-file {prompt}\n"
    assert backend.read_text(encoding="utf-8") == "HPW_AGENT_BACKEND=grok\n"


def test_grok_stub_exits_with_the_configured_rc():
    stub = STUBS / "grok"
    assert stub.is_file(), "grok stub must honor HMAD_STUB_GROK_RC"
    result = subprocess.run([str(stub)], env=_stub_env(HMAD_STUB_GROK_RC="17"),
                            text=True, capture_output=True)
    assert result.returncode == 17, "grok stub ignored HMAD_STUB_GROK_RC"


@pytest.mark.parametrize("name", ["codex", "agy", "grok"])
def test_stub_claude_env_knob_records_names_when_set(tmp_path, name):
    stub = STUBS / name
    assert stub.is_file(), f"{name} stub must capture exported CLAUDE* names"
    capture = tmp_path / "claude-names.txt"
    env = _stub_env(CLAUDECODE="1", CLAUDE_EFFORT="high",
                    HMAD_STUB_CLAUDE_ENV_CAPTURE=str(capture))
    result = subprocess.run([str(stub)], env=env, input="", text=True,
                            capture_output=True)
    assert result.returncode == 0
    assert capture.is_file(), f"{name} stub did not create the CLAUDE* names capture"
    assert capture.read_text(encoding="utf-8").splitlines() == [
        "CLAUDECODE", "CLAUDE_EFFORT"
    ], f"{name} stub must record sorted exported CLAUDE* names"


@pytest.mark.parametrize("name", ["codex", "agy"])
def test_stub_claude_env_knob_is_inert_when_unset(tmp_path, name):
    capture = tmp_path / "claude-names.txt"
    backend = tmp_path / "backend.txt"
    env = _stub_env(CLAUDECODE="1", CLAUDE_EFFORT="high",
                    HMAD_STUB_ENV_CAPTURE=str(backend), HPW_AGENT_BACKEND="existing")
    result = subprocess.run([str(STUBS / name)], env=env, input="", text=True,
                            capture_output=True)
    assert result.returncode == 0
    assert result.stdout == ("[codex] running task...\n" if name == "codex"
                             else "VERDICT: COMPLIANT\n")
    assert backend.read_text(encoding="utf-8") == "HPW_AGENT_BACKEND=existing\n"
    assert not capture.exists(), f"{name} stub created CLAUDE* capture without the knob"


def test_usr_bin_farm_hides_the_absent_tool(tmp_path):
    f = _fixtures()
    farm = f.usr_bin_farm(tmp_path, ("jq",), ())
    env = f.farm_env(farm)
    missing = subprocess.run(["bash", "-c", "command -v jq"], env=env,
                             text=True, capture_output=True)
    present = subprocess.run(["bash", "-c", "command -v env"], env=env,
                             text=True, capture_output=True)
    assert missing.returncode != 0 and not missing.stdout, "usr_bin_farm must hide jq"
    assert present.returncode == 0 and present.stdout.strip() == str(farm / "env"), (
        "usr_bin_farm must expose env"
    )
    assert env["PATH"] == f"{farm}:/bin"
    assert "BASH_ENV" not in env and "ENV" not in env
    direct = f.wrapper_fn_in_env("printf 'wrapper-ready\\n'", env)
    assert direct.returncode == 0
    assert direct.stdout == "wrapper-ready\n"
