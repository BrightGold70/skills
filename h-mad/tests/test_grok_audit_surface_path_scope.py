"""Task 14a RED: opt-in path-scope clause in assembled audit prompts."""

import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest

from grokauditfixtures import _hostile_text
from test_h_mad_assemble_audit import _project_with_history
from test_hmad_dispatch_audit_cycle import STUB_PATH_SCOPE_CLAUSE


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "h_mad_assemble_audit.py"
SKILL_DIR = SCRIPT.parents[1]
PINNED = "7e10f543237267643824c8d452b0415b10103d33"


@pytest.fixture
def audit_module():
    def load(path=SCRIPT, name="h_mad_assemble_audit_under_test"):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return load


def _project(tmp_path, monkeypatch, *, n=5):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    root = _project_with_history(tmp_path, n=n)
    doc = root / "docs/01-plan/features/demo.plan.md"
    doc.write_text(doc.read_text(encoding="utf-8") + "\n" + _hostile_text(), encoding="utf-8")
    return root


def _assemble(module, root, phase="plan", *, report_file="/tmp/demo.report.md", **kwargs):
    return module.assemble(
        feature="demo", phase=phase, project_root=root,
        docs_dir=root / "docs/01-plan/features",
        sentinel="AUDIT-demo-plan-v1", report_file=report_file,
        template=SKILL_DIR / "audit-prompt.template.md", vh_tail=2, **kwargs,
    )


def _without_report_path(text, report_file):
    return text.replace(report_file, "")


def _assert_root_absent(text, root, report_file):
    scrubbed = _without_report_path(text, report_file)
    assert str(root) not in scrubbed, "assembled prompt must not disclose the supplied project-root spelling"
    assert str(root.resolve()) not in scrubbed, "assembled prompt must not disclose the resolved project root"


def test_path_scope_clause_present_when_switched_on(audit_module, tmp_path, monkeypatch):
    module = audit_module()
    root = _project(tmp_path, monkeypatch)
    text, problems = _assemble(module, root, path_scope=True)

    assert problems == []
    assert text.count(STUB_PATH_SCOPE_CLAUSE) == 1, (
        "assemble(path_scope=True) must put the path-scope clause in the prompt exactly once"
    )
    assert text.index(module.CONTRACT_SEPARATOR) < text.index(STUB_PATH_SCOPE_CLAUSE)
    assert text.index(STUB_PATH_SCOPE_CLAUSE) < text.index("Target document:")


def test_path_scope_flag_reaches_the_prompt_through_the_cli(audit_module, tmp_path,
                                                             monkeypatch, capsys):
    module = audit_module()
    root = _project(tmp_path, monkeypatch)
    report = tmp_path / "report.report.md"
    out = tmp_path / "prompt.txt"
    rc = module.main([
        "--feature", "demo", "--phase", "plan", "--project-root", str(root),
        "--report-file", str(report), "--out", str(out), "--path-scope",
    ])

    assert rc == 0
    assert "ASSEMBLE: PASS" in capsys.readouterr().out
    prompt = out.read_text(encoding="utf-8")
    assert prompt.count(STUB_PATH_SCOPE_CLAUSE) == 1, (
        "main(--path-scope) must forward the switch into assemble and its written prompt"
    )


def test_assembled_prompt_carries_no_root_path(audit_module, tmp_path, monkeypatch):
    module = audit_module()
    real_root = _project(tmp_path / "real", monkeypatch)
    linked_root = tmp_path / "project-link"
    linked_root.symlink_to(real_root, target_is_directory=True)
    report_file = str(linked_root / ".hmad-report/audit.report.md")

    # Deliberately omit path_scope: this guard pins today's default behavior.
    text, problems = _assemble(module, linked_root, report_file=report_file)

    assert problems == []
    assert "3 of 5 Version History entries omitted" in text
    _assert_root_absent(text, linked_root, report_file)


def test_path_scope_clause_is_identical_across_roots_and_report_paths(
        audit_module, tmp_path, monkeypatch):
    module = audit_module()
    first_root = _project(tmp_path / "first", monkeypatch)
    second_root = _project(tmp_path / "second", monkeypatch)
    first_report = str(tmp_path / "first" / "report.report.md")
    second_report = str(tmp_path / "second" / "different.report.md")

    first, first_problems = _assemble(
        module, first_root, report_file=first_report, path_scope=True)
    second, second_problems = _assemble(
        module, second_root, report_file=second_report, path_scope=True)

    assert first_problems == second_problems == []
    first_clause = [line for line in first.splitlines() if line == STUB_PATH_SCOPE_CLAUSE]
    second_clause = [line for line in second.splitlines() if line == STUB_PATH_SCOPE_CLAUSE]
    assert first_clause == second_clause == [STUB_PATH_SCOPE_CLAUSE], (
        "the switch-on clause must be invariant across project roots and report paths"
    )
    _assert_root_absent(first, first_root, first_report)
    _assert_root_absent(second, second_root, second_report)


@pytest.mark.parametrize("phase", ["plan", "design", "impl-plan"], ids=["plan", "design", "impl-plan"])
def test_switch_off_prompt_is_byte_identical_to_the_pinned_assembler(
        audit_module, tmp_path, monkeypatch, phase):
    root = _project(tmp_path / "project", monkeypatch)
    ref = tmp_path / "ref"
    (ref / "scripts").mkdir(parents=True)
    for source, target in (
        ("h-mad/scripts/h_mad_assemble_audit.py", ref / "scripts/h_mad_assemble_audit.py"),
        ("h-mad/audit-prompt.template.md", ref / "audit-prompt.template.md"),
    ):
        result = subprocess.run(
            ["git", "show", f"{PINNED}:{source}"],
            capture_output=True, text=True, check=True, timeout=15,
        )
        target.write_text(result.stdout, encoding="utf-8")
    shutil.copyfile(SKILL_DIR / "invariants.base.md", ref / "invariants.base.md")
    pinned = audit_module(ref / "scripts/h_mad_assemble_audit.py", "pinned_audit_assembler")
    current = audit_module()
    report_file = str(tmp_path / "report.report.md")
    docs_dir = root / "docs/01-plan/features"
    kwargs = dict(
        feature="demo", phase=phase, project_root=root, docs_dir=docs_dir,
        sentinel="AUDIT-demo-plan-v1", report_file=report_file, vh_tail=2,
    )

    pinned_text, pinned_problems = pinned.assemble(
        **kwargs, template=ref / "audit-prompt.template.md")
    # No path_scope keyword: switch-off must preserve the current call contract.
    current_text, current_problems = current.assemble(
        **kwargs, template=SKILL_DIR / "audit-prompt.template.md")

    assert pinned_problems == current_problems == []
    assert current_text == pinned_text, (
        f"assemble(phase={phase!r}) with the switch off must remain byte-identical to {PINNED}"
    )


@pytest.mark.parametrize("phase", ["plan", "design", "impl-plan"], ids=["plan", "design", "impl-plan"])
def test_switch_on_prompt_is_switch_off_plus_the_clause_only(
        audit_module, tmp_path, monkeypatch, phase):
    module = audit_module()
    root = _project(tmp_path, monkeypatch)
    switched_off, off_problems = _assemble(module, root, phase)
    switched_on, on_problems = _assemble(module, root, phase, path_scope=True)

    assert off_problems == on_problems == []
    assert switched_on.count(STUB_PATH_SCOPE_CLAUSE + "\n\n") == 1
    assert switched_on.replace(STUB_PATH_SCOPE_CLAUSE + "\n\n", "", 1) == switched_off, (
        "switching on path scope may add only the clause and its two trailing newlines"
    )
