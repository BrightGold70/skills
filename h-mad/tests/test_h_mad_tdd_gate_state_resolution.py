"""The Phase-5 TDD gate must find its state file in a sub-project layout.

The hook resolved `STATE_FILE="${CLAUDE_PROJECT_DIR:-.}/docs/.bkit-memory.json"`
and then fast-pathed on `[ ! -f "$STATE_FILE" ] && exit 0` — documented as "no
state file → no orchestrator → allow".

That fail-open is correct when a project genuinely has no h-mad state. It is
catastrophic when the state file merely lives somewhere else: HemaSuite keeps
its orchestrator state at `hematology-paper-writer/docs/.bkit-memory.json`, so
the repo-root path never exists and the gate stood down on EVERY write. A full
Phase 5 ran there believing production `.py` writes were blocked. They were not,
and nothing said so — the gate's silence is indistinguishable from its approval.

Both existing suites (skills + HemaSuite consumer) set `CLAUDE_PROJECT_DIR` to
`state_file.parent.parent`, i.e. the repo-root layout only, which is exactly why
this survived. These tests pin the sub-project case, and — just as importantly —
pin the two directions the fix must NOT break: a project with no state anywhere
still allows, and a state file outside the project is never adopted.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

HOOK = Path.home() / ".claude" / "hooks" / "h-mad-tdd-gate.sh"

_STATE_STEP5 = {
    "version": 1,
    "features": {},
    "orchestrator_state": {
        "feat": {
            "feature": "feat", "current_phase": 5, "phase": "step5",
            "last_completed_phase": 4, "halt_reason": None,
            # Declared so the Codex-authorship gate is not what fires; this file
            # is about state-file RESOLUTION, and a test that passes for the
            # other gate's reason would prove nothing.
            "codex_status": "exhausted",
        }
    },
}


def _write_state(docs_parent: Path) -> Path:
    docs = docs_parent / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    sf = docs / ".bkit-memory.json"
    sf.write_text(json.dumps(_STATE_STEP5), encoding="utf-8")
    return sf


def _bin(tmp_path: Path) -> Path:
    b = tmp_path / "bin"
    b.mkdir(exist_ok=True)
    jq = shutil.which("jq")
    if jq and not (b / "jq").exists():
        (b / "jq").symlink_to(jq)
    return b


def _run(project_dir: Path, target: str, bin_dir: Path) -> subprocess.CompletedProcess:
    env = {"PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": str(Path.home()),
           "CLAUDE_PROJECT_DIR": str(project_dir)}
    return subprocess.run([str(HOOK), target], capture_output=True, text=True,
                          check=False, env=env)


def test_gate_finds_state_one_directory_down(tmp_path: Path) -> None:
    """THE bug: HemaSuite's layout. Repo root has no state; the sub-project does."""
    root = tmp_path / "HemaSuite"
    sub = root / "hematology-paper-writer"
    sub.mkdir(parents=True)
    _write_state(sub)
    assert not (root / "docs" / ".bkit-memory.json").exists(), "fixture must mirror the real layout"

    target = sub / "tools" / "widget.py"
    target.parent.mkdir(parents=True)

    r = _run(root, str(target), _bin(tmp_path))
    assert r.returncode == 1, (
        "the gate stood down: it resolved a repo-root state file that does not "
        f"exist and allowed a Phase-5 production write. stdout={r.stdout!r} stderr={r.stderr!r}"
    )
    assert "H-MAD-TDD-GATE" in r.stderr, r.stderr


def test_no_state_anywhere_still_allows(tmp_path: Path) -> None:
    """The fail-open the fix must PRESERVE.

    A project with no h-mad state has no orchestrator, so the gate must not
    block. Losing this would make the hook refuse writes in every non-h-mad
    repo — far worse than the bug being fixed.
    """
    root = tmp_path / "plain-repo"
    (root / "src").mkdir(parents=True)
    target = root / "src" / "thing.py"
    r = _run(root, str(target), _bin(tmp_path))
    assert r.returncode == 0, (
        f"blocked a write in a project with no h-mad state: {r.stderr!r}"
    )


def test_repo_root_layout_still_works(tmp_path: Path) -> None:
    """Back-compat: the single-project layout every existing test uses."""
    root = tmp_path / "single"
    root.mkdir(parents=True)
    _write_state(root)
    target = root / "tools" / "widget.py"
    target.parent.mkdir(parents=True)
    r = _run(root, str(target), _bin(tmp_path))
    assert r.returncode == 1, f"regressed the repo-root layout: {r.stdout!r} {r.stderr!r}"


def test_state_outside_the_project_is_not_adopted(tmp_path: Path) -> None:
    """Bound the search.

    Walking up from the target must stop at the project root. A state file in a
    PARENT of the project belongs to a different project; adopting it would let
    one repo's Phase 5 gate writes in an unrelated sibling — a false block, and
    the kind that is baffling to diagnose because nothing in the current repo
    explains it.
    """
    outer = tmp_path / "outer"
    _write_state(outer)                      # a foreign project's state, above ours
    project = outer / "inner-project"
    (project / "src").mkdir(parents=True)
    target = project / "src" / "thing.py"

    r = _run(project, str(target), _bin(tmp_path))
    assert r.returncode == 0, (
        "adopted a state file from OUTSIDE the project root — a Phase 5 in a "
        f"parent repo would gate writes here: {r.stderr!r}"
    )


# --- the allow-list must anchor to the basename ---------------------------
#
# Found while writing the tests above: pytest names its tmp dirs `test_<name>0`,
# so every fixture written under one matched `*test_*.py` and was exempted. That
# made two expect-block tests fail for a reason that had nothing to do with
# state resolution — and it is a real defect, not a test artifact.


def test_a_production_file_under_a_test_named_directory_is_still_gated(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    (root / "test_helpers").mkdir(parents=True)
    _write_state(root)
    target = root / "test_helpers" / "widget.py"
    r = _run(root, str(target), _bin(tmp_path))
    assert r.returncode == 1, (
        "a production .py under a directory containing 'test_' was exempted — the "
        f"allow-list matched a parent directory, not the filename: {r.stderr!r}"
    )


def test_real_test_files_are_still_exempt(tmp_path: Path) -> None:
    """Counter-direction: anchoring must not start gating actual test files."""
    root = tmp_path / "proj"
    (root / "pkg").mkdir(parents=True)
    _write_state(root)
    for name in ("test_widget.py", "widget_test.py", "conftest.py"):
        target = root / "pkg" / name
        r = _run(root, str(target), _bin(tmp_path))
        assert r.returncode == 0, f"{name} should be exempt but was gated: {r.stderr!r}"


def test_test_directories_are_still_exempt(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    (root / "tests").mkdir(parents=True)
    _write_state(root)
    target = root / "tests" / "helper.py"
    r = _run(root, str(target), _bin(tmp_path))
    assert r.returncode == 0, f"a file under tests/ should be exempt: {r.stderr!r}"
