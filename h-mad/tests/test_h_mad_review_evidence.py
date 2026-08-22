"""Tests for the 6a-prime evidence gate (J40).

The defect: a review that made ONE tool call, which errored, whose result carried
`status: ERROR`, and which had therefore read no files at all, returned
`ASSESSMENT: READY_TO_MERGE` -- and `exec` rc, `h_mad_extract_verdict.py` and the
Phase-7 gate all accepted it. The verdict line was well-formed; the evidence under
it did not exist.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "h-mad" / "scripts" / "h_mad_review_evidence.py"
sys.path.insert(0, str(SCRIPT.parent))

import h_mad_review_evidence as ev  # noqa: E402


def _tool(name, state, **info):
    return json.dumps({
        "event": "step_update",
        "step_update": {
            "step_type": "tool",
            "tool_name": name,
            "state": state,
            "tool_info": {"name": name, "parameters": info},
        },
    })


def _log(tmp_path, *lines, name="run.log"):
    p = tmp_path / name
    p.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return p


def _run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True)


def _token(out):
    lines = [l for l in out.splitlines() if l.startswith("EVIDENCE:")]
    assert len(lines) == 1, f"expected exactly one verdict line, got {lines!r}"
    return lines[0]


class TestVerdict:
    def test_one_successful_tool_call_is_evidence(self, tmp_path):
        log = _log(tmp_path, _tool("view_file", "ACTIVE"), _tool("view_file", "DONE"))
        tok = _token(_run(str(log)).stdout)
        assert tok.startswith("EVIDENCE: PASS ")
        assert "ok=1" in tok

    def test_the_measured_j40_case_is_none(self, tmp_path):
        """Regression pin on the live incident: one view_file, it errored."""
        log = _log(tmp_path,
                   _tool("view_file", "ACTIVE", AbsolutePath="/scratch/nope.py"),
                   _tool("view_file", "ERROR", AbsolutePath="/scratch/nope.py"))
        r = _run(str(log))
        assert r.returncode == 0, "a verdict is not an operational error"
        tok = _token(r.stdout)
        assert tok.startswith("EVIDENCE: NONE ")
        assert "ok=0" in tok and "failed=1" in tok

    def test_a_log_with_no_tool_calls_at_all_is_none(self, tmp_path):
        log = _log(tmp_path, json.dumps({"event": "init"}),
                   json.dumps({"event": "result", "result": {"status": "SUCCESS"}}))
        tok = _token(_run(str(log)).stdout)
        assert tok.startswith("EVIDENCE: NONE ")
        assert "tools=0" in tok

    def test_counts_ANY_tool_name_not_a_hardcoded_list(self, tmp_path):
        """The J40 sibling defect: a name-specific probe reported a false zero.

        agy used view_file/grep_search on one dispatch and run_command on the next.
        A check that knows tool names cannot survive the agent changing its mind.
        """
        log = _log(tmp_path,
                   _tool("run_command", "DONE"),
                   _tool("some_tool_invented_next_year", "DONE"))
        tok = _token(_run(str(log)).stdout)
        assert tok.startswith("EVIDENCE: PASS ")
        assert "ok=2" in tok

    def test_mixed_success_and_failure_still_passes(self, tmp_path):
        """One good read is evidence, even alongside failures."""
        log = _log(tmp_path, _tool("view_file", "ERROR"), _tool("grep_search", "DONE"))
        tok = _token(_run(str(log)).stdout)
        assert tok.startswith("EVIDENCE: PASS ")
        assert "ok=1" in tok and "failed=1" in tok


class TestCannotJudge:
    def test_missing_log_is_unreadable_not_none(self, tmp_path):
        """"I could not look" and "I looked and found nothing" are opposite facts.

        NONE says the review read nothing -- act on it. UNREADABLE says the check
        did not run, which is not a verdict about the review at all.
        """
        r = _run(str(tmp_path / "does-not-exist.log"))
        assert r.returncode == 2
        tok = _token(r.stdout)
        assert tok.startswith("EVIDENCE: UNREADABLE")

    def test_unreadable_carries_no_counts(self, tmp_path):
        """Same discipline as CTXBUDGET: UNKNOWN -- a cannot-judge must not be
        mistakable for a zero count."""
        tok = _token(_run(str(tmp_path / "nope.log")).stdout)
        assert "ok=" not in tok and "tools=" not in tok

    def test_empty_log_is_unreadable(self, tmp_path):
        """`format: empty` (started, emitted nothing) is not `no tool calls`."""
        log = _log(tmp_path)
        r = _run(str(log))
        assert r.returncode == 2
        assert _token(r.stdout).startswith("EVIDENCE: UNREADABLE")


class TestRobustness:
    def test_survives_non_json_and_heartbeat_lines(self, tmp_path):
        """The log legitimately carries `#hmad-beat` lines and caller content."""
        log = _log(tmp_path, "#hmad-beat", "not json at all",
                   json.dumps(["a", "list"]), _tool("view_file", "DONE"))
        assert "ok=1" in _token(_run(str(log)).stdout)

    def test_result_status_is_reported_but_does_not_decide(self, tmp_path):
        """status=ERROR beside a successful tool call is NOT absence of evidence.

        hmad-dispatch ignores .status deliberately: a single denied tool call yields
        status ERROR alongside a complete correct answer. This gate must agree, or it
        re-creates the false no_verdict halt that reasoning exists to prevent.
        """
        log = _log(tmp_path, _tool("view_file", "DONE"),
                   json.dumps({"event": "result", "result": {"status": "ERROR"}}))
        tok = _token(_run(str(log)).stdout)
        assert tok.startswith("EVIDENCE: PASS ")
        assert "status=ERROR" in tok, "surface it for triage, but do not gate on it"


class TestDocumented:
    """A gate nobody is obliged to run is documentation, not a gate.

    This repo's own history: the PREFLIGHT token detected stale pins correctly for a
    long time while no step was obliged to consume it, which made a correct signal
    advisory. Pin the obligation, not just the script.
    """

    def _skill(self) -> str:
        return (REPO_ROOT / "h-mad" / "SKILL.md").read_text(encoding="utf-8")

    def test_6a_prime_names_the_evidence_gate(self):
        s = self._skill()
        assert "h_mad_review_evidence.py" in s
        assert "EVIDENCE:" in s

    def test_states_the_halt_route(self):
        assert "step6a-prime:review_read_nothing" in self._skill()

    def test_halt_route_is_in_failure_recovery(self):
        fr = (REPO_ROOT / "h-mad" / "references" / "failure-recovery.md").read_text(encoding="utf-8")
        assert "review_read_nothing" in fr

    def test_warns_that_a_correct_cd_is_not_sufficient(self):
        """The path failure is what made the blind review possible in the first place."""
        s = self._skill()
        assert "ABSOLUTE path" in s
        assert "scratch" in s

    def test_says_it_does_not_gate_on_result_status(self):
        """Guarding the reasoning, not just the behaviour: a future editor who adds a
        status check would re-create the false no_verdict halt hmad-dispatch avoids."""
        s = self._skill()
        i = s.index("h_mad_review_evidence.py")
        assert "result.status" in s[i:i + 3000] or "`result.status`" in s[i:i + 3000]

    def test_says_it_knows_no_tool_names(self):
        s = self._skill()
        i = s.index("h_mad_review_evidence.py")
        assert "run_command" in s[i:i + 3000]
