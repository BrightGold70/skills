"""--check-anchors flags a mutation row whose `test` names a pytest AUTO param id.

Row "refuse auto-generated parametrize ids in a spec's `test`" (skill-candidates,
2026-10-31): pytest names a non-literal parametrize value `<argname><N>`. Insert a
case before it and `[case3]` silently names a DIFFERENT case that still exists
and still passes, so the pin precheck admits it and the mutant is scored against
the wrong case. The rule reads the test file statically — `--check-anchors` runs
no tests — and reports a per-spec detail line, never a new summary word.

Calibration that shaped it: the three committed rows whose ids LOOK auto
(`[p2]`, `[p2]`, `[s2]`) all use explicit `ids=`, so an id-shape regex alone would
flag every one of them. A segment is flagged only when it equals a REAL argname
of that test's parametrize plus digits, and that parametrize has no explicit ids.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from h_mad_mutation_harness import _check_anchors, precheck_spec  # noqa: E402

TARGET = "SENTINEL = 1\n"


def _spec(tmp_path: Path, test_source: str | None, test_id: str) -> Path:
    (tmp_path / "target.py").write_text(TARGET, encoding="utf-8")
    if test_source is not None:
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_t.py").write_text(test_source, encoding="utf-8")
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({
        "command": ["python3", "-m", "pytest", "-q"],
        "target_command": ["python3", "-m", "pytest", "-q"],
        "mutations": [{
            "name": "m1", "file": "target.py",
            "find": "SENTINEL = 1", "replace": "SENTINEL = 2",
            "test": f"tests/test_t.py::{test_id}",
        }],
    }), encoding="utf-8")
    return spec


def _flags(spec: Path) -> tuple[list, list]:
    result = precheck_spec(spec)
    return result["auto_param_ids"], result["param_ids_unjudged"]


AUTO = '''import pytest
@pytest.mark.parametrize("case", [{"a": 1}, {"a": 2}])
def test_x(case):
    assert case
'''


def test_an_auto_index_id_is_flagged(tmp_path: Path) -> None:
    auto, unjudged = _flags(_spec(tmp_path, AUTO, "test_x[case1]"))
    assert [e["segment"] for e in auto] == ["case1"]
    assert unjudged == []


def test_explicit_ids_are_not_flagged__the_calibration_case(tmp_path: Path) -> None:
    source = '''import pytest
@pytest.mark.parametrize("drop,pass_number", [(1, 2), (3, 4)], ids=["p2", "p1"])
def test_x(drop, pass_number):
    assert drop
'''
    assert _flags(_spec(tmp_path, source, "test_x[p2]")) == ([], [])


def test_a_shape_matching_value_that_is_not_argname_plus_digits_is_not_flagged(
    tmp_path: Path,
) -> None:
    # `s2` is shaped like an auto id but `stage` is the argname: a literal value.
    source = '''import pytest
@pytest.mark.parametrize("stage", ["resmoke", "s2"])
def test_x(stage):
    assert stage
'''
    assert _flags(_spec(tmp_path, source, "test_x[s2]")) == ([], [])


def test_argname_plus_digits_inside_a_literal_value_is_not_flagged(tmp_path: Path) -> None:
    # Calibration hit (H4, test_h_mad_tdd_gate_judge.py): the string value
    # "allow-rc1" splits on '-' into a segment `rc1` that equals argname `rc` + 1.
    # `rc` holds only int literals, which pytest renders as `1`, never `rc1`.
    source = '''import pytest
@pytest.mark.parametrize("variant,rc", [("allow-rc1", 1), ("x", 0)])
def test_x(variant, rc):
    assert variant
'''
    assert _flags(_spec(tmp_path, source, "test_x[allow-rc1-1]")) == ([], [])


def test_a_name_valued_case_is_auto__the_tdd_judge_shape(tmp_path: Path) -> None:
    # The six real hits: a module constant as the value gets `<argname><N>`.
    source = '''import pytest
_OLD = object()
@pytest.mark.parametrize("line,target", [("E   x", _OLD), ("E   y", _OLD)])
def test_x(line, target):
    assert line
'''
    auto, unjudged = _flags(_spec(tmp_path, source, "test_x[E   y-target1]"))
    assert [e["segment"] for e in auto] == ["target1"] and unjudged == []


def test_a_non_literal_case_list_is_cannot_judge(tmp_path: Path) -> None:
    source = '''import pytest
CASES = [{"a": 1}]
@pytest.mark.parametrize("case", CASES)
def test_x(case):
    assert case
'''
    auto, unjudged = _flags(_spec(tmp_path, source, "test_x[case0]"))
    assert auto == [] and len(unjudged) == 1


def test_pytest_param_with_id_is_not_flagged(tmp_path: Path) -> None:
    source = '''import pytest
@pytest.mark.parametrize("case", [pytest.param({}, id="case1"), pytest.param({}, id="case2")])
def test_x(case):
    assert case is not None
'''
    assert _flags(_spec(tmp_path, source, "test_x[case1]")) == ([], [])


def test_stacked_parametrize_ids_are_split_on_hyphens(tmp_path: Path) -> None:
    source = '''import pytest
@pytest.mark.parametrize("mode", ["fast", "slow"])
@pytest.mark.parametrize("cfg", [{"a": 1}, {"a": 2}])
def test_x(cfg, mode):
    assert cfg
'''
    auto, unjudged = _flags(_spec(tmp_path, source, "test_x[cfg0-fast]"))
    assert [e["segment"] for e in auto] == ["cfg0"]
    assert unjudged == []


def test_descriptive_hyphenated_ids_are_never_flagged(tmp_path: Path) -> None:
    source = '''import pytest
@pytest.mark.parametrize("load", ["fg-cpu-1"])
def test_x(load):
    assert load
'''
    assert _flags(_spec(tmp_path, source, "test_x[fg-cpu-1]")) == ([], [])


def test_an_unreadable_test_file_is_cannot_judge_not_ok(tmp_path: Path) -> None:
    auto, unjudged = _flags(_spec(tmp_path, None, "test_x[case1]"))
    assert auto == []
    assert len(unjudged) == 1 and "m1" == unjudged[0]["name"]


def test_params_from_outside_a_literal_parametrize_are_cannot_judge(tmp_path: Path) -> None:
    # Fixture `params=`, `pytest_generate_tests`, a class-level mark: the id's
    # origin is not on the function, so a silent OK would be a guess.
    source = '''import pytest
def test_x(case):
    assert case
'''
    auto, unjudged = _flags(_spec(tmp_path, source, "test_x[case1]"))
    assert auto == [] and len(unjudged) == 1


def test_an_unbracketed_test_is_never_inspected(tmp_path: Path) -> None:
    # No test file at all: an unbracketed id must not even be read.
    assert _flags(_spec(tmp_path, None, "test_x")) == ([], [])


def test_the_sweep_prints_a_detail_line_and_keeps_its_summary_verdict(
    tmp_path: Path, capsys,
) -> None:
    rc = _check_anchors([_spec(tmp_path, AUTO, "test_x[case1]")])
    out = capsys.readouterr().out
    assert rc == 0, out                        # advisory: the verdict is unchanged
    assert "[H-MAD] anchors ANCHORS_OK" in out
    assert "auto-param-id: m1 :: tests/test_t.py::test_x[case1] (case1)" in out
