## Summary
Task 8 leaves a plan path absent at the base commit as an open 5d decision: the counted contract is Option A (exit 1 with no token, 8 refusal nodes, mutation total 88) and the same paragraph recommends Option B (a ninth `plan-absent-at-base` refusal, total 89). Design v1.4 already records Option A as a closed residual, and the cited signal-discipline rule permits a non-zero exit for missing input, so the recommendation does not close the fork. The parser, doc/data definition, listing matcher, three host gates, and prose pins otherwise match the tree and the design. Evidence: 40 files opened, 49 greps run.

## Must-fix
- Task 8 tells the 5d worker to resolve, during implementation, whether a plan path absent at the base commit exits 1 with no token or becomes a ninth `FR9-DRIVE: UNREADABLE plan-absent-at-base` row with marker `# M:D-PLAN-ABSENT`. The plan counts Option A (8 nodes in `test_fr9_driver_refuses`, mutation total 88) and recommends Option B (9 and 89). Design v1.4 already closed that case as exit 1 with no token. The recommendation cites Audit-gate signal discipline as preferring a token; that rule permits a non-zero exit for missing or unreadable input, so it does not select Option B. The driver, the refusal test, and `fr9_drive_refusals.json` differ between the two options.
  class: build
  quote: docs/01-plan/features/gate-non-py-production-files.impl-plan.md › `OPEN-DECISION: a plan path absent at the base commit crashes the driver with no token — resolve in 5d.`
  quote: docs/02-design/features/gate-non-py-production-files.design.md › `the plan path absent at the base commit, exits 1 with no token and reads as no verdict.`
  quote: h-mad/invariants.base.md › `exit is permitted ONLY for genuine operational errors (missing/unreadable input).`

## Should-fix
- Task 3's `_match_plans` sketch places the `L-ABSENT` append only inside a comment, followed by `...`. The mutation find is that append text, and it already occurs inside the comment. A literal copy of the block makes the harness edit the comment, so `test_listing_absent_plan_is_not_listed` does not kill `L-ABSENT`. A real statement carrying the same text beside the comment matches twice and is refused.
  class: build
  quote: docs/01-plan/features/gate-non-py-production-files.impl-plan.md › `# FileNotFoundError: result.append(PlanMatch(plan, "absent", "", ()))  # M:L-ABSENT`
- Task 6's NFR paragraph defines its three prototype cases as 2 extra launches, 0 extra, and 0 extra, then reports the series 2, 4 and 2 for those cases. That series matches neither those extras nor the totals in that case order (4, then 2, then 2). The same task's `test_claude_process_count[unlisted-with-state]` already expects 4 launches, and the two control parameters expect 2, so correcting the sentence leaves the tests as written.
  class: measurement
  quote: docs/01-plan/features/gate-non-py-production-files.impl-plan.md › `2, 4 and 2 launches for those three cases.`

## Nit
- Task 7 says the deliverable is literal text, but the `helper-scripts.md` edit only says the judge-verb sentence gains `listing` and the three `TDD-LISTING:` values. `test_helper_scripts_registers_the_judge` pins those tokens, so the replacement sentence itself is unspecified.
