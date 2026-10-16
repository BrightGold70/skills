# Handoff — agy-coder-fallback Phases 2–5c done; 5d (Codex RED/GREEN) next

**Date:** 2026-10-16
**Branch:** main (docs) · feature work on `feature/agy-coder-fallback` (worktree below)
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-10-16-main__agy-peer-implementer-p1.md

## Session Summary

This session took `agy-coder-fallback` from Phase 2 through Phase 5c.

**Documents (all operator-approved):**
- spec v1.10 @ `c283bb63`: 21 ACs, decisions D-1..D-16
- plan v1.6 @ `8e242d06`
- design v1.4 @ `2cd5d7f1`
- impl-plan v1.2: 23 tasks, 2 of them wiring, 88 mutation rows

Each audited phase ran the two-round cap with codex and agy, then took a final corrective revision.

**5c:**
- Branch `feature/agy-coder-fallback` lives in worktree `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback`.
- Its first commit, `d280af07`, is the impl-plan v1.2. `h_mad_baseline_sha.py` returns `BASELINE: OK sha=d280af07…`.
- Wires were registered in `7919a542`.

**State:** `phase=step5`, `current_phase=5`, `last_completed_phase=4`; substrate recorded as orca. The claim is released at this closeout. No production code has been written. Next is 5d: dispatch Codex RED for Task 0/1.

## Key Learnings

- **An implementer agent's final chat message is not the deliverable.** Three author dispatches returned "No change." or similar as their message after the work was done. The REPORT file plus `h_mad_done_gate.py` was the only reliable signal: gate on the file, never on the message.
- **A relay to a running author lands only if it arrives before its last step.** Otherwise the agent is resumed and reports again: the plan author went v1.5 → v1.6 that way. Wait for the second notification before committing.
- **The h-mad state file is gitignored, so a new git worktree has none.** The TDD gate reads state from the target's tree, so all gates stand down in a feature worktree. The design flags this as a pre-existing residual, and it must be resolved before 5d (Next Step 1). `[gotcha, 0.7]`
- **agy design audits on prompts of about 270 KB can hit a 1800 s timeout while still reading** (rc=124, `RESULT status=ERROR`, no report). Re-dispatch on a fresh assembled prompt with `--timeout 3300`. The second run finished in about 87 tool calls. `[gotcha, 0.5]`
- **`audit-cycle`'s Effort counter shows codex legs as `tools=0` or "not measured".** It parses only agy stream-json. Judge a codex leg by its cited controlled executions, not by that line.
- **Close the class, every round.** Each decision sheet carried explicit class sweeps: deny gating, anchor re-anchoring, verdict exit-0 and `[H-MAD]` markers. Several findings were caught as class members, not as the one instance a reviewer named.

## Next Steps

1. **Resolve state provisioning in the feature worktree before 5d.**
   - `docs/.bkit-memory.json` is gitignored (`.gitignore:21`) and absent in the worktree, so the TDD gate stands down there.
   - Options: symlink the worktree's `docs/.bkit-memory.json` to the main file, or run h-mad state ops against the main store with `--cd <worktree>` for dispatch. Decide, record, then proceed.
   - Note that this repo has no `.codex/hooks.json`, so Codex writes here are not gated by `h-mad-codex-tdd-gate.py`. The plan/spec already note this.
2. **Claim and resume.**
   - `python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature agy-coder-fallback --session-id <sid>`
   - Then `--claim`, and run `hmad-dispatch env` and require `PREFLIGHT: PASS`.
3. **Before the first RED, run the prescribed-block check:**
   - `python3 ~/.claude/skills/h-mad/scripts/h_mad_prescribed_block_guards.py docs/01-plan/features/agy-coder-fallback.impl-plan.md --repo-root /Users/kimhawk/orca/workspaces/skills/agy-coder-fallback`
   - Read the `PRESCRIBED-BLOCKS:` token.
4. **5d Task-by-task.**
   - Stage each dispatch with `h_mad_assemble_tdd.py --phase red --task <N> --expect-fail/--expect-pass` (counts from the impl-plan), with `--test-path` under `h-mad/tests`.
   - Dispatch with `hmad-dispatch exec codex … --cd <worktree> --log … &`, then `progress`, then `h_mad_extract_verdict.py --key STATUS`.
   - Use the interpreter `/opt/anaconda3/bin/python3`.
5. **5e per Task.**
   - GREEN with `--mutation-spec`, then the revert test.
   - Before 5e, add an `implementation_authors` append step to SKILL.md. It is FR-10, an impl-plan Task.
   - FR-8's live tracer is post-merge (D-13). COMPLETE only after AC-8.1 and AC-8.2 pass.

## Open / Blocked Items

**agy-coder-fallback** — status: Phase 5c done, 5d next, blocked on Next Step 1 (worktree state).
- Location:
  - repo: `/Users/kimhawk/orca/skills` · branch: `feature/agy-coder-fallback` · worktree: `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback`
  - impl-plan v1.2 exists only on the branch; main holds v1.1 at `fc92becf`.
- Author reports, decision sheets and owed lists are persisted in `docs/03-analysis/agy-coder-fallback.authoring/`.
- Open decisions inside the impl-plan:
  - OD-1 is closed: (A) a transcription test.
  - OD-2 is closed: a directory target is refused under S.
- Known follow-ups:
  - The design FR-4 sentence may still say Task 4 corrects only `FAIL shell-policy`. Task 4 now fixes `FAIL parser` too. One-line design follow-up.
  - `failure-recovery.md` has no rows for the three `step5:implementer_*` halts. Open; not in scope.
  - A later feature should classify the existing ASSEMBLE-TDD HALT reasons as verdict or operational (spec FR-5 residual).

**Carried from `2026-10-16-main__agy-peer-implementer-p1.md`:**
- **agy-coder-fallback Phase 2:** CLOSED. Phases 2–5c are done (above).
- **Fix 3 (#8) WIRE-PIN new-caller RED case:** folded into agy-coder-fallback FR-9, impl-plan Tasks 13–15. It lands with that feature's 5d/5e. The `hmad-notebooklm-carry-fixes` record stays open until it lands. Origin: Handover-From HemaSuite · main · session 0980df8b.
- **Skill-candidate triage (OPEN=13):** unchanged. Run `python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md`. Duplicates: 2595 = 2576, 2598 = 2582.
- **NS2 HemaSuite feature/204 `INCOMPLETE reason=no-mutation-spec`:** unchanged; HemaSuite's call.
- **Unchanged since 2026-10-05:** deferred rows 1931, 1624, 1679, 1662, 1387, 1348, 2113, 2288.
- **Unchanged since 2026-10-12:**
  - rows 2364, 2395, 1269 (deferred);
  - rows 2481, 2496 (maybe).
- **Unchanged:**
  - concurrent HemaSuite sessions share the live skill through symlinks, so mutation sweeps run in throwaway worktrees;
  - `#56` residue trichotomy;
  - graft statusline;
  - review residuals on rows 1406, 1937 and 1685;
  - pass-log rotation;
  - over-refusals accepted 2026-10-06;
  - V-11.1 residuals;
  - `tdd-gate-fail-opens` bookkeeping.
- **Foreign `stash@{0}` (resolved-model):** unchanged; do not touch.
- **Bash pin blast radius:** unchanged (`h_mad_bash4_fence_probe.py`).
- **Memory index above the 17500 target:** unchanged. A SessionStart hook warns that the `-Users-kimhawk-Coding` index is at 81%.
- **HemaSuite canonical checkout 1 ahead / 1 behind with foreign `graft/` edits:** unchanged. Run `git -C /Users/kimhawk/orca/HemaSuite pull --rebase` when that lane is idle.
- **Local config change, not versioned:** in this clone, `.git/info/exclude` line `/.agents/` was narrowed to `/.agents/skills/` (D-10, operator). The backup is `/tmp/exclude.bak` (ephemeral).

## Context for Next Session

**Files touched this session:**
- `docs/01-plan/features/agy-coder-fallback.{spec,plan,impl-plan}.md`
- `docs/01-plan/features/agy-coder-fallback.{plan,impl-plan}.audit.v*.md` and their sidecars
- `docs/02-design/features/agy-coder-fallback.design.md` and `.design.audit.v*.md`
- `docs/03-analysis/agy-coder-fallback.plan.delta-review.*`
- `docs/03-analysis/probes/agy-coder-fallback/{fr3_state_line_grammar,fr6_import_failure_pair}.py`
- `docs/03-analysis/agy-coder-fallback.authoring/`
- `.h-mad/wires.jsonl`

**Worktree:**
- Worktree root: `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback`, branch `feature/agy-coder-fallback` (5c = `d280af07`)
- Parent repo: `/Users/kimhawk/orca/skills`, branch `main`, 31 commits ahead of origin (pushed at this closeout)

**Uncommitted changes:** none besides this handoff, its learnings and the persisted authoring directory.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
# /h-mad "agy-coder-fallback"   → resume_manual @ phase 5; settle Next Step 1, then 5d in the worktree
cd /Users/kimhawk/orca/workspaces/skills/agy-coder-fallback   # where Codex dispatches run (--cd)
```

**Related docs:**
- `docs/01-plan/features/agy-coder-fallback.impl-plan.md` (on the feature branch, v1.2)
- `docs/02-design/features/agy-coder-fallback.design.md` v1.4: §FR-4 deny table, kinds, T-sequence
- `docs/03-analysis/agy-coder-fallback.authoring/acf_ip_c2_decisions.md`
