"""The context-budget helper decides whether a call that can end the run is safe.

Every failure mode below produces a number that is too SMALL, i.e. a false `OK` on a
session that is already past the ceiling -- the direction that overflows the window.
So the tests are written against the mis-reads, not against the happy path:

  * summing usage across turns is wrong in the other direction (inflates), but the
    fix for it -- "take the last one" -- is what makes the sidechain bug possible:
    the newest usage line in the JSONL can belong to a SUBAGENT, whose context is a
    fraction of the parent's. A 500k orchestrator then measures as 8k and passes.
  * `cache_read_input_tokens` alone omits the fresh and newly-cached parts of the
    prompt; all three must be summed or a long tool-result turn under-reads.
  * an unreadable transcript must be a cannot-judge, not a pass. It carries no
    `used=` for the same reason `WIREPIN: UNREADABLE` carries no counts: a verdict
    shape that can be parsed by a count that was never measured will be.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "h-mad" / "scripts" / "h_mad_context_budget.py"

sys.path.insert(0, str(SCRIPT.parent))
import h_mad_context_budget as cb  # noqa: E402


def _turn(read=0, create=0, fresh=0, sidechain=False):
    return json.dumps({
        "isSidechain": sidechain,
        "type": "assistant",
        "message": {"usage": {
            "input_tokens": fresh,
            "cache_creation_input_tokens": create,
            "cache_read_input_tokens": read,
            "output_tokens": 999,
        }},
    })


def _transcript(tmp_path, *lines):
    p = tmp_path / "session.jsonl"
    p.write_text("\n".join(lines) + "\n")
    return p


def _run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def _token(out):
    lines = [l for l in out.splitlines() if l.startswith("CTXBUDGET:")]
    assert len(lines) == 1, f"expected exactly one verdict line, got {lines!r}"
    return lines[0]


class TestWhichNumberItReads:
    def test_sums_the_input_triple_not_just_cache_read(self, tmp_path):
        t = _transcript(tmp_path, _turn(read=90_000, create=5_000, fresh=1_000))
        assert cb.last_context_tokens(t) == 96_000

    def test_takes_the_last_turn_not_the_sum_of_turns(self, tmp_path):
        """cache_read is the whole prompt replayed each turn; adding turns up
        inflates by roughly the turn count and denies a session that is fine."""
        t = _transcript(tmp_path,
                        _turn(read=100_000), _turn(read=200_000), _turn(read=300_000))
        assert cb.last_context_tokens(t) == 300_000

    def test_ignores_subagent_turns(self, tmp_path):
        """The one that fails toward a false OK: a subagent's usage is written into
        the same file and is a fraction of the parent's context."""
        t = _transcript(tmp_path,
                        _turn(read=500_000), _turn(read=8_000, sidechain=True))
        assert cb.last_context_tokens(t) == 500_000

    def test_survives_malformed_and_usageless_lines(self, tmp_path):
        t = _transcript(tmp_path,
                        "{not json", json.dumps({"type": "user"}),
                        json.dumps(["a", "list"]), _turn(read=42_000))
        assert cb.last_context_tokens(t) == 42_000

    def test_an_all_zero_usage_block_does_not_overwrite_a_real_reading(self, tmp_path):
        """A usage dict can be present and empty of the input triple (a continuation
        or tool-only frame). Accepting its 0 as "the last turn" reports a 500k
        session as 0 -- pct=0.0, `OK`, and the run overflows on the next call.
        Zero is not a measurement; it is the absence of one."""
        t = _transcript(tmp_path,
                        _turn(read=500_000),
                        json.dumps({"isSidechain": False,
                                    "message": {"usage": {"output_tokens": 12}}}))
        assert cb.last_context_tokens(t) == 500_000

    def test_no_usage_anywhere_is_none_not_zero(self, tmp_path):
        """Zero would render as `pct=0.0` and pass -- the exact false OK."""
        t = _transcript(tmp_path, json.dumps({"type": "user", "message": {}}))
        assert cb.last_context_tokens(t) is None


class TestVerdict:
    def test_ok_below_the_ceiling(self, tmp_path):
        t = _transcript(tmp_path, _turn(read=100_000))
        r = _run("--transcript", str(t), "--window", "1000000")
        assert r.returncode == 0
        tok = _token(r.stdout)
        assert tok.startswith("CTXBUDGET: OK ")
        assert "used=100000" in tok and "pct=10.0" in tok

    def test_deny_above_the_ceiling(self, tmp_path):
        t = _transcript(tmp_path, _turn(read=525_742))
        r = _run("--transcript", str(t), "--window", "1000000")
        assert r.returncode == 0, "a verdict is not an operational error"
        assert _token(r.stdout).startswith("CTXBUDGET: DENY ")

    def test_projected_is_the_doubled_context(self, tmp_path):
        """The number the reader actually needs: what the TURN will cost."""
        t = _transcript(tmp_path, _turn(read=525_742))
        tok = _token(_run("--transcript", str(t), "--window", "1000000").stdout)
        assert "projected=1051484" in tok

    def test_the_measured_overflow_case_denies(self, tmp_path):
        """Regression pin on the live incident (session 97490faf): 525,742 on a 1M
        window produced 1,056,891 and overflowed."""
        t = _transcript(tmp_path, _turn(read=525_742))
        assert "DENY" in _token(_run("--transcript", str(t), "--window", "1000000").stdout)

    def test_ceiling_is_inclusive_at_45(self, tmp_path):
        t = _transcript(tmp_path, _turn(read=450_000))
        assert "OK" in _token(_run("--transcript", str(t), "--window", "1000000").stdout)

    def test_window_is_configurable(self, tmp_path):
        t = _transcript(tmp_path, _turn(read=100_000))
        assert "DENY" in _token(
            _run("--transcript", str(t), "--window", "200000").stdout)


class TestRunCeiling:
    """`--mode run` prices the RUN, not an advisor() call.

    Different question, different remedy: the 45 advisor ceiling is a margin under
    50 because advisor forwards a second full copy, whereas the run ceiling asks
    "is this session about to die mid-phase", where the remedy is halt-and-hand-off.
    Sharing a verdict word between them would let a reader apply the wrong remedy.
    """

    def test_run_mode_defaults_to_80(self, tmp_path):
        t = _transcript(tmp_path, _turn(read=790_000))
        tok = _token(_run("--transcript", str(t), "--window", "1000000", "--mode", "run").stdout)
        assert "ceiling=80" in tok
        assert tok.startswith("CTXBUDGET: OK ")

    def test_run_mode_halts_above_the_ceiling(self, tmp_path):
        t = _transcript(tmp_path, _turn(read=810_000))
        r = _run("--transcript", str(t), "--window", "1000000", "--mode", "run")
        assert r.returncode == 0, "a verdict is not an operational error"
        assert _token(r.stdout).startswith("CTXBUDGET: HALT ")

    def test_run_ceiling_is_inclusive_at_80(self, tmp_path):
        t = _transcript(tmp_path, _turn(read=800_000))
        assert "OK" in _token(
            _run("--transcript", str(t), "--window", "1000000", "--mode", "run").stdout)

    def test_run_mode_halt_is_not_the_advisor_deny_word(self, tmp_path):
        """The anti-conflation pin, and the reason this is a separate verdict word.

        `hooks/h-mad-advisor-gate.sh` blocks on the glob `*"CTXBUDGET: DENY"*`. If a
        run-ceiling breach also said DENY, the two verdicts would be indistinguishable
        to every existing consumer -- and they prescribe different actions.
        """
        t = _transcript(tmp_path, _turn(read=900_000))
        tok = _token(_run("--transcript", str(t), "--window", "1000000", "--mode", "run").stdout)
        assert "DENY" not in tok
        assert "mode=run" in tok

    def test_run_mode_omits_the_advisor_projection(self, tmp_path):
        """`projected` is `used * 2` because advisor forwards a second copy. A run
        cap forwards nothing, so printing it would invite reading the run ceiling as
        an advisor projection -- the exact conflation this mode exists to prevent."""
        t = _transcript(tmp_path, _turn(read=810_000))
        assert "projected=" not in _token(
            _run("--transcript", str(t), "--window", "1000000", "--mode", "run").stdout)

    def test_advisor_mode_output_is_unchanged(self, tmp_path):
        """Regression pin on the LIVE hook. Advisor mode is what
        `h-mad-advisor-gate.sh` parses today; adding run mode must not touch it."""
        t = _transcript(tmp_path, _turn(read=525_742))
        tok = _token(_run("--transcript", str(t), "--window", "1000000").stdout)
        assert tok == (
            "CTXBUDGET: DENY used=525742 window=1000000 "
            "pct=52.6 projected=1051484 ceiling=45"
        )

    def test_run_mode_still_cannot_judge_without_usage(self, tmp_path):
        """A cannot-judge stays a cannot-judge: it must not read as an OK just
        because the run ceiling is generous."""
        t = _transcript(tmp_path, json.dumps({"type": "user"}))
        r = _run("--transcript", str(t), "--window", "1000000", "--mode", "run")
        assert r.returncode == 2
        tok = _token(r.stdout)
        assert tok.startswith("CTXBUDGET: UNKNOWN")
        assert "used=" not in tok


class TestCannotJudge:
    @pytest.mark.parametrize("reason,args", [
        ("no_transcript", ("--transcript", "/nonexistent/session.jsonl")),
        ("bad_window", None),
    ])
    def test_unknown_exits_2_and_carries_no_used(self, tmp_path, reason, args):
        if args is None:
            t = _transcript(tmp_path, _turn(read=1_000))
            args = ("--transcript", str(t), "--window", "0")
        r = _run(*args)
        assert r.returncode == 2
        tok = _token(r.stdout)
        assert tok == f"CTXBUDGET: UNKNOWN reason={reason}", tok
        assert "used=" not in tok, "a cannot-judge must not look like a verdict"
        assert "ERROR:" in r.stderr

    def test_transcript_without_usage_is_unknown_not_ok(self, tmp_path):
        t = _transcript(tmp_path, json.dumps({"type": "user", "message": {}}))
        r = _run("--transcript", str(t))
        assert r.returncode == 2
        assert _token(r.stdout) == "CTXBUDGET: UNKNOWN reason=no_usage"


class TestResolution:
    def test_explicit_transcript_beats_the_environment(self, tmp_path, monkeypatch):
        other = _transcript(tmp_path, _turn(read=999_000))
        chosen = tmp_path / "chosen.jsonl"
        chosen.write_text(_turn(read=1_000) + "\n")
        monkeypatch.setenv("CLAUDE_TRANSCRIPT_PATH", str(other))
        assert cb.resolve_transcript(str(chosen), tmp_path) == chosen

    def test_env_used_when_no_explicit_path(self, tmp_path, monkeypatch):
        t = _transcript(tmp_path, _turn(read=1_000))
        monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "abc-123")
        monkeypatch.setenv("CLAUDE_TRANSCRIPT_PATH", str(t))
        assert cb.resolve_transcript(None, tmp_path) == t

    def test_session_id_beats_the_cwd_slug(self, tmp_path, monkeypatch):
        """The cwd slug names the SESSION's project root, not the process's cwd.
        Run from a subdirectory it resolves to a directory that does not exist and
        the tool is `UNKNOWN` forever -- the documented invocation returned exactly
        that before this branch existed."""
        monkeypatch.delenv("CLAUDE_TRANSCRIPT_PATH", raising=False)
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        proj = tmp_path / ".claude" / "projects" / "-some-repo"
        proj.mkdir(parents=True)
        mine = proj / "abc-123.jsonl"
        mine.write_text(_turn(read=1_000) + "\n")
        monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "abc-123")
        # cwd deliberately has no project dir of its own
        assert cb.resolve_transcript(None, tmp_path / "elsewhere") == mine

    def test_session_id_with_path_characters_is_refused(self, tmp_path, monkeypatch):
        """It is interpolated into a glob path, so `..` must not escape the projects
        tree. Asserting on a traversal that lands on nothing proves nothing -- the
        unvalidated version returns None there too, for the wrong reason. Plant a
        real file where the traversal WOULD land, so the refusal is what is measured.
        """
        monkeypatch.delenv("CLAUDE_TRANSCRIPT_PATH", raising=False)
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        (tmp_path / ".claude" / "projects" / "-a-repo").mkdir(parents=True)
        planted = tmp_path / ".claude" / "escaped.jsonl"
        planted.write_text(_turn(read=1_000) + "\n")
        monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "../../escaped")
        # sanity: the traversal really does reach it when unguarded
        import glob as _glob
        assert _glob.glob(str(tmp_path / ".claude" / "projects" / "*" /
                              "../../escaped.jsonl")), "traversal target unreachable"
        assert cb.resolve_transcript(None, tmp_path / "nope") is None

    def test_walks_up_from_a_subdirectory_when_no_session_id(self, tmp_path, monkeypatch):
        monkeypatch.delenv("CLAUDE_TRANSCRIPT_PATH", raising=False)
        monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        repo = tmp_path / "repo"
        (repo / "sub" / "deeper").mkdir(parents=True)
        proj = cb._project_dir(repo)
        proj.mkdir(parents=True)
        t = proj / "s.jsonl"
        t.write_text(_turn(read=7_000) + "\n")
        assert cb.resolve_transcript(None, repo / "sub" / "deeper") == t

    def test_explicit_path_beats_the_session_id(self, tmp_path, monkeypatch):
        chosen = tmp_path / "chosen.jsonl"
        chosen.write_text(_turn(read=1) + "\n")
        monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "abc-123")
        assert cb.resolve_transcript(str(chosen), tmp_path) == chosen

    def test_missing_project_dir_resolves_to_none(self, tmp_path, monkeypatch):
        monkeypatch.delenv("CLAUDE_TRANSCRIPT_PATH", raising=False)
        monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        assert cb.resolve_transcript(None, tmp_path / "no" / "such") is None

    def test_project_slug_matches_claude_code_layout(self, tmp_path, monkeypatch):
        """Non-alphanumerics become '-', so /Users/x/orca/skills is
        -Users-x-orca-skills. A wrong slug silently finds no transcript, which is
        an UNKNOWN -- safe, but it makes the tool useless by default."""
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        d = cb._project_dir(Path("/Users/x/orca/skills"))
        assert d.name == "-Users-x-orca-skills"


def test_stdlib_only():
    """Same constraint as every other h-mad helper: runs on a stock python3."""
    src = SCRIPT.read_text()
    for third_party in ("import requests", "import yaml", "import jsonschema"):
        assert third_party not in src
