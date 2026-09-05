## Summary

The plan still contains incompatible acceptance criteria, exception contracts, and RED instructions, plus a migration step that silently removes duplicate-fence protection. Read-only filesystem restrictions prevented writing the requested report and `.done` artifacts; this report is delivered here instead.

Evidence: 9 files opened, 4 greps run.

## Must-fix

- **Cleanup test rejects the prescribed implementation.** Python 3.11 probes confirm that explicit `raise err from cleanup_error` sets `__suppress_context__` to `True`, while preserving the correct cause. AC-3.14 demands `False`, so the specified implementation cannot pass. Assert cause identity and expect explicit-chaining semantics.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `and `__suppress_context__` is False.`

- **`LaunchFailed` excludes its newly required error type.** Task 3 passes the NUL-triggered `ValueError`, but Task 1’s expressly exhaustive annotation accepts only `OSError` and `TimeoutExpired`. Widen the authoritative constructor contract and its explanatory comment.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `def __init__(self, stage: str, err: OSError | subprocess.TimeoutExpired,`

- **The overlap exception has incompatible representations across tasks and design.** Task 1 defines pairs of strings; Task 2 adds a separate intersections argument; the design requires tagged records in one argument. Choose one representation and propagate its constructor, attributes, raise sites, and renderer consistently.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `def __init__(self, pairs: list[tuple[str, str]]): ...`
  quote: docs/01-plan/features/doc-block-exec.design.md › `` `pairs` carries both kinds, each tagged with the kind that raised it ``

- **Task 2 requires output from a renderer that lands in Task 4.** Its intersection test calls the exception-raising `substitute` API but must assert an emitted CLI detail line. Keep exception-data assertions in Task 2 and prescribe the real CLI assertion in Task 4; otherwise Task 2 cannot meet its own GREEN boundary.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `**The emitted detail line is asserted verbatim**`

- **Task 5’s separately committed scaffold silently accepts duplicate gating fences.** The shipped consumer asserts exactly one match; the scaffold takes `_gating[0]`. A controlled zero/one/two-match probe produces `IndexError`/first/first, so duplicates are accepted, not refused. Preserve the guard in the scaffold and corresponding mutation payload; literal symmetry does not justify this guard narrowing.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `and Task 5 GREEN a missing or duplicated gating fence therefore raises `IndexError` on `_gating[0]``

- **The prescribed RED outcome contradicts the consuming implementer prompt.** Task 2 explicitly requires missing-function `AttributeError` failures, while the shipped prompt rejects those as RED evidence for behavioural tests. Reconcile the workflow before dispatch; the implementer cannot obey both contracts.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `**ten** tests this task adds, all with `AttributeError``
  quote: h-mad/references/codex-implementer-prompt.md › `(An `ImportError`/`AttributeError` standing in for a behavioural assertion is not a RED — it is an unwritten test.)`

## Should-fix

- **Add subprocess coverage for both NUL composition paths.** The new tests exercise only `run_block`; the CLI launch tests use an empty `PATH`. Those tests do not establish that a NUL-bearing document or preamble produces the promised quoted diagnostic and process exit without a traceback.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `**Acceptance Criteria** (every test here calls `dbe.run_block` in-process at the API — none goes`

- **Task 2 still publishes conflicting RED counts.** Its acceptance list and `--expect-fail` require ten, while the gate paragraph says nine. Remove the stale count so dispatch instructions have one expected result.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `the nine new tests fail with `AttributeError``

## Nit

None
