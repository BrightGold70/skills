"""Caller-level RED for the fallback-agent fold and Claude gate."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

from test_h_mad_tdd_gate_judge import HOOK, TARGET, _bin, _gate, _root, _tree_b
from tdd_gate_support import decision, hermetic_env, hook_form, write_state

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import h_mad_tdd_judge as judge  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
BASE_SHA = "8ef6009f9491796d5d16b96a54e3b3185a8a6f19"
HOSTILE_OTHER = 'other "q"\\newline\n[H-MAD:MARKER]%'
TEST = "shared/tests/test_widget.py"
PROD = "shared/widget.py"
RED_BODY = "def test_red():\n    assert False, 'intentionally red'\n"


@pytest.fixture(autouse=True)
def _hostile_input(monkeypatch):
    for name in list(os.environ):
        if name.startswith(("CLAUDE", "CODEX")) or name == "HMAD_CODEX_UNAVAILABLE":
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")


@pytest.fixture(scope="module")
def base_dir(tmp_path_factory):
    dest = tmp_path_factory.mktemp("fallback-base")
    archive = dest / "base.tar"
    with archive.open("wb") as out:
        subprocess.run(["git", "-C", str(REPO), "archive", BASE_SHA, "h-mad"],
                       stdout=out, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
                       env=hermetic_env(), timeout=30, check=True)
    with tarfile.open(archive) as stream:
        stream.extractall(dest, filter="data")
    return dest


def _step(status="exhausted", **extra):
    return {"phase": "step5", "codex_status": status, **extra}


def _project(tmp_path, *, status="exhausted", fallback=..., other=None):
    root = tmp_path / "repo"
    root.mkdir()
    feat = _step(status)
    if fallback is not ...:
        feat["fallback_agent"] = fallback
    write_state(root, {HOSTILE_OTHER: other or {"phase": "step3"}, "feat": feat})
    test = root / TEST
    test.parent.mkdir(parents=True)
    test.write_text(RED_BODY, encoding="utf-8")
    assert test.is_file(), "derived failing test must exist"
    assert not (root / PROD).exists(), "target must be a new production file"
    return root


def _outcome(root, tmp_path, *, codex=False, unavailable=False, hook=HOOK, target=PROD):
    bin_dir = _bin(tmp_path, codex=codex)
    if not codex:
        assert shutil.which("codex", path=f"{bin_dir}:/usr/bin:/bin") is None
    env = {"HMAD_CODEX_UNAVAILABLE": "1"} if unavailable else {}
    result = _gate(root, arg=target, bin_dir=bin_dir, extra_env=env, hook=hook)
    return result, decision(result, hook_form(hook))


def _assert_class(out, expected):
    decision_name, kind = expected
    assert (out.decision, out.kind) == (decision_name, kind), (
        f"expected {expected}, got {out}"
    )


STATUSES = ("available", "unavailable", "exhausted", "unknown")
FALLBACKS = (..., None, "claude", "grok", "codex")


@pytest.mark.parametrize("status", STATUSES)
@pytest.mark.parametrize("fallback", FALLBACKS, ids=["absent", "null", "claude", "grok", "codex"])
@pytest.mark.parametrize("unavailable", [False, True], ids=["env-off", "env-on"])
@pytest.mark.parametrize("codex", [False, True], ids=["path-off", "path-on"])
def test_gate_matrix(tmp_path, status, fallback, unavailable, codex):
    root = _project(tmp_path, status=status, fallback=fallback)
    _, out = _outcome(root, tmp_path, codex=codex, unavailable=unavailable)
    codex_out = unavailable or status in ("unavailable", "exhausted") or not codex
    if not codex_out:
        expected = ("deny", "codex-authorship")
    elif fallback == "grok":
        expected = ("deny", "fallback-grok")
    elif fallback == "codex":
        expected = ("deny", "fallback-invalid")
    else:
        expected = ("allow", "")
    _assert_class(out, expected)


INVALIDS = (False, True, 0, "null", "", "Grok", {}, [])
ROUTES = ("environment", "status", "path")


@pytest.mark.parametrize("value", INVALIDS, ids=["false", "true", "zero", "string-null", "empty", "case", "object", "array"])
@pytest.mark.parametrize("route", ROUTES)
def test_invalid_class_blocks_each_value_alone(tmp_path, value, route):
    status = "exhausted" if route == "status" else "available"
    root = _project(tmp_path, status=status, fallback=value)
    _, out = _outcome(root, tmp_path, codex=route != "path", unavailable=route == "environment")
    _assert_class(out, ("deny", "fallback-invalid"))
    assert "fallback_agent=" + json.dumps(value, separators=(",", ":")) in out.reason
    assert "grok|claude" in out.reason


@pytest.mark.parametrize("value", INVALIDS, ids=["false", "true", "zero", "string-null", "empty", "case", "object", "array"])
def test_invalid_class_with_codex_available_is_block_codex(tmp_path, value):
    root = _project(tmp_path, status="available", fallback=value)
    _, out = _outcome(root, tmp_path, codex=True)
    _assert_class(out, ("deny", "codex-authorship"))


@pytest.mark.parametrize("route", ROUTES)
def test_json_null_control_falls_through(tmp_path, route):
    root = _project(tmp_path, status="exhausted" if route == "status" else "available", fallback=None)
    _, out = _outcome(root, tmp_path, codex=route != "path", unavailable=route == "environment")
    _assert_class(out, ("allow", ""))


@pytest.mark.parametrize("route", ROUTES)
def test_absent_key_control_falls_through(tmp_path, route):
    root = _project(tmp_path, status="exhausted" if route == "status" else "available")
    _, out = _outcome(root, tmp_path, codex=route != "path", unavailable=route == "environment")
    _assert_class(out, ("allow", ""))


@pytest.mark.parametrize("status", STATUSES)
@pytest.mark.parametrize("fallback", (..., None, "claude"), ids=["absent", "null", "claude"])
@pytest.mark.parametrize("unavailable", [False, True], ids=["env-off", "env-on"])
@pytest.mark.parametrize("codex", [False, True], ids=["path-off", "path-on"])
def test_absent_null_claude_match_the_base_hook(tmp_path, base_dir, status, fallback, unavailable, codex):
    root = _project(tmp_path, status=status, fallback=fallback)
    current, _ = _outcome(root, tmp_path, codex=codex, unavailable=unavailable)
    base_hook = base_dir / "h-mad/hooks/h-mad-tdd-gate.sh"
    base, _ = _outcome(root, tmp_path, codex=codex, unavailable=unavailable, hook=base_hook)
    assert (current.returncode, current.stdout, current.stderr) == (base.returncode, base.stdout, base.stderr)


def test_block_grok_stderr_names_the_four_things(tmp_path):
    root = _project(tmp_path, fallback="grok")
    _, out = _outcome(root, tmp_path)
    _assert_class(out, ("deny", "fallback-grok"))
    for required in ("hmad-dispatch exec grok", "--agent grok", "--set fallback_agent=claude",
                     "HMAD_CODEX_UNAVAILABLE does not override fallback_agent=grok"):
        assert required in out.reason


def test_block_grok_reads_the_active_features_fallback_agent(tmp_path):
    root = _project(tmp_path, fallback="grok")
    _, out = _outcome(root, tmp_path)
    _assert_class(out, ("deny", "fallback-grok"))
    assert "--feature feat" in out.reason


def test_other_feature_grok_does_not_change_active_outcome(tmp_path):
    root = _project(tmp_path, other={"phase": "step3", "codex_status": "exhausted", "fallback_agent": "grok"})
    _, out = _outcome(root, tmp_path)
    _assert_class(out, ("allow", ""))


@pytest.mark.parametrize("target", ["shared/test_widget.py", "shared/tests/helpers.py", "shared/fixtures/data.py",
                                     "docs/notes.md", "shared/config.toml", "shared/run.sh", "shared/widget.js"])
def test_exempt_files_stay_exempt_under_grok(tmp_path, target):
    root = _project(tmp_path, fallback="grok")
    _, out = _outcome(root, tmp_path, target=target)
    _assert_class(out, ("allow", ""))


def _stub_outcome(tmp_path, state_line):
    root = _root(tmp_path)
    hook, _ = _tree_b(tmp_path, state_line=state_line,
                      judge_line="TDD-JUDGE: ALLOW kind=red-measured source=impl-plan test=x\n")
    result = _gate(root, arg=str(root / TARGET), bin_dir=_bin(tmp_path), hook=hook)
    return decision(result, hook_form(hook))


PREFIX = "TDD-STATE: active codex-escape=yes blocker=0 records=1"
RECORD = " record=feat,exhausted,/x/docs/.bkit-memory.json,"


@pytest.mark.parametrize("field", ["", " fallback=codex:1", " fallback=grok:0"],
                         ids=["missing-field", "unknown-kind", "position-zero"])
def test_state_stub_fallback_field_is_judge_error(tmp_path, field):
    out = _stub_outcome(tmp_path, PREFIX + field + RECORD + "absent")
    _assert_class(out, ("deny", "judge-error"))


def test_state_stub_fallback_position_out_of_range_is_judge_error(tmp_path):
    out = _stub_outcome(tmp_path, PREFIX + " fallback=grok:2" + RECORD + "grok")
    _assert_class(out, ("deny", "judge-error"))


def test_fold_invalid_record_governs_over_grok(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    write_state(root, {"a": _step(fallback_agent="grok"), "b": _step(fallback_agent=False)})
    test = root / TEST
    test.parent.mkdir(parents=True)
    test.write_text(RED_BODY, encoding="utf-8")
    _, out = _outcome(root, tmp_path)
    _assert_class(out, ("deny", "fallback-invalid"))
    assert "fallback_agent=false" in out.reason and "--feature b" in out.reason


def test_second_active_record_holding_grok_blocks(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    state = write_state(root, {"a": _step(), "b": _step(fallback_agent="grok")})
    test = root / TEST
    test.parent.mkdir(parents=True)
    test.write_text(RED_BODY, encoding="utf-8")
    _, out = _outcome(root, tmp_path)
    _assert_class(out, ("deny", "fallback-grok"))
    assert "--feature b" in out.reason and str(state) in out.reason


def test_format_state_line_emits_the_fallback_fold(tmp_path):
    root = _project(tmp_path, fallback="grok")
    line = judge.format_state_line(judge.read_chain(root, None), root)
    assert " records=1 fallback=grok:1 record=" in line


@pytest.mark.parametrize("fold,values", [("none", [None]), ("grok:1", ["grok"]),
                                         ("invalid:2", ["grok", False])], ids=["none", "grok", "invalid"])
def test_fold_outcome_round_trips_through_the_gate_ere(tmp_path, fold, values):
    root = tmp_path / "repo"
    root.mkdir()
    write_state(root, {f"feat{i}": _step(fallback_agent=value) for i, value in enumerate(values, 1)})
    line = judge.format_state_line(judge.read_chain(root, None), root)
    literals = re.findall(r"^STATE_ACTIVE_RE='(.*)'$", HOOK.read_text(encoding="utf-8"), re.M)
    assert len(literals) == 1, "hook must have one STATE_ACTIVE_RE literal"
    match = re.fullmatch(literals[0], line)
    assert match is not None, f"state line must round-trip through the hook grammar: {line}"
    assert match.group(4) == fold, "the grammar's fallback capture must equal the judge fold"


@pytest.mark.parametrize("tag", ["invalid:false", "absent"], ids=["invalid-false", "absent"])
def test_state_stub_grok_fold_naming_a_non_grok_record_is_judge_error(tmp_path, tag):
    out = _stub_outcome(tmp_path, PREFIX + " fallback=grok:1" + RECORD + tag)
    _assert_class(out, ("deny", "judge-error"))


@pytest.mark.parametrize("tag", ["grok", "claude"])
def test_state_stub_invalid_fold_naming_a_valid_record_is_judge_error(tmp_path, tag):
    out = _stub_outcome(tmp_path, PREFIX + " fallback=invalid:1" + RECORD + tag)
    _assert_class(out, ("deny", "judge-error"))
    if tag == "grok":
        assert "disagrees with its record's tag grok" in out.reason


@pytest.mark.parametrize("fold,tag,kind,value", [("grok:1", "grok", "fallback-grok", ""),
                                                 ("invalid:1", "invalid:false", "fallback-invalid", "fallback_agent=false")],
                         ids=["grok", "invalid"])
def test_state_stub_agreeing_fold_refuses_its_own_kind(tmp_path, fold, tag, kind, value):
    out = _stub_outcome(tmp_path, PREFIX + f" fallback={fold}" + RECORD + tag)
    _assert_class(out, ("deny", kind))
    assert value in out.reason
