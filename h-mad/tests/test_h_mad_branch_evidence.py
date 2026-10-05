"""`h_mad_branch_evidence.py` collects a worktree executor's evidence from the tree.

Skill-candidates row "collect a worktree executor's evidence mechanically": four
of six worktree executors in one session ended on "Done.", "No action." or
"Nothing new." with no evidence, and one ended "No change." while it had
committed. Each time the orchestrator re-derived the result by hand: the branch
tip, the dirty state, the changed tests, every mutation spec over the changed
scripts. This verb does that from the worktree, so the evidence never depends on
what the agent said.

Most tests drive the script over a tmp git repo with a stub `pytest` package on
PYTHONPATH and a stub harness in `HMAD_BRANCH_EVIDENCE_SCRIPT_DIR`, both logging
start and end to one file, so the run order and the arguments are observable.
One test runs the real harness and the real pytest end to end on a tiny repo.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HMAD = Path(__file__).resolve().parents[1]
SCRIPT = HMAD / "scripts" / "h_mad_branch_evidence.py"
REAL_CONSUMERS = HMAD / "scripts" / "h_mad_doc_consumers.py"
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}

STUB_PYTEST = r'''
import json, os, sys, time
log = os.environ["STUB_LOG"]
files = [a for a in sys.argv[1:] if a.endswith(".py")]
def note(event):
    with open(log, "a") as fh:
        fh.write(json.dumps({"who": "pytest", "event": event, "t": time.time(),
                             "args": files}) + "\n")
note("start")
time.sleep(float(os.environ.get("STUB_SLEEP", "0")))
mode = os.environ.get("STUB_PYTEST", "pass")
note("end")
if mode == "pass":
    print(f"{len(files) * 2} passed in 0.01s")
    sys.exit(0)
if mode == "fail":
    print("FAILED " + files[0] + "::test_x - assert 0")
    print(f"1 failed, {len(files) * 2 - 1} passed in 0.01s")
    sys.exit(1)
if mode == "nosummary":
    print("Segmentation fault")
    sys.exit(0)
if mode == "skipped":
    print(f"{len(files)} skipped in 0.01s")
    sys.exit(0)
if mode == "busy":
    print("SUITE: BUSY holder=4242 age=3s what=pytest-session lock=/x/.h-mad/mutation.lock")
    print("no tests ran in 0.01s")
    sys.exit(75)
if mode == "treemoved":
    print("SUITE: TREE_MOVED paths=h-mad/x.py n=1")
    print(f"{len(files) * 2} passed in 0.01s")
    sys.exit(0)
if mode == "hang":
    time.sleep(120)
if mode == "failquotes":
    # A REAL failure of a test about the suite lock: its assertion quotes the
    # conftest's tokens, and its captured stdout even starts a line with one.
    print("FAILED " + files[0] + "::test_line - AssertionError: assert 'x' == 'SUITE: BUSY holder=1'")
    print("E       AssertionError: assert 'x' == 'SUITE: TREE_MOVED paths=a n=1'")
    print("----------------------------- Captured stdout call -----------------------------")
    print("SUITE: BUSY holder=1 age=1s what=pytest-session lock=x")
    print("SUITE: TREE_MOVED paths=a n=1 (quoted by the test, not the conftest)")
    print(f"1 failed, {len(files) * 2 - 1} passed in 0.01s")
    sys.exit(1)
sys.exit(3)
'''

STUB_HARNESS = r'''
import json, os, sys, time
log = os.environ["STUB_LOG"]
args = sys.argv[1:]
who = "anchors" if "--check-anchors" in args else "harness"
def note(event):
    with open(log, "a") as fh:
        fh.write(json.dumps({"who": who, "event": event, "t": time.time(),
                             "args": [a for a in args if a != "--check-anchors"]}) + "\n")
note("start")
time.sleep(float(os.environ.get("STUB_SLEEP", "0")))
if who == "harness" and os.environ.get("STUB_MUTATION") == "HANG":
    # A real harness mid-run: a mutant on disk, a pytest grandchild that ignores
    # SIGTERM, and a restore that runs only on SIGTERM/SIGINT (never on SIGKILL).
    import pathlib, signal, subprocess
    target = pathlib.Path("h-mad", "scripts", "tool.py")
    original = target.read_text()
    target.write_text("MUTANT\n")
    grandchild = subprocess.Popen([sys.executable, "-c",
        "import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(300)"])
    def restore(*_):
        target.write_text(original)
        sys.exit(143)
    signal.signal(signal.SIGTERM, restore)
    signal.signal(signal.SIGINT, restore)
    with open(log, "a") as fh:
        fh.write(json.dumps({"who": "harness", "event": "hanging", "t": time.time(),
                             "args": [], "grandchild": grandchild.pid}) + "\n")
    time.sleep(120)
note("end")
if who == "anchors":
    word = os.environ.get("STUB_ANCHORS", "ANCHORS_OK")
    if word == "NOTOKEN":
        sys.exit(1)
    n = len(args) - 1
    print(f"ANCHORS: {word} specs={n} mutations={n} ok={n} drifted=0 unreadable=0 skipped=0 unclassifiable=0")
    sys.exit(0)
word = os.environ.get("STUB_MUTATION", "ALL_CAUGHT")
if word == "NOTOKEN":
    print("Traceback (most recent call last):")
    sys.exit(1)
print(f"MUTATION: {word} mutations=1 caught=1 survived=0 refused=0 unreadable=0")
if word == "SURVIVED":
    print("  survived: stub-mutant")
    print("  a mutation the suite did not notice is a guard that does not bite")
sys.exit(0)
'''

SPEC = {
    "root": "../..",
    "command": ["python3", "-m", "pytest", "tests/test_tool.py", "-q"],
    "target_command": ["python3", "-m", "pytest", "-q"],
    "mutations": [{"name": "m", "file": "scripts/tool.py", "find": "return 1\n",
                   "replace": "return 0\n", "test": "tests/test_tool.py::test_tool"}],
}


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, text=True,
                          env={**os.environ, **GIT_ENV}, capture_output=True).stdout


def _write(repo: Path, files: dict[str, str]) -> None:
    for rel, body in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")


def _commit(repo: Path, files: dict[str, str], msg: str = "c") -> None:
    _write(repo, files)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)


def _base_repo(tmp_path: Path) -> Path:
    """main: a script, its test, an unrelated test, a document and its reader."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _commit(repo, {
        "h-mad/scripts/tool.py": "def tool():\n    return 1\n",
        "h-mad/scripts/other.py": "def other():\n    return 2\n",
        "h-mad/tests/test_tool.py": "from tool import tool\ndef test_tool(): assert tool() == 1\n",
        "h-mad/tests/test_other.py": "from other import other\ndef test_other(): pass\n",
        "h-mad/tests/test_docs.py": 'DOC = HERE / "SKILL.md"\ndef test_docs(): pass\n',
        # Names `toolkit`, never `tool`: a raw substring match would select it.
        "h-mad/tests/test_toolkit.py": "from toolkit import kit\ndef test_kit(): pass\n",
        "h-mad/SKILL.md": "# skill\n",
    }, "base")
    _git(repo, "checkout", "-q", "-b", "feat")
    return repo


@pytest.fixture
def stubs(tmp_path: Path) -> dict:
    pkg = tmp_path / "stubpath" / "pytest"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "__main__.py").write_text(STUB_PYTEST, encoding="utf-8")
    scripts = tmp_path / "stubscripts"
    scripts.mkdir()
    (scripts / "h_mad_mutation_harness.py").write_text(STUB_HARNESS, encoding="utf-8")
    shutil.copy(REAL_CONSUMERS, scripts / "h_mad_doc_consumers.py")
    log = tmp_path / "stub.log"
    env = {**os.environ, "PYTHONPATH": str(pkg.parent),
           "HMAD_BRANCH_EVIDENCE_SCRIPT_DIR": str(scripts), "STUB_LOG": str(log)}
    return {"env": env, "log": log}


def _run(target: str | Path, env: dict, *args: str, cwd: Path | None = None,
         **extra: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), str(target), *args],
                          capture_output=True, text=True, env={**env, **extra},
                          cwd=str(cwd) if cwd else None, timeout=300)


def _events(log: Path) -> list[dict]:
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]


def _verdict(proc: subprocess.CompletedProcess) -> str:
    lines = proc.stdout.rstrip().splitlines()
    assert lines, proc.stderr
    assert lines[-1].startswith("EVIDENCE-VERDICT: "), proc.stdout + proc.stderr
    return lines[-1]


def _full_feature(repo: Path) -> None:
    """A complete executor commit: script change, its test, a spec targeting it."""
    _commit(repo, {
        "h-mad/scripts/tool.py": "def tool():\n    # changed\n    return 1\n",
        "h-mad/tests/test_tool.py": "from tool import tool\ndef test_tool(): assert tool() == 1\n# more\n",
        "h-mad/tests/mutation-specs/tool.json": json.dumps(SPEC, indent=2),
    }, "feat: change tool")


def test_committed_branch_reports_sha_and_ahead(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _full_feature(repo)
    tip = _git(repo, "rev-parse", "HEAD").strip()
    base = _git(repo, "rev-parse", "main").strip()

    proc = _run(repo, stubs["env"])

    first = proc.stdout.splitlines()[0]
    assert first == f"EVIDENCE: sha={tip[:9]} base={base[:9]} ahead=1 dirty=0", proc.stdout
    assert f"{tip[:9]} feat: change tool" in proc.stdout, "the commit beyond base is listed"
    assert "h-mad/scripts/tool.py" in proc.stdout, "the changed script is named"
    assert _verdict(proc) == "EVIDENCE-VERDICT: COMPLETE", proc.stdout
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_dirty_tree_is_INCOMPLETE(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _full_feature(repo)
    (repo / "h-mad" / "scratch.txt").write_text("untracked\n", encoding="utf-8")

    proc = _run(repo, stubs["env"])

    assert proc.stdout.splitlines()[0].endswith("ahead=1 dirty=1"), proc.stdout
    assert "?? h-mad/scratch.txt" in proc.stdout, "the dirty entry is named"
    assert _verdict(proc) == "EVIDENCE-VERDICT: INCOMPLETE reason=dirty"
    assert _events(stubs["log"]) == [], "a dirty tree is not a sha: nothing is measured"


def test_no_commits_is_INCOMPLETE(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)

    proc = _run(repo, stubs["env"])

    assert "ahead=0 dirty=0" in proc.stdout.splitlines()[0], proc.stdout
    assert _verdict(proc) == "EVIDENCE-VERDICT: INCOMPLETE reason=no-commits"
    assert _events(stubs["log"]) == []


def test_changed_tests_are_the_pytest_set(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _commit(repo, {
        "h-mad/scripts/tool.py": "def tool():\n    # changed\n    return 1\n",
        "h-mad/tests/test_new.py": "def test_new(): pass\n",
        "h-mad/tests/mutation-specs/tool.json": json.dumps(SPEC),
    })

    proc = _run(repo, stubs["env"])

    runs = [e["args"] for e in _events(stubs["log"]) if e["who"] == "pytest" and e["event"] == "start"]
    assert runs == [["h-mad/tests/test_new.py", "h-mad/tests/test_tool.py"]], runs
    assert "test_other.py" not in proc.stdout, "a test that reads no changed script is not run"
    assert "TESTS: PASS files=2 passed=4" in proc.stdout, proc.stdout
    assert _verdict(proc) == "EVIDENCE-VERDICT: COMPLETE"


def test_failing_tests_are_INCOMPLETE_and_name_the_failure(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _full_feature(repo)

    proc = _run(repo, stubs["env"], STUB_PYTEST="fail")

    assert "TESTS: FAIL files=1 failed=1 errors=0" in proc.stdout, proc.stdout
    assert "FAILED h-mad/tests/test_tool.py::test_x" in proc.stdout
    assert _verdict(proc) == "EVIDENCE-VERDICT: INCOMPLETE reason=tests-failed"


@pytest.mark.parametrize("mode,reason", [("nosummary", "pytest-no-summary"),
                                         ("crash", "pytest-rc3")])
def test_pytest_crash_is_UNREADABLE_never_clean(tmp_path: Path, stubs: dict,
                                                 mode: str, reason: str) -> None:
    repo = _base_repo(tmp_path)
    _full_feature(repo)

    proc = _run(repo, stubs["env"], STUB_PYTEST=mode)

    assert f"TESTS: UNREADABLE reason={reason}" in proc.stdout, proc.stdout
    assert _verdict(proc) == f"EVIDENCE-VERDICT: UNREADABLE reason=tests-{reason}"
    assert proc.returncode == 2, proc.stdout + proc.stderr


def test_missing_pytest_is_UNREADABLE(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _full_feature(repo)
    init = Path(stubs["env"]["PYTHONPATH"]) / "pytest" / "__init__.py"
    init.write_text("raise ImportError('no pytest here')\n", encoding="utf-8")

    proc = _run(repo, stubs["env"])

    assert "TESTS: UNREADABLE reason=pytest-missing" in proc.stdout, proc.stdout
    assert _verdict(proc).startswith("EVIDENCE-VERDICT: UNREADABLE")


def test_changed_spec_is_run_and_its_verdict_forwarded(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    # A spec already on the base that targets a script the branch changes is run
    # too, not only the specs the branch itself adds.
    _git(repo, "checkout", "-q", "main")
    _commit(repo, {"h-mad/tests/specs/other.mutation.json": json.dumps(
        {**SPEC, "mutations": [{**SPEC["mutations"][0], "file": "scripts/other.py"}]})}, "spec")
    _git(repo, "checkout", "-q", "-B", "feat")
    _commit(repo, {"h-mad/scripts/other.py": "def other():\n    return 3\n",
                   "h-mad/tests/test_other.py": "from other import other\ndef test_other(): pass\n#\n",
                   "h-mad/tests/mutation-specs/tool.json": json.dumps(SPEC)}, "other")

    proc = _run(repo, stubs["env"], STUB_MUTATION="SURVIVED")

    harness = [e["args"] for e in _events(stubs["log"]) if e["who"] == "harness" and e["event"] == "start"]
    assert harness == [["h-mad/tests/mutation-specs/tool.json"],
                       ["h-mad/tests/specs/other.mutation.json"]], harness
    assert "MUTATION: h-mad/tests/mutation-specs/tool.json SURVIVED mutations=1" in proc.stdout, proc.stdout
    assert "  survived: stub-mutant" in proc.stdout, "which mutant survived is forwarded"
    assert "guard that does not bite" not in proc.stdout, "only the named rows, not the prose"
    assert _verdict(proc) == "EVIDENCE-VERDICT: INCOMPLETE reason=mutation-survived"


def test_prod_change_without_test_is_INCOMPLETE(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _commit(repo, {"h-mad/scripts/tool.py": "def tool():\n    # c\n    return 1\n",
                   "h-mad/tests/mutation-specs/tool.json": json.dumps(SPEC)})

    proc = _run(repo, stubs["env"])

    assert _verdict(proc) == "EVIDENCE-VERDICT: INCOMPLETE reason=no-tests", proc.stdout


def test_prod_change_without_spec_is_INCOMPLETE_unless_waived(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _commit(repo, {"h-mad/scripts/tool.py": "def tool():\n    # c\n    return 1\n",
                   "h-mad/tests/test_tool.py": "from tool import tool\ndef test_tool(): pass\n#\n"})

    proc = _run(repo, stubs["env"])
    assert "UNSPECCED: h-mad/scripts/tool.py" in proc.stdout, proc.stdout
    assert _verdict(proc) == "EVIDENCE-VERDICT: INCOMPLETE reason=no-mutation-spec"

    waived = _run(repo, stubs["env"], "--no-mutation")
    assert _verdict(waived) == "EVIDENCE-VERDICT: COMPLETE waived=no-mutation", waived.stdout


@pytest.mark.parametrize("word", ["BUSY", "UNREADABLE", "TREE_MOVED", "RESTORE_FAILED", "NOTOKEN"])
def test_child_busy_or_unreadable_never_COMPLETE(tmp_path: Path, stubs: dict, word: str) -> None:
    repo = _base_repo(tmp_path)
    _full_feature(repo)

    proc = _run(repo, stubs["env"], STUB_MUTATION=word)

    assert _verdict(proc).startswith("EVIDENCE-VERDICT: UNREADABLE reason=mutation-"), proc.stdout
    assert proc.returncode == 2, proc.stdout + proc.stderr


@pytest.mark.parametrize("word,verdict", [
    ("ANCHORS_DRIFTED", "EVIDENCE-VERDICT: INCOMPLETE reason=anchors-drifted"),
    ("ANCHORS_UNREADABLE", "EVIDENCE-VERDICT: UNREADABLE reason=anchors-unreadable"),
])
def test_anchor_verdict_is_forwarded_and_never_clean(tmp_path: Path, stubs: dict,
                                                      word: str, verdict: str) -> None:
    repo = _base_repo(tmp_path)
    _full_feature(repo)

    proc = _run(repo, stubs["env"], STUB_ANCHORS=word)

    assert f"ANCHORS: {word} specs=1" in proc.stdout, proc.stdout
    assert _verdict(proc) == verdict


def test_steps_run_sequentially_not_concurrently(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _full_feature(repo)
    _commit(repo, {"h-mad/SKILL.md": "# skill, edited\n",
                   "h-mad/tests/mutation-specs/second.json": json.dumps(SPEC)}, "doc")

    proc = _run(repo, stubs["env"], STUB_SLEEP="0.3")

    events = _events(stubs["log"])
    order = [(e["who"], e["event"]) for e in events]
    assert order == [("pytest", "start"), ("pytest", "end"),      # TESTS
                     ("pytest", "start"), ("pytest", "end"),      # CONSUMERS-RUN
                     ("anchors", "start"), ("anchors", "end"),
                     ("harness", "start"), ("harness", "end"),
                     ("harness", "start"), ("harness", "end")], order
    for prev, nxt in zip(events, events[1:]):
        assert prev["t"] <= nxt["t"], "a step started before the previous one ended"
    assert _verdict(proc) == "EVIDENCE-VERDICT: COMPLETE", proc.stdout


def test_doc_change_invokes_consumers_run(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _commit(repo, {"h-mad/SKILL.md": "# skill, edited\n"}, "doc only")

    proc = _run(repo, stubs["env"])

    runs = [e["args"] for e in _events(stubs["log"]) if e["who"] == "pytest" and e["event"] == "start"]
    assert runs == [["h-mad/tests/test_docs.py"]], runs
    assert "TESTS: NONE" in proc.stdout, proc.stdout
    assert "CONSUMERS-RUN: PASS files=1 passed=2" in proc.stdout
    assert _verdict(proc) == "EVIDENCE-VERDICT: COMPLETE"

    failing = _run(repo, stubs["env"], STUB_PYTEST="fail")
    assert "CONSUMERS-RUN: FAIL files=1 failed=1" in failing.stdout, failing.stdout
    assert _verdict(failing) == "EVIDENCE-VERDICT: INCOMPLETE reason=consumers-failed"


def test_unknown_base_is_UNREADABLE(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _full_feature(repo)

    proc = _run(repo, stubs["env"], "--base", "no-such-branch")

    assert _verdict(proc) == "EVIDENCE-VERDICT: UNREADABLE reason=unknown-base"
    assert proc.returncode == 2, proc.stdout + proc.stderr


def test_branch_name_resolves_to_its_worktree(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _git(repo, "checkout", "-q", "main")
    wt = tmp_path / "wt"
    _git(repo, "worktree", "add", "-q", str(wt), "feat")
    _full_feature(wt)
    tip = _git(wt, "rev-parse", "HEAD").strip()

    proc = _run("feat", stubs["env"], cwd=repo)

    assert proc.stdout.splitlines()[0].startswith(f"EVIDENCE: sha={tip[:9]} "), proc.stdout
    assert f"worktree={wt.resolve()}" in proc.stdout
    assert _verdict(proc) == "EVIDENCE-VERDICT: COMPLETE"

    missing = _run("no-such-branch", stubs["env"], cwd=repo)
    assert _verdict(missing) == "EVIDENCE-VERDICT: UNREADABLE reason=no-worktree"


def _snapshot(repo: Path) -> tuple[str, str, dict]:
    status = _git(repo, "status", "--porcelain", "--ignored", "--untracked-files=all")
    files = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(repo.rglob("*")) if p.is_file() and ".git" not in p.parts}
    return _git(repo, "rev-parse", "HEAD"), status, files


def test_collection_never_modifies_the_worktree(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _full_feature(repo)
    _commit(repo, {"h-mad/SKILL.md": "# skill, edited\n"}, "doc")
    before = _snapshot(repo)

    proc = _run(repo, stubs["env"])

    assert _verdict(proc) == "EVIDENCE-VERDICT: COMPLETE", proc.stdout
    assert _snapshot(repo) == before, "the collector wrote into the worktree it measures"


def test_tree_moved_during_collection_is_UNREADABLE(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _full_feature(repo)
    harness = Path(stubs["env"]["HMAD_BRANCH_EVIDENCE_SCRIPT_DIR"]) / "h_mad_mutation_harness.py"
    harness.write_text(
        "import os, pathlib, sys\n"
        "if '--check-anchors' in sys.argv:\n"
        "    print('ANCHORS: ANCHORS_OK specs=1')\n"
        "else:\n"
        "    pathlib.Path(os.getcwd(), 'h-mad', 'moved.txt').write_text('x')\n", encoding="utf-8")

    proc = _run(repo, stubs["env"])

    # tree-moved leads, and the child's own missing token is not erased by it.
    assert _verdict(proc) == "EVIDENCE-VERDICT: UNREADABLE reason=tree-moved,mutation-no-token", proc.stdout


def test_end_to_end_real_pytest_and_harness_on_a_tiny_repo(tmp_path: Path) -> None:
    repo = tmp_path / "tiny"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _commit(repo, {"pkg/scripts/tool.py": "def tool(x):\n    return x + 1\n",
                   "pkg/README.md": "# tiny\n"}, "base")
    _git(repo, "checkout", "-q", "-b", "feat")
    # No `-p no:cacheprovider` here: the collector's own environment must keep the
    # harness's pytest from writing .pytest_cache into the tree it measures.
    py = [sys.executable, "-m", "pytest", "-q"]
    spec = {"root": "../..", "command": [*py, "tests/test_tool.py"], "target_command": py,
            "mutations": [{"name": "drop-guard", "file": "scripts/tool.py",
                           "find": "    if x < 0:\n        raise ValueError(x)\n", "replace": "",
                           "test": "tests/test_tool.py::test_negative_is_refused"}]}
    _commit(repo, {
        "pkg/scripts/tool.py": "def tool(x):\n    if x < 0:\n        raise ValueError(x)\n    return x + 1\n",
        "pkg/tests/test_tool.py": (
            "import sys, pathlib, pytest\n"
            "sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))\n"
            "from tool import tool\n"
            "def test_adds(): assert tool(1) == 2\n"
            "def test_negative_is_refused():\n"
            "    with pytest.raises(ValueError):\n"
            "        tool(-1)\n"),
        "pkg/tests/mutation-specs/tool.json": json.dumps(spec, indent=2),
        "pkg/README.md": "# tiny, edited\n",
    }, "feat: refuse negatives")
    before = _snapshot(repo)
    env = {k: v for k, v in os.environ.items()
           if k not in ("HMAD_BRANCH_EVIDENCE_SCRIPT_DIR", "PYTHONPATH",
                        "PYTHONDONTWRITEBYTECODE", "PYTEST_ADDOPTS")}
    # Strip EVERY variable the collector sets for its children. This test runs under
    # the collector itself when it is dogfooded (the harness inherits them), and an
    # inherited value hides a collector that stopped setting it: measured twice,
    # once per variable (`children-write-bytecode`, `pytest-writes-its-cache`).

    proc = _run(repo, env)

    out = proc.stdout
    assert "TESTS: PASS files=1 passed=2" in out, out + proc.stderr
    assert "CONSUMERS-RUN: NONE" in out, out
    assert "ANCHORS: ANCHORS_OK specs=1" in out, out
    assert "MUTATION: pkg/tests/mutation-specs/tool.json ALL_CAUGHT" in out, out
    assert _verdict(proc) == "EVIDENCE-VERDICT: COMPLETE", out
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _snapshot(repo) == before, "the real harness run left the tree changed"


# --- review round 1 (90a78d05): every must-fix and should-fix has a test below ---


def _started(log: Path, who: str) -> list[list[str]]:
    return [e["args"] for e in _events(log) if e["who"] == who and e["event"] == "start"]


def _alive(pid: int) -> bool:
    import time
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        time.sleep(0.1)
    return True


def test_deleted_script_runs_the_tests_that_name_it(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _git(repo, "rm", "-q", "h-mad/scripts/tool.py")
    _git(repo, "commit", "-q", "-m", "delete tool")

    proc = _run(repo, stubs["env"])

    assert "deleted h-mad/scripts/tool.py" in proc.stdout, proc.stdout
    assert _started(stubs["log"], "pytest") == [["h-mad/tests/test_tool.py"]], proc.stdout
    assert "TESTS: PASS files=1" in proc.stdout


@pytest.mark.parametrize("victim", ["h-mad/tests/test_other.py",
                                    "h-mad/tests/mutation-specs/tool.json"])
def test_deleted_test_or_spec_is_INCOMPLETE(tmp_path: Path, stubs: dict, victim: str) -> None:
    repo = _base_repo(tmp_path)
    _git(repo, "checkout", "-q", "main")
    _commit(repo, {"h-mad/tests/mutation-specs/tool.json": json.dumps(SPEC)}, "spec")
    _git(repo, "checkout", "-q", "-B", "feat")
    _git(repo, "rm", "-q", victim)
    _git(repo, "commit", "-q", "-m", "delete a guard")

    proc = _run(repo, stubs["env"])

    assert f"DELETED-GUARD: {victim}" in proc.stdout, proc.stdout
    assert _verdict(proc) == "EVIDENCE-VERDICT: INCOMPLETE reason=deleted-guard"


def test_conftest_change_runs_every_test_under_it(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _commit(repo, {"h-mad/tests/conftest.py": "import pytest\n"}, "conftest")

    proc = _run(repo, stubs["env"])

    assert _started(stubs["log"], "pytest") == [[
        "h-mad/tests/test_docs.py", "h-mad/tests/test_other.py",
        "h-mad/tests/test_tool.py", "h-mad/tests/test_toolkit.py"]], proc.stdout
    assert "TESTS: PASS files=4" in proc.stdout


def test_harness_timeout_restores_the_tree_and_kills_the_group(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _full_feature(repo)
    before = _snapshot(repo)
    import time
    started = time.time()

    proc = _run(repo, stubs["env"], "--child-timeout", "3", STUB_MUTATION="HANG")

    # The harness restored and exited at once; an orphan holding its stdout pipe
    # must not stretch that into the whole SIGTERM grace (30 s).
    assert time.time() - started < 20, "the stop waited on the orphan's pipe, not the child"
    assert "MUTATION: h-mad/tests/mutation-specs/tool.json UNREADABLE reason=timeout" in proc.stdout, proc.stdout
    assert "TREE: UNCHANGED" in proc.stdout, "the harness was killed before it could restore"
    assert _verdict(proc) == "EVIDENCE-VERDICT: UNREADABLE reason=mutation-timeout"
    assert _snapshot(repo) == before
    hanging = [e for e in _events(stubs["log"]) if e["event"] == "hanging"]
    assert hanging and not _alive(hanging[0]["grandchild"]), "an orphan pytest kept running"


@pytest.mark.parametrize("sig", ["SIGINT", "SIGTERM"])
def test_interrupt_restores_the_tree_and_reports_UNREADABLE(tmp_path: Path, stubs: dict, sig: str) -> None:
    import signal
    import time
    repo = _base_repo(tmp_path)
    _full_feature(repo)
    before = _snapshot(repo)
    tool = subprocess.Popen([sys.executable, str(SCRIPT), str(repo)], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True,
                            env={**stubs["env"], "STUB_MUTATION": "HANG"})
    deadline = time.time() + 60
    while not [e for e in _events(stubs["log"]) if e["event"] == "hanging"]:
        assert time.time() < deadline and tool.poll() is None, "harness stub never started"
        time.sleep(0.1)

    tool.send_signal(getattr(signal, sig))
    out, err = tool.communicate(timeout=60)

    assert out.rstrip().splitlines()[-1] == "EVIDENCE-VERDICT: UNREADABLE reason=interrupted", out + err
    assert tool.returncode == 2, out + err
    assert _snapshot(repo) == before, "the mutant was left in the tree"
    hanging = [e for e in _events(stubs["log"]) if e["event"] == "hanging"]
    assert not _alive(hanging[0]["grandchild"]), "an orphan pytest kept running"


def test_test_files_outside_a_tests_directory_are_tests(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _git(repo, "checkout", "-q", "main")
    _commit(repo, {"handoff/scripts/learn.py": "def learn():\n    return 1\n",
                   "handoff/scripts/test_learn.py": "from learn import learn\ndef test_learn(): pass\n"},
            "handoff")
    _git(repo, "checkout", "-q", "-B", "feat")
    learn_spec = {**SPEC, "mutations": [{**SPEC["mutations"][0], "file": "scripts/learn.py"}]}
    _commit(repo, {"handoff/scripts/learn.py": "def learn():\n    return 2\n",
                   "handoff/scripts/test_learn.py": "from learn import learn\ndef test_learn(): pass\n#\n",
                   "handoff/tests/mutation-specs/learn.json": json.dumps(learn_spec)}, "learn")

    proc = _run(repo, stubs["env"])

    assert "test handoff/scripts/test_learn.py" in proc.stdout, proc.stdout
    assert _started(stubs["log"], "pytest") == [["handoff/scripts/test_learn.py"]]
    assert _verdict(proc) == "EVIDENCE-VERDICT: COMPLETE"


def test_no_mutation_waives_only_the_missing_spec(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _git(repo, "checkout", "-q", "main")
    _commit(repo, {"h-mad/tests/mutation-specs/tool.json": json.dumps(SPEC)}, "spec")
    _git(repo, "checkout", "-q", "-B", "feat")
    _commit(repo, {"h-mad/scripts/tool.py": "def tool():\n    # c\n    return 1\n",
                   "h-mad/scripts/other.py": "def other():\n    return 3\n",
                   "h-mad/tests/test_tool.py": "from tool import tool\ndef test_tool(): pass\n#\n"})

    proc = _run(repo, stubs["env"], "--no-mutation", STUB_MUTATION="SURVIVED")

    assert "UNSPECCED: h-mad/scripts/other.py" in proc.stdout, proc.stdout
    assert _started(stubs["log"], "harness") == [["h-mad/tests/mutation-specs/tool.json"]], \
        "the waiver skipped a spec that exists"
    assert _verdict(proc) == "EVIDENCE-VERDICT: INCOMPLETE reason=mutation-survived"


def test_spec_over_a_changed_document_is_anchor_checked_not_run(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _git(repo, "checkout", "-q", "main")
    doc_spec = {**SPEC, "mutations": [{**SPEC["mutations"][0], "file": "SKILL.md",
                                       "find": "# skill\n"}]}
    _commit(repo, {"h-mad/tests/mutation-specs/doc.json": json.dumps(doc_spec)}, "doc spec")
    _git(repo, "checkout", "-q", "-B", "feat")
    _commit(repo, {"h-mad/SKILL.md": "# skill\nmore\n"}, "doc")

    proc = _run(repo, stubs["env"])

    assert "h-mad/tests/mutation-specs/doc.json (anchors only)" in proc.stdout, proc.stdout
    assert _started(stubs["log"], "anchors") == [["h-mad/tests/mutation-specs/doc.json"]]
    assert _started(stubs["log"], "harness") == [], "a document's spec ran its whole mutation pass"
    assert "MUTATION: NONE specs=0" in proc.stdout
    assert _verdict(proc) == "EVIDENCE-VERDICT: COMPLETE"


@pytest.mark.parametrize("mode,reason", [("busy", "tests-suite-busy"),
                                         ("treemoved", "tests-suite-tree-moved")])
def test_suite_busy_and_tree_moved_are_named(tmp_path: Path, stubs: dict,
                                             mode: str, reason: str) -> None:
    repo = _base_repo(tmp_path)
    _full_feature(repo)

    proc = _run(repo, stubs["env"], STUB_PYTEST=mode)

    assert _verdict(proc) == f"EVIDENCE-VERDICT: UNREADABLE reason={reason}", proc.stdout
    assert proc.returncode == 2, proc.stdout + proc.stderr


def test_a_directory_that_is_not_a_worktree_toplevel_is_UNREADABLE(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _full_feature(repo)
    ghost = repo / ".claude" / "worktrees" / "agent-ghost"
    ghost.mkdir(parents=True)

    proc = _run(ghost, stubs["env"])

    assert _verdict(proc) == "EVIDENCE-VERDICT: UNREADABLE reason=not-a-worktree", proc.stdout
    assert _events(stubs["log"]) == [], "it measured the enclosing checkout"


def test_extensionless_script_is_code(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _git(repo, "checkout", "-q", "main")
    _commit(repo, {"h-mad/git-hooks/pre-push": "#!/bin/sh\nexit 0\n"}, "hook")
    _git(repo, "checkout", "-q", "-B", "feat")
    _commit(repo, {"h-mad/git-hooks/pre-push": "#!/bin/sh\nexit 1\n"}, "hook change")

    proc = _run(repo, stubs["env"])

    assert "prod h-mad/git-hooks/pre-push" in proc.stdout, proc.stdout
    assert _verdict(proc) == "EVIDENCE-VERDICT: INCOMPLETE reason=no-tests,no-mutation-spec"


def test_all_skipped_is_UNREADABLE_never_PASS(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _full_feature(repo)

    proc = _run(repo, stubs["env"], STUB_PYTEST="skipped")

    assert "TESTS: UNREADABLE reason=pytest-inconsistent" in proc.stdout, proc.stdout
    assert _verdict(proc) == "EVIDENCE-VERDICT: UNREADABLE reason=tests-pytest-inconsistent"


def test_pytest_timeout_is_UNREADABLE(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _full_feature(repo)

    proc = _run(repo, stubs["env"], "--child-timeout", "2", STUB_PYTEST="hang")

    assert "TESTS: UNREADABLE reason=pytest-timeout" in proc.stdout, proc.stdout
    assert _verdict(proc).startswith("EVIDENCE-VERDICT: UNREADABLE reason=tests-pytest-timeout")


def test_missing_anchors_token_is_UNREADABLE(tmp_path: Path, stubs: dict) -> None:
    repo = _base_repo(tmp_path)
    _full_feature(repo)

    proc = _run(repo, stubs["env"], STUB_ANCHORS="NOTOKEN")

    assert "ANCHORS: UNREADABLE reason=no-token" in proc.stdout, proc.stdout
    assert _verdict(proc) == "EVIDENCE-VERDICT: UNREADABLE reason=anchors-no-token"


STUB_CONSUMERS = r'''
import json, os, sys, time
with open(os.environ["STUB_LOG"], "a") as fh:
    fh.write(json.dumps({"who": "consumers", "event": "start", "t": time.time(),
                         "args": sys.argv[1:]}) + "\n")
case = os.environ["STUB_CONSUMERS"]
print("CONSUMERS: h-mad/SKILL.md n=1")
if case == "UNKNOWN":
    print("CONSUMERS-RUN: UNREADABLE reason=unknown-docs missing=h-mad/SKILL.md")
elif case == "TIMEOUT":
    print("CONSUMERS-RUN: UNREADABLE reason=timeout after=5s")
elif case == "BUSY":
    sys.stderr.write("SUITE: BUSY holder=1 age=1s what=pytest-session lock=x\n")
    print('CONSUMERS-RUN: UNREADABLE reason=incomplete rc=75 summary="no tests ran"')
elif case == "NONE":
    print("CONSUMERS-RUN: NONE")
sys.exit(0 if case in ("NONE", "NOTOKEN") else 2)
'''


@pytest.mark.parametrize("case,verdict", [
    ("UNKNOWN", "EVIDENCE-VERDICT: UNREADABLE reason=consumers-unknown-docs"),
    ("TIMEOUT", "EVIDENCE-VERDICT: UNREADABLE reason=consumers-timeout"),
    ("BUSY", "EVIDENCE-VERDICT: UNREADABLE reason=consumers-suite-busy"),
    ("NOTOKEN", "EVIDENCE-VERDICT: UNREADABLE reason=consumers-no-token"),
    ("NONE", "EVIDENCE-VERDICT: COMPLETE"),
])
def test_consumer_run_token_is_forwarded_and_never_clean(tmp_path: Path, stubs: dict,
                                                         case: str, verdict: str) -> None:
    repo = _base_repo(tmp_path)
    _commit(repo, {"h-mad/SKILL.md": "# skill, edited\n"}, "doc")
    stub = Path(stubs["env"]["HMAD_BRANCH_EVIDENCE_SCRIPT_DIR"]) / "h_mad_doc_consumers.py"
    stub.write_text(STUB_CONSUMERS, encoding="utf-8")

    proc = _run(repo, stubs["env"], STUB_CONSUMERS=case)

    calls = _started(stubs["log"], "consumers")
    assert len(calls) == 1 and "--run" in calls[0], calls
    assert calls[0][-1] == "h-mad/SKILL.md", "documents go to the one --run contract"
    assert _verdict(proc) == verdict, proc.stdout


# --- review round 2 (e22381ab) ---


def test_real_failure_quoting_the_suite_tokens_reads_FAIL(tmp_path: Path, stubs: dict) -> None:
    """N1: a genuine FAIL in a suite-lock test quotes `SUITE: BUSY` / `SUITE: TREE_MOVED`;
    only the conftest's own signal (its line AND exit 75) means the suite was busy."""
    repo = _base_repo(tmp_path)
    _full_feature(repo)

    proc = _run(repo, stubs["env"], STUB_PYTEST="failquotes")

    assert "TESTS: FAIL files=1 failed=1 errors=0" in proc.stdout, proc.stdout
    assert _verdict(proc) == "EVIDENCE-VERDICT: INCOMPLETE reason=tests-failed"


def test_repo_root_conftest_runs_every_test_in_testpaths(tmp_path: Path, stubs: dict) -> None:
    """N2: a root conftest (the suite-lock entry point) is test infrastructure for the
    whole `testpaths` selection, never a script needing its own test and spec."""
    repo = _base_repo(tmp_path)
    _git(repo, "checkout", "-q", "main")
    _commit(repo, {"pytest.ini": "[pytest]\ntestpaths = h-mad/tests handoff/scripts\n",
                   "conftest.py": "import pytest\n",
                   "handoff/scripts/learn.py": "def learn():\n    return 1\n",
                   "handoff/scripts/test_learn.py": "def test_learn(): pass\n",
                   "other/tests/test_outside.py": "def test_outside(): pass\n"}, "root conftest")
    _git(repo, "checkout", "-q", "-B", "feat")
    _commit(repo, {"conftest.py": "import pytest\n\n@pytest.fixture(autouse=True)\ndef boom(): raise RuntimeError\n"},
            "break every test")

    proc = _run(repo, stubs["env"])

    assert "support conftest.py" in proc.stdout, proc.stdout
    assert "UNSPECCED" not in proc.stdout, "a conftest is not a script"
    assert _started(stubs["log"], "pytest") == [[
        "h-mad/tests/test_docs.py", "h-mad/tests/test_other.py", "h-mad/tests/test_tool.py",
        "h-mad/tests/test_toolkit.py", "handoff/scripts/test_learn.py"]], proc.stdout
    assert _verdict(proc) == "EVIDENCE-VERDICT: COMPLETE"
