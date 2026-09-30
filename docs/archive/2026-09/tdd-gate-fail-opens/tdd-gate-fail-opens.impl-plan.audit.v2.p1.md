AUDIT-tdd-gate-fail-opens-impl-plan-v2-BEGIN
## Summary
The revision addresses the prior audit, but three planned checks still leave observable contract violations untested: an invalid comparator reading, an empty patch header, and a permissive resume-option guard. The root-failure return type also needs an explicit caller branch for implementers.
Evidence: 13 files opened, 15 greps run. 🌱 graft saved ~29,778 tokens (3 calls).

## Must-fix
- T0 tests only a missing file as a comparator operational error; add a control reading with `REPRO: agent-cli-reachable=yes` and require non-zero exit with no `COMPARE:` token — the paired design declares that reading invalid, but a parser that ignores the non-key line can report PASS.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md › `A missing reading path exits non-zero and prints no `COMPARE:` token`
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `A reading is valid only when the value is `no`.`
- T4 has no acceptance case for an empty path after trimming; add a governed `*** Update File: ` case asserting `judge-error` — an implementation can drop the now-empty marker and reach the existing generic unidentified-target refusal while every listed header test passes.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md › `An empty path, or one still containing U+0000 to U+001F or U+007F, is a bad header.`
- T11 counts unknown-option refusals as regression guards without a post-registration permissive mutation; run each guard with the resume key present and the option check disabled, and verify the mutation landed — at RED the absent safe-list key already refuses both commands, so their green result does not prove option filtering.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md › `Guards: `test_codex_hook_refuses_cat_subst_oracle`, `test_codex_hook_refuses_unknown_resume_options`.`

## Should-fix
- Specify where `_main_guarded` branches on a root arm-2 `Identity` before calling `_any_phase5_status`, and which spelled `Path` it passes to the status scan — the current code immediately passes `_project_root`'s return to a Path-consuming function, while the planned return type is a union.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md › `def _project_root(payload: dict[str, Any]) -> Path | Identity: ...   # Identity only on an arm-2 root`

## Nit
None
AUDIT-tdd-gate-fail-opens-impl-plan-v2-END
