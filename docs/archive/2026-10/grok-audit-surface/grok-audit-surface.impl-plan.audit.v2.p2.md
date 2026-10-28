AUDIT-grok-audit-surface-impl-plan-v2-BEGIN
## Summary

The tables reconcile to 169 planned mutation rows and 115 marker sites. Gaps remain in refusal types, in-process crash visibility, and reproducible behavioral evidence; repository files were left unchanged.
Evidence: 15 files opened, 9 greps run.

## Must-fix

- Align the refusal class sketches with the required common base — Tasks 3 and 5 inherit directly from `Exception`, contradicting the shared `ProbeRefusal` hierarchy. Following those sketches makes expected refusals take the unexpected-exception traceback path. Change their bases and explicitly test traceback absence for a non-UsageError refusal.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `class Refusal(Exception):`; `class ResetArgsConflict(Exception): ...`; `class RootResetMismatch(Exception): ...`

- Extend traceback forwarding to in-process `main(argv)` assertions — the rule requires forwarding only for subprocess assertions, while monkeypatched tests consume captured stderr before asserting. An unexpected exception can therefore change the token and kill a mutant while disappearing from the zero-crash measurement. A controlled pair with the actual `crash_kill` returned `None` when the captured traceback was omitted and `KeyError` when forwarded. Require captured stderr in these assertion messages too, retaining the stated intentional-exception exceptions.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `Every subprocess assertion passes the child's stderr`; `A test that replaces a function calls`

- Supply runnable commands beside the new behavioral readings — Task 2 records argparse exit-site measurements under two interpreters, and Task 5 records no-follow and parent-link behavior, without their reproduction commands. This violates “Behavioural premises carry their command”; append the exact commands and observed outputs so later reviewers can reproduce these load-bearing premises.
  class: measurement
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › ``4 `.exit(` sites in the module source on each interpreter``; `Measured on this Mac: that open of a link fails with`

## Should-fix

- Specify a failing pin for Task 16's runtime-reference edit — its named tests and assertions cover SKILL.md and the measurement document, but do not require the AC-1.5/AC-1.8 sentence in the runtime reference or preservation of the host-mapping sentence. Add explicit assertions and negative observations for these properties.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `compatibility" gains the AC-1.5 sentence (scored outcome) or the AC-1.8 sentence (smoke failure);`

- Add negative fixtures for the ROOT and Effort parsers — the task lists name their positive renderer fixtures, but no malformed ROOT token or malformed/missing Effort-block fixture. A root record containing no ROOT line tests line discovery, and an unrecognised Effort item tests item classification; neither establishes rejection by the respective parser.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `test_root_line_parser_reads_build_root_output`; `test_effort_parser_reads_effort_items_output`

## Nit

None

🌱 graft saved ~351,491 tokens this turn, 8 calls; reported prices total $0.15 plus <$0.01.
AUDIT-grok-audit-surface-impl-plan-v2-END
