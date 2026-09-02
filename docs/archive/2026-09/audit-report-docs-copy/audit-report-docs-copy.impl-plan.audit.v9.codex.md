## Summary
The implementation plan is mostly concrete and consistent with the paired design, with exact file paths, task ordering, wiring pins, and executable ACs for the collector/CLI/gate/doc/mutation surfaces. I found one blocking contradiction in Task 6 where the spec shape is still described as 22 names while the rest of the task requires 23, plus one stale cross-document source pointer.

## Must-fix
- `docs/01-plan/features/audit-report-docs-copy.impl-plan.md:294` still says the mutation spec shape is “exactly the 22 names” while the Task 6 opening, table, AC-6.3, AC-6.3a, implementation order, and version history all require 23 mutations — this is a hard contradiction in the spec-shape requirement and can make `test_mutation_spec_shape` assert the wrong cardinality or drop the restored e′ mutant, weakening the Mutation verification/Test discrimination invariant.

## Should-fix
- `docs/01-plan/features/audit-report-docs-copy.impl-plan.md:3` says the impl-plan tracks the design newest entry “currently v1.15”, but the paired design’s newest entries are v1.16 and v1.17 and those entries are load-bearing for e′ restoration and the argparse `SystemExit` handler — the plan content appears updated, but the stale provenance line undermines cross-document consistency.

## Nit
None
