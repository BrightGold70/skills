"""`h_mad_live_runs.py` names the h-mad runs live elsewhere before a skill change lands.

Skill-candidates row "check for a live run before merging a shared skill change":
`~/.claude/skills/h-mad` is a symlink into this repo, so a change here alters the
installed skill in every session at once. `3219bdd` landed while a HemaSuite run was
mid-cycle and "silently invalidated a batch-18 decision". The check is a warning naming
the lanes, never a block: whether to hold is the operator's judgement.

State records are produced by the real writer (`h_mad_state_write.py`), not
hand-written, so the fixture has the shape the running system writes.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "h_mad_live_runs.py"
WRITER = SCRIPTS / "h_mad_state_write.py"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def _project(root: Path, feature: str, session: str | None, age_hours: float = 0) -> Path:
    state = root / "docs" / ".bkit-memory.json"
    state.parent.mkdir(parents=True, exist_ok=True)
    if not state.exists():
        state.write_text("{}", encoding="utf-8")
    args = [sys.executable, str(WRITER), str(state), "--feature", feature, "--create"]
    if session:
        args += ["--claim", session]
    subprocess.run(args, check=True, capture_output=True)
    if age_hours:
        data = json.loads(state.read_text(encoding="utf-8"))
        rec = data["orchestrator_state"][feature]
        from datetime import datetime, timedelta, timezone
        old = datetime.now(timezone.utc) - timedelta(hours=age_hours)
        rec["owner_heartbeat_ts"] = old.strftime("%Y-%m-%dT%H:%M:%SZ")
        state.write_text(json.dumps(data), encoding="utf-8")
    return root


def _run(*args: str | Path, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True,
                          text=True, cwd=str(cwd) if cwd else None)


def _token(out: str) -> str:
    return next((l for l in out.splitlines() if l.startswith("LIVE-RUNS:")), "")


def test_a_fresh_claim_in_another_lane_is_named(tmp_path: Path) -> None:
    lane = _project(tmp_path / "hemasuite", "batch-18", "sess-abcdef12")

    proc = _run("--path", lane)

    assert proc.returncode == 0
    assert _token(proc.stdout) == "LIVE-RUNS: 1 checked=1", proc.stdout
    assert f"live: {lane} · batch-18 · owner sess-abc" in proc.stdout, proc.stdout


def test_stale_and_released_claims_are_not_live(tmp_path: Path) -> None:
    stale = _project(tmp_path / "a", "old", "sess-1", age_hours=3)
    unowned = _project(tmp_path / "b", "never-claimed", None)

    proc = _run("--path", stale, "--path", unowned)

    assert _token(proc.stdout) == "LIVE-RUNS: NONE checked=2", proc.stdout


def test_an_unreadable_state_file_is_unknown_not_none(tmp_path: Path) -> None:
    lane = tmp_path / "lane"
    (lane / "docs").mkdir(parents=True)
    (lane / "docs" / ".bkit-memory.json").write_text("{not json", encoding="utf-8")

    proc = _run("--path", lane)

    assert _token(proc.stdout).startswith("LIVE-RUNS: UNKNOWN"), proc.stdout
    assert f"unreadable: {lane}" in proc.stdout, proc.stdout


def test_a_lane_without_state_is_checked_and_quiet(tmp_path: Path) -> None:
    (tmp_path / "plain").mkdir()

    proc = _run("--path", tmp_path / "plain")

    assert _token(proc.stdout) == "LIVE-RUNS: NONE checked=1", proc.stdout


def test_failed_discovery_is_unknown_not_none(tmp_path: Path) -> None:
    """No `--path` and no worktree list: nothing was checked, which is not 'none live'."""
    proc = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True,
                          env={**os.environ, "PATH": str(tmp_path)})

    assert _token(proc.stdout).startswith("LIVE-RUNS: UNKNOWN"), proc.stdout


def _skills_repo(tmp_path: Path, staged: dict[str, str]) -> Path:
    repo = tmp_path / "skills"
    (repo / "h-mad").mkdir(parents=True)
    (repo / "h-mad" / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    (repo / "notes.md").write_text("n\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True, env=ENV)
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, env=ENV)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "i"], check=True, env=ENV)
    for rel, body in staged.items():
        (repo / rel).write_text(body, encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", rel], check=True, env=ENV)
    return repo


def test_if_staged_skill_is_silent_when_no_skill_file_is_staged(tmp_path: Path) -> None:
    repo = _skills_repo(tmp_path, {"notes.md": "edited\n"})
    lane = _project(tmp_path / "lane", "f", "sess-1")

    proc = _run("--if-staged-skill", "--path", lane, cwd=repo)

    assert proc.stdout == "", proc.stdout


def test_if_staged_skill_warns_when_a_skill_file_is_staged(tmp_path: Path) -> None:
    repo = _skills_repo(tmp_path, {"h-mad/SKILL.md": "# skill, edited\n"})
    lane = _project(tmp_path / "lane", "f", "sess-1")

    proc = _run("--if-staged-skill", "--path", lane, cwd=repo)

    assert _token(proc.stdout) == "LIVE-RUNS: 1 checked=1", proc.stdout
