## Summary
Axis C Spec Reconciliation results: 47 ACs are implemented as written, 2 ACs are restated (AC-3.14, AC-6.4), and 0 ACs are absent. The design is highly detailed and robust, successfully addressing the feature's requirements while satisfying the mutation verification and time-bounding invariants. A minor contradiction in the Invariant Compliance prose and the two spec restatements need to be resolved.

| Identifier | Classification |
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
| AC-2.8 | implemented-as-written |
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
| AC-3.14 | restated |
| AC-4.1 | implemented-as-written |
| AC-4.2 | implemented-as-written |
| AC-4.3 | implemented-as-written |
| AC-4.4 | implemented-as-written |
| AC-4.5 | implemented-as-written |
| AC-4.6 | implemented-as-written |
| AC-5.1 | implemented-as-written |
| AC-5.2 | implemented-as-written |
| AC-5.3 | implemented-as-written |
| AC-5.4 | implemented-as-written |
| AC-5.5 | implemented-as-written |
| AC-5.6 | implemented-as-written |
| AC-6.1 | implemented-as-written |
| AC-6.2 | implemented-as-written |
| AC-6.3 | implemented-as-written |
| AC-6.4 | restated |
| AC-6.5 | implemented-as-written |
| AC-6.6 | implemented-as-written |

## Must-fix
- Axis A Contradiction — The `Detailed Design` verdict table correctly assigns `exit 2` to `LAUNCH_FAILED`. However, the `Invariant Compliance` section under `Audit-gate signal discipline` states: "exit 2 only for genuine operational errors — `UNREADABLE` ... and `CLEANUP_FAILED`", explicitly omitting `LAUNCH_FAILED` from the prose. Update the prose to align with the table and the spec.
- AC-3.14 (restated) — Spec says: "`__cause__` is the pending `BlockTimeout` when the run had also timed out, else `cleanup_error`". Design says: "`__cause__` is the pending outcome when there was one (the `BlockTimeout`, or a `LaunchFailed`), else `cleanup_error`". The design is wider (adds `LaunchFailed` to the `__cause__` chain if cleanup fails after a launch failure). This is a well-reasoned refinement, but must land in the spec.
- AC-6.4 (restated) — Spec says: "...plus a fixed tuple of the named new node IDs added to existing files (`test_h_mad_collect_report_docs.py`, `test_docsections.py`), each of which the test asserts exists." Design says: "...the five being the named node IDs added to `test_h_mad_collect_report_docs.py`... each asserted present". The design dropped `test_docsections.py` from the tuple of existing files receiving new node IDs (as the delegation tests are placed in the new module). The spec must reflect this narrower scope.

## Should-fix
None

## Nit
None
