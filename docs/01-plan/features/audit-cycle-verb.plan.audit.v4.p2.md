## Summary
The plan is highly rigorous and shows outstanding compliance with the H-MAD base invariants (specifically around mutation verification and connection enforcement). The decision to reap first and use a grace period instead of a 600s timeout is a smart architectural improvement, but it restates FR-4 from the spec and must be reconciled.

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
- **Spec Reconciliation (FR-4): Restated** — The spec requires the verb to call `report_wait` first with the full timeout: *"The verb calls `h_mad_report_wait.py <report-path>` first for each pass, with a configurable `--report-timeout` (default 600s)."* The plan restates this to reap the background processes first and then wait with a short grace period: *"Reap first, then decide from the file... Empty or absent → `report_wait` with a grace timeout (`--report-grace`, default 5s), not the 600s figure."* This is a well-reasoned narrowing that prevents a 600s hang if a dispatch exits early, but the divergence must be recorded in the spec to close the loop.
- **Contradiction in CLI signature vs Implementation** — The *Implementation Strategy* states that the wait logic uses a new configurable grace period (`--report-grace`, default 5s). However, the *CLI signature* in the Scope section lists only `--report-timeout <sec>` and `--timeout <sec>`, omitting the new `--report-grace` flag. Add the flag to the CLI signature so the contract is complete.

## Should-fix
None

## Nit
None
