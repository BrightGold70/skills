"""Grok's resolved model comes from the last completed stream event."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import grokfixtures


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "h_mad_resolved_model.py"
DISPATCH = SKILL_ROOT / "bin" / "hmad-dispatch"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "HMAD_STUB_HOSTILE": "all"}
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, env=env,
    )


def write_log(tmp_path: Path, body: str) -> Path:
    log = tmp_path / "log [agent](x) **status** `$()` ===HMAD-DISPATCH-BOUNDARY===.ndjson"
    log.write_text(body, encoding="utf-8")
    return log


def expected_line(log: Path, model: str) -> str:
    return (f"RESOLVED-MODEL agent=grok model={model} effort=- "
            f"resolved=1 source={log}\n")


def test_grok_reads_the_model_from_the_last_end(tmp_path: Path) -> None:
    log = write_log(tmp_path, grokfixtures.f0_text())

    result = run("grok", "--log", str(log))

    assert result.stdout == expected_line(log, "grok-4.7-build"), (
        "main must route grok --log to the last end event's modelUsage"
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("case", ["f_trunc", "f_twomodel", "no_log", "missing_path"])
def test_grok_refusals_exit_2_unknown(tmp_path: Path, case: str) -> None:
    if case == "no_log":
        args = ("grok",)
    elif case == "missing_path":
        args = ("grok", "--log", str(tmp_path / "missing [agent] `$()`.ndjson"))
    else:
        body = grokfixtures.f_trunc() if case == "f_trunc" else grokfixtures.f_twomodel()
        args = ("grok", "--log", str(write_log(tmp_path, body)))

    result = run(*args)

    assert "RESOLVED-MODEL: UNKNOWN" in result.stderr, (
        f"{case}: grok must refuse unresolvable model evidence through _fail; {result.stderr}"
    )
    assert result.returncode == 2, f"{case}: refusal must exit 2"
    assert result.stdout == "", f"{case}: refusal must not emit a resolved model"
    if case == "f_twomodel":
        assert "grok-4.7-build" in result.stderr
        assert "grok-4.7-mini" in result.stderr


def test_grok_empty_model_usage_refuses(tmp_path: Path) -> None:
    lines = grokfixtures.f0_lines()
    last_end = json.loads(lines[-1])
    last_end["modelUsage"] = {}
    lines[-1] = json.dumps(last_end)
    log = write_log(tmp_path, "\n".join(lines) + "\n")

    result = run("grok", "--log", str(log))

    assert "RESOLVED-MODEL: UNKNOWN" in result.stderr, (
        "an end event with empty modelUsage must be refused"
    )
    assert result.returncode == 2
    assert result.stdout == ""


def test_grok_resolves_from_the_last_end_on_a_shared_log(tmp_path: Path) -> None:
    log = write_log(tmp_path, grokfixtures.f_shared())

    result = run("grok", "--log", str(log))

    assert result.stdout == expected_line(log, "grok-4.7-build"), (
        "the last end must remain authoritative when a later dispatch is truncated"
    )
    assert result.returncode == 0, result.stderr


def test_grok_second_dispatch_model_wins(tmp_path: Path) -> None:
    log = write_log(tmp_path, grokfixtures.f_second_model())

    result = run("grok", "--log", str(log))

    assert result.stdout == expected_line(log, "grok-other-build"), (
        "the second dispatch's end event must replace the first model"
    )
    assert result.returncode == 0, result.stderr


def test_hmad_dispatch_resolved_model_grok_passes_through(tmp_path: Path) -> None:
    log = write_log(tmp_path, grokfixtures.f0_text())
    env = {**os.environ, "HMAD_STUB_HOSTILE": "all"}

    result = subprocess.run(
        [str(DISPATCH), "resolved-model", "grok", "--log", str(log)],
        capture_output=True, text=True, env=env,
    )

    assert result.stdout == expected_line(log, "grok-4.7-build"), (
        "hmad-dispatch resolved-model must forward grok and --log to main"
    )
    assert result.returncode == 0, result.stderr
