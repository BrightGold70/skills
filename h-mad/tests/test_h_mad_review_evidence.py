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

from docsections import section_from

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


def _response(thinking, state="DONE", **usage):
    """An `agent_response` step. agy reports per-response `usage.thinking_tokens`
    here; it is the only place effort is visible without opening the report."""
    u = {"input_tokens": 100, "output_tokens": 50, "thinking_tokens": thinking}
    u.update(usage)
    return json.dumps({
        "event": "step_update",
        "step_update": {"step_type": "agent_response", "state": state, "usage": u},
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


CODEX_TEXT = """OpenAI Codex v0.153.2
--------
workdir: /Users/x/repo
model: gpt-5.6-terra
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR]
reasoning effort: high
--------
user
Review the diff between BASE and HEAD.
codex
I read scripts/h_mad_doc_block_exec.py lines 40-118 and the tests.
No Critical or Important issues.
ASSESSMENT: READY_TO_MERGE
"""


class TestUnsupportedFormat:
    """#154 — a gate's zero is only a measurement if the instrument can read that input.

    `EVIDENCE: NONE tools=0` fired on a codex review that verifiably read the tree,
    because this gate parses agy NDJSON and codex transcripts are `codex-text`. The
    blocker named a real hazard (a review that read nothing) that was not the one
    present, and cost a cycle to diagnose. A transcript this gate cannot parse is a
    cannot-judge carrying no counts — the same rule as a missing or empty log.
    """

    def test_a_codex_text_transcript_is_unreadable_not_none(self, tmp_path):
        log = tmp_path / "codex.log"
        log.write_text(CODEX_TEXT, encoding="utf-8")
        r = _run(str(log))
        tok = _token(r.stdout)
        assert tok == "EVIDENCE: UNREADABLE reason=unsupported_format", tok
        assert r.returncode == 2
        assert "tools=" not in tok and "ok=" not in tok, "a cannot-judge carries no counts"

    def test_stderr_names_what_the_gate_can_read(self, tmp_path):
        log = tmp_path / "codex.log"
        log.write_text(CODEX_TEXT, encoding="utf-8")
        err = _run(str(log)).stderr.lower()
        assert "agy" in err and "ndjson" in err, err

    def test_an_agy_log_with_no_tools_is_still_none_not_unreadable(self, tmp_path):
        """The two zeros this fix separates: `NONE` is an agy run that called no
        tool; `UNREADABLE` is a transcript the gate cannot read at all."""
        log = _log(tmp_path, json.dumps({"event": "init"}),
                   json.dumps({"event": "result", "result": {"status": "SUCCESS"}}))
        assert _token(_run(str(log)).stdout).startswith("EVIDENCE: NONE ")

    def test_scan_reports_the_format_it_saw(self, tmp_path):
        assert ev.scan(CODEX_TEXT)["agy_events"] == 0
        agy = "\n".join([json.dumps({"event": "init"}), _tool("view_file", "DONE")])
        assert ev.scan(agy)["agy_events"] >= 1

    def test_agrees_with_the_wrappers_own_log_classifier(self, tmp_path):
        """`hmad-dispatch` classifies the same file with `_exec_log_format`; the two
        instruments must not disagree about what an agy transcript is, or one
        renders it with the agy lens while the other calls it unreadable."""
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from test_hmad_dispatch import run_fn  # noqa: E402
        agy = tmp_path / "agy.log"
        agy.write_text(json.dumps({"event": "init"}) + "\n" + _tool("view_file", "DONE") + "\n",
                       encoding="utf-8")
        codex = tmp_path / "codex.log"
        codex.write_text(CODEX_TEXT, encoding="utf-8")
        # The divergent shape: a bare step_update line with no `event` key — what a
        # hand-built fixture emits, never agy. Both instruments must call it foreign.
        bare = tmp_path / "bare.log"
        bare.write_text(json.dumps({"step_update": {"step_type": "tool", "state": "DONE"}}) + "\n",
                        encoding="utf-8")
        for path, expect_shell, expect_agy in ((agy, "agy-ndjson", True),
                                               (codex, "codex-text", False),
                                               (bare, "codex-text", False)):
            shell = run_fn(f"_exec_log_format '{path}'").stdout.strip()
            assert shell == expect_shell, (path.name, shell)
            assert (ev.scan(path.read_text())["agy_events"] > 0) is expect_agy, path.name


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
        block = section_from(s, i)
        assert "result.status" in block or "`result.status`" in block

    def test_says_brief_with_the_question_never_the_answer(self):
        """#153: handing the reviewer the conclusion drove tools=12 -> tools=0."""
        text = self._skill()
        assert "never the answer" in text
        assert "tools=12" in text and "tools=0" in text

    def test_says_unsupported_format_is_a_cannot_judge(self):
        """#154: the skill must say a codex-text log is UNREADABLE, never tools=0,
        and that a codex review does not satisfy 6a-prime's evidence gate."""
        text = self._skill()
        assert "reason=unsupported_format" in text
        assert "codex" in text.split("reason=unsupported_format", 1)[1][:600].lower()

    def test_says_it_knows_no_tool_names(self):
        s = self._skill()
        i = s.index("h_mad_review_evidence.py")
        assert "run_command" in section_from(s, i)


# --- J49: effort must be visible without opening the NDJSON ------------------
#
# Across the 8 audit passes of cycles 21-24, every substantive finding came from a
# pass with high thinking tokens or ~34 tool calls. Cycle 21 pass A ran 0 tool
# calls and returned "CLEAN PASS" on a plan another pass proved defective; cycle 24
# double-cleaned with thinking collapsed to 6.2k/4.4k and exactly 2 tool calls each
# -- the `write_to_file` and the `.done` marker, i.e. no reads. At the verdict line
# that is indistinguishable from a real clean pass.
#
# THIS CLI reports effort and never decides — the scoping matters since #13.
# `h_mad_audit_cycle.combine()` now DOES decide on these same counts, in one
# direction: a pass at or below the delivery floor cannot certify a clean. The
# 2-call defence below is why that direction is the only one, and why the floor is
# checked after the findings loop: a pass that made 2 tool calls honoured the
# delivery contract exactly as asked, and one such pass in this very repo
# (5,356 thinking / 2 tools) still returned a REAL finding — which still counts.


class TestEffortIsReported:
    def test_thinking_tokens_are_summed_across_responses(self, tmp_path):
        log = _log(tmp_path, _response(4000), _response(2248),
                   _tool("view_file", "DONE"))

        tok = _token(_run(str(log)).stdout)

        assert "thinking=6248" in tok

    def test_thinking_is_zero_not_absent_when_no_response_carries_it(self, tmp_path):
        """An absent number and a zero are different facts, and `thinking=` missing
        from the line would make a hollow pass look like an older log format."""
        log = _log(tmp_path, _tool("view_file", "DONE"))

        assert "thinking=0" in _token(_run(str(log)).stdout)

    def test_only_completed_responses_count(self, tmp_path):
        """An ACTIVE step is the start of a response, not its outcome. Counting both
        double-counts every response's usage -- the same defect the tool counter
        already avoids by ignoring ACTIVE."""
        log = _log(tmp_path, _response(500, state="ACTIVE"), _response(500),
                   _tool("view_file", "DONE"))

        assert "thinking=500" in _token(_run(str(log)).stdout)

    def test_a_missing_usage_block_does_not_crash(self, tmp_path):
        line = json.dumps({"event": "step_update",
                           "step_update": {"step_type": "agent_response", "state": "DONE"}})
        log = _log(tmp_path, line, _tool("view_file", "DONE"))

        r = _run(str(log))

        assert r.returncode == 0
        assert "thinking=0" in _token(r.stdout)

    def test_a_null_thinking_value_reads_as_zero(self, tmp_path):
        """`thinking_tokens: null` appears in real logs and `None + int` raises."""
        log = _log(tmp_path, _response(None), _tool("view_file", "DONE"))

        r = _run(str(log))

        assert r.returncode == 0
        assert "thinking=0" in _token(r.stdout)

    def test_unreadable_still_carries_no_counts(self, tmp_path):
        """The cannot-judge rule extends to the new field: `thinking=0` on a log
        that was never read would be a measurement of nothing presented as zero."""
        r = _run(str(tmp_path / "gone.log"))

        tok = _token(r.stdout)
        assert "thinking=" not in tok
        assert "tools=" not in tok

    def test_effort_never_changes_the_verdict(self, tmp_path):
        """J49 is a scoring caveat, not a defect. Zero thinking with a successful
        read is still PASS; heavy thinking with no successful call is still NONE."""
        no_think = _log(tmp_path, _response(0), _tool("view_file", "DONE"), name="a.log")
        all_think = _log(tmp_path, _response(90_000), _tool("view_file", "ERROR"),
                         name="b.log")

        assert _token(_run(str(no_think)).stdout).startswith("EVIDENCE: PASS ")
        assert _token(_run(str(all_think)).stdout).startswith("EVIDENCE: NONE ")


# --- codex text transcripts (#27) --------------------------------------------
#
# #24 (`6f00f8c`) stopped this gate reporting a FALSE ZERO for a codex leg. It did
# not make the surface measurable -- `scan()` reads agy NDJSON only, so a codex
# leg's transcript yielded no figures at all and the gate was single-surface on a
# feature where codex carried 25 of 27 disagreements.
#
# The fixtures are REAL transcripts from live runs, not hand-built: a hand-built
# one does not have the shape the CLI emits, which is the whole reason H7's
# prototype was copied rather than written. Only the echoed prompt is elided, and
# the elision was accepted only after `scan_codex_text(full) == scan_codex_text(elided)`
# was executed on the originals.

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CODEX_8 = FIXTURES / "codex-text-8-exec.log"
CODEX_0 = FIXTURES / "codex-text-0-exec.log"


def _evidence():
    sys.path.insert(0, str(SCRIPT.parent))
    import importlib
    return importlib.import_module("h_mad_review_evidence")


def test_a_codex_transcript_that_ran_tools_is_measured() -> None:
    """The CONTROL, and it must not read as hollow.

    Calibrating a new instrument only against the artifact that motivated it is how
    a detector that fires on everything ships. This is a real design-audit leg that
    did read the tree.
    """
    m = _evidence()
    got = m.scan_codex_text(CODEX_8.read_text(encoding="utf-8", errors="replace"))
    assert got["tools"] == 8 and got["ok"] == 8 and got["failed"] == 0, got
    assert got["complete"] is True
    assert got["agrees"] is True, "the two instruments disagree on a clean transcript"


def test_a_codex_leg_that_ran_NOTHING_is_now_visible() -> None:
    """The finding this closes, from a real `doc-block-exec` archreview.

    That leg made zero tool calls -- its own output says `The requested view_file
    tool is unavailable in this session, so I could not inspect the worktree` --
    and it emitted `ASSESSMENT: NO` anyway, a verdict over a tree it never read.
    196,184 tokens consumed. Before this, the gate could not see any of it.

    This is a MEASURED zero, which is exactly what #24 said a codex zero was not
    allowed to be until it could be measured. The difference is `complete`.
    """
    m = _evidence()
    got = m.scan_codex_text(CODEX_0.read_text(encoding="utf-8", errors="replace"))
    assert got["tools"] == 0 and got["complete"] is True, got


def test_a_truncated_codex_transcript_is_NOT_tools_zero() -> None:
    """#24's lesson, one level down: "could not measure" and "measured zero" must
    never take the same branch. A transcript without the trailing token total was
    killed, is still running, or was copied mid-write."""
    m = _evidence()
    got = m.scan_codex_text("OpenAI Codex v0.151.0\n exec\n succeeded in 3ms:\n")
    assert got["complete"] is False, got
    # This sample also exercises the cross-check: `exec` is indented here, so the
    # two instruments DISAGREE and that must be reported rather than reconciled by
    # silently preferring one of them.
    assert got["exec_lines"] == 0 and got["tools"] == 1, got
    assert got["agrees"] is False, got


def test_a_non_codex_transcript_returns_None_not_a_zero_row() -> None:
    """None is refusal. A dict of zeros would be a measurement of a file this
    instrument cannot read -- the mode-15 trap."""
    m = _evidence()
    assert m.scan_codex_text('{"event":"init"}\n') is None
    assert m.scan_codex_text("") is None


def test_the_gate_reports_codex_figures_but_still_refuses_the_leg(tmp_path) -> None:
    """A codex leg does not SATISFY the 6a-prime gate -- #24's rule, unchanged, so
    the rc stays 2 and the verdict stays a cannot-judge. What changes is that the
    numbers are printed, so a leg that read nothing is visible rather than merely
    unjudged."""
    log = tmp_path / "codex.log"
    log.write_text(CODEX_0.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), str(log)],
                       capture_output=True, text=True)
    assert r.returncode == 2, r.stdout + r.stderr
    # The codex numbers ride their OWN token. On the EVIDENCE line they would be
    # globbed as agy counts, and #24's whole point is that those two zeros differ.
    assert "CODEXEVIDENCE: tools=0 ok=0 failed=0" in r.stdout, r.stdout
    assert "EVIDENCE: UNREADABLE reason=unsupported_format" in r.stdout, r.stdout
    assert "EVIDENCE: NONE" not in r.stdout, "a codex leg must never render as a measured agy NONE"


def test_a_truncated_codex_transcript_gets_its_own_reason(tmp_path) -> None:
    log = tmp_path / "codex.log"
    log.write_text("OpenAI Codex v0.151.0\nexec\n succeeded in 3ms:\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), str(log)],
                       capture_output=True, text=True)
    assert r.returncode == 2
    assert "CODEXEVIDENCE: UNREADABLE reason=truncated_no_token_total" in r.stdout, r.stdout
    assert "CODEXEVIDENCE: tools=" not in r.stdout, "a truncated transcript must publish no count"


def test_the_agy_path_is_untouched_by_the_codex_branch() -> None:
    """The codex branch is reached only when there are no agy events, so an agy
    transcript must measure exactly as before."""
    m = _evidence()
    agy = "\n".join([
        json.dumps({"event": "init"}),
        json.dumps({"event": "step_update", "tool": "read", "status": "OK"}),
        json.dumps({"event": "result"}),
    ])
    counts = m.scan(agy)
    assert counts["agy_events"] >= 1
    assert m.scan_codex_text(agy) is None
