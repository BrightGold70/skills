## Summary

The plan covers every source-spec functional requirement as written; the reconciliation table is below.  Its coupled implementation plan is nevertheless stale against the current plan/design contract, leaving the required mutation-verification work incomplete on the executable task surface.

| FR | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

## Must-fix

- The implementation plan is stale against the plan and design's 67-row helper mutation contract — the target plan's Deliverables require `doc_block_exec.json` to contain 67 rows (65 helper-source and two registry rows), and the current design enumerates 67, but `doc-block-exec.impl-plan.md` still identifies design/plan v1.60 and specifies/runs only 63 rows.  It consequently has no task-level mutation rows for the four later guards (`heading-level-pin-ignored`, `mktemp-invocation-planted`, `allow-abbrev-restored`, and `stream-write-oserror-unwrapped`), despite claiming every design guard has one. This violates the mutation-verification invariant and leaves implementers without a complete, exact mutation plan; update the impl-plan provenance, task allocations, expected counts, and verification command to the 67-row matrix before implementation.

## Should-fix

None

## Nit

None
