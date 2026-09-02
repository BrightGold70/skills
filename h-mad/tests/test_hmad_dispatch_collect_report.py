import json
import re
import stat
import sys
import textwrap
from pathlib import Path


SKILL = Path(__file__).resolve().parent.parent
SCRIPT_DIR = SKILL / "scripts"
WRAPPER = SCRIPT_DIR / "hmad-dispatch.sh"

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(SCRIPT_DIR))

import h_mad_audit_gate  # noqa: E402
from test_hmad_dispatch import _bindir, run  # noqa: E402
from test_hmad_dispatch_audit_cycle import (  # noqa: E402
    dispatch_args,
    install_audit_cycle_stubs,
    project_with_docs,
    read_jsonl,
    run_audit_cycle,
)


COLLECT_ARGV = [
    "--feature",
    "f",
    "--phase",
    "plan",
    "--cycle",
    "1",
    "--surface",
    "codex",
    "--report",
    "/x",
    "--project-root",
    "/y",
]


def _bindir_with_python(tmp_path: Path) -> Path:
    bindir = _bindir(tmp_path, [])
    (bindir / "python3").symlink_to(sys.executable)
    return bindir


def _install_collect_report_stub(tmp_path: Path) -> tuple[Path, Path]:
    script_dir = tmp_path / "collect-report-scripts"
    script_dir.mkdir()
    calls = script_dir / "collect_report_calls.json"
    stub = script_dir / "h_mad_collect_report.py"
    stub.write_text(
        textwrap.dedent(
            f"""\
            import json
            import sys
            from pathlib import Path

            Path({str(calls)!r}).write_text(json.dumps(sys.argv[1:]), encoding="utf-8")
            print("STUB-OUT")
            sys.exit(7)
            """
        ),
        encoding="utf-8",
    )
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
    return script_dir, calls


def test_collect_report_verb_execs_script_with_argv(tmp_path: Path) -> None:
    script_dir, calls = _install_collect_report_stub(tmp_path)

    result = run(
        ["collect-report", *COLLECT_ARGV],
        env={
            "_BINDIR": _bindir_with_python(tmp_path),
            "HMAD_AUDIT_CYCLE_SCRIPT_DIR": str(script_dir),
            "HMAD_STUB_HOSTILE": "all",
        },
    )

    assert result.returncode == 7, (
        "collect-report must delegate to h_mad_collect_report.py and propagate "
        f"its exit status; stderr was {result.stderr!r}"
    )
    assert result.stdout == "STUB-OUT\n", (
        "collect-report must propagate h_mad_collect_report.py stdout unchanged"
    )
    assert json.loads(calls.read_text(encoding="utf-8")) == COLLECT_ARGV, (
        "collect-report must pass argv through to h_mad_collect_report.py verbatim"
    )


def test_collect_reportx_unknown_verb_does_not_invoke_stub(tmp_path: Path) -> None:
    script_dir, calls = _install_collect_report_stub(tmp_path)

    result = run(
        ["collect-reportx", "--feature", "f"],
        env={
            "_BINDIR": _bindir_with_python(tmp_path),
            "HMAD_AUDIT_CYCLE_SCRIPT_DIR": str(script_dir),
            "HMAD_STUB_HOSTILE": "all",
        },
    )

    assert result.returncode == 2, "unknown collect-reportx verb must exit 2"
    assert "unknown verb 'collect-reportx'" in result.stderr
    assert not calls.exists(), "unknown collect-reportx verb must not invoke the stub"


def test_verbs_header_names_collect_report() -> None:
    verbs_line = next(
        line
        for line in WRAPPER.read_text(encoding="utf-8").splitlines()
        if line.startswith("# Verbs:")
    )

    verbs = [part.strip() for part in verbs_line.removeprefix("# Verbs:").split("|")]
    assert "collect-report" in verbs, (
        "# Verbs: header must include collect-report as a registered verb"
    )


def test_audit_cycle_assembler_report_file_uses_transport_name(tmp_path: Path) -> None:
    root = project_with_docs(tmp_path)
    script_dir, assemble_calls, _cycle_calls = install_audit_cycle_stubs(tmp_path)
    result = run_audit_cycle(
        tmp_path,
        dispatch_args(root=root, passes="1"),
        env={"HMAD_AUDIT_CYCLE_SCRIPT_DIR": str(script_dir)},
        capture=tmp_path / "agy.calls",
    )

    assert result.returncode == 0, result.stderr
    assemble_argv = read_jsonl(assemble_calls)[0]
    report_file = Path(assemble_argv[assemble_argv.index("--report-file") + 1])

    assert re.fullmatch(h_mad_audit_gate.TRANSPORT_RE, report_file.name), (
        "audit-cycle assembler --report-file basename must match "
        "h_mad_audit_gate.TRANSPORT_RE"
    )
