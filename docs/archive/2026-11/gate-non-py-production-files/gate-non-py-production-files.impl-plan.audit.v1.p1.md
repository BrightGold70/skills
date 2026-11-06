## Summary

The eight-task plan largely follows the paired design, but its helper-test contract, deferred driver decision, and prototype evidence need correction before implementation. This was a read-only source audit; the planned tests and removed prototype were not executed.
Evidence: 36 files opened, 14 greps run.

## Must-fix

- Task 4's helper test cannot reject an always-skipping implementation — an uncaught `pytest.skip.Exception` marks the entire node skipped before the return assertion or second arm runs. The installed pytest implementation confirms this outcome. This violates Test discrimination and can silently remove the case-fold coverage. Specify a positive arm that converts an unexpected skip into failure, a negative arm expecting skip, and an always-skip mutation that demonstrably fails.
  class: build
  quote: docs/01-plan/features/gate-non-py-production-files.impl-plan.md › `A helper that always skips fails the first arm on this Mac.`

- Task 8 leaves its missing-base-plan behavior to the implementer — option A and option B produce different driver code, refusal tests, mutation rows, and acceptance counts. Budgeting A while recommending B does not settle the explicitly deferred choice. Select either contract before dispatch and align the task and ledger with it.
  class: build
  quote: docs/01-plan/features/gate-non-py-production-files.impl-plan.md › `OPEN-DECISION: a plan path absent at the base commit crashes the driver with no token — resolve in 5d.`

- The regression-prototype reading lacks its reproducible command and corpus selector — the plan reports results for 34 existing test files, but supplies neither their exact selection command nor the invocation and scratch-tree preparation that produced that result. The future per-task commands are different populations. This breaches Behavioural premises carry their command; provide the exact recipe and observed output, or withdraw the reading as unverified.
  class: measurement
  quote: docs/01-plan/features/gate-non-py-production-files.impl-plan.md › `the 34 test files that name an edited module read 9 failures`

## Should-fix

- Task 6 reverses the first two process-count labels — its preceding cases are unlisted code-like with state, doc/data, then unlisted without state, so the stated implementation and named test expectations imply 4, 2, 2 total launches in that order. Label each observation explicitly or reorder the published tuple; the planned test assertions already use the correct mapping.
  class: measurement
  quote: docs/01-plan/features/gate-non-py-production-files.impl-plan.md › ``Prototype reading through a logging `python3` shim: 2, 4 and 2 launches for those three cases.``

## Nit

None

