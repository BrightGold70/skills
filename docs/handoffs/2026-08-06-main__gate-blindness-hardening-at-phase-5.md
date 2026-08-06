# Handoff — exec-path-hardening shipped; gate-blindness-hardening ready for Phase 5

**Date:** 2026-08-06
**Branch:** main
**Project:** /Users/kimhawk/orca/skills

## Session Summary

Evaluated whether Orca orchestration could replace h-mad's `exec` dispatch (it cannot — weaker
completion signal), then took the resulting `exec-path-hardening` feature through all 7 H-MAD
phases: merged and pushed as `2bf54ca`. The live e2e that the closure report listed as owed was
then actually run, and found **two production defects the whole gate stack had missed** — fixed
and pushed (`63fca45`, `352098a`). Those findings motivated a second feature,
`gate-blindness-hardening`, now complete through Phase 4 with both gates clean and **ready to
enter Phase 5**. Nothing is blocked.

## Key Learnings

- **A live run found what 1063 tests, a clean 5/5 mutation sweep, five wire-scoped reverts and a
  clean architectural review all missed.** `prefix="${current%$rest}"` left `$rest` unquoted, so
  bash glob-matched it instead of stripping a literal suffix. Production verdicts embed the
  agent's markdown (`[x](y)`, `**bold**`), so the strip failed and every stamp emitted the whole
  comment twice. The real worktree card reached **513 spans / 38,329 bytes**; feeding it back
  through the composer reproduced it exactly (513 → 1026). Every fixture used short glob-free
  ASCII, so the bug was not under-tested — it was *unreachable*.
- **`archreview` is optional by omission, not just skippable.** `h_mad_phase7_preconditions.py`
  branches on `WITH_FIXES`/`NO` and `SKIPPED_NO_PANE` with **no `else`**, so a record that never
  wrote the field returns `PHASE7: READY blockers=0`. Probed live. The documented
  `SKIPPED_NO_PANE` escape is not even needed to close a feature with no architectural review.
- **6a-prime is the only pass that looks outside the pinned contract, and the protocol tells you
  to skip it.** It caught `beat) state="running · 0m"` — a heartbeat that would have read `0m`
  for the entire duration of any dispatch. SKILL.md's pane preflight fails in the ordinary case
  (`exec` is the default; stale pins are normal), and its offered remedy is the unchecked hole
  above.
- **`values == sorted(values)` is satisfied by a constant.** That is how the `0m` heartbeat
  passed its own monotonicity AC. Minute granularity was part of the cover: the field cannot
  change inside any short test.
- **I wrote two vacuous tests while closing a gap and only mutation-checking caught them** —
  first env knobs that did not exist in the stubs, then a missing `state=` that made the write
  path unreachable, so it passed with *both* guard layers mutated out.
- **Codex reported `BLOCKED` three times and was right every time** — two test-harness defects in
  tests it had authored during RED, and once refusing to add production behaviour keyed to a test
  env var. Verifying each claim before accepting it was cheap and never wasted.
- **`h_mad_state_write.py` refuses out-of-schema keys, and that is load-bearing.** It rejected
  `match_rate`, which is why the Phase-7 gate reads the rate from the analysis doc instead.
- **The mutation harness needs `root` passed explicitly.** Its spec key is `command` (not
  `suite`) and `root` defaults to the *spec file's* directory — a spec in the scratchpad yields
  `BASELINE_NOT_GREEN`. Both signals were correct and refused to score anything.

## Next Steps

1. **Enter Phase 5 for `gate-blindness-hardening`** — impl-plan → 5b audit + wire-pin gate →
   branch → RED/GREEN → mutation → Phase 6/7. Plan and design are gate-clean; see
   `docs/01-plan/features/gate-blindness-hardening.plan.md` and
   `docs/02-design/features/gate-blindness-hardening.design.md`.
2. **Respect the landing order — it is a safety property, not a preference:**
   **FR-4 → FR-3 → FR-2 → FR-1**, then FR-5/FR-6. Landing FR-1 (absent `archreview` blocks)
   before FR-4 (headless review + auto-record) makes the field mandatory while nothing writes it
   and no override exists — and via the symlink, the first run to hit that is *this feature's own
   Phase 7*. Documented at `docs/01-plan/features/gate-blindness-hardening.plan.md`
   §"Landing order".
3. **Expect to invert six existing assertions**, enumerated in the plan's A5 table
   (`test_h_mad_phase7_preconditions.py` ×2, `test_h_mad_archreview_pane_halt.py` ×4). Each must
   assert the **new** contract positively; a deletion is not a substitute.
   `test_skipping_is_explicitly_not_a_pass` is kept and strengthened as the continuity marker.
4. **Dogfood the gate**: this feature's own 6a-prime must run headless and auto-record, closing
   Phase 7 under the new contract. That is the acceptance evidence, per the design.
5. `[suggested]` **File the two Orca bug docs upstream** to `stablyai/orca` — carried unfiled
   across three sessions now. `docs/orca-bug-worker-release-dispatch-not-found.md`,
   `docs/orca-bug-terminal-read-empty-after-restart.md`. `gh` is authenticated as `BrightGold70`.
6. `[suggested]` **Backfill `docs/skill-monitoring.md`** — it stops at J18 (2026-07-23); J19–J23
   plus this session's findings were never filed, so the registry no longer tracks the exec path.
7. `[suggested]` **Repair the stale pins** — `PREFLIGHT: FAIL stale=codex,agy` ran from the first
   command of this session to the last. `hmad-dispatch pin-agents` or `launch`.

## Open / Blocked Items

- **`gate-blindness-hardening` Phase 5** — status: ready, not started. Claim released this
  session, so the next session can `--claim` without `--force`. State:
  `current_phase=5, last_completed_phase=4`.
- **Two Orca bug docs unfiled upstream** — status: deliberate (operator chose docs-only), carried
  from the 2026-08-05 handoff. Not blocked.
- **`docs/skill-monitoring.md` stops at J18** — status: deferred, explicitly out of scope for
  `gate-blindness-hardening`. Its own pass.
- **Stale codex/agy pane pins** — status: deferred; operational, one command. The whole session
  dispatched headless via `exec`, which is the transport both features are about.
- **6a-prime pane mandate** — status: being fixed by `gate-blindness-hardening` FR-4. Until it
  lands, SKILL.md still instructs recording `SKIPPED_NO_PANE` when a pane does not resolve; this
  session deliberately deviated and ran the review headless instead, recording the deviation in
  `docs/04-report/features/exec-path-hardening.report.md` §Carry.
- **Mutation-harness `root` undocumented in SKILL.md** — status: deferred, noted in the plan's
  Convention Prerequisites so the next Phase 5 does not re-hit it.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/hmad-dispatch.sh` — `_exec_comment_compose`, `_exec_wt_target`, `_exec_stamp`, `_exec_run`
- `h-mad/tests/test_hmad_dispatch_exec_stamp.py` (new), `h-mad/tests/test_hmad_dispatch_exec.py`
- `h-mad/tests/stubs/orca`
- `h-mad/SKILL.md`
- `docs/01-plan/features/exec-path-hardening*`, `docs/02-design/features/exec-path-hardening*`
- `docs/03-analysis/exec-path-hardening.analysis.md`, `docs/04-report/features/exec-path-hardening.report.md`
- `docs/01-plan/features/gate-blindness-hardening*`, `docs/02-design/features/gate-blindness-hardening*`

**Uncommitted changes:** none — feature docs committed as `d1d979f`.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
git pull --ff-only
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
# suite (the default python3 has no pytest):
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/ handoff/ -q     # expect 1148 passed
# then:
/h-mad "gate-blindness-hardening"        # routes to enter_autonomous / Phase 5
```

**Related docs:**
- `docs/02-design/features/gate-blindness-hardening.design.md` — the authoritative design; §"The `archreview` ladder becomes total" and §"Implementation Order"
- `docs/01-plan/features/gate-blindness-hardening.plan.md` — §"Landing order", §A5 (the six inverted assertions)
- `docs/04-report/features/exec-path-hardening.report.md` — what shipped and what the live e2e found
- `docs/03-analysis/exec-path-hardening.analysis.md` — §"What 6a-prime caught that nothing else did"
