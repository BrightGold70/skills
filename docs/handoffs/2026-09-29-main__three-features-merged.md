# Handoff — three features merged and pushed; tdd-gate-fail-opens opened at Phase 1

**Date:** 2026-09-29
**Branch:** main
**Project:** skills
**Supersedes:** 2026-09-29-main__three-features-in-5c.md

## Session Summary

A `/loop` session took all three in-flight H-MAD features through Phases 5–7, merged them into main in the planned order, and pushed. The order was codex-tdd-gate-defects (`8ef6009f`), then grok-codex-fallback (`52a78ca8`), then multi-host-runtime (`05bf39c2`, plus the path fix `be2f5f43`). origin/main is at `5020a66e`. A fresh-context 6a verifier found reproducible defects in each feature: tdd-gate D1–D5 were deferred, grok D1/D2 fixed, and mhr D1–D4 all resolved. A new feature, **tdd-gate-fail-opens**, now covers the deferred tdd-gate D1–D5. Its Phase 1 brainstorm (`5020a66e`) is written and **waits for operator approval**. The session stopped at 73% context.

## Key Learnings

- **Every merge needs a merged-tree suite run.** A fresh-context adversarial 6a verifier found reproducible defects in all three features after the suite, the mutation harness and agy `READY_TO_MERGE` had all passed. agy's clean reviews read 4, 17 and 35 tools and named no file:line findings.
- **A merged-tree suite catches what worktree suites cannot.** mhr's D2 fix baked the worktree's absolute path into three adapters. The tests compared against "this checkout's path", so they passed in the worktree and failed 4 ways on main. Run the suite on the merged main before pushing, even when the merge reports `identity=y` and docs moved.
- **Codex fix prompts must forbid format and design changes.** The mhr D3 fix invented an `exec_input` log format that real codex never emits, and rewrote 30 fixtures and the design. It was discarded, and the design's stated residual was pinned instead.
- **Plan RED splits can be wrong when a test asserts a diagnostic that only GREEN can print.** That happened with grok v1.5.1. A later guard can also mask an earlier guard's outcome (grok G9, v1.6.1). Fix the plan or the test, never the gate.
- **The harness runs pytest from `h-mad/`, not the repo root.** Tests that shell out with repo-relative paths (`git archive … h-mad`) read `BASELINE_NOT_GREEN` there, so pin `cwd`.
- **Wire registration on main strands features that merge earlier.** Registering one feature's wires on main (`6156a2dc`, mhr) made every earlier-merging feature's 5f verify read `missing=N`. The operator accepted and recorded it for grok. Registry verify is not feature-scoped.
- **zsh does not split an unquoted `$T`.** `no tests ran` appeared again this session and is not a result.
- **`h_mad_telemetry.py record` never reads the state's `iterate_cycles`.** It printed 0 for grok (1) and mhr (2).

## Next Steps

1. **Approve or revise the tdd-gate-fail-opens brainstorm:** `docs/01-plan/features/tdd-gate-fail-opens-brainstorm.md`.
   - It carries three operator decisions: scope D1–D5 all, resolve-first in both gates, and case-fold the `.py` suffix.
   - It has two open questions: whether a dangling or looping symlink target is refused, and whether D5 gets its own DENY kind.
   - Then run `/h-mad "tdd-gate-fail-opens"` → Phase 2, which dispatches `spec-author`.
2. **Decide what to do with the new untracked files on main:** `.agents/` and `skills-lock.json` appeared this session and are not this session's. Also the pre-existing `.gitignore` edit (`+/graft/`), `.ignore`, `.mcp.json`, `AGENTS.md`, `opencode.json` and `docs/03-analysis/jev-system-one-adaptation.md`.
3. **Remove the three merged worktrees and branches when idle.** Phase 7 integrate reported them and left them in place:
   - `git worktree remove /Users/kimhawk/orca/skills-codex-tdd-gate-defects && git branch -d feature/codex-tdd-gate-defects`
   - same for `skills-grok-codex-fallback` (`feature/216-grok-codex-fallback`) and `skills-multi-host-runtime` (`feature/multi-host-runtime`).
4. **Re-arm HemaSuite #28's codex TDD hook.** The tdd-gate shipped, so the hook can be re-armed once it is live-verified in HemaSuite.
   - Location: repo `/Users/kimhawk/orca/HemaSuite`, branch `feature/28-review-manifest-guideline-evidence`.

## Open / Blocked Items

- **tdd-gate-fail-opens** is at Phase 1 and waits on operator approval.
  - This session holds the claim, and releases it at closeout.
  - Record: `docs/.bkit-memory.json`, `current_phase=1`.
- **Carried defects, filed in `docs/skill-candidates.md`:**
  - grok D3: non-identifier `CLAUDE*` env names leak to the grok child.
  - grok D4: the heartbeat can split an event; this fails closed.
  - The codex TDD gate denies the documented resume call: the script is not in `SAFE_HMAD_SCRIPT_OPTIONS`, and `$(cat …)` fails the gate's shell rule.
  - The telemetry `iterate_cycles` bug.
  - The in-place `conftest.py` mutation by two suite tests (`b1f8954c`), the source of the "concurrency artifact" flakes.
- **Live smoke runs still owed:**
  - mhr V-11.1..V-11.5 live runs are an operator step; `live-smoke.md` is absent.
  - OQ-D1's Codex half is open because the Codex gate is not registered on this machine.
- **grok quality measurement (D4 follow-up):** deferred, unchanged since 2026-09-28.
- **Pre-existing suite failure `test_top_level_key_set_still_matches`** (live-binary drift): unchanged.
- **Carried from 2026-09-15:**
  - The `exec-pane` wrapper leak (open row `:2186`) is unchanged.
  - The HemaSuite pointer (`2026-09-14-main__wsg-backlog-two-items-owed-here.md`) is answered, and ownership stays here. Unchanged.
- **Closed this session:**
  - tdd-gate Tasks 10–11, 5f/5g, Phase 6 and Phase 7: merged `8ef6009f`.
  - Task 10 verify: `ab83ae92`.
  - The wire-registry flake: explained by the in-place `conftest.py` mutation (3/3 pass alone).
  - `.h-mad/wires.jsonl` on main: committed `6156a2dc`.
  - grok rebase, Tasks 12 and 14–17, Phases 6–7: merged `52a78ca8`.
  - mhr rebase, 5f/5g, Phases 6–7: merged `05bf39c2` and `be2f5f43`.
  - Pushing main: done through `5020a66e`.
- **Foreign stash:** `stash@{0}` ("resolved-model") is untouched.

## Context for Next Session

**Files touched this session (main):**
- Merges of the three features.
- `docs/skill-candidates.md`
- `h-mad/references/{codex,agy,grok}-runtime.md`
- `h-mad/tests/test_host_runtime_docs.py`
- `h-mad/tests/test_h_mad_codex_tdd_gate_judge.py`
- `docs/01-plan/features/tdd-gate-fail-opens-brainstorm.md`

**Worktrees** (all merged, idle, and not removed):
- `/Users/kimhawk/orca/skills-codex-tdd-gate-defects`
- `/Users/kimhawk/orca/skills-grok-codex-fallback`
- `/Users/kimhawk/orca/skills-multi-host-runtime`

**Uncommitted changes (main):** none of this session's. The pre-existing and foreign files are listed in Next Steps item 2.

**Scratchpad** (probe outputs, discarded mhr D3 work in `mhr_d3_discarded/`): `/private/tmp/claude-501/-Users-kimhawk-orca-skills/ddcfd1dc-41bb-4886-ba51-8c094fc1704e/scratchpad`

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short
/h-mad "tdd-gate-fail-opens"
```

**Related docs:**
- `docs/archive/2026-09/codex-tdd-gate-defects/codex-tdd-gate-defects.gap.v1.md` (the D1–D5 repros)
- `docs/archive/2026-09/{codex-tdd-gate-defects,grok-codex-fallback,multi-host-runtime}/*.report.md`
