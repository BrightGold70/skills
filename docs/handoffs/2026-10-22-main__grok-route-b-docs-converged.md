# Handoff — grok-audit-surface: route (b) ruled; spec, design and impl-plan converged; Phase 5 next

**Date:** 2026-10-22
**Branch:** main
**Project:** skills
**Supersedes:** 2026-10-22-main__grok-task15-halted.md

## Session Summary

The operator ruled on how Task 15 proceeds.

- **The ruling.** Route (b) adds an audit-prompt path-scope clause. Two follow-up rulings shape it:
  - The clause applies to **calibration cycles only**. Production prompts stay byte-identical.
  - A run with **`assembler=unpinned` is not scored**.
- **The root cause.** The d1 seeded plan names its own worktree paths, and grok ran `ls -d` on
  exactly those paths. Its `find` over `~/.local/state/h-mad` was its own initiative.
- **Where the documents stand:**
  - spec v1.17 → v1.21
  - design v1.13 → v1.16 (new D21, plus the owed D18 note)
  - impl-plan v1.8 → v1.11 (new Tasks 14a–14d before Task 15)
- **The audits.** Three gating doc-auditor rounds ran: 3, then 4, then 1 must-fix, all applied. The
  round-3 fixes were not re-audited. I checked them by grep and by reading the hunks.
- **State.** No code is written yet. All 14 commits are pushed.

## Key Learnings

- **Audits caught build defects only by executing.** Each was found by applying the planned edits
  to a `git archive HEAD h-mad` copy and running pytest, never by reading:
  - `[ -n "${scope_arg[@]+x}" ]` is TRUE for an empty bash array. The test becomes a one-argument
    `[ -n ]`, which would have halted every production audit. Use `[ "${#arr[@]}" -gt 0 ]`.
  - `n="$(grep -c …)"` aborts under `set -euo pipefail` when the count is 0. Add `|| true` and
    compare as a string.
- **Every remediation round introduced new must-fixes** (3, then 4, then 1). Re-audit each fix
  delta.
  - Examples: the `here.txt` write placed after an `exit` path, which made `assemble_halt` runs
    unscorable.
  - A spec change routed to only one document of the spec/design pair.
- **The TDD judge has a 40 s `-x` budget** (`JUDGE_BUDGET_S`).
  - `test_grok_audit_surface_containment.py` already takes 40.5 s, so new tests go in new modules.
  - Real `h_mad_audit_cycle.py` runs cost about 19 s with the default `--report-grace 5`, and
    6.9 s with `--report-grace 0`.
- **Test-isolation traps:**
  - The conftest `HMAD_AUDIT_STEM_DIR` is session-wide, so any absence assertion must use its own
    `tmp_path` stem dir.
  - The real `h_mad_audit_cycle.py` always prints an `[H-MAD]` line after `AUDITCYCLE:`. Assert
    through `auditcycle_lines`, never through the last stdout line.

## Next Steps

1. **Phase-5 preflight (before the first codex dispatch).**
   - Confirm how `h-mad/scripts/h_mad_tdd_judge.py` maps the NEW test modules to their production
     files: `test_grok_audit_surface_path_scope.py` → `h_mad_assemble_audit.py` /
     `hmad-dispatch.sh`, and `test_grok_audit_surface_assembler_pin.py` →
     `h_mad_grok_containment.py`. It may be a table or a naming convention. If the mapping fails,
     the gate DENYs every write.
   - Confirm the Phase-5 hook does not refuse on h-mad `halt_reason` (it is currently
     `route_b_docs_converged`).
   - `.h-mad/phase5-shell-allow` admits `/opt/anaconda3/bin/python3.11 -m pytest` generically.
2. **Task 14a, codex TDD.** `docs/01-plan/features/grok-audit-surface.impl-plan.md` §"Task 14a"
   (v1.11, `d046c388`).
   - The RED prompt carries the F ids only. The GUARD/P ids are a first-green run.
   - Give codex the exact old/new anchors. Its interpreter is `/opt/anaconda3/bin/python3.11`.
3. **Task 14b**, then **14c**, then **14d** (full suite; `MUTATION: ALL_CAUGHT untargeted=0/421`;
   `--durations=3`). Run the full suite per task, not scoped. Keep the tree still during mutation
   runs.
4. **Task 15 run 3** in a new run directory (impl-plan §"Task 15", Setup creates `$RUN/assembler`).
   Reuse `$KEEP/resmoke.sh` and `$KEEP/run-current.env`, rewritten at setup.
5. **Task 16**, then **Task 17**, then 5f/5g, Phase 6 (6a-prime must also read `c4b754b1`,
   `2925febd` and the Task 14 commits), and Phase 7.

## Open / Blocked Items

**This session:**

- **Round-3 fixes not re-audited:** design v1.16 (`5767086f`) and impl-plan v1.11 (`d046c388`).
  - Status: grep-verified, and the hunks read by hand.
  - The assemble_halt assertion string, the PS16 `→ true` row targeting the production GUARD, and
    the 421/423/425 totals are all correct.
  - Run an optional round-4 auditor only if Phase 5 hits an anchor or count surprise.
- **Audit and author reports** are copied to
  `docs/03-analysis/grok-audit-surface.route-b-audits-2026-10-22/` (9 files).
- **Foreign untracked files.** Not ours; never stage them:
  - `hemasuite/docs/research/`
  - `docs/03-analysis/2026-10-22-ai-memory-hmad-handoff-integration.analysis.md`
  - `docs/03-analysis/2026-10-22-billion-context-hmad-handoff-integration.analysis.md`
- **h-mad state:** `phase=step5`, `halt_reason=step5:task15:route_b_docs_converged …`, claim
  released.

**Carried from `2026-10-22-main__grok-task15-halted.md`:**

- **Task 15 route ruling.** CLOSED: route (b), recorded in `242c26bd`.
- **The D18 design note.** CLOSED: design v1.13 D18 step 6 now states the `casefold()` match.
- **Halted run dirs** `$KEEP/run-ab2c85dc2e25-20261022T015212Z` and `…T044856Z`. Incident evidence;
  never score them. Unchanged.
- **h-mad tooling defects.** Open, still not filed as skill-candidate rows (the scout was skipped
  again). Unchanged:
  1. The codex gate does not check `run --timeout` inner commands.
  2. The TDD judge falls back to a python with no pytest when there is no `.venv`.
  3. The assembler's bare `--python`.
  4. agy and codex source reads are refused under the Phase-5 hook.
  5. The judge's test-passing DENY has no path for a behaviour-preserving fix.
  6. Subagent transport truncates at about 4 KB.
  7. The 40 s judge budget against a slow file.
- **Stray `$RUN/roots/graft/.cache/`** in run 2. Harmless. Unchanged.
- **Local env.** Unchanged:
  - `.h-mad/phase5-shell-allow` (8 bounded pytest lines);
  - root `.venv`.
- **Phase 6 residuals.** Deferred, unchanged:
  - T19 RMGUARD fixture (D16);
  - T22 `test_quarantine_never_deletes` greps the whole source.
- **About 179 leaked `hmad_exec_prompt.*`** in system temp. Unchanged.
- **Owed measurement-class notes.** Unchanged:
  - T19 `mktemp -t`/TMPDIR;
  - T19 AC-T19.4 grep scoping;
  - T20 re-anchor `audit_cycle_connections.mutation.json`;
  - T25 fixture ruling;
  - T26 RED split 29/3;
  - plan marker count 177;
  - T26 `unrecorded_*` → `unrecorded`;
  - D18 `cannot_run:truncated` cannot be reached on the live path.
- **Old S2 data** at `~/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25/`. Evidence only,
  read by the step 10 positive control. Unchanged.
- **HemaSuite `pytest tests/` PID 70888.** Exited, result suspect, HemaSuite's. Unchanged.
- **Escape diff backup** `grok-escape-1254595a.patch` in the 2026-10-20 session scratchpad.
  Unchanged.
- **Task 16 inputs:** agy/codex `delivered=out`, codex `Effort: not measured`. Unchanged.
- **7 older `candidate: yes` rows** in `docs/skill-candidates.md` (2666, 2667, 2672, 2673, 2677,
  2678, 2682). Deferred, unchanged.
- **agy install-check gap** (`:2673`, `AGY_SIBLING_COLLISION`). Unchanged.
- **Other deferred items.** Unchanged:
  - mutation-harness interpreter override row (`:2666`);
  - backlog_cycle LOW residuals;
  - census `--help` FileNotFoundError;
  - `h_mad_mutation_harness.py:2300` SyntaxWarning.
- **HemaSuite feature/204 `no-mutation-spec`.** HemaSuite's call. Unchanged.
- **Foreign `stash@{0}` (`resolved-model`).** Do not touch. Unchanged.
- **Watch-only.** Unchanged:
  - the Bash pin blast radius;
  - the `.git/info/exclude` entries;
  - the row 1412 liveness limits;
  - agy-coder-fallback `review_independence_unrecorded`.
- **"Advisor ceiling exceeded".** This session made two `advisor()` calls. Context reached about
  62%, over h-mad's 45% ceiling, which is why the session closed before Phase 5.
- **"Handoff WRITE does not verify claimed state" and "Plan audit exit stamp never written".**
  Unchanged.
- **From `2026-10-02-main__v111-review-loop-closed.md`.** Unchanged:
  - [task #28] Run `test_h_mad_check_memory_index.py::TestAgainstTheLiveBinary::test_the_warn_and_target_fractions_still_match`
    by name.
  - [optional] agy live smoke.
  - V-11.1 residuals, round-22 F2, and tdd-gate-fail-opens bookkeeping.
  - The skill-candidates reconcile.
  - HemaSuite pointer `2026-09-14-main__wsg-backlog-two-items-owed-here.md`; ownership stays here.

## Context for Next Session

**Commits this session (all on `main`, pushed):**

| Commit | Content |
|---|---|
| `242c26bd` | Ruling record |
| `d0f784dc` → `061bde85` | Spec v1.17 → v1.21 |
| `8a27d264` → `5767086f` | Design v1.13 → v1.16 |
| `7e1c48e3` → `d046c388` | Impl-plan v1.8 → v1.11 |

**Files touched:**
- `docs/03-analysis/grok-audit-surface.incident-2026-10-22-task15-halts.md` (§Ruling)
- `docs/01-plan/features/grok-audit-surface.spec.md`
- `docs/02-design/features/grok-audit-surface.design.md`
- `docs/01-plan/features/grok-audit-surface.impl-plan.md`
- `docs/03-analysis/grok-audit-surface.route-b-audits-2026-10-22/`

**Uncommitted changes:** none besides this closeout and the audit-report copies. The three foreign
untracked paths remain.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
/h-mad "grok-audit-surface"   # halted at step5; claim, then Phase-5 preflight (Next Step 1) → Task 14a
```

**Related docs:**
- Design D21 (path-scope switch + assembler gate), D8, D14, D15, D18
- Spec AC-3.6, AC-3.9, AC-1.9, Delivery by outcome
- Impl-plan §"Task 14a"–§"Task 14d", §"Task 15", §"Task 16"
