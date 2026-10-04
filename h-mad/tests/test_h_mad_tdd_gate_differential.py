"""Compare the two TDD gates over the published FR-6 in-root domain."""
from __future__ import annotations

import json
import os
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
    # docs/ first-component rule: an executable probe committed under the project's
    # docs/ tree is not production (both gates); a package NAMED docs anywhere else,
    # a top-level docs.py, an ordinary package module, and a docs/ path whose kernel
    # target lies outside docs/ all stay gated.
    ("docs/03-analysis/probes/x/m17_reach_probe.py", "allow", ""),
    ("src/docs/foo.py", "deny", "no-test-resolved"),
    ("pkg/mod.py", "deny", "no-test-resolved"),
    ("docs.py", "deny", "no-test-resolved"),
    ("DOCS-link-file", "deny", "no-test-resolved"),
    ("DOCS-link-dir", "deny", "no-test-resolved"),
)

# Cells under a prefix the name map CAN map (shared/<x>.py -> shared/tests/test_<x>.py).
# The EXPECTATIONS fixture root has no such prefix, so every deny there reads
# no-test-resolved whichever path a gate judged. Here the kernel's target maps to
# a named test that does not exist, so a gate that judged the kernel's target says
# test-missing and names that test, while a gate that judged the spelled tests/...
# path says no-test-resolved or allows. Each entry: (cell, decision, kind, mapped
# test named in the reason or "").
MAPPED = (
    ("MX-6", "deny", "test-missing", "shared/tests/test_prod.py"),
    ("MX-gap1b", "deny", "test-missing", "shared/tests/test_prod.py"),
    ("MX-dot", "deny", "test-missing", "shared/tests/test_prod.py"),
    ("MX-N1", "deny", "test-missing", "shared/tests/test_prod.py"),
    ("MX-N1-exempt", "allow", "", ""),
    ("AC-1.8/absent-leaf", "deny", "test-missing", "shared/tests/test_brandnew.py"),
    ("AC-1.8/absent-parent", "deny", "test-missing", "shared/tests/test_mod.py"),
    ("AC-1.9/hardlink", "deny", "test-missing", "shared/tests/test_prod.py"),
)
SEALED: list[Path] = []


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
    elif cell == "DOCS-link-file":
        (root / "docs/alias.py").symlink_to("../src/prod.py")
        relative = "docs/alias.py"
    elif cell == "DOCS-link-dir":
        (root / "docs/sub").symlink_to("../src", target_is_directory=True)
        relative = "docs/sub/prod.py"
    elif cell in ("notes.md", "tests/test_x.py", "sub/test_x.PY",
                  "docs/03-analysis/probes/x/m17_reach_probe.py", "src/docs/foo.py",
                  "pkg/mod.py", "docs.py"):
        relative = cell
    elif cell.startswith(("MX-", "AC-1.")):
        return root, _mapped_fixture(root, cell), None
    return root, root / relative, prefix


def _mapped_fixture(root: Path, cell: str) -> str:
    shared = root / "shared"
    _write(shared / "prod.py")
    (shared / "tests").mkdir(parents=True)
    (shared / "lib/sub").mkdir(parents=True)
    _write(shared / "lib/prod.py")
    if cell == "MX-6":
        (shared / "tests/l").symlink_to("../lib", target_is_directory=True)
        spelled, kernel = "shared/tests/l/../prod.py", shared / "prod.py"
    elif cell == "MX-gap1b":
        (shared / "tests/l").symlink_to("../lib/sub", target_is_directory=True)
        spelled, kernel = "shared/tests/l/new/../../prod.py", shared / "lib/prod.py"
    elif cell == "MX-dot":
        spelled, kernel = "shared/tests/./../prod.py", shared / "prod.py"
    elif cell.startswith("MX-N1"):
        (shared / "a/b").mkdir(parents=True)
        spelled = ("shared/a/b/../../tests/test_x.py" if cell == "MX-N1-exempt"
                   else "shared/a/b/../../prod.py")
        kernel = shared / ("tests/test_x.py" if cell == "MX-N1-exempt" else "prod.py")
        (shared / "a").chmod(0o311)
        SEALED.append(shared / "a")
    elif cell == "AC-1.8/absent-leaf":
        spelled, kernel = "shared/brandnew.py", None
    elif cell == "AC-1.8/absent-parent":
        spelled, kernel = "shared/newpkg/mod.py", None
    else:  # AC-1.9/hardlink
        os.link(shared / "prod.py", shared / "test_prod.py")
        assert os.stat(shared / "prod.py").st_ino == os.stat(shared / "test_prod.py").st_ino
        spelled, kernel = "shared/test_prod.py", shared / "prod.py"
    target = str(root) + "/" + spelled  # string join: pathlib would drop the '.'
    if kernel is not None and kernel.exists():
        assert os.path.realpath(target) == os.path.realpath(kernel) or (
            os.path.samefile(target, kernel)), f"{cell}: kernel precondition"
    return target


def _bin(base: Path) -> Path:
    bin_dir = base / "bin"
    bin_dir.mkdir()
    for name, source in (("python3", sys.executable), ("dirname", "/usr/bin/dirname"),
                         ("basename", "/usr/bin/basename"), ("jq", shutil.which("jq"))):
        if source:
            (bin_dir / name).symlink_to(source)
    return bin_dir


def _run(root: Path, target: Path | str, bin_dir: Path, gate: str) -> tuple[str, str, str]:
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
        return outcome.decision, outcome.kind, outcome.reason
    if result.returncode == 0 and result.stdout.strip() in ("", "{}"):
        return "allow", "", ""
    assert result.returncode == 0, f"Codex gate failed: {result.stderr}"
    output = json.loads(result.stdout)["hookSpecificOutput"]
    assert output["permissionDecision"] == "deny", f"Codex gate protocol invalid: {output}"
    reason = output["permissionDecisionReason"]
    match = re.search(r"kind=([a-z-]+)", reason)
    return "deny", match.group(1) if match else "", reason


def _observed(base: Path, cell: str) -> tuple[tuple[str, str], tuple[str, str]]:
    root, target, prefix = _fixture(base, cell)
    if prefix is not None:
        canonical_root = root.resolve(strict=True)
        canonical_prefix = prefix.resolve(strict=True)
        assert canonical_prefix == canonical_root or canonical_root in canonical_prefix.parents, (
            f"{cell}: resolved prefix {canonical_prefix} is outside canonical root {canonical_root}"
        )
    bin_dir = _bin(base)
    try:
        return (_run(root, target, bin_dir, "claude"),
                _run(root, target, bin_dir, "codex"))
    finally:
        while SEALED:
            SEALED.pop().chmod(0o755)


@pytest.fixture(scope="module")
def observed_cells(tmp_path_factory):
    base = tmp_path_factory.mktemp("tdd-differential")
    cells = [row[0] for row in EXPECTATIONS] + [row[0] for row in MAPPED]
    return {cell: _observed(base / f"cell-{index}", cell) for index, cell in enumerate(cells)}


@pytest.mark.parametrize("cell,expected_decision,expected_kind", EXPECTATIONS,
                         ids=[row[0] for row in EXPECTATIONS])
def test_differential_cell(observed_cells, cell, expected_decision, expected_kind):
    claude, codex = (outcome[:2] for outcome in observed_cells[cell])
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
        observed_deny_count = sum(observed_cells[cell][gate_index][0] == "deny"
                                  for cell, _, _ in EXPECTATIONS)
        assert observed_deny_count == expected_deny_count, (
            f"{gate}: denial count differs from expectation table: "
            f"expected {expected_deny_count}, got {observed_deny_count}"
        )


@pytest.mark.parametrize("cell,expected_decision,expected_kind,mapped_test", MAPPED,
                         ids=[row[0] for row in MAPPED])
def test_mapped_prefix_cell_names_the_kernels_test(observed_cells, cell, expected_decision,
                                                    expected_kind, mapped_test):
    for gate, (decision_, kind, reason) in zip(("Claude", "Codex"), observed_cells[cell]):
        assert (decision_, kind) == (expected_decision, expected_kind), (
            f"{cell}: {gate} judged a different path than the kernel's: got {(decision_, kind)}: {reason}")
        if mapped_test:
            assert mapped_test in reason, f"{cell}: {gate} reason does not name {mapped_test}: {reason}"
