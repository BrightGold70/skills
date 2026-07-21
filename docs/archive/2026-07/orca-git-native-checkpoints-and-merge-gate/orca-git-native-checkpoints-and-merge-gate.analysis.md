# Analysis: orca-git-native-checkpoints-and-merge-gate

## Executive Summary
All 9 FRs are implemented — the two code FRs (verbs, default flip) are covered by 13 passing pytest cases, and the seven prose-protocol FRs are present in the skill/reference docs and confirmed by the agy 6a-prime architectural review (READY_TO_MERGE). Ready for Phase 7.

## Match Rate: 100%

## FR Coverage

| FR | ACs Total | ACs Met | Status | Evidence |
|---|---|---|---|---|
| FR-1: worktree-comment + worktree-current verbs | 7 | 7 | ✅ Complete | `h-mad/scripts/hmad-dispatch.sh` `_cmd_worktree_comment`/`_cmd_worktree_current`, header + `main()`; tests `test_worktree_comment_*`, `test_worktree_current_*` |
| FR-2: substrate default flip | 4 | 4 | ✅ Complete | `_detect_substrate` two-branch swap; `test_detect_default_both_present_is_orca`, `test_detect_cmux_only_is_cmux`, `test_detect_orca_only_is_orca`, `test_detect_override_forces_cmux`, `test_detect_marker_forces_cmux` |
| FR-3: handoff WRITE stamp | 4 | 4 | ✅ Complete | `handoff/SKILL.md` "WRITE — stamp an Orca checkpoint" step + frontmatter |
| FR-4: handoff READ reconcile | 5 | 5 | ✅ Complete | `handoff/SKILL.md` "Orca worktree reconcile" bullet in Step 3 (uses `worktree-current`/`worktree-ps`, read-only) |
| FR-5: substrate-gated degradation | 3 | 3 | ✅ Complete | `[handoff] worktree_comment_skipped` / `worktree_reconcile_skipped` markers; `hmad-dispatch env` gate on both steps |
| FR-6: Phase-5 winner-merge gate | 5 | 5 | ✅ Complete | `orchestration-mode.md` §"Winner-merge decision gate"; `h-mad/SKILL.md` fanout; orchestration-off fallback retained |
| FR-7: progress checkpoints | 3 | 3 | ✅ Complete | `orchestration-mode.md` §"Progress checkpoints" |
| FR-8: diff-anchored review surfacing | 2 | 2 | ✅ Complete | `orchestration-mode.md` §"Reviewing diffs at the merge gate" |
| FR-9: Orca ship-path doc | 2 | 2 | ✅ Complete | `orchestration-mode.md` §"Ship path (Orca)"; `--force-with-lease`, never-force-push preserved |

**Totals: 35/35 ACs met.**

## Gaps
None. Every FR is addressed. No `code-vs-design`, `design-vs-spec`, or `both` unmet-AC classifications — the design was audited clean (cycle 2, all ACs `implemented-as-written`) and the implementation was TDD'd against it.

## Test Results
```
env -u HMAD_ORCA_COORDINATOR_TERMINAL -u HMAD_ORCA_CODEX_TERMINAL -u HMAD_ORCA_AGY_TERMINAL \
    -u HMAD_SUBSTRATE -u CMUX -u CMUX_PANE -u ORCA_SESSION -u ORCA_TERMINAL_ID \
    python3 -m pytest h-mad/tests/ -q
342 passed in 4.96s
```
Note: the suite must be run with the live `HMAD_ORCA_*` session pins stripped — see finding F13 (`run()` helper does not strip them, so an in-session run spuriously fails 8 `orca_identity`/`task`/`await` tests). With pins stripped: 342/342 pass, including the 13 new cases.

## Architectural review (6a-prime)
agy `ASSESSMENT: READY_TO_MERGE` — confirmed: no cross-module coupling violation (verbs follow the existing Orca-wrapper pattern), two-branch swap implemented as specified, Axis-B base + domain invariants fully maintained (marker discipline, skill self-containment, manifest integrity, never-`git push --force`), merge-gate conflict path aborts cleanly.

## Verdict
Match rate: 100% (threshold: 90%). Tests: 342/342 passing (pins stripped). 6a-prime: READY_TO_MERGE.
→ Advance to Phase 7.

## Version History
- v1.0: Initial gap analysis draft.
