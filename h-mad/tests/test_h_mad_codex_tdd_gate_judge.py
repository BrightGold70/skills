"""Caller-level RED tests for the Codex hook's judge and state-chain wires."""
from __future__ import annotations

import json
import importlib.util
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import time

import pytest

from tdd_gate_support import assert_case_insensitive, build_venv, detaching_sleeper, fake_venv, hermetic_env, shell_corpus, sleeper, stop_detached, write_plan, write_state


CODEX_GATE = Path(__file__).resolve().parents[1] / "hooks" / "h-mad-codex-tdd-gate.py"
HOSTILE_KEY = 'agent "q"\\newline\n[H-MAD:MARKER]%'
TARGET = "hematology-paper-writer/tools/w.py"


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "root"
    root.mkdir()
    write_state(root, {HOSTILE_KEY: {"phase": "step5"}})
    return root


def _file(root: Path, relative: str, body: str = "# governed production\n") -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _payload(target: str = TARGET, *, cwd: str | None = None) -> dict:
    payload = {"tool_name": "apply_patch", "tool_input": {
        "patch": f"*** Update File: {target}\n",
    }}
    if cwd is not None:
        payload["cwd"] = cwd
    return payload


def _run(root: Path, payload: dict, *, gate: Path = CODEX_GATE, timeout: float = 60.0,
         path: str | None = None):
    start = time.monotonic()
    try:
        process = subprocess.run(
            [sys.executable, str(gate)], input=json.dumps(payload), capture_output=True,
            text=True, cwd=root,
            env=hermetic_env(CODEX_PROJECT_DIR=str(root), HMAD_STUB_HOSTILE="all",
                             **({"PATH": path} if path is not None else {})),
            timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired:
        return "invalid", "subprocess timed out", time.monotonic() - start
    output = process.stdout.strip()
    elapsed = time.monotonic() - start
    if process.returncode != 0:
        return "invalid", output, elapsed
    if output in ("", "{}"):
        return "allow", "", elapsed
    try:
        decision = json.loads(output)["hookSpecificOutput"]
        if decision["permissionDecision"] == "deny":
            return "deny", decision["permissionDecisionReason"], elapsed
    except (ValueError, KeyError, TypeError):
        pass
    return "invalid", output, elapsed


def _pid_gone(pidfile: Path) -> None:
    assert pidfile.exists(), "the bounded judge never started the sleeper"
    pid = int(pidfile.read_text(encoding="utf-8"))
    deadline = time.monotonic() + 0.5
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.01)
    with pytest.raises(ProcessLookupError, match=""):
        os.kill(pid, 0)


@pytest.mark.parametrize("kind", [
    "red-measured", "no-test-resolved", "test-missing", "venv-escapes-root",
    "pytest-missing", "pytest-error", "no-tests-ran", "no-summary",
    "test-passing", "timeout", "judge-timeout", "judge-error",
])
def test_codex_gate_kind(tmp_path, kind):
    root = _root(tmp_path)
    _file(root, TARGET)
    target = TARGET
    if kind != "test-missing":
        body = "def test_red():\n    assert False\n"
        if kind == "pytest-error":
            body = "import module_that_does_not_exist_for_gate\n"
        elif kind == "no-tests-ran":
            body = "# no tests collected\n"
        elif kind == "test-passing":
            body = "def test_green():\n    assert True\n"
        _file(root, "hematology-paper-writer/tests/test_w.py", body)

    if kind == "no-test-resolved":
        target = "tools/x.py"
        _file(root, target)
    elif kind == "venv-escapes-root":
        outside = tmp_path / "outside"
        fake_venv(outside, "exit 0")
        (root / "hematology-paper-writer/.venv").symlink_to(outside / ".venv", target_is_directory=True)
    elif kind == "pytest-missing":
        build_venv(root / "hematology-paper-writer/.venv", with_pytest=False)
    elif kind == "no-summary":
        fake_venv(root / "hematology-paper-writer", "exit 1")
    elif kind == "timeout":
        python = fake_venv(root / "hematology-paper-writer", "exit 0")
        pidfile = tmp_path / "sleeper.pid"
        sleeper(python, pidfile, seconds=90)
    elif kind == "judge-timeout":
        python = fake_venv(root / "hematology-paper-writer", "exit 0")
        pidfile = tmp_path / "detached.pid"
        detaching_sleeper(python, pidfile, seconds=90, parent_seconds=90)
    elif kind == "judge-error":
        other = tmp_path / "B"
        gate = other / "hooks/h-mad-codex-tdd-gate.py"
        gate.parent.mkdir(parents=True)
        shutil.copyfile(CODEX_GATE, gate)
        _file(other, "scripts/h_mad_tdd_judge.py", 'raise ImportError("broken judge for AC-5.4")\n')

    try:
        verdict, reason, elapsed = _run(
            root, _payload(target), gate=gate if kind == "judge-error" else CODEX_GATE,
            timeout=120.0 if kind in ("timeout", "judge-timeout") else 60.0,
        )
    finally:
        if kind == "judge-timeout":
            stop_detached(pidfile)
    if kind == "red-measured":
        assert verdict == "allow", (verdict, reason)
    else:
        assert verdict == "deny", f"{kind}: expected JSON deny, got {verdict}: {reason}"
        assert f"kind={kind}" in reason, f"{kind}: {reason}"
    if kind == "timeout":
        assert elapsed < 60.0, f"judge exceeded its 40-second budget: {elapsed:.2f}s"
        _pid_gone(pidfile)


@pytest.mark.parametrize("depth", ["one-absent", "two-absent"])
def test_codex_absent_intermediate_dirs_judge_the_real_target(tmp_path, depth):
    root = _root(tmp_path)
    if depth == "one-absent":
        (root / "hematology-paper-writer").mkdir()
    target = "hematology-paper-writer/tools/x.py"
    verdict, reason, _ = _run(root, _payload(target))
    assert verdict == "deny", (verdict, reason)
    assert "kind=test-missing" in reason, reason
    assert "hematology-paper-writer/tests/test_x.py" in reason, reason


def test_codex_gate_judge_timeout_reason(tmp_path):
    root = _root(tmp_path)
    _file(root, TARGET)
    other = tmp_path / "B"
    gate = other / "hooks/h-mad-codex-tdd-gate.py"
    gate.parent.mkdir(parents=True)
    shutil.copyfile(CODEX_GATE, gate)
    stub = other / "scripts/h_mad_tdd_judge.py"
    stub.parent.mkdir(parents=True)
    shutil.copyfile(CODEX_GATE.parents[1] / "scripts/h_mad_target_identity.py",
                    stub.parent / "h_mad_target_identity.py")
    stub.write_text(
        "from types import SimpleNamespace\n"
        "def read_chain(root, target):\n"
        "    return SimpleNamespace(value='active', records=())\n"
        "def judge(root, target, records):\n"
        "    return SimpleNamespace(decision='DENY', kind='judge-timeout', reason='stub')\n",
        encoding="utf-8",
    )
    verdict, reason, _ = _run(root, _payload(), gate=gate)
    assert verdict == "deny", f"judge-timeout stub must deny: {verdict}: {reason}"
    assert "kind=judge-timeout" in reason, reason


def test_root_step5_governs_a_subproject_with_its_own_state(tmp_path):
    root = _root(tmp_path)
    write_state(root / "hematology-paper-writer", {})
    _file(root, TARGET)
    _file(root, "hematology-paper-writer/tests/test_w.py", "def test_green():\n    assert True\n")
    verdict, reason, _ = _run(root, _payload())
    assert verdict == "deny", f"read_chain must retain root step5: {verdict}: {reason}"
    assert "kind=test-passing" in reason


def _cwd_project(tmp_path: Path, test_body: str):
    root = _root(tmp_path)
    relative = "hematology-paper-writer/tools/review_round/guideline_excerpts.py"
    _file(root, relative)
    _file(root, "hematology-paper-writer/tests/test_guideline_excerpts.py", test_body)
    write_plan(root, HOSTILE_KEY, (
        "## Task 1: review_round\n"
        "**Production file**: `tools/review_round/guideline_excerpts.py`\n"
        "**Test file**: `tests/test_guideline_excerpts.py`\n"
    ))
    alias = tmp_path / "alias"
    alias.symlink_to(root, target_is_directory=True)
    cwd = str(alias / "hematology-paper-writer")
    assert os.path.realpath(cwd) != cwd
    return root, cwd, relative


def test_payload_cwd_base_resolves_a_subproject_relative_target(tmp_path):
    root, cwd, _ = _cwd_project(tmp_path, "def test_red():\n    assert False\n")
    verdict, reason, _ = _run(root, _payload("tools/review_round/guideline_excerpts.py", cwd=cwd))
    assert verdict == "allow", f"payload cwd must resolve the RED project target: {verdict}: {reason}"


def test_payload_cwd_deny_names_the_prefixed_path(tmp_path):
    root, cwd, relative = _cwd_project(tmp_path, "def test_green():\n    assert True\n")
    verdict, reason, _ = _run(root, _payload("tools/review_round/guideline_excerpts.py", cwd=cwd))
    assert verdict == "deny", f"payload cwd must resolve the GREEN project target: {verdict}: {reason}"
    assert relative in reason, f"deny must name root-relative project path: {reason}"


def test_payload_cwd_outside_the_root_falls_back_to_the_root(tmp_path):
    root = _root(tmp_path)
    _file(root, TARGET)
    _file(root, "hematology-paper-writer/tests/test_w.py", "def test_red():\n    assert False\n")
    verdict, reason, _ = _run(root, _payload(cwd=str(tmp_path)))
    assert verdict == "allow", f"outside cwd must fall back to root: {verdict}: {reason}"


def test_fifo_state_on_the_chain_denies_a_write_without_blocking(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    state = root / "hematology-paper-writer/docs/.bkit-memory.json"
    state.parent.mkdir(parents=True)
    os.mkfifo(state)
    verdict, reason, elapsed = _run(root, _payload(), timeout=5.0)
    assert elapsed < 1.0, f"FIFO state read blocked the write for {elapsed:.2f}s"
    assert verdict == "deny" and "unreadable" in reason, (verdict, reason)


def test_fifo_state_off_the_chain_denies_shell_without_blocking(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    state = root / "other/docs/.bkit-memory.json"
    state.parent.mkdir(parents=True)
    os.mkfifo(state)
    verdict, reason, elapsed = _run(
        root, {"tool_name": "shell_command", "tool_input": {"command": "ls"}}, timeout=5.0,
    )
    assert elapsed < 1.0, f"FIFO state scan blocked the shell for {elapsed:.2f}s"
    assert verdict == "deny" and "state is unreadable" in reason, (verdict, reason)


def test_unsearchable_docs_on_the_chain_denies_although_the_scan_is_inactive(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    state = write_state(root / "hematology-paper-writer", {HOSTILE_KEY: {"phase": "step5"}})
    docs = state.parent
    docs.chmod(0)
    try:
        verdict, reason, _ = _run(root, _payload())
    finally:
        docs.chmod(0o755)
    assert verdict == "deny", f"unsearchable governing state must fail closed: {verdict}: {reason}"
    assert "kind=judge-error" in reason, reason


def test_codex_gate_keeps_no_private_resolver():
    source = CODEX_GATE.read_text(encoding="utf-8")
    for token in ("_target_phase5_status", "_derived_test", "_test_exit", "h_mad_derive_test_path.sh"):
        assert token not in source, f"hook still owns private resolution: {token}"


def _expect_gate(root: Path, target: str, expected: str, kind: str = "", *, cwd: str | None = None) -> str:
    verdict, reason, _ = _run(root, _payload(target, cwd=cwd))
    assert verdict == expected, f"{target}: expected {expected} kind={kind}, got {verdict}: {reason}"
    if kind:
        assert f"kind={kind}" in reason, f"{target}: expected kind={kind}, got {verdict}: {reason}"
    return reason



@pytest.mark.parametrize("relative", ["tests/./sub/../../src/prod.py", "tests/./../src/prod.py"])
def test_codex_dot_then_dotdot_into_production_denies(tmp_path, relative):
    root = _root(tmp_path)
    (root / "tests/sub").mkdir(parents=True)
    _file(root, "src/prod.py")
    assert os.path.samefile(str(root) + "/" + relative, root / "src/prod.py"), "kernel precondition"
    _expect_gate(root, relative, "deny")

def test_codex_dotdot_after_symlink_denies(tmp_path):
    root = _root(tmp_path)
    _file(root, "src/prod.py")
    (root / "tests").mkdir()
    (root / "src/sub").mkdir()
    (root / "tests/l").symlink_to("../src/sub", target_is_directory=True)
    _expect_gate(root, "tests/l/../prod.py", "deny", "no-test-resolved")


@pytest.mark.parametrize("on_disk,spelled", [("Case", "case"), ("case", "Case")], ids=["forward", "reverse"])
def test_codex_case_root_m8_denies(tmp_path, on_disk, spelled):
    root = tmp_path / on_disk / "tests/proj"
    root.mkdir(parents=True)
    assert_case_insensitive(tmp_path)
    _file(root, "src/prod.py")
    write_state(root, {HOSTILE_KEY: {"phase": "step5"}})
    _expect_gate(root, str(tmp_path / spelled / "tests/proj/src/prod.py"), "deny", "no-test-resolved")


@pytest.mark.parametrize("on_disk,spelled", [("Case", "case"), ("case", "Case")], ids=["forward", "reverse"])
def test_codex_case_spelled_root_m8_denies(tmp_path, on_disk, spelled):
    physical = tmp_path / on_disk / "proj"
    physical.mkdir(parents=True)
    assert_case_insensitive(tmp_path)
    _file(physical, "src/prod.py")
    write_state(physical, {HOSTILE_KEY: {"phase": "step5"}})
    root = tmp_path / spelled / "proj"
    # Path.resolve keeps the spelled case, so only the on-disk canonicaliser can
    # make the target relative to the root.
    assert str(root.resolve()) != str(physical.resolve())

    _expect_gate(root, "src/prod.py", "deny", "no-test-resolved")


def test_codex_case_directory_m9_denies(tmp_path):
    root = _root(tmp_path)
    assert_case_insensitive(root)
    _file(root, "Tests/prod.py")
    _expect_gate(root, "tests/prod.py", "deny", "no-test-resolved")


def test_codex_toward_allow_m10(tmp_path):
    root = _root(tmp_path)
    assert_case_insensitive(root)
    _file(root, "fixtures/helper.py")
    _expect_gate(root, "FIXTURES/helper.py", "allow")


def test_codex_m11_stays_allow(tmp_path):
    root = _root(tmp_path)
    _file(root, "tests/helper.py")
    (root / "src").mkdir()
    (root / "src/tl").symlink_to("../tests", target_is_directory=True)
    _expect_gate(root, "src/tl/helper.py", "allow")


@pytest.mark.parametrize("relative", ["src/brandnew.py", "src/newpkg/mod.py"], ids=["absent-leaf", "absent-parent"])
def test_codex_new_file_denies_without_judge_error(tmp_path, relative):
    root = _root(tmp_path)
    (root / "src").mkdir()
    _expect_gate(root, relative, "deny", "no-test-resolved")


def test_codex_hard_link_alias_denies(tmp_path):
    root = _root(tmp_path)
    source = _file(root, "src/prod.py")
    alias = root / "src/test_prod.py"
    os.link(source, alias)
    assert os.stat(source).st_ino == os.stat(alias).st_ino, "hard-link fixture must share an inode"
    _expect_gate(root, "src/test_prod.py", "deny", "no-test-resolved")


def test_codex_hardlink_mixed_names_judges_the_production_name(tmp_path):
    root = _root(tmp_path)
    target = "hematology-paper-writer/tools/test_a.py"
    alias = _file(root, target)
    production = root / "hematology-paper-writer/tools/z.py"
    os.link(alias, production)
    assert alias.stat().st_ino == production.stat().st_ino

    reason = _expect_gate(root, target, "deny", "test-missing")
    assert "hematology-paper-writer/tests/test_z.py" in reason, reason


def test_codex_fold_existing_leaf_denies(tmp_path):
    root = _root(tmp_path)
    _file(root, "src/prod.PY")
    _expect_gate(root, "src/prod.PY", "deny", "no-test-resolved")


@pytest.mark.parametrize("relative", ["src/new.PY", "src/new.pY", "src/new.Py"], ids=["m3", "pY", "Py"])
def test_codex_fold_new_leaf_denies(tmp_path, relative):
    root = _root(tmp_path)
    (root / "src").mkdir()
    _expect_gate(root, relative, "deny", "no-test-resolved")


@pytest.mark.parametrize("relative,expected", [
    ("sub/test_x.PY", "allow"), ("sub/x_test.PY", "allow"),
    ("sub/conftest.PY", "allow"), ("sub/TEST_x.py", "deny"),
])
def test_codex_test_shaped_names_stay_exempt(tmp_path, relative, expected):
    root = _root(tmp_path)
    (root / "sub").mkdir()
    _expect_gate(root, relative, expected, "no-test-resolved" if expected == "deny" else "")


def test_codex_trailing_space_is_not_folded(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    from h_mad_target_identity import fold_py_suffix

    assert fold_py_suffix("src/prod.py ") == "src/prod.py "
    assert fold_py_suffix("src/prod.PY ") == "src/prod.PY "
    root = _root(tmp_path)
    (root / "src").mkdir()
    # FR-4 trims patch header whitespace, so this target is now governed.
    _expect_gate(root, "src/prod.py ", "deny", "no-test-resolved")


def test_codex_d1_repro_patch_denies(tmp_path):
    root = _root(tmp_path)
    _file(root, "src/prod.PY")
    verdict, reason, _ = _run(root, {"tool_name": "apply_patch", "tool_input": {
        "patch": "*** Begin Patch\n*** Update File: src/prod.PY\n@@\n-X = 1\n+X = 2\n*** End Patch\n"}})
    assert verdict == "deny", f"D-1 patch was {verdict}: {reason}"
    assert "kind=no-test-resolved" in reason, reason


@pytest.mark.parametrize("suffix", [
    pytest.param("\r", id="crlf"), pytest.param(" ", id="space"),
    pytest.param("\t", id="tab"), pytest.param("\u00a0", id="nbsp"),
    pytest.param("\u3000", id="u3000"), pytest.param("\u2028", id="u2028"),
    pytest.param("\u0085", id="u0085"), pytest.param("\u2003", id="u2003"),
    pytest.param("\v", id="vt"), pytest.param("\f", id="ff"),
])
def test_codex_trailing_header_whitespace_denies(tmp_path, suffix):
    root = _root(tmp_path)
    _file(root, "src/prod.py")
    patch = f"*** Begin Patch\n*** Update File: src/prod.py{suffix}\n@@\n-a\n+b\n*** End Patch\n"
    verdict, reason, _ = _run(root, {"tool_name": "apply_patch", "tool_input": {"patch": patch}})
    assert verdict == "deny", f"trailing header whitespace must gate src/prod.py: {verdict}: {reason}"
    assert "kind=no-test-resolved" in reason, f"trailing header whitespace lost the production target: {reason}"


@pytest.mark.parametrize("variant,patch", [
    pytest.param("m16", "*** Begin Patch\n *** Update File: src/prod.py\n@@\n-a\n+b\n*** End Patch\n", id="m16"),
    pytest.param("m17", "*** Begin Patch\n*** Add File: docs/x.md\n+x\n  *** Update File: src/prod.py\n@@\n-a\n+b\n*** End Patch\n", id="m17"),
])
def test_codex_indented_header_denies(tmp_path, variant, patch):
    root = _root(tmp_path)
    _file(root, "src/prod.py")
    verdict, reason, _ = _run(root, {"tool_name": "apply_patch", "tool_input": {"patch": patch}})
    assert verdict == "deny", f"{variant} indented header must gate src/prod.py: {verdict}: {reason}"
    assert "kind=no-test-resolved" in reason, f"{variant} indented header lost the production target: {reason}"


def test_codex_move_to_trailing_space_denies(tmp_path):
    root = _root(tmp_path)
    _file(root, "docs/a.md", "a\n")
    verdict, reason, _ = _run(root, {"tool_name": "apply_patch", "tool_input": {
        "patch": "*** Begin Patch\n*** Update File: docs/a.md\n*** Move to: src/prod2.py \n@@\n-a\n+b\n*** End Patch\n",
    }})
    assert verdict == "deny", f"trailing-space Move to must gate src/prod2.py: {verdict}: {reason}"
    assert "kind=no-test-resolved" in reason, f"trailing-space Move to lost its production target: {reason}"


@pytest.mark.parametrize("variant,path", [
    pytest.param("m20", "src/n.py\x1f", id="m20"),
    pytest.param("u0001", "src/pr\x01od.py", id="u0001"),
])
def test_codex_control_byte_header_is_judge_error(tmp_path, variant, path):
    root = _root(tmp_path)
    patch = f"*** Begin Patch\n*** Add File: {path}\n+x\n*** End Patch\n"
    verdict, reason, _ = _run(root, {"tool_name": "apply_patch", "tool_input": {"patch": patch}})
    assert verdict == "deny", f"{variant} control byte header must be refused: {verdict}: {reason}"
    assert "kind=judge-error" in reason, f"{variant} control byte header needs judge-error: {reason}"
    assert "header" in reason.lower(), f"{variant} refusal must name the bad header: {reason}"


@pytest.mark.parametrize("header", [
    "*** update file: src/prod.py", "***  Update File: src/prod.py",
    "*** Update File:src/prod.py", "**** Update File: src/prod.py",
    "*** Update File:\tsrc/prod.py",
], ids=["lowercase", "double-space", "missing-space", "extra-star", "tab-after-colon"])
def test_codex_inexact_marker_is_unidentified(tmp_path, header):
    root = _root(tmp_path)
    _file(root, "src/prod.py")
    patch = f"*** Begin Patch\n{header}\n@@\n-a\n+b\n*** End Patch\n"
    verdict, reason, _ = _run(root, {"tool_name": "apply_patch", "tool_input": {"patch": patch}})
    assert verdict == "deny", f"inexact marker must be unidentified: {header!r}: {verdict}: {reason}"
    assert "could not identify" in reason, f"inexact marker was recognized: {header!r}: {reason}"
    assert "kind=" not in reason, f"inexact marker acquired a target kind: {header!r}: {reason}"


@pytest.mark.parametrize("variant,path", [
    pytest.param("m20", "src/n.py\x1f", id="m20"),
    pytest.param("u0001", "src/pr\x01od.py", id="u0001"),
])
def test_codex_control_byte_header_step3_allows(tmp_path, variant, path):
    root = _root(tmp_path)
    write_state(root, {HOSTILE_KEY: {"phase": "step3"}})
    patch = f"*** Begin Patch\n*** Add File: {path}\n+x\n*** End Patch\n"
    verdict, reason, _ = _run(root, {"tool_name": "apply_patch", "tool_input": {"patch": patch}})
    assert verdict == "allow", f"{variant} non-governing control header raised or denied: {verdict}: {reason}"


def test_codex_bad_header_does_not_raise_when_inactive(tmp_path):
    root = _root(tmp_path)
    write_state(root, {HOSTILE_KEY: {"phase": "step3"}})
    patch = "*** Begin Patch\n*** Update File: \n@@\n-a\n+b\n*** End Patch\n"
    verdict, reason, _ = _run(root, {"tool_name": "apply_patch", "tool_input": {"patch": patch}})
    assert verdict == "allow", f"inactive bad header must not raise or deny: {verdict}: {reason}"
    assert "raised" not in reason, f"inactive bad header raised: {reason}"


@pytest.mark.parametrize("code_point,trimmed", [
    pytest.param(0x20, True, id="u0020"), pytest.param(0x09, True, id="u0009"),
    pytest.param(0x0B, True, id="u000b"), pytest.param(0x0C, True, id="u000c"),
    pytest.param(0x0D, True, id="u000d"), pytest.param(0x85, True, id="u0085"),
    pytest.param(0xA0, True, id="u00a0"), pytest.param(0x3000, True, id="u3000"),
    pytest.param(0x2028, True, id="u2028"), pytest.param(0x1C, False, id="u001c"),
    pytest.param(0x1F, False, id="u001f"), pytest.param(0x200B, False, id="u200b"),
    pytest.param(0xFEFF, False, id="ufeff"),
])
def test_codex_trim_set_code_points(code_point, trimmed):
    spec = importlib.util.spec_from_file_location("codex_gate_header_trim_test", CODEX_GATE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    parser = getattr(module, "_patch_header_paths", None)
    assert callable(parser), "header trim-set parser _patch_header_paths is missing"
    character = chr(code_point)
    paths, bad_header = parser(f"{character}*** Update File: src/prod.py{character}\n")
    if trimmed:
        assert (paths, bad_header) == (["src/prod.py"], ""), f"U+{code_point:04X} must trim at both ends: {paths!r}, {bad_header!r}"
    else:
        assert paths == [], f"U+{code_point:04X} must not trim at the leading end: {paths!r}"
        assert bad_header == "", f"U+{code_point:04X} leading non-trim is not a recognized bad header: {bad_header!r}"
        paths, bad_header = parser(f"*** Update File: src/prod.py{character}\n")
        if code_point in {0x1C, 0x1F}:
            assert paths == [] and character in bad_header, f"U+{code_point:04X} trailing control must be a bad header: {paths!r}, {bad_header!r}"
        else:
            assert (paths, bad_header) == ([f"src/prod.py{character}"], ""), f"U+{code_point:04X} must remain in the path: {paths!r}, {bad_header!r}"


def test_patch_header_paths_split_on_newline_only():
    spec = importlib.util.spec_from_file_location("codex_gate_header_split_test", CODEX_GATE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    parser = getattr(module, "_patch_header_paths", None)
    assert callable(parser), "newline-only patch header parser _patch_header_paths is missing"
    header = "*** Update File: src/prod.py\u2028inside\x1cstill\u0085one-line"
    paths, bad_header = parser(f"*** Begin Patch\n{header}\n*** End Patch\n")
    assert paths == [], f"newline-only split must not produce a partial path: {paths!r}"
    assert bad_header == header, f"newline-only split must retain the whole bad header: {bad_header!r}"


def test_codex_empty_header_path_is_judge_error(tmp_path):
    root = _root(tmp_path)
    patch = "*** Begin Patch\n*** Update File: \n@@\n-a\n+b\n*** End Patch\n"
    verdict, reason, _ = _run(root, {"tool_name": "apply_patch", "tool_input": {"patch": patch}})
    assert verdict == "deny", f"empty header path must be refused: {verdict}: {reason}"
    assert "kind=judge-error" in reason, f"empty header path must be judge-error: {reason}"
    assert "*** Update File:" in reason, f"empty path refusal must name its header: {reason}"
    assert "could not identify" not in reason, f"empty path was treated as an unidentified target: {reason}"


def _unresolvable(root: Path, variant: str) -> tuple[str, str]:
    if variant == "m12":
        (root / "docs/d.md").symlink_to("../src/newprod.py")
        return "docs/d.md", str(root / "docs/d.md")
    if variant == "m13-leaf":
        (root / "src").mkdir()
        (root / "src/dang.py").symlink_to("nowhere/x.py")
        return "src/dang.py", str(root / "src/dang.py")
    if variant == "m13-intermediate":
        (root / "lnk").symlink_to("nowhere", target_is_directory=True)
        return "lnk/x.py", str(root / "lnk")
    (root / "src").mkdir()
    (root / "src/loopa.py").symlink_to("loopb.py")
    (root / "src/loopb.py").symlink_to("loopa.py")
    return "src/loopa.py", str(root / "src/loopa.py")


@pytest.mark.parametrize("variant", ["m12", "m13-leaf", "m13-intermediate", "m14"])
def test_codex_unresolvable_governed_is_judge_error(tmp_path, variant):
    root = _root(tmp_path)
    target, component = _unresolvable(root, variant)
    reason = _expect_gate(root, target, "deny", "judge-error")
    assert component in reason, f"missing unresolvable component {component}: {reason}"


@pytest.mark.parametrize("variant", ["m13-leaf", "m13-intermediate", "m14"])
def test_codex_unresolvable_step3_allows(tmp_path, variant):
    root = _root(tmp_path)
    write_state(root, {HOSTILE_KEY: {"phase": "step3"}})
    target, _ = _unresolvable(root, variant)
    _expect_gate(root, target, "allow")


def test_codex_resolver_reports_loop_unresolvable(tmp_path):
    root = _root(tmp_path)
    target, _ = _unresolvable(root, "m14")
    spec = importlib.util.spec_from_file_location("codex_gate_identity_test", CODEX_GATE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        identity = module._relative_target(root, target)
    except (OSError, RuntimeError) as exc:
        pytest.fail(f"loop resolver raised {type(exc).__name__} instead of returning unresolvable Identity: {exc}")
    assert getattr(identity, "unresolvable", False) is True, f"loop resolver returned {identity!r}"


@pytest.mark.parametrize("cell", ["a", "b"])
def test_codex_unreadable_component_step5(tmp_path, cell):
    _unreadable_component_case(tmp_path, cell, "step5", "deny", "judge-error")


@pytest.mark.parametrize("cell", ["a", "b"])
def test_codex_unreadable_component_step3_allows(tmp_path, cell):
    _unreadable_component_case(tmp_path, cell, "step3", "allow")


def _unreadable_component_case(tmp_path: Path, cell: str, phase: str, expected: str, kind: str = "") -> None:
    root = _root(tmp_path)
    write_state(root, {HOSTILE_KEY: {"phase": phase}})
    if cell == "a":
        directory = root / "Tests"
        directory.mkdir()
        target = "tests/newmod.py"
    else:
        directory = root / "src"
        _file(root, "src/prod.py")
        target = "src/prod.py"
    directory.chmod(0o311)
    try:
        with pytest.raises(PermissionError):
            os.listdir(directory)
        reason = _expect_gate(root, target, expected, kind)
        if kind:
            assert str(directory) in reason, f"missing unreadable component {directory}: {reason}"
    finally:
        directory.chmod(0o755)


@pytest.mark.parametrize("phase", ["active", "unknown", "inactive"])
def test_codex_root_open_failure_refuses_only_when_governed(tmp_path, phase):
    root = _root(tmp_path)
    write_state(root, {HOSTILE_KEY: {"phase": "step5" if phase == "active" else "step3"}})
    if phase == "unknown":
        (root / "docs/.bkit-memory.json").write_text("{bad json", encoding="utf-8")
    root.chmod(0o311)
    try:
        with pytest.raises(PermissionError):
            os.listdir(root)
        reason = _expect_gate(root, str(root / "src/prod.py"), "allow" if phase == "inactive" else "deny",
                              "" if phase == "inactive" else "judge-error")
        if phase != "inactive":
            assert str(root) in reason, f"missing root component {root}: {reason}"
    finally:
        root.chmod(0o755)



@pytest.mark.parametrize("phase", ["active", "inactive"])
def test_codex_mode_000_root_refuses_whatever_the_phase(tmp_path, phase):
    # Operator decision D-2 (2026-09-30): parity with the Claude root-refuse.
    # rglob yields nothing on a root it cannot enter, so the gate must refuse
    # before it looks for state, not infer "inactive" from an empty walk.
    root = _root(tmp_path)
    write_state(root, {HOSTILE_KEY: {"phase": "step5" if phase == "active" else "step3"}})
    original_mode = root.stat().st_mode & 0o7777
    root.chmod(0)
    try:
        with pytest.raises(PermissionError):
            os.open(root, os.O_RDONLY)
        process = subprocess.run(
            [sys.executable, str(CODEX_GATE)], input=json.dumps(_payload(str(root / "src/prod.py"))),
            capture_output=True, text=True, cwd=tmp_path,
            env=hermetic_env(CODEX_PROJECT_DIR=str(root), HMAD_STUB_HOSTILE="all"),
            timeout=60, check=False,
        )
    finally:
        root.chmod(original_mode)
    assert process.returncode == 0, process.stderr
    decision = json.loads(process.stdout)["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny", decision
    reason = decision["permissionDecisionReason"]
    assert "kind=judge-error" in reason and "cannot be entered" in reason, reason

def test_codex_root_open_failure_names_the_on_disk_root(tmp_path):
    root = _root(tmp_path).rename(tmp_path / "Proj")
    assert_case_insensitive(root)
    spelled_root = root.with_name("proj")
    original_mode = root.stat().st_mode & 0o7777
    root.chmod(0o311)
    try:
        with pytest.raises(PermissionError):
            os.open(spelled_root, os.O_RDONLY)
        reason = _expect_gate(spelled_root, str(spelled_root / "src/prod.py"), "deny", "judge-error")
        assert str(root) in reason, f"missing on-disk root component {root}: {reason}"
    finally:
        root.chmod(original_mode)


@pytest.mark.parametrize("variant", ["missing", "loop", "mode000", "mode0311"])
def test_codex_payload_cwd_oserror_uses_payload_cwd_base(tmp_path, variant):
    root = _root(tmp_path)
    _file(root, "src/prod.py")
    cwd = root / "badcwd"
    if variant == "loop":
        cwd.symlink_to("badcwd")
    elif variant.startswith("mode"):
        cwd.mkdir()
        cwd.chmod(0 if variant == "mode000" else 0o311)
    try:
        target = "src/prod.py" if variant in {"missing", "loop"} else "../src/prod.py"
        reason = _expect_gate(root, target, "deny", "no-test-resolved", cwd=str(cwd))
        assert "before src/prod.py" in reason, f"cwd join chose the wrong target: {reason}"
    finally:
        if variant.startswith("mode"):
            cwd.chmod(0o755)


def test_codex_safe_shell_script_keeps_path_resolve_spelling(tmp_path):
    root = _root(tmp_path)
    scripts = CODEX_GATE.parent.parent / "scripts"
    script = scripts / "h_mad_wire_registry.py"
    upper = scripts.parent / "SCRIPTS" / script.name
    assert os.path.exists(upper), "case-insensitive SCRIPTS precondition failed"
    spec = importlib.util.spec_from_file_location("codex_gate_shell_test", CODEX_GATE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module._safe_shell_command(f"python3 {script} challenge", root, str(root)) is True
    assert module._safe_shell_command(f"python3 {upper} challenge", root, str(root)) is False


def test_codex_canonical_cwd_is_rechecked_by_payload_cwd_base(tmp_path, monkeypatch):
    """Pin the canonical-cwd containment call shape required by the design.

    A reachable escape (a canonical cwd outside the root) is not constructible
    without a race on this host, so this test pins the required call shape.
    """
    spec = importlib.util.spec_from_file_location("codex_gate_canonical_cwd_test", CODEX_GATE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    identity = module._load_identity()
    # Match the gate's canonical project root through its identity loader.
    root = Path(identity.canonical_directory(str(_root(tmp_path))))
    target = _file(root, "src/prod.py")
    cwd = root / "src"
    canonical_cwd = identity.canonical_directory(str(cwd))
    calls = []
    original = module._payload_cwd_base

    def recording_payload_cwd_base(project_root, payload_cwd):
        calls.append(payload_cwd)
        return original(project_root, payload_cwd)

    monkeypatch.setattr(module, "_payload_cwd_base", recording_payload_cwd_base)
    resolved = module._relative_target(root, "prod.py", str(cwd))

    assert resolved is not None
    assert Path(resolved.target) == target
    assert calls[0] == str(cwd), f"raw cwd must be checked first: {calls!r}"
    assert canonical_cwd in calls[1:], (
        f"canonical cwd must be rechecked after raw cwd: {calls!r}"
    )


def test_codex_empty_cwd_joins_root(tmp_path):
    root = _root(tmp_path)
    _file(root, "src/prod.py")
    _expect_gate(root, "src/prod.py", "deny", "no-test-resolved", cwd="")


def test_codex_forced_fold_does_not_exempt_dangling_test_name(tmp_path):
    root = _root(tmp_path)
    (root / "sub").mkdir()
    (root / "sub/test_x.PY").symlink_to("nowhere.py")
    _expect_gate(root, "sub/test_x.PY", "deny", "judge-error")


@pytest.fixture(scope="module")
def shell_rows(tmp_path_factory):
    scripts_dir = CODEX_GATE.parent.parent / "scripts"
    return shell_corpus(tmp_path_factory.mktemp("shell-policy"), scripts_dir)


def _shell_verdict(root: Path, cwd: Path, command: str) -> tuple[str, str]:
    verdict, reason, _ = _run(
        root, {"tool_name": "shell_command", "cwd": str(cwd),
               "tool_input": {"command": command}}, path="/usr/bin:/bin",
    )
    return verdict, reason


def test_codex_gate_allows_documented_budget_command_in_step5(tmp_path):
    adapter = CODEX_GATE.parent.parent / "references" / "codex-runtime.md"
    script = CODEX_GATE.parent.parent / "scripts" / "h_mad_context_budget.py"
    documented = 'python3 "<HMAD_SKILL_ROOT>/scripts/h_mad_context_budget.py" --host codex'
    assert documented in adapter.read_text(encoding="utf-8")
    command = documented.replace("<HMAD_SKILL_ROOT>", str(script.parent.parent))
    assert command == f'python3 "{script}" --host codex'
    root = _root(tmp_path)
    verdict, reason, _ = _run(
        root, {"tool_name": "exec_command", "tool_input": {"cmd": command}, "cwd": str(root)},
    )
    assert verdict == "allow", reason


@pytest.mark.parametrize("name,expected", [
    ("contained/sub-cwd/pytest", "allow"),
    ("contained/root-prefix/pytest", "allow"),
    ("venv-symlink-out/sub-cwd/pytest", "deny"),
    ("venv-symlink-out/root-prefix/pytest", "deny"),
    ("contained/doubled/pytest", "deny"),
    ("contained/sub-cwd/c-write", "deny"),
    ("contained/root-prefix/c-write", "deny"),
    ("contained/doubled/c-write", "deny"),
    ("venv-symlink-out/sub-cwd/c-write", "deny"),
    ("venv-symlink-out/root-prefix/c-write", "deny"),
    ("venv-symlink-out/doubled/c-write", "deny"),
], ids=[
    "sub-cwd-contained", "root-cwd-contained", "sub-cwd-escaping", "root-cwd-escaping",
    "doubled-path", "c-sub-cwd-contained", "c-root-cwd-contained", "c-doubled-contained",
    "c-sub-cwd-escaping", "c-root-cwd-escaping", "c-doubled-escaping",
])
def test_shell_venv_token(shell_rows, name, expected):
    row = next(row for row in shell_rows if row.name == name)
    verdict, reason = _shell_verdict(row.root, row.cwd, row.command)
    assert verdict == expected, f"{name}: venv token must be {expected}: {verdict}: {reason}"


def _exec_workdir_verdict(root: Path, session_cwd: Path, workdir: object, command: str) -> tuple[str, str]:
    """codex's real exec_command shape: the SESSION cwd at top level, the shell's own
    directory in tool_input.workdir (observed in codex rollouts, 2026-07..10)."""
    verdict, reason, _ = _run(
        root, {"tool_name": "exec_command", "cwd": str(session_cwd),
               "tool_input": {"cmd": command, "workdir": workdir}}, path="/usr/bin:/bin",
    )
    return verdict, reason


def test_relative_venv_resolves_against_the_commands_workdir_not_the_session_cwd(shell_rows):
    """F2 (HemaSuite citation-fidelity-blind-adjudication, Phase 5): codex ran with
    `--cd <repo root>` and issued `.venv/bin/python -m pytest` with workdir
    `<repo>/hematology-paper-writer`. The gate resolved the token against the session
    cwd, found no `<root>/.venv`, and refused a contained interpreter."""
    row = next(row for row in shell_rows if row.name == "contained/sub-cwd/pytest")
    verdict, reason = _exec_workdir_verdict(row.root, row.root, str(row.cwd), row.command)
    assert verdict == "allow", f"workdir-relative venv must resolve under the workdir: {verdict}: {reason}"


def test_a_relative_workdir_joins_the_session_cwd(shell_rows):
    """`.` names the SESSION cwd (the sub-project here), not the hook process's cwd
    (the root, which has no venv): taken as-is it would resolve under the root."""
    row = next(row for row in shell_rows if row.name == "contained/sub-cwd/pytest")
    assert not (row.root / ".venv").exists(), "fixture drift: the root must have no venv"
    verdict, reason = _exec_workdir_verdict(row.root, row.cwd, ".", row.command)
    assert verdict == "allow", f"relative workdir must join the session cwd: {verdict}: {reason}"


def test_the_inverse_a_workdir_without_a_venv_is_not_rescued_by_the_session_cwd(shell_rows):
    """Session cwd = the sub-project (which HAS a venv), workdir = the root (which has
    none): the command runs `<root>/.venv/bin/python`, which does not exist. A gate that
    admitted the token under EITHER directory would vouch for the session's venv."""
    row = next(row for row in shell_rows if row.name == "contained/sub-cwd/pytest")
    assert (row.cwd / ".venv").is_dir() and not (row.root / ".venv").exists(), "fixture drift"
    control, why = _shell_verdict(row.root, row.cwd, row.command)
    assert control == "allow", f"positive control: the session's own venv with no workdir: {control}: {why}"
    verdict, reason = _exec_workdir_verdict(row.root, row.cwd, str(row.root), row.command)
    assert verdict == "deny", f"a venv only under the session cwd must not be admitted: {verdict}: {reason}"


@pytest.mark.parametrize("workdir", [0, ["/elsewhere"], {"path": "."}, True],
                         ids=["int", "list", "dict", "bool"])
def test_a_present_but_malformed_workdir_fails_closed(shell_rows, workdir):
    """A workdir codex sent but the gate cannot read is not an absent one: falling back
    to the session cwd judges the token where the command may not run."""
    row = next(row for row in shell_rows if row.name == "contained/sub-cwd/pytest")
    verdict, reason = _exec_workdir_verdict(row.root, row.cwd, workdir, row.command)
    assert verdict == "deny", f"malformed workdir {workdir!r} must refuse a relative venv: {verdict}: {reason}"


@pytest.mark.parametrize("shape", ["outside-absolute", "dotdot-escape", "absent"])
def test_a_workdir_outside_the_root_stays_refused(tmp_path, shape):
    """Fail-closed: the workdir is honoured, never trusted. The ROOT carries a contained
    venv here on purpose -- falling an out-of-root workdir back to the root (as a write
    target's cwd does) would vouch for `<root>/.venv` while the command runs elsewhere."""
    root = tmp_path / "root"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True, stdin=subprocess.DEVNULL,
                   timeout=30.0, env=hermetic_env())
    write_state(root, {"feat": {"phase": "step5"}})
    build_venv(root / ".venv", with_pytest=True)
    outside = tmp_path / "elsewhere"
    build_venv(outside / ".venv", with_pytest=True)
    workdir = {"outside-absolute": str(outside), "dotdot-escape": "../elsewhere",
               "absent": str(root / "no-such-dir")}[shape]
    command = ".venv/bin/python -m pytest tests/test_x.py"
    control, why = _exec_workdir_verdict(root, root, str(root), command)
    assert control == "allow", f"positive control: the root's own venv must be admitted: {control}: {why}"
    verdict, reason = _exec_workdir_verdict(root, root, workdir, command)
    assert verdict == "deny", f"{shape}: an out-of-root workdir must not admit a venv: {verdict}: {reason}"


@pytest.mark.parametrize("case,expected", [
    ("contained-venv", "allow"),
    ("usr-bin-python3-control", "allow"),
    ("escaping-venv", "deny"),
    ("script-outside-scripts", "deny"),
], ids=["contained-venv", "usr-bin-python3-control", "escaping-venv", "script-outside-scripts"])
def test_shell_control_allowlist_under_a_venv(shell_rows, case, expected):
    by_name = {row.name: row for row in shell_rows}
    if case == "contained-venv":
        row = by_name["contained/sub-cwd/pytest"]
    elif case == "usr-bin-python3-control":
        row = by_name["control/usr-python-pytest"]
    elif case == "escaping-venv":
        row = by_name["venv-symlink-out/sub-cwd/pytest"]
    else:
        row = by_name["contained/sub-cwd/pytest"]
        script = row.cwd / "h_mad_wire_registry.py"
        script.write_text("# script outside h-mad/scripts\n", encoding="utf-8")
        command = f".venv/bin/python {script} verify"
        verdict, reason = _shell_verdict(row.root, row.cwd, command)
        assert verdict == expected, f"scripts-root rule must deny {command}: {verdict}: {reason}"
        return
    verdict, reason = _shell_verdict(row.root, row.cwd, row.command)
    assert verdict == expected, f"{case}: shell control must be {expected}: {verdict}: {reason}"


def test_venv_token_keys_on_the_lexical_name(tmp_path):
    root = _root(tmp_path)
    sub = root / "hematology-paper-writer"
    python = fake_venv(sub, "exit 0")
    python.unlink()
    python.symlink_to("/bin/cat")
    (sub / "notes.txt").write_text("notes\n", encoding="utf-8")
    verdict, reason = _shell_verdict(root, sub, ".venv/bin/python notes.txt")
    assert verdict == "deny", f"lexical python token must retain python argv rules: {verdict}: {reason}"


def test_shell_policy_corpus_allows_exactly_the_expected_rows(shell_rows):
    actual = set()
    expected = {row.name for row in shell_rows if row.expected_new == "allow"}
    for row in shell_rows:
        verdict, reason = _shell_verdict(row.root, row.cwd, row.command)
        assert verdict in {"allow", "deny"}, f"{row.name}: invalid verdict {verdict}: {reason}"
        if verdict == "allow":
            actual.add(row.name)
    assert actual == expected, f"shell-policy corpus allowed mismatch: missing={expected - actual}, extra={actual - expected}"


def test_venv_token_still_obeys_the_argv_rules(shell_rows):
    row = next(row for row in shell_rows if row.name == "contained/sub-cwd/pytest")
    command = ".venv/bin/python -c pass"
    assert runpy.run_path(str(CODEX_GATE))["SIMPLE_SHELL_COMMAND"].fullmatch(command), \
        "argv-rule oracle must pass the lexical shell subset"
    verdict, reason = _shell_verdict(row.root, row.cwd, command)
    assert verdict == "deny", f"contained venv must still reject python -c: {verdict}: {reason}"
