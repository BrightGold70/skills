# Handoff — audit-cycle-verb: Phase-4 RE-AUDIT gated clean, Tasks 1–4 shipped (helper complete), Tasks 5–9 not started

**Date:** 2026-08-20 (extended 2026-08-21)
**Branch:** feature/audit-cycle-verb
**Project:** skills (`/Users/kimhawk/orca/skills`)

## Session Summary

Resumed `audit-cycle-verb` at `enter_autonomous` (Phase 5) and took it through 5a, 5b, 5c and
Tasks 1–4 of 5d/5e — **the Python helper `h_mad_audit_cycle.py` is now complete and its central
claim is demonstrated live**: a prose-only finding plus a bulleted finding gate per-pass to
`must=2`, while the same two reports concatenated gate to `must=1`. The impl-plan was authored,
audited over **nine two-pass cycles (55 findings, zero deferrals)** and gated clean on both passes,
and the wire-pin gate registered all six wires. Each of Tasks 1–4 shipped RED→GREEN with a revert
test, a wire-scoped revert plus force mutation where it is a `wiring` task, and an independent agy
spec review. Suite: 49 tests. **Tasks 5–9 have not started; no shell verb, no mutation specs, no SKILL.md changes exist
yet.** The feature is claimed by this session's id — release or take it over on resume.

**2026-08-21: the operator ruled the v1.15 design errata must be RE-GATED, not accepted.**
Phase-4 re-audit ran cycles 17–23 (two independent agy passes each): **7 must-fix, 2 should-fix,
5 nits, 0 deferrals**, design v1.15 → **v1.21**, and cycle 23 gates `PASS must=0 should=0` on BOTH
passes with zero nits — covering the edit that closed cycle 22, so nothing in this design stands on
an unaudited change. Both code obligations it raised are closed (`d7c775c`), suite **59/59**.

Ten commits on the branch; the first eight are pushed, `d7c775c` and `3cd5c84` are not.

**Nine defects were caught across Tasks 1–4, every one of them under a green suite.** Four of
the five in Task 4 were found by running the binary end-to-end against the design's documented
shapes — not by the 49-test suite and not by a reviewer.

## Key Learnings

- **`gpt-5.6-luna` — the `~/.codex/config.toml` default — cannot execute ANY tool.** Every shell
  and patch call dies on `codex_core::tools::router: timed out negotiating with the code-mode
  host`, including `true`. It still writes fluent prose, so it returns a well-formed
  `STATUS: BLOCKED` with an empty tree delta — indistinguishable from a genuine task blocker, and
  the same shape a prompt echo produces (the implementer prompt contains the literal
  `STATUS: BLOCKED` in its own contract block). `gpt-5.4` and `gpt-5.5` both work. **Pass
  `--model gpt-5.5` on every `exec codex`.** Saved as `feedback_codex_luna_code_mode_broken.md`.
- **The documented revert sequence silently did nothing here.** `git add -N -- <path>` followed by
  `git stash push -- <path>` left the untracked production file **in place**, exit 0, stash list
  empty — and the suite stayed green, which would have read as a *passing* revert test over
  un-reverted code. Only the "did the revert land" assertion caught it. Use a physical `mv` aside
  and assert absence.
- **A green suite, `STATUS: DONE`, and a passing revert test all sailed over a fabricated
  verdict.** Task 1's `main()` declared `--pass`, never read it, and fell through to
  `combine([])`: two nonexistent report paths, one carrying `rc=1`, produced
  `AUDITCYCLE: PASS must=0 should=0` at exit 0. 19/19 tests were green because none drove `main()`
  with `--pass`, so the hardcoded `[]` was unreachable by every test. **Only the independent agy
  spec review caught it** — reading against the ACs rather than executing. The second lane is not
  ceremony.
- **Five more defects in Task 4 alone, all under a green 43–49 test suite.** (a) `main()`
  hardcoded `cycle=1` and never declared `--cycle`, so every cycle's reports would land at
  `…audit.v1.p<i>.md` and the Task 7 verb — which passes `--cycle N` — could never have run;
  (b) `--grace` was `type=float` while `h_mad_report_wait.py --timeout` is `type=int`, so EVERY
  real fall-through-to-wait crashed, including on the default — invisible because ten tests stub
  that binary and the stub accepts what it rejects; (c) the premise checklist printed on
  `UNVERIFIED`; (d) the verdict line injected `reason=` into FAIL, breaking AC-8.1's shape;
  (e) `render()` gated `delivered=` on "did any pass deliver?" instead of "was anything
  dispatched?", so an all-`none` post-dispatch cycle printed byte-identically to the no-pass form.
- **The recurring root cause is a constant standing in for a real input, with no test supplying
  that input.** `combine([])` in Task 1, `cycle=1` in Task 4. A green suite cannot see an input it
  never provides. Ask a reviewer to hunt that *class* by name — it found none remaining.
- **Tests written after an implementation inherit its assumptions.** Several Task 4 tests DID
  assert the verdict line — they asserted what the code emitted, not what the design specifies.
  Assert against the design's documented shapes.
- **Run the binary end-to-end against the design's shapes.** Four of Task 4's five defects came
  from a probe written to *demonstrate* the feature, not from the suite and not from a reviewer.
- **`grep -c` exits 1 on zero matches**, so a guard whose success is "no matches" reports the whole
  command as failed. And `grep -qx '.*<testname>'` can never match a pytest `FAILED` line, because
  pytest appends ` - AssertionError…`; that produced a **false "wire NOT enforced"** on a wire that
  was enforced. Print the exact failing-test list beside any such check.
- **An unlanded mutation plus a green suite reads as "connection enforced".** One wire-scoped
  regex failed to match and the run then printed an empty failing set. Every mutation this session
  asserts its anchor matches **exactly once** before applying, and refuses otherwise.
- **Ask reviewers for the verdict token unbolded on its own line.** One returned
  `**VERDICT: COMPLIANT**`; `h_mad_extract_verdict.py` correctly rejected it, which turns the
  extractor from authoritative into something a human overrides by eye.
- **Bare `python3` on this box is 3.14 with no pytest.** Use `/opt/anaconda3/bin/python3.11`. A
  plain `python3 -m pytest` returns `No module named pytest`, which reads like a broken test run.
- **`--log` appends across runs, so a raw error count is not a per-run measurement.** A re-dispatch
  showed "8 negotiation errors" on a healthy run; timestamps proved all six unique ones belonged to
  the earlier failed run. Splitting runs by grepping the dispatch boundary *also* failed — it
  matched `DISPATCH_BOUNDARY = "===HMAD-DISPATCH-BOUNDARY==="`, a string literal inside logged file
  content. Timestamps were the only reliable discriminator.
- **A probe's success string in the log may be the echoed prompt.** Grepping the codex log for
  `CODEX_HOST_OK` hit line 13 — the prompt — not output. Exclude the prompt's line before
  concluding anything ran.
- **`timeout` does not exist on this machine.** Wrapping a probe in it yields `rc=127` which reads
  as "the probe failed" when the probe never ran.
- **The 9-cycle audit reproduced the alternating pattern exactly.** Passes agreed on a minority of
  findings; from cycle 6 the clean pass **alternated sides** (cycle 6: p1 clean, p2 found 3; cycle
  8: p2 clean, p1 found 3). A single-pass gate would have shipped twice. **Nine prescriptions were
  wrong while their facts were right** — `exec agy` where the in-process entry is `_cmd_exec`;
  `dirname "$0"` where the `bin/` shim makes `BASH_SOURCE` necessary; `*UNVERIFIED*` where the
  measured value is lowercase so the "fix" matches nothing.
- **The re-audit justified itself: FOUR of its nine findings were introduced by the edits meant to
  fix the previous cycle**, and one was a live defect in already-committed code. v1.15 left
  "connection mutation 2/10" dangling and left "three rows marked *anchors*" after adding two more;
  v1.17 specified a write-failure fixture using a read-only dir (the guard sits AFTER the write, so
  `PermissionError` raises first, the guard is never reached, and deleting it would still crash —
  the mutation SURVIVES while looking caught); v1.20 updated a scenario column to "all three" and
  left its verification column saying "both removed". Each edit was correct in what it *changed*
  and wrong in what it *left inconsistent* — which re-reading your own edit does not catch.
- **A live defect in shipped code, proven before fixing:** `collected_path` was not covered by the
  pre-dispatch clearing, so on a re-run the previous run's report sat at that exact path and a
  silently-failed write left `exists()`/`st_size > 0` True on the OLD file — a stale report scored
  as a fresh measurement. Fixed with `unlink(missing_ok=True)` in both writers.
- **Two guards had NO discrimination coverage** (`len(findings) == must`, and the collected-write
  re-read). Both now have negative tests, each mutation-verified to fail **exactly one** test.
- **An empty failing set is a non-result, not a clean guard.** One mutation anchor matched two
  lines and the harness refused; the run then printed an empty failing set, which reads as "the
  guard does not bite". Assert the anchor matches exactly once and treat a refusal as no data.
- **A filename appearing in a log is not evidence anything touched it.** I mis-diagnosed the
  missing cycle-23 reports from log hits that were pytest PARAMETRIZATION IDs, and from a
  `grep -c` that counted my own prompt text. Both hypotheses (destructive suite; `git clean`) were
  refuted empirically before acting.
- **Do not run a workspace-write codex dispatch concurrently with a job writing untracked
  artifacts into the same tree.** Cycle 23's collected reports vanished between gate time and
  commit; cause unproven, but the two dispatches overlapped. **Verify gating evidence is ON DISK
  before committing** — a clean `git status` plus absent artifacts looks exactly like
  nothing-to-commit.
- **Two fixes composed into new defects**, each caught only by the next cycle: v1.3's mutation-anchor
  correction produced v1.5's unit-vs-`main()` defect, and v1.7's prompt-exists guard broke the HALT
  path (a halt deliberately writes no prompt). Reconcile a cycle's findings against each other
  before applying any.

## Next Steps

1. **Re-claim the feature** — `python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature audit-cycle-verb --session-id "<sid>"` then `--claim "<sid>"`. It is currently owned by session `eea70bac`, which has stopped.
2. **Task 5 RED** — the `audit-cycle` verb's arg validation, path templating, clearing + `[ ! -e ]` assertions, per-pass assembly, token combine and identity assertion. WIRE-PIN `test_verb_assemble_halt_no_dispatch`. Task text: `docs/01-plan/features/audit-cycle-verb.impl-plan.md`.
3. **Reuse the dispatch recipe verbatim** — assemble prompt from the impl-plan task + `~/.claude/skills/h-mad/references/codex-implementer-prompt.md`, then `hmad-dispatch exec codex <prompt> --cd /Users/kimhawk/orca/skills --model gpt-5.5 --out <o> --log <l> --timeout 900`, backgrounded.
4. **Then Tasks 6→9 in order**: 6 verb → `_cmd_exec agy` · 7 verb → helper · 8 both mutation specs · 9 SKILL.md + docs token test.
5. **Tasks 5–7 are where Task 4's fixes get exercised for real** — the verb passes `--cycle N` (which `main()` did not accept until this session) and consumes the `delivered=` shape. Run the verb end-to-end before believing its tests.
6. **5f** — `h_mad_wire_registry.py verify --base 41efe98 --rootdir /Users/kimhawk/orca/skills --testpath h-mad/tests`, then `challenge --base 41efe98` (warning-only), then the full suite.
7. ~~Push~~ — **DONE.** Branch is fully pushed; `origin/feature/audit-cycle-verb` is level with HEAD (`a8907e8`).

## Open / Blocked Items

- **Tasks 5–9 of audit-cycle-verb** — status: not started, unblocked. `repo: /Users/kimhawk/orca/skills · branch: feature/audit-cycle-verb · worktree: none (main worktree)`. Artifacts: `docs/01-plan/features/audit-cycle-verb.{spec,plan,impl-plan}.md`, `docs/02-design/features/audit-cycle-verb.design.md`, 18 impl-plan audit reports `…impl-plan.audit.v{1..9}.p{1,2}.md`, registry `.h-mad/wires.jsonl` (6 rows).
- **h-mad claim** — status: **held by session `eea70bac`** (this one). Not released, because the work is mid-Phase-5 and the next session should take it deliberately rather than inherit an unowned feature. Plain `--claim` will take it once stale.
- **`phase = "step5"` is still armed** — deliberate. It keeps the TDD gate blocking Claude-authored production `.py`. Do NOT write `phase = null` before 5g completes.
- **Anti-gaming verify pass not run for ANY of Tasks 1–4** — status: owed. `references/codex-verifier-prompt.md`. The agy spec review (COMPLIANT on re-review) and the revert test are done; the independent module-count/test-discrimination/full-suite pass is not.
- **Design v1.15 errata — RULED AND CLOSED 2026-08-21.** The operator required a full Phase-4
  re-audit rather than accepting them. Cycles 17–23 ran; design is now **v1.21**, gated
  `PASS must=0 should=0` on both passes at cycle 23. Both code obligations closed. Nothing owed.
- **Cycle-23 collected reports briefly went missing** — status: recovered and committed
  (`3cd5c84`), cause unproven. Re-collected from `/tmp` and re-gated to the identical verdict. The
  suite is proven NOT destructive (whole-docs-tree snapshot unchanged across a full run).
- **`PREFLIGHT: FAIL unresolved=codex,agy`** — status: known, not blocking. Zero candidate panes in this worktree; `exec` is pane-independent and both CLIs are on PATH. Only the `send`/pane path is affected.
- **Carry-forward, untouched this session** — the 249-row skill-candidate reconcile, advisor-gate live-fire (`HMAD_CONTEXT_WINDOW=1000 claude`), wiring-checker sanity vs a broken matcher, `HMAD_CONTEXT_WINDOW` derived-vs-defaulted, and the 4-file task-tool sweep. All in `.omc/notepad.md`.

## Context for Next Session

**Files touched this session:**
- `docs/01-plan/features/audit-cycle-verb.impl-plan.md` (new, v1.8)
- `docs/01-plan/features/audit-cycle-verb.impl-plan.audit.v{1..9}.p{1,2}.md` (18 new)
- `docs/02-design/features/audit-cycle-verb.design.md` (v1.15 errata)
- `h-mad/scripts/h_mad_audit_cycle.py` (new, Task 1)
- `h-mad/tests/test_h_mad_audit_cycle.py` (new, 21 tests)
- `.h-mad/wires.jsonl`, `docs/.bkit-memory.json` (gitignored state)

**Uncommitted changes:** none. **Nothing unpushed** — `origin/feature/audit-cycle-verb` is level with HEAD. Suite 59/59.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout feature/audit-cycle-verb
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
hmad-dispatch env                       # substrate: orca; PREFLIGHT FAIL is OK for exec
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/test_h_mad_audit_cycle.py -q   # expect 21 passed
/h-mad "audit-cycle-verb"               # resumes at Phase 5, Task 2
```

**Related docs:**
- `docs/01-plan/features/audit-cycle-verb.impl-plan.md` — §"Architecture constraints carried from the plan" (the four measured assumptions, including the live `delivered=out` incident), the twelve-row connection-mutation table, and Version History v1.1–v1.8 recording every refuted prescription so they are not re-derived.
- `h-mad/SKILL.md` §"Phase 5 (Implementation) sub-steps" — the revert-test and mutation contracts.
