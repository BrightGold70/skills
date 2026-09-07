## Summary

The design covers every spec acceptance criterion as written; the reconciliation is below. It nevertheless has three blocking implementation/invariant gaps: its non-success CLI exits violate the base gate contract, its stated timeout-cleanup precedence cannot execute with the described exception flow, and its in-suite full-suite pass-count check has no non-recursive execution design.

| AC | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-1.4 | implemented-as-written |
| AC-1.5 | implemented-as-written |
| AC-1.6 | implemented-as-written |
| AC-1.7 | implemented-as-written |
| AC-1.8 | implemented-as-written |
| AC-1.9 | implemented-as-written |
| AC-2.1 | implemented-as-written |
| AC-2.2 | implemented-as-written |
| AC-2.3 | implemented-as-written |
| AC-2.4 | implemented-as-written |
| AC-2.5 | implemented-as-written |
| AC-2.6 | implemented-as-written |
| AC-2.7 | implemented-as-written |
| AC-3.1 | implemented-as-written |
| AC-3.2 | implemented-as-written |
| AC-3.3 | implemented-as-written |
| AC-3.4 | implemented-as-written |
| AC-3.5 | implemented-as-written |
| AC-3.6 | implemented-as-written |
| AC-3.7 | implemented-as-written |
| AC-3.8 | implemented-as-written |
| AC-3.9 | implemented-as-written |
| AC-3.10 | implemented-as-written |
| AC-3.11 | implemented-as-written |
| AC-3.12 | implemented-as-written |
| AC-3.13 | implemented-as-written |
| AC-3.14 | implemented-as-written |
| AC-4.1 | implemented-as-written |
| AC-4.2 | implemented-as-written |
| AC-4.3 | implemented-as-written |
| AC-4.4 | implemented-as-written |
| AC-4.5 | implemented-as-written |
| AC-5.1 | implemented-as-written |
| AC-5.2 | implemented-as-written |
| AC-5.3 | implemented-as-written |
| AC-5.4 | implemented-as-written |
| AC-5.5 | implemented-as-written |
| AC-5.6 | implemented-as-written |
| AC-6.1 | implemented-as-written |
| AC-6.2 | implemented-as-written |
| AC-6.3 | implemented-as-written |
| AC-6.4 | implemented-as-written |
| AC-6.5 | implemented-as-written |
| AC-6.6 | implemented-as-written |

## Must-fix

- The proposed CLI returns exit 2 for normal, tokenized refusals such as `NOT_FOUND`, `AMBIGUOUS`, `BAD_INDEX`, `BAD_TIMEOUT`, `SUBST_MISSING`, and `BAD_INFO` — the base Audit-gate signal discipline requires an explicit stdout verdict with exit 0 for normal PASS/FAIL-style outcomes, reserving non-zero exits for genuine operational errors. The design, plan, and source spec all instead make the verdict table's cannot-judge rows exit 2. Reconcile the contract before implementation: give all normal logical verdicts exit 0 and reserve a non-zero exit for actual I/O/launch faults, or explicitly change/reclassify the feature so it is not an orchestrator-consumed gate; update the spec/table/tests together.
- `CLEANUP_FAILED` cannot outrank `TIMEOUT` using the described control flow — `run_block` raises `BlockTimeout` from the timeout handler, then relies on a read-back “after the try” to raise `CleanupFailed`. Python runs the `finally` but propagates the pending exception immediately, skipping statements after the try; therefore a timeout plus silent retained cwd yields `TIMEOUT`, not the required cleanup precedence. Specify a pending-outcome/state-capture flow that always runs cleanup and read-back before selecting and raising the final error, and add the combined timeout-plus-cleanup-failure test that proves the stated precedence.
- `test_suite_floor_holds` is required to assert the full-suite *pass* count but is itself part of that full suite, with no execution topology stated — a test that launches `pytest -q` to obtain that count recursively launches itself indefinitely (while `--collect-only` alone cannot establish passed count). Define an external verification command/artifact, or an explicit re-entrancy guard plus exclusion/accounting that preserves the stated floor, and test that mechanism; otherwise AC-6.4 is not executable as planned.

## Should-fix

- The fixed tuple of “named node IDs added to existing files” used by AC-6.4 is never enumerated in either document — make the tuple's exact node IDs and owning files explicit so the count floor is reviewable and cannot silently omit one of the wire/delegation tests.

## Nit

None

