"""Non-Python production paths reach the real parser's CLI consumers."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tdd_gate_support import hermetic_env, write_plan, write_state

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from h_mad_wire_pin_gate import _parse_tasks  # noqa: E402


@pytest.fixture(scope="module")
def hostile_plan_note() -> str:
    """Use the stub's actual hostile agent payload as free-form plan prose."""
    env = {key: value for key, value in hermetic_env().items()
           if not key.startswith("HMAD_STUB_")}
    env["HMAD_STUB_HOSTILE"] = "all"
    proc = subprocess.run(
        ["bash", str(Path(__file__).parent / "stubs" / "orca"),
         "worktree", "set", "--comment", "fixture", "--json"],
        env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True,
        timeout=30.0, check=True,
    )
    note = json.loads(proc.stdout)["result"]["worktree"]["comment"]
    assert "**bold**" in note and "⟦/h-mad⟧" in note and "\n" in note
    return note


def _task(production: str, tests: str, note: str, *, wiring: bool = False) -> str:
    lines = [
        "## Task 1: parser",
        f"**Production file**: {production}",
        f"**Test file**: {tests}",
        f"**Task shape**: `{'wiring' if wiring else 'new-behaviour'}`",
    ]
    if wiring:
        lines.extend([
            "**WIRE**: `src/m.py:run` -> `engine.measure`",
            "**WIRE-PIN**: `tests/test_m.py::test_run_calls_measure`",
            "**WIRE-RUNNER**: `pytest`",
            "**Judge budget**: 37s",
        ])
    return "\n".join([*lines, "", note, ""])


def _one_task(text: str) -> dict:
    tasks = _parse_tasks(text)
    assert len(tasks) == 1, "the hostile plan must still parse as exactly one task"
    return tasks[0]


def _judge(root: Path, text: str, target: str) -> subprocess.CompletedProcess:
    write_state(root, {"f": {"phase": "step5"}})
    write_plan(root, "f", text)
    path = root / target
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# production fixture\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "h_mad_tdd_judge.py"),
         "judge", "--root", str(root), "--target", target],
        env=hermetic_env(), stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=60.0, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return proc


def test_mixed_production_line_collects_all_three(hostile_plan_note: str) -> None:
    task = _one_task(_task(
        "`h-mad/scripts/hmad-dispatch.sh`, `h-mad/scripts/a.py`, `h-mad/bin/hmad-dispatch`",
        "`tests/test_t.py`", hostile_plan_note,
    ))
    assert task["production"] == [
        "h-mad/scripts/a.py", "h-mad/scripts/hmad-dispatch.sh", "h-mad/bin/hmad-dispatch",
    ], "production must collect Python first, then every non-Python path in line order"


def test_judge_cli_finds_each_token_of_a_mixed_production_line(
    tmp_path: Path, hostile_plan_note: str,
) -> None:
    text = _task(
        "`h-mad/scripts/x.sh`, `h-mad/scripts/a.py`, `h-mad/bin/hmad-dispatch`",
        "`tests/test_t.py`", hostile_plan_note,
    )
    outputs = {target: _judge(tmp_path, text, target).stdout for target in (
        "h-mad/scripts/x.sh", "h-mad/scripts/a.py", "h-mad/bin/hmad-dispatch",
    )}
    assert all("TDD-JUDGE: DENY kind=test-missing " in out for out in outputs.values()), (
        "each mixed production token must resolve the declared missing test", outputs,
    )
    assert all("tests/test_t.py" in out for out in outputs.values()), outputs


def test_judge_cli_ignores_a_non_py_test_token(
    tmp_path: Path, hostile_plan_note: str,
) -> None:
    candidate = tmp_path / "h-mad/tests/mutation-specs/x.json"
    candidate.parent.mkdir(parents=True)
    candidate.write_text("{}\n", encoding="utf-8")
    proc = _judge(tmp_path, _task(
        "`scripts/x.sh`", "`h-mad/tests/mutation-specs/x.json`", hostile_plan_note,
    ), "scripts/x.sh")
    assert "TDD-JUDGE: DENY kind=test-missing " in proc.stdout, (
        "the shell production path must match while the JSON test remains excluded", proc.stdout,
    )
    assert "no resolved test file exists ()" in proc.stdout, (
        "a non-Python Test file token must contribute no candidate", proc.stdout,
    )


def test_wire_pin_cli_output_ignores_a_non_py_token(
    tmp_path: Path, hostile_plan_note: str,
) -> None:
    plan = tmp_path / "f.impl-plan.md"
    outputs = []
    records = []
    for index, production in enumerate(("`src/m.py`", "`src/m.py`, `scripts/x.sh`")):
        plan.write_text(_task(production, "`tests/test_m.py`", hostile_plan_note,
                              wiring=True), encoding="utf-8")
        registry_path = tmp_path / f"wires-{index}.jsonl"
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "h_mad_wire_pin_gate.py"), str(plan),
             "--feature", "f", "--registry", str(registry_path)],
            env=hermetic_env(), stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=60.0, check=False,
        )
        assert proc.returncode == 0, proc.stderr
        assert "registration: registered=1 skipped=0" in proc.stdout, proc.stdout
        record, = [json.loads(line) for line in registry_path.read_text(encoding="utf-8").splitlines()]
        assert "registered_ts" in record, record
        records.append({key: value for key, value in record.items() if key != "registered_ts"})
        outputs.append(proc.stdout)
    assert records[0] == records[1], "a non-Python production token must preserve the registry record"
    assert outputs[0] == outputs[1], "a non-Python production token must preserve wire-pin stdout"


def test_python_only_production_line_keeps_items_and_order(hostile_plan_note: str) -> None:
    task = _one_task(_task("`src/z.py`, `src/a.py`, `src/z.py`", "`tests/test_m.py`",
                           hostile_plan_note))
    assert task["production"] == ["src/z.py", "src/a.py", "src/z.py"], (
        "Python-only production paths must retain their order and multiplicity"
    )


def test_none_value_production_stays_empty(hostile_plan_note: str) -> None:
    task = _one_task(_task("none (writes `docs/x/run.sh` and `docs/x/ignored.py`)", "`tests/test_m.py`",
                           hostile_plan_note))
    assert task["production"] == [], "a none production value must suppress even backticked paths"
    assert task["path_labels"] == {"production", "tests"}, "none is still a production declaration"


def test_non_py_test_token_stays_out_of_tests_and_production(hostile_plan_note: str) -> None:
    task = _one_task(_task("`src/m.py`", "`h-mad/tests/mutation-specs/x.json`",
                           hostile_plan_note))
    assert task["tests"] == [], "Test file tokens remain Python-only"
    assert task["production"] == ["src/m.py"], "a JSON test token must not leak into production"


def test_other_task_fields_match_with_and_without_a_non_py_token(hostile_plan_note: str) -> None:
    original = _one_task(_task("`src/m.py`", "`tests/test_m.py`", hostile_plan_note, wiring=True))
    widened = _one_task(_task("`src/m.py`, `scripts/x.sh`", "`tests/test_m.py`",
                              hostile_plan_note, wiring=True))
    expected = {
        "shape": "wiring",
        "wire": "`src/m.py:run` -> `engine.measure`",
        "pin": "`tests/test_m.py::test_run_calls_measure`",
        "wires": [(None, "`src/m.py:run` -> `engine.measure`")],
        "pins": [(None, "`tests/test_m.py::test_run_calls_measure`")],
        "path_labels": {"production", "tests"},
        "runner": "pytest", "runner_error": None, "judge_budget": 37,
    }
    assert {key: original[key] for key in expected} == expected, "the control must parse real field values"
    assert {key: widened[key] for key in expected} == expected, "non-Python paths must preserve other task fields"


def test_judge_cli_keeps_a_python_only_line(tmp_path: Path, hostile_plan_note: str) -> None:
    test = tmp_path / "tests/test_m.py"
    test.parent.mkdir()
    test.write_text("def test_red():\n    assert 1 == 2\n", encoding="utf-8")
    proc = _judge(tmp_path, _task("`src/m.py`", "`tests/test_m.py`", hostile_plan_note), "src/m.py")
    assert proc.stdout.strip() == (
        "TDD-JUDGE: ALLOW kind=red-measured source=impl-plan test=tests/test_m.py"
    ), "a Python production path must still resolve and measure its failing test: " + proc.stdout


def test_judge_cli_ignores_a_none_production_value(tmp_path: Path, hostile_plan_note: str) -> None:
    text = _task("none (writes `docs/x/run.sh` and `docs/x/ignored.py`)",
                 "`tests/test_m.py`", hostile_plan_note)
    for target in ("docs/x/run.sh", "docs/x/ignored.py"):
        proc = _judge(tmp_path, text, target)
        assert "TDD-JUDGE: DENY kind=no-test-resolved " in proc.stdout, (
            "none must keep its backticked paths out of judge resolution", target, proc.stdout,
        )
