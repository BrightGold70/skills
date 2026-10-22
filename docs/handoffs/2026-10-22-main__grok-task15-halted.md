# Handoff — grok-audit-surface Task 15: two live runs halted; a ruling is needed before run 3

**Date:** 2026-10-22
**Branch:** main
**Project:** skills
**Supersedes:** 2026-10-22-main__grok-s0c-merged.md

## Session Summary

Task 15, the live sequence, was started from `main` and halted twice. Both runs are recorded in
`docs/03-analysis/grok-audit-surface.incident-2026-10-22-task15-halts.md` (`b86a0480`). Neither run
is scored. Nothing was pushed to `calibration/grok-audit-surface`, which is still `f7520e72`.

- **Run 1** stopped at the canary with `no_denial`. The judge required the capitalised
  `Operation not permitted`, but zsh prints it in lowercase. The fix was operator-approved and
  shipped test-first:
  - RED `c4b754b1`, GREEN `2925febd`, authored by codex.
  - Full h-mad suite: 7246 passed.
  - Mutation spec: `MUTATION: ALL_CAUGHT 378/378`.
- **Run 2** passed setup, the tracer pair (`pass/pass`), the first quarantine and the canary
  (`GROK-CANARY: PASS`). It then halted on the first re-smoke grok cycle:
  - `TOOLSCAN: OUT_OF_ROOT out_of_root=2 checkout=1`.
  - grok ran `ls`/`find` against the live checkout. The sandbox denied the reads and the output was
    empty, but the D19 scan halts on any attempt.

The operator chose to stop here. The h-mad state carries `halt_reason`, and the claim is released.

## Key Learnings

- **The containment scan halts on attempts, not on successful reads.** grok searches outside its
  root on its own initiative ("Locate plan doc and skills worktree"). Under `strict`, those reads
  return empty, but the call still names the path. Expect every run to halt until a ruling changes
  either the scan rule or the prompt.
- **The canary judge must not depend on the exact error wording.** zsh prints `operation not
  permitted` in lowercase. grok's Bash tool `rawOutput.output` is a **byte list** (a list of
  ints); the text survives only in `output_for_prompt`. grok's `write` tool on a sandbox-denied
  path fails with `File exists (os error 17)`, not EPERM.
- **The codex Phase-5 write gate cannot reach a RED test at the end of a slow test file.** The TDD
  judge runs the mapped file with `-x` inside a 40 s budget (`JUDGE_BUDGET_S`), while
  `test_grok_audit_surface_containment.py` takes about 70 s. The workaround was to move the RED
  test to the top of the file for the dispatch, then restore the committed file byte-for-byte.
- **Codex in Phase 5 needs the exact old and new line.**
  - Its `sed -n`/graft reads were refused, so GREEN only landed once the prompt carried both lines
    for `apply_patch`.
  - Its allowlisted pytest interpreter is `/opt/anaconda3/bin/python3.11`, not `.venv/bin/python`.
- **Editing any tracked file during a mutation run makes it `TREE_MOVED`**, even a document no
  mutation row reads. Keep the tree still and re-run on the commit.
- **Shell state does not survive between tool calls.** The live run's variables live in
  `$KEEP/run-current.env`; run `source` on it first in every call. The re-smoke runs as a script,
  `$KEEP/resmoke.sh`, in the background, and only its token lines are surfaced.

## Next Steps

1. **Operator ruling on the Task 15 route.** This blocks every further run. Choose one:
   - (a) Change the D19 scan so that an out-of-root call whose read was refused, or returned empty,
     counts as contained. This is a design and spec change via `design-author`/`spec-author`,
     with audits.
   - (b) Add an audit-prompt clause forbidding paths outside the cwd. This is a spec change, and it
     changes the measurement for every surface.
   - (c) Retry as-is. grok's behaviour is nondeterministic. Each attempt costs about 13 minutes of
     grok time and a new run directory.

   The evidence is in `docs/03-analysis/grok-audit-surface.incident-2026-10-22-task15-halts.md`.
2. **After the ruling, run Task 15 again in a new run directory.** Start from step 1 of
   `docs/01-plan/features/grok-audit-surface.impl-plan.md:1737`.
   - Reuse `$KEEP/resmoke.sh`. It reads `$KEEP/run-current.env`, so rewrite that file at setup, as
     this session did.
   - The calibration-ref precondition (`impl-plan.md:1832`) is already in the impl-plan. The
     earlier handoff's "add the precondition" is done.
3. **Route the owed D18 design note to `design-author`.** D18 step 6 still names the literal
   `Operation not permitted`. The note is in `docs/03-analysis/grok-audit-surface.phase5-s0c-notes.md`
   §"Design notes owed".
4. **Task 16** (`impl-plan.md:1864`, titled "S3 publish"; the predecessor called it "the measurement
   doc"). It must also cite both halted runs and the incident record.
5. **Task 17** (`:1967`). It is gated on a scored, unhalted fresh S2.
6. **5f/5g, then Phase 6 (6a-prime and gap analysis), then Phase 7.**
   - The 5c base is `cfb940e8`.
   - Expect `h_mad_baseline_sha.py --branch feature/218b-grok-containment` to report `UNVERIFIED`.
   - Keep the local branch until 6a-prime has read `cfb940e8..cd99d39f`.
   - The fix commits `c4b754b1` and `2925febd` landed on `main`, outside that range. 6a-prime must
     review them too.
7. **[owed doc notes, measurement-class]** These carry over from the predecessor, unchanged:
   - T19: the `mktemp -t`/TMPDIR premise.
   - T19: AC-T19.4 grep scoping.
   - T20: re-anchor `audit_cycle_connections.mutation.json`.
   - T25: the fixture ruling.
   - T26: the RED split, 29/3.
   - The plan marker count is 177.
   - T26: the reasons `unrecorded_run`/`unrecorded_root` should be `unrecorded`.
   - D18: `cannot_run:truncated` cannot be reached on the live path.

   The full list is in `docs/03-analysis/grok-audit-surface.phase5-s0c-notes.md`.

## Open / Blocked Items

**This session:**

- **Task 15 route.** Blocked on the operator ruling in Next Step 1. The h-mad state has
  `halt_reason=step5:task15:resmoke_grok_out_of_root`, `phase=step5`, and the claim released.
- **Halted run directories, kept outside git as incident evidence.** Never score them.
  - `$KEEP/run-ab2c85dc2e25-20261022T015212Z`: the canary refusal. Its env is in
    `run-current.env.final`.
  - `$KEEP/run-ab2c85dc2e25-20261022T044856Z`: the re-smoke halt. `HALT` is present, and the grok
    cycle is recorded under `data/runs/<id>/resmoke/grok`.
- **h-mad tooling defects 5–6, new:** the judge budget against a slow test file, and codex source
  reads being refused. They are recorded in `phase5-s0c-notes.md` §"h-mad defects found". Status:
  open, and not yet rows in `docs/skill-candidates.md`, because the scout was skipped.
- **Stray `$RUN/roots/graft/.cache/`** in run 2. It came from codex's graft MCP server starting in
  the tracer's `--cd`. It is harmless and outside every root.

**Carried from `2026-10-22-main__grok-s0c-merged.md`:**

- **h-mad tooling defects 1–6, to file as skill-candidate rows.** Status: open, unchanged.
  1. The codex gate does not check `run --timeout N --` inner commands.
  2. The TDD judge falls back to a python with no pytest when there is no `.venv`.
  3. The assembler's bare `--python`.
  4. agy reads are refused under the Phase-5 hook (codex reads were refused this session too).
  5. The judge's `test-passing` DENY has no path for a behaviour-preserving fix.
  6. Subagent transport truncates at about 4 KB.
- **Local environment changes, machine-only.** Status: keep, unchanged.
  - `.h-mad/phase5-shell-allow` has 8 bounded-pytest lines, interpreter
    `/opt/anaconda3/bin/python3.11`.
  - Root `.venv` (excluded).
- **Phase 6 residuals.** Status: deferred, unchanged.
  - T19: the RMGUARD refusal fixture (D16).
  - T22: `test_quarantine_never_deletes` greps the whole source.
- **About 179 leaked `hmad_exec_prompt.*` files** in system temp. Status: not cleaned, harmless.
- **Foreign untracked `hemasuite/docs/research/`.** Not ours; never stage it.
- **Phase-5 notes.** The D9 fetched-ref precondition is **closed** (it is in the impl-plan at
  `:1832`). The `cannot_run:truncated` D18 note is still owed (Next Step 7). The plan's
  `[prompt-divergence-repro]` is unchanged.
- **Old S2 data** at `~/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25/`. It is incident
  evidence only; it is read by the step 10 positive control and never scored. Unchanged.
- **HemaSuite `pytest tests/` PID 70888.** Exited, result suspect, HemaSuite's. Unchanged.
- **Escape diff backup** `grok-escape-1254595a.patch` in the 2026-10-20 session scratchpad.
  Unchanged.
- **Task 16 inputs:** agy/codex `delivered=out`, and codex `Effort: not measured`. Next Step 4.
- **The 7 older `candidate: yes` rows in `docs/skill-candidates.md`** (2666, 2667, 2672, 2673, 2677,
  2678, 2682). Deferred, unchanged.
- **agy install-check gap** (`:2673`). `AGY_SIBLING_COLLISION ~/.gemini/config/skills/debugger` was
  seen again this session. Unchanged.
- **Deferred, unchanged:**
  - The mutation harness interpreter override row (`:2666`).
  - backlog_cycle LOW residuals.
  - The census `--help` FileNotFoundError.
  - The `h_mad_mutation_harness.py:2300` SyntaxWarning.
- **HemaSuite feature/204 `no-mutation-spec`.** HemaSuite's call. Unchanged.
- **Foreign `stash@{0}` (`resolved-model`).** Present; do not touch. Unchanged.
- **Watch-only, unchanged:**
  - The Bash pin blast radius.
  - The `.git/info/exclude` entries.
  - The row 1412 liveness limits.
  - agy-coder-fallback `review_independence_unrecorded`.
- **"Advisor ceiling exceeded".** One `advisor()` call this session, at about 30%.
- **"Handoff WRITE does not verify claimed state" and "Plan audit exit stamp never written".**
  Unchanged.
- **From `2026-10-02-main__v111-review-loop-closed.md`:**
  - [task #28] Run `test_h_mad_check_memory_index.py::TestAgainstTheLiveBinary::test_the_warn_and_target_fractions_still_match`
    by name. The full suite passed 7246 this session, so it is likely green, but it has still not
    been run by name. Unchanged.
  - [optional] agy live smoke. Unchanged.
  - V-11.1 residuals, round-22 F2, and tdd-gate-fail-opens bookkeeping. Deferred, unchanged.
  - The skill-candidates reconcile. Not run (the scout was skipped again).
  - HemaSuite pointer `2026-09-14-main__wsg-backlog-two-items-owed-here.md`. Unchanged; ownership
    stays here.

## Context for Next Session

**Commits this session, all on `main` and pushed:**

| Commit | What |
|---|---|
| `c4b754b1` | RED |
| `2925febd` | GREEN, the mutation spec row, and notes |
| `b86a0480` | The incident record |

**Files touched:**
- `h-mad/scripts/h_mad_grok_containment.py` (`canary_judge`, the `# M:CANARY-DENIAL-ID` line)
- `h-mad/tests/test_grok_audit_surface_containment.py`: 3 tests and the `_write_denial_log` helper
- `h-mad/tests/mutation-specs/grok_audit_surface.json`: 378 rows
- `docs/03-analysis/grok-audit-surface.phase5-s0c-notes.md`
- `docs/03-analysis/grok-audit-surface.incident-2026-10-22-task15-halts.md`

**Outside git:**
- `$KEEP/run-current.env`, which points at run 2.
- `$KEEP/resmoke.sh`.
- The two run directories.

`KEEP=~/.local/state/h-mad/grok-audit-surface`.

**Uncommitted changes:** none besides this closeout. The foreign `hemasuite/docs/research/` is
still there.

**h-mad state:**
- `phase=step5`
- `halt_reason` set (resmoke_grok_out_of_root)
- claim released
- `implementation_authors` gained `h_mad_grok_containment`/codex

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
/h-mad "grok-audit-surface"   # → halted; get the Task 15 route ruling first (Next Step 1)
```

**Related docs:**
- `docs/03-analysis/grok-audit-surface.incident-2026-10-22-task15-halts.md`
- `docs/03-analysis/grok-audit-surface.incident-2026-10-20-grok-root-escape.md`
- `docs/02-design/features/grok-audit-surface.design.md`: D8 `:208`, D18 `:510`, D19 `:527`
- `docs/01-plan/features/grok-audit-surface.impl-plan.md` §"Task 15" `:1737`
