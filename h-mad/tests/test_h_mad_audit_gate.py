import ast
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "h-mad" / "scripts"
MODULE_PATH = SCRIPT_DIR / "h_mad_audit_gate.py"

sys.path.insert(0, str(SCRIPT_DIR))

from h_mad_audit_gate import classify  # noqa: E402


def run_gate(audit_file: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(MODULE_PATH), str(audit_file), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_classify_bare_none_sections_pass() -> None:
    text = "## Must-fix\nNone\n## Should-fix\nNone\n"

    assert classify(text) == {
        "verdict": "PASS",
        "must_count": 0,
        "should_count": 0,
    }


def test_classify_stray_dash_none_is_not_blocking() -> None:
    text = "## Must-fix\n- None\n## Should-fix\nNone\n"

    result = classify(text)

    assert result["verdict"] == "PASS"
    assert result["must_count"] == 0
    assert result["should_count"] == 0


def test_classify_real_must_fix_bullet_fails() -> None:
    result = classify("## Must-fix\n- real issue - why\n")

    assert result["verdict"] == "FAIL"
    assert result["must_count"] == 1
    assert result["should_count"] == 0


def test_classify_header_only_sections_do_not_count() -> None:
    text = "## Must-fix\n## Should-fix\n## Notes\n- not blocking\n"

    assert classify(text) == {
        "verdict": "PASS",
        "must_count": 0,
        "should_count": 0,
    }


def test_classify_acknowledged_items_are_excluded_from_counts() -> None:
    text = "\n".join(
        [
            "## Must-fix",
            "- base-layer item waived by operator",
            "- still broken",
            "## Should-fix",
            "- acknowledged should item",
            "- should still block",
            "## Acknowledged-not-fixed",
            "- base-layer item waived by operator",
            "- acknowledged should item",
            "",
        ]
    )

    result = classify(
        text,
        acknowledged={
            "base-layer item waived by operator",
            "acknowledged should item",
        },
    )

    assert result["verdict"] == "FAIL"
    assert result["must_count"] == 1
    assert result["should_count"] == 1


def test_cli_clean_file_prints_pass_marker_and_exits_zero(tmp_path: Path) -> None:
    audit_file = tmp_path / "audit.md"
    audit_file.write_text("## Must-fix\nNone\n## Should-fix\nNone\n", encoding="utf-8")

    result = run_gate(audit_file)

    assert result.returncode == 0
    assert "GATE: PASS must=0 should=0" in result.stdout
    assert "[H-MAD]" in result.stdout
    assert "gate PASS" in result.stdout
    assert result.stderr == ""


def test_cli_dirty_file_prints_fail_marker_and_exits_zero(tmp_path: Path) -> None:
    audit_file = tmp_path / "audit.md"
    audit_file.write_text(
        "## Must-fix\n- fix this\n## Should-fix\n- also fix this\n",
        encoding="utf-8",
    )

    result = run_gate(audit_file)

    assert result.returncode == 0
    assert "GATE: FAIL must=1 should=1" in result.stdout
    assert "[H-MAD]" in result.stdout
    assert "gate FAIL" in result.stdout
    assert result.stderr == ""


def test_cli_missing_file_prints_stderr_and_exits_two(tmp_path: Path) -> None:
    missing_file = tmp_path / "missing.md"

    result = run_gate(missing_file)

    assert result.returncode == 2
    assert result.stderr
    assert result.stdout == ""


def test_cli_must_only_bases_verdict_on_must_count(tmp_path: Path) -> None:
    audit_file = tmp_path / "audit.md"
    audit_file.write_text(
        "## Must-fix\nNone\n## Should-fix\n- should-only issue\n",
        encoding="utf-8",
    )

    result = run_gate(audit_file, "--must-only")

    assert result.returncode == 0
    assert "GATE: PASS must=0 should=1" in result.stdout
    assert "gate PASS" in result.stdout


def test_production_module_uses_only_stdlib_imports() -> None:
    stdlib = getattr(sys, "stdlib_module_names", set())
    if not stdlib:
        pytest.skip("sys.stdlib_module_names is unavailable on this Python")

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.partition(".")[0])

    assert imported_roots <= stdlib
