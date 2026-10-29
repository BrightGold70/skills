"""Task 1 RED: deterministic Phase-4 Test Boundaries checker contract.

Import the new module inside each method: an absent production module must give
24 behavioural test failures, rather than a collection error. Expected values
come from the dispatch/spec and reference documents, never the checker itself.
"""
from __future__ import annotations

import ast
import importlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "h-mad" / "scripts"
SCRIPT = SCRIPTS / "h_mad_test_boundaries_check.py"
AUDIT_GATE = SCRIPTS / "h_mad_audit_gate.py"
sys.path.insert(0, str(SCRIPTS))

COLUMNS = (
    "Public interface", "Acceptance criteria", "Expected result source",
    "Mocked dependencies", "Exclusions",
)
PRE_EXISTING = (
    "claude-context-reduction", "exec-missing-report-recovery",
    "hemasuite-100-percent", "hpw-csa-macos-app", "hpw-csa-unified-ui",
    "hpw-csa-unified-ui-v2", "hpw-protocol-extraction",
    "orca-native-orchestration", "orca-native-transport",
    "tdd-dispatch-verification-discipline",
)
PLACEHOLDERS = (
    "-", "--", "---", "—", "–", "?", "???", "...", "…", "tbd", "todo",
    "fixme", "xxx", "n/a", "na", "none", "null", "nil", "placeholder",
    "pending", "later", "tba", "wip", "same", "ditto", "see above", "see below",
    "tbd explanation", "todo explanation", "fixme explanation", "placeholder explanation",
)
CALIBRATIONS = (
    ("2026-08", "exec-path-hardening", 24),
    ("2026-09", "audit-report-docs-copy", 40),
    ("2026-09", "tdd-gate-fail-opens", 44),
)


def _checker():
    return importlib.import_module("h_mad_test_boundaries_check")


@lru_cache(maxsize=4)
def _hostile_text(kind: str = "all") -> str:
    """Exercise the shipped hostile-input knob, not a tidy stand-in payload."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("HMAD_STUB_")}
    env.update(HMAD_STUB_HOSTILE=kind, HMAD_STUB_CAPTURE=os.devnull)
    proc = subprocess.run(
        ["bash", str(ROOT / "h-mad/tests/stubs/orca"), "worktree", "set", "--json"],
        env=env, capture_output=True, text=True, timeout=5,
    )
    assert proc.returncode == 0, f"hostile {kind} stub failed: {proc.stderr}"
    payload = json.loads(proc.stdout)["result"]["worktree"]["comment"]
    assert payload and payload != "c", f"hostile {kind} payload was not selected"
    return payload


def _agent_cell() -> str:
    return _hostile_text().replace("\n", "<br>").replace("|", r"\|")


def _row(acs: str = "AC-1.1") -> list[str]:
    return [
        f"`service.check` — {_agent_cell()}", acs,
        "Independent acceptance example in docs/contract.md", "none",
        f"Live network requests outside this contract; {_agent_cell()}",
    ]


def _table(rows: list[list[str]] | None = None, columns=COLUMNS) -> str:
    if rows is None:
        rows = [_row()]
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join("---" for _ in columns) + "|"]
    lines.extend("| " + " | ".join(cells) + " |" for cells in rows)
    return "\n".join(lines) + "\n"


def _spec(acs=("AC-1.1",)) -> str:
    return "# Specification\n\n" + "\n".join(f"- {ac}: specified outcome" for ac in acs) + "\n"


def _pair(tmp_path: Path, *, rows=None, spec_text=None, design_text=None, name="demo"):
    tmp_path.mkdir(parents=True, exist_ok=True)
    design = tmp_path / f"{name}.design.md"
    spec = tmp_path / f"{name}.spec.md"
    if design_text is None:
        design_text = f"# Design\n\n{_hostile_text()}\n\n## Test Boundaries\n\n{_table(rows)}"
    design.write_text(design_text, encoding="utf-8")
    spec.write_text(_spec() if spec_text is None else spec_text, encoding="utf-8")
    return design, spec


def _cli(design: Path, *args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(design), *(str(arg) for arg in args)],
        cwd=cwd, capture_output=True, text=True, timeout=5,
    )


def _clean_audit(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Audit\n\n## Must-fix\nNone\n\n## Should-fix\nNone\n\n"
        f"## Notes\n{_hostile_text()}\n", encoding="utf-8",
    )
    return path


def _gate_cli(audit: Path, *args, cwd=None):
    return subprocess.run(
        [sys.executable, str(AUDIT_GATE), str(audit), *(str(arg) for arg in args)],
        cwd=cwd, capture_output=True, text=True, timeout=5,
    )


def _assert_boundary_output_order(proc, primary: str, *, stamped=False):
    lines = proc.stdout.splitlines()
    assert lines[0].startswith("GATE: "), proc.stdout
    assert lines[1].startswith("GATE-CLASS: "), proc.stdout
    index = 2
    if stamped:
        assert lines[index].startswith("GATE-LEGS: "), proc.stdout
        index += 1
    assert lines[index] == primary, (
        "boundary result must immediately follow GATE/GATE-CLASS/GATE-LEGS", proc.stdout,
    )
    assert lines[-1].startswith("[H-MAD] "), proc.stdout


def _assert_cli(proc, token: str, exit_code: int = 0):
    assert proc.returncode == exit_code, (proc.stdout, proc.stderr)
    assert proc.stdout.splitlines()[0] == token, proc.stdout
    assert proc.stderr == "", proc.stderr


def _issues(result):
    return [(i.row, i.col, i.code) for i in result.issues]


def _assert_failure(checker, result, expected):
    assert result.status == "FAIL", result
    assert result.exit_code == 0, result
    assert _issues(result) == expected, result.issues
    output = checker.format_check_result(result)
    reasons = ",".join(sorted({code for _, _, code in expected}))
    assert output.splitlines()[0] == (
        f"TEST-BOUNDARIES: FAIL path={result.path} issues={len(expected)} reasons={reasons}"
    ), output
    assert len(output.splitlines()) == len(expected) + 1, output
    for line, issue in zip(output.splitlines()[1:], result.issues):
        assert line == (
            f"TEST-BOUNDARIES-ISSUE: row={issue.row} col={issue.col} "
            f"code={issue.code} detail={issue.detail}"
        ), output


def _calibrated_pair(tmp_path, case=CALIBRATIONS[0]):
    month, feature, count = case
    source = ROOT / "docs/archive" / month / feature
    tmp_path.mkdir(parents=True, exist_ok=True)
    design = tmp_path / f"{feature}.design.md"
    spec = tmp_path / f"{feature}.spec.md"
    shutil.copyfile(source / design.name, design)
    shutil.copyfile(source / spec.name, spec)
    # Independent census of these three known non-retired corpora. In particular,
    # do not build coverage fixtures from extract_spec_acs(), the method tested.
    text = spec.read_text(encoding="utf-8").split("## Version History", 1)[0]
    acs = set(re.findall(
        r"(?m)^\s*(?:-\s+(?:\[[ xX]\]\s+)?|#{1,6}\s+)(?:\*\*|`)*(AC-\d+\.\d+[a-z]?)\b",
        text,
    ))
    assert len(acs) == count, f"reference census changed for {feature}: {sorted(acs)}"
    acs = sorted(acs, key=lambda ac: tuple(int(n) if n.isdigit() else n for n in re.findall(r"\d+|[a-z]+", ac)))
    rows = [_row(ac) for ac in acs]
    original = design.read_text(encoding="utf-8")
    assert "\n## Test Boundaries\n" not in original, "archive already augmented"
    design.write_text(original + f"\n{_hostile_text()}\n\n## Test Boundaries\n\n" + _table(rows), encoding="utf-8")
    return design, spec, rows


def _assert_calibration(checker, tmp_path, case):
    design, spec, _ = _calibrated_pair(tmp_path, case)
    expected = case[2]
    started = time.monotonic()
    result = checker.check_design(design, spec_path=spec, no_exempt=True)
    elapsed = time.monotonic() - started
    assert result.status == "PASS", result
    assert result.exit_code == 0 and result.rows == expected, result
    assert (result.acs_covered, result.acs_total) == (expected, expected), result
    token = f"TEST-BOUNDARIES: PASS path={design} rows={expected} acs={expected}/{expected}"
    assert checker.format_check_result(result) == token
    assert elapsed < 0.200, f"check_design for {case[1]} took {elapsed:.6f}s (limit 0.200s)"
    started = time.monotonic()
    proc = _cli(design, "--spec", spec, "--no-exempt")
    cli_elapsed = time.monotonic() - started
    _assert_cli(proc, token)
    assert cli_elapsed < 0.200, f"CLI for {case[1]} took {cli_elapsed:.6f}s (limit 0.200s)"


class TestCliAndTableValidation:
    def test_cli_tokens_and_unreadable_vs_missing_spec_disambiguation(self, tmp_path, monkeypatch, capsys):
        checker = _checker()
        design, spec = _pair(tmp_path)
        passed = checker.check_design(design)
        assert (passed.status, passed.exit_code, passed.path, passed.rows,
                passed.acs_covered, passed.acs_total, passed.issues) == (
            "PASS", 0, str(design), 1, 1, 1, (),
        ), passed
        token = f"TEST-BOUNDARIES: PASS path={design} rows=1 acs=1/1"
        _assert_cli(_cli(design, "--spec", spec, "--root", tmp_path, "--no-exempt"), token)
        assert checker.main([str(design), "--spec", str(spec), "--root", str(tmp_path), "--no-exempt"]) == 0
        assert capsys.readouterr().out == token + "\n"

        spec.unlink()
        missing = checker.check_design(design)
        _assert_failure(checker, missing, [("-", "-", "missing_spec")])
        assert missing.issues[0].detail == f"missing paired spec: {spec}"
        _assert_cli(_cli(design), f"TEST-BOUNDARIES: FAIL path={design} issues=1 reasons=missing_spec")
        _assert_cli(_cli(design, "--spec", spec), f"TEST-BOUNDARIES: UNREADABLE path={spec} err=FileNotFoundError", 2)

        absent_design = tmp_path / "absent.design.md"
        _assert_cli(_cli(absent_design), f"TEST-BOUNDARIES: UNREADABLE path={absent_design} err=FileNotFoundError", 2)
        assert not checker.should_activate_design_check(absent_design)
        directory = tmp_path / "directory.design.md"
        directory.mkdir()
        assert checker.should_activate_design_check(directory)
        _assert_cli(_cli(directory), f"TEST-BOUNDARIES: UNREADABLE path={directory} err=IsADirectoryError", 2)
        bad_design = tmp_path / "bytes.design.md"
        bad_design.write_bytes(b"\xff\xfe")
        assert checker.should_activate_design_check(bad_design)
        _assert_cli(_cli(bad_design), f"TEST-BOUNDARIES: UNREADABLE path={bad_design} err=UnicodeDecodeError", 2)

        # Paired operational failures precede all structural early returns.
        structures = (
            "# No boundaries\n", "## Test Boundaries\nNo table\n",
            "## Test Boundaries\n" + _table(columns=("wrong",) * 5),
        )
        for structure in structures:
            design.write_text(structure, encoding="utf-8")
            for explicit in (False, True):
                args = ("--spec", spec) if explicit else ()
                spec.write_bytes(b"\xff\xfe")
                assert checker.should_activate_design_check(design)
                _assert_cli(_cli(design, *args), f"TEST-BOUNDARIES: UNREADABLE path={spec} err=UnicodeDecodeError", 2)
                spec.unlink()
                spec.mkdir()
                assert checker.should_activate_design_check(design)
                _assert_cli(_cli(design, *args), f"TEST-BOUNDARIES: UNREADABLE path={spec} err=IsADirectoryError", 2)
                spec.rmdir()
                if explicit:
                    _assert_cli(_cli(design, *args), f"TEST-BOUNDARIES: UNREADABLE path={spec} err=FileNotFoundError", 2)

        spec.write_text(_spec(), encoding="utf-8")
        original_read = Path.read_text
        for target in (design, spec):
            with monkeypatch.context() as patch:
                def denied(path, *args, **kwargs):
                    if path == target:
                        raise PermissionError("fixture read denied")
                    return original_read(path, *args, **kwargs)
                patch.setattr(Path, "read_text", denied)
                assert checker.should_activate_design_check(design)
                result = checker.check_design(design)
                assert (result.status, result.exit_code, result.path, result.error_type) == (
                    "UNREADABLE", 2, str(target), "PermissionError",
                ), result

        old, _ = _pair(tmp_path, name=PRE_EXISTING[0], design_text="# old design\n")
        _assert_cli(_cli(old), f"TEST-BOUNDARIES: EXEMPT path={old} reason=pre_existing_feature")
        # Exemptions precede even an explicitly unreadable paired spec.
        _assert_cli(_cli(old, "--spec", tmp_path / "absent.spec.md"),
                    f"TEST-BOUNDARIES: EXEMPT path={old} reason=pre_existing_feature")

    def test_infer_project_root_and_two_branch_resolve_spec_path_from_external_cwd(self, tmp_path, monkeypatch):
        checker = _checker()
        assert checker.infer_project_root(Path("/project/docs/02-design/features/demo.design.md")) == Path("/project").resolve()
        assert checker.infer_project_root(Path("/project/docs/archive/2026-08/demo/demo.design.md")) == Path("/project").resolve()
        assert checker.infer_project_root(Path("/project/docs/archive/demo.design.md")) == Path("/project").resolve()
        assert checker.infer_project_root(tmp_path / "demo.design.md") is None
        project = tmp_path / "project"
        design, sibling = _pair(project / "docs/02-design/features")
        plan = project / "docs/01-plan/features/demo.spec.md"
        plan.parent.mkdir(parents=True)
        plan.write_text(_spec(), encoding="utf-8")
        outside = tmp_path / "external-cwd"
        outside.mkdir()
        monkeypatch.chdir(outside)
        assert checker.infer_project_root(design) == project
        assert checker.resolve_spec_path(design) == plan
        _assert_cli(_cli(design, cwd=outside), f"TEST-BOUNDARIES: PASS path={design} rows=1 acs=1/1")
        plan.unlink()
        assert checker.resolve_spec_path(design) == sibling
        sibling.unlink()
        assert checker.resolve_spec_path(design) == plan
        plan.mkdir()
        assert checker.resolve_spec_path(design) == plan, "existing directory must not fall back"
        _assert_cli(_cli(design), f"TEST-BOUNDARIES: UNREADABLE path={plan} err=IsADirectoryError", 2)
        plan.rmdir()
        plan.write_bytes(b"\xff\xfe")
        assert checker.resolve_spec_path(design) == plan
        _assert_cli(_cli(design), f"TEST-BOUNDARIES: UNREADABLE path={plan} err=UnicodeDecodeError", 2)

        override = tmp_path / "override"
        override_spec = override / "docs/01-plan/features/demo.spec.md"
        override_spec.parent.mkdir(parents=True)
        override_spec.write_text(_spec(), encoding="utf-8")
        assert checker.infer_project_root(design, override) == override.resolve()
        assert checker.resolve_spec_path(design, root=override) == override_spec
        _assert_cli(_cli(design, "--root", override), f"TEST-BOUNDARIES: PASS path={design} rows=1 acs=1/1")
        explicit = Path("relative-input.spec.md")
        assert checker.resolve_spec_path(design, explicit, override) == explicit
        nested, _ = _pair(project / "docs/02-design/features/nested")
        plan.write_text(_spec(), encoding="utf-8")
        assert checker.resolve_spec_path(nested, root=project) == plan
        assert checker.should_activate_design_check(nested, root=project)
        for directory in (tmp_path / "synthetic", project / "docs/archive/2026-08/deep/demo"):
            noncanonical, sibling = _pair(directory)
            assert checker.resolve_spec_path(noncanonical, root=project) == sibling
            sibling.unlink()
            assert checker.resolve_spec_path(noncanonical, root=project) == sibling
            assert checker.resolve_spec_path(noncanonical) == sibling, "outside canonical design tree, only sibling is eligible"
        bare, bare_spec = _pair(tmp_path / "bare", design_text="# synthetic design\n", spec_text="# No ACs\n")
        assert not checker.should_activate_design_check(bare)
        bare_spec.write_text(_spec(), encoding="utf-8")
        assert checker.should_activate_design_check(bare)
        design.write_text("# canonical design without boundaries\n", encoding="utf-8")
        assert checker.should_activate_design_check(design)

    def test_missing_section_and_missing_table_and_empty_rows(self, tmp_path):
        checker = _checker()
        for text, code in (
            ("# Design\n## Other\n" + _table(), "missing_section"),
            ("## Test Boundaries\n\nNo table\n", "missing_table"),
            ("## Test Boundaries\n\n" + _table([]), "missing_table"),
            ("## Test Boundaries\nNo table here\n## Next\n" + _table(), "missing_table"),
            ("## Test Boundaries\nNo table here\n# Next\n" + _table(), "missing_table"),
        ):
            design, _ = _pair(tmp_path, design_text=text)
            result = checker.check_design(design)
            _assert_failure(checker, result, [("-", "-", code)])
            if code == "missing_section":
                assert result.issues[0].detail == "missing ## Test Boundaries section"

    def test_invalid_columns_headers_cell_counts_and_zero_ac_tokens(self, tmp_path):
        checker = _checker()
        for columns in (COLUMNS[:-1], COLUMNS + ("Extra",), tuple(reversed(COLUMNS)), ("Interface",) + COLUMNS[1:]):
            design, _ = _pair(tmp_path, design_text="## Test Boundaries\n" + _table(columns=columns))
            _assert_failure(checker, checker.check_design(design), [("header", "-", "invalid_columns")])
        for cells in (_row()[:-1], _row() + ["extra"]):
            design, _ = _pair(tmp_path, rows=[_row(), cells])
            result = checker.check_design(design)
            _assert_failure(checker, result, [("2", "-", "invalid_columns")])
            assert result.issues[0].detail == f"expected 5 columns, got {len(cells)}"
        design, _ = _pair(tmp_path, rows=[_row("covered by prose only")])
        _assert_failure(checker, checker.check_design(design), [
            ("1", "Acceptance criteria", "invalid_columns"), ("-", "Acceptance criteria", "uncovered_ac"),
        ])
        assert checker.check_design(design).issues[0].detail == "Acceptance criteria cell contains zero AC-X.Y tokens"
        # Header comparison permits whitespace and case, and escaped pipes stay in a cell.
        cells = _row()
        cells[0] = r"public.check with escaped \| literal"
        design, _ = _pair(tmp_path, design_text="## Test Boundaries\n" + _table([cells], tuple(c.upper() for c in COLUMNS)))
        assert checker.check_design(design).status == "PASS"
        design, _ = _pair(tmp_path, rows=[_row("No active requirements")], spec_text="# Spec without ACs\n")
        assert checker.check_design(design).status == "PASS"

    def test_fenced_code_blocks_decoy_headings_and_tables_ignored(self, tmp_path):
        checker = _checker()
        for opener, closer, inside in (
            ("```markdown", "```", ""), ("~~~markdown", "~~~", ""),
            ("   ````markdown", "   ````", "```\n~~~\n"),
            ("~~~~", "~~~~", "~~~\n```\n"),
        ):
            decoy = f"{opener}\n{inside}## Test Boundaries\n{_table()}\n{closer}\n"
            assert not checker.has_test_boundaries_heading(decoy), decoy
            design, _ = _pair(tmp_path, design_text=decoy)
            _assert_failure(checker, checker.check_design(design), [("-", "-", "missing_section")])
            design.write_text("## Test Boundaries\n" + f"{opener}\n{_table()}\n{closer}\n", encoding="utf-8")
            _assert_failure(checker, checker.check_design(design), [("-", "-", "missing_table")])
            design.write_text(decoy + "## Test Boundaries\n" + _table(), encoding="utf-8")
            assert checker.has_test_boundaries_heading(design.read_text(encoding="utf-8"))
            assert checker.should_activate_design_check(design)
            assert checker.check_design(design).status == "PASS"
        for kind in ("markdown", "newlines", "markers", "all"):
            design, _ = _pair(tmp_path, design_text=f"{_hostile_text(kind)}\n## Test Boundaries\n" + _table())
            assert checker.check_design(design).status == "PASS", f"hostile {kind} data broke valid table"

    def test_empty_cell_and_placeholder_cell_across_all_five_columns(self, tmp_path):
        checker = _checker()
        assert checker.normalize_cell("  ** `__  MiXeD\t  Case __` **  ") == "mixed case"
        for col_idx, col in enumerate(COLUMNS):
            for value in ("", "   ", " ** `__` ** ", *PLACEHOLDERS):
                if col == "Mocked dependencies" and value == "none":
                    continue
                cells = _row()
                cells[col_idx] = value
                design, _ = _pair(tmp_path, rows=[cells])
                code = "empty_cell" if not value.strip(" `*_\t\n") else "placeholder_cell"
                expected = [("1", col, code)]
                if col_idx == 1:
                    expected.append(("-", "Acceptance criteria", "uncovered_ac"))
                _assert_failure(checker, checker.check_design(design), expected)
                if code == "placeholder_cell":
                    assert checker.is_placeholder_cell(checker.normalize_cell(value), col), (col, value)
        # Basic cell diagnostics are row-major, then unknown/oracle/non-test,
        # with numeric (not lexical) AC order in the final coverage issue.
        design, _ = _pair(tmp_path, rows=[
            ["", "AC-99.1", "implementation", "todo", ""],
            ["verified by: mystery", "AC-1.1", "manual review", "none", "scope excluded"],
        ], spec_text=_spec(("AC-10.1", "AC-2.10", "AC-2.2b", "AC-2.2a", "AC-1.1")))
        result = checker.check_design(design)
        _assert_failure(checker, result, [
            ("1", "Public interface", "empty_cell"),
            ("1", "Mocked dependencies", "placeholder_cell"),
            ("1", "Exclusions", "empty_cell"),
            ("1", "Acceptance criteria", "unknown_ac"),
            ("1", "Expected result source", "tautological_oracle"),
            ("2", "Public interface", "invalid_non_test_row"),
            ("-", "Acceptance criteria", "uncovered_ac"),
        ])
        assert result.issues[-1].detail == "missing active ACs: AC-2.2a, AC-2.2b, AC-2.10, AC-10.1"

    def test_mocked_dependencies_allows_none_and_none_explanations_only_in_col_4(self, tmp_path):
        checker = _checker()
        for value in ("none", "none — explanation", "none (explanation)", "none - local files", "none: pure", "none; pure", "none, pure", "none – pure"):
            assert not checker.is_placeholder_cell(value, "Mocked dependencies"), value
            cells = _row()
            cells[3] = value
            design, _ = _pair(tmp_path, rows=[cells])
            assert checker.check_design(design).status == "PASS", value
        for index in (0, 1, 2, 4):
            col = COLUMNS[index]
            assert checker.is_placeholder_cell("none", col), col
            for value in ("none", "none — explanation", "none (explanation)"):
                assert checker.is_placeholder_cell(value, col) == (value == "none"), (col, value)
                cells = _row()
                cells[index] = value
                design, _ = _pair(tmp_path, rows=[cells])
                result = checker.check_design(design)
                if value == "none":
                    expected = [("1", col, "placeholder_cell")]
                elif index == 1:
                    expected = [("1", col, "invalid_columns")]
                else:
                    assert result.status == "PASS", result
                    continue
                if index == 1:
                    expected.append(("-", "Acceptance criteria", "uncovered_ac"))
                _assert_failure(checker, result, expected)

    def test_tautological_oracle_exact_tokens_and_phrase_regexes_rejected(self, tmp_path):
        checker = _checker()
        values = (
            "implementation", "the implementation", "code", "the code", "source", "the source",
            "source code", "the source code", "function", "the function", "function output",
            "return value", "the return value", "computed", "computed value", "calculated",
            "calculated value", "self", "same function", "sut", "system under test", "unit under test",
            "actual output", "actual", "runtime output", "internal state", "mock", "the mock", "mock return value",
            "computed by the implementation", "calling the same helper", "same algorithm",
            "method under test", "whatever the code returns", "function itself", "call the same method",
        )
        for value in values:
            oracle = f" **`{value.upper()}`**. "
            assert checker.is_tautological_oracle(oracle), value
            cells = _row()
            cells[2] = oracle
            design, _ = _pair(tmp_path, rows=[cells])
            _assert_failure(checker, checker.check_design(design), [("1", "Expected result source", "tautological_oracle")])
        for value in ("Independent worked example in docs/contract.md", "Published source code standard, example 4", "Human calculated example 42"):
            assert not checker.is_tautological_oracle(value), value

    def test_provenance_suffix_in_expected_result_source_does_not_mask_tautology(self, tmp_path):
        checker = _checker()
        for oracle in (
            "implementation (verified by: h-mad/tests/test_x.py)",
            "the code (VERIFIED BY: h-mad/tests/test_x.py)  ",
            "computed by the implementation (verified by: docs/result.md)",
        ):
            assert checker.is_tautological_oracle(oracle), "provenance suffix masked direct-helper tautology"
            cells = _row()
            cells[2] = oracle
            design, _ = _pair(tmp_path, rows=[cells])
            _assert_failure(checker, checker.check_design(design), [("1", "Expected result source", "tautological_oracle")])
        assert not checker.is_tautological_oracle("Independent example in docs/contract.md (verified by: tests/test_x.py)")


class TestSpecAcCoverageAndNonTestRows:
    def test_extract_spec_acs_reference_counts_and_retired_filtering(self):
        checker = _checker()
        live_or_archived_spec = ROOT / "docs/01-plan/features/hmad-test-boundaries.spec.md"
        if not live_or_archived_spec.is_file():
            live_or_archived_spec = next(ROOT.glob("docs/archive/*/hmad-test-boundaries/hmad-test-boundaries.spec.md"))
        references = [
            (live_or_archived_spec, 17, set(), set()),
            (ROOT / "docs/archive/2026-08/exec-path-hardening/exec-path-hardening.spec.md", 24, set(), set()),
            (ROOT / "docs/archive/2026-09/audit-report-docs-copy/audit-report-docs-copy.spec.md", 40, set(), {"AC-2.6a", "AC-2.6b", "AC-3.5a"}),
            (ROOT / "docs/archive/2026-09/tdd-gate-fail-opens/tdd-gate-fail-opens.spec.md", 44, set(), {"AC-3.6"}),
            (ROOT / "docs/archive/2026-10/grok-audit-surface/grok-audit-surface.spec.md", 63, {"AC-3.7"}, set()),
        ]
        for path, count, retired_expected, included in references:
            active, retired = checker.extract_spec_acs(path.read_text(encoding="utf-8"))
            assert len(active) == count, f"active AC census for {path}: {len(active)} != {count}"
            assert retired == retired_expected, f"retired AC census for {path}: {retired}"
            assert included <= active, f"suffix/parenthesized head ACs missing from {path}: {included - active}"
            assert not active & retired, f"retired AC counted active in {path}"
        text = "\n".join((
            "- AC-1.1: active", "- ~~AC-1.2: former~~", "- AC-1.2: duplicate later",
            "- AC-1.3: active then retired", "- AC-1.3: superseded by AC-1.1",
            "- **AC-1.4**: removed", "### AC-1.5: dropped", "- `AC-1.6` (note) [old]: Retired",
        ))
        assert checker.extract_spec_acs(text) == ({"AC-1.1"}, {"AC-1.2", "AC-1.3", "AC-1.4", "AC-1.5", "AC-1.6"})

    def test_mid_line_prose_and_version_history_and_fenced_ac_mentions_ignored(self, tmp_path):
        checker = _checker()
        text = "\n".join((
            "# Spec", "Prose references AC-90.1 but declares nothing.",
            "- A sentence mentioning AC-90.2 is not an AC head.",
            "```markdown", "- AC-90.3: fenced", "## Version History", "```",
            "~~~", "### AC-90.4: fenced", "~~~",
            "- [ ] **AC-1.1**: active", "### `AC-1.2`: active",
            "- [x] AC-1.3a: active", "## Version History", "- AC-90.5: historical",
        ))
        assert checker.extract_spec_acs(text) == ({"AC-1.1", "AC-1.2", "AC-1.3a"}, set())
        design, _ = _pair(tmp_path, rows=[_row("`AC-1.1, AC-1.2, AC-1.3a`")], spec_text=text)
        result = checker.check_design(design)
        assert (result.status, result.rows, result.acs_covered, result.acs_total) == ("PASS", 1, 3, 3), result

    def test_uncovered_ac_and_unknown_ac_and_optional_retired_ac_handling(self, tmp_path):
        checker = _checker()
        text = _spec() + "- ~~AC-1.2: obsolete~~\n- AC-3.7: Retired in v1.10.\n"
        for acs in ("AC-1.1", "AC-1.1, AC-1.2, AC-3.7"):
            design, _ = _pair(tmp_path, rows=[_row(acs)], spec_text=text)
            result = checker.check_design(design)
            assert (result.status, result.acs_covered, result.acs_total) == ("PASS", 1, 1), result
        design, _ = _pair(tmp_path, rows=[_row("AC-9.9, AC-1.2")], spec_text=text)
        result = checker.check_design(design)
        _assert_failure(checker, result, [
            ("1", "Acceptance criteria", "unknown_ac"), ("-", "Acceptance criteria", "uncovered_ac"),
        ])
        assert result.issues[0].detail == "unknown AC not in spec: AC-9.9"
        assert result.issues[1].detail == "missing active ACs: AC-1.1"
        # With no paired spec, tokens cannot be labelled unknown or uncovered.
        (tmp_path / "demo.spec.md").unlink()
        _assert_failure(checker, checker.check_design(design), [("-", "-", "missing_spec")])

    def test_verified_by_rows_accept_valid_kinds_and_proving_artifacts_and_reject_invalid(self, tmp_path):
        checker = _checker()
        artifacts = ("Evidence at docs/review.md", "CHECKER: PASS", "Run `review --check`", "evidence.json")
        for kind in ("audit", "live-run", "operator", "doc-review"):
            for artifact in artifacts:
                cells = _row()
                cells[0] = f"`verified by: {kind} — {_agent_cell()}`"
                cells[2] = artifact
                assert checker.has_proving_artifact(artifact), artifact
                assert checker.validate_non_test_row(1, cells[0], artifact, False) == []
                design, _ = _pair(tmp_path, rows=[cells])
                assert checker.check_design(design).status == "PASS", (kind, artifact)
        for kind in ("review", "auditish", "", "live run"):
            pub = f"verified by: {kind}"
            issues = checker.validate_non_test_row(3, pub, "docs/review.md", False)
            assert [(i.row, i.col, i.code) for i in issues] == [("3", "Public interface", "invalid_non_test_row")]
            cells = _row()
            cells[0] = pub
            design, _ = _pair(tmp_path, rows=[cells])
            _assert_failure(checker, checker.check_design(design), [("1", "Public interface", "invalid_non_test_row")])
        assert checker.validate_non_test_row(1, "public.check", "manual inspection", False) == []
        assert not checker.has_proving_artifact("manual inspection by reviewer")
        for oracle, basic_error in (("", "empty_cell"), ("tbd", "placeholder_cell"), ("implementation", "tautological_oracle")):
            cells = _row()
            cells[0] = "verified by: operator"
            cells[2] = oracle
            assert checker.validate_non_test_row(1, cells[0], oracle, True) == []
            design, _ = _pair(tmp_path, rows=[cells])
            _assert_failure(checker, checker.check_design(design), [("1", "Expected result source", basic_error)])


class TestExemptionsAndAuditGateIntegration:
    def test_pre_existing_and_archived_designs_exempt_unless_no_exempt(self, tmp_path):
        checker = _checker()
        assert set(checker.PRE_EXISTING_FEATURES) == set(PRE_EXISTING)
        designs = [(ROOT / "docs/02-design/features" / f"{name}.design.md", "pre_existing_feature") for name in PRE_EXISTING]
        archived = tmp_path / "docs/archive/2026-08/deep/demo/demo.design.md"
        archived.parent.mkdir(parents=True)
        archived.write_text(f"# Archived design\n{_hostile_text()}\n", encoding="utf-8")
        designs.append((archived, "archived"))
        for design, reason in designs:
            result = checker.check_design(design)
            assert (result.status, result.exit_code, result.exempt_reason) == ("EXEMPT", 0, reason), result
            _assert_cli(_cli(design), f"TEST-BOUNDARIES: EXEMPT path={design} reason={reason}")
            _assert_failure(checker, checker.check_design(design, no_exempt=True), [("-", "-", "missing_section")])
            _assert_cli(_cli(design, "--no-exempt"), f"TEST-BOUNDARIES: FAIL path={design} issues=1 reasons=missing_section")
        # Once augmented, both exemption classes must undergo validation.
        for directory, name in ((archived.parent, "demo"), (tmp_path / "augmented", PRE_EXISTING[0])):
            cells = _row()
            cells[4] = "tbd"
            design, _ = _pair(directory, name=name, rows=[cells])
            _assert_failure(checker, checker.check_design(design), [("1", "Exclusions", "placeholder_cell")])

    def test_isolated_spec_from_file_location_activation_parity(self, tmp_path, monkeypatch):
        direct = _checker()
        hostile = _hostile_text()
        cases = []
        for name, text, spec_text, expected in (
            ("fenced", "```markdown\n## Test Boundaries\n```\n", None, False),
            ("tilde-fenced", "~~~markdown\n## Test Boundaries\n~~~\n", None, False),
            ("heading", "## Test Boundaries\n", None, True),
            ("lettered", "# Design\n", _spec(("AC-4.2a",)), True),
            ("retired", "# Design\n", "- ~~AC-4.2a: retired~~\n", False),
        ):
            design = tmp_path / name / "demo.design.md"
            design.parent.mkdir()
            design.write_text(f"{text}\n{hostile}\n", encoding="utf-8")
            if spec_text is not None:
                design.with_name("demo.spec.md").write_text(spec_text, encoding="utf-8")
            cases.append((design, None, expected, design.with_name("demo.spec.md")))

        # Both spec-resolution branches, with canonical plan taking precedence.
        for branch in ("plan", "sibling"):
            project = tmp_path / branch
            design, sibling = _pair(
                project / "docs/02-design/features",
                design_text=f"# Design\n{hostile}\n",
                spec_text="- ~~AC-4.2a: retired~~\n" if branch == "plan" else _spec(("AC-4.2a",)),
            )
            expected_spec = sibling
            if branch == "plan":
                expected_spec = project / "docs/01-plan/features/demo.spec.md"
                expected_spec.parent.mkdir(parents=True)
                expected_spec.write_text(_spec(("AC-4.2a",)), encoding="utf-8")
            cases.append((design, project, True, expected_spec))

        for design, root, expected, expected_spec in cases:
            assert direct.should_activate_design_check(design, root) is expected
            assert direct.resolve_spec_path(design, root=root) == expected_spec

        # Remove both the search path and cached ordinary import: this models the
        # tree_lock_plugin's file-path load, not the pytest process's setup.
        monkeypatch.setattr(sys, "path", [
            entry for entry in sys.path if Path(entry).resolve() != SCRIPTS.resolve()
        ])
        monkeypatch.delitem(sys.modules, "h_mad_test_boundaries_check", raising=False)
        assert all(Path(entry).resolve() != SCRIPTS.resolve() for entry in sys.path)
        spec = importlib.util.spec_from_file_location("_isolated_audit_gate", AUDIT_GATE)
        assert spec is not None and spec.loader is not None
        gate = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, spec.name, gate)
        spec.loader.exec_module(gate)
        loader = getattr(gate, "_load_test_boundaries_checker", None)
        assert callable(loader), "audit gate must load its checker by file path without scripts on sys.path"
        monkeypatch.setitem(sys.modules, "_h_mad_test_boundaries_check", direct)
        isolated, checker_path = loader()
        assert checker_path.resolve() == SCRIPT.resolve()
        assert isolated is not direct, "parity must exercise an independently loaded checker"
        for design, root, expected, expected_spec in cases:
            assert isolated.should_activate_design_check(design, root) is expected, design
            assert isolated.should_activate_design_check(design, root) == direct.should_activate_design_check(design, root)
            assert isolated.resolve_spec_path(design, root=root) == expected_spec

    def test_external_project_root_activation_fails_missing_section(self, tmp_path):
        project = tmp_path / "external_project"
        design = project / "docs/02-design/features/demo.design.md"
        design.parent.mkdir(parents=True)
        design.write_text(f"# Design\n{_hostile_text()}\n", encoding="utf-8")
        assert not design.with_name("demo.spec.md").exists()
        assert _checker().infer_project_root(design) == project
        assert _checker().should_activate_design_check(design)
        audit = _clean_audit(project / "docs/03-analysis/demo.design.audit.v1.md")
        proc = _gate_cli(audit, "--gated", design, cwd=ROOT)
        assert proc.returncode == 0 and proc.stderr == "", (proc.stdout, proc.stderr)
        assert "GATE: FAIL must=0 should=0" in proc.stdout, proc.stdout
        primary = f"TEST-BOUNDARIES: FAIL path={design} issues=1 reasons=missing_section"
        _assert_boundary_output_order(proc, primary)
        assert not Path(str(audit) + ".gated.json").exists()

    def test_unreadable_paired_spec_fails_gate_closed(self, tmp_path):
        design, spec = _pair(
            tmp_path / "external_project", design_text=f"# Design\n{_hostile_text()}\n",
        )
        spec.write_bytes(b"\xff\xfe")
        assert _checker().should_activate_design_check(design) is True
        audit = _clean_audit(design.parent / "demo.design.audit.v1.md")
        proc = _gate_cli(audit, "--gated", design)
        assert proc.returncode == 0 and proc.stderr == "", (proc.stdout, proc.stderr)
        assert "GATE: FAIL must=0 should=0" in proc.stdout, proc.stdout
        _assert_boundary_output_order(
            proc, f"TEST-BOUNDARIES: UNREADABLE path={spec} err=UnicodeDecodeError",
        )
        assert not Path(str(audit) + ".gated.json").exists()

    def test_directory_valued_design_candidate_fails_gate_closed(self, tmp_path):
        directory = tmp_path / "external_project/docs/02-design/features"
        directory.mkdir(parents=True)
        design = directory / "demo.design.md"
        design.mkdir()
        assert _checker().should_activate_design_check(design) is True
        audit = _clean_audit(directory / "demo.design.audit.v1.p1.md")
        proc = _gate_cli(audit)
        assert proc.returncode == 0 and proc.stderr == "", (proc.stdout, proc.stderr)
        assert "GATE: FAIL must=0 should=0" in proc.stdout, proc.stdout
        _assert_boundary_output_order(
            proc, f"TEST-BOUNDARIES: UNREADABLE path={design} err=IsADirectoryError",
        )
        assert not Path(str(audit) + ".gated.json").exists()

    def test_gate_fails_and_suppresses_stamp_when_design_boundaries_fail(self, tmp_path):
        # The existing CLI is the caller. No reference to the new helper is
        # needed: removing only its eventual call must restore the wrong PASS.
        for mode in ("repeatable-gated", "positional", "missing-gated-fallback"):
            directory = tmp_path / mode
            cells = _row()
            cells[4] = "tbd"
            design, _ = _pair(directory, rows=[cells])
            audit = _clean_audit(directory / "demo.design.audit.v1.md")
            stamp = Path(str(audit) + ".gated.json")
            args = []
            if mode == "repeatable-gated":
                passing, _ = _pair(directory, name="passing")
                # Passing first must not mask failure of a later candidate;
                # duplicate design paths must not duplicate checker output.
                args = ["--gated", passing, "--gated", design, "--gated", design]
            elif mode == "missing-gated-fallback":
                args = ["--gated", directory / "missing.design.md"]
            proc = _gate_cli(audit, *args)
            assert proc.returncode == 0 and proc.stderr == "", (mode, proc.stdout, proc.stderr)
            assert "GATE: FAIL must=0 should=0" in proc.stdout, (
                "main must propagate the failing design checker verdict before stamping", mode, proc.stdout,
            )
            assert not stamp.exists(), "failing boundaries must suppress the audit stamp"
            boundary_lines = [line for line in proc.stdout.splitlines() if line.startswith("TEST-BOUNDARIES:")]
            failed = f"TEST-BOUNDARIES: FAIL path={design} issues=1 reasons=placeholder_cell"
            if mode == "repeatable-gated":
                passed = f"TEST-BOUNDARIES: PASS path={passing} rows=1 acs=1/1"
                assert boundary_lines == [passed, failed], proc.stdout
                _assert_boundary_output_order(proc, passed)
            else:
                assert boundary_lines == [failed], proc.stdout
                _assert_boundary_output_order(proc, failed)

    def test_gate_passes_and_writes_stamp_when_activated_design_passes_or_is_exempt(self, tmp_path):
        project = tmp_path / "external_project"
        passing, _ = _pair(project / "docs/02-design/features")
        archived = project / "docs/archive/2026-10/demo/demo.design.md"
        archived.parent.mkdir(parents=True)
        archived.write_text(f"# Archived design\n{_hostile_text()}\n", encoding="utf-8")
        for name, design, expected in (
            ("passing", passing, f"TEST-BOUNDARIES: PASS path={passing} rows=1 acs=1/1"),
            ("exempt", archived, f"TEST-BOUNDARIES: EXEMPT path={archived} reason=archived"),
        ):
            assert _checker().should_activate_design_check(design)
            audit = _clean_audit(project / f"docs/03-analysis/{name}.design.audit.v1.md")
            proc = _gate_cli(audit, "--gated", design, "--legs", "codex", "--suite-result", "PASS")
            assert proc.returncode == 0 and proc.stderr == "", (proc.stdout, proc.stderr)
            assert "GATE: PASS must=0 should=0 gated=1" in proc.stdout, proc.stdout
            assert expected in proc.stdout, "activated PASS/EXEMPT must be emitted by the caller"
            # SUITE precedes the gate result when supplied by the cycle driver.
            assert proc.stdout.splitlines()[0] == "SUITE: PASS source=cycle"
            gate_output = subprocess.CompletedProcess(
                proc.args, proc.returncode, "\n".join(proc.stdout.splitlines()[1:]), proc.stderr,
            )
            _assert_boundary_output_order(gate_output, expected, stamped=True)
            stamp = Path(str(audit) + ".gated.json")
            assert stamp.is_file()
            recorded = json.loads(stamp.read_text(encoding="utf-8"))
            assert recorded["verdict"] == "PASS"
            assert recorded["suite"] == "PASS" and recorded["legs"] == ["codex"]
            assert len(recorded["files"]) == 1
            verified = _gate_cli(audit, "--verify-stamp")
            assert verified.returncode == 0 and verified.stderr == "", (verified.stdout, verified.stderr)
            assert verified.stdout.splitlines()[0] == "GATESTAMP: CURRENT checked=1 changed=0"

    def test_gate_does_not_activate_on_bare_synthetic_design_in_tmp_path(self, tmp_path):
        design = tmp_path / "demo.design.md"
        design.write_text(f"# Synthetic design\n{_hostile_text()}\n", encoding="utf-8")
        assert not design.with_name("demo.spec.md").exists()
        assert _checker().infer_project_root(design) is None
        assert not _checker().should_activate_design_check(design)
        audit = _clean_audit(tmp_path / "demo.design.audit.v1.md")
        proc = _gate_cli(audit, "--gated", design)
        assert proc.returncode == 0 and proc.stderr == "", (proc.stdout, proc.stderr)
        assert "GATE: PASS must=0 should=0 gated=1" in proc.stdout, proc.stdout
        assert "TEST-BOUNDARIES:" not in proc.stdout, proc.stdout
        stamp = Path(str(audit) + ".gated.json")
        assert stamp.is_file()
        assert json.loads(stamp.read_text(encoding="utf-8"))["verdict"] == "PASS"


class TestDesignAuthorAndSelfBootstrap:
    def test_design_author_requires_test_boundaries_and_pre_done_check(self) -> None:
        author = (ROOT / "h-mad/agents/design-author.md").read_text(encoding="utf-8")
        rule_match = re.search(
            r"^7a\.\s+(?P<body>.*?)(?=^\d+[a-z]?\.\s|\Z)",
            author,
            flags=re.MULTILINE | re.DOTALL,
        )
        assert rule_match is not None, (
            "design-author.md must require ## Test Boundaries and its pre-DONE checker in Rule 7a. (AC-1.3)"
        )
        rule = rule_match.group("body")
        assert "## Test Boundaries" in rule
        assert "every active spec `AC-X.Y[a-z]`" in rule
        assert "docs/01-plan/features/<feature>.spec.md" in rule
        assert (
            "| Public interface | Acceptance criteria | Expected result source | Mocked dependencies | Exclusions |"
        ) in rule
        assert (
            "python3 <skill_dir>/scripts/h_mad_test_boundaries_check.py "
            "docs/02-design/features/<feature>.design.md "
            "--spec docs/01-plan/features/<feature>.spec.md"
        ) in rule, "Rule 7a must give the exact host-independent boundary self-check command"
        assert (
            "(where <skill_dir> is the active H-MAD skill directory for the current host, e.g. h-mad in this checkout"
        ) in rule
        assert "Before emitting `DESIGN-AUTHOR: DONE`, run:" in rule
        assert "Read the `TEST-BOUNDARIES:` token, never `$?`." in rule
        assert "TEST-BOUNDARIES: FAIL" in rule
        assert "TEST-BOUNDARIES-ISSUE:" in rule
        assert "UNREADABLE" in rule
        assert "until the checker prints `TEST-BOUNDARIES: PASS`" in rule
        output_match = re.search(
            r"^## Output\s*\n```\s*\nDESIGN-AUTHOR: DONE[^\n]*\n```\s*\n(?P<body>.*?)(?=^## |\Z)",
            author,
            flags=re.MULTILINE | re.DOTALL,
        )
        assert output_match is not None, "design-author.md must retain its ## Output contract"
        output = output_match.group("body")
        assert "TEST-BOUNDARIES: PASS" in output, (
            "DESIGN-AUTHOR: DONE output must report TEST-BOUNDARIES: PASS verification alongside premise commands"
        )
        assert "command you used" in output

    def test_hmad_test_boundaries_design_passes_self_check(self):
        checker = _checker()
        design = ROOT / "docs/02-design/features/hmad-test-boundaries.design.md"
        spec = ROOT / "docs/01-plan/features/hmad-test-boundaries.spec.md"
        if not design.is_file():
            design = next(ROOT.glob("docs/archive/*/hmad-test-boundaries/hmad-test-boundaries.design.md"))
        if not spec.is_file():
            spec = next(ROOT.glob("docs/archive/*/hmad-test-boundaries/hmad-test-boundaries.spec.md"))
        result = checker.check_design(design, spec_path=spec, no_exempt=True)
        assert (result.status, result.exit_code, result.acs_covered, result.acs_total) == ("PASS", 0, 17, 17), result
        assert result.rows > 0 and result.issues == (), result
        _assert_cli(_cli(design, "--spec", spec, "--no-exempt"),
                    f"TEST-BOUNDARIES: PASS path={design} rows={result.rows} acs=17/17")


class TestAuditPromptAndDocAuditorContract:
    @staticmethod
    def _assert_rubric(text: str, source: str) -> None:
        # Check the isolated instruction, so an unrelated rule cannot supply
        # the severity, exception, or semantic checks this rubric promises.
        plain = " ".join(text.replace("`", "").replace("**", "").split())
        required = (
            ("blocking severity", "## Must-fix"),
            ("build classification", "class: build"),
            ("non-exempt missing-section finding", "## Test Boundaries is missing on a non-exempt design"),
            ("active spec AC coverage", "any active spec AC-X.Y[a-z] uncovered"),
            ("placeholder rejection", "placeholder cells"),
            ("expected-result oracle review", "Expected result source"),
            ("semantic oracle independence", "semantically tautological"),
            ("independent oracle requirement", "rather than an independent"),
            ("fixture oracle", "fixture"),
            ("protocol oracle", "protocol"),
            ("analytical oracle", "analytical invariant"),
            ("private-helper rejection", "private/internal helper instead of the public interface"),
            ("unit-under-test mocking rejection", "mocks the unit under test"),
            ("internal-collaborator mocking review", "internal collaborator that should"),
            ("real collaborator execution", "for real"),
            ("non-test verification kinds", "verified by: audit | live-run | operator | doc-review"),
            ("non-test verification justification", "claims non-test verification for behavior that can and should be unit/integration tested"),
            ("proving-artifact review", "names a proving artifact"),
        )
        for property_name, phrase in required:
            assert phrase in plain, f"{source}: Test Boundaries rubric must require {property_name} (AC-5.1)"
        assert "implementation" in plain and "helper" in plain, (
            f"{source}: oracle tautologies must challenge implementation/helper-derived expectations"
        )
        assert re.search(r"does not(?: actually)? verify the listed AC", plain), (
            f"{source}: proving artifact must actually verify the listed AC (AC-5.1)"
        )

    def test_audit_prompt_and_doc_auditor_contain_test_boundaries_rubric(self):
        template = (ROOT / "h-mad/audit-prompt.template.md").read_text(encoding="utf-8")
        axis_a = template.split("Axis A — Generic adversarial:", 1)[1].split("Axis B —", 1)[0]
        blocks = [
            match for match in re.finditer(
                r"^\{\{ONLY:design\}\}\s*\n(?P<body>.*?)^\{\{END-ONLY\}\}",
                axis_a, flags=re.MULTILINE | re.DOTALL,
            )
            if "## Test Boundaries" in match.group("body")
        ]
        assert len(blocks) == 1, (
            "audit-prompt.template.md: Axis A must contain one design-only ## Test Boundaries rubric (AC-5.1)"
        )
        block = blocks[0]
        assert axis_a[:block.start()].rstrip().endswith("plan-stated behavior."), (
            "Test Boundaries rubric must immediately follow the Cross-doc bullet and its continuations"
        )
        assert not axis_a[block.end():].strip(), "Test Boundaries rubric must precede Axis B"
        assert "5-column table" in block.group("body"), "rubric must identify the 5-column table"
        self._assert_rubric(block.group("body"), "audit-prompt.template.md design block")

        auditor = (ROOT / "h-mad/agents/doc-auditor.md").read_text(encoding="utf-8")
        rules = auditor.split("## Rules — each closes a measured failure class", 1)[1].split("\n## ", 1)[0]
        rule = re.search(r"^7c\.\s+(?P<body>.*?)(?=^\d+[a-z]?\.\s|\Z)",
                         rules, flags=re.MULTILINE | re.DOTALL)
        assert rule is not None, "doc-auditor.md must require the Test Boundaries rubric in Rule 7c (AC-5.1)"
        assert "7b. **Classify every finding" in rules[:rule.start()]
        assert rules[rule.end():].startswith("8. **You never fix anything.")
        assert "Phase 4 design audits" in rule.group("body"), "Rule 7c must apply to Phase 4 design audits"
        self._assert_rubric(rule.group("body"), "doc-auditor.md Rule 7c")

    def test_assemble_audit_resolves_test_boundaries_for_design_only(self):
        assembler = importlib.import_module("h_mad_assemble_audit")
        template = (ROOT / "h-mad/audit-prompt.template.md").read_text(encoding="utf-8")
        hostile = _hostile_text("all")
        template = template.replace("<INLINE_TARGET_DOC>", hostile)
        resolved = {}
        for phase in ("design", "plan", "impl-plan"):
            text = assembler.resolve(assembler.strip_orchestrator_note(template), phase)
            resolved[phase] = text
            assert hostile in text, f"{phase}: resolver must preserve hostile authored document content"
            leaks = [reason for reason in assembler.preflight(text, {})
                     if reason.startswith("unresolved_conditional:")]
            assert leaks == [], f"{phase}: Test Boundaries resolution leaked conditionals: {leaks}"
            assert "{{ONLY:" not in text and "{{END-ONLY}}" not in text, (
                f"{phase}: resolver must consume applicability markers"
            )
        assert "## Test Boundaries" in resolved["design"], (
            "resolve(design) must include the ## Test Boundaries audit rubric (AC-5.1)"
        )
        axis_a = resolved["design"].split("Axis A — Generic adversarial:", 1)[1].split("Axis B —", 1)[0]
        self._assert_rubric(axis_a, "resolve(design)")
        for phase in ("plan", "impl-plan"):
            for design_only_phrase in ("## Test Boundaries", "Expected result source", "verified by:"):
                assert design_only_phrase not in resolved[phase], (
                    f"resolve({phase}) must strip the Test Boundaries rubric: {design_only_phrase}"
                )


class TestArchivedCalibrationAndPerformance:
    def test_calibrated_exec_path_hardening_passes_under_200ms(self, tmp_path):
        checker = _checker()
        _assert_calibration(checker, tmp_path, CALIBRATIONS[0])

    def test_calibrated_audit_report_docs_copy_passes_under_200ms(self, tmp_path):
        checker = _checker()
        _assert_calibration(checker, tmp_path, CALIBRATIONS[1])

    def test_calibrated_tdd_gate_fail_opens_passes_under_200ms(self, tmp_path):
        checker = _checker()
        _assert_calibration(checker, tmp_path, CALIBRATIONS[2])

    def test_archive_directory_remains_unmodified_and_stdlib_only(self):
        checker = _checker()
        assert callable(checker.check_design), "archive calibration requires the real checker"
        proc = subprocess.run(["git", "status", "--porcelain", "--", "docs/archive/"],
                              cwd=ROOT, capture_output=True, text=True, timeout=5)
        assert proc.returncode == 0, proc.stderr
        assert proc.stdout == "", f"archive corpus was modified: {proc.stdout}"
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert node.level == 0, f"checker imports a local dependency: {ast.dump(node)}"
                imported.add((node.module or "").split(".")[0])
        assert imported <= sys.stdlib_module_names, f"non-stdlib checker imports: {imported - sys.stdlib_module_names}"


class TestSeededBrokenFixtures:
    def test_mutation_spec_schema_and_check_anchors_pass(self):
        spec_dir = ROOT / "h-mad/tests/mutation-specs"
        spec_path = spec_dir / "test_boundaries_gate.json"
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        assert spec["root"] == "../..", "AC-6.3: mutation paths must resolve from h-mad"
        for key in ("command", "target_command", "mutations"):
            assert isinstance(spec[key], list) and spec[key], f"AC-6.3: {key} must be a non-empty list"
        assert "-k" in spec["command"], "AC-6.3: mutation probes must exclude the anchor self-check"
        exclusion = "not test_mutation_spec_schema_and_check_anchors_pass"
        assert exclusion in spec["command"], "AC-6.3: mutation probes must not recursively check active anchors"
        assert spec["command"][spec["command"].index("-k") + 1] == exclusion
        assert len(spec["mutations"]) == 8, "AC-6.3: require two connection mutations and six checker mutations"
        targets = [mutation["file"] for mutation in spec["mutations"]]
        assert targets.count("scripts/h_mad_audit_gate.py") == 2
        assert targets.count("scripts/h_mad_test_boundaries_check.py") == 6

        proc = subprocess.run(
            ["python3", str(SCRIPTS / "h_mad_mutation_harness.py"), "--check-anchors",
             str(spec_path), str(spec_dir / "audit_suite_gate.json"),
             str(spec_dir / "audit_gate_stamp.json")],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "ANCHORS: ANCHORS_OK" in proc.stdout, (
            "AC-6.3: all three mutation specs must pass anchor validation", proc.stdout, proc.stderr,
        )

    def test_seeded_broken_missing_section_and_missing_table_rejected(self, tmp_path):
        checker = _checker()
        design, spec, _ = _calibrated_pair(tmp_path)
        assert checker.check_design(design, spec_path=spec, no_exempt=True).status == "PASS"
        original = design.read_text(encoding="utf-8")
        before, _ = original.split("\n## Test Boundaries\n", 1)
        for text, code in ((before, "missing_section"), (before + "\n## Test Boundaries\nTable removed\n", "missing_table")):
            design.write_text(text, encoding="utf-8")
            _assert_failure(checker, checker.check_design(design, no_exempt=True), [("-", "-", code)])
            _assert_cli(_cli(design, "--no-exempt"), f"TEST-BOUNDARIES: FAIL path={design} issues=1 reasons={code}")

    def test_seeded_broken_placeholder_cell_rejected(self, tmp_path):
        checker = _checker()
        design, spec, rows = _calibrated_pair(tmp_path)
        assert checker.check_design(design, spec_path=spec, no_exempt=True).status == "PASS"
        before = design.read_text(encoding="utf-8").split("\n## Test Boundaries\n", 1)[0]
        for value in ("tbd", "n/a", "none"):
            broken = [list(row) for row in rows]
            broken[0][4] = value
            design.write_text(before + "\n## Test Boundaries\n" + _table(broken), encoding="utf-8")
            _assert_failure(checker, checker.check_design(design, no_exempt=True), [("1", "Exclusions", "placeholder_cell")])
            _assert_cli(_cli(design, "--no-exempt"), f"TEST-BOUNDARIES: FAIL path={design} issues=1 reasons=placeholder_cell")

    def test_seeded_broken_uncovered_ac_rejected(self, tmp_path):
        checker = _checker()
        design, spec, rows = _calibrated_pair(tmp_path)
        assert checker.check_design(design, spec_path=spec, no_exempt=True).status == "PASS"
        before = design.read_text(encoding="utf-8").split("\n## Test Boundaries\n", 1)[0]
        removed = rows[-1][1]
        design.write_text(before + "\n## Test Boundaries\n" + _table(rows[:-1]), encoding="utf-8")
        result = checker.check_design(design, no_exempt=True)
        _assert_failure(checker, result, [("-", "Acceptance criteria", "uncovered_ac")])
        assert result.issues[0].detail == f"missing active ACs: {removed}"
        _assert_cli(_cli(design, "--no-exempt"), f"TEST-BOUNDARIES: FAIL path={design} issues=1 reasons=uncovered_ac")

    def test_seeded_broken_implementation_oracle_rejected(self, tmp_path):
        checker = _checker()
        design, spec, rows = _calibrated_pair(tmp_path)
        assert checker.check_design(design, spec_path=spec, no_exempt=True).status == "PASS"
        before = design.read_text(encoding="utf-8").split("\n## Test Boundaries\n", 1)[0]
        rows[0][2] = "implementation"
        design.write_text(before + "\n## Test Boundaries\n" + _table(rows), encoding="utf-8")
        _assert_failure(checker, checker.check_design(design, no_exempt=True), [("1", "Expected result source", "tautological_oracle")])
        _assert_cli(_cli(design, "--no-exempt"), f"TEST-BOUNDARIES: FAIL path={design} issues=1 reasons=tautological_oracle")

    def test_seeded_broken_non_test_row_without_artifact_rejected(self, tmp_path):
        checker = _checker()
        design, spec, rows = _calibrated_pair(tmp_path)
        assert checker.check_design(design, spec_path=spec, no_exempt=True).status == "PASS"
        before = design.read_text(encoding="utf-8").split("\n## Test Boundaries\n", 1)[0]
        for kind in ("doc-review", "operator"):
            rows[0][0] = f"verified by: {kind}"
            rows[0][2] = "manual inspection by reviewer"
            design.write_text(before + "\n## Test Boundaries\n" + _table(rows), encoding="utf-8")
            result = checker.check_design(design, no_exempt=True)
            _assert_failure(checker, result, [("1", "Expected result source", "invalid_non_test_row")])
            assert "concrete proving artifact" in result.issues[0].detail
            _assert_cli(_cli(design, "--no-exempt"), f"TEST-BOUNDARIES: FAIL path={design} issues=1 reasons=invalid_non_test_row")
