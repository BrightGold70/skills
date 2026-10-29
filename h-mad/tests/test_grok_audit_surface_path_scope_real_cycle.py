"""Row 28 split: real-cycle path-scope tests extracted from test_grok_audit_surface_path_scope.py.

Keeps test_grok_audit_surface_path_scope.py (~4.6 s) well under the TDD judge's
40 s JUDGE_BUDGET_S even under heavy concurrent load.
"""

import json
import re
from pathlib import Path

import pytest

from test_hmad_dispatch_audit_cycle import (
    STUB_PATH_SCOPE_CLAUSE,
    auditcycle_lines,
    dispatch_args,
    project_with_docs,
    run_audit_cycle,
)


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "h_mad_assemble_audit.py"


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


@pytest.mark.parametrize("halt", [False], ids=["real"])
def test_calibration_cycle_records_its_here(tmp_path, monkeypatch, halt):
    _root, _roots, stem_dir, _capture, result = _real_path_scope_cycle(tmp_path, monkeypatch)
    expected_here = str((SCRIPT.parent).resolve())
    records = list(stem_dir.glob("*.here.txt"))
    assert len(records) == 1, "a calibration cycle must write exactly one here record"
    assert records[0].read_text(encoding="utf-8").splitlines() == [f"here={expected_here}"]
    assert result.returncode == 0, result.stderr
