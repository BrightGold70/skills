# Analysis: fanout-integrity-and-defects

> Cycle 1 — measured at commit `b4e5aa6` (Phase 5g).

## Executive Summary

All nine FRs are implemented with every acceptance criterion asserted, the suite is green at
592/592 with zero regressions against the 550 baseline, and every guard was verified to
discriminate by mutation rather than by a passing run.

## Match Rate: 100%

FR-level (FRs where *every* AC is met ÷ total FRs): **9/9 = 100%**.
AC-level, for calibration: **35/35 = 100%**.

## FR Coverage

| FR | ACs Total | ACs Met | Status | Evidence |
|---|---|---|---|---|
| FR-1: refuse uncommitted changes | 4 | 4 | ✅ Complete | `hmad-dispatch.sh` `_worktree_holds_work`; `test_worktree_rm_refuses_modified_tracked_repo`, `..._refuses_untracked_repo`, `..._ignores_ignored_only_change` |
| FR-2: refuse unmerged commits | 4 | 4 | ✅ Complete | `_worktree_default_base` + `_worktree_holds_work`; `test_worktree_rm_refuses_unmerged_commit`, `..._allows_commits_reachable_from_base`, `..._skips_unmerged_check_without_default_base` |
| FR-3: `--force` overrides and announces | 3 | 3 | ✅ Complete | `_cmd_worktree_rm` force branch; `test_worktree_rm_force_short_circuits_dirty_repo` + the **unmodified** `test_worktree_rm_argv_force_and_failure` |
| FR-4: unguarded paths unchanged | 4 | 4 | ✅ Complete | `test_worktree_rm_unresolvable_selector_is_removed`, plus the pre-existing argv/cmux/idempotence tests, all passing unmodified |
| FR-5: `worktree-create` task-id | 4 | 4 | ✅ Complete | `_cmd_worktree_create`; `test_worktree_create_prompt_registers_task_on_stderr`, `..._task_id_can_open_gate`, `..._task_registration_failure_is_nonfatal`, `..._without_prompt_registers_no_task` |
| FR-6: `started_ts` = now(UTC) | 4 | 4 | ✅ Complete | `h_mad_state_write.py:139`; `test_default_started_ts_is_current_utc_time_not_epoch`, `test_explicit_started_ts_is_stored_verbatim` (AC-6.2, unlabelled), `test_new_default_started_ts_produces_short_telemetry_elapsed` |
| FR-7: contentless concern is an error | 6 | 6 | ✅ Complete | `h_mad_extract_verdict.py` `concern_stated` + `main()`; `TestConcernContent` parametrised set, `test_contentless_done_with_concerns_exits_2_without_verdict` (AC-7.5), the `none of the tests…` case (AC-7.6), `test_other_contracts_are_unaffected_without_concerns` |
| FR-8: concern obligation stated | 2 | 2 | ✅ Complete | `references/codex-implementer-prompt.md`; `test_codex_prompt_requires_a_named_concern` |
| FR-9: docs match machinery | 4 | 4 | ✅ Complete | `SKILL.md`, `references/orchestration-mode.md`; `test_skill_documents_worktree_rm_guards`, `test_orchestration_mode_documents_task_id_on_both_paths`, `test_fanout_teardown_documents_the_base_override`, `test_skill_frontmatter_still_valid` |

## Gaps

None outstanding.

**Three ACs are covered but unlabelled** — AC-6.2, AC-7.5 and AC-7.6 have assertions without
naming the AC in a docstring. Counted as met on the strength of the assertion, not the label. A
label-only comparison would have reported three false gaps here, which is the same trap Wave 3 hit.

## Guards found vacuous during verification, and fixed

Two guards passed their tests while not being enforced. Both were found by mutation, neither by
review, and both are recorded because a green suite concealing an unenforced guard is the exact
defect class this wave exists to remove.

1. **The `--prompt-file` gate (FR-5).** Replacing `[ -n "$pf" ]` with `true` — registering a task
   unconditionally — broke **nothing**. The pre-existing argv test passes whether or not the gate
   exists, because `run()` strips `HMAD_ORCA_*`, so `_coordinator()` fails and `task-create` returns
   before ever calling `orca`; the capture stays clean for the wrong reason. Closed by
   `test_worktree_create_without_prompt_registers_no_task`, which pins a coordinator to remove that
   accident. It now fails under the same mutation.
2. **My own `--base` documentation test (FR-9).** Asserting that `--base` and "feature branch"
   appear somewhere passed with the guidance deleted, because both documents already carry
   `--base <ref>` in a verb table and "feature branch" in unrelated prose. Re-anchored on the literal
   `--base <feature-branch>` form; it now fails when either file loses it.

## Test Results

```
/opt/anaconda3/bin/python3 -m pytest h-mad/tests/ -q
592 passed in 20.69s
```

Baseline before this feature: 550. No test was weakened, skipped or deleted.

Mutation results — every guard was disabled in turn and the suite re-run:

| Mutation | Failures |
|---|---|
| `_worktree_holds_work` → `return 0` | 3 |
| `--force` no longer short-circuits | 2 (one of them the **pre-existing** exact-capture assertion) |
| `--prompt-file` gate → `true` | 0 before the fix, 1 after |
| `started_ts` → epoch sentinel | 2 |
| `concern_stated` → `return True` | 10 |
| `--base <feature-branch>` stripped from `SKILL.md` | 1 |
| `--base <feature-branch>` stripped from `orchestration-mode.md` | 1 |

## Live verification beyond the suite

J15 was reproduced against a **real Orca worktree**, not a stub, in the exact Wave-3 shape:

| Case | Result |
|---|---|
| Untracked + modified, uncommitted | `worktree_has_uncommitted_work`, rc=1, worktree and work both survived |
| Committed but not merged | `worktree_has_unmerged_commits`, rc=1 |
| `--base <feature-branch>`, 1 real unmerged commit | still refused |
| `--base HEAD`, all reachable | removed cleanly |

J10's detector was replayed against the 13 real `DONE_WITH_CONCERNS` reports on this machine and
reproduced the prototype exactly: 6 state a concern, 7 do not.

## Verdict

Match rate: 100% (threshold: 90%). Tests: 592/592 passing.
→ **Advance to Phase 7**, subject to the 6a-prime assessment.

## Version History
- v1.0: Initial gap analysis draft.
