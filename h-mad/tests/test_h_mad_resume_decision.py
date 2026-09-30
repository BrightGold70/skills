import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "h-mad" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import h_mad_resume_decision as resume_decision  # noqa: E402
from h_mad_resume_decision import _phase_num, decide  # noqa: E402


def _write_state(tmp_path: Path, feature: str, feat_state: dict) -> Path:
    state_file = tmp_path / ".bkit-memory.json"
    state_file.write_text(
        json.dumps({"version": 1, "orchestrator_state": {feature: feat_state}}),
        encoding="utf-8",
    )
    return state_file


@pytest.mark.parametrize(
    "value,expected",
    [
        (7, 7),          # schema int form
        (4, 4),
        (0, 0),
        ("step7", 7),    # orchestrator "stepN" string form actually written to state
        ("phase7", 7),   # alternate "phaseN" form also seen in real state
        ("step4", 4),
        ("STEP5", 5),    # case-insensitive
        ("complete", 7), # sentinel
        ("5", 5),        # bare digit string
        (None, 0),       # absent/unknown degrades, never raises
        (True, 0),       # bool is an int subclass — must NOT count as 1
        ("garbage", 0),
    ],
)
def test_phase_num_coerces_every_state_form(value, expected) -> None:
    assert _phase_num(value) == expected


def test_decide_complete_from_stepN_string_does_not_crash(tmp_path: Path) -> None:
    # Regression: state stored "step7" (string) while decide() compared `>= 7`
    # (int) -> TypeError on every completed feature. Must return "complete".
    state = _write_state(tmp_path, "feat", {"last_completed_phase": "step7"})
    assert decide(state, "feat") == "complete"


def test_decide_honors_explicit_complete_flag(tmp_path: Path) -> None:
    state = _write_state(
        tmp_path, "feat", {"complete": True, "last_completed_phase": "step5"}
    )
    assert decide(state, "feat") == "complete"


def test_decide_complete_sentinel_phase(tmp_path: Path) -> None:
    state = _write_state(tmp_path, "feat", {"last_completed_phase": "complete"})
    assert decide(state, "feat") == "complete"


def test_decide_current_phase_complete_with_phase7_last(tmp_path: Path) -> None:
    # Real synopsis-manifest-source-ingestion shape: current_phase sentinel
    # plus the "phaseN" (not "stepN") last_completed_phase variant.
    state = _write_state(
        tmp_path,
        "feat",
        {"current_phase": "complete", "last_completed_phase": "phase7"},
    )
    assert decide(state, "feat") == "complete"
    # Keep the sentinel assertion discriminating: phase7 alone also completes.
    sentinel_only = _write_state(
        tmp_path, "feat", {"current_phase": "complete", "last_completed_phase": 4}
    )
    assert decide(sentinel_only, "feat") == "complete", (
        "current_phase=complete must complete even below the phase7 threshold"
    )


def test_decide_routing_thresholds(tmp_path: Path) -> None:
    assert decide(_write_state(tmp_path, "f", {"last_completed_phase": "step4"}), "f") == "enter_autonomous"
    assert decide(_write_state(tmp_path, "f", {"last_completed_phase": "step2"}), "f") == "resume_manual"
    assert decide(_write_state(tmp_path, "f", {"halt_reason": "step5d:no_codex_pane"}), "f") == "halted"


class TestAnUnreadableStateFileIsNotAnEmptyOne:
    """WSG-6. Three different states used to return `start_fresh`, and only two of
    them mean it.

    "No file" and "the file parsed and holds no record for this feature" both
    legitimately mean nothing is claimed. "The file is there and I could not read
    it" does not: the store may hold dozens of records and a live owner for this
    very feature, and `start_fresh` tells the caller to initialise over it. The
    incident that filed this was a state file that vanished with the cause
    undetermined; an unreadable file is the half a tool can defend against.
    """

    def test_invalid_json_is_cannot_judge_not_start_fresh(self, tmp_path: Path) -> None:
        state = tmp_path / ".bkit-memory.json"
        state.write_text('{"orchestrator_state": {"feat": ', encoding="utf-8")
        assert decide(state, "feat") == "cannot_judge"

    def test_a_truncated_write_over_a_POPULATED_store_is_cannot_judge(self, tmp_path: Path) -> None:
        """The realistic shape: the file held records a moment ago and the write was
        cut. Answering `start_fresh` here is what routes a second session onto a
        feature the first is working."""
        good = _write_state(tmp_path, "feat", {"last_completed_phase": 5,
                                               "owner_session_id": "someone-else"})
        whole = good.read_text(encoding="utf-8")
        good.write_text(whole[: len(whole) // 2], encoding="utf-8")
        assert decide(good, "feat") == "cannot_judge"

    def test_an_unreadable_file_is_cannot_judge(self, tmp_path: Path) -> None:
        import os
        state = _write_state(tmp_path, "feat", {"last_completed_phase": 5})
        state.chmod(0o000)
        try:
            if os.access(state, os.R_OK):        # root ignores the mode
                pytest.skip("running as root — the permission path is unreachable")
            assert decide(state, "feat") == "cannot_judge"
        finally:
            state.chmod(0o600)

    def test_an_ABSENT_file_still_starts_fresh_deliberately(self, tmp_path: Path) -> None:
        """Not an oversight. A feature that was never started is the common case, and
        the callers that know better check for the file before asking. Telling "never
        existed" from "vanished" needs evidence this script does not have — so that
        half of WSG-6 stays open rather than being papered over with a false alarm."""
        assert decide(tmp_path / "nonexistent.json", "feat") == "start_fresh"

    def test_the_token_is_documented_where_callers_read_it(self) -> None:
        """A token nobody documented is one every caller's enumeration misclassifies.
        `handoff/SKILL.md` used to end its list with "any other token -> safe to
        proceed", which is fail-OPEN: a token added FOR safety would have been read as
        permission to proceed."""
        skill = (REPO_ROOT / "h-mad" / "SKILL.md").read_text(encoding="utf-8")
        assert "`cannot_judge`" in skill, (
            "the decision-token table must name cannot_judge, or an operator hitting "
            "it has no prescribed action")

        handoff = Path.home() / ".claude" / "skills" / "handoff" / "SKILL.md"
        if not handoff.is_file():
            pytest.skip("handoff skill not installed alongside h-mad")
        text = handoff.read_text(encoding="utf-8")
        assert "`cannot_judge`" in text, (
            "the handoff skill's oracle enumeration does not mention cannot_judge, so "
            "it falls into whatever that list's default is")

        # The POSITIVE invariant, because the negative one is what a bare substring
        # check gets wrong. A first version of this test asserted `"any other token"
        # not in text` and failed on the sentence in THIS repo documenting the
        # retired defect — a proxy that cannot tell a live instruction from prose
        # quoting the instruction it replaced. What actually matters is that the list
        # is CLOSED.
        assert "**anything else** → STOP" in text, (
            "the liveness-oracle enumeration must end with a closed default. Without "
            "one it fails OPEN: every token added to the oracle later is "
            "auto-classified as whatever the trailing bullet says, and cannot_judge "
            "was added FOR safety.")

        # And the specific fail-open construction must not be live: the phrase and the
        # permission on the SAME line is the shape that granted it.
        live = [ln for ln in text.splitlines()
                if "any other token" in ln and "safe to proceed" in ln]
        assert not live, ("fail-open default is live again:\n" + "\n".join(live))


def test_decide_missing_feature_or_state_starts_fresh(tmp_path: Path) -> None:
    state = _write_state(tmp_path, "other", {"last_completed_phase": "step7"})
    assert decide(state, "absent") == "start_fresh"
    assert decide(tmp_path / "nonexistent.json", "feat") == "start_fresh"


@pytest.fixture
def minted_identity():
    # Exercise agent-authored markdown, glob characters, markers and newlines
    # through the shared hostile-input knob instead of a tidy UUID fixture.
    result = subprocess.run(
        [str(REPO_ROOT / "h-mad" / "tests" / "stubs" / "orca"),
         "worktree", "set", "--comment", "fixture"],
        env={"PATH": os.environ["PATH"], "HMAD_STUB_HOSTILE": "all"},
        capture_output=True, text=True, check=True, timeout=10,
    )
    session_id = json.loads(result.stdout)["result"]["worktree"]["comment"]
    # A feature is a filename suffix, so keep hostile data but no path separator.
    feature = "resume " + session_id.replace("/", "_")
    return feature, session_id


@pytest.fixture
def git_checkout(tmp_path: Path, monkeypatch):
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR",
                 "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY"):
        monkeypatch.delenv(name, raising=False)
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", str(root)], capture_output=True,
                   text=True, check=True, timeout=10)
    subprocess.run(
        ["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
         "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
         "commit", "--allow-empty", "-m", "Fixture root"],
        cwd=root, capture_output=True, text=True, check=True, timeout=10,
    )
    return root


@pytest.mark.parametrize("checkout", ["repo", "worktree"])
def test_session_id_from_git_dir_reads_minted_id(
    checkout, tmp_path: Path, monkeypatch, git_checkout, minted_identity
) -> None:
    root = git_checkout
    cwd = root
    if checkout == "worktree":
        cwd = tmp_path / "linked worktree"
        subprocess.run(["git", "worktree", "add", "--detach", str(cwd)],
                       cwd=root, capture_output=True, text=True, check=True, timeout=10)
    monkeypatch.chdir(cwd)
    git_dir = Path(subprocess.run(
        ["git", "rev-parse", "--absolute-git-dir"],
        capture_output=True, text=True, check=True, timeout=10,
    ).stdout.strip())
    if checkout == "worktree":
        assert git_dir.resolve() != (root / ".git").resolve(), (
            "the linked worktree must use its own git directory"
        )
    feature, session_id = minted_identity
    (git_dir / ("h-mad-session-id." + feature)).write_text(
        session_id + "\n", encoding="utf-8"
    )
    calls = []
    real_run = subprocess.run

    def recorded_run(*args, **kwargs):
        calls.append((args, kwargs))
        return real_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", recorded_run)
    read_id = resume_decision.session_id_from_git_dir
    assert read_id(feature) == session_id.strip(), (
        "session_id_from_git_dir must read the current checkout's minted id and strip it"
    )
    assert calls == [((['git', 'rev-parse', '--absolute-git-dir'],),
                      {"timeout": 10.0, "capture_output": True, "text": True})], (
        "git-dir discovery must use subprocess.run with the stdlib timeout bound"
    )


@pytest.mark.parametrize(
    "failure", ["absent", "empty", "whitespace", "mode000", "outside-repo",
                "no-git", "bound-expired"]
)
def test_session_id_from_git_dir_failure_returns_none(
    failure, tmp_path: Path, monkeypatch, git_checkout, minted_identity
) -> None:
    monkeypatch.chdir(git_checkout)
    feature, session_id = minted_identity
    id_file = git_checkout / ".git" / ("h-mad-session-id." + feature)
    if failure != "absent":
        contents = {"empty": "", "whitespace": " \t\n \r\n"}.get(
            failure, session_id + "\n"
        )
        id_file.write_text(contents, encoding="utf-8")
    if failure == "mode000":
        id_file.chmod(0o000)
        try:
            with pytest.raises(PermissionError, match="Permission denied"):
                id_file.read_text(encoding="utf-8")
            read_id = resume_decision.session_id_from_git_dir
            assert read_id(feature) is None, (
                "session_id_from_git_dir must return None when reading the id raises OSError"
            )
        finally:
            id_file.chmod(0o600)
        return
    if failure == "outside-repo":
        monkeypatch.chdir(tmp_path)
        result = subprocess.run(["git", "rev-parse", "--absolute-git-dir"],
                                capture_output=True, text=True, timeout=10)
        assert result.returncode != 0, "outside-repo must exercise a non-zero git exit"
    if failure in ("no-git", "bound-expired"):
        bin_dir = tmp_path / "hermetic bin"
        bin_dir.mkdir()
        monkeypatch.setenv("PATH", str(bin_dir))
        if failure == "no-git":
            assert shutil.which("git") is None, "the hermetic PATH must contain no git"
        else:
            stub = bin_dir / "git"
            stub.write_text(f"#!{sys.executable}\nimport time\ntime.sleep(5)\n",
                            encoding="utf-8")
            stub.chmod(0o755)
            read_id = resume_decision.session_id_from_git_dir
            monkeypatch.setattr(resume_decision, "GIT_DIR_BOUND_S", 0.5)
    read_id = resume_decision.session_id_from_git_dir
    started = time.monotonic()
    assert read_id(feature) is None, (
        f"session_id_from_git_dir must return None for {failure}"
    )
    if failure == "bound-expired":
        assert time.monotonic() - started < 2.0, (
            "git-dir discovery must return well before the git stub's five-second sleep"
        )


def test_build_parser_is_module_level() -> None:
    parser = resume_decision.build_parser()
    options = {option for action in parser._actions for option in action.option_strings}
    assert {"--state", "--feature", "--host", "--session-id", "--now"} <= options, (
        "module-level build_parser must preserve all five existing long options"
    )


def test_git_dir_bound_constant() -> None:
    assert resume_decision.GIT_DIR_BOUND_S == 10.0, (
        "GIT_DIR_BOUND_S must independently bound git-dir discovery at ten seconds"
    )


@pytest.mark.parametrize(
    "checkout,ownership",
    [("repo", "owner"), ("repo", "other"),
     ("worktree", "owner"), ("worktree", "other")],
    ids=["repo-owner", "repo-other", "worktree-owner", "worktree-other"],
)
def test_git_dir_flag_matches_session_id_token(
    checkout, ownership, tmp_path: Path, git_checkout, minted_identity
) -> None:
    feature, session_id = minted_identity
    cwd = git_checkout
    if checkout == "worktree":
        cwd = tmp_path / "linked worktree"
        subprocess.run(["git", "worktree", "add", "--detach", str(cwd)],
                       cwd=git_checkout, capture_output=True, text=True,
                       check=True, timeout=10)
        # Reading the main checkout's id must not satisfy the worktree pin.
        (git_checkout / ".git" / ("h-mad-session-id." + feature)).write_text(
            session_id + "\nwrong checkout", encoding="utf-8"
        )
    git_dir = Path(subprocess.run(
        ["git", "rev-parse", "--absolute-git-dir"], cwd=cwd,
        capture_output=True, text=True, check=True, timeout=10,
    ).stdout.strip())
    id_file = git_dir / ("h-mad-session-id." + feature)
    id_file.write_text(session_id + "\n", encoding="utf-8")
    state = _write_state(tmp_path, feature, {
        "last_completed_phase": 4,
        "owner_session_id": (session_id if ownership == "owner"
                             else session_id + "\nother live owner"),
        "owner_heartbeat_ts": "2026-07-22T01:00:00Z",
    })
    command = [sys.executable, str(SCRIPT_DIR / "h_mad_resume_decision.py"),
               "--state", str(state), "--feature", feature, "--host", "codex",
               "--now", "2026-07-22T01:05:00Z"]
    explicit = subprocess.run(
        command + ["--session-id", id_file.read_text(encoding="utf-8").strip()],
        cwd=cwd, capture_output=True, text=True, timeout=10,
    )
    expected = "enter_autonomous" if ownership == "owner" else "owned_elsewhere"
    assert explicit.returncode == 0 and explicit.stdout.strip() == expected, (
        "the explicit minted session id must establish the ownership control token"
    )
    flagged = subprocess.run(command + ["--session-id-from-git-dir"], cwd=cwd,
                             capture_output=True, text=True, timeout=15)
    assert flagged.stdout.strip() == explicit.stdout.strip(), (
        "main --session-id-from-git-dir must propagate the current checkout's "
        f"minted id to decide and print {expected}; got {flagged.stdout!r}; "
        f"stderr={flagged.stderr!r}"
    )
    assert flagged.returncode == 0, "the git-dir flag must be a successful CLI route"


@pytest.mark.parametrize(
    "host,failure",
    [(host, failure) for host in ("codex", "claude")
     for failure in ("absent", "empty", "whitespace", "mode000", "outside-repo",
                     "no-git", "bound-expired")],
    ids=[f"{host}-{failure}" for host in ("codex", "claude")
         for failure in ("absent", "empty", "whitespace", "mode000", "outside-repo",
                         "no-git", "bound-expired")],
)
def test_git_dir_flag_failure_is_cannot_judge(
    host, failure, tmp_path: Path, monkeypatch, capsys, git_checkout, minted_identity
) -> None:
    feature, session_id = minted_identity
    state = _write_state(tmp_path, feature, {
        "last_completed_phase": 4, "owner_session_id": session_id,
        "owner_heartbeat_ts": "2026-07-22T01:00:00Z",
    })
    cwd = git_checkout
    id_file = git_checkout / ".git" / ("h-mad-session-id." + feature)
    if failure != "absent":
        id_file.write_text(
            {"empty": "", "whitespace": " \t\n \r\n"}.get(failure, session_id + "\n"),
            encoding="utf-8",
        )
    if failure == "mode000":
        id_file.chmod(0o000)
    if failure == "outside-repo":
        cwd = tmp_path
        probe = subprocess.run(["git", "rev-parse", "--absolute-git-dir"],
                               cwd=cwd, capture_output=True, text=True, timeout=10)
        assert probe.returncode != 0, "outside-repo must exercise a failed git lookup"
    if failure in ("no-git", "bound-expired"):
        bin_dir = tmp_path / "hermetic bin"
        bin_dir.mkdir()
        monkeypatch.setenv("PATH", str(bin_dir))
        if failure == "no-git":
            assert shutil.which("git") is None, "no-git must have no git executable"
        else:
            stub = bin_dir / "git"
            stub.write_text(f"#!{sys.executable}\nimport time\ntime.sleep(5)\n",
                            encoding="utf-8")
            stub.chmod(0o755)
            monkeypatch.setattr(resume_decision, "GIT_DIR_BOUND_S", 0.5)
    command = [sys.executable, str(SCRIPT_DIR / "h_mad_resume_decision.py"),
               "--state", str(state), "--feature", feature, "--host", host,
               "--now", "2026-07-22T01:05:00Z", "--session-id-from-git-dir"]
    started = time.monotonic()
    try:
        if failure == "mode000":
            with pytest.raises(PermissionError, match="Permission denied"):
                id_file.read_text(encoding="utf-8")
        if failure == "bound-expired":
            # Patch the bound in the same process as main, not across a subprocess.
            monkeypatch.chdir(cwd)
            monkeypatch.setattr(sys, "argv", command[1:])
            try:
                returncode = resume_decision.main()
            except SystemExit as error:
                returncode = error.code
            captured = capsys.readouterr()
            stdout, stderr = captured.out, captured.err
        else:
            result = subprocess.run(command, cwd=cwd, capture_output=True,
                                    text=True, timeout=15)
            returncode, stdout, stderr = result.returncode, result.stdout, result.stderr
        assert stdout.strip() == "cannot_judge", (
            f"main must print cannot_judge for {host}/{failure} without falling "
            f"through to decide with no identity; got {stdout!r}; stderr={stderr!r}"
        )
        assert returncode == 0, "an unreadable git-dir id must return a verdict at exit 0"
        if failure == "bound-expired":
            assert time.monotonic() - started < 2.0, (
                "main must bound discovery well before the git stub's five-second sleep"
            )
    finally:
        if failure == "mode000":
            id_file.chmod(0o600)


@pytest.fixture
def recording_git(tmp_path: Path, monkeypatch, git_checkout):
    bin_dir = tmp_path / "recording bin"
    bin_dir.mkdir()
    record = tmp_path / "git invocations.json"
    stub = bin_dir / "git"
    stub.write_text(
        f"#!{sys.executable}\n"
        "import json, sys\nfrom pathlib import Path\n"
        f"Path({str(record)!r}).write_text(json.dumps(sys.argv[1:]))\n"
        f"print({str(git_checkout / '.git')!r})\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir) + os.pathsep + os.environ["PATH"])
    assert shutil.which("git") == str(stub), "the recording stub must be first on PATH"
    return record


def test_git_dir_flag_excludes_session_id(
    tmp_path: Path, git_checkout, minted_identity, recording_git
) -> None:
    feature, session_id = minted_identity
    state = _write_state(tmp_path, feature, {"last_completed_phase": 4})
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "h_mad_resume_decision.py"),
         "--state", str(state), "--feature", feature, "--session-id", session_id,
         "--session-id-from-git-dir"],
        cwd=git_checkout, capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 2, "conflicting identity options must exit 2"
    assert result.stdout == "", "conflicting identity options must print no verdict"
    assert "not allowed with argument" in result.stderr, (
        "build_parser must reject identity options as mutually exclusive; "
        f"stderr={result.stderr!r}"
    )
    assert not recording_git.exists(), "argument rejection must precede git-dir discovery"


def test_build_parser_offers_the_git_dir_flag() -> None:
    parser = resume_decision.build_parser()
    options = {option for action in parser._actions for option in action.option_strings
               if option.startswith("--") and option != "--help"}
    assert options == {"--state", "--feature", "--host", "--session-id", "--now",
                       "--session-id-from-git-dir"}, (
        "build_parser must offer exactly the six FR-8 long options, including "
        f"--session-id-from-git-dir; got {sorted(options)!r}"
    )


def test_session_id_alone_does_not_read_git_dir(
    tmp_path: Path, git_checkout, minted_identity, recording_git
) -> None:
    feature, session_id = minted_identity
    (git_checkout / ".git" / ("h-mad-session-id." + feature)).write_text(
        session_id + "\n", encoding="utf-8"
    )
    state = _write_state(tmp_path, feature, {
        "last_completed_phase": 4, "owner_session_id": session_id,
        "owner_heartbeat_ts": "2026-07-22T01:00:00Z",
    })
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "h_mad_resume_decision.py"),
         "--state", str(state), "--feature", feature, "--host", "codex",
         "--session-id", session_id + "\nother live session",
         "--now", "2026-07-22T01:05:00Z"],
        cwd=git_checkout, capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0 and result.stdout.strip() == "owned_elsewhere", (
        "main must preserve the explicit other session's ownership verdict"
    )
    assert not recording_git.exists(), (
        "main with only --session-id must not invoke git, even when the minted id is readable"
    )
