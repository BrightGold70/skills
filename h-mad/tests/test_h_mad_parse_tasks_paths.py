"""Task path labels in implementation plans, without disturbing existing fields."""

import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SCRIPTS))

from h_mad_wire_pin_gate import _FIELD_RE, _parse_tasks  # noqa: E402
from tdd_gate_support import hermetic_env  # noqa: E402


# Keep this independent of production: it also identifies the lines removed from
# the checked-in plan corpus before comparing the pre-existing parser fields.
_PATHS_LABEL_LINE = re.compile(
    r"^\s*(?:[-*•]\s+)?\*{0,2}\s*(?P<label>Production(?:\s+files?)?|Test(?:\s+files?)?)"
    r"\s*(?::\s*\*{0,2}|\*{0,2}\s*:)\s*(?P<value>.*)$",
    re.IGNORECASE,
)


def _one_task(*lines: str) -> dict:
    tasks = _parse_tasks("\n".join(("## Task 1: t", *lines)))
    assert len(tasks) == 1, "the fixture must parse as one task"
    return tasks[0]


@pytest.mark.parametrize(
    "label_line,key,expected",
    [
        pytest.param("**Production file**: `a.py`", "production", ["a.py"], id="production-file"),
        pytest.param("**Production files**: `a.py`, `b.py`", "production", ["a.py", "b.py"], id="production-files"),
        pytest.param("**Production**: `a.py`", "production", ["a.py"], id="production"),
        pytest.param("**Production file:** `a.py`", "production", ["a.py"], id="production-colon-inside"),
        pytest.param("production file: `a.py`", "production", ["a.py"], id="production-unbolded-lowercase"),
        pytest.param("**Test file**: `a.py`", "tests", ["a.py"], id="test-file"),
        pytest.param("**Test files**: `a.py`, `b.py`", "tests", ["a.py", "b.py"], id="test-files"),
        pytest.param("**Test**: `a.py`", "tests", ["a.py"], id="test"),
        pytest.param("**Test:** `a.py`", "tests", ["a.py"], id="test-colon-inside"),
        pytest.param("- **Test file**: `a.py`", "tests", ["a.py"], id="test-bulleted"),
    ],
)
def test_paths_label_spelling(label_line: str, key: str, expected: list[str]) -> None:
    task = _one_task(label_line)
    other = "tests" if key == "production" else "production"
    assert task.get(key) == expected, f"{label_line!r} should yield {key} paths {expected!r}"
    assert task.get(other) == [], f"{label_line!r} should leave {other} paths empty"


def test_tests_plural_prose_label_contributes_nothing() -> None:
    task = _one_task("**Tests** (5 functions, `x.py`)")
    assert task.get("tests") == [], "plural Tests prose should not contribute test paths"


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("none (writes `docs/x/derive_readings.py`)", id="none-with-quoted-path"),
        pytest.param("**none** — x", id="bold-none-dash"),
        pytest.param("None.", id="none-period"),
        pytest.param("none", id="bare-none"),
    ],
)
def test_none_value_contributes_nothing(value: str) -> None:
    task = _one_task(f"**Production file**: {value}")
    assert task.get("production") == [], f"none value {value!r} should contribute no production paths"


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param("`none.py`", "none.py", id="none-py-token"),
        pytest.param("`tools/a.py`", "tools/a.py", id="tools-path"),
        pytest.param("nonexistent `a.py`", "a.py", id="nonexistent-word"),
        pytest.param("none/`a.py`", "a.py", id="none-slash"),
    ],
)
def test_none_rule_keeps_a_real_path(value: str, expected: str) -> None:
    task = _one_task(f"**Production file**: {value}")
    assert task.get("production") == [expected], f"real path in {value!r} should be retained"


def test_label_lines_accumulate() -> None:
    task = _one_task("**Production file**: `first.py`", "**Production file**: `second.py`")
    assert task.get("production") == ["first.py", "second.py"], "production paths should accumulate in line order"


def test_existing_fields_unchanged() -> None:
    old_lines = (
        "**Task shape**: `wiring`",
        "**WIRE**: `caller.py:run` -> `callee.call`",
        "**WIRE-PIN**: `test_caller_calls_callee`",
    )
    with_paths = _one_task(*old_lines, "**Production file**: `caller.py`", "**Test file**: `test_caller.py`")
    without_paths = _one_task(*old_lines)
    fields = ("shape", "wire", "pin", "wires", "pins")
    assert tuple(with_paths[key] for key in fields) == tuple(without_paths[key] for key in fields), "path labels must preserve old fields"
    assert with_paths["shape"] == "wiring", "existing task shape must still parse"
    assert with_paths["wire"] == "`caller.py:run` -> `callee.call`", "existing WIRE must still parse"
    assert with_paths["pin"] == "`test_caller_calls_callee`", "existing WIRE-PIN must still parse"
    assert with_paths["wires"] == [(None, with_paths["wire"])], "existing WIRE list must still parse"
    assert with_paths["pins"] == [(None, with_paths["pin"])], "existing WIRE-PIN list must still parse"


def test_field_re_is_unchanged() -> None:
    original = re.compile(
        r"^\s*(?:[-*•]\s+)?\*{0,2}\s*(?P<label>Task\s+shape|WIRE-PIN|WIRE)"
        r"(?:\s*(?P<suffix>[0-9][\w.]*))?\s*\*{0,2}"
        r"\s*(?:\([^)]*\))?\s*\*{0,2}\s*:\s*(?P<value>.*)$",
        re.IGNORECASE,
    )
    assert _FIELD_RE.pattern == original.pattern, "existing field regex pattern must remain unchanged"
    assert _FIELD_RE.flags == original.flags, "existing field regex flags must remain unchanged"


def test_corpus_old_fields_unperturbed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_ZZZ_PROBE", "1")
    env = hermetic_env()
    assert "CLAUDE_ZZZ_PROBE" not in env, "git subprocess must use the hermetic environment"
    listed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "*.impl-plan.md"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        env=env,
        timeout=60.0,
        check=True,
    )
    paths = [
        path for path in listed.stdout.splitlines()
        if "/archive/" not in f"/{path}"
    ]
    assert paths, "the checked-in implementation-plan corpus must be nonempty"

    corpus = []
    removed_python_lines = 0
    for path in paths:
        text = (REPO_ROOT / path).read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        removed = [line for line in lines if _PATHS_LABEL_LINE.match(line)]
        removed_python_lines += sum(bool(re.search(r"`[^`]+\.py`", line)) for line in removed)
        without_paths = "".join(line for line in lines if not _PATHS_LABEL_LINE.match(line))
        corpus.append((path, _parse_tasks(text), _parse_tasks(without_paths)))
    assert removed_python_lines > 0, "the corpus must remove a path-label line with a .py token"
    assert any(
        task["shape"] is not None or task["wire"] is not None or task["pin"] is not None
        for _, original, _ in corpus for task in original
    ), "the corpus must exercise existing parsed fields"

    fields = ("shape", "wire", "pin", "wires", "pins")
    for path, original, without_paths in corpus:
        assert [task["id"] for task in original] == [task["id"] for task in without_paths], f"{path}: task IDs changed after removing path labels"
        for before, after in zip(original, without_paths):
            assert tuple(before[key] for key in fields) == tuple(after[key] for key in fields), f"{path}: old fields changed in {before['id']}"
