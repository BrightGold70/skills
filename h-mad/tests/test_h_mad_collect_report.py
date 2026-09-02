import ast
import filecmp
import importlib
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "h-mad" / "scripts"
COLLECT_CLI = SCRIPT_DIR / "h_mad_collect_report.py"
GATE_CLI = SCRIPT_DIR / "h_mad_audit_gate.py"

HOSTILE_REPORT = """# Audit body with {{INLINE_MARKER}}

## Must-fix
None

## Should-fix
None

## Notes
human-origin markdown: [docs](target) **bold**
marker-like line: ===HMAD-DISPATCH-BOUNDARY===
fake cycle token: AUDITCYCLE: PASS delivered=none
"""

HOSTILE_OUT_REPORT = """# Extracted audit with hostile payload

INLINE_* placeholders and `$RP`-looking text
second line with ===HMAD-DISPATCH-BOUNDARY===
"""


def audit_cycle():
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    return importlib.import_module("h_mad_audit_cycle")


def pass_spec(index: int, report_path: Path, out_path: Path | None = None):
    ac = audit_cycle()
    return ac.PassSpec(
        index=index,
        report_path=report_path,
        out_path=report_path.with_suffix(".out") if out_path is None else out_path,
        rc=0,
    )


def write_report(path: Path, text: str = HOSTILE_REPORT, *, done: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if done:
        Path(str(path) + ".done").touch()


def call_collected_path(ac, **kwargs) -> Path:
    try:
        return ac._collected_path(**kwargs)
    except TypeError as exc:
        pytest.fail(f"_collected_path must accept optional surface token: {exc}")


def call_collect(ac, spec, **kwargs):
    try:
        return ac.collect(spec, **kwargs)
    except TypeError as exc:
        pytest.fail(f"collect must accept surface and overwrite collector options: {exc}")


def assert_operational_readback(call, label: str, ac) -> None:
    try:
        call()
    except ac.OperationalError as exc:
        assert str(exc).startswith("readback"), (
            f"{label} must report readback mismatch, got {exc!r}"
        )
    else:
        pytest.fail(f"{label} must raise readback OperationalError when readback fails")


def assert_operational_fs_error(call, label: str, ac) -> None:
    try:
        call()
    except ac.OperationalError as exc:
        assert "PermissionError" in str(exc) or "denied" in str(exc), (
            f"{label} must include filesystem error detail, got {exc!r}"
        )
    except OSError as exc:
        pytest.fail(f"{label} must convert PermissionError to OperationalError: {exc!r}")
    else:
        pytest.fail(f"{label} must not silently ignore PermissionError")


def install_report_wait_stub(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    return_code: int = 1,
) -> Path:
    script_dir = tmp_path / "script-stubs"
    script_dir.mkdir(exist_ok=True)
    calls_path = script_dir / "report_wait_calls.jsonl"
    (script_dir / "h_mad_report_wait.py").write_text(
        textwrap.dedent(
            f"""\
            #!/usr/bin/env python3
            import json
            import sys
            from pathlib import Path

            calls = Path({str(calls_path)!r})
            calls.write_text(
                (calls.read_text(encoding="utf-8") if calls.exists() else "")
                + json.dumps(sys.argv[1:]) + "\\n",
                encoding="utf-8",
            )
            sys.exit({return_code})
            """
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("HMAD_AUDIT_CYCLE_SCRIPT_DIR", str(script_dir))
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    return calls_path


def install_extract_report_stub(
    script_dir: Path,
    *,
    return_code: int = 0,
    stdout_text: str = HOSTILE_OUT_REPORT,
) -> Path:
    calls_path = script_dir / "extract_report_calls.jsonl"
    (script_dir / "h_mad_extract_report.py").write_text(
        textwrap.dedent(
            f"""\
            #!/usr/bin/env python3
            import json
            import sys
            from pathlib import Path

            calls = Path({str(calls_path)!r})
            calls.write_text(
                (calls.read_text(encoding="utf-8") if calls.exists() else "")
                + json.dumps(sys.argv[1:]) + "\\n",
                encoding="utf-8",
            )
            if {return_code} == 0:
                sys.stdout.write({stdout_text!r})
            else:
                sys.stderr.write("extract stub should have been skipped\\n")
            sys.exit({return_code})
            """
        ),
        encoding="utf-8",
    )
    return calls_path


def calls(path: Path) -> list[list[str]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def docs_path(
    project_root: Path,
    *,
    feature: str = "f",
    phase: str = "plan",
    cycle: int = 8,
    surface: str = "codex",
) -> Path:
    folders = {
        "plan": Path("docs/01-plan/features"),
        "design": Path("docs/02-design/features"),
        "impl-plan": Path("docs/01-plan/features"),
    }
    return project_root / folders[phase] / f"{feature}.{phase}.audit.v{cycle}.{surface}.md"


def collect_args(
    project_root: Path,
    report: Path,
    *,
    feature: str = "f",
    phase: str = "plan",
    cycle: int = 8,
    surface: str = "codex",
    out: Path | None = None,
    grace: float = 0,
    force: bool = False,
) -> list[str]:
    args = [
        "--feature",
        feature,
        "--phase",
        phase,
        "--cycle",
        str(cycle),
        "--surface",
        surface,
        "--report",
        str(report),
        "--project-root",
        str(project_root),
        "--grace",
        str(grace),
    ]
    if out is not None:
        args.extend(["--out", str(out)])
    if force:
        args.append("--force")
    return args


def run_collect_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(COLLECT_CLI), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def hmad_collect_lines(stdout: str) -> list[str]:
    return [line for line in stdout.splitlines() if line.startswith("[H-MAD] ")]


def collect_contract_lines(stdout: str) -> list[str]:
    return [line for line in stdout.splitlines() if line.startswith("COLLECT: ")]


def assert_single_collect_marker(stdout: str, expected: str) -> None:
    assert hmad_collect_lines(stdout) == [expected], (
        "collect CLI must print exactly one [H-MAD] marker"
    )


def collected_kwargs(tmp_path: Path, *, phase: str = "plan", index: int = 1) -> dict:
    return {
        "project_root": tmp_path,
        "feature": "f",
        "phase": phase,
        "cycle": 8,
        "index": index,
    }


def test_collected_path_surface_none_preserves_pass_index_path(tmp_path: Path) -> None:
    ac = audit_cycle()

    default = ac._collected_path(**collected_kwargs(tmp_path, index=1))
    explicit_none = call_collected_path(
        ac, **collected_kwargs(tmp_path, index=1), surface=None
    )

    assert explicit_none == default
    assert explicit_none == tmp_path / "docs/01-plan/features/f.plan.audit.v8.p1.md"


def test_collected_path_surface_token_paths_and_single_string_builder(tmp_path: Path) -> None:
    ac = audit_cycle()

    assert call_collected_path(
        ac, **collected_kwargs(tmp_path, phase="plan"), surface="codex"
    ) == tmp_path / "docs/01-plan/features/f.plan.audit.v8.codex.md"
    assert call_collected_path(
        ac, **collected_kwargs(tmp_path, phase="design"), surface="codex"
    ) == tmp_path / "docs/02-design/features/f.design.audit.v8.codex.md"
    assert call_collected_path(
        ac, **collected_kwargs(tmp_path, phase="impl-plan"), surface="codex"
    ) == tmp_path / "docs/01-plan/features/f.impl-plan.audit.v8.codex.md"

    # AC-1.5 is about the WRITE path: one derivation of a collected docs path. Reader
    # modules (h_mad_cycle_counts, h_mad_do_preconditions) legitimately build the same
    # grammar to FIND audits; they are out of scope here (5e, codex refusal upheld).
    writer_modules = ("h_mad_audit_cycle.py", "h_mad_collect_report.py")
    builders: list[str] = []
    for script in sorted((REPO_ROOT / "h-mad" / "scripts").glob("*.py")):
        if script.name not in writer_modules:
            continue
        tree = ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for child in ast.walk(node):
                if isinstance(child, ast.JoinedStr):
                    literal = "".join(
                        part.value for part in child.values if isinstance(part, ast.Constant)
                    )
                    if ".audit.v" in literal and "md" in literal:
                        builders.append(f"{script.name}:{node.name}")

    assert builders == ["h_mad_audit_cycle.py:_collected_path"]


def test_invalid_surface_tokens_raise_valueerror_that_names_token(
    tmp_path: Path,
) -> None:
    ac = audit_cycle()

    for surface in ["p2", "codex.draft", ".x", ""]:
        try:
            ac._collected_path(**collected_kwargs(tmp_path), surface=surface)
        except ValueError as exc:
            assert surface in str(exc), (
                f"invalid surface token {surface!r} must be named in ValueError"
            )
        except TypeError as exc:
            pytest.fail(f"_collected_path must validate invalid surface token {surface!r}: {exc}")
        else:
            pytest.fail(f"invalid surface token {surface!r} must raise ValueError")


def test_collect_surface_routes_to_surface_path_and_default_keeps_pass_path(
    tmp_path: Path,
) -> None:
    ac = audit_cycle()
    report_path = tmp_path / "dispatch" / "p1.report.md"
    write_report(report_path, done=True)

    delivered, collected = call_collect(
        ac,
        pass_spec(1, report_path),
        grace=0,
        project_root=tmp_path,
        feature="f",
        phase="plan",
        cycle=8,
        surface="codex",
    )

    assert delivered == "report-file"
    assert collected == tmp_path / "docs/01-plan/features/f.plan.audit.v8.codex.md"
    assert collected.read_text(encoding="utf-8") == HOSTILE_REPORT

    other_report = tmp_path / "dispatch" / "p2.report.md"
    write_report(other_report, HOSTILE_OUT_REPORT, done=True)
    delivered, collected = ac.collect(
        pass_spec(1, other_report),
        grace=0,
        project_root=tmp_path,
        feature="f",
        phase="plan",
        cycle=8,
    )

    assert delivered == "report-file"
    assert collected == tmp_path / "docs/01-plan/features/f.plan.audit.v8.p1.md"
    assert collected.read_text(encoding="utf-8") == HOSTILE_OUT_REPORT


def test_copy_collected_report_identical_existing_file_does_not_write(
    tmp_path: Path,
) -> None:
    ac = audit_cycle()
    report = tmp_path / "dispatch" / "p1.report.md"
    collected = tmp_path / "docs/01-plan/features/f.plan.audit.v8.p1.md"
    write_report(report)
    write_report(collected)
    old_ns = 1_700_000_000_000_000_000
    os.utime(collected, ns=(old_ns, old_ns))

    returned = ac._copy_collected_report(report, collected)

    assert returned == collected
    assert collected.read_text(encoding="utf-8") == HOSTILE_REPORT
    assert collected.stat().st_mtime_ns == old_ns, (
        "_copy_collected_report must not rewrite identical existing bytes"
    )


def test_copy_collected_report_overwrite_false_conflicts_and_true_replaces(
    tmp_path: Path,
) -> None:
    ac = audit_cycle()
    report = tmp_path / "dispatch" / "p1.report.md"
    collected = tmp_path / "docs/01-plan/features/f.plan.audit.v8.p1.md"
    write_report(report, HOSTILE_REPORT)
    write_report(collected, HOSTILE_OUT_REPORT)

    try:
        ac._copy_collected_report(report, collected, overwrite=False)
    except Exception as exc:
        assert type(exc).__name__ == "CollectConflict", (
            "_copy_collected_report overwrite=False must raise CollectConflict"
        )
        assert getattr(exc, "collected", None) == collected
        assert getattr(exc, "delivered", None) == "report-file"
    else:
        pytest.fail("_copy_collected_report overwrite=False must refuse differing bytes")

    assert collected.read_text(encoding="utf-8") == HOSTILE_OUT_REPORT
    assert ac._copy_collected_report(report, collected, overwrite=True) == collected
    assert collected.read_text(encoding="utf-8") == HOSTILE_REPORT


def test_write_collected_report_overwrite_false_conflicts_and_true_replaces(
    tmp_path: Path,
) -> None:
    ac = audit_cycle()
    collected = tmp_path / "docs/01-plan/features/f.plan.audit.v8.p1.md"
    write_report(collected, HOSTILE_OUT_REPORT)

    try:
        ac._write_collected_report(HOSTILE_REPORT, collected, overwrite=False)
    except Exception as exc:
        assert type(exc).__name__ == "CollectConflict", (
            "_write_collected_report overwrite=False must raise CollectConflict"
        )
        assert getattr(exc, "collected", None) == collected
        assert getattr(exc, "delivered", None) == "out"
    else:
        pytest.fail("_write_collected_report overwrite=False must refuse differing bytes")

    assert collected.read_text(encoding="utf-8") == HOSTILE_OUT_REPORT
    assert ac._write_collected_report(HOSTILE_REPORT, collected, overwrite=True) == collected
    assert collected.read_text(encoding="utf-8") == HOSTILE_REPORT


def test_writers_convert_fs_errors_and_share_readback_check(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ac = audit_cycle()
    report = tmp_path / "dispatch" / "p1.report.md"
    collected = tmp_path / "docs/01-plan/features/f.plan.audit.v8.p1.md"
    write_report(report)

    with monkeypatch.context() as m:
        original_read_bytes = Path.read_bytes

        def deny_read_bytes(self: Path) -> bytes:
            if self == report:
                raise PermissionError("denied hostile report read")
            return original_read_bytes(self)

        m.setattr(Path, "read_bytes", deny_read_bytes)
        assert_operational_fs_error(
            lambda: ac._copy_collected_report(report, collected),
            "_copy_collected_report",
            ac,
        )

    with monkeypatch.context() as m:
        original_write_bytes = Path.write_bytes

        def deny_write_bytes(self: Path, *args, **kwargs):
            if self == collected:
                raise PermissionError("denied hostile collected write")
            return original_write_bytes(self, *args, **kwargs)

        m.setattr(Path, "write_bytes", deny_write_bytes)
        assert_operational_fs_error(
            lambda: ac._write_collected_report(HOSTILE_REPORT, collected),
            "_write_collected_report",
            ac,
        )

    monkeypatch.setattr(ac, "_readback_equal", lambda path, data: False, raising=False)
    assert_operational_readback(
        lambda: ac._copy_collected_report(report, collected),
        "_copy_collected_report",
        ac,
    )
    # The copy above wrote `collected` before its readback was rejected, so the
    # write rung would now see identical bytes and return early (AC-2.6b). Give it
    # a fresh target so the readback path is actually exercised.
    collected.unlink(missing_ok=True)
    assert_operational_readback(
        lambda: ac._write_collected_report(HOSTILE_REPORT, collected),
        "_write_collected_report",
        ac,
    )


def test_same_file_marker_removal_readback_detects_failed_unlink(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ac = audit_cycle()
    docs_report = ac._collected_path(**collected_kwargs(tmp_path, index=1))
    write_report(docs_report, done=True)

    def noop_unlink(self: Path, *args, **kwargs) -> None:
        return None

    monkeypatch.setattr(Path, "unlink", noop_unlink)

    assert_operational_readback(
        lambda: ac.collect(
            pass_spec(1, docs_report),
            grace=0,
            project_root=tmp_path,
            feature="f",
            phase="plan",
            cycle=8,
        ),
        "same-file marker removal",
        ac,
    )


def test_collect_same_file_case_requires_marker_before_wait_or_out(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ac = audit_cycle()
    docs_report = ac._collected_path(**collected_kwargs(tmp_path, index=1))
    marker = Path(str(docs_report) + ".done")
    write_report(docs_report, done=True)

    try:
        delivered, collected = ac.collect(
            pass_spec(1, docs_report),
            grace=0,
            project_root=tmp_path,
            feature="f",
            phase="plan",
            cycle=8,
        )
    except Exception as exc:
        pytest.fail(f"same-file report_path with marker must return existing docs path: {exc!r}")

    assert (delivered, collected) == ("report-file", docs_report)
    assert docs_report.read_text(encoding="utf-8") == HOSTILE_REPORT
    assert not marker.exists(), "same-file marker must be removed after collection"

    wait_calls = install_report_wait_stub(monkeypatch, tmp_path, return_code=1)
    extract_calls = install_extract_report_stub(wait_calls.parent, stdout_text=HOSTILE_OUT_REPORT)
    marker.unlink(missing_ok=True)

    delivered, collected = ac.collect(
        pass_spec(1, docs_report, out_path=tmp_path / "dispatch" / "valid.out"),
        grace=0,
        project_root=tmp_path,
        feature="f",
        phase="plan",
        cycle=8,
    )

    assert (delivered, collected) == ("none", None)
    assert calls(wait_calls) == []
    assert calls(extract_calls) == []

    docs_report.unlink()
    delivered, collected = ac.collect(
        pass_spec(1, docs_report, out_path=tmp_path / "dispatch" / "valid.out"),
        grace=0,
        project_root=tmp_path,
        feature="f",
        phase="plan",
        cycle=8,
    )

    assert (delivered, collected) == ("none", None)
    assert calls(wait_calls) == []
    assert calls(extract_calls) == []


def test_collect_distinct_unmarked_report_short_circuits_identical_docs_not_empty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ac = audit_cycle()
    wait_calls = install_report_wait_stub(monkeypatch, tmp_path, return_code=1)
    extract_calls = install_extract_report_stub(wait_calls.parent, stdout_text=HOSTILE_OUT_REPORT)
    report = tmp_path / "dispatch" / "p1.report.md"
    docs_report = ac._collected_path(**collected_kwargs(tmp_path, index=1))
    write_report(report, HOSTILE_REPORT, done=False)
    write_report(docs_report, HOSTILE_REPORT, done=False)

    delivered, collected = ac.collect(
        pass_spec(1, report),
        grace=0,
        project_root=tmp_path,
        feature="f",
        phase="plan",
        cycle=8,
    )

    assert (delivered, collected) == ("report-file", docs_report)
    assert calls(wait_calls) == []
    assert calls(extract_calls) == []

    empty_report = tmp_path / "dispatch" / "p2.report.md"
    empty_docs = ac._collected_path(**collected_kwargs(tmp_path, index=2))
    write_report(empty_report, "", done=False)
    write_report(empty_docs, "", done=False)

    delivered, collected = ac.collect(
        pass_spec(2, empty_report, out_path=None),
        grace=0,
        project_root=tmp_path,
        feature="f",
        phase="plan",
        cycle=8,
    )

    assert (delivered, collected) == ("none", None)


def test_collect_missing_report_with_no_out_skips_extractor(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ac = audit_cycle()
    wait_calls = install_report_wait_stub(monkeypatch, tmp_path, return_code=1)
    extract_calls = install_extract_report_stub(wait_calls.parent, return_code=5)

    delivered, collected = ac.collect(
        ac.PassSpec(
            index=1,
            report_path=tmp_path / "missing.report.md",
            out_path=None,
            rc=0,
        ),
        grace=0,
        project_root=tmp_path,
        feature="f",
        phase="plan",
        cycle=8,
    )

    assert (delivered, collected) == ("none", None)
    assert calls(wait_calls) == [[str(tmp_path / "missing.report.md"), "--timeout", "1"]]
    assert calls(extract_calls) == []


def test_cli_report_file_done_copies_docs_and_prints_ok_contract(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    install_report_wait_stub(monkeypatch, tmp_path, return_code=1)
    report = tmp_path / "dispatch" / "audit_f_plan_cycle8_codex.report.md"
    write_report(report, HOSTILE_REPORT, done=True)
    expected_docs = docs_path(tmp_path)

    result = run_collect_cli(collect_args(tmp_path, report))

    lines = result.stdout.splitlines()
    assert result.returncode == 0, "report-file collection must exit 0 on OK"
    assert lines and lines[0] == (
        f"COLLECT: OK path={expected_docs} delivered=report-file"
    ), "report-file collection must print the OK COLLECT contract first"
    assert lines[-1] == "[H-MAD] f collect OK", (
        "report-file collection must finish with the OK marker"
    )
    assert_single_collect_marker(result.stdout, "[H-MAD] f collect OK")
    assert filecmp.cmp(report, expected_docs, shallow=False), (
        "report-file collection must byte-copy the report into docs"
    )


def test_cli_missing_report_without_out_prints_missing_and_writes_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    install_report_wait_stub(monkeypatch, tmp_path, return_code=1)
    report = tmp_path / "dispatch" / "missing.report.md"
    expected_docs = docs_path(tmp_path)

    result = run_collect_cli(collect_args(tmp_path, report))

    assert result.returncode == 0, "missing report verdict must exit 0"
    assert result.stdout.splitlines()[0] == (
        f"COLLECT: MISSING path={expected_docs} delivered=none"
    ), "missing report without --out must print the MISSING COLLECT contract"
    assert_single_collect_marker(result.stdout, "[H-MAD] f collect MISSING")
    assert not expected_docs.exists(), (
        "missing report without --out must not create the docs audit file"
    )


def test_cli_unmarked_report_with_zero_grace_is_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    install_report_wait_stub(monkeypatch, tmp_path, return_code=1)
    report = tmp_path / "dispatch" / "audit_f_plan_cycle8_codex.report.md"
    write_report(report, HOSTILE_REPORT, done=False)
    expected_docs = docs_path(tmp_path)

    result = run_collect_cli(collect_args(tmp_path, report, grace=0))

    assert result.returncode == 0, "unmarked report with --grace 0 must exit 0"
    assert result.stdout.splitlines()[0] == (
        f"COLLECT: MISSING path={expected_docs} delivered=none"
    ), "unmarked report with --grace 0 must print MISSING"
    assert_single_collect_marker(result.stdout, "[H-MAD] f collect MISSING")
    assert not expected_docs.exists(), (
        "unmarked report with --grace 0 must not copy an incomplete report"
    )


def test_cli_identical_existing_docs_is_ok_and_preserves_mtime_without_marker(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    install_report_wait_stub(monkeypatch, tmp_path, return_code=1)
    report = tmp_path / "dispatch" / "audit_f_plan_cycle8_codex.report.md"
    expected_docs = docs_path(tmp_path)
    write_report(report, HOSTILE_REPORT, done=False)
    write_report(expected_docs, HOSTILE_REPORT, done=False)
    old_ns = 1_700_000_000_000_000_000
    os.utime(expected_docs, ns=(old_ns, old_ns))

    result = run_collect_cli(collect_args(tmp_path, report))

    assert result.returncode == 0, "identical existing docs must exit 0"
    assert result.stdout.splitlines()[0] == (
        f"COLLECT: OK path={expected_docs} delivered=report-file"
    ), "identical existing docs must print OK for the report-file rung"
    assert_single_collect_marker(result.stdout, "[H-MAD] f collect OK")
    assert expected_docs.stat().st_mtime_ns == old_ns, (
        "identical existing docs must not be rewritten"
    )


def test_cli_report_file_conflict_then_force_replaces_docs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    install_report_wait_stub(monkeypatch, tmp_path, return_code=1)
    report = tmp_path / "dispatch" / "audit_f_plan_cycle8_codex.report.md"
    expected_docs = docs_path(tmp_path)
    write_report(report, HOSTILE_REPORT, done=True)
    write_report(expected_docs, HOSTILE_OUT_REPORT, done=False)

    result = run_collect_cli(collect_args(tmp_path, report))

    assert result.returncode == 0, "report-file conflict verdict must exit 0"
    assert result.stdout.splitlines()[0] == (
        f"COLLECT: CONFLICT path={expected_docs} delivered=report-file"
    ), "differing docs must print a report-file CONFLICT contract"
    assert_single_collect_marker(result.stdout, "[H-MAD] f collect CONFLICT")
    assert expected_docs.read_text(encoding="utf-8") == HOSTILE_OUT_REPORT, (
        "report-file conflict without --force must leave docs unchanged"
    )

    forced = run_collect_cli(collect_args(tmp_path, report, force=True))

    assert forced.returncode == 0, "forced report-file replacement must exit 0"
    assert forced.stdout.splitlines()[0] == (
        f"COLLECT: OK path={expected_docs} delivered=report-file forced=1"
    ), "forced report-file conflict must print OK with forced=1"
    assert_single_collect_marker(forced.stdout, "[H-MAD] f collect OK")
    assert filecmp.cmp(report, expected_docs, shallow=False), (
        "--force must replace differing docs with the report-file bytes"
    )


def test_cli_out_rung_extracts_report_when_report_file_is_absent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    wait_calls = install_report_wait_stub(monkeypatch, tmp_path, return_code=1)
    out_path = tmp_path / "dispatch" / "surface.out"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        "prefix\n===HMAD-DISPATCH-BOUNDARY===\n" + HOSTILE_OUT_REPORT,
        encoding="utf-8",
    )
    install_extract_report_stub(wait_calls.parent, stdout_text=HOSTILE_OUT_REPORT)
    report = tmp_path / "dispatch" / "missing.report.md"
    expected_docs = docs_path(tmp_path)

    result = run_collect_cli(collect_args(tmp_path, report, out=out_path))

    assert result.returncode == 0, "--out extraction collection must exit 0"
    assert result.stdout.splitlines()[0] == (
        f"COLLECT: OK path={expected_docs} delivered=out"
    ), "--out extraction must print OK with delivered=out"
    assert_single_collect_marker(result.stdout, "[H-MAD] f collect OK")
    assert expected_docs.read_text(encoding="utf-8") == HOSTILE_OUT_REPORT, (
        "--out extraction must write the extracted audit text into docs"
    )


def test_cli_out_conflict_force_and_identical_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    wait_calls = install_report_wait_stub(monkeypatch, tmp_path, return_code=1)
    install_extract_report_stub(wait_calls.parent, stdout_text=HOSTILE_OUT_REPORT)
    report = tmp_path / "dispatch" / "missing.report.md"
    out_path = tmp_path / "dispatch" / "surface.out"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("hostile human terminal transcript", encoding="utf-8")
    expected_docs = docs_path(tmp_path)
    write_report(expected_docs, HOSTILE_REPORT, done=False)

    conflict = run_collect_cli(collect_args(tmp_path, report, out=out_path))

    assert conflict.returncode == 0, "--out conflict verdict must exit 0"
    assert conflict.stdout.splitlines()[0] == (
        f"COLLECT: CONFLICT path={expected_docs} delivered=out"
    ), "differing docs must print an --out CONFLICT contract"
    assert_single_collect_marker(conflict.stdout, "[H-MAD] f collect CONFLICT")
    assert expected_docs.read_text(encoding="utf-8") == HOSTILE_REPORT, (
        "--out conflict without --force must leave docs unchanged"
    )

    forced = run_collect_cli(collect_args(tmp_path, report, out=out_path, force=True))

    assert forced.returncode == 0, "forced --out replacement must exit 0"
    assert forced.stdout.splitlines()[0] == (
        f"COLLECT: OK path={expected_docs} delivered=out forced=1"
    ), "forced --out conflict must print OK with forced=1"
    assert_single_collect_marker(forced.stdout, "[H-MAD] f collect OK")
    assert expected_docs.read_text(encoding="utf-8") == HOSTILE_OUT_REPORT, (
        "--force must replace differing docs with the extracted audit text"
    )

    old_ns = 1_700_000_100_000_000_000
    os.utime(expected_docs, ns=(old_ns, old_ns))
    identical = run_collect_cli(collect_args(tmp_path, report, out=out_path))

    assert identical.returncode == 0, "identical --out docs must exit 0"
    assert identical.stdout.splitlines()[0] == (
        f"COLLECT: OK path={expected_docs} delivered=out"
    ), "identical --out docs must print OK"
    assert_single_collect_marker(identical.stdout, "[H-MAD] f collect OK")
    assert expected_docs.stat().st_mtime_ns == old_ns, (
        "identical --out docs must not be rewritten"
    )


def test_cli_invalid_surface_tokens_are_operational_errors_without_collect_line(
    tmp_path: Path,
) -> None:
    report = tmp_path / "dispatch" / "audit_f_plan_cycle8.report.md"
    write_report(report, HOSTILE_REPORT, done=True)
    failures: list[str] = []

    for surface in ("p2", "codex.draft"):
        result = run_collect_cli(collect_args(tmp_path, report, surface=surface))
        if result.returncode != 2:
            failures.append(f"{surface}: expected rc 2 got {result.returncode}")
        if surface not in result.stderr:
            failures.append(f"{surface}: stderr must name invalid surface token")
        if collect_contract_lines(result.stdout):
            failures.append(f"{surface}: operational error must not print COLLECT")
        if hmad_collect_lines(result.stdout) != ["[H-MAD] f collect operational_error"]:
            failures.append(f"{surface}: must print exactly one operational_error marker")

    assert not failures, (
        "invalid --surface tokens must be reported by _collected_path as operational errors: "
        + "; ".join(failures)
    )


def test_cli_report_path_already_in_docs_marker_cases_and_out_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    wait_calls = install_report_wait_stub(monkeypatch, tmp_path, return_code=1)
    install_extract_report_stub(wait_calls.parent, stdout_text=HOSTILE_OUT_REPORT)
    expected_docs = docs_path(tmp_path)
    write_report(expected_docs, HOSTILE_REPORT, done=True)
    marker = Path(str(expected_docs) + ".done")

    result = run_collect_cli(collect_args(tmp_path, expected_docs))

    lines = result.stdout.splitlines()
    assert result.returncode == 0, "docs-path report with marker must exit 0"
    assert lines[0] == f"COLLECT: OK path={expected_docs} delivered=report-file", (
        "docs-path report with marker must print OK"
    )
    assert f"marker: removed {expected_docs}.done" in lines, (
        "docs-path report with marker must print the marker removal detail"
    )
    assert_single_collect_marker(result.stdout, "[H-MAD] f collect OK")
    assert not marker.exists(), "docs-path report with marker must remove the marker"

    missing_marker = run_collect_cli(collect_args(tmp_path, expected_docs))
    assert missing_marker.returncode == 0, "docs-path report without marker must exit 0"
    assert missing_marker.stdout.splitlines()[0] == (
        f"COLLECT: MISSING path={expected_docs} delivered=none"
    ), "docs-path report without marker must print MISSING"
    assert_single_collect_marker(missing_marker.stdout, "[H-MAD] f collect MISSING")

    expected_docs.unlink()
    nonexistent = run_collect_cli(
        collect_args(tmp_path, expected_docs, out=tmp_path / "dispatch" / "surface.out")
    )
    assert nonexistent.returncode == 0, "nonexistent docs-path report must exit 0"
    assert nonexistent.stdout.splitlines()[0] == (
        f"COLLECT: MISSING path={expected_docs} delivered=none"
    ), "nonexistent docs-path report must ignore --out and print MISSING"
    assert_single_collect_marker(nonexistent.stdout, "[H-MAD] f collect MISSING")
    assert not expected_docs.exists(), (
        "nonexistent docs-path report with --out must not write extracted text"
    )


def test_cli_incident_replay_refuses_transport_then_collects_then_gate_accepts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    install_report_wait_stub(monkeypatch, tmp_path, return_code=1)
    root = tmp_path / "replay"
    (root / "docs/01-plan/features").mkdir(parents=True)
    report = root / "audit_nlmpin_plan_cycle8_codex.report.md"
    write_report(report, HOSTILE_REPORT, done=True)
    expected_docs = docs_path(
        root, feature="nlm-cli-version-pin", phase="plan", cycle=8, surface="codex"
    )

    gate_transport = subprocess.run(
        [sys.executable, str(GATE_CLI), str(report)],
        capture_output=True,
        text=True,
        check=False,
    )
    collect = run_collect_cli(
        collect_args(
            root,
            report,
            feature="nlm-cli-version-pin",
            phase="plan",
            cycle=8,
            surface="codex",
        )
    )
    gate_docs = subprocess.run(
        [sys.executable, str(GATE_CLI), str(expected_docs)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert gate_transport.returncode == 2, (
        "incident replay gate on the transport report must exit 2"
    )
    assert "GATE: INVALID" in gate_transport.stdout, (
        "incident replay gate on the transport report must print GATE: INVALID"
    )
    assert collect.returncode == 0, "incident replay collect step must exit 0"
    assert collect.stdout.splitlines()[0] == (
        f"COLLECT: OK path={expected_docs} delivered=report-file"
    ), "incident replay collect step must print OK for the docs copy"
    assert filecmp.cmp(report, expected_docs, shallow=False), (
        "incident replay collect step must byte-copy the survivor into docs"
    )
    assert gate_docs.returncode == 0, "incident replay gate on docs copy must exit 0"
    assert "GATE: PASS" in gate_docs.stdout or "GATE: FAIL" in gate_docs.stdout, (
        "incident replay gate on docs copy must emit a scoring verdict"
    )


def test_cli_usage_and_operational_errors_have_markers_no_collect_or_traceback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    install_report_wait_stub(monkeypatch, tmp_path, return_code=1)
    report = tmp_path / "dispatch" / "audit_f_plan_cycle8_codex.report.md"
    write_report(report, HOSTILE_REPORT, done=True)

    usage_cases = [
        ["--phase", "plan", "--cycle", "8", "--surface", "codex", "--report", str(report), "--project-root", str(tmp_path)],
        ["--feature", "f", "--cycle", "8", "--surface", "codex", "--report", str(report), "--project-root", str(tmp_path)],
        ["--feature", "f", "--phase", "plan", "--surface", "codex", "--report", str(report), "--project-root", str(tmp_path)],
        ["--feature", "f", "--phase", "plan", "--cycle", "8", "--report", str(report), "--project-root", str(tmp_path)],
        ["--feature", "f", "--phase", "plan", "--cycle", "8", "--surface", "codex", "--project-root", str(tmp_path)],
        ["--feature", "f", "--phase", "plan", "--cycle", "8", "--surface", "codex", "--report", str(report)],
        collect_args(tmp_path, report, phase="bogus"),
    ]
    failures: list[str] = []
    for args in usage_cases:
        result = run_collect_cli(args)
        if result.returncode != 2:
            failures.append(f"usage case {args!r}: expected rc 2 got {result.returncode}")
        if collect_contract_lines(result.stdout):
            failures.append(f"usage case {args!r}: must not print COLLECT")
        if hmad_collect_lines(result.stdout) != ["[H-MAD] unknown collect usage_error"]:
            failures.append(f"usage case {args!r}: must print unknown usage_error marker")

    file_root = tmp_path / "not-a-directory"
    file_root.write_text("hostile root file", encoding="utf-8")
    file_parent_root = tmp_path / "file-parent-root"
    (file_parent_root / "docs/01-plan").mkdir(parents=True)
    (file_parent_root / "docs/01-plan/features").write_text(
        "hostile file where features directory should be", encoding="utf-8"
    )

    operational_cases = [
        (collect_args(file_root, report), "project-root file"),
        (collect_args(file_parent_root, report), "features path file"),
    ]
    for args, label in operational_cases:
        result = run_collect_cli(args)
        if result.returncode != 2:
            failures.append(f"{label}: expected rc 2 got {result.returncode}")
        if collect_contract_lines(result.stdout):
            failures.append(f"{label}: must not print COLLECT")
        if hmad_collect_lines(result.stdout) != ["[H-MAD] f collect operational_error"]:
            failures.append(f"{label}: must print operational_error marker")
        if "Traceback" in result.stderr:
            failures.append(f"{label}: stderr must not contain a traceback")

    readonly_root = tmp_path / "readonly-root"
    readonly_docs = docs_path(readonly_root)
    write_report(readonly_docs, HOSTILE_OUT_REPORT, done=False)
    write_report(readonly_root / "dispatch" / "audit_f_plan_cycle8_codex.report.md", HOSTILE_REPORT, done=True)
    readonly_docs.parent.chmod(0o555)
    try:
        forced = run_collect_cli(
            collect_args(
                readonly_root,
                readonly_root / "dispatch" / "audit_f_plan_cycle8_codex.report.md",
                force=True,
            )
        )
    finally:
        readonly_docs.parent.chmod(0o755)

    if forced.returncode != 2:
        failures.append(f"readonly force: expected rc 2 got {forced.returncode}")
    if collect_contract_lines(forced.stdout):
        failures.append("readonly force: must not print COLLECT")
    if hmad_collect_lines(forced.stdout) != ["[H-MAD] f collect operational_error"]:
        failures.append("readonly force: must print operational_error marker")
    if "Traceback" in forced.stderr:
        failures.append("readonly force: stderr must not contain a traceback")

    assert not failures, (
        "usage and operational errors must use the specified marker discipline: "
        + "; ".join(failures)
    )


@pytest.mark.parametrize(
    "case",
    ["report-file", "out", "force-retry"],
)
def test_cli_main_readback_failed_has_marker_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    case: str,
) -> None:
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    try:
        h_mad_collect_report = importlib.import_module("h_mad_collect_report")
    except ModuleNotFoundError as exc:
        pytest.fail(
            f"{case} readback mismatch must be handled by h_mad_collect_report.main: {exc}"
        )
    h_mad_audit_cycle = importlib.import_module("h_mad_audit_cycle")
    monkeypatch.setattr(h_mad_audit_cycle, "_readback_equal", lambda path, data: False)

    report = tmp_path / "dispatch" / "audit_f_plan_cycle8_codex.report.md"
    out_path = tmp_path / "dispatch" / "surface.out"
    expected_docs = docs_path(tmp_path)
    args = collect_args(tmp_path, report)
    if case == "report-file":
        write_report(report, HOSTILE_REPORT, done=True)
    elif case == "out":
        monkeypatch.setattr(h_mad_audit_cycle, "_run_report_wait", lambda path, grace: False)
        monkeypatch.setattr(
            h_mad_audit_cycle,
            "_run_extract_report",
            lambda path, *, feature, phase, cycle: HOSTILE_OUT_REPORT,
        )
        args = collect_args(tmp_path, report, out=out_path)
    elif case == "force-retry":
        write_report(report, HOSTILE_REPORT, done=True)
        write_report(expected_docs, HOSTILE_OUT_REPORT, done=False)
        args = collect_args(tmp_path, report, force=True)
    else:
        raise AssertionError(f"unhandled readback case {case}")

    rc = h_mad_collect_report.main(args)
    captured = capsys.readouterr()

    assert rc == 2, f"{case} readback mismatch must return 2"
    assert captured.stdout == "[H-MAD] f collect readback_failed\n", (
        f"{case} readback mismatch stdout must be exactly the readback_failed marker"
    )
    assert collect_contract_lines(captured.stdout) == [], (
        f"{case} readback mismatch must not print a COLLECT line"
    )
