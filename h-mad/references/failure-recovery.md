# Failure Recovery — per-phase halt routes + recovery hints (v2.2)

**Halt + notify + leave intermediate state.** No auto-rollback.

## Common halt protocol

1. Write `orchestrator_state[<feature>]`: `halt_reason`, `halt_ts`, `phase = null` (clears hook arm), pin `current_phase` + `last_completed_phase`.
2. Emit `[H-MAD] <feature> phase<N> halted reason=<reason>`.
3. `cmux notify --title "/h-mad halted" --subtitle <feature> --body <reason>`.
4. Print recovery hints.
5. Exit.

## Per-phase failure routes (v2.2 numbering)

| Phase | Failure mode | `halt_reason` | Recovery hint |
|---|---|---|---|
| 1–2 | User declines | `<phase>:user_declined` | "Edit artifact; re-run `/h-mad "<feature>"`" |
| 3 | `/pdca plan` non-zero | `step3:bkit_plan_exit_<code>` | "Inspect bkit error; re-run" |
| 3 | 5 audit cycles, must-fix > 0 | `step3:audit_max_cycles` | "Operator override: author `.audit.v6.md` with `## Acknowledged-not-fixed`; commit `[audit-override]`; re-run" |
| 3, 4, 5 | Cmux pane not alive | `<phase>:no_<agent>_pane` | "Launch agent in cmux (`cmux split-window --command 'codex'` or `cmux split-window --command 'agy --dangerously-skip-permissions'`); re-run" |
| 3, 4 | agy dispatch fail (cmux 400) | `<phase>:agy_dispatch_failed` | "Restart agy pane per `CLAUDE.md` §F-12; re-run" |
| 4 | `/pdca design` non-zero | `step4:bkit_design_exit_<code>` | "Inspect bkit error; re-run" |
| 4 | 5 audit cycles, must-fix > 0 | `step4:audit_max_cycles` | (same as Phase 3) |
| 4 | Back-propagation loop ≥ 3 times | `step4:back_prop_max` | "Manual review; revise both plan and design; re-run" |
| 5a | writing-plans failed | `step5a:writing_plans_failed` | "Inspect writing-plans error; re-run" |
| 5b | impl-plan audit must-fix > 0 after 5 cycles | `step5b:impl_plan_audit_max_cycles` | "Operator override: author `.impl-plan.audit.v6.md` with `## Acknowledged-not-fixed`; commit `[audit-override]`; re-run" |
| 5c | Baseline branch failed | `step5c:branch_failed:<stderr>` | "Inspect git error; re-run" |
| 5d | RED tests don't all fail | `step5d:red_not_all_failing` | "Codex's tests passed without implementation — likely test bugs; review; re-run" |
| 5e | GREEN unreachable after 3 retries | `step5e:green_unreachable:<module>` | "Inspect failed module; fix codex prompt or implement manually; re-run" |
| 5e | Codex reports BLOCKED or NEEDS_CONTEXT (v2.1 status enum) | `step5e:codex_blocked:<reason>` or `step5e:codex_needs_context:<reason>` | "Read Codex's reported reason; provide context or fix the upstream issue; re-run" |
| 5e | Hook recorded violations | `step5e:hook_violations:<count>` | "Bug in orchestrator dispatch logic — escalate; do not bypass hook" |
| 5e-review | agy spec-compliance review found drift (v2.1 NEW) | `step5e-review:spec_drift:<module>` | "Read agy's findings; fix Codex's implementation to match the impl-plan task OR revise the impl-plan if Codex's deviation is the better approach. Re-run." |
| 6a-prime | agy architectural review failed (v2.1 NEW) | `step6a-prime:architectural_review_failed` | "Read agy's review; fix architectural issues; re-run. Operator override: `.archreview.override.md` + `[archreview-override]` commit." |
| 6 | Iterate 5-cycle cap, match < 90% | `step6:iterate_max_cycles` | "Inspect analysis gaps; revise design or implementation; re-run" |
| 6 | Tests not 100% after iterate | `step6:tests_not_green` | "Inspect failing tests; fix; re-run" |
| 7a | `/pdca report` failed | `step7:report_failed` | "Inspect bkit error; re-run" |
| 7b | `/pdca archive` failed | `step7:archive_failed:<stderr>` | "Inspect archive collision; resolve; re-run" |
| 7c | Pre-commit rejected | `step7:commit_failed:<stderr>` | "Fix pre-commit (DO NOT use --no-verify); re-run" |
| 7d | Push rejected (non-FF / auth / network) | `step7:push_failed:<stderr>` | "Resolve push issue (pull-rebase, re-auth); re-run. NEVER force-push." |

## Hook-stale-state recovery

If the orchestrator dies mid-Phase 5 without clearing `phase = "step5"`, the hook keeps blocking writes machine-wide.

1. `/h-mad status` heuristic surfaces stale flags (60min `autonomous_entry_ts` + `halt_reason = null`).
2. `/h-mad reset "<feature>"` clears all `orchestrator_state[<feature>]`. Does NOT touch git or docs.
