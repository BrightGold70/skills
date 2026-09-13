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
        # TWO tool steps, not one: this test's subject is that undecodable bytes do
        # not abort the scan, and a single call now trips the delivery floor -- which
        # would make it pass or fail for a reason that has nothing to do with UTF-8.
        step = json.dumps({"event": "step_update", "step_update": {
            "step_type": "tool", "state": "DONE"}}).encode()
        log.write_bytes(b"\xff\xfe not utf-8 \n" + json.dumps({"event": "init"}).encode()
                        + b"\n" + step + b"\n" + step + b"\n")
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


def test_the_6a_prime_recovery_step_does_not_prescribe_a_wait_that_cannot_succeed():
    """WSG-3, and the defect is in the DOCS, not in agy.

    `.done` is never written by a 6a-prime `exec agy` dispatch because nothing in
    THIS channel asks for it — `_read_report_channel` records that deliberately, since
    requiring the marker would send every report to the fallback and undo the channel.
    It IS asked for on the audit path, by `audit-prompt.template.md:252` (not, as an
    earlier revision of this said, only by the codex verifier template — those cover
    5d/5e), which is why the recovery row's phase split is a split and not a blanket. So the
    observation "the marker was never written on 5 of 5 cycles" is correct AND
    expected, and the fix is not to make agy write one.

    What IS broken is `failure-recovery.md`'s recovery row, which covers 6a-prime and
    prescribes `report-wait "$RP"`. That poller treats `<path>.done` as the completion
    signal, so it blocks for the full timeout and exits 1 on a complete report.
    Measured: rc=1 after the timeout, rc=0 immediately with `--no-done-marker`.

    Asserted here rather than trusted as prose because a documented rule is not an
    enforced one, and this one is a single clause inside a very long table cell.
    """
    doc = (SCRIPTS.parent / "references" / "failure-recovery.md").read_text(
        encoding="utf-8")
    rows = [ln for ln in doc.splitlines()
            if "6a-prime" in ln and "report-wait" in ln]
    assert rows, "the 6a-prime recovery row no longer mentions report-wait — re-check this"

    # The PRESCRIPTION, not the bare flag token. An earlier version of this test
    # asked only whether `--no-done-marker` appeared somewhere on the same physical
    # line, and it FAILED OPEN: a review added a row naming 6a-prime with a bare
    # `report-wait "$RP"` whose cell mentioned `--no-done-marker` about the *5b* leg,
    # and the test passed. Line-level co-occurrence is not clause attribution, and a
    # very long table cell is exactly where a flag and the prescription it belongs to
    # drift apart while still sharing a line. Requiring the sentence closes that.
    CLAUSE = "For 6a-prime, that wait needs `--no-done-marker`"
    for row in rows:
        assert CLAUSE in row, (
            "a 6a-prime recovery row prescribes `report-wait` without carrying the "
            f"clause {CLAUSE!r} that attaches the flag TO 6a-prime. Mentioning the "
            "flag about another leg in the same cell is not the same prescription, "
            "and an operator following this row waits for a marker this channel "
            "never writes:\n" + row[:300])


def test_the_audit_path_still_ASKS_for_the_done_marker():
    """The load-bearing sentence behind `failure-recovery.md`'s "must NOT have it" half.

    `report-wait` is correct WITHOUT `--no-done-marker` for phases 3/4/5b only because
    `audit-prompt.template.md` instructs the agy audit leg to create the marker. That
    sentence was identified as load-bearing and left unpinned; if it is ever edited
    out, those phases' bare `report-wait` hangs exactly as 6a-prime's did, and nothing
    would have said so.

    Pinned on the PRODUCER here. `h_mad_audit_cycle._has_complete_report` is the
    consumer and is pinned by its own tests; a contract needs both ends.
    """
    tpl = (SCRIPTS.parent / "audit-prompt.template.md").read_text(encoding="utf-8")
    assert "create the marker" in tpl and ".done" in tpl, (
        "audit-prompt.template.md no longer asks the audit leg to create its `.done` "
        "marker. Phases 3/4/5b now need `--no-done-marker` too, and "
        "`references/failure-recovery.md`'s phase split must change with it.")


class TestACleanVerdictMustRestOnMoreThanTheDeliveryContract:
    """J49 in the 6a-prime channel: the gate was `tools == 0`, a floor of ZERO.

    This channel's own contract says "you must also WRITE your report file with
    `run_command`. That is the only write you may make", and asks for no `.done`
    marker -- so a reviewer that read nothing and merely obeyed the delivery
    instruction scores exactly `tools=1` and passed. `h_mad_audit_cycle` has carried
    `DELIVERY_FLOOR = 2` against the same failure (cycle 24 double-cleaned on
    delivery calls alone); one channel was guarded and the other was not.

    The asymmetry is the point and it is deliberate: findings are evidence of
    reading, a clean is not. Only READY_TO_MERGE is held to the floor.
    """

    def _stored(self, state):
        return json.loads(state.read_text(encoding="utf-8"))[
            "orchestrator_state"]["feat"].get("archreview")

    def test_a_clean_on_the_delivery_contract_alone_is_refused(self, tmp_path):
        state = _state(tmp_path)
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(_log(tmp_path, 1)),
                      "--review", str(_review(tmp_path, "ASSESSMENT: READY_TO_MERGE\n")))

        assert result.returncode == 2, result.stdout
        assert "ARCHREVIEW: LOW_EVIDENCE_CLEAN tools=1 floor=1" in result.stdout
        assert "step6a-prime:review_read_nothing" in result.stdout
        assert self._stored(state) is None, (
            "a refused verdict must not be recorded — a recorded READY_TO_MERGE is "
            "what the Phase-7 gate reads")

    def test_one_call_above_the_floor_is_recorded(self, tmp_path):
        """The floor must not be an off-by-one that refuses every real review."""
        state = _state(tmp_path)
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(_log(tmp_path, 2)),
                      "--review", str(_review(tmp_path, "ASSESSMENT: READY_TO_MERGE\n")))

        assert result.returncode == 0, result.stdout
        assert "ARCHREVIEW: READY_TO_MERGE tools=2" in result.stdout
        assert self._stored(state) == "READY_TO_MERGE"

    def test_findings_at_the_same_count_are_still_recorded(self, tmp_path):
        """The asymmetry. A pass in this repo with 2 tool calls returned a REAL
        finding, so a low-evidence pass that found something is scored on what it
        found. Refusing these too would discard review work that was actually done --
        the failure the report-file channel exists to prevent."""
        for verdict in ("WITH_FIXES", "NO"):
            state = _state(tmp_path)   # re-created per verdict: `--set` is a write
            result = _run("score", "--feature", "feat", "--state", str(state),
                          "--log", str(_log(tmp_path, 1)),
                          "--review", str(_review(tmp_path, f"ASSESSMENT: {verdict}\n")))

            assert result.returncode == 0, (verdict, result.stdout)
            assert f"ARCHREVIEW: {verdict} tools=1" in result.stdout, verdict
            assert "LOW_EVIDENCE_CLEAN" not in result.stdout, verdict
            assert self._stored(state) == verdict, verdict

    def test_zero_calls_is_still_the_older_and_stronger_token(self, tmp_path):
        """`NO_EVIDENCE` must keep firing at zero rather than being absorbed into the
        new token: it is the stronger claim (nothing ran at all, for ANY verdict),
        and its halt is what SKILL.md and the existing spec assert on."""
        state = _state(tmp_path)
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(_log(tmp_path, 0)),
                      "--review", str(_review(tmp_path, "ASSESSMENT: WITH_FIXES\n")))

        assert result.returncode == 2, result.stdout
        assert "ARCHREVIEW: NO_EVIDENCE tools=0" in result.stdout
        assert "LOW_EVIDENCE_CLEAN" not in result.stdout

    def test_the_floor_is_derived_from_the_shipped_template_not_guessed(self, tmp_path):
        """The number has one source: the contract. If the template ever asks for a
        second write (a `.done` marker, as the audit path's does), the floor moves and
        this assertion is what says so out loud instead of the gate silently going
        one call too permissive."""
        tpl = (SCRIPTS.parent / "references" / "agy-architectural-reviewer-prompt.md"
               ).read_text(encoding="utf-8")
        assert "That is the only write you may make" in tpl, (
            "the floor of 1 rests on this sentence; if the contract now asks for more "
            "than one write, raise DELIVERY_FLOOR to match it")

        sys.path.insert(0, str(SCRIPTS))
        import h_mad_archreview_cycle as arc
        assert arc.DELIVERY_FLOOR == 1, arc.DELIVERY_FLOOR


class TestTheStagedPromptMustBeDeliverable:
    """This channel had ZERO size guards while the audit path had several.

    A ~690 KB 6a-prime prompt was written, said STAGED, and was then refused by the
    surface -- which reads as "6a-prime failed" rather than "the prompt was never
    delivered".

    The FIRST version of this gate was wrong in the permissive direction and these
    tests defended the wrong boundary. It reused `h_mad_assemble_audit.prompt_oversize`,
    which counts CHARACTERS against codex's stdin limit. But `exec agy` passes the
    prompt as one argv element (`hmad-dispatch.sh:2944`), so the real ceiling is
    ARG_MAX: a BYTE budget the kernel shares with the environment. Measured: an argv
    payload at the old character limit fails `Argument list too long`. Reuse of a
    measured constant is not automatically right -- it imported the other surface's
    UNITS along with its number.

    So the boundary test below does not restate a constant. It EXECUTES: it asks the
    gate what it blesses and then proves that payload actually survives as argv.
    """

    def _budget(self, tmp_path):
        """The budget as the STAGING PROCESS computes it, read off its own token.

        Not recomputed in this process, and that is not fastidiousness: the budget
        is a function of `os.environ`, and the test process's environment is not
        byte-identical to the child's (measured: a 25-byte disagreement, enough to
        put a boundary payload on the wrong side of the line). Asking the child what
        it blessed is the only figure that means anything about the child.
        """
        probe, _ = self._stage(tmp_path, "x" * 2_000_000, prompt_name="budget.txt")
        assert probe.returncode == 2, probe.stdout[:200]
        token = [ln for ln in probe.stdout.splitlines()
                 if ln.startswith("ARCHREVIEW: OVERSIZE")]
        assert token, probe.stdout[:300]
        fields = dict(f.split("=", 1) for f in token[0].split() if "=" in f)
        return int(fields["budget"]), int(fields["reserve"])

    def _tpl(self, tmp_path, *, with_report_slot: bool):
        t = tmp_path / ("tpl_r.md" if with_report_slot else "tpl.md")
        body = ("feature <INLINE_FEATURE>\nbase <INLINE_BASE_SHA>\n"
                "head <INLINE_HEAD_SHA>\nfiles <INLINE_DIFF_FILES>\n"
                "design <INLINE_AUDITED_DESIGN>\nsummary <INLINE_PHASE_5_SUMMARY>\n")
        if with_report_slot:
            body += "report <INLINE_REPORT_FILE>\n"
        t.write_text(body, encoding="utf-8")
        return t

    def _stage(self, tmp_path, design_text, *, report_file=None, vh_tail=None,
               slot=None, prompt_name="p.txt"):
        design = tmp_path / "d.md"
        design.write_text(design_text, encoding="utf-8")
        prompt = tmp_path / prompt_name
        tpl = self._tpl(tmp_path, with_report_slot=(report_file is not None
                                                   if slot is None else slot))
        argv = ["stage", "--feature", "feat", "--template", str(tpl),
                "--base", "aaa1111", "--head", "bbb2222", "--design", str(design),
                "--diff-files", "a.py", "--summary", "did things",
                "--prompt", str(prompt)]
        if report_file is not None:
            argv += ["--report-file", report_file]
        if vh_tail is not None:
            argv += ["--vh-tail", str(vh_tail)]
        return _run(*argv), prompt

    def _pad_to_bytes(self, tmp_path, target_bytes, *, report_file=None, slot=None):
        """A design whose staged prompt is exactly `target_bytes` long.

        Measured by staging once, not computed from the template: the substitution
        and the contract both change the length, and a guessed figure would test the
        guess rather than the gate.
        """
        probe, prompt = self._stage(tmp_path, "x", report_file=report_file, slot=slot,
                                    prompt_name="probe.txt")
        assert probe.returncode == 0, probe.stdout + probe.stderr
        base = len(prompt.read_bytes())
        return "x" * (1 + target_bytes - base)

    def test_a_prompt_no_surface_accepts_is_refused_and_not_written(self, tmp_path):
        """Both halves matter. The refusal is the point; the ABSENT file is what makes
        it safe -- an oversize prompt left on disk is one that gets dispatched anyway
        by the next copy-pasted command line."""
        budget, reserve = self._budget(tmp_path)
        design = self._pad_to_bytes(tmp_path, budget + 1)
        result, prompt = self._stage(tmp_path, design, prompt_name="over.txt")

        assert result.returncode == 2, result.stdout[:400]
        assert "ARCHREVIEW: OVERSIZE" in result.stdout
        assert f"budget={budget}" in result.stdout
        assert f"reserve={reserve}" in result.stdout
        assert not prompt.exists(), "an oversize prompt must not be left on disk"
        assert "--vh-tail" in result.stdout, "a halt must name its escape hatch"

    def test_the_largest_blessed_prompt_IS_ACTUALLY_DELIVERABLE(self, tmp_path):
        """The boundary, proven by execution rather than asserted against a constant.

        This is the test that was wrong before: it asserted STAGED at the old
        character limit, and an argv payload of exactly that size fails with
        `Argument list too long`. A test that restates the gate's own arithmetic
        cannot catch a gate whose arithmetic is in the wrong unit -- so this one
        takes what the gate blesses and hands it to the kernel.
        """
        budget, _ = self._budget(tmp_path)
        design = self._pad_to_bytes(tmp_path, budget)
        result, prompt = self._stage(tmp_path, design, prompt_name="edge.txt")

        assert result.returncode == 0, result.stdout[:400]
        assert "ARCHREVIEW: STAGED" in result.stdout
        body = prompt.read_bytes()
        assert len(body) == budget

        # The claim under test: this payload is deliverable as ONE argv element,
        # which is how `exec agy` passes it. `/usr/bin/true` ignores the argument;
        # only the kernel's argv+envp accounting is being measured.
        try:
            subprocess.run(["/usr/bin/true", body.decode("utf-8")],
                           capture_output=True)
        except OSError as exc:
            raise AssertionError(
                f"the gate blessed {len(body)} bytes and the kernel refused it as "
                f"argv: {exc}. The budget is too permissive — this is the defect "
                f"the char-count version of this gate had."
            ) from exc

    def test_OVERSIZE_removes_a_STALE_prompt_at_the_same_path(self, tmp_path):
        """Writing no file is not the same as leaving no file.

        6a-prime iterates against ONE `--prompt` path, and cycle N's
        `hmad-dispatch exec agy <prompt>` line stays in the operator's scrollback. A
        halt that merely declines to write leaves the previous cycle's prompt there,
        dispatchable — so re-running that line reviews the superseded prompt and comes
        back clean. The first version of this gate had exactly that hole: its comment
        claimed "an unwritten prompt cannot be dispatched by mistake" while a stale one
        survived untouched.
        """
        budget, _ = self._budget(tmp_path)
        prompt = tmp_path / "iter.txt"

        first, _ = self._stage(tmp_path, "the first cycle", prompt_name="iter.txt")
        assert first.returncode == 0, first.stdout
        assert prompt.exists()
        stale = prompt.read_bytes()
        assert b"the first cycle" in stale

        design = self._pad_to_bytes(tmp_path, budget + 1)
        second, _ = self._stage(tmp_path, design, prompt_name="iter.txt")

        assert second.returncode == 2, second.stdout[:300]
        assert "ARCHREVIEW: OVERSIZE" in second.stdout
        assert "stale_removed=1" in second.stdout, (
            "the halt must SAY it removed the superseded prompt; a file vanishing "
            "without a word is worse than one that stays\n" + second.stdout[:300])
        assert not prompt.exists(), (
            "the previous cycle's prompt is still on disk and still dispatchable — "
            "the halt's stated safety property does not hold on a re-stage")

    def test_OVERSIZE_on_a_clear_path_reports_that_it_removed_nothing(self, tmp_path):
        """The other direction, so `stale_removed` is a measurement and not a constant."""
        budget, _ = self._budget(tmp_path)
        design = self._pad_to_bytes(tmp_path, budget + 1)
        result, prompt = self._stage(tmp_path, design, prompt_name="fresh.txt")

        assert result.returncode == 2, result.stdout[:300]
        assert "stale_removed=0" in result.stdout, result.stdout[:300]
        assert not prompt.exists()

    def test_the_gate_measures_the_body_the_contract_prepend_produced(self, tmp_path):
        """The discriminating case, and the reason the gate sits after the prepend.

        A body exactly deliverable BEFORE the output contract is prepended is NOT
        deliverable after it. A gate placed before the prepend passes this prompt and
        the surface then refuses it -- the original defect with a size check bolted on
        that cannot see the last thing written.

        The sizing has to isolate the CONTRACT and nothing else. A first version sized
        against a slot-less template and staged against a slot-carrying one, and the
        extra `report <INLINE_REPORT_FILE>` line was itself enough to trip the gate --
        so the test passed with the contract discounted, and the mutation that
        discounts it SURVIVED. Same template, same flags, both times; only the design
        length moves.
        """
        budget, _ = self._budget(tmp_path)
        report = "/tmp/r.md"

        # Measure this exact staging's contract length rather than restating it: the
        # substituted template begins at the template's own first line, so everything
        # before that is the prepend.
        probe, probe_prompt = self._stage(tmp_path, "x", report_file=report,
                                          prompt_name="probe_c.txt")
        assert probe.returncode == 0, probe.stdout + probe.stderr
        text = probe_prompt.read_text(encoding="utf-8")
        contract_len = len(text[:text.index("feature feat\n")].encode("utf-8"))
        assert contract_len > 0, "no contract was prepended; this test would be vacuous"
        pre_contract = len(probe_prompt.read_bytes()) - contract_len

        # A design that makes the PRE-contract body exactly the largest deliverable
        # size. With the contract it is over; without it, it is not.
        design = "x" * (budget - pre_contract + 1)
        result, prompt = self._stage(tmp_path, design, report_file=report,
                                     prompt_name="contract.txt")

        assert result.returncode == 2, (
            "the gate passed a body that is only deliverable without its own contract; "
            f"contract={contract_len} bytes\n" + result.stdout[:400])
        assert "ARCHREVIEW: OVERSIZE" in result.stdout
        assert not prompt.exists()

    def test_a_multibyte_design_is_measured_in_BYTES_not_characters(self, tmp_path):
        """The unit, isolated. Every other fixture here is ASCII, where chars == bytes
        and a character-counting gate looks identical to a byte-counting one.

        The design documents this channel actually inlines are not ASCII — the ones in
        this repo measure 1.004-1.010 bytes/char — so the window a char gate opens is
        only reachable with multi-byte content. A tidy ASCII suite cannot see it, which
        is why the first version shipped.
        """
        budget, _ = self._budget(tmp_path)

        # Three bytes per character, so a body that is comfortably under `budget`
        # CHARACTERS is far over it in bytes.
        probe, probe_prompt = self._stage(tmp_path, "\u4e00", prompt_name="mb_probe.txt")
        assert probe.returncode == 0, probe.stdout + probe.stderr
        # Everything the staged prompt holds EXCEPT the design. The probe's own
        # one-character design is 3 bytes and must come back off — leaving it in put
        # the first version of this fixture 3 bytes under the line, and it staged.
        prefix = len(probe_prompt.read_bytes()) - len("\u4e00".encode("utf-8"))

        chars = -(-(budget + 3 - prefix) // 3)    # ceil: land just OVER in bytes
        design = "\u4e00" * chars
        predicted = prefix + 3 * chars
        assert len(design) < budget, "the fixture must be UNDER budget in characters"
        assert predicted > budget, (
            f"the fixture must be OVER budget in bytes ({predicted} vs {budget}), "
            "or it discriminates nothing")

        result, prompt = self._stage(tmp_path, design, prompt_name="mb.txt")

        assert result.returncode == 2, (
            "a design under the budget in characters but over it in bytes was staged; "
            "the gate is counting the wrong unit\n" + result.stdout[:300])
        assert "ARCHREVIEW: OVERSIZE" in result.stdout
        assert not prompt.exists()

    def test_the_budget_is_derived_at_runtime_and_leaves_room_for_the_environment(self):
        """A second hardcoded constant would drift exactly as the first one did.

        The budget must fall below ARG_MAX by at least the size of the current
        environment, because the kernel charges argv and envp against one budget.
        """
        import os
        sys.path.insert(0, str(SCRIPTS))
        import h_mad_archreview_cycle as arc
        budget, reserve = arc._argv_budget()
        arg_max = os.sysconf("SC_ARG_MAX")
        env_bytes = sum(len(k) + len(v) + 2 for k, v in os.environ.items())

        assert budget + reserve == arg_max, (budget, reserve, arg_max)
        assert reserve > env_bytes, (
            f"reserve {reserve} does not even cover this environment's {env_bytes} "
            "bytes, so the budget is not an argv budget")
        assert budget < arg_max - env_bytes

    def test_vh_tail_trims_the_inlined_design(self, tmp_path):
        """The remedy OVERSIZE prescribes has to exist in the channel that halts.
        A halt whose escape hatch is unimplemented here is a wall."""
        design = ("the design body\n"
                  "\n## Version History\n"
                  "- v1 first\n- v2 second\n- v3 third\n- v4 fourth\n")
        result, prompt = self._stage(tmp_path, design, vh_tail=1)

        assert result.returncode == 0, result.stdout + result.stderr
        body = prompt.read_text(encoding="utf-8")
        assert "the design body" in body, "the body is never the trim's subject"
        assert "- v4 fourth" in body, "the LAST entry is the one kept"
        assert "- v1 first" not in body
        assert "3 of 4 Version History entries omitted" in body
        assert "git show" in body, "the omitted entries must stay reachable"

    def test_the_omission_note_names_the_path_THE_REPO_knows(self, tmp_path):
        """`git show <sha>:<ref>` resolves from the repo root, so the ref must too.

        This value was arbitrarily wrong with the whole suite green: a review replaced
        it with a literal "COMPLETELY/WRONG/PATH.md" and 3202 tests still passed. It
        was computed against `Path.cwd()` while its own comment claimed the repo root
        — and those coincide only when the process starts at the root, which `…/h-mad`
        (where this suite actually runs) is not.

        Hermetic: a throwaway git repo in tmp_path, so the assertion is about the
        REPO root and not about wherever pytest happened to be invoked. Under the
        cwd-based version the design is not below cwd at all, `relative_to` raises,
        and the ref collapses to a bare basename — which is the failure.
        """
        subprocess.run(["git", "init", "-q", str(tmp_path)], check=True,
                       capture_output=True)
        nested = tmp_path / "docs" / "02-design" / "features"
        nested.mkdir(parents=True)
        design = nested / "thing.design.md"
        design.write_text(
            "body\n\n## Version History\n- v1 a\n- v2 b\n- v3 c\n", encoding="utf-8")

        prompt = tmp_path / "p.txt"
        result = _run("stage", "--feature", "feat",
                      "--template", str(self._tpl(tmp_path, with_report_slot=False)),
                      "--base", "aaa1111", "--head", "bbb2222", "--design", str(design),
                      "--diff-files", "a.py", "--summary", "s",
                      "--prompt", str(prompt), "--vh-tail", "1")

        assert result.returncode == 0, result.stdout + result.stderr
        body = prompt.read_text(encoding="utf-8")
        assert "git show <sha>:docs/02-design/features/thing.design.md" in body, (
            "the omission note must name the path the repo knows, or the reviewer has "
            "no way back to the omitted entries. Got:\n"
            + "\n".join(ln for ln in body.splitlines() if "git show" in ln))
        assert "git show <sha>:thing.design.md" not in body, (
            "the ref collapsed to a bare basename — it is being resolved against the "
            "process's cwd rather than the repository root")

    def test_vh_tail_omitted_is_a_strict_no_op(self, tmp_path):
        """Existing callers and their prompt hashes must be unaffected: the default
        has to be byte-identical to the code before the flag existed."""
        design = ("body\n\n## Version History\n- v1 a\n- v2 b\n- v3 c\n")
        with_flag, p1 = self._stage(tmp_path, design, prompt_name="a.txt")
        assert with_flag.returncode == 0, with_flag.stdout

        assert "- v1 a" in p1.read_text(encoding="utf-8")
        assert "omitted" not in p1.read_text(encoding="utf-8")


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

    def test_a_report_file_with_NO_VERDICT_loses_to_a_last_message_that_has_one(self, tmp_path):
        """Non-empty is not complete. A write killed part-way leaves real prose and
        no verdict line, and once the file started winning over the last message,
        preferring it DISCARDED a verdict that had survived.

        The audit path's own completeness gate is three-part
        (`h_mad_audit_cycle._has_complete_report`: exists, non-empty, `.done`
        marker). That third part is NOT copied here and must not be: neither the
        agy template nor the head contract `stage()` injects asks the reviewer to
        create a `.done` marker — only the codex VERIFIER template does — so
        requiring one would send every report to the fallback and undo the channel.
        The usable gate on this surface is whether the file carries a verdict.
        """
        state = _state(tmp_path)
        rep = tmp_path / "truncated.md"
        rep.write_text("## Findings\n\nThe module is sound, and the wiring is\n",
                       encoding="utf-8")   # cut mid-sentence, no ASSESSMENT
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(_log(tmp_path, 6)),
                      "--review", str(_review(tmp_path, "ASSESSMENT: WITH_FIXES\n")),
                      "--report-file", str(rep))
        assert result.returncode == 0, result.stdout + result.stderr
        assert "ARCHREVIEW: WITH_FIXES" in result.stdout, result.stdout
        assert "channel=last-message" in result.stdout, (
            "a verdictless file must not win — the last message is what this "
            "channel exists to rescue", result.stdout)
        assert json.loads(state.read_text())["orchestrator_state"]["feat"]["archreview"] == "WITH_FIXES"

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
