"""The 6a-prime loop was hand-assembled seven times in one session, and once more
while closing J43 in this one.

Seven mechanical steps, every one already prescribed by SKILL.md: rebuild the
prompt from `agy-architectural-reviewer-prompt.md`, substitute
feature/BASE/HEAD/diff/design, append the absolute-path instructions, re-stamp the
HEAD sha, dispatch `exec agy`, run the evidence gate on the log, extract
`ASSESSMENT:`. Two of them have no other home and are the two that get skipped:

  * **the BASE/HEAD stamp** — a stale sha silently reviews the PREVIOUS commit and
    reports cleanly, which is the J41 failure one level up; and
  * **the evidence gate** — `EVIDENCE: PASS tools=N` is the only thing separating a
    review that read from one that merely sounds like it did. Measured: a 6a-prime
    dispatch whose single `view_file` errored returned `READY_TO_MERGE` in 1510
    confident bytes, and rc, the extractor and the Phase-7 gate all took it.

Deliberately NOT modelled on `audit-cycle`, despite the candidate row asking for
"an audit-cycle for the architectural gate". That tool is a multi-pass verdict
COMBINER — it takes `--pass` specs of runs that already finished, fans out N
parallel passes, and rejects any phase outside plan/design/impl-plan. 6a-prime is
one reviewer re-run sequentially after fixes, emitting a word rather than finding
counts. Same name, different machine.

**This driver runs exactly one cycle and refuses to decide whether to run
another.** That judgement is the operator's: the seven-cycle run went to seven
because cycle 3 came back clean and cycle 4 then found a Critical vacuous pass. A
loop-until-clean driver would have stopped at three and shipped the defect.

Split into `stage` and `score` for the same reason `h_mad_assemble_tdd.py` stages
rather than dispatches: the dispatch is the side-effecting, agy-dependent,
minutes-long part, while assembly and scoring are pure and testable. Both halves
of the skip-prone pair land in the tested halves.
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "h_mad_archreview_cycle.py"

VALID_STATE = {
    "feature": "feat", "started_ts": "2026-08-28T00:00:00Z",
    "last_completed_phase": 5, "current_phase": 6, "phase": None,
    "audit_cycles": {"plan": 0, "design": 0, "impl_plan": 0},
    "iterate_cycles": 0, "halt_reason": None, "halt_ts": None,
}


def _state(tmp_path: Path) -> Path:
    p = tmp_path / "bkit.json"
    p.write_text(json.dumps({"orchestrator_state": {"feat": dict(VALID_STATE)}}),
                 encoding="utf-8")
    return p


def _log(tmp_path: Path, tools: int) -> Path:
    """A dispatch log carrying `tools` completed tool calls."""
    p = tmp_path / "run.log"
    # The shape `h_mad_review_evidence.scan` actually reads: a `step_update` whose
    # `step_type` is "tool" and whose `state` is DONE. Built from the real reader
    # rather than from memory of the log format — a fixture in the wrong shape
    # reports zero tools, which is indistinguishable from a review that read
    # nothing, and would have made every evidence assertion here vacuous.
    # Bracketed with the `init`/`result` events every real agy transcript carries,
    # so a zero-tool log is an agy run that called nothing (NO_EVIDENCE) rather
    # than an empty or foreign file (UNREADABLE) — the two zeros #154 separates.
    lines = [json.dumps({"event": "init"})]
    for i in range(tools):
        lines.append(json.dumps({
            "event": "step_update",
            "step_update": {"step_type": "tool", "state": "DONE", "name": f"view_file_{i}"},
        }))
    lines.append(json.dumps({"event": "result", "result": {"status": "SUCCESS"}}))
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def _codex_text_log(tmp_path: Path) -> Path:
    p = tmp_path / "codex.log"
    p.write_text("OpenAI Codex v0.153.2\n--------\nworkdir: /x\n--------\nuser\nreview\n"
                 "codex\nI read the files.\nASSESSMENT: READY_TO_MERGE\n", encoding="utf-8")
    return p


def _review(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "review.md"
    p.write_text(body, encoding="utf-8")
    return p


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True)


class TestScoreRecordsOnlyAProvenReview:
    """The gate order is the contract: evidence BEFORE verdict, always."""

    def test_a_read_review_is_recorded_and_read_back(self, tmp_path):
        state = _state(tmp_path)
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(_log(tmp_path, 12)),
                      "--review", str(_review(tmp_path, "ok\nASSESSMENT: READY_TO_MERGE\n")))

        assert result.returncode == 0, result.stdout + result.stderr
        assert "ARCHREVIEW: READY_TO_MERGE" in result.stdout
        assert "tools=12" in result.stdout
        record = json.loads(state.read_text())["orchestrator_state"]["feat"]
        assert record["archreview"] == "READY_TO_MERGE"

    def test_the_owners_score_write_beats_the_heartbeat(self, tmp_path):
        """#126 applied to h-mad's own writer: score --session-id <owner> refreshes."""
        state = tmp_path / "bkit.json"
        rec = dict(VALID_STATE, owner_session_id="me", owner_heartbeat_ts="2026-07-22T00:00:00Z")
        state.write_text(json.dumps({"orchestrator_state": {"feat": rec}}), encoding="utf-8")
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(_log(tmp_path, 4)),
                      "--review", str(_review(tmp_path, "ASSESSMENT: READY_TO_MERGE\n")),
                      "--session-id", "me")
        assert result.returncode == 0, result.stdout + result.stderr
        stored = json.loads(state.read_text())["orchestrator_state"]["feat"]
        assert stored["archreview"] == "READY_TO_MERGE"
        assert stored["owner_heartbeat_ts"] != "2026-07-22T00:00:00Z"

    def test_a_codex_text_log_is_a_cannot_judge_not_no_evidence(self, tmp_path):
        """#154. A transcript this gate cannot parse must not score as a review that
        read nothing: the diagnosis was wrong for a cycle. Records nothing either way."""
        state = _state(tmp_path)
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(_codex_text_log(tmp_path)),
                      "--review", str(_review(tmp_path, "ASSESSMENT: READY_TO_MERGE\n")))
        assert result.returncode == 2
        assert "ARCHREVIEW: UNREADABLE reason=unsupported_format" in result.stdout, result.stdout
        assert "NO_EVIDENCE" not in result.stdout
        assert "archreview" not in json.loads(state.read_text())["orchestrator_state"]["feat"]

    def test_an_unreadable_log_is_a_cannot_judge_with_a_token_not_a_traceback(self, tmp_path):
        """Review finding: the log was read outside the try, so a mode-000 or
        non-UTF-8 log crashed at exit 1 with NO ARCHREVIEW: token at all."""
        import os
        state = _state(tmp_path)
        log = _log(tmp_path, 3)
        os.chmod(log, 0)
        try:
            result = _run("score", "--feature", "feat", "--state", str(state),
                          "--log", str(log),
                          "--review", str(_review(tmp_path, "ASSESSMENT: READY_TO_MERGE\n")))
        finally:
            os.chmod(log, 0o644)
        if os.geteuid() == 0:
            return  # root reads a mode-000 file; the probe cannot run as root
        assert result.returncode == 2, result.stderr
        assert "ARCHREVIEW: UNREADABLE reason=log:" in result.stdout, result.stdout
        assert "Traceback" not in result.stderr
        assert "archreview" not in json.loads(state.read_text())["orchestrator_state"]["feat"]

    def test_a_non_utf8_log_does_not_crash(self, tmp_path):
        state = _state(tmp_path)
        log = tmp_path / "run.log"
        log.write_bytes(b"\xff\xfe not utf-8 \n" + json.dumps({"event": "init"}).encode()
                        + b"\n" + json.dumps({"event": "step_update", "step_update": {
                            "step_type": "tool", "state": "DONE"}}).encode() + b"\n")
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(log),
                      "--review", str(_review(tmp_path, "ASSESSMENT: READY_TO_MERGE\n")))
        assert "Traceback" not in result.stderr
        assert "ARCHREVIEW: READY_TO_MERGE" in result.stdout, result.stdout

    def test_a_review_that_read_nothing_is_refused_and_records_nothing(self, tmp_path):
        """The 1510-confident-bytes case. The verdict line says READY_TO_MERGE and
        it must not reach state — recording it is what made the defect survivable."""
        state = _state(tmp_path)
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(_log(tmp_path, 0)),
                      "--review", str(_review(tmp_path, "ASSESSMENT: READY_TO_MERGE\n")))

        assert result.returncode == 2
        assert "ARCHREVIEW: NO_EVIDENCE" in result.stdout
        assert "step6a-prime:review_read_nothing" in result.stdout
        assert "archreview" not in json.loads(state.read_text())["orchestrator_state"]["feat"]

    def test_a_missing_verdict_is_refused_and_records_nothing(self, tmp_path):
        state = _state(tmp_path)
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(_log(tmp_path, 5)),
                      "--review", str(_review(tmp_path, "I looked at some files.\n")))

        assert result.returncode == 2
        assert "ARCHREVIEW: NO_VERDICT" in result.stdout
        assert "step6a-prime:no_verdict" in result.stdout
        assert "archreview" not in json.loads(state.read_text())["orchestrator_state"]["feat"]

    def test_a_failing_verdict_is_recorded_and_halts(self, tmp_path):
        """WITH_FIXES is a real verdict — it must be recorded, and it must halt."""
        state = _state(tmp_path)
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(_log(tmp_path, 3)),
                      "--review", str(_review(tmp_path, "ASSESSMENT: WITH_FIXES\n")))

        assert result.returncode == 0, result.stdout
        assert "ARCHREVIEW: WITH_FIXES" in result.stdout
        assert "step6a-prime:architectural_review_failed" in result.stdout
        assert json.loads(state.read_text())["orchestrator_state"]["feat"]["archreview"] == "WITH_FIXES"

    def test_the_last_assessment_wins(self, tmp_path):
        """Same rule as every other extractor here: a log carries the prompt before
        the answer, so a first-match read returns the instruction's own echo."""
        state = _state(tmp_path)
        # BOTH lines must be line-anchored, or the regex sees one match and
        # first-vs-last is untestable. The first draft opened the echo with "emit",
        # which never matched — the mutation surviving is what exposed it, and a
        # tidy fixture is exactly how that hides.
        body = ("Instructions said:\n"
                "ASSESSMENT: READY_TO_MERGE\n"
                "...having actually read the diff...\n"
                "ASSESSMENT: WITH_FIXES\n")
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(_log(tmp_path, 4)),
                      "--review", str(_review(tmp_path, body)))

        assert "ARCHREVIEW: WITH_FIXES" in result.stdout, result.stdout

    def test_an_unreadable_log_is_a_cannot_judge_not_a_verdict(self, tmp_path):
        state = _state(tmp_path)
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(tmp_path / "nope.log"),
                      "--review", str(_review(tmp_path, "ASSESSMENT: READY_TO_MERGE\n")))

        assert result.returncode == 2
        assert "ARCHREVIEW: UNREADABLE" in result.stdout
        assert "READY_TO_MERGE" not in result.stdout

    def test_a_dropped_write_is_caught_by_the_readback(self, tmp_path):
        """`archreview` is not in the schema's `required`, so strict validation
        passes over a write that never landed. The read-back is the only check."""
        state = _state(tmp_path)
        log = _log(tmp_path, 4)
        review = _review(tmp_path, "ASSESSMENT: READY_TO_MERGE\n")
        # The DIRECTORY, not the file: the writer replaces atomically, and
        # `os.replace` needs only directory write permission — a read-only file is
        # still replaced. Simulating the drop the wrong way would have made this
        # test pass for a driver with no read-back at all.
        state.parent.chmod(0o555)
        try:
            result = _run("score", "--feature", "feat", "--state", str(state),
                          "--log", str(log), "--review", str(review))
            assert result.returncode == 2, result.stdout
            assert "ARCHREVIEW: NOT_RECORDED" in result.stdout
        finally:
            state.parent.chmod(0o755)


class TestStage:
    def _tpl(self, tmp_path):
        t = tmp_path / "tpl.md"
        t.write_text(
            "feature <INLINE_FEATURE>\nbase <INLINE_BASE_SHA>\nhead <INLINE_HEAD_SHA>\n"
            "files <INLINE_DIFF_FILES>\ndesign <INLINE_AUDITED_DESIGN>\n"
            "summary <INLINE_PHASE_5_SUMMARY>\n", encoding="utf-8")
        return t

    def test_every_placeholder_is_substituted(self, tmp_path):
        design = tmp_path / "d.md"
        design.write_text("the design\n", encoding="utf-8")
        prompt = tmp_path / "p.txt"
        result = _run("stage", "--feature", "feat", "--template", str(self._tpl(tmp_path)),
                      "--base", "aaa1111", "--head", "bbb2222",
                      "--design", str(design), "--diff-files", "a.py\nb.py",
                      "--summary", "did things", "--prompt", str(prompt))

        assert result.returncode == 0, result.stdout + result.stderr
        body = prompt.read_text(encoding="utf-8")
        assert "<INLINE_" not in body, body

    def test_an_unsubstituted_placeholder_is_refused(self, tmp_path):
        """A prompt shipped with a live `<INLINE_…>` in it asks the reviewer to
        review a placeholder, and it reads as a real prompt to everything else."""
        t = tmp_path / "tpl.md"
        t.write_text("feature <INLINE_FEATURE>\nmystery <INLINE_SOMETHING_ELSE>\n",
                     encoding="utf-8")
        design = tmp_path / "d.md"
        design.write_text("d\n", encoding="utf-8")
        result = _run("stage", "--feature", "feat", "--template", str(t),
                      "--base", "a", "--head", "b", "--design", str(design),
                      "--diff-files", "x.py", "--summary", "s",
                      "--prompt", str(tmp_path / "p.txt"))

        assert result.returncode == 2, result.stdout
        assert "ARCHREVIEW: UNSUBSTITUTED" in result.stdout
        assert "INLINE_SOMETHING_ELSE" in result.stdout

    def test_base_and_head_must_differ(self, tmp_path):
        """A stale stamp is the J41 failure one level up: BASE == HEAD reviews an
        empty diff and comes back clean, which reads exactly like a passing review."""
        design = tmp_path / "d.md"
        design.write_text("d\n", encoding="utf-8")
        result = _run("stage", "--feature", "feat", "--template", str(self._tpl(tmp_path)),
                      "--base", "same", "--head", "same", "--design", str(design),
                      "--diff-files", "x.py", "--summary", "s",
                      "--prompt", str(tmp_path / "p.txt"))

        assert result.returncode == 2, result.stdout
        assert "ARCHREVIEW: DEGENERATE_RANGE" in result.stdout

    def test_the_printed_command_carries_the_log_the_score_step_needs(self, tmp_path):
        """`score` cannot run without `--log`, so staging must not print a dispatch
        that omits it — that is how the evidence gate gets skipped."""
        design = tmp_path / "d.md"
        design.write_text("d\n", encoding="utf-8")
        result = _run("stage", "--feature", "feat", "--template", str(self._tpl(tmp_path)),
                      "--base", "aaa", "--head", "bbb", "--design", str(design),
                      "--diff-files", "x.py", "--summary", "s",
                      "--prompt", str(tmp_path / "p.txt"))

        assert "--log" in result.stdout
        assert "exec agy" in result.stdout


def test_it_refuses_to_decide_whether_to_run_another_cycle():
    """The one judgement this tool must never make.

    Asserted on the source because it is an absence, and an absence is exactly
    what nobody notices being added later. The seven-cycle run went to seven
    because cycle 3 was clean and cycle 4 then found a Critical vacuous pass; a
    loop-until-clean driver would have stopped at three and shipped it.
    """
    import ast

    # The AST, not the text: both `while`s in this file are prose in the module
    # docstring, and a grep over the source called them loops. Asserting on
    # executable structure is the only version of this that means anything.
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    loops = [n for n in ast.walk(tree) if isinstance(n, (ast.While, ast.For))]
    assert loops == [] or all(
        not isinstance(n, ast.While) for n in loops
    ), "no while-loop: one cycle per invocation, the operator decides on another"


class TestSummaryReachesTheReviewer:
    """#31 — `--summary` took a literal string while `--design` read a file.

    An operator who writes the Phase-5 summary to a file and passes
    `--summary /tmp/summary.md` gets the PATH substituted into the prompt, not
    the 35 lines they wrote. `--design` is `type=Path` and is `read_text()`;
    `--summary` was neither. The staging still reported STAGED, and the two
    architectural review legs ran without the context they were given.

    The tell was byte length: two stagings with DIFFERENT summary files produced
    prompts of identical size, because both substituted a path of equal length.
    """

    def _tpl(self, tmp_path):
        t = tmp_path / "tpl.md"
        t.write_text(
            "feature <INLINE_FEATURE>\nbase <INLINE_BASE_SHA>\nhead <INLINE_HEAD_SHA>\n"
            "files <INLINE_DIFF_FILES>\ndesign <INLINE_AUDITED_DESIGN>\n"
            "summary <INLINE_PHASE_5_SUMMARY>\n", encoding="utf-8")
        return t

    def _stage(self, tmp_path, summary_arg, prompt_name="p.txt"):
        design = tmp_path / "d.md"
        design.write_text("the design\n", encoding="utf-8")
        prompt = tmp_path / prompt_name
        result = _run("stage", "--feature", "feat", "--template", str(self._tpl(tmp_path)),
                      "--base", "aaa1111", "--head", "bbb2222",
                      "--design", str(design), "--diff-files", "a.py",
                      "--summary", summary_arg, "--prompt", str(prompt))
        return result, prompt

    def test_a_summary_file_is_read_not_pasted_as_a_path(self, tmp_path):
        body_text = "Task 7 rewrote the transport guard and re-pinned the anchor.\n"
        summary = tmp_path / "phase5_summary.md"
        summary.write_text(body_text, encoding="utf-8")

        result, prompt = self._stage(tmp_path, str(summary))

        assert result.returncode == 0, result.stdout + result.stderr
        staged = prompt.read_text(encoding="utf-8")
        assert body_text.strip() in staged, (
            "the summary FILE's contents never reached the prompt — the path was "
            "substituted instead, so the reviewer read a filename"
        )
        assert str(summary) not in staged, "the path itself must not be pasted in"

    def test_two_different_summary_files_produce_different_prompts(self, tmp_path):
        """The byte-length tell: equal-length paths made distinct summaries look identical."""
        a = tmp_path / "sum_a.md"
        b = tmp_path / "sum_b.md"
        a.write_text("Alpha finding: the flush fires before the disclosure.\n", encoding="utf-8")
        b.write_text("Beta finding: the guard reads a different field entirely.\n", encoding="utf-8")

        _r1, p1 = self._stage(tmp_path, str(a), "p1.txt")
        _r2, p2 = self._stage(tmp_path, str(b), "p2.txt")

        assert p1.read_text(encoding="utf-8") != p2.read_text(encoding="utf-8")

    def test_an_inline_summary_string_still_works(self, tmp_path):
        """Back-compat: a literal summary that is not a path must still substitute."""
        result, prompt = self._stage(tmp_path, "did things inline")

        assert result.returncode == 0, result.stdout + result.stderr
        assert "did things inline" in prompt.read_text(encoding="utf-8")

    def test_a_missing_summary_file_is_a_staging_failure(self, tmp_path):
        """A path-shaped argument that does not exist must not be pasted as text."""
        result, prompt = self._stage(tmp_path, str(tmp_path / "does_not_exist.md"))

        assert result.returncode != 0, result.stdout + result.stderr
        assert not prompt.exists(), "a failed staging must not leave a prompt behind"

    def test_a_value_whose_slot_is_absent_is_a_staging_failure(self, tmp_path):
        """#31's other half: a required value with no slot reaches nobody.

        The existing guard catches the inverse — a slot left UNSUBSTITUTED. A
        template that simply lacks the slot leaves nothing behind, so it passed.
        """
        t = tmp_path / "no_summary_slot.md"
        t.write_text(
            "feature <INLINE_FEATURE>\nbase <INLINE_BASE_SHA>\nhead <INLINE_HEAD_SHA>\n"
            "files <INLINE_DIFF_FILES>\ndesign <INLINE_AUDITED_DESIGN>\n", encoding="utf-8")
        design = tmp_path / "d.md"
        design.write_text("the design\n", encoding="utf-8")
        prompt = tmp_path / "p.txt"

        result = _run("stage", "--feature", "feat", "--template", str(t),
                      "--base", "aaa1111", "--head", "bbb2222",
                      "--design", str(design), "--diff-files", "a.py",
                      "--summary", "did things", "--prompt", str(prompt))

        assert result.returncode != 0, result.stdout + result.stderr
        assert "INLINE_PHASE_5_SUMMARY" in (result.stdout + result.stderr)


class TestTheVerdictLineIsTheLastThingTheTemplateSays:
    """#153 — three dispatches, three replies with no ASSESSMENT line.

    Then two more after the position was fixed, because the exemplar's FORM was
    not — see tests/test_h_mad_verdict_exemplar.py.

    The template asked for "a final line" and then kept talking for three more
    paragraphs, so the reviewer's own final line was whatever it chose. `stage()`
    writes the template verbatim, so the template's tail IS the prompt's tail: the
    verdict instruction must be the last thing in the file, and the file must say
    "last line of your reply" in words the extractor's regex agrees with.
    """

    TEMPLATE = SCRIPTS.parent / "references" / "agy-architectural-reviewer-prompt.md"

    def test_the_template_ends_with_the_verdict_line(self):
        """2026-09-09: the expected tail changed, and this assertion is why.

        #153 fixed the verdict's POSITION and this assertion then froze its FORM
        as a fenced schema — `<A | B | C>`, in the same angle-bracket grammar the
        template uses for orchestrator-filled slots, wrapped in the very code
        fence the next test requires the prose to forbid. Two further dispatches
        died on it (`ARCHREVIEW: NO_VERDICT`, after reading 11 and 19 files).
        So this pinned the defect; replacing it is the fix, and the replacement
        is stricter. See tests/test_h_mad_verdict_exemplar.py.
        """
        tail = self.TEMPLATE.read_text(encoding="utf-8").rstrip().splitlines()[-3:]
        assert tail == [
            "ASSESSMENT: READY_TO_MERGE",
            "ASSESSMENT: WITH_FIXES",
            "ASSESSMENT: NO",
        ], tail

    def test_the_template_says_last_line_and_nothing_after(self):
        text = self.TEMPLATE.read_text(encoding="utf-8")
        assert "very last line of your reply" in text
        assert "nothing after it" in text
        assert "no code fence around it" in text

    def test_no_instruction_follows_the_report_format_heading_except_the_verdict(self):
        text = self.TEMPLATE.read_text(encoding="utf-8")
        after = text.split("## Report Format", 1)[1]
        assert "## " not in after, "a section after Report Format pushes the verdict off the tail"
        assert "If READY_TO_MERGE" not in after, "verdict meanings belong ABOVE the format section"


class TestTheReportFileChannel:
    """6a-prime was the only `exec agy` path with no report-file channel, so its
    deliverable rode the agent's last message alone — and every observed failure
    was a last-message failure: four dispatches, four `NO_VERDICT`, all four having
    demonstrably read the tree.

    The slot is `<INLINE_REPORT_FILE>` and NOT the `<REPORT_FILE_PATH>` the handover
    brief proposed. `_PLACEHOLDER` matches `<INLINE_[A-Z_0-9]+>` only, so a slot
    named outside that grammar inherits NEITHER existing guard: a template that
    failed to substitute it would ship a live placeholder that reads as real prose
    to the reviewer, which is exactly what `UNSUBSTITUTED` exists to prevent.
    """

    def _tpl(self, tmp_path, with_slot=True, name="tpl.md"):
        t = tmp_path / name
        body = ("feature <INLINE_FEATURE>\nbase <INLINE_BASE_SHA>\nhead <INLINE_HEAD_SHA>\n"
                "files <INLINE_DIFF_FILES>\ndesign <INLINE_AUDITED_DESIGN>\n"
                "summary <INLINE_PHASE_5_SUMMARY>\n")
        if with_slot:
            body += "report <INLINE_REPORT_FILE>\n"
        t.write_text(body, encoding="utf-8")
        return t

    def _stage(self, tmp_path, *, with_slot=True, report_file="/tmp/r.md", prompt_name="p.txt"):
        design = tmp_path / "d.md"
        design.write_text("the design\n", encoding="utf-8")
        prompt = tmp_path / prompt_name
        argv = ["stage", "--feature", "feat",
                "--template", str(self._tpl(tmp_path, with_slot, prompt_name + ".tpl")),
                "--base", "aaa1111", "--head", "bbb2222",
                "--design", str(design), "--diff-files", "a.py",
                "--summary", "did things", "--prompt", str(prompt)]
        if report_file is not None:
            argv += ["--report-file", report_file]
        return _run(*argv), prompt

    # --- stage ---------------------------------------------------------------

    def test_the_report_path_reaches_the_prompt(self, tmp_path):
        result, prompt = self._stage(tmp_path, report_file="/tmp/archreview_feat.report.md")
        assert result.returncode == 0, result.stdout + result.stderr
        assert "/tmp/archreview_feat.report.md" in prompt.read_text(encoding="utf-8")

    def test_a_template_without_the_slot_is_MISSING_SLOTS(self, tmp_path):
        """The value would otherwise reach the reviewer nowhere while staging still
        reported success — the J31 failure, which this slot must not reintroduce."""
        result, _p = self._stage(tmp_path, with_slot=False)
        assert result.returncode == 2, result.stdout
        assert "MISSING_SLOTS" in result.stdout and "<INLINE_REPORT_FILE>" in result.stdout

    def test_the_slot_is_covered_by_the_placeholder_guard(self, tmp_path):
        """EXECUTED, not asserted: the guard's own regex must match this slot name.

        `<REPORT_FILE_PATH>` — the name the brief proposed — does not, and a slot
        outside that grammar ships as live prose if substitution ever misses it.
        """
        import re as _re
        src = (SCRIPTS / "h_mad_archreview_cycle.py").read_text(encoding="utf-8")
        pat = _re.search(r'_PLACEHOLDER = re\.compile\(r"([^"]+)"\)', src).group(1)
        assert _re.fullmatch(pat, "<INLINE_REPORT_FILE>"), pat
        assert not _re.fullmatch(pat, "<REPORT_FILE_PATH>"), (
            "the brief's proposed name would evade the UNSUBSTITUTED guard")

    def test_the_printed_followup_names_the_report_file(self, tmp_path):
        """The operator copies that line. If it omits --report-file the channel is
        built and then not used, which looks identical to not having built it."""
        result, _p = self._stage(tmp_path, report_file="/tmp/rep.md")
        assert "--report-file /tmp/rep.md" in result.stdout, result.stdout

    # --- score ---------------------------------------------------------------

    def test_the_report_file_carries_the_verdict(self, tmp_path):
        state = _state(tmp_path)
        rep = tmp_path / "rep.md"
        rep.write_text("full review\nASSESSMENT: WITH_FIXES\n", encoding="utf-8")
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(_log(tmp_path, 9)),
                      "--review", str(_review(tmp_path, "conversational tail, no verdict\n")),
                      "--report-file", str(rep))
        assert result.returncode == 0, result.stdout + result.stderr
        assert "ARCHREVIEW: WITH_FIXES" in result.stdout
        assert "channel=report-file" in result.stdout, result.stdout

    def test_the_report_file_BEATS_a_conflicting_last_message(self, tmp_path):
        """The whole point: the last message is the unreliable surface. If the two
        disagree the file wins, or the channel has bought nothing."""
        state = _state(tmp_path)
        rep = tmp_path / "rep.md"
        rep.write_text("ASSESSMENT: NO\n", encoding="utf-8")
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(_log(tmp_path, 5)),
                      "--review", str(_review(tmp_path, "ASSESSMENT: READY_TO_MERGE\n")),
                      "--report-file", str(rep))
        assert "ARCHREVIEW: NO" in result.stdout, result.stdout
        assert json.loads(state.read_text())["orchestrator_state"]["feat"]["archreview"] == "NO"

    def test_an_absent_report_file_falls_back_and_SAYS_SO(self, tmp_path):
        """A silent fallback is the defect one level down: the operator would read a
        verdict recorded from the last message as one recorded from the file."""
        state = _state(tmp_path)
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(_log(tmp_path, 7)),
                      "--review", str(_review(tmp_path, "ASSESSMENT: READY_TO_MERGE\n")),
                      "--report-file", str(tmp_path / "never_written.md"))
        assert result.returncode == 0, result.stdout + result.stderr
        assert "ARCHREVIEW: READY_TO_MERGE" in result.stdout
        assert "channel=last-message" in result.stdout, result.stdout

    def test_a_good_report_file_WINS_over_a_review_that_cannot_be_READ(self, tmp_path):
        """The file must win over an ABSENT `--out`, not only over an empty one.

        `score` read `--review` first and `return 2`'d on OSError, so two spellings
        of "the last message carried nothing" took opposite branches: an EMPTY
        `--out` scored the report fine, an ABSENT one refused the whole cycle with
        `UNREADABLE reason=review:FileNotFoundError` while a complete report sat
        unread beside it.

        Not an exotic path. `exec` writes `--out` atomically and the J29 clobber
        guard PRESERVES a stale file rather than removing it, so reaching the absent
        case takes a dispatch killed before `_write_out_atomic` ran — a timeout —
        with the agent's report already on disk. That is exactly the last-message
        failure this channel exists to rescue, refused at the door.
        """
        state = _state(tmp_path)
        rep = tmp_path / "report.md"
        rep.write_text("Full review body.\n\nASSESSMENT: READY_TO_MERGE\n", encoding="utf-8")
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(_log(tmp_path, 5)),
                      "--review", str(tmp_path / "never_written_by_exec.md"),
                      "--report-file", str(rep))
        assert result.returncode == 0, result.stdout + result.stderr
        assert "ARCHREVIEW: READY_TO_MERGE" in result.stdout, result.stdout
        assert "channel=report-file" in result.stdout, result.stdout
        assert json.loads(state.read_text())["orchestrator_state"]["feat"]["archreview"] == "READY_TO_MERGE"

    def test_an_unreadable_review_is_STILL_fatal_when_no_report_file_can_serve(self, tmp_path):
        """The other half, and the reason the fix is an ordering change rather than
        a softened guard: with nothing readable on EITHER channel there is no review
        to judge, and `UNREADABLE` must still refuse. Asserted for both ways a report
        file can fail to serve — never written, and written empty — because a fix
        that merely stopped returning 2 would pass the test above and silently score
        a cycle that read nothing at all."""
        state = _state(tmp_path)
        empty = tmp_path / "empty_report.md"
        empty.write_text("", encoding="utf-8")
        for report_args in ([], ["--report-file", str(empty)],
                            ["--report-file", str(tmp_path / "never.md")]):
            result = _run("score", "--feature", "feat", "--state", str(state),
                          "--log", str(_log(tmp_path, 5)),
                          "--review", str(tmp_path / "absent_review.md"), *report_args)
            assert result.returncode == 2, (report_args, result.stdout)
            assert "UNREADABLE reason=review:" in result.stdout, (report_args, result.stdout)

    def test_score_without_the_flag_is_unchanged(self, tmp_path):
        """Back-compat: every existing caller passes no --report-file."""
        state = _state(tmp_path)
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(_log(tmp_path, 3)),
                      "--review", str(_review(tmp_path, "ASSESSMENT: READY_TO_MERGE\n")))
        assert result.returncode == 0, result.stdout + result.stderr
        assert "channel=last-message" in result.stdout, result.stdout

    def test_an_empty_report_file_falls_back_rather_than_reading_as_no_verdict(self, tmp_path):
        """An agent that created the file and wrote nothing is the commonest partial
        failure. Empty must route to the fallback, not to NO_VERDICT — the file
        existing is not evidence it was written."""
        state = _state(tmp_path)
        rep = tmp_path / "rep.md"
        rep.write_text("   \n", encoding="utf-8")
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(_log(tmp_path, 6)),
                      "--review", str(_review(tmp_path, "ASSESSMENT: WITH_FIXES\n")),
                      "--report-file", str(rep))
        assert result.returncode == 0, result.stdout + result.stderr
        assert "ARCHREVIEW: WITH_FIXES" in result.stdout
        assert "channel=last-message" in result.stdout, result.stdout

    def test_the_SHIPPED_template_carries_the_slot_above_report_format(self, tmp_path):
        """The machinery is worthless if the real template has no slot, and the
        position is a hard constraint, not a preference:
        `test_no_instruction_follows_the_report_format_heading_except_the_verdict`
        forbids any `## ` heading after `## Report Format`, so the section must
        precede it. Both facts are executed against the shipped file."""
        tpl = (SCRIPTS.parent / "references" / "agy-architectural-reviewer-prompt.md"
               ).read_text(encoding="utf-8")
        assert "<INLINE_REPORT_FILE>" in tpl
        assert tpl.index("<INLINE_REPORT_FILE>") < tpl.index("## Report Format"), (
            "the slot must sit ABOVE `## Report Format` or the heading guard refuses it")
        assert "fallback" in tpl.lower(), (
            "the template must say the reply is the fallback, or the agent has no "
            "reason to write both")

    def test_the_template_PERMITS_the_write_it_demands(self, tmp_path):
        """The defect a live dispatch caught, pinned so it cannot return.

        The first build of this channel added "write your report to this file" to a
        template whose tool rules said "Use only `view_file` for code inspection".
        The reviewer obeyed the restriction: 40 `run_command` calls for inspection,
        zero writes, and a fifth consecutive NO_VERDICT. A prompt that forbids the
        action it requires is worse than one that never asked.
        """
        tpl = (SCRIPTS.parent / "references" / "agy-architectural-reviewer-prompt.md"
               ).read_text(encoding="utf-8")
        assert "Use only `view_file`" not in tpl, (
            "the tool restriction still forbids the write this template demands")
        i_rule = tpl.index("`view_file` for code inspection")
        i_slot = tpl.index("<INLINE_REPORT_FILE>")
        assert "run_command" in tpl[i_rule:i_slot], (
            "the write permission must be stated between the tool rule and the slot, "
            "or the reviewer reads the restriction and never reaches the exception")

    def test_the_report_instruction_is_near_the_HEAD_not_only_the_tail(self, tmp_path):
        """The defect the SECOND live dispatch exposed, and the reason the first fix
        was insufficient.

        The template's own text is ~7 KB; the substituted design and file list make
        the prompt ~690 KB. Measured on the real staged prompt, the report-file
        instruction sat at char 686,590 of 689,456 — 99.6% through — and the
        transcript never mentioned the path at all. `prepend_output_contract` in
        `h_mad_assemble_audit.py` already takes `report_file` for exactly this
        reason; this mirrors it instead of inventing a second mechanism.
        """
        design = tmp_path / "d.md"
        design.write_text("PADDING LINE\n" * 20000, encoding="utf-8")   # a realistic bulk
        prompt = tmp_path / "big.txt"
        r = _run("stage", "--feature", "feat",
                 "--template", str(self._tpl(tmp_path, True, "big.tpl")),
                 "--base", "aaa1111", "--head", "bbb2222",
                 "--design", str(design), "--diff-files", "a.py",
                 "--summary", "did things", "--prompt", str(prompt),
                 "--report-file", "/tmp/rep_head.md")
        assert r.returncode == 0, r.stdout + r.stderr
        body = prompt.read_text(encoding="utf-8")
        first = body.index("/tmp/rep_head.md")
        assert first / len(body) < 0.05, (
            f"the report path first appears {100*first/len(body):.1f}% into the prompt; "
            "an instruction behind hundreds of KB of context is not an instruction")
        assert "ASSESSMENT: READY_TO_MERGE" in body[:first + 2000], (
            "the head contract must carry the verdict literals too — the verdict line "
            "has the identical burial problem")

    def test_the_STAGED_token_carries_the_SHAS_not_the_contract_block(self, tmp_path):
        """The BASE/HEAD stamp is one of the two steps this module's own docstring
        says "have no other home and are the two that get skipped" — and until this
        test, nothing asserted the token that carries it. `grep -c 'head=' ` and
        `grep -c 'base=' ` over this file both returned 0 while 216 test lines and a
        67-line mutation spec shipped alongside the report-file channel.

        The defect that gap admitted: the head-contract block was bound to the name
        `head`, shadowing the git HEAD sha parameter, so every `--report-file`
        staging emitted a 16-line blob where the sha goes. The prompt body was
        correct throughout — only the audit trail was destroyed, which is why a
        green suite, the mutation battery and a live dispatch all missed it.

        Asserted for BOTH invocations, because the bug fired only on the
        `--report-file` path and a single-arm test would have passed on the
        control while the shipped path was broken.
        """
        design = tmp_path / "tok_design.md"
        design.write_text("# Design\nbody\n", encoding="utf-8")
        # Each arm gets the template that matches it. A slot-carrying template
        # with no `--report-file` is a DIFFERENT defect (the slot goes
        # unsubstituted and stage halts rc=2), and pairing them wrongly would
        # make this test fail for a reason that has nothing to do with the token.
        for report_file in (None, "/tmp/rep_token.md"):
            slot = report_file is not None
            args = ["stage", "--feature", "feat",
                    "--template", str(self._tpl(tmp_path, slot, f"tok{slot}.tpl")),
                    "--base", "aaa1111", "--head", "bbb2222",
                    "--design", str(design),
                    "--diff-files", "a.py", "--summary", "did things",
                    "--prompt", str(tmp_path / f"tok_{slot}.txt")]
            if report_file is not None:
                args += ["--report-file", report_file]
            r = _run(*args)
            assert r.returncode == 0, r.stdout + r.stderr
            # Anchored on the token PREFIX, not a bare `"STAGED" in l`: stage()
            # also prints a follow-up command block that mentions the word, so a
            # substring filter matches two lines and the count assertion below
            # fails for a reason unrelated to what is being tested.
            staged = [l for l in r.stdout.splitlines()
                      if l.startswith("ARCHREVIEW: STAGED ")]
            assert len(staged) == 1, (report_file, r.stdout)
            line = staged[0]
            # The whole point is that the token is ONE line: a multi-line value
            # would satisfy a naive `in` check while destroying the artifact.
            assert "base=aaa1111 head=bbb2222 " in line, (report_file, line)
            assert "READ THIS BLOCK FIRST" not in line, (
                "the contract block leaked into the STAGED token — `head` is the git "
                f"HEAD sha, not the prompt preamble (report_file={report_file!r})")
