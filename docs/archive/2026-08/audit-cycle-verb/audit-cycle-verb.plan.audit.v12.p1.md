AUDIT-audit-cycle-verb-plan-v12-BEGIN
## Summary
The Plan correctly outlines the orchestration of the `audit-cycle` verb and addresses the functional requirements, including rigorous connection testing. However, it contradicts the Spec by dropping the `.done` marker requirement for report collection, omits the required write verification for collected reports, and contains an internal contradiction regarding the required number of connection mutation tests.

| Requirement | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | restated |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |
| FR-7 | implemented-as-written |
| FR-8 | implemented-as-written |
| FR-9 | implemented-as-written |
| FR-10 | implemented-as-written |

## Must-fix
- **FR-4 restated (fast-path collection drops `.done` marker)** — Spec AC-4.1 states: "non-empty **and** `<report-path>.done` exists → `delivered=report-file`, **no wait at all**". The Plan (`Concurrency, and the reap/collect ordering` step 2) states: "For each pass, test the report path directly. Non-empty → `delivered=report-file`, no wait at all." The Plan is narrower because it drops the `.done` marker check from the direct test, which will cause the cycle to accept a torn write mid-flush.
- **FR-4 absent (extracted report write verification)** — Spec AC-4.4 states: "The write is verified by re-reading (exists and non-empty) before the pass is recorded as delivered." The Plan is absent on this requirement; it outlines the collection fallback but does not mandate verifying the final file write. This also violates the Axis B *Mutation verification* invariant, as the report write is a state mutation that must be proven by re-reading rather than assumed from a zero exit.
- **Contradiction (5 vs 6 composed call sites)** — The Plan's `Success Criteria` requires that "Each of the five composed call sites has a test". The `Implementation Strategy` intro similarly states "What it ships is five call sites". However, the connection mutation table lists **six** call sites (adding `verb → h_mad_audit_cycle.py`). The success criteria must be updated to 6, otherwise a test run could satisfy the criteria while leaving the load-bearing shell→helper boundary unverified.

## Should-fix
None

## Nit
None
AUDIT-audit-cycle-verb-plan-v12-END
