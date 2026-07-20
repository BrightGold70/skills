# Failure Recovery — per-phase halt routes + recovery hints (v2.2, standalone)

**Halt + notify + leave intermediate state.** No auto-rollback.

## Common halt protocol

1. Write `orchestrator_state[<feature>]`: `halt_reason`, `halt_ts`, `phase = null` (clears hook arm), pin `current_phase` + `last_completed_phase`.
2. Emit `[H-MAD] <feature> phase<N> halted reason=<reason>`.
3. `hmad-dispatch notify "/h-mad halted" "<feature>: <reason>"`.
4. Print recovery hints.
5. Exit.

## Per-phase failure routes (v2.2)

| Phase | Failure mode | `halt_reason` | Recovery hint |
|---|---|---|---|
| 1–2 | User declines | `<phase>:user_declined` | "Edit artifact; re-run `/h-mad "<feature>"`" |
| 3 | Inline plan generation failed | `step3:plan_gen_failed` | "Inspect error; re-run Phase 3" |
| 3, 4, 5 | Cmux pane not alive | `<phase>:no_<agent>_pane` | "Launch agent per `references/agent-substrate.md` (cmux `cmux split-window --command …` OR orca `orca terminal create`); confirm `hmad-dispatch alive <agent>`; re-run" |
| 3, 4 | agy dispatch fail (cmux 400) | `<phase>:agy_dispatch_failed` | "cmux only: Restart agy pane per CLAUDE.md §F-12; re-run (orca: restart the terminal via `orca terminal create` and re-pin)" |
| 4 | Inline design generation failed | `step4:design_gen_failed` | "Inspect error; re-run Phase 4" |
| 4 | Back-propagation loop ≥ 3 times | `step4:back_prop_max` | "Manual review; revise both plan and design; re-run" |
| 5a | Impl-plan generation failed | `step5a:impl_plan_gen_failed` | "Inspect error; re-run Phase 5a" |
| 5c | Baseline branch failed | `step5c:branch_failed:<stderr>` | "Inspect git error; re-run" |
| 5d | RED tests don't all fail | `step5d:red_not_all_failing` | "Codex's tests passed without implementation — likely test bugs; review; re-run" |
| 5e | GREEN unreachable after 3 retries | `step5e:green_unreachable:<module>` | "Inspect failed module; fix Codex prompt or implement manually; re-run" |
| 5e | Codex reports BLOCKED | `step5e:codex_blocked:<reason>` | "Read Codex's reported reason; provide context or fix the upstream issue; re-run" |
| 5e | Codex reports NEEDS_CONTEXT | `step5e:codex_needs_context:<reason>` | "Read Codex's reported reason; provide context; re-run" |
| 5e | Hook recorded violations | `step5e:hook_violations:<count>` | "Bug in orchestrator dispatch logic — escalate; do not bypass hook" |
| 5e-review | agy spec-compliance review found drift | `step5e-review:spec_drift:<module>` | "Read agy's findings; fix Codex's implementation to match impl-plan task OR revise impl-plan if Codex's deviation is better; re-run" |
| 6a-prime | agy architectural review failed | `step6a-prime:architectural_review_failed` | "Read agy's review; fix architectural issues; re-run. Operator override: `.archreview.override.md` + `[archreview-override]` commit." |
| 6 | Iterate no progress (zero gaps closed) | `step6:iterate_no_progress` | "Inspect gaps; may require design revision; re-run" |
| 6 | Iterate 5-cycle cap, match < 90% | `step6:iterate_max_cycles` | "Inspect analysis gaps; revise design or implementation; re-run" |
| 6 | Tests not 100% after iterate | `step6:tests_not_green` | "Inspect failing tests; fix; re-run" |
| 7a | Telemetry record failed | `step7:telemetry_failed` | "Non-fatal — emit warning, continue to report step" |
| 7b | Report generation failed | `step7:report_failed` | "Inspect error; re-run" |
| 7c | Archive failed | `step7:archive_failed:<stderr>` | "Inspect archive collision; resolve; re-run" |
| 7d | Pre-commit rejected | `step7:commit_failed:<stderr>` | "Fix pre-commit issue; re-run" |
| 7e | Push failed | `step7:push_failed:<stderr>` | "Resolve upstream conflict; re-run" |

## Hook-stale-state recovery

If the orchestrator dies mid-Phase 5 without clearing `phase = "step5"`, the hook keeps blocking writes machine-wide.

1. `/h-mad status` heuristic surfaces stale flags (60min `autonomous_entry_ts` + `halt_reason = null`).
2. `/h-mad reset "<feature>"` clears all `orchestrator_state[<feature>]`. Does NOT touch git or docs.
