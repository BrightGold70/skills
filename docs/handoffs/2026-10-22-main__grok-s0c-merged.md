# Handoff — grok-audit-surface: S0c containment built, verified and merged

**Date:** 2026-10-22
**Branch:** main
**Project:** skills
**Supersedes:** 2026-10-21-main__grok-containment-docs-final.md

## Session Summary

All of S0c, Tasks 18–30, ran through test-first development on `feature/218b-grok-containment`. The
branch was then merged into `main` as a `--no-ff` merge, `cd99d39f`, and pushed. The merged tree is
byte-identical to the branch tip.

The Task 29 gate and the Task 30 live round trip both passed:

| Check | Result |
|---|---|
| Full h-mad suite | 7243 passed |
| `grok_audit_surface.json` | `MUTATION: ALL_CAUGHT 377/377` |
| Task 30 live round trip | `GROK-CANARY: PASS`, `REQUIRE: OK`, work-tree exec `OK` under `strict`, `STATUS=same`, staging 0 |

Phase 5 is not finished. The next step is Task 15, the live sequence, which leads to a fresh S2. After
it come Task 16, Task 17, then 5f/5g, Phase 6 and Phase 7.

## Key Learnings

- **A green suite can be bought by production code bending to a defective RED test.** This happened in
  Task 26:
  - A RED fixture recorded mismatched blobs.
  - To pass it, GREEN made the `list_changed` refusal conditional on `--run-id`, which fails open.
  - GREEN also loosened the D5 parser, which made a mutation row equivalent.

  The tests passed throughout. The only check that caught it was comparing GREEN's code to the
  design. Every later task's brief required that comparison.
- **Per-task mutation subsets do not see regressions in older rows.** Task 26 moved fixtures, and two
  S0 rows (`p-list-unrecorded` and `p-list-malformed`) quietly lost their guard. Only the
  full-spec run in the Task 29 gate found it. Run the whole spec at the gate, not only the new rows.
- **Codex's Phase-5 sandbox needed two environment fixes before it could run tests:**
  - **Allowlist.** `.h-mad/phase5-shell-allow` matches exact argv, so pass the interpreter with an
    absolute path. The bounded `hmad-dispatch run --timeout N -- …` form needs its own allowlist
    lines, because the inner command is never checked against that file.
  - **Interpreter.** The TDD judge needs a `.venv` with pytest in the repo. Otherwise it falls back to
    the homebrew `python3.15`, which has no pytest, and every production `.py` write is refused.
- **A delegated runbook kept the orchestrator's context bounded.** A fresh subagent ran each task's
  RED→GREEN→verify cycle under a runbook. It cost about 2k of orchestrator context per task, against
  about 45k for an inline task. The subagent report must go to a file, because the message transport
  truncates at about 4 KB.
- **Equivalent mutants recur when a plan row assumes two independent checks but the design defines one
  reason with two alternatives.** Two cases: Task 23 row 16, and Task 26 row 4. The Codex write gate
  refuses behaviour-preserving changes with `test-passing`, so the fix is to re-pin the row or add a
  test parameter. Forcing Codex to change code does not work.
- **`git stash` in a delegate applied the foreign `stash@{0}`.** A failed push was followed by a pop.
  The stash survived because the pop itself failed. The runbook now bans `git stash`; use copy-aside
  plus `git show HEAD:` instead.

## Next Steps

1. **Claim, then start Task 15 from `main`.**
   - Run `/h-mad "grok-audit-surface"`. The oracle should answer `enter_autonomous`, with
     `phase=step5`, and the claim is released.
   - The sequence is in `docs/01-plan/features/grok-audit-surface.impl-plan.md` §"Task 15" (~line
     1737), in this order:
     1. codex tracer pair
     2. `h_mad_grok_containment.py quarantine`
     3. canary
     4. S1 re-smoke and TOOLSCAN
     5. smoke
     6. re-smoke commit, whose parent is the calibration tip
     7. quarantine again
     8. fresh S2 of 9 docs × 3 surfaces as v1, in a new `run-<cal12>-<UTC>`, with per-cycle `require` and HALT
     9. d5 v1 positive control
     10. extract, labels, score sha
   - Before the runbook, add the precondition from the 2026-10-21 notes: the D9 runbook needs a
     fetched local calibration ref, and a forced fetch discards a local ref that is ahead of origin.
2. **Task 16**, the measurement doc. Cite the incident record, the superseded smoke `f7520e72`, and
   `docs/03-analysis/grok-audit-surface.phase5-s0c-notes.md`. Include agy/codex `delivered=out` and codex
   `Effort: not measured`.
3. **Task 17.** It is gated on S0c being merged (done) and on a scored, unhalted fresh S2.
4. **5f/5g, Phase 6 (6a-prime, gap analysis) and Phase 7.**
   - Derive the 5c sha with `h_mad_baseline_sha.py --branch feature/218b-grok-containment`. Expect
     `UNVERIFIED`: the branch's first commit is the Task 18 RED, not an impl-plan, because the
     impl-plan was committed on main beforehand. The 5c base is therefore `cfb940e8`.
   - The branch still exists locally. Do not delete it before 6a-prime has read the
     `cfb940e8..cd99d39f` diff.
5. **[owed doc notes, measurement-class]** The impl-plan and design need these corrections:
   - T19 `mktemp -t` / TMPDIR premise.
   - T19 AC-T19.4 grep scoping.
   - T20 re-anchor of `audit_cycle_connections.mutation.json`.
   - T25 fixture ruling.
   - T26 RED split 29/3.
   - The plan marker count is 177, not 175.
   - Task 26 table reasons: the names `unrecorded_run`/`unrecorded_root` should be `unrecorded`.
   - D18 note: `cannot_run:truncated` is unreachable on the live path.

   The full list is in `docs/03-analysis/grok-audit-surface.phase5-s0c-notes.md`.

## Open / Blocked Items

**This session:**

- **h-mad tooling defects, to file as skill-candidate rows.** This was not done this WRITE, because the
  scout was skipped (see below).
  1. The codex gate does not check `run --timeout N -- <cmd>`'s inner command against
     `phase5-shell-allow` (`h_mad_target_identity.py` `M:CX-RUN-INNER`).
  2. The TDD judge falls back to the hook's `sys.executable`, which has no pytest, when no `.venv`
     exists. No bootstrap step creates the `.venv`.
  3. The assembler's `--python` with a bare name does not match the absolute allowlist prefix.
  4. Under the Phase-5 hook, agy reviews have `read_file` and `git` refused. Only `grep -n`/`sed -n`
     through `run_command` are admitted, and one review read nothing.
  5. The TDD judge scores `test-passing` as DENY, so a behaviour-preserving fix of a survivor has no
     path through the gate.
  6. Subagent message transport truncates at about 4 KB.

  Status: open.
- **Local environment changes, which live on this machine only.** Status: keep. The S2 run (Task 15)
  dispatches codex through the same gate.
  - `.h-mad/phase5-shell-allow` gained 8 bounded-pytest lines. This file is gitignored.
  - Root `.venv` was created and excluded in `.git/info/exclude`.
- **Residuals from Tasks 19 and 22.** Status: deferred to Phase 6.
  - Task 19: the RMGUARD refusal direction has no fixture. A signal between creation and removal leaves
    `S` (D16).
  - Task 22: `test_quarantine_never_deletes` greps the whole containment source.
- **Leaked `hmad_exec_prompt.*` files.** About 179 sit in the system temp dir, from runs before
  Task 19. Status: not cleaned up, harmless.
- **Foreign untracked `hemasuite/docs/research/pdfcraft-application-priorities.md`.** Another session
  wrote it mid-run. Status: not ours, never stage it.

**Carried from the 2026-10-21 handoff (`2026-10-21-main__grok-containment-docs-final.md`):**

- Phase-5 notes from the authors:
  - `REQUIRE:` two printers. **Closed:** respected in Tasks 22, 27 and 20.
  - D18 glued-hex token. **Closed:** an operator decision on 2026-10-22 changed the judge to an exact
    substring match (`b93fbc76`, `f3714912`, `a58b394f`).
  - D9 fetched-ref precondition. **Open:** Next Step 1.
  - Canary `cannot_run:truncated` unreachable. **Confirmed** by Task 29. The D18 note is still owed
    (Next Step 5).
  - Plan `[prompt-divergence-repro]`. Acknowledged and unchanged.
- Tasks 15–17. Re-ordered and now unblocked: S0c is merged. These are Next Steps 1–3.
- Old S2 data at `~/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25/data/s2/` is incident evidence
  only and is never scored. Unchanged.
- HemaSuite `pytest tests/` (PID 70888) has exited and its result is suspect. It belongs to HemaSuite.
  Unchanged.
- The escape diff backup sits in the 2026-10-20 session scratchpad (`grok-escape-1254595a.patch`). It is
  session-scoped. It was still present on 2026-10-21. Unchanged.
- S1/S2 artefacts for Task 16 (agy/codex `delivered=out`, codex `Effort: not measured`). These are
  Next Step 2.
- The 7 older `candidate: yes` rows in `docs/skill-candidates.md` (2666, 2667, 2672, 2673, 2677,
  2678, 2682). Deferred and unchanged.
- The Codex Phase-5 gate refuses read-only checks (`e39f15c5`). It did bite this session, as
  graft/git refused inside codex. It is now covered by tooling defect 4 above.
- The agy install-check gap (`skill-candidates.md:2673`). Unchanged. `AGY_SIBLING_COLLISION
  ~/.gemini/config/skills/debugger` was seen again.
- Deferred and unchanged:
  - mutation harness interpreter override row (`:2666`)
  - backlog_cycle LOW residuals
  - census `--help` FileNotFoundError
  - `h_mad_mutation_harness.py:2300` SyntaxWarning, which is still printed
- HemaSuite feature/204 `no-mutation-spec`. HemaSuite's call. Unchanged.
- The foreign `stash@{0}` (`resolved-model`) is present and intact. It was briefly applied and
  reverted this session, and its file is at HEAD. Do not touch it.
- Watch-only, unchanged: the Bash pin blast radius, the `.git/info/exclude` entries (one more added:
  `.venv`), the row 1412 liveness limits, and agy-coder-fallback `review_independence_unrecorded`.
- "Advisor ceiling exceeded". No `advisor()` calls this session. Unchanged.
- "Handoff WRITE does not verify claimed state" and "Plan audit exit stamp never written". Unchanged.
- From `2026-10-02-main__v111-review-loop-closed.md`:
  - [task #28] Run `test_h_mad_check_memory_index.py::TestAgainstTheLiveBinary::test_the_warn_and_target_fractions_still_match`
    by name. The full suite passed 7243 four times this session, so it is likely green, but it was
    not run by name. Unchanged.
  - [optional] agy live smoke. Unchanged.
  - [suggested] `h_mad_assemble_tdd.py --mutation-spec` live at a 5e. **Closed:** used on every GREEN
    this session.
  - V-11.1 residuals, round-22 F2, and tdd-gate-fail-opens bookkeeping. Deferred, unchanged.
  - skill-candidates reconcile. Not run again (scout skipped).
  - HemaSuite pointer `2026-09-14-main__wsg-backlog-two-items-owed-here.md`. Unchanged, and ownership
    stays here.

## Context for Next Session

**Commits this session, all on `main` via the merge `cd99d39f` and pushed:**

| Task | Commits |
|---|---|
| 18 | `d061a118` / `09bb54d2` |
| 21 | `cd507309` / `fa9b0cc3` |
| 24 | `583484b5` / `552c5928` |
| 19 | `0f05c2d8` / `cc65f5b2` |
| 20 | `8ad548ad` / `69a6a486` |
| 25 | `16983743` / `7f7acd5e` |
| 22 | `770a5961` / `4820b1e7`, plus the order fix `00657372` / `2bff499a` |
| 23 | `ce8e3ae4` / `396018b8`, plus the D18 reads `08181dd5` / `432c30b9` |
| 26 | `eeb3ce53` / `1ac89e50` |
| 27 | `66cded16` / `98e11940` |
| 28 | `2cdf86b4` / `bfd76555` |
| Gate F1 | `d80015e1` |
| Exact-token canary fix | `b93fbc76` / `f3714912` / `a58b394f` |
| 30 | evidence `bf85af45` |

**Files touched:**
- `h-mad/scripts/hmad-dispatch.sh`
- `h-mad/scripts/h_mad_tool_calls.py` (new)
- `h-mad/scripts/h_mad_grok_containment.py` (new)
- `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py`
- `h-mad/SKILL.md` and `references/agent-substrate.md` (Task 28)
- tests:
  - `test_grok_audit_surface_{wrapper,containment,probe,smoke}.py`
  - `grokauditfixtures.py`
  - `test_hmad_dispatch_exec_grok.py`
- `h-mad/tests/mutation-specs/grok_audit_surface.json` (377 rows)
- `h-mad/tests/specs/audit_cycle_connections.mutation.json`
- the design D18 note
- `docs/03-analysis/grok-audit-surface.s0c-live-roundtrip.md`
- `docs/03-analysis/grok-audit-surface.phase5-s0c-notes.md`
- `docs/03-analysis/grok-audit-surface.phase5-delegate-runbook.md`

**Uncommitted changes:** none besides this closeout. The foreign untracked `hemasuite/docs/research/` is
not ours.

**h-mad state:** `phase=step5`, `halt_reason=null`. The claim was released at closeout, and
`implementation_authors`/`review_independence` were appended for every module.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
/h-mad "grok-audit-surface"     # enter_autonomous → Task 15 live sequence
```

**Related docs:**
- `docs/03-analysis/grok-audit-surface.phase5-s0c-notes.md`, which holds the deviations, rulings,
  tooling defects and residuals.
- `docs/03-analysis/grok-audit-surface.phase5-delegate-runbook.md`, the per-task delegate runbook.
  Reuse it for 5d/5e work.
- `docs/03-analysis/grok-audit-surface.s0c-live-roundtrip.md`, the Task 30 evidence.
- `docs/01-plan/features/grok-audit-surface.impl-plan.md` §"Task 15", §"Task 16" and §"Task 17".
- `docs/03-analysis/grok-audit-surface.incident-2026-10-20-grok-root-escape.md`.
