# Handoff — three H-MAD features past design: grok 5–11 GREEN, tdd-gate P4 closed, mhr 5a done

**Date:** 2026-09-28
**Branch:** main
**Project:** skills
**Supersedes:** 2026-09-28-main__three-parallel-hmad-features.md

## Session Summary

This session resumed the three parallel H-MAD features and moved all three past design.

| Feature | Where it stands | Next |
|---|---|---|
| `grok-codex-fallback` | Tasks 5–11 RED+GREEN committed on `feature/216-grok-codex-fallback` (HEAD `0cdbf8e0`), each GREEN verified in both locales, by a named-stash module revert, by a wire-scoped revert per WIRE, and by the full suite | **Task 12 is blocked** on the re-plan onto tdd-gate D13 (see Open Items) |
| `codex-tdd-gate-defects` | Phase 3 exited at the round cap (plan v1.2 → v1.4). Phase 4 exited at the round cap: design v1.2, spec v1.4, plan v1.4 at `dbd91b60` | 5a impl-plan |
| `multi-host-runtime` | Phase 4 exited at the round cap: design v1.2 (`34c0e962`), spec v1.4 + plan v1.3 (`7e155451`). 5a impl-plan v1.0 committed (`98f868b4`: 19 tasks, 3 wiring, 94 mutation rows, WIREPIN PASS) | 5b impl-plan audit |

`.h-mad/invariants.md` was amended by operator decision (`76e7af19`): the self-containment path exception now names `~/.agents/skills` and `~/.gemini/config/skills` beside `~/.claude`. main is 16+ commits ahead of origin and nothing was pushed.

## Key Learnings

- **Python's `re.compile` cache makes an `is` identity test between two separately compiled identical patterns vacuous.** `re.compile(p, re.M)` twice returns one cached object, so grok Task 7's "single-sourced banner" test passed at RED. The fix is `re.purge()` then `importlib.reload()` of the module before the identity check. This is now carried into the mhr impl-plan as a rule.
- **Subprocess tests that assert on `CLAUDE*` env names are not hermetic under this orchestrator.** Claude Code exports about 15 `CLAUDE*` names, so an exact-list guard failed at RED (grok Task 9: 25/5 instead of 23/7). Strip every `^CLAUDE` name and `HPW_AGENT_BACKEND` before a test sets its own, and prove the split with an extra `CLAUDE_ZZZ_PROBE=1`. After this note was added to the dispatch prompts, Tasks 10 and 11 came back right first time.
- **codex was right to `BLOCK` twice, and both times on an impl-plan defect, not its own.** Both BLOCKs were resolved by a narrow test-only amendment prompt with the diagnosis stated. Neither needed an impl-plan revision in-session. Both deviations are recorded in the RED commit messages (`5f50987b`, `29e055fa`), and the impl-plan still carries the old text; see Open Items.
- **After a round cap, the corrective revision is followed by a propagation revision.** The final design revision owes sentences to the spec and plan, and those authors run in parallel. The pattern that worked: commit the pair, cross-check each "owed" sentence by grep against the other document, and only then commit. This caught six missing spec sentences for tdd-gate (spec v1.4) and a live-smoke path conflict for mhr.
- **The audit gate over-counts nested sub-bullets.** `h_mad_audit_gate.py` scored the tdd-gate design teammate report as `must=27 should=37 untagged=49` while the auditor's DONE line and top-level bullets said 3 must. The per-cycle verdict is still FAIL either way, but the exit-check counts are not trustworthy on nested-bullet reports. This is not yet filed.
- **The full h-mad suite has exactly one pre-existing failure on both main and the grok branch:** `test_h_mad_check_plugin_hooks.py::TestAgainstTheLiveBinary::test_top_level_key_set_still_matches`. It comes from live Claude Code binary drift in the `TOP` key set. Every audit cycle's `SUITE:` reads FAIL because of it, and this blocks the exit streak rather than the cycle.

## Next Steps

1. **Re-plan grok Task 12 onto tdd-gate D13 before dispatching it.**
   - Contract: tdd-gate design v1.2 §"D13 — Rebase contract for grok-codex-fallback D2" (`docs/02-design/features/codex-tdd-gate-defects.design.md`) and the `fallback=` wire encoding in D10.
   - Re-plan list: D13 lists the grok artifacts anchored on pre-feature gate text, including Task 14 rows G1–G6 and WR12 and the Task 12 harness. Every test must pass `stdin=` explicitly.
   - Route: dispatch `implplan-author` in the grok worktree (`/Users/kimhawk/orca/skills-grok-codex-fallback`) for impl-plan v1.4. Record the Task 7/Task 9 test deviations there too.
   - Decision owed first: grok merges after tdd-gate, so Task 12 either targets the post-tdd-gate hook, which means rebasing onto tdd-gate first, or is deferred. See Open Items.
2. **grok Tasks 13–16 do not touch the hook and can proceed before Task 12 if dependencies allow.** Check each Task's "Dependencies on other tasks" line. Task 14 (mutation specs) has rows for Task 12 (G1–G6, WR12), so run it after the re-plan.
   - Per-task recipe:
     - `h_mad_assemble_tdd.py --feature grok-codex-fallback --task "Task N" --phase red|green --project-root <wt> --module … --test-path … --python /opt/anaconda3/bin/python --expect-fail X --expect-pass Y --guard …`
     - Append the hermetic-env note to the prompt.
     - Dispatch with `hmad-dispatch exec codex … --cd <wt>` via `run_in_background`.
   - Verification recipe, the one used for Tasks 5–11:
     - re-run under both `en_US.UTF-8` and `C`;
     - check that every plan code line appears verbatim;
     - revert with a named stash, then check the `stash@{0}` label before popping;
     - revert one wire at a time per WIRE;
     - run the full suite in the background;
     - `git checkout -- .gitignore && rm -f .ignore` before each commit.
3. **multi-host-runtime 5b: audit impl-plan v1.0.**
   - Run: `hmad-dispatch audit-cycle --feature multi-host-runtime --phase impl-plan --cycle 1 --passes 1 --surfaces codex --gated docs/01-plan/features/multi-host-runtime.impl-plan.md --legs codex --legs teammate --project-root /Users/kimhawk/orca/skills --project-tests h-mad/tests --suite-cmd "/opt/anaconda3/bin/python -m pytest h-mad/tests -q -p no:cacheprovider"`.
   - Alongside it: a `doc-auditor` teammate full pass over the assembled prompt (`h_mad_assemble_audit.py --phase impl-plan --report-file …`).
   - Cap is two gating rounds. Then 5c: the branch `feature/NNN-multi-host-runtime`, with Task 0 (the probe sidecar) first.
4. **codex-tdd-gate-defects 5a.** Arm `phase=step5`, then dispatch `implplan-author` from design v1.2, spec v1.4 and plan v1.4 at `dbd91b60`. Carry the same Phase-5 lessons as the mhr brief: hermetic env, no `re.compile` identity, named ids, RED splits checked per task.
5. **Operator pre-step, unchanged:** create `~/.agents/skills/{h-mad,handoff}` and `~/.gemini/config/skills/{h-mad,handoff}` symlinks into `/Users/kimhawk/orca/skills` before any live verification.
6. **Merge order, unchanged:** codex-tdd-gate-defects, then grok-codex-fallback, then multi-host-runtime.

## Open / Blocked Items

- **grok Task 12: blocked on the re-plan onto tdd-gate D13.**
  - Location: `repo: /Users/kimhawk/orca/skills · branch: feature/216-grok-codex-fallback · worktree: /Users/kimhawk/orca/skills-grok-codex-fallback`.
  - tdd-gate removes `$ACTIVE`, the hook's `jq` state read and `exit 1`, which grok D2 builds on.
  - Decision owed: rebase grok onto tdd-gate before Task 12, or defer Task 12 until tdd-gate merges.
- **grok impl-plan still states the pre-deviation text for Task 7 test 11 and Task 9's env handling.** The committed tests are correct; the plan text is stale. Fold this into the Task 12 re-plan (impl-plan v1.4).
- **grok Tasks 13–17 are not started.** Task 17 is the live `exec grok` smoke and halts to the operator if grok cannot run. The 5c baseline is `1a8450c2`.
- **multi-host-runtime 5b is not started.** The impl-plan is at `98f868b4`. Its Task 0 probe sidecar (`docs/03-analysis/probes/multi-host-runtime/{calibrate.sh,seed.json,seed_coverage.py}`) is still absent (`ls` gives "No such file").
- **codex-tdd-gate-defects 5a is not started.** Design v1.2, spec v1.4 and plan v1.4 are at `dbd91b60`.
- **codex-tdd-gate-defects OQ-D1 is open for the operator:** the Codex-side host hook timeout. The Claude half is a 5g merge condition (host-deadline probe, design D6).
- **The audit-gate nested-bullet over-count is not filed.** File it as a skill-candidate or `h-mad` issue, with the measurement: `codex-tdd-gate-defects.design.audit.v1.teammate.md` scored `must=27` against a real 3.
- **The pre-existing suite failure is open:** `test_top_level_key_set_still_matches`. It is live-binary drift and is not owned by these features.
- **grok quality measurement (D4 follow-up): deferred**, unchanged since 2026-09-28.
- **Carried from `2026-09-15-main__two-false-task-premises.md` via the predecessor, unchanged and still not re-verified:**
  - (a) the `docs/skill-candidates.md` open-row census: `python3.11 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md`;
  - (b) the `exec-pane` wrapper leak, to be closed by a conftest finalizer;
  - (c) a pointer to HemaSuite: its `docs/handoffs/2026-09-14-main__wsg-backlog-two-items-owed-here.md` Next Step 1 is answered by `docs/04-report/features/wsg-56-impl-plan-ac-enumeration.probe.v1.md`.
- **HemaSuite #28 still runs with the codex TDD hook disarmed,** until codex-tdd-gate-defects ships and is live-verified.
  - Location: `repo: /Users/kimhawk/orca/HemaSuite · branch: feature/28-review-manifest-guideline-evidence`.
  - Ownership stays here; this is unchanged.
- **Closed in the predecessor, not re-emitted:** the assembler-wiring item (`448fd8f3`) and the three HemaSuite foreign items (`fd20459`, `a82d9a4`, `9af64b5`).

## Context for Next Session

**Claims:** all three features are released at this closeout (session `2fdae87c`). `--claim` each one before working it.

**State (`docs/.bkit-memory.json`):**

| Feature | State |
|---|---|
| grok-codex-fallback | `phase=step5`, `current_phase=5` |
| codex-tdd-gate-defects | `current_phase=5`, `last_completed=4`, `phase` not yet `step5` |
| multi-host-runtime | `phase=step5`, `current_phase=5`, `last_completed=4` |

**Worktree:**
- Worktree root: `/Users/kimhawk/orca/skills-grok-codex-fallback`, branch `feature/216-grok-codex-fallback`, 23 commits ahead of main, untracked `graft/` only.
- Parent repo: `/Users/kimhawk/orca/skills`, branch `main`.

**Uncommitted changes (main):** pre-existing only: `.gitignore`, `.ignore`, `.mcp.json`, `AGENTS.md`, `docs/03-analysis/jev-system-one-adaptation.md`, `opencode.json`.

**Foreign stash:** `stash@{0}` ("resolved-model") is untouched. Every revert this session used a named stash and was checked before popping.

**Scratch** (per-task prompts, author reports, suite logs): `/private/tmp/claude-501/-Users-kimhawk-orca-skills/2fdae87c-7cce-4359-ae6b-370ef94ab311/scratchpad/`.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills-grok-codex-fallback && git status --short   # expect ?? graft/
/opt/anaconda3/bin/python -m pytest h-mad/tests/test_hmad_dispatch_audit_cycle_grok.py h-mad/tests/test_hmad_dispatch_progress_grok.py h-mad/tests/test_hmad_dispatch_exec_grok.py -q -p no:cacheprovider   # expect 47 passed
```

**Related docs:**
- tdd-gate:
  - `docs/02-design/features/codex-tdd-gate-defects.design.md` (v1.2, D13)
  - `docs/01-plan/features/codex-tdd-gate-defects.{spec,plan}.md` (v1.4 / v1.4)
- mhr:
  - `docs/02-design/features/multi-host-runtime.design.md` (v1.2)
  - `docs/01-plan/features/multi-host-runtime.{spec,plan,impl-plan}.md` (v1.4 / v1.3 / v1.0)
- grok: `docs/01-plan/features/grok-codex-fallback.impl-plan.md` (on the branch)
- Audit reports: `docs/0{1-plan,2-design}/features/*.audit.v*.{p1,teammate}.md` and `*.delta-review.v1.1.md`
