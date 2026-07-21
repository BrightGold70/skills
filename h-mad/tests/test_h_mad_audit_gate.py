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


def test_cli_marker_feature_is_derived_from_filename(tmp_path: Path) -> None:
    # Project-agnostic: the [H-MAD] marker feature must come from the audit
    # filename, not a hardcoded constant.
    audit_file = tmp_path / "some-other-feature.plan.audit.v1.md"
    audit_file.write_text("## Must-fix\nNone\n## Should-fix\nNone\n", encoding="utf-8")

    result = run_gate(audit_file)

    assert "[H-MAD] some-other-feature gate PASS" in result.stdout
    assert "h-mad-audit-surfaces-reconcile" not in result.stdout


def test_classify_indented_gemini_tui_output_counts_findings() -> None:
    # F1: agy (Gemini) renders every line indented ~2 spaces. A real Must-fix
    # must still be counted, not silently scored PASS by a column-0 header match.
    text = "  ## Must-fix\n  - real issue - why\n  ## Should-fix\n  None\n"

    result = classify(text)

    assert result["verdict"] == "FAIL"
    assert result["must_count"] == 1
    assert result["should_count"] == 0


def test_classify_unicode_and_asterisk_bullets_count() -> None:
    # F1: agy emits `•`, other tools `*`; both are blocking bullets.
    text = "## Must-fix\n• bullet issue\n* asterisk issue\n## Should-fix\nNone\n"

    result = classify(text)

    assert result["must_count"] == 2
    assert result["verdict"] == "FAIL"


def test_classify_indented_bare_none_still_passes() -> None:
    # F1: indentation must not turn a clean (None) audit into a false FAIL.
    text = "  ## Must-fix\n  None\n  ## Should-fix\n  None\n"

    assert classify(text) == {"verdict": "PASS", "must_count": 0, "should_count": 0}


def test_cli_indented_bullet_scored_end_to_end(tmp_path: Path) -> None:
    # F1 end-to-end: an indented `•` Must-fix must FAIL (exit 0), not false-PASS.
    audit_file = tmp_path / "feat.plan.audit.v1.md"
    audit_file.write_text(
        "  ## Summary\n  x\n  ## Must-fix\n  • real problem — why\n  ## Should-fix\n  None\n  ## Nit\n  None\n",
        encoding="utf-8",
    )

    result = run_gate(audit_file)

    assert result.returncode == 0
    assert "GATE: FAIL must=1 should=0" in result.stdout


def test_cli_header_less_input_is_invalid_exit_two(tmp_path: Path) -> None:
    # F2: an empty/garbled extract lacking the mandatory sections must NOT score
    # as a clean PASS. It is an operational error: GATE: INVALID, exit 2.
    audit_file = tmp_path / "feat.plan.audit.v1.md"
    audit_file.write_text("", encoding="utf-8")

    result = run_gate(audit_file)

    assert result.returncode == 2
    assert "GATE: INVALID" in result.stdout
    assert "PASS" not in result.stdout


def test_cli_garbage_without_sections_is_invalid(tmp_path: Path) -> None:
    # F2: non-empty but section-less content (a stray scrape) is still INVALID.
    audit_file = tmp_path / "feat.plan.audit.v1.md"
    audit_file.write_text("some terminal noise\n> prompt\n", encoding="utf-8")

    result = run_gate(audit_file)

    assert result.returncode == 2
    assert "GATE: INVALID" in result.stdout


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
