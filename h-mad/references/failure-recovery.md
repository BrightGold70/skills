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
| 5d | No `STATUS:` line extractable from the codex scrape | `step5d:no_verdict:<module>` | "The agent dispatched and produced no verdict. Re-read with `--from-start` (a bigger tail can still be an overdrawn frame region — J3); if still absent, `hmad-dispatch clear codex` and re-dispatch. Never proceed on silence — an absent verdict is not a pass." |
| 5b | `h_mad_wire_pin_gate.py` returned `WIREPIN: FAIL` | `step5b:wire_pin_missing:<task>` | "A `wiring`-shaped task names no `WIRE`/`WIRE-PIN`, or left the template placeholder in. Return to 5a and name the connection plus the test that fails when that connection alone is removed. Do not proceed on the reasoning that 5d/5e will catch it — both are scoped to the callee and neither can (`invariants.base.md` §\"Connection enforcement\")." |
| 5b | `h_mad_wire_pin_gate.py` returned `WIREPIN: UNSHAPED` (exit 2) | `step5b:impl_plan_unshaped` | "No task declares a `**Task shape**`, so a wiring task in this plan is indistinguishable from new behaviour and the gate refuses to score it — cannot-judge must not read as nothing-to-fix. Regenerate the impl-plan against the current template (`references/inline-protocols.md` §Phase 5a). An unedited `new-behaviour \| refactor \| wiring` alternation also counts as undeclared." |
| 5d | `wiring` task dispatched with no `WIRE-PIN` | `step5d:no_wire_pin:<module>` | "The task ships a connection and named no test that fails when the connection alone is removed. Do not proceed to 5e — a whole-module revert cannot establish a wire, so GREEN would certify nothing about it. Return to 5a, add `WIRE` + `WIRE-PIN` to the task, re-audit at 5b." |
| 5d | `WIRE-PIN` test's RED is a missing symbol, not caller behaviour | `step5d:red_wrong_reason:<module>` | "An `ImportError`/`AttributeError`/`NameError` RED means the pin tests the callee, so it goes green the moment the callee exists — wired or not. Re-dispatch the pin as an assertion on the caller's observable behaviour (the call was not made; the value did not propagate). Counts cannot catch this; only the failure mode can." |
| 5e | Wire-scoped revert left the module suite green | `step5e:wire_unenforced:<module>` | "The connection is unenforced and every other Phase-5 gate is blind to it (`invariants.base.md` §\"Connection enforcement\"). Confirm the revert actually landed first — `git stash push -- <paths>` stashes nothing and exits 0 on an untracked path, so a revert that never happened reports as a pass. If it landed and nothing failed, write the discriminating test before accepting the wire; do not weaken the pin. Also mutate the other direction (force the connection to fire unconditionally) — a wire that is present but unconditional passes the first direction." |
| 5e | GREEN unreachable after 3 retries | `step5e:green_unreachable:<module>` | "Inspect failed module; fix Codex prompt or implement manually; re-run" |
| 5e | Codex reports BLOCKED | `step5e:codex_blocked:<reason>` | "Read Codex's reported reason; provide context or fix the upstream issue; re-run" |
| 5e | Codex reports NEEDS_CONTEXT | `step5e:codex_needs_context:<reason>` | "Read Codex's reported reason; provide context; re-run" |
| 5e | Hook recorded violations | `step5e:hook_violations:<count>` | "Bug in orchestrator dispatch logic — escalate; do not bypass hook" |
| 5e-review | agy spec-compliance review found drift | `step5e-review:spec_drift:<module>` | "Read agy's findings; fix Codex's implementation to match impl-plan task OR revise impl-plan if Codex's deviation is better; re-run" |
| 5e / 5e-review | No `STATUS:`/`VERDICT:` line extractable | `step5e:no_verdict:<module>` | "The halt condition is `VERDICT: DRIFT`, so a scrape with no verdict at all would grep clean and commit the module on silence. Re-read with `--from-start` (a bigger tail can still be an overdrawn frame region — J3); if still absent, `hmad-dispatch clear agy` and re-dispatch. Do not commit the module until a verdict is extracted." |
| 3, 4, 5b, 6a-prime | `exec agy` returned a short last message with no `<AUDIT_SENTINEL>` pair (`h_mad_extract_report.py` exit 2) | `<phase>:no_verdict` | "`agy --print` surfaces only the **last** message, so the report has one fragile channel (measured: 358 B of narration naming real Must-fix items, no sentinel — either a summarizing turn replaced the report or it was never emitted, i.e. **F-10 claim-execution divergence** per `AGENTS.md`; the remedy is the same either way). Do **not** apply the `exec` missing-report recovery — that is codex-scoped; an audit leaves no tree delta, and for agy `--log` is byte-identical to `--out`, so re-reading it recovers nothing. Re-read with `--from-start`, then `hmad-dispatch clear agy` and re-dispatch **with the report-file slot filled** + `report-wait "$RP"` (a file survives a later turn; last-message does not). Audits are idempotent — re-dispatch is safe. Never score the narration." |
| 6a-prime | No reviewer pane resolves (`agy -> UNRESOLVED`) | `step6a-prime:no_reviewer_pane` | "Launch a reviewer pane (`references/agent-substrate.md` §Launching the panes) or pin `HMAD_ORCA_AGY_TERMINAL`/`HMAD_CMUX_AGY_SURFACE`, then re-run. If proceeding without one is a deliberate call, record `archreview: \"SKIPPED_NO_PANE\"` in state and carry it into the Phase 7 report — never as `READY_TO_MERGE`. This is the only pass that catches design-level drift; skipping it silently is how a feature closes looking reviewed." |
| 6a-prime | agy architectural review failed | `step6a-prime:architectural_review_failed` | "Read agy's review; fix architectural issues; re-run. Operator override: `.archreview.override.md` + `[archreview-override]` commit." |
| 6a-prime | No `ASSESSMENT:` line extractable | `step6a-prime:no_verdict` | "An empty architectural review is not `READY_TO_MERGE`. Re-read with `--from-start` (a bigger tail can still be an overdrawn frame region — J3); if still absent, `hmad-dispatch clear agy` and re-dispatch." |
| 6 | Iterate no progress (zero gaps closed) | `step6:iterate_no_progress` | "Inspect gaps; may require design revision; re-run" |
| 6 | Iterate 5-cycle cap, match < 90% | `step6:iterate_max_cycles` | "Inspect analysis gaps; revise design or implementation; re-run" |
| 6 | Tests not 100% after iterate | `step6:tests_not_green` | "Inspect failing tests; fix; re-run" |
| 7 | Phase 7 preconditions not met | `step7:verification_not_run` | "Phase 7 merges; Phase 6 verifies. Run `h_mad_phase7_preconditions.py` and clear each blocker: complete Phase 6, produce a gap analysis stating a match rate at or above threshold, resolve any open halt, and address a failing 6a-prime. A feature once reached main and origin with no Phase 6 at all — the suite was green and said nothing about spec conformance; the analysis run afterwards measured 0%." |
| 7a | Telemetry record failed | `step7:telemetry_failed` | "Non-fatal — emit warning, continue to report step" |
| 7b | Report generation failed | `step7:report_failed` | "Inspect error; re-run" |
| 7c | Archive failed | `step7:archive_failed:<stderr>` | "Inspect archive collision; resolve; re-run" |
| 7d | Pre-commit rejected | `step7:commit_failed:<stderr>` | "Fix pre-commit issue; re-run" |
| 7e | Push failed | `step7:push_failed:<stderr>` | "Resolve upstream conflict; re-run" |

## Hook-stale-state recovery

If the orchestrator dies mid-Phase 5 without clearing `phase = "step5"`, the hook keeps blocking writes machine-wide.

1. `/h-mad status` heuristic surfaces stale flags (60min `autonomous_entry_ts` + `halt_reason = null`).
2. `/h-mad reset "<feature>"` clears all `orchestrator_state[<feature>]`. Does NOT touch git or docs.
