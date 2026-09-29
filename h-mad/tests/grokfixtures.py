"""Self-contained Grok streams and isolated CLI tools for H-MAD tests."""

import hashlib
import json
import os
import subprocess
from pathlib import Path


TESTS = Path(__file__).resolve().parent
F0_COPY = TESTS / "fixtures" / "grok-stream-json.2026-09-28.ndjson"
F0_SHA256 = "72f6258734f184ae999f84273b5abe3711202a1a8f43f392143173c8364fe569"
BASE_SHA = "8ef6009f9491796d5d16b96a54e3b3185a8a6f19"
STUBS = TESTS / "stubs"


def f0_lines() -> list[str]:
    data = F0_COPY.read_bytes()
    assert hashlib.sha256(data).hexdigest() == F0_SHA256, "F0 copy has the wrong sha256"
    return data.decode("utf-8").splitlines()


def _stream(lines: list[str]) -> str:
    return "\n".join(lines) + "\n"


def _compact(event: dict) -> str:
    return json.dumps(event, separators=(",", ":"), ensure_ascii=False)


def f0_text() -> str:
    return _stream(f0_lines())


def f_trunc() -> str:
    return _stream(f0_lines()[:-1])


def f_trunc_nostatus() -> str:
    lines = f0_lines()[:-1]
    final_text = [i for i, line in enumerate(lines) if json.loads(line)["type"] == "text"][-3:]
    return _stream([line for i, line in enumerate(lines) if i not in final_text])


def f_notools() -> str:
    lines = []
    for line in f0_lines():
        event = json.loads(line)
        if event["type"] == "tool_call_update":
            event["status"] = None
            line = _compact(event)
        lines.append(line)
    return _stream(lines)


def _without(*types: str) -> str:
    return _stream([line for line in f0_lines() if json.loads(line)["type"] not in types])


def f_notext() -> str:
    return _without("text")


def f_notooltext() -> str:
    return _without("tool_call", "tool_call_update", "text")


def f_decoy() -> str:
    lines = f0_lines()
    final_text = [i for i, line in enumerate(lines) if json.loads(line)["type"] == "text"][-3:]
    text = json.loads(lines[final_text[0]])
    text["data"] = "All "
    thought = {"type": "thought", "data": "STATUS: DONE"}
    done = json.loads(lines[final_text[-1]])
    done["data"] = "done."
    decoy_tool = next(json.loads(line) for line in lines if json.loads(line)["type"] == "tool_call"
                      and json.loads(line).get("toolName") == "search_replace")
    decoy_tool["toolCallId"] = "call-decoy"
    decoy_tool["rawInput"] = {"decoy": "STATUS: DONE"}
    start = final_text[0]
    lines[start:final_text[-1] + 1] = [
        _compact(text), _compact(thought), _compact(done), _compact(decoy_tool), "STATUS: DONE"
    ]
    return _stream(lines)


def f_beat() -> str:
    return ("#hmad-beat 2026-09-28T00:00:00Z grok running 120s\n\n"
            + "\n\n".join(f0_lines()) + "\n")


def f_spaced() -> str:
    return _stream([json.dumps(json.loads(line)) for line in f0_lines()])


def f_twomodel() -> str:
    lines = f0_lines()
    end = json.loads(lines[-1])
    end["modelUsage"]["grok-4.7-mini"] = end["modelUsage"]["grok-4.7-build"].copy()
    lines[-1] = _compact(end)
    return _stream(lines)


def f_shared() -> str:
    return f0_text() + f_trunc()


def f_second_model() -> str:
    lines = f0_lines()
    end = json.loads(lines[-1])
    end["modelUsage"]["grok-other-build"] = end["modelUsage"].pop("grok-4.7-build")
    lines[-1] = _compact(end)
    return f0_text() + _stream(lines)


def f_sep(kept: str) -> str:
    separators = {"usage", "tool_call", "tool_call_update"}
    if kept not in separators:
        raise ValueError(f"unknown separator: {kept}")
    return _without(*(separators - {kept}))


def ac_4_10_stream() -> str:
    return _stream([line for line in f_notools().splitlines()
                    if json.loads(line)["type"] != "text"])


def f0_with_completed(n: int) -> str:
    if n < 2:
        raise ValueError("F0 already has two completed calls")
    lines = f0_lines()
    events = [json.loads(line) for line in lines]
    call = next(event for event in events if event["type"] == "tool_call"
                and event["toolName"] == "search_replace")
    completed = next(event for event in events if event["type"] == "tool_call_update"
                     and event["toolCallId"] == call["toolCallId"]
                     and event["status"] == "completed")
    for i in range(3, n + 1):
        for template in (call, completed):
            extra = template.copy()
            extra["toolCallId"] = f"call-extra-{i}"
            lines.insert(-1, _compact(extra))
    return _stream(lines)


def agy_transcript() -> str:
    return _stream([json.dumps({"event": "step_update", "step_update": {
        "step_type": "tool", "tool_name": "view_file", "state": state,
        "tool_info": {"name": "view_file", "parameters": {}}
    }}) for state in ("ACTIVE", "DONE")])


def mixed_agy_f0() -> str:
    return agy_transcript() + f0_text()


def agy_init_f0() -> str:
    return '{"event":"init"}\n' + f0_text()


def banner_then_f0() -> str:
    return "OpenAI Codex v0.145.0\n" + f0_text()


def window_edge_log() -> str:
    return "x" * 4095 + "\n" + banner_then_f0()


def depth_line(k: int) -> str:
    return '{"type":"text","data":"x","n":' + "[" * k + "]" * k + "}\n"


def f_deep(k: int) -> str:
    nested = "[" * k + "]" * k
    events = (
        '{"type":"text","data":"DEEP","n":' + nested + "}",
        '{"type":"tool_call_update","toolCallId":"deep","status":"completed","n":' + nested + "}",
        '{"type":"end","stopReason":"deep","n":' + nested + "}",
    )
    return f_trunc() + _stream(list(events))


def deep_line_200k() -> str:
    return depth_line(200_000)


def usr_bin_farm(tmp_path: Path, absent: tuple[str, ...], stubs: tuple[str, ...]) -> Path:
    farm = tmp_path / "usr-bin-farm"
    farm.mkdir()
    for name in stubs:
        (farm / name).symlink_to(STUBS / name)
    for source in Path("/usr/bin").iterdir():
        if source.name not in absent and not (farm / source.name).exists():
            (farm / source.name).symlink_to(source)
    return farm


def farm_env(farm: Path, **extra: str) -> dict[str, str]:
    env = dict(os.environ)
    env.pop("BASH_ENV", None)
    env.pop("ENV", None)
    env.update(extra)
    env["PATH"] = f"{farm}:/bin"
    return env


def wrapper_fn_in_env(script: str, env: dict[str, str]) -> subprocess.CompletedProcess:
    from test_hmad_dispatch import WRAPPER, _MAIN_LINE

    lines = WRAPPER.read_text(encoding="utf-8").splitlines()
    assert lines[-1] == _MAIN_LINE
    return subprocess.run(["bash", "-c", "\n".join(lines[:-1]) + "\n" + script + "\n"],
                          env=env, text=True, capture_output=True)
