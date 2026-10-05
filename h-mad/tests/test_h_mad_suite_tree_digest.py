"""A pytest session reports a working tree that moved under it (row 745).

A suite measured while its files were being rewritten prints a pass count about
bytes that no longer exist: a `set -e` cleanup landed in `hmad-dispatch.sh`
during a full suite (2026-08-25), a gap analysis read `13 failed` while a fix
rewrote the module under it (2026-09-07), and edits during a mutation run
produced a false `REFUSED` (2026-09-07). The session now digests the
non-ignored tree at start and end and prints `SUITE: TREE_MOVED paths=… n=K`
when they differ. It REPORTS; it never refuses an edit.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from suite_lock_support import git, make_tree, run_session, session_env

HARNESS = Path(__file__).resolve().parents[1] / "scripts" / "h_mad_mutation_harness.py"


def _moved_line(out: str) -> str | None:
    return next((line for line in out.splitlines() if line.startswith("SUITE: TREE_MOVED")), None)


def test_tree_moved_reported_when_tracked_file_edited_mid_session(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    proc = run_session(root, tmp_path / "bt", env=session_env(PROBE_WRITE="notes.txt"))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _moved_line(proc.stdout) == "SUITE: TREE_MOVED paths=notes.txt n=1", proc.stdout


def test_new_untracked_file_mid_session_is_reported(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    proc = run_session(root, tmp_path / "bt", env=session_env(PROBE_WRITE="docs/new.md"))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _moved_line(proc.stdout) == "SUITE: TREE_MOVED paths=docs/new.md n=1", proc.stdout


def test_ignored_writes_pycache_pytest_cache_hmad_are_quiet(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    writes = ",".join(["h-mad/scripts/__pycache__/x.cpython-311.pyc", ".pytest_cache/v/x",
                       ".h-mad/scratch.json", "report.md.done"])
    proc = run_session(root, tmp_path / "bt", env=session_env(PROBE_WRITE=writes))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (root / ".h-mad" / "scratch.json").exists(), "the probe did not write"
    assert _moved_line(proc.stdout) is None, proc.stdout


def test_unchanged_tree_prints_no_tree_moved_line(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    proc = run_session(root, tmp_path / "bt")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "1 passed" in proc.stdout
    assert _moved_line(proc.stdout) is None, proc.stdout


def test_edit_then_revert_is_not_reported(tmp_path: Path) -> None:
    """The documented LIMIT, pinned: two digests cannot see an edit undone in between.

    A file rewritten and restored before the session ends leaves the same bytes at
    both reads. Cases 1-3 behind this row were all persistent edits; an
    edit-and-revert inside one run is out of reach of a start/end comparison.
    """
    root = make_tree(tmp_path)
    proc = run_session(root, tmp_path / "bt",
                       env=session_env(PROBE_WRITE="notes.txt", PROBE_REVERT="1"))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (root / "notes.txt").read_text(encoding="utf-8") == "tracked\n"
    assert _moved_line(proc.stdout) is None, proc.stdout


def test_harness_tree_moved_on_dirty_edit_not_only_head(tmp_path: Path) -> None:
    """An uncommitted edit during a mutation run is a moved tree too.

    The harness compared HEAD only, so a sibling's unstaged write under a run was
    invisible to it (2026-09-07: a false `REFUSED` anchor).
    """
    from h_mad_mutation_harness import run_spec

    root = make_tree(tmp_path)
    head = git(root, "rev-parse", "HEAD")
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({
        "root": str(root),
        "command": [sys.executable, "-c",
                    "import pathlib,sys;"
                    f"p=pathlib.Path({str(root)!r});"
                    "(p/'docs').mkdir(exist_ok=True);"
                    "(p/'docs'/'sibling.md').write_text('a sibling wrote this');"
                    "sys.exit(0 if 'tracked' in (p/'notes.txt').read_text() else 1)"],
        "mutations": [{"name": "m", "file": "notes.txt", "find": "tracked",
                       "replace": "moved"}],
    }), encoding="utf-8")
    result = run_spec(spec)
    assert result["verdict"] == "TREE_MOVED", result
    assert result["head_before"] == result["head_after"] == head
    assert result["paths"] == ["docs/sibling.md"], result

    (root / "docs" / "sibling.md").unlink()
    proc = subprocess.run([sys.executable, str(HARNESS), str(spec)], cwd=root,
                          env=session_env(), capture_output=True, text=True, timeout=120)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "MUTATION: TREE_MOVED " in proc.stdout, proc.stdout
    assert "paths=docs/sibling.md n=1" in proc.stdout, proc.stdout


def test_hmad_operational_writes_are_quiet_when_not_ignored(tmp_path: Path) -> None:
    """Review S5. HemaSuite TRACKS `.h-mad/telemetry.jsonl` and does not ignore
    `*.done`, and the harness is shared through the skill install. A live lane's
    telemetry row or phase marker during a multi-minute run is h-mad's own
    bookkeeping, not a change to what the run measures, and must not void it."""
    from h_mad_mutation_harness import run_spec

    root = make_tree(tmp_path)
    (root / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    (root / ".h-mad").mkdir(exist_ok=True)
    (root / ".h-mad" / "telemetry.jsonl").write_text("{}\n", encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "hemasuite-shaped ignores")
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({
        "root": str(root),
        "command": [sys.executable, "-c",
                    "import pathlib,sys;"
                    f"p=pathlib.Path({str(root)!r});"
                    "open(p/'.h-mad'/'telemetry.jsonl','a').write('{\"row\":1}\\n');"
                    "(p/'docs').mkdir(exist_ok=True);"
                    "(p/'docs'/'r.report.md.done').write_text('done');"
                    "sys.exit(0 if 'tracked' in (p/'notes.txt').read_text() else 1)"],
        "mutations": [{"name": "m", "file": "notes.txt", "find": "tracked",
                       "replace": "moved"}],
    }), encoding="utf-8")
    result = run_spec(spec)
    assert result["verdict"] == "ALL_CAUGHT", result


def test_audit_gate_carries_tree_moved_into_its_suite_line(tmp_path: Path) -> None:
    """Review S7. A suite that printed TREE_MOVED is still PASS (report-only),
    but the verdict line the gate prints must say the tree moved under it."""
    from h_mad_audit_gate import run_suite
    from test_h_mad_audit_suite_gate import CLEAN, fake_suite, run

    sh = fake_suite(tmp_path, "moved.sh",
                    'echo "3 passed in 0.1s"; echo "SUITE: TREE_MOVED paths=a.py,b.md n=2"')
    outcome = run_suite(tmp_path, command=[str(sh)])
    assert outcome["verdict"] == "PASS", outcome
    assert outcome["tree_moved"] == "a.py,b.md", outcome
    audit = tmp_path / "f.plan.audit.v1.codex.md"
    audit.write_text(CLEAN, encoding="utf-8")
    out = run(str(audit), "--project-tests", str(tmp_path), "--suite-cmd", str(sh)).stdout
    assert "SUITE: PASS passed=3 failed=0 tree_moved=a.py,b.md" in out, out


def test_audit_cycle_carries_tree_moved_into_its_suite_line(capsys, tmp_path: Path) -> None:
    from test_h_mad_audit_cycle import _two_leg_reports, audit_cycle, run_collect_cycle
    from test_h_mad_audit_suite_gate import fake_suite

    sh = fake_suite(tmp_path, "moved.sh",
                    'echo "3 passed in 0.1s"; echo "SUITE: TREE_MOVED paths=a.py n=1"')
    rc, out, _ = run_collect_cycle(
        audit_cycle(), tmp_path=tmp_path, capsys=capsys, report_paths=_two_leg_reports(tmp_path),
        extra_args=["--project-tests", str(tmp_path), "--suite-cmd", str(sh)])
    assert "SUITE: PASS passed=3 failed=0 tree_moved=a.py" in out, out


def test_tracked_hmad_file_edited_mid_session_is_reported(tmp_path: Path) -> None:
    """R2-S1: only h-mad's CHURN is skipped. `.h-mad/invariants.md` is tracked
    (force-added here; HemaSuite tracks it) and read by
    `test_h_mad_invariants_layering.py`; an edit to it mid-run moved the tree.
    (`wires.jsonl` would do too, but the conftest's live-registry guard fails
    any session that edits it, which is a different refusal.)"""
    root = make_tree(tmp_path)
    (root / ".h-mad").mkdir(exist_ok=True)
    (root / ".h-mad" / "invariants.md").write_text("# invariants\n", encoding="utf-8")
    git(root, "add", "-f", ".h-mad/invariants.md")
    git(root, "commit", "-qm", "invariants")
    proc = run_session(root, tmp_path / "bt",
                       env=session_env(PROBE_WRITE=".h-mad/invariants.md"))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _moved_line(proc.stdout) == "SUITE: TREE_MOVED paths=.h-mad/invariants.md n=1", proc.stdout


def test_audit_gate_reads_a_colored_tree_moved_line(tmp_path: Path) -> None:
    """R2-N3: the plugin writes the line yellow; under --color=yes it starts with SGR."""
    from h_mad_audit_gate import run_suite
    from test_h_mad_audit_suite_gate import fake_suite

    sh = fake_suite(tmp_path, "colored.sh",
                    'echo "3 passed in 0.1s"; '
                    'printf "\\033[33mSUITE: TREE_MOVED paths=a.py n=1\\033[0m\\n"')
    assert run_suite(tmp_path, command=[str(sh)]).get("tree_moved") == "a.py"
