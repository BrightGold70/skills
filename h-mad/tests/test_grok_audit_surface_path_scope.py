"""Task 14a RED: opt-in path-scope clause in assembled audit prompts."""

import ast
import importlib.util
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from grokauditfixtures import _hostile_text
from test_h_mad_assemble_audit import _project_with_history
from test_hmad_dispatch_audit_cycle import STUB_PATH_SCOPE_CLAUSE
from test_grok_audit_surface_wrapper import (
    _pass_root_case, _run_pass_roots,
)
from test_hmad_dispatch_audit_cycle import (
    auditcycle_lines, dispatch_args, dispatch_count, project_with_docs,
    read_jsonl, run_audit_cycle,
)


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


def _own_stems(tmp_path, case):
    stem_dir = tmp_path / "audit stems [*] 'quoted'"
    stem_dir.mkdir()
    case["env"]["HMAD_AUDIT_STEM_DIR"] = str(stem_dir)
    return stem_dir


def test_audit_cycle_with_pass_roots_passes_the_switch_to_every_pass(tmp_path):
    case = _pass_root_case(tmp_path)
    _own_stems(tmp_path, case)
    result = _run_pass_roots(tmp_path, case, roots=case["roots"], passes=3)

    calls = read_jsonl(case["assemble"])
    assert len(calls) == 3, "audit-cycle must assemble every pass-root prompt"
    assert all("--path-scope" in args for args in calls), (
        "_cmd_audit_cycle must pass --path-scope to every pass when --pass-root is present"
    )
    assert result.returncode == 0, result.stderr


def test_audit_cycle_without_pass_roots_does_not_pass_the_switch(tmp_path):
    case = _pass_root_case(tmp_path)
    stem_dir = _own_stems(tmp_path, case)
    result = run_audit_cycle(
        tmp_path, dispatch_args(root=case["root"], passes="3"),
        env=case["env"], capture=case["capture"], cwd=tmp_path,
    )

    calls = read_jsonl(case["assemble"])
    assert calls and all("--path-scope" not in args for args in calls), (
        "audit-cycle without --pass-root must leave the path-scope switch off"
    )
    assert len(auditcycle_lines(result.stdout)) == 1 and "REQUIRE: STOP" not in result.stdout
    assert not list(stem_dir.glob("*.here.txt")), "switch-off cycles must not record a here file"


def _real_path_scope_cycle(tmp_path, monkeypatch):
    monkeypatch.delenv("HMAD_AUDIT_CYCLE_SCRIPT_DIR", raising=False)
    feature = "scope-cycle"
    root = project_with_docs(tmp_path, feature=feature)
    (root / ".h-mad/invariants.md").write_text("# Local project rules\n", encoding="utf-8")
    # Replace the hostile fixture documents with plain human-authored material,
    # including one absolute path line like a real audit input might contain.
    for kind in ("spec", "plan", "impl-plan"):
        (root / "docs/01-plan/features" / f"{feature}.{kind}.md").write_text(
            "# Plain audit input\n\n/author/machine/private.txt\n", encoding="utf-8")
    (root / "docs/02-design/features" / f"{feature}.design.md").write_text(
        "# Plain design input\n", encoding="utf-8")
    roots = [root]
    for index, name in enumerate(("scope pass two", "scope pass three"), 2):
        other = project_with_docs(tmp_path / name, feature=feature)
        (other / ".h-mad/invariants.md").write_text(
            f"# Local project rules {index}\n", encoding="utf-8")
        for kind in ("spec", "plan", "impl-plan"):
            (other / "docs/01-plan/features" / f"{feature}.{kind}.md").write_text(
                f"# Pass {index} audit input\n\n/author/machine/private-{index}.txt\n",
                encoding="utf-8")
        (other / "docs/02-design/features" / f"{feature}.design.md").write_text(
            f"# Pass {index} design input\n", encoding="utf-8")
        roots.append(other.resolve())
    stem_dir = tmp_path / "real audit stems"
    stem_dir.mkdir()
    capture = tmp_path / "real agy calls"
    result = run_audit_cycle(
        tmp_path,
        dispatch_args(feature=feature, root=root, passes="3")
        + [arg for item in roots for arg in ("--pass-root", str(item))]
        + ["--report-grace", "0"],
        env={"HMAD_AUDIT_STEM_DIR": str(stem_dir), "HMAD_STUB_HOSTILE": "all"},
        capture=capture, cwd=tmp_path,
    )
    return root, roots, stem_dir, capture, result


def test_calibration_cycle_carries_the_clause_in_every_pass_and_reaches_dispatch(tmp_path, monkeypatch):
    _root, _roots, stem_dir, _capture, result = _real_path_scope_cycle(tmp_path, monkeypatch)
    assert result.returncode == 0, result.stderr
    assembled = sorted(stem_dir.glob("*_p[0-9].asm.txt"))
    assert len(assembled) == 3
    assert all("ASSEMBLE: PASS" in path.read_text(encoding="utf-8") for path in assembled), [
        path.read_text(encoding="utf-8") for path in assembled
    ]
    prompts = []
    for path in assembled:
        pass_line = next(line for line in path.read_text(encoding="utf-8").splitlines()
                         if line.startswith("ASSEMBLE: PASS "))
        # The path may hold spaces; it ends where the `<bytes>B` size field begins.
        prompt = Path(re.match(r"ASSEMBLE: PASS (.+?) \d+B ", pass_line).group(1))
        assert prompt.parent == stem_dir, "real pass prompts must be staged in the cycle stem dir"
        prompts.append(prompt)
    assert all(path.read_text(encoding="utf-8").splitlines().count(STUB_PATH_SCOPE_CLAUSE) == 1
               for path in prompts), "each assembled pass prompt must carry the clause once"
    logs = sorted(stem_dir.glob("*_p[0-9].log"))
    assert len(logs) == 3 and all(
        sum(json.loads(line).get("event") == "init"
            for line in path.read_text(encoding="utf-8").splitlines()) == 1
        for path in logs
    ), "the real cycle must reach exactly one dispatch for each pass"
    assert not any("reason=prompt_divergence" in line for line in auditcycle_lines(result.stdout))


@pytest.mark.parametrize("halt", [False, True], ids=["real", "assemble_halt"])
def test_calibration_cycle_records_its_here(tmp_path, monkeypatch, halt):
    if not halt:
        _root, _roots, stem_dir, _capture, result = _real_path_scope_cycle(tmp_path, monkeypatch)
        expected_here = str((SCRIPT.parent).resolve())
    else:
        case = _pass_root_case(tmp_path)
        stem_dir = _own_stems(tmp_path, case)
        here = case["env"]["HMAD_AUDIT_CYCLE_SCRIPT_DIR"]
        case["env"]["HMAD_ASSEMBLE_HALT_P2"] = "1"
        result = _run_pass_roots(tmp_path, case, roots=case["roots"], passes=3)
        expected_here = here

    records = list(stem_dir.glob("*.here.txt"))
    assert len(records) == 1, "a calibration cycle must write exactly one here record"
    assert records[0].read_text(encoding="utf-8").splitlines() == [f"here={expected_here}"]
    if halt:
        assert auditcycle_lines(result.stdout) == [
            "AUDITCYCLE: UNVERIFIED reason=assemble_halt:p2 passes=3 size_status=verified"
        ]
    else:
        assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("drop,pass_number", [
    ({"HMAD_ASSEMBLE_DROP_CLAUSE_P2": "1"}, "p2"),
    ({"HMAD_ASSEMBLE_DROP_CLAUSE_P1": "1"}, "p1"),
    ({"HMAD_ASSEMBLE_DROP_CLAUSE_P1": "1", "HMAD_ASSEMBLE_DROP_CLAUSE_P2": "1",
      "HMAD_ASSEMBLE_DROP_CLAUSE_P3": "1"}, "p1"),
], ids=["p2", "p1", "all"])
def test_calibration_cycle_halts_when_a_pass_lacks_the_clause(tmp_path, drop, pass_number):
    case = _pass_root_case(tmp_path)
    stem_dir = _own_stems(tmp_path, case)
    halt_file = tmp_path / "HALT"
    case["env"].update(drop)
    result = _run_pass_roots(tmp_path, case, roots=case["roots"], passes=3,
                             extra=["--halt-file", str(halt_file)])
    token = f"REQUIRE: STOP reason=path_scope_missing:{pass_number}"
    assert result.returncode == 0
    assert result.stdout.splitlines()[-1:] == [token]
    assert not auditcycle_lines(result.stdout)
    assert dispatch_count(case["capture"]) == 0
    assert read_jsonl(case["cycle"]) == []
    assert halt_file.read_text(encoding="utf-8").splitlines().count(
        f"path_scope_missing:{pass_number}") == 1
    assert f"[H-MAD] audit-cycle halted path_scope_missing:{pass_number}" in result.stderr
    assert stem_dir.exists()


def test_calibration_cycle_with_the_clause_in_every_pass_launches(tmp_path):
    case = _pass_root_case(tmp_path)
    stem_dir = _own_stems(tmp_path, case)
    result = _run_pass_roots(tmp_path, case, roots=case["roots"], passes=3,
                             extra=["--halt-file", str(tmp_path / "absent-HALT")])
    assert dispatch_count(case["capture"]) == 3
    assert len(auditcycle_lines(result.stdout)) == 1
    assert "REQUIRE: STOP" not in result.stdout
    for args in read_jsonl(case["assemble"]):
        prompt = Path(args[args.index("--out") + 1])
        assert prompt.read_text(encoding="utf-8").splitlines().count(STUB_PATH_SCOPE_CLAUSE) == 1
    assert stem_dir.exists()


def test_pre_clause_assembler_refuses_the_switch_and_nothing_launches(tmp_path):
    old = tmp_path / "old/scripts"
    old.mkdir(parents=True)
    revision = "7e10f543237267643824c8d452b0415b10103d33"
    source = subprocess.run(
        ["git", "show", f"{revision}:h-mad/scripts/h_mad_assemble_audit.py"],
        capture_output=True, text=True, check=True, timeout=15,
    )
    (old / "h_mad_assemble_audit.py").write_text(source.stdout, encoding="utf-8")
    for name in ("h_mad_audit_cycle.py", "h_mad_extract_report.py",
                 "h_mad_review_evidence.py", "h_mad_audit_gate.py"):
        shutil.copyfile(SCRIPT.parent / name, old / name)
    old_root = old.parent
    shutil.copyfile(SKILL_DIR / "audit-prompt.template.md", old_root / "audit-prompt.template.md")
    shutil.copyfile(SKILL_DIR / "invariants.base.md", old_root / "invariants.base.md")
    feature = "old-assembler"
    root = project_with_docs(tmp_path, feature=feature)
    (root / ".h-mad/invariants.md").write_text("# Local project rules\n", encoding="utf-8")
    for kind in ("spec", "plan", "impl-plan"):
        (root / "docs/01-plan/features" / f"{feature}.{kind}.md").write_text(
            "# Plain audit input\n\n/author/machine/private.txt\n", encoding="utf-8")
    (root / "docs/02-design/features" / f"{feature}.design.md").write_text(
        "# Plain design input\n", encoding="utf-8")
    roots = [root]
    for index, name in enumerate(("old pass two", "old pass three"), 2):
        other_base = tmp_path / name
        other_root = project_with_docs(other_base, feature=feature)
        (other_root / ".h-mad/invariants.md").write_text(
            f"# Local project rules {index}\n", encoding="utf-8")
        for kind in ("spec", "plan", "impl-plan"):
            (other_root / "docs/01-plan/features" / f"{feature}.{kind}.md").write_text(
                f"# Pass {index} audit input\n\n/author/machine/private-{index}.txt\n",
                encoding="utf-8")
        (other_root / "docs/02-design/features" / f"{feature}.design.md").write_text(
            f"# Pass {index} design input\n", encoding="utf-8")
        roots.append(other_root.resolve())
    stem_dir = tmp_path / "old assembler stems"
    stem_dir.mkdir()
    capture = tmp_path / "old assembler agy calls"
    result = run_audit_cycle(
        tmp_path,
        dispatch_args(feature=feature, root=root, passes="3")
        + [arg for item in roots for arg in ("--pass-root", str(item))]
        + ["--report-grace", "0"],
        env={"HMAD_AUDIT_STEM_DIR": str(stem_dir),
             "HMAD_AUDIT_CYCLE_SCRIPT_DIR": str(old), "HMAD_STUB_HOSTILE": "all"},
        capture=capture, cwd=tmp_path,
    )
    assert dispatch_count(capture) == 0, (
        "the pre-clause assembler must reject --path-scope before any agent launch"
    )
    assert result.returncode == 4
    assert not auditcycle_lines(result.stdout)


def test_wrapper_clause_copy_equals_the_assembler_constant():
    wrapper = (SCRIPT.parent / "hmad-dispatch.sh").read_text(encoding="utf-8")
    matches = re.findall(r'^_HMAD_PATH_SCOPE_CLAUSE="([^"\n]*)"$', wrapper, re.M)
    assert len(matches) == 1, "wrapper must define exactly one path-scope clause copy"
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    values = [node.value.value for node in tree.body
              if isinstance(node, ast.Assign)
              and any(isinstance(target, ast.Name) and target.id == "PATH_SCOPE_CLAUSE"
                      for target in node.targets)
              and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)]
    assert len(values) == 1 and matches[0] == values[0] == STUB_PATH_SCOPE_CLAUSE
