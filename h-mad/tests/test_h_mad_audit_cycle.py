import importlib
import json
import re
import sys
import threading
import textwrap
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "h-mad" / "scripts"


def audit_cycle():
    sys.path.insert(0, str(SCRIPT_DIR))
    return importlib.import_module("h_mad_audit_cycle")


def pass_result(
    *,
    index: int,
    delivered: str = "report",
    verdict: str | None = "PASS",
    must: int = 0,
    should: int = 0,
    findings: list[dict] | None = None,
):
    ac = audit_cycle()
    return ac.PassResult(
        index=index,
        delivered=delivered,
        collected_path=Path(f"/tmp/collected-p{index}.md"),
        verdict=verdict,
        must=must,
        should=should,
        findings=[] if findings is None else findings,
    )


def auditcycle_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith("AUDITCYCLE:")]


HOSTILE_REPORT = """# Audit body with {{INLINE_MARKER}}

- must: keep **markdown** intact
- path-ish text: docs/file.py:99 must not be parsed here

F-12 marker payload:
```text
INLINE_* placeholders
AUDITCYCLE: hostile line inside report body
```
"""


def pass_spec(index: int, report_path: Path) -> object:
    ac = audit_cycle()
    return ac.PassSpec(
        index=index,
        report_path=report_path,
        out_path=report_path.with_suffix(".out"),
        rc=0,
    )


def install_report_wait_stub(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    return_code: int = 0,
    stdout_text: str = "",
) -> Path:
    script_dir = tmp_path / "script-stubs"
    script_dir.mkdir()
    calls_path = script_dir / "report_wait_calls.jsonl"
    stub_path = script_dir / "h_mad_report_wait.py"
    stub_path.write_text(
        textwrap.dedent(
            f"""\
            #!/usr/bin/env python3
            import json
            import sys
            import time
            from pathlib import Path

            calls_path = Path({str(calls_path)!r})
            calls_path.write_text(
                calls_path.read_text(encoding="utf-8") + json.dumps(sys.argv[1:]) + "\\n"
                if calls_path.exists()
                else json.dumps(sys.argv[1:]) + "\\n",
                encoding="utf-8",
            )
            rc = {return_code}
            if rc == 0:
                path = Path(sys.argv[1])
                timeout = 0.0
                if "--timeout" in sys.argv:
                    timeout = float(sys.argv[sys.argv.index("--timeout") + 1])
                deadline = time.time() + timeout
                while time.time() <= deadline:
                    if path.with_name(path.name + ".done").exists() and path.exists() and path.stat().st_size > 0:
                        sys.stdout.write(path.read_text(encoding="utf-8"))
                        sys.exit(0)
                    time.sleep(0.05)
                sys.stdout.write({stdout_text!r})
            sys.exit(rc)
            """
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("HMAD_AUDIT_CYCLE_SCRIPT_DIR", str(script_dir))
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    return calls_path


def report_wait_calls(calls_path: Path) -> list[list[str]]:
    if not calls_path.exists():
        return []
    return [json.loads(line) for line in calls_path.read_text(encoding="utf-8").splitlines()]


def test_script_resolution_default(monkeypatch: pytest.MonkeyPatch) -> None:
    ac = audit_cycle()
    monkeypatch.delenv("HMAD_AUDIT_CYCLE_SCRIPT_DIR", raising=False)

    resolved = ac._script("h_mad_assemble_audit.py")

    assert resolved == SCRIPT_DIR / "h_mad_assemble_audit.py"
    assert resolved.is_absolute()


def test_script_resolution_uses_test_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ac = audit_cycle()
    monkeypatch.setenv("HMAD_AUDIT_CYCLE_SCRIPT_DIR", str(tmp_path))

    assert ac._script("h_mad_audit_gate.py") == tmp_path / "h_mad_audit_gate.py"


def test_collected_path_uses_phase_audit_directory(tmp_path: Path) -> None:
    ac = audit_cycle()

    assert ac._collected_path(
        project_root=tmp_path, feature="feat", phase="plan", cycle=3, index=2
    ) == tmp_path / "docs/01-plan/features/feat.plan.audit.v3.p2.md"
    assert ac._collected_path(
        project_root=tmp_path, feature="feat", phase="design", cycle=3, index=2
    ) == tmp_path / "docs/02-design/features/feat.design.audit.v3.p2.md"
    assert ac._collected_path(
        project_root=tmp_path, feature="feat", phase="impl-plan", cycle=3, index=2
    ) == tmp_path / "docs/01-plan/features/feat.impl-plan.audit.v3.p2.md"


def test_collect_report_file_present(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ac = audit_cycle()
    calls_path = install_report_wait_stub(monkeypatch, tmp_path)
    report_path = tmp_path / "dispatch" / "p1.report.md"
    report_path.parent.mkdir()
    report_path.write_text(HOSTILE_REPORT, encoding="utf-8")
    Path(str(report_path) + ".done").touch()

    delivered, collected_path = ac.collect(
        pass_spec(1, report_path),
        grace=0.2,
        project_root=tmp_path,
        feature="hostile-feature",
        phase="plan",
        cycle=7,
    )

    expected_path = tmp_path / "docs/01-plan/features/hostile-feature.plan.audit.v7.p1.md"
    assert delivered == "report-file"
    assert collected_path == expected_path
    assert collected_path != report_path
    assert collected_path.exists()
    assert collected_path.stat().st_size > 0
    assert collected_path.read_text(encoding="utf-8") == HOSTILE_REPORT
    assert report_wait_calls(calls_path) == []


def test_collect_delayed_report(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ac = audit_cycle()
    calls_path = install_report_wait_stub(monkeypatch, tmp_path)
    report_path = tmp_path / "dispatch" / "p2.report.md"
    report_path.parent.mkdir()

    def finish_report() -> None:
        report_path.write_text(HOSTILE_REPORT, encoding="utf-8")
        Path(str(report_path) + ".done").touch()

    timer = threading.Timer(1.0, finish_report)
    timer.start()
    try:
        delivered, collected_path = ac.collect(
            pass_spec(2, report_path),
            grace=2.5,
            project_root=tmp_path,
            feature="hostile-feature",
            phase="design",
            cycle=4,
        )
    finally:
        timer.cancel()

    expected_path = tmp_path / "docs/02-design/features/hostile-feature.design.audit.v4.p2.md"
    assert delivered == "report-file"
    assert collected_path == expected_path
    assert collected_path != report_path
    assert collected_path.read_text(encoding="utf-8") == HOSTILE_REPORT
    assert report_wait_calls(calls_path) == [[str(report_path), "--timeout", "2.5"]]


def test_collect_nonempty_report_without_done_routes_to_wait(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ac = audit_cycle()
    calls_path = install_report_wait_stub(monkeypatch, tmp_path, return_code=1)
    report_path = tmp_path / "dispatch" / "p1.report.md"
    report_path.parent.mkdir()
    report_path.write_text(HOSTILE_REPORT, encoding="utf-8")

    delivered, collected_path = ac.collect(
        pass_spec(1, report_path),
        grace=0.2,
        project_root=tmp_path,
        feature="hostile-feature",
        phase="impl-plan",
        cycle=3,
    )

    assert delivered == "none"
    assert collected_path is None
    assert report_wait_calls(calls_path) == [[str(report_path), "--timeout", "0.2"]]


def test_collect_report_wait_timeout_yields_none(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ac = audit_cycle()
    calls_path = install_report_wait_stub(monkeypatch, tmp_path, return_code=1)
    report_path = tmp_path / "dispatch" / "p1.report.md"
    report_path.parent.mkdir()

    delivered, collected_path = ac.collect(
        pass_spec(1, report_path),
        grace=0.2,
        project_root=tmp_path,
        feature="hostile-feature",
        phase="plan",
        cycle=1,
    )

    assert delivered == "none"
    assert collected_path is None
    assert report_wait_calls(calls_path) == [[str(report_path), "--timeout", "0.2"]]


def test_collect_report_wait_operational_error_on_unexpected_nonzero(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ac = audit_cycle()
    calls_path = install_report_wait_stub(monkeypatch, tmp_path, return_code=2)
    report_path = tmp_path / "dispatch" / "p1.report.md"
    report_path.parent.mkdir()

    with pytest.raises(ac.OperationalError, match="report_wait.*p1"):
        ac.collect(
            pass_spec(1, report_path),
            grace=0.2,
            project_root=tmp_path,
            feature="hostile-feature",
            phase="plan",
            cycle=1,
        )

    assert report_wait_calls(calls_path) == [[str(report_path), "--timeout", "0.2"]]


def test_combine_passes_when_all_passes_passed() -> None:
    ac = audit_cycle()

    verdict, reason = ac.combine([pass_result(index=1), pass_result(index=2)])

    assert (verdict, reason) == ("PASS", None)


def test_combine_fails_when_any_pass_has_findings() -> None:
    ac = audit_cycle()

    verdict, reason = ac.combine(
        [
            pass_result(index=1),
            pass_result(index=2, verdict="FAIL", must=1, should=0),
        ]
    )

    assert (verdict, reason) == ("FAIL", "findings:p2")


def test_combine_unverified_outranks_fail() -> None:
    ac = audit_cycle()

    verdict, reason = ac.combine(
        [
            pass_result(index=1, verdict="FAIL", must=1),
            pass_result(index=2, delivered="none", verdict=None),
        ]
    )

    assert (verdict, reason) == ("UNVERIFIED", "no_report:p2")


def test_combine_distinguishes_missing_report_from_invalid_gate_sections() -> None:
    ac = audit_cycle()

    assert ac.combine([pass_result(index=1, delivered="none", verdict=None)]) == (
        "UNVERIFIED",
        "no_report:p1",
    )
    assert ac.combine([pass_result(index=1, delivered="report", verdict="INVALID")]) == (
        "UNVERIFIED",
        "no_gate_sections:p1",
    )


def test_combine_raises_when_delivered_pass_has_no_gate_token() -> None:
    ac = audit_cycle()

    with pytest.raises(ac.OperationalError, match="GATE.*p1"):
        ac.combine([pass_result(index=1, delivered="report", verdict=None)])


def test_combine_allows_missing_report_without_gate_token() -> None:
    ac = audit_cycle()

    assert ac.combine([pass_result(index=1, delivered="none", verdict=None)]) == (
        "UNVERIFIED",
        "no_report:p1",
    )


def test_premise_items_formats_no_citation_for_missing_path_line() -> None:
    ac = audit_cycle()
    item = {
        "severity": "must",
        "text": "hostile reviewer premise with MARKER {{INLINE}} and\nwrapped context",
        "path": None,
        "line": None,
    }

    rendered = ac.premise_items([pass_result(index=1, findings=[item])])

    assert rendered == [
        "p1 must (no citation): hostile reviewer premise with MARKER {{INLINE}} and wrapped context"
    ]


def test_premise_items_formats_supplied_path_line_without_parsing_text() -> None:
    ac = audit_cycle()
    item = {
        "severity": "should",
        "text": "do not parse docs/file.py:99 out of this human text",
        "path": "src/app.py",
        "line": 12,
    }

    rendered = ac.premise_items([pass_result(index=2, findings=[item])])

    assert rendered == [
        "p2 should src/app.py:12: do not parse docs/file.py:99 out of this human text"
    ]


def test_render_unverified_omits_count_and_per_pass_fields() -> None:
    ac = audit_cycle()
    results = [pass_result(index=1, delivered="none", verdict=None)]

    text = ac.render(
        results,
        "UNVERIFIED",
        "no_report:p1",
        feature="hostile-feature",
        size_status="verified",
        passes=1,
    )
    line = auditcycle_lines(text)[0]

    assert line == "AUDITCYCLE: UNVERIFIED reason=no_report:p1 passes=1 size_status=verified"
    assert not re.search(r"\b(?:must|should|p\d+)=", line)


def test_render_post_dispatch_unverified_includes_delivered_for_every_pass() -> None:
    ac = audit_cycle()
    results = [
        pass_result(index=1, delivered="report", verdict="PASS"),
        pass_result(index=2, delivered="none", verdict=None),
    ]

    text = ac.render(
        results,
        "UNVERIFIED",
        "no_report:p2",
        feature="feature",
        size_status="verified",
        passes=2,
    )
    line = auditcycle_lines(text)[0]

    assert "delivered=p1:report,p2:none" in line


def test_render_pass_has_no_premise_items() -> None:
    ac = audit_cycle()
    results = [pass_result(index=1), pass_result(index=2)]

    text = ac.render(
        results,
        "PASS",
        None,
        feature="feature",
        size_status="verified",
        passes=2,
    )

    assert "Premise checklist: empty" in text
    assert text.count("Premise checklist:") == 1
    assert len(auditcycle_lines(text)) == 1


def test_render_every_verdict_includes_hmad_marker_once() -> None:
    ac = audit_cycle()

    for verdict, reason, results in [
        ("PASS", None, [pass_result(index=1)]),
        ("FAIL", "findings:p1", [pass_result(index=1, verdict="FAIL", must=1)]),
        ("UNVERIFIED", "no_report:p1", [pass_result(index=1, delivered="none", verdict=None)]),
    ]:
        text = ac.render(
            results,
            verdict,
            reason,
            feature="feature",
            size_status="verified",
            passes=1,
        )
        assert len(auditcycle_lines(text)) == 1
        assert text.count(f"[H-MAD] feature audit-cycle {verdict}") == 1


def test_main_rejects_unknown_phase_without_auditcycle(capsys: pytest.CaptureFixture, tmp_path: Path) -> None:
    ac = audit_cycle()

    rc = ac.main(
        [
            "--feature",
            "feature",
            "--phase",
            "bogus",
            "--project-root",
            str(tmp_path),
            "--passes",
            "1",
        ]
    )
    captured = capsys.readouterr()

    assert rc == 2
    assert "AUDITCYCLE:" not in captured.out


def test_main_rejects_non_positive_pass_count_without_auditcycle(
    capsys: pytest.CaptureFixture, tmp_path: Path
) -> None:
    ac = audit_cycle()

    for bad_passes in ("0", "-1"):
        rc = ac.main(
            [
                "--feature",
                "feature",
                "--phase",
                "plan",
                "--project-root",
                str(tmp_path),
                "--passes",
                bad_passes,
            ]
        )
        captured = capsys.readouterr()
        assert rc == 2
        assert "AUDITCYCLE:" not in captured.out


def test_main_rejects_pass_flag_until_task4(
    capsys: pytest.CaptureFixture, tmp_path: Path
) -> None:
    ac = audit_cycle()

    rc = ac.main(
        [
            "--feature",
            "feature",
            "--phase",
            "plan",
            "--project-root",
            str(tmp_path),
            "--passes",
            "2",
            "--pass",
            "1:/nonexistent/a.md:/nonexistent/a.out:0",
        ]
    )
    captured = capsys.readouterr()

    assert rc == 2
    assert "unrecognized arguments: --pass" in captured.err
    assert auditcycle_lines(captured.out) == []


def test_main_without_mode_is_operational_error(
    capsys: pytest.CaptureFixture, tmp_path: Path
) -> None:
    ac = audit_cycle()

    rc = ac.main(
        [
            "--feature",
            "feature",
            "--phase",
            "plan",
            "--project-root",
            str(tmp_path),
            "--passes",
            "2",
        ]
    )
    captured = capsys.readouterr()

    assert rc == 2
    assert "ERROR:" in captured.err
    assert auditcycle_lines(captured.out) == []


def test_main_no_pass_halt_reason_renders_unverified_and_exits_zero(
    capsys: pytest.CaptureFixture, tmp_path: Path
) -> None:
    ac = audit_cycle()

    rc = ac.main(
        [
            "--feature",
            "feature",
            "--phase",
            "plan",
            "--project-root",
            str(tmp_path),
            "--passes",
            "2",
            "--size-status",
            "verified",
            "--halt-reason",
            "assemble_halt:p2",
        ]
    )
    captured = capsys.readouterr()

    assert rc == 0
    assert auditcycle_lines(captured.out) == [
        "AUDITCYCLE: UNVERIFIED reason=assemble_halt:p2 passes=2 size_status=verified"
    ]
    assert "delivered=" not in captured.out
    assert "[H-MAD] feature audit-cycle UNVERIFIED" in captured.out


def test_main_no_pass_prompt_divergence_renders_single_auditcycle_line(
    capsys: pytest.CaptureFixture, tmp_path: Path
) -> None:
    ac = audit_cycle()

    rc = ac.main(
        [
            "--feature",
            "feature",
            "--phase",
            "design",
            "--project-root",
            str(tmp_path),
            "--passes",
            "3",
            "--size-status",
            "warning",
            "--halt-reason",
            "prompt_divergence:p1",
        ]
    )
    captured = capsys.readouterr()

    assert rc == 0
    assert auditcycle_lines(captured.out) == [
        "AUDITCYCLE: UNVERIFIED reason=prompt_divergence:p1 passes=3 size_status=warning"
    ]
    assert captured.out.count("AUDITCYCLE:") == 1
    assert "[H-MAD] feature audit-cycle UNVERIFIED" in captured.out
