"""The advisor gate is the mechanical half of the context-budget rule.

The doc rule ("never above ~45% window used") is one the orchestrator can talk
itself out of, and it is most tempting to do so at exactly the point where being
wrong ends the run. This hook makes it a refusal.

Every test here is about a way the gate is WORSE than no gate:

  * blocking on a cannot-judge. The budget script exits 2 on UNKNOWN, and a hook
    that inherits that rc blocks -- PreToolUse exit 2 means deny. A fresh session
    has no usage record yet, so the naive version denies the early, cheap call the
    ladder actually recommends. Read the token, never the rc.
  * blocking a tool that is not advisor. A gate that fires on the wrong tool gets
    removed wholesale, taking the real rule with it.
  * blocking with no way out. A deny that does not teach the escape is a deny that
    gets disabled at the settings level.
  * measuring the wrong session. The harness hands the hook `transcript_path`; if
    it is ignored, the gate scores whatever ambient session it can find.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / "h-mad" / "hooks" / "h-mad-advisor-gate.sh"
BUDGET = REPO_ROOT / "h-mad" / "scripts" / "h_mad_context_budget.py"


def _turn(read):
    return json.dumps({
        "isSidechain": False,
        "message": {"usage": {"input_tokens": 0,
                              "cache_creation_input_tokens": 0,
                              "cache_read_input_tokens": read}},
    })


def _transcript(tmp_path, read, name="session.jsonl"):
    p = tmp_path / name
    p.write_text(_turn(read) + "\n")
    return p


def _run(payload, tmp_path, **env):
    """Hermetic: no ambient session may leak in and decide the verdict."""
    e = dict(os.environ)
    for leak in ("CLAUDE_TRANSCRIPT_PATH", "CLAUDE_CODE_SESSION_ID",
                 "HMAD_ADVISOR_OVERRIDE", "HMAD_CONTEXT_WINDOW",
                 "HMAD_CONTEXT_CEILING"):
        e.pop(leak, None)
    e["HOME"] = str(tmp_path / "home")
    (tmp_path / "home").mkdir(exist_ok=True)
    e["HMAD_CONTEXT_BUDGET_SCRIPT"] = str(BUDGET)
    e.update({k: str(v) for k, v in env.items()})
    return subprocess.run(["bash", str(HOOK)], input=json.dumps(payload),
                          capture_output=True, text=True, env=e)


class TestItBlocksTheExpensiveCall:
    def test_denies_above_the_ceiling(self, tmp_path):
        t = _transcript(tmp_path, 525_742)
        r = _run({"tool_name": "advisor", "transcript_path": str(t)}, tmp_path)
        assert r.returncode == 2, r.stderr
        assert "BLOCK" in r.stderr
        assert "CTXBUDGET: DENY" in r.stderr

    def test_the_block_names_the_substitutes_and_the_override(self, tmp_path):
        """A deny with no escape gets removed from settings.json, and then the
        rule is gone entirely rather than merely ignored once."""
        t = _transcript(tmp_path, 525_742)
        err = _run({"tool_name": "advisor", "transcript_path": str(t)}, tmp_path).stderr
        assert "exec agy" in err
        assert "fork" in err
        assert "/compact" in err
        assert "HMAD_ADVISOR_OVERRIDE=1" in err

    def test_the_block_names_the_assumed_window(self, tmp_path):
        """The window is a guess from an env default. If the model's window is
        smaller, the percentage is wrong and the reader must be able to see why."""
        t = _transcript(tmp_path, 525_742)
        err = _run({"tool_name": "advisor", "transcript_path": str(t)}, tmp_path).stderr
        assert "1000000" in err
        assert "HMAD_CONTEXT_WINDOW" in err


class TestItDoesNotBlockAnythingElse:
    def test_allows_below_the_ceiling(self, tmp_path):
        t = _transcript(tmp_path, 100_000)
        r = _run({"tool_name": "advisor", "transcript_path": str(t)}, tmp_path)
        assert r.returncode == 0, r.stderr

    def test_a_cannot_judge_allows(self, tmp_path):
        """THE inverted-design case: the budget script exits 2 on UNKNOWN. Under
        `set -e`, or on any rc-based branch, that becomes a BLOCK -- denying the
        early cheap call the ladder recommends, in a session too fresh to measure."""
        r = _run({"tool_name": "advisor",
                  "transcript_path": str(tmp_path / "nope.jsonl")}, tmp_path)
        assert r.returncode == 0, r.stderr

    def test_a_transcript_with_no_usage_yet_allows(self, tmp_path):
        p = tmp_path / "fresh.jsonl"
        p.write_text(json.dumps({"type": "user", "message": {}}) + "\n")
        r = _run({"tool_name": "advisor", "transcript_path": str(p)}, tmp_path)
        assert r.returncode == 0, r.stderr

    @pytest.mark.parametrize("tool", ["Bash", "Read", "Advisor", ""])
    def test_only_advisor_is_gated(self, tmp_path, tool):
        t = _transcript(tmp_path, 525_742)
        r = _run({"tool_name": tool, "transcript_path": str(t)}, tmp_path)
        assert r.returncode == 0, f"{tool!r} was blocked: {r.stderr}"

    def test_malformed_payload_allows(self, tmp_path):
        e = dict(os.environ)
        e["HOME"] = str(tmp_path)
        e["HMAD_CONTEXT_BUDGET_SCRIPT"] = str(BUDGET)
        e.pop("HMAD_ADVISOR_OVERRIDE", None)
        r = subprocess.run(["bash", str(HOOK)], input="{not json",
                           capture_output=True, text=True, env=e)
        assert r.returncode == 0, r.stderr

    def test_missing_budget_script_allows(self, tmp_path):
        """A gate that cannot measure must not block; an install mid-repair would
        otherwise wedge every advisor call with no explanation."""
        t = _transcript(tmp_path, 525_742)
        r = _run({"tool_name": "advisor", "transcript_path": str(t)}, tmp_path,
                 HMAD_CONTEXT_BUDGET_SCRIPT=str(tmp_path / "gone.py"))
        assert r.returncode == 0, r.stderr

    def test_override_wins_even_over_a_deny(self, tmp_path):
        t = _transcript(tmp_path, 525_742)
        r = _run({"tool_name": "advisor", "transcript_path": str(t)}, tmp_path,
                 HMAD_ADVISOR_OVERRIDE=1)
        assert r.returncode == 0, r.stderr


class TestItMeasuresTheSessionItWasHanded:
    def test_transcript_path_from_the_payload_decides(self, tmp_path):
        """Both files exist; only the one the harness named may be scored."""
        big = _transcript(tmp_path, 525_742, "big.jsonl")
        small = _transcript(tmp_path, 10_000, "small.jsonl")
        assert _run({"tool_name": "advisor", "transcript_path": str(big)},
                    tmp_path).returncode == 2
        assert _run({"tool_name": "advisor", "transcript_path": str(small)},
                    tmp_path).returncode == 0

    def test_ceiling_and_window_are_configurable(self, tmp_path):
        t = _transcript(tmp_path, 100_000)
        assert _run({"tool_name": "advisor", "transcript_path": str(t)},
                    tmp_path, HMAD_CONTEXT_WINDOW=200_000).returncode == 2
        assert _run({"tool_name": "advisor", "transcript_path": str(t)},
                    tmp_path, HMAD_CONTEXT_WINDOW=200_000,
                    HMAD_CONTEXT_CEILING=90).returncode == 0


def test_hook_is_executable_and_not_set_e():
    """`set -e` here would turn the budget script's exit-2 cannot-judge into a
    block. The absence is load-bearing, so assert it rather than trusting it."""
    src = HOOK.read_text()
    assert os.access(HOOK, os.X_OK)
    assert "set -uo pipefail" in src
    assert "set -euo pipefail" not in src
