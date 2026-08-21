## Summary
The plan correctly maps all Functional Requirements to unify the audit cycle and rigorously enforces the H-MAD base invariants (including explicit connection enforcement and state-mutation verification). However, the plan's proposed collection logic introduces a "reap-first" optimization that diverges from the spec's mandated use of `--report-timeout`, requiring a spec reconciliation.

Axis C Spec Reconciliation:
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
- FR-4 (Report collection) is restated — The spec (AC-4.1) dictates: "The verb calls h_mad_report_wait.py <report-path> first for each pass, with a configurable --report-timeout (default 600s)." The plan states: "Empty or absent → `report_wait` with a **grace** timeout (`--report-grace`, default 5s), not the 600s figure." While the plan's reap-first design correctly prevents the collector from hanging on a dead process, it formally contradicts the spec's 600s timeout parameter. This divergence must be reconciled into the spec before proceeding.

## Should-fix
None

## Nit
None
