"""Test sessions stage audit stems privately, and never sweep the shared `/tmp`.

`audit-cycle` mints a fresh `audit_<f>_<p>_cycle<N>_run<UTC>-<pid>` stem per run
(claim once, never re-hand a report path). Under `/tmp` that left ~900 files per
suite, so a session fixture snapshotted `/tmp/audit_*_run*` before the session and
unlinked every NEW match after it. `/tmp` is shared by every pytest session on the
machine, other worktrees of this repository included, so one session's teardown
deleted the stems a concurrent session was still using: `sed: /tmp/audit_handed-…
_p2.asm.txt: No such file or directory`, random audit-cycle failures, and mutation
runs reporting BASELINE_NOT_GREEN. The suite lock serialises sessions per git
toplevel, so it cannot cover two worktrees.

The verb now stages under `$HMAD_AUDIT_STEM_DIR` (default `/tmp`, so production is
unchanged), the conftest points it at a directory under the session's own basetemp,
and nothing sweeps `/tmp` any more.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from test_hmad_dispatch_audit_cycle import (  # noqa: E402
    assert_registered_verb,
    dispatch_args,
    install_audit_cycle_stubs,
    project_with_docs,
    read_jsonl,
    run_audit_cycle,
)

HERE = Path(__file__).resolve().parent
RUN_STEM = r"_run\d{8}T\d{6}Z-\d+"
# Every name a pass of the verb can leave behind, for an exact-path cleanup.
PASS_SUFFIXES = (".txt", ".report.md", ".report.md.done", ".out.txt", ".log", ".asm.txt")


def _inner_session(tmp_path: Path, body: str) -> subprocess.CompletedProcess:
    """Run a child pytest session under a copy of the real conftest.

    The copy has no sibling `tree_lock_plugin.py`, so it takes no tree lock (see
    `_register_tree_lock_plugin` in conftest.py): the child can run while this
    session holds the lock.
    """
    suite = tmp_path / "suite"
    suite.mkdir()
    for name in ("conftest.py", "leak_reaper.py"):
        shutil.copy(HERE / name, suite / name)
    (suite / "test_inner.py").write_text(body, encoding="utf-8")
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(suite),
         "--basetemp", str(tmp_path / "bt")],
        capture_output=True, text=True, cwd=suite, timeout=120, check=False)


def test_session_teardown_spares_a_foreign_sessions_stem_file(tmp_path):
    """A stem file another session created while this one ran is not this
    session's to delete, even when its name matches every pattern the suite uses.

    Known flake: the file sits in the shared /tmp and matches the OLD sweep regex,
    so a session still running pre-fix code that ends inside the ~1 s inner
    window can delete it. A lone failure here is that, not a regression."""
    foreign = Path(f"/tmp/audit_demo_plan_cycle{uuid.uuid4().hex}"
                   f"_run20261005T000000Z-{os.getpid()}_p1.asm.txt")
    body = (
        "import subprocess, sys\n"
        "def test_a_concurrent_session_stages_a_stem():\n"
        "    subprocess.run([sys.executable, '-c',\n"
        "                    'import sys; open(sys.argv[1], \"w\").write(\"foreign\")',\n"
        f"                    {str(foreign)!r}], check=True)\n"
    )
    try:
        result = _inner_session(tmp_path, body)
        assert result.returncode == 0, result.stdout + result.stderr
        assert foreign.exists(), (
            "the session's teardown deleted a /tmp stem file it did not create; a "
            "concurrent session in another worktree loses its audit files")
        assert foreign.read_text(encoding="utf-8") == "foreign"
    finally:
        foreign.unlink(missing_ok=True)


def test_session_exports_a_private_stem_dir_under_its_basetemp(tmp_path):
    record = tmp_path / "stem-dir.txt"
    body = (
        "import os\n"
        "def test_records_the_stem_dir():\n"
        f"    open({str(record)!r}, 'w').write(os.environ.get('HMAD_AUDIT_STEM_DIR', ''))\n"
    )
    result = _inner_session(tmp_path, body)
    assert result.returncode == 0, result.stdout + result.stderr
    stem_dir = record.read_text(encoding="utf-8")
    assert stem_dir, "the session did not export HMAD_AUDIT_STEM_DIR"
    basetemp = (tmp_path / "bt").resolve()
    assert Path(stem_dir).resolve().is_relative_to(basetemp), (stem_dir, basetemp)


def _assemble_outs(assemble_calls: Path) -> list[str]:
    return [a[a.index("--out") + 1] for a in read_jsonl(assemble_calls)]


def test_verb_stages_its_stem_under_hmad_audit_stem_dir(tmp_path):
    root = project_with_docs(tmp_path)
    script_dir, assemble_calls, _ = install_audit_cycle_stubs(tmp_path)
    stems = tmp_path / "stems"
    stems.mkdir()
    feature = f"stemdir-{uuid.uuid4().hex}"
    r = run_audit_cycle(
        tmp_path, dispatch_args(feature=feature, root=root, passes="2"),
        env={"HMAD_AUDIT_CYCLE_SCRIPT_DIR": str(script_dir),
             "HMAD_AUDIT_STEM_DIR": str(stems)},
        capture=tmp_path / "agy.calls",
    )
    assert r.returncode == 0, r.stderr
    assert_registered_verb(r)
    stem = re.escape(f"{stems}/audit_{feature}_plan_cycle7") + RUN_STEM
    outs = _assemble_outs(assemble_calls)
    assert len(outs) == 2, outs
    for i, out in enumerate(outs, start=1):
        assert re.fullmatch(stem + rf"_p{i}\.txt", out), out
        assert Path(out[: -len(".txt")] + ".asm.txt").is_file(), out
    assert not list(Path("/tmp").glob(f"audit_{feature}_*")), "a stem leaked into /tmp"


def test_verb_stem_dir_defaults_to_tmp(tmp_path, monkeypatch):
    """Unset, the verb stages exactly where it always did. The cleanup deletes the
    exact paths this test was handed, never a pattern."""
    monkeypatch.delenv("HMAD_AUDIT_STEM_DIR", raising=False)
    root = project_with_docs(tmp_path)
    script_dir, assemble_calls, _ = install_audit_cycle_stubs(tmp_path)
    feature = f"stemdefault-{uuid.uuid4().hex}"
    outs: list[str] = []
    try:
        r = run_audit_cycle(
            tmp_path, dispatch_args(feature=feature, root=root, passes="1"),
            env={"HMAD_AUDIT_CYCLE_SCRIPT_DIR": str(script_dir)},
            capture=tmp_path / "agy.calls",
        )
        outs = _assemble_outs(assemble_calls)
        assert r.returncode == 0, r.stderr
        assert len(outs) == 1, outs
        assert re.fullmatch(re.escape(f"/tmp/audit_{feature}_plan_cycle7") + RUN_STEM
                            + r"_p1\.txt", outs[0]), outs
    finally:
        for out in outs:
            base = out[: -len(".txt")]
            for suffix in PASS_SUFFIXES:
                Path(base + suffix).unlink(missing_ok=True)
    assert not list(Path("/tmp").glob(f"audit_{feature}_*")), "a pass file was not enumerated"


def test_verb_refuses_an_unusable_stem_dir(tmp_path):
    root = project_with_docs(tmp_path)
    script_dir, assemble_calls, cycle_calls = install_audit_cycle_stubs(tmp_path)
    colon = tmp_path / "a:b"
    colon.mkdir()
    # Each bad value is refused by its own check alone: the relative one EXISTS
    # (relative to the verb's cwd), the colon one is absolute and exists.
    for n, bad in enumerate(("stems", str(tmp_path / "absent"), str(colon))):
        run_dir = tmp_path / f"run{n}"  # each run needs its own stub bindir
        (run_dir / "stems").mkdir(parents=True)
        r = run_audit_cycle(
            run_dir, dispatch_args(root=root, passes="1"),
            env={"HMAD_AUDIT_CYCLE_SCRIPT_DIR": str(script_dir),
                 "HMAD_AUDIT_STEM_DIR": bad},
            capture=tmp_path / "agy.calls", cwd=run_dir,
        )
        assert r.returncode == 2, (bad, r.returncode, r.stderr)
        assert "HMAD_AUDIT_STEM_DIR" in r.stderr, (bad, r.stderr)
        assert "AUDITCYCLE:" not in r.stdout
        assert read_jsonl(assemble_calls) == [], f"{bad!r} must be refused before assembly"
        assert read_jsonl(cycle_calls) == [], f"{bad!r} must be refused before the helper"


def test_divergence_halt_survives_a_regex_metacharacter_stem_dir(tmp_path):
    """Review should-fix: the report paths reach `grep -v -e` as patterns. A stem
    dir holding `[` made grep error out, the filter printed nothing, and the
    prompt_divergence HALT could never fire for that run."""
    root = project_with_docs(tmp_path)
    script_dir, assemble_calls, cycle_calls = install_audit_cycle_stubs(tmp_path)
    stems = tmp_path / "br[acket"
    stems.mkdir()
    r = run_audit_cycle(
        tmp_path, dispatch_args(root=root, passes="2"),
        env={"HMAD_AUDIT_CYCLE_SCRIPT_DIR": str(script_dir),
             "HMAD_AUDIT_STEM_DIR": str(stems),
             "HMAD_ASSEMBLE_DIVERGE_P2": "1"},
        capture=tmp_path / "agy.calls",
    )
    cycle_argv = read_jsonl(cycle_calls)[0]
    assert cycle_argv[cycle_argv.index("--halt-reason") + 1] == "prompt_divergence", (
        r.stdout, r.stderr)
