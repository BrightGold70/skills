## Summary

The plan covers all six functional requirements, but its collect-alone strategy diverges from the spec and its mutation deliverable contradicts the current matrix. The heading, Setext and 14-case renderer probes reproduced; the read-only filesystem policy prevented report-file and marker creation.

Evidence: 13 files opened, 6 greps run.

| Requirement | Classification |
|---|---|
| FR-1 | restated |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

## Must-fix

- **FR-1 / AC-1.8: the collect-alone pin executes tests instead of only collecting them.** The plan requires running `test_docsections.py`, while the spec explicitly limits this subprocess to collection. Under `docsections-delegation-reverted`, the delegation test would fail inside that subprocess and consequently fail the helper’s import pin too, contradicting the promised wire-only discrimination. Adopt the spec’s exact `--collect-only` invocation.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `pytest h-mad/tests/test_docsections.py -q`
  quote: docs/01-plan/features/doc-block-exec.spec.md › `The collect-alone pin is collection-only, and that is a contract rather than an`

- **The helper mutation deliverable still requires 81 rows, while its authoritative matrix requires 85.** I counted 85 matrix rows, including one registry-target row. The four additions cover intersecting substitutions, spawn-time `ValueError`, rollback identity checking and cleanup exception chaining; satisfying the plan’s stated total would omit required discrimination coverage. Reconcile the deliverable with the matrix or remove the duplicated total.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `81 mutations with a full-node-ID`
  quote: docs/02-design/features/doc-block-exec.design.md › `85 mutations (85 rows: 84 of the helper's source, 1 of`
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `25 + 6 + 26 + 28 = **85 rows**`

## Should-fix

- **The evidence register contradicts the executions recorded in this revision.** It retains the Setext differential as un-re-run even though the measurement section records its worktree reproduction and current cross-check. Conversely, the de-indentation heading claims a run by “this revision” while its closing paragraph explicitly says no revision since v1.95 re-ran it. Reconcile these statuses and regenerate the register’s membership and partition.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `- The Setext differential and its` ; `and re-derived at `1861157` from a worktree, on both readings of it.` ; `Fence-body de-indentation, the one case this revision ran` ; `since no`

- **The two closure failures are incorrectly dated relative to each other.** The plan says the `.py` closure broke before the other closure. Running both `git diff --name-only 74e126f af19d53 -- h-mad handoff` and its `-- '*.py'` counterpart returns the same assembler and test paths: both closures fail at `af19d53`. Correct the relative chronology; the separate-corpus principle remains valid.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `one commit before this section's other closure did`

## Nit

None
