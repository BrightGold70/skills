"""Lane liveness from four independent clocks, not the heartbeat alone.

Skill-candidates row "gate-on-two-independent-clocks". `owner_heartbeat_ts` is
one clock, and it misread a working lane as dead four times across two repos:
a lane shipped three tasks with the heartbeat 92-153 minutes cold; an owner
working with a heartbeat 110 minutes cold lost its claim on wall-clock; a
false-dead reading (frozen transcript, cold heartbeat) led to a `--force` claim
and a duplicate task run; a day-old heartbeat sat on a live owner whose
transcript was seconds old. `fc2ae164` made more writers refresh the heartbeat,
which is still one clock, and two of those cases came after it.

So the reading combines four: the heartbeat, the owner's transcript mtime, the
lane's newest commit, and `ps` argv naming the owner session. Any fresh clock
is LIVE. QUIET needs every clock readable and cold. An unreadable clock is
UNKNOWN, never QUIET. `ps` is positive-only: a session id is in argv only for
resumed or explicit-id launches, so its absence proves nothing.

Every clock source is injected here; no test reads the real `~/.claude`, `ps`
or a real lane.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import h_mad_state_ownership as ownership  # noqa: E402
from h_mad_state_ownership import OWNERSHIP_STALE_AFTER_SECONDS, liveness_evidence  # noqa: E402

WRITER = SCRIPTS / "h_mad_state_write.py"
NOW = datetime(2026, 9, 14, 12, 0, 0, tzinfo=timezone.utc)
OWNER = "22e0a5f1-4b7c-4a51-9d2e-0c1f6a3b9e77"
WINDOW = OWNERSHIP_STALE_AFTER_SECONDS
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def _ago(seconds: float) -> float:
    return NOW.timestamp() - seconds


def _record(heartbeat_age: float | None, owner: str | None = OWNER) -> dict:
    beat = None if heartbeat_age is None else (
        NOW - timedelta(seconds=heartbeat_age)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"owner_session_id": owner, "owner_heartbeat_ts": beat}


def _read(record: dict, *, transcript: float | None, commit: float | None,
          ps: list[str] | None, minted: bool = False) -> str:
    return liveness_evidence(
        record, Path("/lanes/x"), NOW.isoformat(),
        transcript_mtime=lambda session: transcript,
        commit_ts=lambda lane: commit,
        ps_commands=lambda: ps,
        minted_owner=lambda lane, session: minted,
    )


COLD = 3 * 60 * 60  # three hours: past the two-hour window on every clock


# --- the four named readings -------------------------------------------------


def test_cold_heartbeat_fresh_transcript_is_LIVE() -> None:
    """Cases 2 and 4: the owner was working; its transcript was seconds old."""
    out = _read(_record(COLD), transcript=_ago(60), commit=_ago(COLD), ps=[])

    assert out == f"LIVENESS: LIVE evidence=transcript:60s heartbeat_age={COLD}s", out


def test_cold_heartbeat_recent_commit_is_LIVE() -> None:
    """Case 1: the lane shipped three tasks while the heartbeat sat cold."""
    out = _read(_record(COLD), transcript=_ago(COLD), commit=_ago(300), ps=[])

    assert out == f"LIVENESS: LIVE evidence=commit:300s heartbeat_age={COLD}s", out


def test_ps_argv_match_is_LIVE_with_frozen_transcript() -> None:
    """Case 3: idle between turns, so the transcript froze; the process still ran."""
    ps = ["/usr/bin/zsh -l", f"claude --resume {OWNER} --model opus"]

    out = _read(_record(COLD), transcript=_ago(COLD), commit=_ago(COLD), ps=ps)

    assert out == f"LIVENESS: LIVE evidence=ps heartbeat_age={COLD}s", out


def test_all_clocks_cold_is_QUIET() -> None:
    """A clean dead lane: no process, an old transcript, no new commits."""
    out = _read(_record(COLD), transcript=_ago(COLD + 1), commit=_ago(COLD + 2), ps=["zsh"])

    assert out == (f"LIVENESS: QUIET heartbeat_age={COLD}s transcript_age={COLD + 1}s "
                   f"commit_age={COLD + 2}s window={WINDOW}s"), out


@pytest.mark.parametrize("clock", ["heartbeat", "transcript", "commit", "ps"])
def test_unreadable_clock_is_UNKNOWN_never_QUIET(clock: str) -> None:
    """Every other clock is cold. One clock that could not be read is not a cold one."""
    record = _record(None if clock == "heartbeat" else COLD)
    out = _read(record,
                transcript=None if clock == "transcript" else _ago(COLD),
                commit=None if clock == "commit" else _ago(COLD),
                ps=None if clock == "ps" else [])

    assert out == f"LIVENESS: UNKNOWN reason={clock}", out


def test_live_runs_reports_lane_live_on_transcript_clock(tmp_path: Path, monkeypatch,
                                                         capsys) -> None:
    """The consumer: a cold heartbeat no longer reads as 'no run here'."""
    lane = _lane(tmp_path / "hemasuite", "batch-18", OWNER, heartbeat_age=COLD)
    _clocks(monkeypatch, transcript=time_ago(30), commit=time_ago(COLD), ps=[])
    import h_mad_live_runs

    assert h_mad_live_runs.main(["--path", str(lane)]) == 0

    out = capsys.readouterr().out
    assert "LIVE-RUNS: 1 checked=1" in out, out
    assert f"live: {lane} · batch-18 · owner {OWNER[:8]}" in out, out
    assert "evidence=transcript:" in out, out


# --- edges of the disjunction ------------------------------------------------


def test_a_fresh_heartbeat_alone_is_LIVE() -> None:
    out = _read(_record(600), transcript=_ago(COLD), commit=_ago(COLD), ps=[])

    assert out == "LIVENESS: LIVE evidence=heartbeat:600s heartbeat_age=600s", out


def test_a_fresh_clock_wins_over_an_unreadable_one() -> None:
    """Positive evidence suffices; UNKNOWN is only for a reading that could be QUIET."""
    out = _read(_record(None), transcript=_ago(5), commit=None, ps=None)

    assert out == "LIVENESS: LIVE evidence=transcript:5s heartbeat_age=unreadable", out


def test_every_fresh_clock_is_named() -> None:
    out = _read(_record(10), transcript=_ago(20), commit=_ago(30), ps=[f"claude --session-id {OWNER}"])

    assert out == ("LIVENESS: LIVE evidence=ps,transcript:20s,commit:30s,heartbeat:10s "
                   "heartbeat_age=10s"), out


def test_age_exactly_at_the_window_is_fresh() -> None:
    """Same inclusive boundary as `owner_is_live`: stale only once strictly older."""
    out = _read(_record(COLD), transcript=_ago(WINDOW), commit=_ago(COLD), ps=[])

    assert out == f"LIVENESS: LIVE evidence=transcript:{WINDOW}s heartbeat_age={COLD}s", out


def test_ps_absence_proves_nothing() -> None:
    """ps read fine and named no process, the transcript could not be read: UNKNOWN."""
    out = _read(_record(COLD), transcript=None, commit=_ago(COLD), ps=["zsh", "python3 x.py"])

    assert out == "LIVENESS: UNKNOWN reason=transcript", out


def test_ps_needs_the_whole_session_id() -> None:
    """A longer token that merely starts with the id is another session."""
    ps = [f"claude --resume {OWNER}0", f"tail -f /tmp/x{OWNER}.log"]

    out = _read(_record(COLD), transcript=_ago(COLD), commit=_ago(COLD), ps=ps)

    assert out.startswith("LIVENESS: QUIET"), out


def test_a_record_with_no_owner_is_UNKNOWN() -> None:
    """No session id: neither the transcript nor ps can be asked."""
    out = _read(_record(None, owner=None), transcript=_ago(COLD), commit=_ago(COLD), ps=[])

    assert out == "LIVENESS: UNKNOWN reason=heartbeat,owner", out


# --- default clock readers (pointed at temp dirs, never the real ones) -------


def test_transcript_reader_takes_the_newest_jsonl_under_the_config_dir(tmp_path: Path,
                                                                        monkeypatch) -> None:
    monkeypatch.delenv(ownership.CLOCKS_OFF_ENV, raising=False)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    old = tmp_path / "projects" / "-a" / f"{OWNER}.jsonl"
    new = tmp_path / "projects" / "-b" / f"{OWNER}.jsonl"
    for path, mtime in ((old, 1_000_000), (new, 2_000_000)):
        path.parent.mkdir(parents=True)
        path.write_text("{}\n", encoding="utf-8")
        os.utime(path, (mtime, mtime))

    assert ownership.read_transcript_mtime(OWNER) == 2_000_000
    assert ownership.read_transcript_mtime("no-such-session") is None
    assert ownership.read_transcript_mtime("../*") is None


def _commit(repo: Path, rel: str, epoch: int) -> None:
    (repo / rel).parent.mkdir(parents=True, exist_ok=True)
    (repo / rel).write_text(f"{epoch}\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", rel], check=True, env=ENV)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", rel], check=True,
                   env={**ENV, "GIT_COMMITTER_DATE": f"@{epoch} +0000"})


def _repo(path: Path) -> Path:
    path.mkdir(parents=True)
    subprocess.run(["git", "-C", str(path), "init", "-q", "-b", "main"], check=True, env=ENV)
    return path


def test_commit_reader_reads_the_lane_head(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv(ownership.CLOCKS_OFF_ENV, raising=False)
    repo = _repo(tmp_path / "lane")
    _commit(repo, "a.txt", 1700000000)

    assert ownership.read_commit_ts(repo) == 1700000000
    assert ownership.read_commit_ts(tmp_path / "not-a-repo") is None


def test_ps_parser_drops_the_header_and_its_own_pid() -> None:
    text = "  PID COMMAND\n  101 claude --resume abc\n  202 python3 self.py abc\n"

    assert ownership.parse_ps(text, own_pid=202) == ["claude --resume abc"]


# --- CLI and the --claim refusal ----------------------------------------------


def test_cli_reads_each_claim_and_writes_nothing(tmp_path: Path, monkeypatch, capsys) -> None:
    lane = _lane(tmp_path / "lane", "alpha", OWNER, heartbeat_age=COLD)
    _lane(lane, "beta", None)
    state = lane / "docs" / ".bkit-memory.json"
    before = (state.read_bytes(), state.stat().st_mtime_ns)
    _clocks(monkeypatch, transcript=time_ago(COLD), commit=time_ago(COLD), ps=[])
    import h_mad_lane_liveness

    assert h_mad_lane_liveness.main([str(lane)]) == 0

    out = capsys.readouterr().out.splitlines()
    assert len(out) == 1 and out[0].startswith("LIVENESS: QUIET ") and out[0].endswith(
        " feature=alpha"), out
    assert (state.read_bytes(), state.stat().st_mtime_ns) == before


def test_cli_unreadable_state_or_missing_feature_is_UNKNOWN(tmp_path: Path, capsys) -> None:
    import h_mad_lane_liveness
    lane = tmp_path / "lane"
    (lane / "docs").mkdir(parents=True)
    (lane / "docs" / ".bkit-memory.json").write_text("{not json", encoding="utf-8")

    h_mad_lane_liveness.main([str(lane)])
    assert capsys.readouterr().out.startswith("LIVENESS: UNKNOWN reason=state"), "unreadable"

    _lane(tmp_path / "ok", "alpha", OWNER)
    h_mad_lane_liveness.main([str(tmp_path / "ok"), "--feature", "nope"])
    assert capsys.readouterr().out.startswith("LIVENESS: UNKNOWN reason=no-such-feature")


def test_claim_refusal_prints_the_liveness_evidence(tmp_path: Path, monkeypatch) -> None:
    """The refusal that names --force carries every clock, so forcing is an informed act."""
    from h_mad_state_write import StateWriteError, claim
    lane = _lane(tmp_path / "lane", "alpha", OWNER, heartbeat_age=60)
    _clocks(monkeypatch, transcript=time_ago(5), commit=time_ago(COLD), ps=[])

    with pytest.raises(StateWriteError) as refused:
        claim(lane / "docs" / ".bkit-memory.json", "alpha", "intruder")

    assert "LIVENESS: LIVE evidence=transcript:" in str(refused.value), refused.value
    assert "force" in str(refused.value)


def test_live_runs_cold_claim_with_an_unreadable_clock_is_unknown_not_none(
        tmp_path: Path, monkeypatch, capsys) -> None:
    lane = _lane(tmp_path / "lane", "alpha", OWNER, heartbeat_age=COLD)
    _clocks(monkeypatch, transcript=None, commit=time_ago(COLD), ps=[])
    import h_mad_live_runs

    h_mad_live_runs.main(["--path", str(lane)])

    out = capsys.readouterr().out
    assert out.startswith("LIVE-RUNS: UNKNOWN"), out
    assert "reason=transcript" in out, out


# --- review of 37f0f5e5 --------------------------------------------------------


def test_ps_ignores_argv_that_only_mentions_the_id() -> None:
    """SF1: the checker's own shell, a grep or a tail naming a dead owner read LIVE."""
    ps = [f"/bin/zsh -c python3 probe.py id.txt; : {OWNER}",
          f"grep {OWNER} docs/.bkit-memory.json",
          f"tail -f /Users/x/.claude/projects/-p/{OWNER}.jsonl",
          f"python3 -c print('{OWNER}')"]

    out = _read(_record(COLD), transcript=_ago(COLD), commit=_ago(COLD), ps=ps)

    assert out.startswith("LIVENESS: QUIET"), out


@pytest.mark.parametrize("argv", [f"claude --resume={OWNER}",
                                  f"node /opt/claude/cli.js -r {OWNER}",
                                  f"claude --session-id {OWNER} -p hi"])
def test_ps_accepts_every_session_flag_form(argv: str) -> None:
    out = _read(_record(COLD), transcript=_ago(COLD), commit=_ago(COLD), ps=[argv])

    assert out == f"LIVENESS: LIVE evidence=ps heartbeat_age={COLD}s", out


def test_commit_reader_ignores_merge_commits(tmp_path: Path, monkeypatch) -> None:
    """SF2: merging main into the lane branch is not the owner working."""
    monkeypatch.delenv(ownership.CLOCKS_OFF_ENV, raising=False)
    repo = _repo(tmp_path / "lane")
    _commit(repo, "a.txt", 1_700_000_000)
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", "-b", "side"], check=True, env=ENV)
    _commit(repo, "b.txt", 1_700_000_100)
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", "main"], check=True, env=ENV)
    _commit(repo, "c.txt", 1_700_000_200)
    subprocess.run(["git", "-C", str(repo), "merge", "-q", "--no-ff", "-m", "m", "side"],
                   check=True, env={**ENV, "GIT_COMMITTER_DATE": "@1800000000 +0000"})

    assert ownership.read_commit_ts(repo) == 1_700_000_200


def test_commit_reader_reads_only_commits_inside_a_nested_lane(tmp_path: Path,
                                                               monkeypatch) -> None:
    """SF2: a lane nested in a busy repo does not inherit the repo's HEAD."""
    monkeypatch.delenv(ownership.CLOCKS_OFF_ENV, raising=False)
    repo = _repo(tmp_path / "skills")
    _commit(repo, "lane/docs/x.md", 1_700_000_000)
    _commit(repo, "other/y.md", 1_800_000_000)

    assert ownership.read_commit_ts(repo / "lane") == 1_700_000_000
    assert ownership.read_commit_ts(repo) == 1_800_000_000


def test_claim_reads_the_commit_clock_at_the_lane_root(tmp_path: Path, monkeypatch) -> None:
    """SF2: scoped to the lane, the clock must not be scoped to the lane's docs/ dir."""
    from h_mad_state_write import StateWriteError, claim
    lane = _lane(tmp_path / "lane", "alpha", OWNER, heartbeat_age=60)
    seen: list[Path] = []
    _clocks(monkeypatch, transcript=time_ago(COLD), commit=None, ps=[])
    monkeypatch.setattr(ownership, "read_commit_ts",
                        lambda where: seen.append(Path(where).resolve()) or time_ago(COLD))

    with pytest.raises(StateWriteError):
        claim(lane / "docs" / ".bkit-memory.json", "alpha", "intruder")

    assert seen == [lane.resolve()], seen


def test_a_minted_owner_has_no_transcript_clock_and_can_read_QUIET() -> None:
    """SF3: a Codex/agy owner id is minted by h-mad, so no transcript can ever exist."""
    out = _read(_record(COLD), transcript=None, commit=_ago(COLD + 2), ps=[], minted=True)

    assert out == (f"LIVENESS: QUIET heartbeat_age={COLD}s transcript_age=n/a "
                   f"commit_age={COLD + 2}s window={WINDOW}s"), out


def test_minted_reader_finds_the_owner_in_the_lane_git_dir(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv(ownership.CLOCKS_OFF_ENV, raising=False)
    repo = _repo(tmp_path / "lane")
    (repo / ".git" / "h-mad-session-id.alpha").write_text(f"{OWNER}\n", encoding="utf-8")

    assert ownership.read_minted_owner(repo, OWNER) is True
    assert ownership.read_minted_owner(repo, "someone-else") is False
    assert ownership.read_minted_owner(tmp_path / "not-a-repo", OWNER) is False


def test_transcript_reader_counts_subagent_transcripts(tmp_path: Path, monkeypatch) -> None:
    """SF4: an owner waiting on a long subagent writes only the subagent's transcript."""
    monkeypatch.delenv(ownership.CLOCKS_OFF_ENV, raising=False)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    top = tmp_path / "projects" / "-a" / f"{OWNER}.jsonl"
    sub = tmp_path / "projects" / "-a" / OWNER / "subagents" / "agent-x.jsonl"
    for path, mtime in ((top, 1_000_000), (sub, 3_000_000)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
        os.utime(path, (mtime, mtime))

    assert ownership.read_transcript_mtime(OWNER) == 3_000_000


def test_the_clocks_off_switch_reads_no_host_clock(monkeypatch) -> None:
    """SF5: with the switch set, no reader touches ps, git or ~/.claude."""
    monkeypatch.setenv(ownership.CLOCKS_OFF_ENV, "1")

    def boom(*args, **kwargs):
        raise AssertionError("a host clock was read")

    monkeypatch.setattr(ownership.subprocess, "run", boom)
    monkeypatch.setattr(ownership.Path, "glob", boom)

    out = liveness_evidence(_record(COLD), Path("/lanes/x"), NOW.isoformat())

    assert out == "LIVENESS: UNKNOWN reason=transcript,commit,ps", out
    assert ownership.read_minted_owner(Path("/lanes/x"), OWNER) is False


def test_the_suite_runs_with_host_clocks_off() -> None:
    """SF5: conftest sets the switch before any test module, subprocess env included."""
    assert os.environ.get(ownership.CLOCKS_OFF_ENV) == "1"


def test_a_stale_takeover_prints_the_liveness_reading(tmp_path: Path, monkeypatch,
                                                      capsys) -> None:
    """SF6: incident 2 was a plain --claim on a cold heartbeat; it must not be silent."""
    from h_mad_state_write import claim
    lane = _lane(tmp_path / "lane", "alpha", OWNER, heartbeat_age=COLD)
    _clocks(monkeypatch, transcript=time_ago(30), commit=time_ago(COLD), ps=[])

    record = claim(lane / "docs" / ".bkit-memory.json", "alpha", "intruder")

    assert record["owner_session_id"] == "intruder"  # the gate itself is unchanged
    err = capsys.readouterr().err
    assert f"STATE-WRITE: TAKEOVER feature=alpha from={OWNER[:8]}" in err, err
    assert "LIVENESS: LIVE evidence=transcript:" in err, err


def test_liveness_is_read_outside_the_store_lock(tmp_path: Path, monkeypatch) -> None:
    """Nit 3: a hung ps must not hold the store lock against the owner's own --beat."""
    import fcntl
    from h_mad_state_write import StateWriteError, claim
    lane = _lane(tmp_path / "lane", "alpha", OWNER, heartbeat_age=60)
    _lane(lane, "beta", OWNER, heartbeat_age=COLD)
    state = lane / "docs" / ".bkit-memory.json"
    held: list[bool] = []

    def probe(session):
        with open(state.with_suffix(".json.lock"), "a", encoding="utf-8") as fh:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                held.append(True)
            else:
                held.append(False)
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        return time_ago(5)

    _clocks(monkeypatch, transcript=None, commit=time_ago(COLD), ps=[])
    monkeypatch.setattr(ownership, "read_transcript_mtime", probe)

    with pytest.raises(StateWriteError):
        claim(state, "alpha", "intruder")
    claim(state, "beta", "intruder")

    assert held == [False, False], held


def test_cli_a_lane_with_no_claim_is_NONE_not_UNKNOWN(tmp_path: Path, capsys) -> None:
    """Nit 2: nothing failed to read, so the reading is not UNKNOWN."""
    import h_mad_lane_liveness
    _lane(tmp_path / "ok", "alpha", None)

    h_mad_lane_liveness.main([str(tmp_path / "ok")])

    assert capsys.readouterr().out.startswith("LIVENESS: NONE reason=no-claim")


def test_live_runs_unjudged_claim_gets_the_hold_advice(tmp_path: Path, monkeypatch,
                                                       capsys) -> None:
    """Nit 4: a claim that could not be judged may be a live run; say so."""
    lane = _lane(tmp_path / "lane", "alpha", OWNER, heartbeat_age=COLD)
    _clocks(monkeypatch, transcript=None, commit=time_ago(COLD), ps=[])
    import h_mad_live_runs

    h_mad_live_runs.main(["--path", str(lane)])

    assert "decide whether to hold it" in capsys.readouterr().out


# --- helpers -------------------------------------------------------------------


def time_ago(seconds: float) -> float:
    """Wall-clock epoch `seconds` ago, for consumers that read the real now."""
    return datetime.now(timezone.utc).timestamp() - seconds


def _clocks(monkeypatch, *, transcript, commit, ps, minted: bool = False) -> None:
    monkeypatch.setattr(ownership, "read_transcript_mtime", lambda session: transcript)
    monkeypatch.setattr(ownership, "read_commit_ts", lambda lane: commit)
    monkeypatch.setattr(ownership, "read_ps_commands", lambda: ps)
    monkeypatch.setattr(ownership, "read_minted_owner", lambda lane, session: minted)


def _lane(root: Path, feature: str, session: str | None, heartbeat_age: float = 0) -> Path:
    """A lane whose state record is written by the real writer, then aged."""
    state = root / "docs" / ".bkit-memory.json"
    state.parent.mkdir(parents=True, exist_ok=True)
    if not state.exists():
        state.write_text("{}", encoding="utf-8")
    args = [sys.executable, str(WRITER), str(state), "--feature", feature, "--create"]
    if session:
        args += ["--claim", session]
    subprocess.run(args, check=True, capture_output=True)
    if heartbeat_age:
        data = json.loads(state.read_text(encoding="utf-8"))
        old = datetime.now(timezone.utc) - timedelta(seconds=heartbeat_age)
        data["orchestrator_state"][feature]["owner_heartbeat_ts"] = old.strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        state.write_text(json.dumps(data), encoding="utf-8")
    return root
