# Handoff — agy-coder-fallback Phases 5d–7 done and merged; post-merge Tasks 20–22 next

**Date:** 2026-10-17
**Branch:** main (merged; feature work was on `feature/agy-coder-fallback`, worktree below)
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-10-16-main__agy-coder-fallback-p2-5c.md

## Session Summary

This session implemented all 20 pre-merge impl-plan Tasks (0–19) test-first. Codex authored; I ran every gate myself outside its sandbox.

- **Phase 5:** each task ran RED, GREEN, mutation sweep, revert probe and full suite. The suite went 6042 → 6514 passed, 0 failed. At 5f the wire registry passed 47/47; 5g set `phase=null`.
- **Phase 6:** the agy 6a-prime review returned `READY_TO_MERGE` (`EVIDENCE: PASS`, all 10 production files read). The fresh-context gap analysis scored 100% (9/9 in-scope FRs, 20/20 ACs; FR-8 deferred by D-13).
- **Phase 7:** `PHASE7: READY blockers=0`.
- **Merge:** operator-approved, merged `--no-ff` as `dba9e1f9`. The merged-main suite passed 6514, and the merge is pushed to origin. The live Claude hook is a symlink into main, so the new gates are live.

**Not COMPLETE:** FR-8 (impl-plan Tasks 20–22) runs post-merge on main. The feature is COMPLETE only after AC-8.1 and AC-8.2 pass. State: `current_phase=7`, `last_completed_phase=6`, `phase=null`. The claim is released at this closeout.

## Key Learnings

- **Codex's `workspace-write` sandbox makes the leak-reaper's teardown `ps` fail with `PermissionError`.** Every scoped pytest exits 1, and the mutation harness then refuses its baseline. Declare it in every prompt as a known artefact that must not decide STATUS, and score all sweeps and suites outside the sandbox. Codex returned BLOCKED on it 3 times before I added the note. `[gotcha, 0.7]`
- **Never let Codex run the full suite inside the sandbox.** It takes about 20 min, which ate a 40-min watchdog, and no report came back (Task 0, rc=124). The orchestrator runs the suite outside instead. `[gotcha, 0.7]`
- **A `PATH` entry cannot contain `:`.** A hostile-payload test root with `:` made `shutil.which` blind to its stub bin (Task 2, D5d-3). Hostile bytes go in arguments and file contents, never in a directory placed on PATH. `[gotcha, 0.7]`
- **New warnings break guards that pin an exact warning set.** Adding a Phase-7 warning broke 5 existing tests that assert "no warnings" or an exact set (D5d-5). The plan claimed no existing test was touched. Before adding a warning or verdict code, grep the existing tests for `not result["warnings"]` and exact-set equality. `[gotcha, 0.5]`
- **The wire registry's `verify` collects from the repository root.** Pins must be repo-relative (`h-mad/tests/...`), not `tests/...`. This feature (`ae541fb0`) and `106421f0` both hit it. Register pins repo-relative at 5b. `[gotcha, 0.7]`
- **`h_mad_wire_registry.py verify` uses the PATH `python3`.** Here that is 3.15 with no pytest, so it answers `UNREADABLE`. Run it as `/opt/anaconda3/bin/python3 …`. `[gotcha, 0.5]`
- **The assembler's `--test-path` takes one path.** For a multi-file task, a space-joined pair works in the prompt, but the printed operator re-run line quotes the pair as one path and breaks. The assembler also has no path for `gate`-shaped tasks: Tasks 0, 8, 14, 18 and 19 used hand prompts, or RED with `--expect-fail 0`. Filed as tooling gaps below.
- **Expectation-override `--control` flags prove the comparison runs, not that the probe reads its input.** Doctored-input controls (`--root`, a doctored log) are the real test (Task 0). `[pattern, 0.5]`
- **Census probes FAIL by construction after later tasks add rows.** Compare re-runs against the recorded post-task readings (acf_5d_task3_decisions.md, D5d-6, acf_5d_task18_19_record.md), not against the 4e4b5ded EXPECT.

## Next Steps

1. **Resume the feature on main.** Run `python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature agy-coder-fallback --session-id <sid>`, then `--claim <sid>`. Run `hmad-dispatch env` and require `PREFLIGHT: PASS`.
2. **Task 20, post-merge payload capture** (`docs/01-plan/features/agy-coder-fallback.impl-plan.md:1871`). Work in a throwaway fixture project beside this checkout, never under `/tmp`, holding a step5 record and FR-5's exact `.agents/hooks.json` entry. A temporary capture hook records one real `toolCall` per class-(b) tool and per `run_command`, plus `init.tools` and `agy --version`. Then run `class_inventory.py <first-log> <capture>`. This is a `new-behaviour` task, so it gets RED/GREEN on `h-mad/hooks/h-mad-agy-tdd-gate.py` (`PATH_KEYS`).
3. **Task 21, post-merge tracer** (`impl-plan.md:1969`, `operational`). In the same fixture project:
   - FR-8 step 2: a real forbidden write through `hmad-dispatch exec agy` must be refused.
   - Step 2a: a delay handler with a sha-recorded `.agents/hooks.json`.
   - Step 3: the turn timings.
4. **Task 22, adoption and the derived timeout** (`impl-plan.md:2000`). Commit `.agents/hooks.json` only after Task 21's refusal passed. Set `TIMEOUT_DEFAULTS["agy"] = max(900, 3 × slower turn)`, rounded up to a multiple of 60. Add the `fr8_timeout_formula.py` probe. The feature is COMPLETE after AC-8.1 and AC-8.2.
5. **Phase 7 closure** after Task 22:
   - Re-run `h_mad_phase7_preconditions.py`. Main's script now carries the review-independence warnings.
   - Run `--append review_independence=` / `implementation_authors=` per the new SKILL.md procedure. The `--append` writer is live on main now.
   - Write `phase7 complete`. Close the `hmad-notebooklm-carry-fixes` record: Fix 3 (#8) shipped as FR-9 Tasks 13–15 in `dba9e1f9`.

## Open / Blocked Items

**agy-coder-fallback**: merged (`dba9e1f9`, pushed); post-merge FR-8 owed (Next Steps 2–5).
- Location: repo `/Users/kimhawk/orca/skills`, branch `main`.
- The feature worktree `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback` (branch `feature/agy-coder-fallback`, fully merged) can be removed when convenient. Its authoring records are merged into main under `docs/03-analysis/agy-coder-fallback.authoring/`.
- Session artefacts (prompts, logs, reports) live in scratchpad `/private/tmp/claude-501/-Users-kimhawk-orca-skills/c83a0ffe-4d6b-4b3a-bac9-efa79608444a/scratchpad/acf5d/`. That folder is ephemeral; every gating report was copied into `docs/03-analysis/agy-coder-fallback.authoring/`.

**Decisions taken in 5d/5e:** each is recorded in `docs/03-analysis/agy-coder-fallback.authoring/acf_5d_*_decisions.md`.
- **D5d-1:** item 15's literal was vacuous; tightened to `agy is out too`.
- **D5d-2:** GREEN verdict overridden on the sandbox artefact; symbol pins added.
- **D5d-3:** stub bin moved out of the `:`-bearing root.
- **D5d-4:** the `git status` differential oracle corrected.
- **D5d-5:** a `REVIEWED` fixture added for 5 exact-warning-set guards.
- **D5d-6:** the doc-pin census delta comes from Task 13's equivalence test.
- **State provisioning:** main store, no symlink, recorded in `acf_5d_state_provisioning_decision.md` (`59216427`).

**Owed impl-plan wording** (next revision; one line each):
- Task 1 item 15 should state `agy is out too` (D5d-1).
- Task 12's regression-guard paragraph should name the `REVIEWED` fixture (D5d-5).

**Tooling gaps found** (candidates for `docs/skill-candidates.md`):
- **No `gate`-shape path:** the assembler cannot stage a `gate` task.
- **One `--test-path`:** it takes a single path, and the printed re-run line breaks on a multi-file pair.
- **Teardown error not declarable:** there is no `--env-known-failure` form for the sandbox leak-reaper teardown, which is not a node id.
- **Wrong interpreter:** `h_mad_wire_registry.py verify` uses the PATH python.

**Carried from 2026-10-16-main__agy-coder-fallback-p2-5c.md:**
- **Design FR-4 sentence** (Task 4 also fixes `FAIL parser`): unchanged, one-line design follow-up.
- **`failure-recovery.md`** has no rows for the `step5:implementer_*` halts: unchanged, open. The halt names now exist in SKILL.md's staging step.
- **ASSEMBLE-TDD HALT verdict/operational classification** (spec FR-5 residual): unchanged.
- **Fix 3 (#8) WIRE-PIN new-caller RED case:** shipped in FR-9 Tasks 13–15 (`03c9da26`, `2e188047`, `419c288b`), merged in `dba9e1f9`. The `hmad-notebooklm-carry-fixes` record is closed at Phase 7 closure (Next Step 5). Origin: Handover-From HemaSuite · main · session 0980df8b.
- **Skill-candidate triage (OPEN=13):** unchanged. Duplicates: 2595 = 2576, 2598 = 2582.
- **NS2 HemaSuite feature/204 `no-mutation-spec`:** unchanged; HemaSuite's call.
- **Deferred rows:** 1931, 1624, 1679, 1662, 1387, 1348, 2113, 2288, 2364, 2395, 1269; maybe-rows 2481, 2496. Unchanged.
- **Other items, unchanged:**
  - concurrent HemaSuite sessions share the live skill (mutation sweeps run in throwaway worktrees);
  - `#56` residue trichotomy;
  - graft statusline;
  - review residuals on rows 1406, 1937, 1685;
  - pass-log rotation;
  - over-refusals accepted 2026-10-06;
  - V-11.1 residuals;
  - `tdd-gate-fail-opens` bookkeeping.
- **Foreign `stash@{0}` (resolved-model):** unchanged; do not touch.
- **Bash pin blast radius:** unchanged.
- **Memory index above the 17500 target:** unchanged. The `-Users-kimhawk-Coding` index is at 82%.
- **HemaSuite canonical checkout:** 1 ahead / 1 behind with foreign `graft/` edits; unchanged. It still showed 76 dirty status lines during Task 19, and Task 19 did not touch it.
- **`.git/info/exclude`:** narrowed to `/.agents/skills/` (D-10); unchanged. Task 22 relies on `.agents/hooks.json` NOT being ignored.

## Context for Next Session

**Files touched this session (all merged in `dba9e1f9`):**
- **New gate:** `h-mad/hooks/h-mad-agy-tdd-gate.py`.
- **Changed hooks:** `h-mad/hooks/h-mad-tdd-gate.sh`, `h-mad/hooks/h-mad-codex-tdd-gate.py`.
- **Changed scripts** (`h-mad/scripts/`): `h_mad_state_schema.json`, `h_mad_state_validate.py`, `h_mad_tdd_judge.py`, `h_mad_target_identity.py`, `h_mad_hook_wiring.py`, `h_mad_assemble_tdd.py`, `h_mad_state_write.py`, `h_mad_phase7_preconditions.py`.
- **Docs:** `h-mad/SKILL.md`, `h-mad/references/{codex-implementer-prompt,failure-recovery,agy-runtime,state-schema}.md`.
- **Tests:** 15 new or extended test files under `h-mad/tests/` and 10 new mutation specs, re-anchoring included.
- **Analysis:** `docs/03-analysis/probes/agy-coder-fallback/*.py` (7 probes), `docs/03-analysis/agy-coder-fallback.{analysis,analysis.v1,archreview.6a-prime}.md`, `docs/03-analysis/agy-coder-fallback.authoring/acf_5d_*`, and `.h-mad/wires.jsonl`.

**Worktree:**
- **Feature worktree:** `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback`, branch `feature/agy-coder-fallback`, fully merged.
- **Parent repo:** `/Users/kimhawk/orca/skills`, branch `main` at `dba9e1f9`, in sync with origin.

**Uncommitted changes:** none besides this handoff and its learnings.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
# /h-mad "agy-coder-fallback" → resume at phase 7 with FR-8 owed; Tasks 20–22 run on main
/opt/anaconda3/bin/python3 -m pytest h-mad/tests -q -p no:cacheprovider   # floor 6514 passed (~21 min)
```

**Related docs:**
- `docs/01-plan/features/agy-coder-fallback.impl-plan.md` §Tasks 20–22 (v1.2, now on main)
- `docs/02-design/features/agy-coder-fallback.design.md` §"FR-8"
- `docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task18_19_record.md` (final census readings)
