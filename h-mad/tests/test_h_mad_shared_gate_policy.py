"""FR-6 shared policy ownership, bindings, and self-check signal contract."""
from __future__ import annotations

import ast
import importlib
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from tdd_gate_support import hermetic_env


ROOT = Path(__file__).resolve().parents[2]
IDENTITY_PATH = "h-mad/scripts/h_mad_target_identity.py"
CODEX_GATE = ROOT / "h-mad/hooks/h-mad-codex-tdd-gate.py"
MOVED_FUNCTIONS = (
    "_contained_venv_executable",
    "_cwd_escapes_root",
    "_load_judge",
    "_option_value",
    "_path_within",
    "_payload_cwd_base",
    "_safe_argv",
    "_safe_hmad_script",
    "_safe_shell_command",
    "_trusted_executable",
    "_shell_allowance",
    "_operator_allowed",
    "_is_shell_allowance",
    "_read_regular_text",
    "_state_status",
    "_any_phase5_status",
    "_is_production_python",
)
MOVED_CONSTANTS = (
    "SIMPLE_SHELL_COMMAND",
    "READ_ONLY_COMMANDS",
    "SAFE_DISPATCH_VERBS",
    "SAFE_HMAD_SCRIPT_OPTIONS",
    "TEMP_OUTPUT_OPTIONS",
    "SHELL_ALLOW_FILE",
    "TRUSTED_BIN_DIRS",
    "MALFORMED_WORKDIR",
)


@pytest.fixture(autouse=True)
def hostile_stub_input(monkeypatch):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")


@pytest.fixture(scope="module")
def tracked_python_trees():
    tracked = subprocess.run(
        ["git", "ls-files", "-z", "h-mad"], cwd=ROOT,
        capture_output=True, text=True, check=True, timeout=30,
    )
    return {
        relative: ast.parse((ROOT / relative).read_text(encoding="utf-8"), filename=relative)
        for relative in tracked.stdout.split("\0")
        if relative.endswith(".py")
    }


@pytest.fixture
def gate(monkeypatch):
    # Isolate any sys.path insertion performed by the gate's policy import.
    monkeypatch.syspath_prepend(str(ROOT / "h-mad/scripts"))
    spec = importlib.util.spec_from_file_location("codex_gate_shared_policy_test", CODEX_GATE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("name", MOVED_FUNCTIONS, ids=MOVED_FUNCTIONS)
def test_each_moved_function_has_one_definition_in_the_identity_module(tracked_python_trees, name):
    definitions = [
        relative
        for relative, tree in tracked_python_trees.items()
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    ]
    assert definitions == [IDENTITY_PATH], (
        f"shared policy function {name} must have exactly one definition, in {IDENTITY_PATH}; "
        f"found {definitions}"
    )


@pytest.mark.parametrize("name", MOVED_CONSTANTS, ids=MOVED_CONSTANTS)
def test_each_moved_constant_is_assigned_in_the_identity_module(tracked_python_trees, name):
    assignments = []
    for relative, tree in tracked_python_trees.items():
        for node in tree.body:
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
            else:
                continue
            if any(
                isinstance(target, ast.Name) and target.id == name
                for assigned in targets for target in ast.walk(assigned)
            ):
                assignments.append(relative)
    assert assignments == [IDENTITY_PATH], (
        f"shared policy constant {name} must have exactly one module-level assignment, "
        f"in {IDENTITY_PATH}; found {assignments}"
    )


def test_codex_gate_binds_every_moved_name_to_the_identity_module(gate):
    identity = importlib.import_module("h_mad_target_identity")
    for name in MOVED_FUNCTIONS + MOVED_CONSTANTS:
        assert name in vars(identity), f"identity module must export shared policy name {name}"
        assert getattr(gate, name) is getattr(identity, name), (
            f"Codex gate must bind {name} to the identity module's exact object"
        )


def test_codex_gate_self_check_reports_a_policy_import_failure(tmp_path):
    copied_gate = tmp_path / "hooks" / CODEX_GATE.name
    copied_gate.parent.mkdir()
    shutil.copyfile(CODEX_GATE, copied_gate)
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copyfile(ROOT / "h-mad/scripts/h_mad_tdd_judge.py", scripts / "h_mad_tdd_judge.py")
    assert not (scripts / "h_mad_target_identity.py").exists()
    process = subprocess.run(
        [sys.executable, str(copied_gate), "--self-check"], cwd=tmp_path,
        env=hermetic_env(HMAD_STUB_HOSTILE="all"), capture_output=True,
        text=True, timeout=30, check=False,
    )
    assert process.stderr.strip() == "CODEX-TDD-GATE: FAIL policy-import", (
        f"missing policy must report FAIL policy-import on stderr; got {process.stderr!r}"
    )
    assert process.stdout == "", "policy-import operational failure must not emit a verdict on stdout"
    assert process.returncode == 2, "policy-import operational failure must exit 2"


def test_codex_gate_self_check_shell_policy_fail_is_a_verdict_with_exit_0(gate, monkeypatch, capsys):
    monkeypatch.setattr(gate, "_safe_shell_command", lambda *a, **k: True)
    monkeypatch.setattr(sys, "argv", ["h-mad-codex-tdd-gate.py", "--self-check"])
    rc = gate.main()
    captured = capsys.readouterr()
    assert captured.out.strip() == "CODEX-TDD-GATE: FAIL shell-policy", (
        "shell-policy self-check FAIL verdict must be printed on stdout"
    )
    assert captured.err == "", "shell-policy self-check FAIL verdict must leave stderr empty"
    assert rc == 0, "shell-policy self-check FAIL verdict must exit 0"


def test_codex_gate_self_check_parser_fail_is_a_verdict_with_exit_0(gate, monkeypatch, capsys):
    monkeypatch.setattr(gate, "_patch_header_paths", lambda patch: (["wrong.py"], ""))
    monkeypatch.setattr(sys, "argv", ["h-mad-codex-tdd-gate.py", "--self-check"])
    rc = gate.main()
    captured = capsys.readouterr()
    assert captured.out.strip() == "CODEX-TDD-GATE: FAIL parser", (
        "parser self-check FAIL verdict must be printed on stdout"
    )
    assert captured.err == "", "parser self-check FAIL verdict must leave stderr empty"
    assert rc == 0, "parser self-check FAIL verdict must exit 0"
