"""Protect real session state from the test suite.

Every test isolates its pin file by passing `HMAD_ORCA_PIN_FILE`. That isolation
is honoured by ONE branch in `_pin_file`, and J2 made the fallback resolve to the
enclosing repository rather than the cwd — so if that branch ever stops working,
writes land on the developer's live `<repo>/.h-mad/orca-pins.env` instead of a
temp path.

That is not hypothetical. Mutation-testing `_pin_file`'s override branch (the
practice `invariants.base.md` §"Test discrimination" mandates) deleted exactly
that branch and redirected the whole suite's pin writes onto the real file,
replacing two live agent handles with `term_live`/`term_explicit`. The suite
reported 642 passed while doing it: from the tests' point of view nothing was
wrong, because they never assert where the file is NOT.

So the protection belongs here rather than in any single test — snapshot the real
file before the session and restore it after if anything moved it, loudly.
"""
import os
import re
import subprocess
from pathlib import Path

import pytest

# No test reads the host's real `ps`, `git` lane history or `~/.claude` transcripts
# through `h_mad_state_ownership`'s liveness readers (row 1406 review, SF5). Set at
# import, before any test module builds an `env={**os.environ, ...}`, so CLI
# subprocesses inherit it too. Tests of the readers themselves unset it.
os.environ["H_MAD_LIVENESS_CLOCKS_OFF"] = "1"

REPO_ROOT = Path(__file__).resolve().parents[2]


def _live_pin_file() -> Path:
    """The same path `_pin_file` resolves to for an unset override, from here."""
    try:
        root = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return REPO_ROOT / ".h-mad" / "orca-pins.env"
    return Path(root) / ".h-mad" / "orca-pins.env"


@pytest.fixture(scope="session", autouse=True)
def _protect_live_pin_file():
    target = _live_pin_file()
    before = target.read_bytes() if target.is_file() else None
    yield
    after = target.read_bytes() if target.is_file() else None
    # J18 pin-file guard mutation anchor. Distinct from the wire-registry anchor
    # below because `if after == before:` appears once per guard, and the mutation
    # harness refuses any anchor it cannot match exactly once.
    if after == before:
        return
    # Restore first, complain second: a developer's live agent handles matter
    # more than the tidiness of this message.
    if before is None:
        try:
            target.unlink()
        except FileNotFoundError:
            pass
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(before)
    pytest.fail(
        f"the test suite modified the live pin file {target} and it has been "
        "restored. Some test is not isolating HMAD_ORCA_PIN_FILE, or a mutation "
        "disabled the override branch in _pin_file. Re-run `hmad-dispatch env` "
        "to confirm your agent handles.",
        pytrace=False,
    )


def _live_wire_registry_file() -> Path:
    """The repository's real wire registry, independent of the test cwd."""
    try:
        root = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return REPO_ROOT / ".h-mad" / "wires.jsonl"
    return Path(root) / ".h-mad" / "wires.jsonl"


@pytest.fixture(scope="session", autouse=True)
def _protect_live_wire_registry():
    target = _live_wire_registry_file()
    before = target.read_bytes() if target.is_file() else None
    yield
    after = target.read_bytes() if target.is_file() else None
    # J18 guard mutation anchor.
    if after == before:
        return
    if before is None:
        try:
            target.unlink()
        except FileNotFoundError:
            pass
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(before)
    pytest.fail(
        f"the test suite modified the live wire registry {target} and it has been "
        "restored. Some test is not isolating its registry path, or a mutation "
        "disabled the path-redirection branch in the wire registry writer.",
        pytrace=False,
    )


import os

_AMBIENT_HOST_KEYS = ("HPW_AGENT_BACKEND", "HMAD_HOST", "HMAD_CONTEXT_WINDOW")


@pytest.fixture
def hermetic_env():
    """Build a subprocess environment carrying no ambient Claude or host markers."""
    def make(**extra: str) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items()
               if not k.startswith("CLAUDE") and k not in _AMBIENT_HOST_KEYS}
        env.update(extra)
        return env
    return make


@pytest.fixture(autouse=True)
def _hermetic_report_path_claims(monkeypatch, tmp_path):
    """`h_mad_assemble_audit.py --report-file` claims each report path once under
    `$XDG_CACHE_HOME/h-mad/handed` (default `~/.cache/h-mad/handed`), and nothing
    releases a claim. A test that reached the real cache would permanently refuse
    that path for the developer, so every test gets its own."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg-cache"))


@pytest.fixture(autouse=True)
def _hermetic_host_skill_roots(monkeypatch, tmp_path):
    monkeypatch.setenv("HMAD_AGENTS_SKILLS_DIR", str(tmp_path / "absent-agents-skills"))
    monkeypatch.setenv("HMAD_AGY_SKILLS_DIR", str(tmp_path / "absent-agy-skills"))


# `audit-cycle` mints a fresh `/tmp/audit_<feature>_<phase>_cycle<N>_run<ts>-<pid>`
# stem per invocation (claim once, never re-hand a report path), so the verb tests
# no longer overwrite one fixed set of /tmp files: each run leaves new ones, about
# 900 per full suite. Remove the ones THIS session created, and only for the
# synthetic feature names the tests use -- /tmp is shared with live audit runs.
_TEST_RUN_FILE = re.compile(
    r"^audit_(cycle-red|cycle-status|cycle-clear|cycle-docs-.+?|size_status=unverified"
    r"|surf\d+|grok-stale-.+?|handed-.+?|demo)_(plan|design|impl-plan)_cycle[^_]+"
    r"_run\d{8}T\d{6}Z-\d+_p\d+\."
)


def _test_run_files() -> set[Path]:
    return {p for p in Path("/tmp").glob("audit_*_run*") if _TEST_RUN_FILE.match(p.name)}


@pytest.fixture(scope="session", autouse=True)
def _remove_fresh_stem_files_this_run_created():
    before = _test_run_files()
    yield
    for path in _test_run_files() - before:
        path.unlink(missing_ok=True)


@pytest.fixture(scope="session", autouse=True)
def _reap_processes_leaked_by_this_run(tmp_path_factory, request):
    """Reap, at session end, every process whose argv names this run's tmp tree.

    A timed-out `subprocess.run` kills only its direct child; what that child
    started is re-parented to PID 1 and keeps running. One leaked
    `hmad-dispatch.sh exec-pane agy` spun for 22 h against a deleted pytest
    tmpdir (docs/skill-candidates.md, "reap LEAKED exec-pane wrapper
    processes"). The run's basetemp is the positive identifier: the suite points
    every wrapper and stub at a tmp_path, and nothing outside the run does.
    Reaped processes are reported, not hidden — each one is a test that leaked.
    """
    from leak_reaper import find_leaked, reap

    yield
    base = tmp_path_factory.getbasetemp()
    markers = sorted({str(base), str(base.resolve())})
    leaked = find_leaked(markers)
    if not leaked:
        return
    reap([pid for pid, _ in leaked])
    reporter = request.config.pluginmanager.get_plugin("terminalreporter")
    lines = [f"[leak-reaper] reaped {len(leaked)} process(es) leaked under {base}:"]
    lines += [f"[leak-reaper]   pid {pid}: {command[:200]}" for pid, command in leaked]
    for line in lines:
        if reporter is not None:
            reporter.write_line(line, yellow=True)
        else:
            print(line)
