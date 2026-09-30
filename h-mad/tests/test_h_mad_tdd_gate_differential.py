"""Compare the two TDD gates over the published FR-6 in-root domain."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tdd_gate_support import assert_case_insensitive, decision, hermetic_env, hook_form, write_state


HOOKS = Path(__file__).resolve().parents[1] / "hooks"
CLAUDE = HOOKS / "h-mad-tdd-gate.sh"
CODEX = HOOKS / "h-mad-codex-tdd-gate.py"
HOSTILE_KEY = 'agent "q"\\newline\n[H-MAD:MARKER]%'

# Each entry is (cell, expected decision, expected denial kind).
EXPECTATIONS = (
    ("M-1", "deny", "no-test-resolved"),
    ("M-2", "deny", "no-test-resolved"),
    ("M-3", "deny", "no-test-resolved"),
    ("M-4", "deny", "no-test-resolved"),
    ("M-5", "deny", "no-test-resolved"),
    ("M-6", "deny", "no-test-resolved"),
    ("M-7", "deny", "no-test-resolved"),
    ("M-8", "deny", "no-test-resolved"),
    ("M-9", "deny", "no-test-resolved"),
    ("M-10", "allow", ""),
    ("M-11", "allow", ""),
    ("M-12", "deny", "judge-error"),
    ("M-13/m13-leaf", "deny", "judge-error"),
    ("M-13/m13-intermediate", "deny", "judge-error"),
    ("M-14", "deny", "judge-error"),
    ("M-18/m13-leaf", "allow", ""),
    ("M-18/m13-intermediate", "allow", ""),
    ("M-18/m14", "allow", ""),
    ("notes.md", "allow", ""),
    ("tests/test_x.py", "allow", ""),
    ("sub/test_x.PY", "allow", ""),
)


def _write(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("X = 1\n", encoding="utf-8")


def _fixture(base: Path, cell: str) -> tuple[Path, Path, Path | None]:
    root = base / "R"
    if cell == "M-7":
        root = base / "R/real"
    elif cell == "M-8":
        root = base / "Case/tests/proj"
    root.mkdir(parents=True)
    _write(root / "src/prod.py")

    phase = "step3" if cell.startswith("M-18/") else "step5"
    write_state(root, {HOSTILE_KEY: {"phase": phase, "codex_status": "exhausted"}})
    subprocess.run(["git", "init", "-q", str(root)], check=True,
                   stdin=subprocess.DEVNULL, timeout=30, env=hermetic_env())

    relative = "src/prod.py"
    prefix = None
    if cell in ("M-2", "M-3"):
        relative = "src/prod.PY" if cell == "M-2" else "src/new.PY"
    elif cell in ("M-4", "M-5"):
        (root / "tests").symlink_to("src", target_is_directory=True)
        relative = "tests/prod.py" if cell == "M-4" else "tests/newmod.py"
    elif cell == "M-6":
        (root / "tests").mkdir()
        (root / "src/sub").mkdir()
        (root / "tests/l").symlink_to("../src/sub", target_is_directory=True)
        relative = "tests/l/../prod.py"
    elif cell == "M-7":
        _write(root / "x.py")
        spelled = base / "R/tests/link"
        spelled.parent.mkdir()
        spelled.symlink_to("../real", target_is_directory=True)
        return root, spelled / "x.py", None
    elif cell == "M-8":
        assert_case_insensitive(base)
        return root, base / "case/tests/proj/src/prod.py", None
    elif cell == "M-9":
        assert_case_insensitive(base)
        _write(root / "Tests/prod.py")
        relative = "tests/prod.py"
    elif cell == "M-10":
        _write(root / "fixtures/helper.py")
        relative = "FIXTURES/helper.py"
    elif cell == "M-11":
        _write(root / "tests/helper.py")
        (root / "src/tl").symlink_to("../tests", target_is_directory=True)
        relative = "src/tl/helper.py"
    elif cell == "M-12":
        (root / "docs/d.md").symlink_to("../src/newprod.py")
        relative, prefix = "docs/d.md", root / "docs"
    elif cell.endswith("/m13-leaf"):
        (root / "src/dang.py").symlink_to("nowhere/x.py")
        relative, prefix = "src/dang.py", root / "src"
    elif cell.endswith("/m13-intermediate"):
        (root / "lnk").symlink_to("nowhere", target_is_directory=True)
        relative, prefix = "lnk/x.py", root
    elif cell == "M-14" or cell.endswith("/m14"):
        (root / "src/loopa.py").symlink_to("loopb.py")
        (root / "src/loopb.py").symlink_to("loopa.py")
        relative, prefix = "src/loopa.py", root / "src"
    elif cell in ("notes.md", "tests/test_x.py", "sub/test_x.PY"):
        relative = cell
    return root, root / relative, prefix


def _bin(base: Path) -> Path:
    bin_dir = base / "bin"
    bin_dir.mkdir()
    for name, source in (("python3", sys.executable), ("dirname", "/usr/bin/dirname"),
                         ("basename", "/usr/bin/basename"), ("jq", shutil.which("jq"))):
        if source:
            (bin_dir / name).symlink_to(source)
    return bin_dir


def _run(root: Path, target: Path, bin_dir: Path, gate: str) -> tuple[str, str]:
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(target)}}
    env = {"PATH": f"{bin_dir}:/usr/bin:/bin", "HMAD_STUB_HOSTILE": "all"}
    if gate == "claude":
        env.update(HOME=str(Path.home()), CLAUDE_PROJECT_DIR=str(root))
        command = [str(CLAUDE)]
    else:
        env.update(CODEX_PROJECT_DIR=str(root))
        payload["cwd"] = str(root)
        command = [sys.executable, str(CODEX)]
    result = subprocess.run(command, input=json.dumps(payload), capture_output=True,
                            text=True, cwd=root, env=hermetic_env(**env),
                            timeout=60, check=False)
    if gate == "claude":
        outcome = decision(result, hook_form(CLAUDE))
        assert outcome.decision != "invalid", f"Claude gate protocol invalid: {outcome}"
        return outcome.decision, outcome.kind
    if result.returncode == 0 and result.stdout.strip() in ("", "{}"):
        return "allow", ""
    assert result.returncode == 0, f"Codex gate failed: {result.stderr}"
    output = json.loads(result.stdout)["hookSpecificOutput"]
    assert output["permissionDecision"] == "deny", f"Codex gate protocol invalid: {output}"
    match = re.search(r"kind=([a-z-]+)", output["permissionDecisionReason"])
    return "deny", match.group(1) if match else ""


def _observed(base: Path, cell: str) -> tuple[tuple[str, str], tuple[str, str]]:
    root, target, prefix = _fixture(base, cell)
    if prefix is not None:
        canonical_root = root.resolve(strict=True)
        canonical_prefix = prefix.resolve(strict=True)
        assert canonical_prefix == canonical_root or canonical_root in canonical_prefix.parents, (
            f"{cell}: resolved prefix {canonical_prefix} is outside canonical root {canonical_root}"
        )
    bin_dir = _bin(base)
    return (_run(root, target, bin_dir, "claude"),
            _run(root, target, bin_dir, "codex"))


@pytest.fixture(scope="module")
def observed_cells(tmp_path_factory):
    base = tmp_path_factory.mktemp("tdd-differential")
    return {cell: _observed(base / f"cell-{index}", cell)
            for index, (cell, _, _) in enumerate(EXPECTATIONS)}


@pytest.mark.parametrize("cell,expected_decision,expected_kind", EXPECTATIONS,
                         ids=[row[0] for row in EXPECTATIONS])
def test_differential_cell(observed_cells, cell, expected_decision, expected_kind):
    claude, codex = observed_cells[cell]
    assert claude[0] == codex[0], f"{cell}: gate decisions differ: Claude={claude}, Codex={codex}"
    if claude[0] == codex[0] == "deny":
        assert claude[1] == codex[1], f"{cell}: denial kinds differ: Claude={claude}, Codex={codex}"
    assert claude == (expected_decision, expected_kind), (
        f"{cell}: Claude differs from expectation table: expected {(expected_decision, expected_kind)}, got {claude}"
    )
    assert codex == (expected_decision, expected_kind), (
        f"{cell}: Codex differs from expectation table: expected {(expected_decision, expected_kind)}, got {codex}"
    )


def test_expectation_table_deny_count_is_derived(observed_cells):
    expected_deny_count = sum(decision == "deny" for _, decision, _ in EXPECTATIONS)
    for gate_index, gate in enumerate(("Claude", "Codex")):
        observed_deny_count = sum(outcomes[gate_index][0] == "deny"
                                  for outcomes in observed_cells.values())
        assert observed_deny_count == expected_deny_count, (
            f"{gate}: denial count differs from expectation table: "
            f"expected {expected_deny_count}, got {observed_deny_count}"
        )
