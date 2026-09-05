## Summary

Four blocking test and implementation-plan gaps remain across the five tasks. Read-only filesystem permissions prevented writing the report file or completion marker; this report is delivered through the terminal.
Evidence: 10 files opened, 7 greps run.

## Must-fix

- **The new subprocess NUL fixture cannot reach the CLI.** `test_cli_nul_composition_is_a_verdict_on_both_paths` passes an embedded NUL through an unsupported `--preamble` argument. A controlled Python 3.11 probe returned exit 0 without NUL and raised `ValueError: embedded null byte` in the parent with NUL, before launching the child. Write the NUL into a preamble file and pass its path through `--preamble-file`.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `a document whose tagged block body contains \x00` is not the document’s spelling; the exact prescribed second arm is `a ` followed by `--preamble` and `argument containing`. 
- **The cleanup mock does not discriminate the prescribed mutant.** An injected `rmtree` that unconditionally raises still raises when its caller adds `ignore_errors=True`; that option suppresses errors inside the real implementation, not outside a replacement function. The controlled probe recorded the same injected exception with either flag value. Specify a mock that honors `ignore_errors`, then require the named test to fail under the mutant; otherwise the claimed mutation kill violates Test discrimination.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `test_cleanup_failure_carries_the_os_error` (in-process, injected: `rmtree` injected to raise;
  quote: docs/02-design/features/doc-block-exec.design.md › `** `cleanup-errors-ignored` (restore `ignore_errors=True`) is killed by`
- **Task 4’s RED split contradicts its modification of an existing test.** Task 1 explicitly schedules the CLI half of `test_invalid_utf8_document_is_unreadable` for Task 4. Adding that assertion makes an existing passing test fail before the CLI lands, so Task 3’s passing total cannot remain the expected passing total. Separate the CLI assertion into a new test or account for the moved test in both RED counts.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `the CLI half is added in Task 4` ; `none of which this task touches. **Expected passing is not 0**;`
- **The new detail-line dispatch guard has no planned discrimination run.** Predicate-removal mutants test whether overlap detection happens; they do not test whether the renderer selects the correct prefix from `kind`. The plan explicitly defers that mutation despite requiring the new rendering assertion. Add a mutation that changes only kind-based rendering and observe the named CLI test failing. Deferring this to whether another round wants it violates Test discrimination.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `this test's own kind-selection arm is a rendering claim the design's matrix does not carry a row for; a row for it is a DESIGN change and is owed to the design if the round wants one.`

## Should-fix

- **Specify the complete mixed-kind output of the second overlap fixture.** On `abc` with keys `a`, `ab`, and `abc`, the prescribed predicates produce three substring records **and three intersection records**, all intersection offsets being 0. The current expectation names only three overlap lines, leaving whether additional lines are required unclear. Assert all six records, or use a separate document without matching spans for the substring-only arm.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `Two invocations of the same CLI on the same document.` ; `followed by exactly three `overlap:` lines`
- **The five-row collateral-failure enumeration is incomplete.** Task 2 explicitly records that deleting the intersection predicate also fails the overlapping-occurrence test. Thus `intersect-check-removed` is another member of the claimed exhaustive population. Re-derive the enumeration, including the newly added CLI regression tests.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `the only rows in **`doc_block_exec.json`** whose mutant reds a second named test;` ; `also reds, so the two are not independent from that side`
- **Specify the minimum offset across all intersecting occurrences.** The implementation plan defines the shared index of two spans but does not clearly select among several intersecting span pairs for the same keys. For `ab`/`bc` in `abc---abc`, require offset 1 rather than 7, and add that repeated-occurrence fixture.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `index the two spans SHARE**, 0-based into `block.text``
  quote: docs/01-plan/features/doc-block-exec.spec.md › `**The minimum is taken over span pairs, not over one pair, because`

## Nit

None
