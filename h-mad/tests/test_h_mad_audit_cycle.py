import importlib
import json
import re
import subprocess
import sys
import threading
import textwrap
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "h-mad" / "scripts"
REAL_AUDIT_REPORTS = tuple(
    sorted(
        [
            *REPO_ROOT.glob("docs/01-plan/features/*.audit.v*.p*.md"),
            *REPO_ROOT.glob("docs/02-design/features/*.audit.v*.p*.md"),
            # Phase 7 moves every feature's artifacts under docs/archive/<YYYY-MM>/,
            # so a live-only corpus is guaranteed to empty out at close-out -- and an
            # empty parametrize SKIPS rather than fails. Reach the archive too.
            *REPO_ROOT.glob("docs/archive/*/*/*.audit.v*.p*.md"),
        ]
    )[:8]
)


def audit_cycle():
    sys.path.insert(0, str(SCRIPT_DIR))
    return importlib.import_module("h_mad_audit_cycle")


def pass_result(
    *,
    index: int,
    delivered: str = "report-file",
    verdict: str | None = "PASS",
    must: int = 0,
    should: int = 0,
    findings: list[dict] | None = None,
    effort: dict | None = None,
    rc: int = 0,
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
        effort=effort,
        rc=rc,
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

HOSTILE_PASS_REPORT = """# Audit body with hostile reviewer payload

## Must-fix
None

## Should-fix
None

## Notes
human-origin text: {{INLINE_MARKER}} [link](target) **bold**
second line with AUDITCYCLE: fake marker
"""

HOSTILE_FAIL_REPORT = """# Audit body with hostile reviewer payload

## Must-fix
- blocking human finding with {{INLINE_MARKER}} [link](target) **bold**

## Should-fix
None

## Notes
second line with AUDITCYCLE: fake marker
"""


def write_done_report(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    Path(str(path) + ".done").touch()


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


def install_extract_report_stub(
    script_dir: Path,
    *,
    return_code: int = 0,
    stdout_text: str = HOSTILE_REPORT,
) -> Path:
    calls_path = script_dir / "extract_report_calls.jsonl"
    stub_path = script_dir / "h_mad_extract_report.py"
    stub_path.write_text(
        textwrap.dedent(
            f"""\
            #!/usr/bin/env python3
            import json
            import sys
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
                sys.stdout.write({stdout_text!r})
            else:
                sys.stderr.write("extract stub failure\\n")
            sys.exit(rc)
            """
        ),
        encoding="utf-8",
    )
    return calls_path


def extract_report_calls(calls_path: Path) -> list[list[str]]:
    if not calls_path.exists():
        return []
    return [json.loads(line) for line in calls_path.read_text(encoding="utf-8").splitlines()]


def install_audit_gate_stub(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    verdicts: dict[str, tuple[str, int, int]],
    *,
    existing_script_dir: Path | None = None,
) -> Path:
    script_dir = existing_script_dir or tmp_path / "gate-stubs"
    script_dir.mkdir(exist_ok=True)
    calls_path = script_dir / "audit_gate_calls.jsonl"
    stub_path = script_dir / "h_mad_audit_gate.py"
    stub_path.write_text(
        textwrap.dedent(
            f"""\
            #!/usr/bin/env python3
            import json
            import sys
            from pathlib import Path

            calls_path = Path({str(calls_path)!r})
            calls_path.write_text(
                calls_path.read_text(encoding="utf-8") + json.dumps(sys.argv[1:]) + "\\n"
                if calls_path.exists()
                else json.dumps(sys.argv[1:]) + "\\n",
                encoding="utf-8",
            )
            verdicts = {verdicts!r}
            audit_file = Path(sys.argv[1])
            verdict, must, should = verdicts[audit_file.name]
            print(f"GATE: {{verdict}} must={{must}} should={{should}}")
            print(f"[H-MAD] {{audit_file.stem}} gate {{verdict}}")
            sys.exit(2 if verdict == "INVALID" else 0)
            """
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("HMAD_AUDIT_CYCLE_SCRIPT_DIR", str(script_dir))
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    return calls_path


def audit_gate_calls(calls_path: Path) -> list[list[str]]:
    if not calls_path.exists():
        return []
    return [json.loads(line) for line in calls_path.read_text(encoding="utf-8").splitlines()]


def pass_arg(index: int, report_path: Path, rc: int = 0) -> str:
    return f"{index}:{report_path}:{report_path.with_suffix('.out')}:{rc}"


def run_collect_cycle(
    ac,
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
    report_paths: list[Path],
    cycle: int = 1,
    extra_args: list[str] | None = None,
) -> tuple[int, str, str]:
    argv = [
        "--feature",
        "hostile-feature",
        "--phase",
        "plan",
        "--cycle",
        str(cycle),
        "--project-root",
        str(tmp_path),
        "--passes",
        str(len(report_paths)),
        "--size-status",
        "verified",
        "--grace",
        "0.2",
    ]
    for index, report_path in enumerate(report_paths, start=1):
        argv.extend(["--pass", pass_arg(index, report_path)])
    if extra_args:
        argv.extend(extra_args)

    rc = ac.main(argv)
    captured = capsys.readouterr()
    return rc, captured.out, captured.err


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
    assert report_wait_calls(calls_path) == [[str(report_path), "--timeout", "3"]]


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
    assert report_wait_calls(calls_path) == [[str(report_path), "--timeout", "1"]]


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
    assert report_wait_calls(calls_path) == [[str(report_path), "--timeout", "1"]]


def test_collect_real_report_wait_accepts_float_grace_timeout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ac = audit_cycle()
    monkeypatch.delenv("HMAD_AUDIT_CYCLE_SCRIPT_DIR", raising=False)
    monkeypatch.setenv("HMAD_REPORT_POLL_INTERVAL", "0")
    report_path = tmp_path / "dispatch" / "never.report.md"
    report_path.parent.mkdir()

    delivered, collected_path = ac.collect(
        pass_spec(1, report_path),
        grace=0.2,
        project_root=tmp_path,
        feature="hostile-feature",
        phase="plan",
        cycle=1,
    )

    assert (delivered, collected_path) == ("none", None)


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

    assert report_wait_calls(calls_path) == [[str(report_path), "--timeout", "1"]]


def test_collect_falls_back_to_out(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ac = audit_cycle()
    wait_calls_path = install_report_wait_stub(monkeypatch, tmp_path, return_code=1)
    extract_calls_path = install_extract_report_stub(wait_calls_path.parent)
    report_path = tmp_path / "dispatch" / "p3.report.md"
    report_path.parent.mkdir()
    out_path = report_path.with_suffix(".out")
    out_path.write_text(
        "\n".join(
            [
                "echoed prompt text",
                "===HMAD-DISPATCH-BOUNDARY===",
                "AUDIT-hostile-feature-design-v8-BEGIN",
                HOSTILE_REPORT,
                "AUDIT-hostile-feature-design-v8-END",
            ]
        ),
        encoding="utf-8",
    )

    delivered, collected_path = ac.collect(
        pass_spec(3, report_path),
        grace=0.2,
        project_root=tmp_path,
        feature="hostile-feature",
        phase="design",
        cycle=8,
    )

    expected_path = tmp_path / "docs/02-design/features/hostile-feature.design.audit.v8.p3.md"
    assert delivered == "out"
    assert collected_path == expected_path
    assert collected_path is not None
    assert collected_path.exists()
    assert collected_path.stat().st_size > 0
    assert collected_path.read_text(encoding="utf-8") == HOSTILE_REPORT
    assert report_wait_calls(wait_calls_path) == [[str(report_path), "--timeout", "1"]]
    assert extract_report_calls(extract_calls_path) == [
        [
            str(out_path),
            "--feature",
            "hostile-feature",
            "--phase",
            "design",
            "--cycle",
            "8",
            "--after-marker",
        ]
    ]


def test_collect_none(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ac = audit_cycle()
    wait_calls_path = install_report_wait_stub(monkeypatch, tmp_path, return_code=1)
    extract_calls_path = install_extract_report_stub(wait_calls_path.parent, return_code=2)
    report_path = tmp_path / "dispatch" / "p4.report.md"
    report_path.parent.mkdir()

    delivered, collected_path = ac.collect(
        pass_spec(4, report_path),
        grace=0.2,
        project_root=tmp_path,
        feature="hostile-feature",
        phase="impl-plan",
        cycle=9,
    )

    assert delivered == "none"
    assert collected_path is None
    assert report_wait_calls(wait_calls_path) == [[str(report_path), "--timeout", "1"]]
    assert extract_report_calls(extract_calls_path) == [
        [
            str(report_path.with_suffix(".out")),
            "--feature",
            "hostile-feature",
            "--phase",
            "impl-plan",
            "--cycle",
            "9",
            "--after-marker",
        ]
    ]


def test_collect_extract_report_operational_error_on_unexpected_nonzero(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ac = audit_cycle()
    wait_calls_path = install_report_wait_stub(monkeypatch, tmp_path, return_code=1)
    extract_calls_path = install_extract_report_stub(wait_calls_path.parent, return_code=5)
    report_path = tmp_path / "dispatch" / "p5.report.md"
    report_path.parent.mkdir()

    with pytest.raises(ac.OperationalError, match="extract_report.*p5"):
        ac.collect(
            pass_spec(5, report_path),
            grace=0.2,
            project_root=tmp_path,
            feature="hostile-feature",
            phase="plan",
            cycle=10,
        )

    assert report_wait_calls(wait_calls_path) == [[str(report_path), "--timeout", "1"]]
    assert extract_report_calls(extract_calls_path) == [
        [
            str(report_path.with_suffix(".out")),
            "--feature",
            "hostile-feature",
            "--phase",
            "plan",
            "--cycle",
            "10",
            "--after-marker",
        ]
    ]


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
    assert ac.combine([pass_result(index=1, delivered="report-file", verdict="INVALID")]) == (
        "UNVERIFIED",
        "no_gate_sections:p1",
    )


def test_combine_raises_when_delivered_pass_has_no_gate_token() -> None:
    ac = audit_cycle()

    with pytest.raises(ac.OperationalError, match="GATE.*p1"):
        ac.combine([pass_result(index=1, delivered="report-file", verdict=None)])


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


def test_render_post_dispatch_unverified_all_none_includes_delivered_for_every_pass() -> None:
    ac = audit_cycle()
    results = [
        pass_result(index=1, delivered="none", verdict=None),
        pass_result(index=2, delivered="none", verdict=None),
    ]

    text = ac.render(
        results,
        "UNVERIFIED",
        "no_report:p1",
        feature="hostile-feature",
        size_status="verified",
        passes=2,
    )
    line = auditcycle_lines(text)[0]

    assert (
        line
        == "AUDITCYCLE: UNVERIFIED reason=no_report:p1 passes=2 delivered=none,none size_status=verified"
    )
    assert not re.search(r"\b(?:must|should|p\d+)=", line)


def test_render_pre_dispatch_unverified_omits_delivered() -> None:
    ac = audit_cycle()

    text = ac.render(
        [],
        "UNVERIFIED",
        "assemble_halt:p2",
        feature="hostile-feature",
        size_status="verified",
        passes=2,
    )
    line = auditcycle_lines(text)[0]

    assert line == "AUDITCYCLE: UNVERIFIED reason=assemble_halt:p2 passes=2 size_status=verified"
    assert "delivered=" not in line
    assert not re.search(r"\b(?:must|should|p\d+)=", line)


def test_render_unverified_omits_premise_checklist() -> None:
    ac = audit_cycle()
    results = [
        pass_result(
            index=1,
            delivered="report-file",
            verdict="FAIL",
            must=1,
            findings=[
                {
                    "severity": "must",
                    "text": "A bulleted finding",
                    "path": None,
                    "line": None,
                }
            ],
        ),
        pass_result(index=2, delivered="none", verdict=None),
    ]

    text = ac.render(
        results,
        "UNVERIFIED",
        "no_report:p2",
        feature="hostile-feature",
        size_status="verified",
        passes=2,
    )

    assert "Premise checklist" not in text
    assert "reports:" not in text
    assert "note:" not in text


def test_render_post_dispatch_unverified_includes_delivered_for_every_pass() -> None:
    ac = audit_cycle()
    results = [
        pass_result(index=1, delivered="report-file", verdict="PASS"),
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

    assert (
        line
        == "AUDITCYCLE: UNVERIFIED reason=no_report:p2 passes=2 delivered=report-file,none size_status=verified"
    )
    assert not re.search(r"\b(?:must|should|p\d+)=", line)


def test_render_pass_verdict_line_matches_ac_8_1() -> None:
    ac = audit_cycle()
    results = [
        pass_result(index=1, delivered="report-file", verdict="PASS", must=0, should=0),
        pass_result(index=2, delivered="report-file", verdict="PASS", must=0, should=0),
    ]

    text = ac.render(
        results,
        "PASS",
        None,
        feature="feature",
        size_status="verified",
        passes=2,
    )
    line = auditcycle_lines(text)[0]

    assert line == (
        "AUDITCYCLE: PASS must=0 should=0 passes=2 p1=0/0 p2=0/0 "
        "delivered=report-file,report-file size_status=verified"
    )
    assert "reason=" not in line


def test_render_fail_verdict_line_matches_ac_8_1() -> None:
    ac = audit_cycle()
    results = [
        pass_result(index=1, delivered="report-file", verdict="FAIL", must=2, should=0),
        pass_result(index=2, delivered="out", verdict="FAIL", must=2, should=1),
    ]

    text = ac.render(
        results,
        "FAIL",
        "findings:p1",
        feature="feature",
        size_status="verified",
        passes=2,
    )
    line = auditcycle_lines(text)[0]

    assert line == (
        "AUDITCYCLE: FAIL must=4 should=1 passes=2 p1=2/0 p2=2/1 "
        "delivered=report-file,out size_status=verified"
    )
    assert "reason=" not in line


def test_render_unverified_verdict_line_matches_ac_8_1() -> None:
    ac = audit_cycle()
    results = [
        pass_result(index=1, delivered="report-file", verdict="PASS", must=0, should=0),
        pass_result(index=2, delivered="none", verdict=None, must=0, should=0),
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

    assert line == (
        "AUDITCYCLE: UNVERIFIED reason=no_report:p2 passes=2 "
        "delivered=report-file,none size_status=verified"
    )
    assert not re.search(r"\b(?:must|should|p\d+)=", line)


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
            "--cycle",
            "1",
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
                "--cycle",
                "1",
                "--project-root",
                str(tmp_path),
                "--passes",
                bad_passes,
            ]
        )
        captured = capsys.readouterr()
        assert rc == 2
        assert "AUDITCYCLE:" not in captured.out


def test_main_requires_cycle(capsys: pytest.CaptureFixture, tmp_path: Path) -> None:
    ac = audit_cycle()
    report_path = tmp_path / "dispatch" / "p1.report.md"
    write_done_report(report_path, HOSTILE_PASS_REPORT)

    rc = ac.main(
        [
            "--feature",
            "feature",
            "--phase",
            "plan",
            "--project-root",
            str(tmp_path),
            "--passes",
            "1",
            "--pass",
            pass_arg(1, report_path),
        ]
    )
    captured = capsys.readouterr()

    assert rc == 2
    assert "AUDITCYCLE:" not in captured.out


def test_main_cycle_reaches_collected_path(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
    tmp_path: Path,
) -> None:
    ac = audit_cycle()
    report_path = tmp_path / "dispatch" / "p1.report.md"
    write_done_report(report_path, HOSTILE_PASS_REPORT)
    collected = tmp_path / "docs/01-plan/features/hostile-feature.plan.audit.v3.p1.md"
    install_audit_gate_stub(
        monkeypatch,
        tmp_path,
        {"hostile-feature.plan.audit.v3.p1.md": ("PASS", 0, 0)},
    )

    rc, stdout, stderr = run_collect_cycle(
        ac,
        tmp_path=tmp_path,
        capsys=capsys,
        report_paths=[report_path],
        cycle=3,
    )

    assert rc == 0
    assert stderr == ""
    assert collected.exists()
    assert not (
        tmp_path / "docs/01-plan/features/hostile-feature.plan.audit.v1.p1.md"
    ).exists()
    assert str(collected) in stdout


def test_main_pass_flag_drives_collect_and_gate(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture, tmp_path: Path
) -> None:
    ac = audit_cycle()
    p1 = tmp_path / "dispatch" / "p1.report.md"
    p2 = tmp_path / "dispatch" / "p2.report.md"
    write_done_report(p1, HOSTILE_PASS_REPORT)
    write_done_report(p2, HOSTILE_PASS_REPORT)
    calls_path = install_audit_gate_stub(
        monkeypatch,
        tmp_path,
        {
            "hostile-feature.plan.audit.v1.p1.md": ("PASS", 0, 0),
            "hostile-feature.plan.audit.v1.p2.md": ("PASS", 0, 0),
        },
    )

    rc, stdout, stderr = run_collect_cycle(
        ac, tmp_path=tmp_path, capsys=capsys, report_paths=[p1, p2]
    )
    collected = [
        tmp_path / "docs/01-plan/features/hostile-feature.plan.audit.v1.p1.md",
        tmp_path / "docs/01-plan/features/hostile-feature.plan.audit.v1.p2.md",
    ]

    assert rc == 0, "--pass must be accepted and drive collect-and-gate"
    assert stderr == ""
    line = auditcycle_lines(stdout)[0]
    assert line.startswith("AUDITCYCLE: PASS")
    assert "must=0" in line
    assert "should=0" in line
    assert "p1=0/0" in line
    assert "p2=0/0" in line
    assert "reports: " + " ".join(str(path) for path in collected) in stdout
    assert (
        "note: must=/should= are sums across passes and may double-count a finding both passes reported"
        in stdout
    )
    assert audit_gate_calls(calls_path) == [[str(collected[0])], [str(collected[1])]]


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
            "--cycle",
            "1",
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
            "--cycle",
            "1",
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
            "--cycle",
            "1",
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


def test_fail_in_either_pass_fails_cycle(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
    tmp_path: Path,
) -> None:
    ac = audit_cycle()

    for failing_index in (1, 2):
        case_dir = tmp_path / f"case-{failing_index}"
        p1 = case_dir / "dispatch" / "p1.report.md"
        p2 = case_dir / "dispatch" / "p2.report.md"
        write_done_report(p1, HOSTILE_FAIL_REPORT if failing_index == 1 else HOSTILE_PASS_REPORT)
        write_done_report(p2, HOSTILE_FAIL_REPORT if failing_index == 2 else HOSTILE_PASS_REPORT)
        calls_path = install_audit_gate_stub(
            monkeypatch,
            case_dir,
            {
                "hostile-feature.plan.audit.v1.p1.md": (
                    "FAIL" if failing_index == 1 else "PASS",
                    1 if failing_index == 1 else 0,
                    0,
                ),
                "hostile-feature.plan.audit.v1.p2.md": (
                    "FAIL" if failing_index == 2 else "PASS",
                    1 if failing_index == 2 else 0,
                    0,
                ),
            },
        )

        rc, stdout, stderr = run_collect_cycle(
            ac, tmp_path=case_dir, capsys=capsys, report_paths=[p1, p2]
        )
        collected = [
            case_dir / "docs/01-plan/features/hostile-feature.plan.audit.v1.p1.md",
            case_dir / "docs/01-plan/features/hostile-feature.plan.audit.v1.p2.md",
        ]

        assert audit_gate_calls(calls_path) == [
            [str(collected[0])],
            [str(collected[1])],
        ], f"p{failing_index} FAIL case must invoke the gate once per collected pass"
        assert rc == 0, f"p{failing_index} FAIL must make the audit cycle fail"
        assert stderr == ""
        line = auditcycle_lines(stdout)[0]
        assert line.startswith("AUDITCYCLE: FAIL")
        assert "must=1" in line
        assert "should=0" in line
        assert "p1=" in line and "p2=" in line
        assert "reports: " + " ".join(str(path) for path in collected) in stdout
        assert (
            "note: must=/should= are sums across passes and may double-count a finding both passes reported"
            in stdout
        )


def test_main_delivered_none_is_unverified(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
    tmp_path: Path,
) -> None:
    ac = audit_cycle()
    p1 = tmp_path / "dispatch" / "p1.report.md"
    p2 = tmp_path / "dispatch" / "p2.report.md"
    write_done_report(p1, HOSTILE_PASS_REPORT)
    calls_path = install_report_wait_stub(monkeypatch, tmp_path, return_code=1)
    install_audit_gate_stub(
        monkeypatch,
        tmp_path,
        {"hostile-feature.plan.audit.v1.p1.md": ("PASS", 0, 0)},
        existing_script_dir=calls_path.parent,
    )

    rc, stdout, stderr = run_collect_cycle(
        ac, tmp_path=tmp_path, capsys=capsys, report_paths=[p1, p2]
    )

    assert rc == 0, "delivered=none must yield UNVERIFIED instead of gating a missing report"
    assert stderr == ""
    assert auditcycle_lines(stdout) == [
        "AUDITCYCLE: UNVERIFIED reason=no_report:p2 passes=2 delivered=report-file,none size_status=verified"
    ]
    assert "reports:" not in stdout
    assert "note: must=/should=" not in stdout
    assert report_wait_calls(calls_path) == [[str(p2), "--timeout", "1"]]


@pytest.mark.parametrize(
    ("name", "body"),
    [
        (
            "missing_both",
            "# hostile malformed report\nhuman text with {{INLINE_MARKER}} and **markdown**\n",
        ),
        (
            "missing_must",
            "# hostile malformed report\n## Should-fix\n- should-only finding\n",
        ),
        (
            "missing_should",
            "# hostile malformed report\n## Must-fix\n- must one\n- must two\n",
        ),
    ],
)
def test_main_invalid_yields_unverified(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
    tmp_path: Path,
    name: str,
    body: str,
) -> None:
    ac = audit_cycle()
    p1 = tmp_path / name / "dispatch" / "p1.report.md"
    p2 = tmp_path / name / "dispatch" / "p2.report.md"
    write_done_report(p1, body)
    write_done_report(p2, HOSTILE_PASS_REPORT)
    install_audit_gate_stub(
        monkeypatch,
        tmp_path / name,
        {
            "hostile-feature.plan.audit.v1.p1.md": ("INVALID", 99, 77),
            "hostile-feature.plan.audit.v1.p2.md": ("PASS", 0, 0),
        },
    )

    rc, stdout, stderr = run_collect_cycle(
        ac, tmp_path=tmp_path / name, capsys=capsys, report_paths=[p1, p2]
    )

    assert rc == 0, f"{name} INVALID must short-circuit to UNVERIFIED without crashing"
    assert stderr == ""
    assert auditcycle_lines(stdout) == [
        "AUDITCYCLE: UNVERIFIED reason=no_gate_sections:p1 passes=2 delivered=report-file,report-file size_status=verified"
    ]
    assert "reports:" not in stdout
    assert "note: must=/should=" not in stdout


def test_gate_invalid_discards_counts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ac = audit_cycle()
    report = tmp_path / "hostile-feature.plan.audit.v1.p1.md"
    report.write_text("## Must-fix\n- counted in-process\n## Notes\nhostile {{INLINE}}\n", encoding="utf-8")
    install_audit_gate_stub(
        monkeypatch,
        tmp_path,
        {"hostile-feature.plan.audit.v1.p1.md": ("INVALID", 99, 77)},
    )

    gate = getattr(ac, "gate", None)
    assert callable(gate), "gate() must exist to discard INVALID subprocess counts"

    assert gate(report, ack_file=None) == ("INVALID", 0, 0, [])


def test_gate_nonzero_exit_is_operational_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A crashing audit_gate that still prints a GATE line must not be scored.

    Axis B, audit-gate signal discipline: the exit code answers "did the script run
    at all" and the token answers "what did it decide", and BOTH are read for every
    composed call. gate() read only the token, so a non-zero exit carrying a
    well-formed GATE line was accepted as a verdict.
    """
    ac = audit_cycle()
    body = "## Must-fix\nNone\n\n## Should-fix\nNone\n"
    collected = tmp_path / "docs/01-plan/features/hostile-feature.plan.audit.v1.p1.md"
    collected.parent.mkdir(parents=True)
    collected.write_text(body, encoding="utf-8")

    script_dir = tmp_path / "gate-stubs"
    script_dir.mkdir(exist_ok=True)
    (script_dir / "h_mad_audit_gate.py").write_text(
        "import sys\nprint('GATE: PASS must=0 should=0')\nsys.exit(4)\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HMAD_AUDIT_CYCLE_SCRIPT_DIR", str(script_dir))

    with pytest.raises(ac.OperationalError, match="audit_gate exited 4"):
        ac.gate(collected, ack_file=None)


def test_gate_invalid_exits_two_and_is_still_a_verdict(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """rc=2 is a VERDICT here, not a crash — narrowing the guard to `!= 0` breaks it.

    `h_mad_audit_gate.py` prints `GATE: INVALID` and returns 2 deliberately, so that
    "no report" can never read as "no findings". That is the one non-zero exit which
    legitimately carries a token, and gate() must keep routing it to the INVALID
    branch (which combine() maps to UNVERIFIED no_gate_sections). This test exists so
    that tightening the exit-code guard turns red instead of silently converting a
    correct UNVERIFIED into an operational error.
    """
    ac = audit_cycle()
    collected = tmp_path / "docs/01-plan/features/hostile-feature.plan.audit.v1.p1.md"
    collected.parent.mkdir(parents=True)
    collected.write_text("# Audit\n\nprose only, no gate sections\n", encoding="utf-8")

    script_dir = tmp_path / "gate-stubs"
    script_dir.mkdir(exist_ok=True)
    (script_dir / "h_mad_audit_gate.py").write_text(
        "import sys\nprint('GATE: INVALID must=0 should=0')\nsys.exit(2)\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HMAD_AUDIT_CYCLE_SCRIPT_DIR", str(script_dir))

    assert ac.gate(collected, ack_file=None) == ("INVALID", 0, 0, [])


def test_gate_count_mismatch_is_operational_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
    tmp_path: Path,
) -> None:
    ac = audit_cycle()
    report = tmp_path / "dispatch" / "p1.report.md"
    body = "## Must-fix\n- one live must-fix finding\n\n## Should-fix\nNone\n"
    write_done_report(report, body)
    collected = tmp_path / "docs/01-plan/features/hostile-feature.plan.audit.v1.p1.md"
    collected.parent.mkdir(parents=True)
    collected.write_text(body, encoding="utf-8")
    install_audit_gate_stub(
        monkeypatch,
        tmp_path,
        {"hostile-feature.plan.audit.v1.p1.md": ("FAIL", 2, 0)},
    )

    with pytest.raises(ac.OperationalError, match="gate count mismatch"):
        ac.gate(collected, ack_file=None)

    rc, stdout, stderr = run_collect_cycle(
        ac, tmp_path=tmp_path, capsys=capsys, report_paths=[report]
    )

    assert rc == 4
    assert "gate count mismatch" in stderr
    assert auditcycle_lines(stdout) == []


def test_collected_write_failure_is_operational_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ac = audit_cycle()
    report = tmp_path / "dispatch" / "p1.report.md"
    write_done_report(report, HOSTILE_PASS_REPORT)
    collected = tmp_path / "docs/01-plan/features/hostile-feature.plan.audit.v3.p1.md"
    collected.parent.mkdir(parents=True)
    collected.write_text("STALE REPORT from the previous run", encoding="utf-8")

    monkeypatch.setattr(Path, "write_bytes", lambda self, data: 0)
    monkeypatch.setattr(Path, "write_text", lambda self, data, *args, **kwargs: 0)

    with pytest.raises(ac.OperationalError, match="collected report was empty after copy"):
        ac.collect(
            pass_spec(1, report),
            grace=0.2,
            project_root=tmp_path,
            feature="hostile-feature",
            phase="plan",
            cycle=3,
        )


def test_ack_file_forwarded(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
    tmp_path: Path,
) -> None:
    ac = audit_cycle()
    p1 = tmp_path / "dispatch" / "p1.report.md"
    p2 = tmp_path / "dispatch" / "p2.report.md"
    write_done_report(p1, HOSTILE_PASS_REPORT)
    write_done_report(
        p2,
        HOSTILE_FAIL_REPORT.replace(
            "blocking human finding with {{INLINE_MARKER}} [link](target) **bold**",
            "acknowledged hostile finding with {{INLINE_MARKER}} [link](target) **bold**",
        ),
    )
    ack_file = tmp_path / "ack.md"
    ack_file.write_text(
        "- acknowledged hostile finding with {{INLINE_MARKER}} [link](target) **bold**\n",
        encoding="utf-8",
    )
    calls_path = install_audit_gate_stub(
        monkeypatch,
        tmp_path,
        {
            "hostile-feature.plan.audit.v1.p1.md": ("PASS", 0, 0),
            "hostile-feature.plan.audit.v1.p2.md": ("PASS", 0, 0),
        },
    )

    rc, stdout, stderr = run_collect_cycle(
        ac,
        tmp_path=tmp_path,
        capsys=capsys,
        report_paths=[p1, p2],
        extra_args=["--ack-file", str(ack_file)],
    )
    collected = [
        tmp_path / "docs/01-plan/features/hostile-feature.plan.audit.v1.p1.md",
        tmp_path / "docs/01-plan/features/hostile-feature.plan.audit.v1.p2.md",
    ]

    assert rc == 0, "ack-file-cleared p2 finding must allow cycle PASS"
    assert stderr == ""
    assert auditcycle_lines(stdout)[0].startswith("AUDITCYCLE: PASS")
    assert "must=0" in auditcycle_lines(stdout)[0]
    assert audit_gate_calls(calls_path) == [
        [str(collected[0]), "--ack-file", str(ack_file)],
        [str(collected[1]), "--ack-file", str(ack_file)],
    ]


def run_real_gate(audit_file: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "h_mad_audit_gate.py"), str(audit_file), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def gate_must(stdout: str) -> int:
    match = re.search(r"^GATE: \S+ must=(\d+) should=(\d+)$", stdout, re.MULTILINE)
    assert match, f"real gate output must include a GATE count line, got: {stdout!r}"
    return int(match.group(1))


def test_prose_plus_bullet_not_concatenated(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
    tmp_path: Path,
) -> None:
    ac = audit_cycle()
    monkeypatch.delenv("HMAD_AUDIT_CYCLE_SCRIPT_DIR", raising=False)
    p1 = tmp_path / "dispatch" / "p1.report.md"
    p2 = tmp_path / "dispatch" / "p2.report.md"
    prose_fixture = REPO_ROOT / "h-mad/tests/fixtures/audit-cycle-prose-only.md"
    bullet_fixture = REPO_ROOT / "h-mad/tests/fixtures/audit-cycle-single-bullet.md"
    write_done_report(p1, prose_fixture.read_text(encoding="utf-8"))
    write_done_report(p2, bullet_fixture.read_text(encoding="utf-8"))

    rc, stdout, stderr = run_collect_cycle(
        ac, tmp_path=tmp_path, capsys=capsys, report_paths=[p1, p2]
    )
    concat = tmp_path / "concat.md"
    concat.write_text(
        prose_fixture.read_text(encoding="utf-8")
        + "\n"
        + bullet_fixture.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    concatenated = run_real_gate(concat)

    assert rc == 0, "separate per-pass real gates must complete the cycle"
    assert stderr == ""
    line = auditcycle_lines(stdout)[0]
    assert line.startswith("AUDITCYCLE: FAIL")
    assert "must=2" in line
    assert "p1=1/0" in line
    assert "p2=1/0" in line
    assert concatenated.returncode == 0
    assert gate_must(concatenated.stdout) == 1


def expected_gate_payloads(text: str, acknowledged: set[str]) -> list[str]:
    sys.path.insert(0, str(SCRIPT_DIR))
    from h_mad_audit_gate import _BULLET_MARKERS, _payload

    payloads: list[str] = []
    in_must = False
    must_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "## Must-fix":
            in_must = True
            continue
        if stripped.startswith("## "):
            in_must = False
            continue
        if in_must and stripped:
            must_lines.append(line)

    non_none = [
        _payload(line)
        for line in must_lines
        if _payload(line) and _payload(line).lower() != "none"
    ]
    bullets = [
        _payload(line)
        for line in must_lines
        if any(line.strip().startswith(marker) for marker in _BULLET_MARKERS)
        and _payload(line)
        and _payload(line).lower() != "none"
        and _payload(line) not in acknowledged
    ]
    if bullets:
        return bullets
    joined = " ".join(payload for payload in non_none if payload)
    if joined and joined not in acknowledged:
        return [joined]
    return []


def assert_premise_items_match_gate(
    ac,
    report: Path,
    *,
    ack_file: Path | None,
    expected: list[str],
) -> None:
    real_args = ["--ack-file", str(ack_file)] if ack_file is not None else []
    real = run_real_gate(report, *real_args)
    assert real.returncode == 0
    must = gate_must(real.stdout)

    gate = getattr(ac, "gate", None)
    assert callable(gate), "gate() must expose findings from the same parser the real gate uses"
    verdict, gate_must_count, should, findings = gate(report, ack_file=ack_file)
    payloads = [finding["text"] for finding in findings]

    assert verdict in {"PASS", "FAIL"}
    assert gate_must_count == must
    assert len(payloads) == must
    assert payloads == expected


@pytest.mark.parametrize(
    ("body", "ack_body"),
    [
        (
            "## Must-fix\n- hostile bullet {{INLINE_MARKER}} [link](target)\n## Should-fix\nNone\n",
            "",
        ),
        (
            "## Must-fix\nhostile prose {{INLINE_MARKER}} with **markdown**\n## Should-fix\nNone\n",
            "",
        ),
        (
            "## Must-fix\n• hostile unicode bullet {{INLINE_MARKER}}\n## Should-fix\nNone\n",
            "",
        ),
        (
            "## Must-fix\n- acknowledged hostile bullet {{INLINE_MARKER}}\n- live hostile bullet {{INLINE_MARKER}}\n## Should-fix\nNone\n",
            "- acknowledged hostile bullet {{INLINE_MARKER}}\n",
        ),
    ],
)
def test_premise_items_match_gate_count(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    body: str,
    ack_body: str,
) -> None:
    ac = audit_cycle()
    monkeypatch.delenv("HMAD_AUDIT_CYCLE_SCRIPT_DIR", raising=False)
    report = tmp_path / "hostile-feature.plan.audit.v1.p1.md"
    report.write_text(body, encoding="utf-8")
    ack_file = tmp_path / "ack.md"
    ack_file.write_text(ack_body, encoding="utf-8")
    acknowledged = set()
    if ack_body:
        sys.path.insert(0, str(SCRIPT_DIR))
        from h_mad_audit_gate import _read_ack_file

        acknowledged = _read_ack_file(ack_file)

    assert_premise_items_match_gate(
        ac,
        report,
        ack_file=ack_file,
        expected=expected_gate_payloads(body, acknowledged),
    )


def test_real_audit_report_corpus_is_not_empty() -> None:
    """An empty parametrize SKIPS, and a skip reads as green in a -q suite run.

    `REAL_AUDIT_REPORTS` feeds the Reimplementation-parity check below against real
    collected reports. It used to glob only the LIVE feature directories -- but every
    feature is archived at Phase 7, so that corpus was guaranteed to empty out, and it
    did: archiving this feature took it from 8 files to 0 and turned the parity test
    into `SKIPPED [1] got empty parameter set` without a single failure anywhere.

    This asserts the corpus exists, so the next archive fails loudly instead of
    silently retiring the guard.
    """
    assert REAL_AUDIT_REPORTS, (
        "real-artifact corpus is empty -- the parity test below is silently skipping; "
        "check the globs still reach the archive"
    )


@pytest.mark.parametrize("report", REAL_AUDIT_REPORTS, ids=lambda path: path.name)
def test_premise_items_match_gate_count_real_artifacts(
    monkeypatch: pytest.MonkeyPatch, report: Path
) -> None:
    ac = audit_cycle()
    monkeypatch.delenv("HMAD_AUDIT_CYCLE_SCRIPT_DIR", raising=False)

    assert_premise_items_match_gate(
        ac,
        report,
        ack_file=None,
        expected=expected_gate_payloads(report.read_text(encoding="utf-8"), set()),
    )


# --- J49: a hollow audit pass must be visible at the verdict ------------------
#
# Across the 8 audit passes of cycles 21-24, every substantive finding came from a
# pass with high thinking tokens or ~34 tool calls. Cycle 21 pass A ran 0 tool calls
# and returned "CLEAN PASS" on a plan another pass proved defective; cycle 24
# double-cleaned with thinking collapsed to 6.2k/4.4k and exactly 2 tool calls each
# -- the report write and the `.done` marker, i.e. no reads at all. At the
# AUDITCYCLE line that is indistinguishable from a real clean pass, and the counts
# were only visible by opening the NDJSON by hand.
#
# The effort block reports. It must never decide: `combine()` does not see it, and a
# pass that made 2 tool calls honoured the delivery contract exactly as asked.


def _agy_log(path: Path, *, tools_ok: int, tools_err: int = 0, thinking: int = 0) -> Path:
    lines = [json.dumps({
        "event": "step_update",
        "step_update": {"step_type": "agent_response", "state": "DONE",
                        "usage": {"thinking_tokens": thinking}},
    })]
    for state, count in (("DONE", tools_ok), ("ERROR", tools_err)):
        for _ in range(count):
            lines.append(json.dumps({
                "event": "step_update",
                "step_update": {"step_type": "tool", "tool_name": "view_file",
                                "state": state},
            }))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _effort_lines(text: str) -> list[str]:
    body = text.split("Effort:", 1)
    return [] if len(body) == 1 else [
        line.strip() for line in body[1].splitlines()
        if line.strip().startswith("- ")
    ]


class TestEffortIsSurfaced:
    def test_pass_spec_accepts_an_optional_log_field(self) -> None:
        """Five fields, not four -- every existing caller passing four must keep
        working, or upgrading the combiner silently breaks the verb."""
        ac = audit_cycle()

        four = ac._parse_pass_spec("1:/r.md:/r.out:0")
        five = ac._parse_pass_spec("1:/r.md:/r.out:0:/r.ndjson")

        assert four.log_path is None
        assert five.log_path == Path("/r.ndjson")
        assert four.index == five.index == 1 and four.rc == five.rc == 0

    def test_a_log_path_may_contain_colons(self) -> None:
        """The log field is last precisely so a path with a colon lands whole."""
        spec = audit_cycle()._parse_pass_spec("1:/r.md:/r.out:0:/a:b/run.ndjson")

        assert spec.log_path == Path("/a:b/run.ndjson")

    def test_effort_block_reports_tools_and_thinking(self, tmp_path, capsys) -> None:
        ac = audit_cycle()
        report = tmp_path / "p1.report.md"
        write_done_report(report, "## Summary\nx\n\n## Must-fix\nNone\n\n## Should-fix\nNone\n")
        log = _agy_log(tmp_path / "p1.ndjson", tools_ok=34, thinking=15786)

        argv = ["--feature", "f", "--phase", "plan", "--cycle", "1",
                "--project-root", str(tmp_path), "--passes", "1", "--grace", "0.2",
                "--pass", f"1:{report}:{report.with_suffix('.out')}:0:{log}"]
        rc = ac.main(argv)
        out = capsys.readouterr().out

        assert rc == 0
        assert "Effort:" in out
        line = _effort_lines(out)[0]
        assert "p1" in line and "tools=34" in line and "thinking=15786" in line

    def test_a_pass_at_or_below_the_delivery_floor_is_marked(self, tmp_path, capsys) -> None:
        """The report-file contract itself costs two successful calls: write the
        report, touch the marker. At or below that floor the pass cannot have read
        anything, which is the J49 signature. Derived from the CONTRACT, not from
        tool names -- the evidence scanner knows no tool names on purpose."""
        ac = audit_cycle()
        report = tmp_path / "p1.report.md"
        write_done_report(report, "## Summary\nx\n\n## Must-fix\nNone\n\n## Should-fix\nNone\n")
        log = _agy_log(tmp_path / "p1.ndjson", tools_ok=2, thinking=4429)

        argv = ["--feature", "f", "--phase", "plan", "--cycle", "1",
                "--project-root", str(tmp_path), "--passes", "1", "--grace", "0.2",
                "--pass", f"1:{report}:{report.with_suffix('.out')}:0:{log}"]
        ac.main(argv)
        out = capsys.readouterr().out

        assert "low-evidence" in _effort_lines(out)[0]

    def test_a_pass_above_the_floor_is_not_marked(self, tmp_path, capsys) -> None:
        ac = audit_cycle()
        report = tmp_path / "p1.report.md"
        write_done_report(report, "## Summary\nx\n\n## Must-fix\nNone\n\n## Should-fix\nNone\n")
        log = _agy_log(tmp_path / "p1.ndjson", tools_ok=3, thinking=100)

        argv = ["--feature", "f", "--phase", "plan", "--cycle", "1",
                "--project-root", str(tmp_path), "--passes", "1", "--grace", "0.2",
                "--pass", f"1:{report}:{report.with_suffix('.out')}:0:{log}"]
        ac.main(argv)

        assert "low-evidence" not in _effort_lines(capsys.readouterr().out)[0]

    def test_an_unreadable_log_says_so_and_reports_no_counts(self, tmp_path, capsys) -> None:
        """A zero here would be a measurement of nothing presented as evidence --
        `tools=0` is exactly what a hollow pass looks like, so a log that could not
        be read must never render as one."""
        ac = audit_cycle()
        report = tmp_path / "p1.report.md"
        write_done_report(report, "## Summary\nx\n\n## Must-fix\nNone\n\n## Should-fix\nNone\n")

        argv = ["--feature", "f", "--phase", "plan", "--cycle", "1",
                "--project-root", str(tmp_path), "--passes", "1", "--grace", "0.2",
                "--pass", f"1:{report}:{report.with_suffix('.out')}:0:{tmp_path / 'gone.ndjson'}"]
        rc = ac.main(argv)
        out = capsys.readouterr().out

        assert rc == 0, "an unreadable log is not an operational failure of the cycle"
        line = _effort_lines(out)[0]
        assert "unreadable" in line
        assert "tools=" not in line and "thinking=" not in line
        assert "low-evidence" not in line

    def test_an_empty_log_is_unreadable_not_a_row_of_zeros(self, tmp_path, capsys) -> None:
        """A present-but-empty log is the sharpest form of the trap: the file
        EXISTS, so an existence check passes, and `tools=0 thinking=0` is exactly
        what a genuinely hollow pass looks like. Assert existence and CONTENT as
        two columns — a dispatch that never wrote its log must not be rendered as
        one that read nothing."""
        ac = audit_cycle()
        report = tmp_path / "p1.report.md"
        write_done_report(report, "## Summary\nx\n\n## Must-fix\nNone\n\n## Should-fix\nNone\n")
        empty = tmp_path / "p1.ndjson"
        empty.write_text("   \n\n", encoding="utf-8")

        ac.main(["--feature", "f", "--phase", "plan", "--cycle", "1",
                 "--project-root", str(tmp_path), "--passes", "1", "--grace", "0.2",
                 "--pass", f"1:{report}:{report.with_suffix('.out')}:0:{empty}"])
        line = _effort_lines(capsys.readouterr().out)[0]

        assert "unreadable" in line
        assert "tools=" not in line and "thinking=" not in line
        assert "low-evidence" not in line

    def test_no_effort_block_when_no_pass_carries_a_log(self, tmp_path, capsys) -> None:
        """Four-field callers must render exactly as before -- an empty Effort block
        would read as 'measured, found nothing'."""
        ac = audit_cycle()
        report = tmp_path / "p1.report.md"
        write_done_report(report, "## Summary\nx\n\n## Must-fix\nNone\n\n## Should-fix\nNone\n")

        argv = ["--feature", "f", "--phase", "plan", "--cycle", "1",
                "--project-root", str(tmp_path), "--passes", "1", "--grace", "0.2",
                "--pass", f"1:{report}:{report.with_suffix('.out')}:0"]
        ac.main(argv)

        assert "Effort:" not in capsys.readouterr().out

    def test_effort_never_changes_the_verdict(self, tmp_path, capsys) -> None:
        """J49 is a scoring caveat, not a defect. The same clean report must produce
        the same AUDITCYCLE line whether the pass was hollow or exhaustive."""
        ac = audit_cycle()
        body = "## Summary\nx\n\n## Must-fix\nNone\n\n## Should-fix\nNone\n"
        verdicts = []
        for name, tools, think in (("hollow", 0, 0), ("deep", 34, 20_000)):
            report = tmp_path / f"{name}.report.md"
            write_done_report(report, body)
            log = _agy_log(tmp_path / f"{name}.ndjson", tools_ok=tools, thinking=think)
            ac.main(["--feature", "f", "--phase", "plan", "--cycle", "1",
                     "--project-root", str(tmp_path), "--passes", "1", "--grace", "0.2",
                     "--pass", f"1:{report}:{report.with_suffix('.out')}:0:{log}"])
            verdicts.append(auditcycle_lines(capsys.readouterr().out)[0])

        assert verdicts[0] == verdicts[1], "effort leaked into the machine verdict"

    def test_the_contract_line_is_unchanged_by_effort(self, tmp_path, capsys) -> None:
        """The AUDITCYCLE line is a machine contract. Effort belongs in the human
        block beside it, not inside a token consumers parse positionally."""
        ac = audit_cycle()
        report = tmp_path / "p1.report.md"
        write_done_report(report, "## Summary\nx\n\n## Must-fix\nNone\n\n## Should-fix\nNone\n")
        log = _agy_log(tmp_path / "p1.ndjson", tools_ok=0, thinking=0)

        ac.main(["--feature", "f", "--phase", "plan", "--cycle", "1",
                 "--project-root", str(tmp_path), "--passes", "1", "--grace", "0.2",
                 "--pass", f"1:{report}:{report.with_suffix('.out')}:0:{log}"])
        line = auditcycle_lines(capsys.readouterr().out)[0]

        assert "tools=" not in line
        assert "thinking=" not in line
        assert "low-evidence" not in line


# --- dispatch rc is part of the verdict -------------------------------------
#
# The pass rc travelled from `hmad-dispatch audit-cycle` into PassSpec and was
# then read by nobody, so a leg killed at `--timeout` (rc 124) that had already
# written a GATE line scored a clean PASS. Observed live on cycle 27 of
# manuscript-model-provenance: `EMPTY final message`, 0 tools, verdict PASS.


def test_timed_out_pass_cannot_certify_a_clean_cycle():
    ac = audit_cycle()
    verdict, reason = ac.combine([
        pass_result(index=1),
        pass_result(index=2, rc=124),
    ])
    assert verdict == "UNVERIFIED"
    assert reason == "dispatch_timeout:p2"


def test_nonzero_rc_that_is_not_a_timeout_is_named_by_its_code():
    ac = audit_cycle()
    verdict, reason = ac.combine([pass_result(index=1, rc=3)])
    assert verdict == "UNVERIFIED"
    assert reason == "dispatch_rc3:p1"


def test_clean_dispatch_still_passes():
    """The control. Without it, `return UNVERIFIED` unconditionally would pass
    both tests above."""
    ac = audit_cycle()
    verdict, reason = ac.combine([pass_result(index=1), pass_result(index=2)])
    assert verdict == "PASS"
    assert reason is None


def test_findings_from_a_timed_out_pass_still_fail():
    """FAIL is checked before rc on purpose: findings a truncated pass did manage
    to write are still findings, and FAIL never falsely gates."""
    ac = audit_cycle()
    verdict, reason = ac.combine([pass_result(index=1, verdict="FAIL", must=1, rc=124)])
    assert verdict == "FAIL"
    assert reason == "findings:p1"


def test_no_report_outranks_rc():
    """A pass that delivered nothing is reported as no_report, not as its rc --
    the more specific diagnosis wins."""
    ac = audit_cycle()
    verdict, reason = ac.combine([
        pass_result(index=1, delivered="none", verdict=None, rc=124),
    ])
    assert verdict == "UNVERIFIED"
    assert reason == "no_report:p1"


def test_render_surfaces_the_rc_reason():
    ac = audit_cycle()
    results = [pass_result(index=1), pass_result(index=2, rc=124)]
    verdict, reason = ac.combine(results)
    text = ac.render(
        results,
        verdict,
        reason,
        feature="f",
        size_status="ok",
        passes=2,
    )
    line = auditcycle_lines(text)[0]
    assert "AUDITCYCLE: UNVERIFIED" in line
    assert "reason=dispatch_timeout:p2" in line
