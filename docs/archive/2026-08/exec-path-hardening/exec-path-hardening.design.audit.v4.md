## Summary
The design delivers a robust, well-probed architecture that effectively neutralizes the severe shared-offset and data-clobber hazards identified in earlier cycles, utilizing a read-then-compose approach and explicit stdin redirect guards. However, reusing the heartbeat-equipped `_exec_run` for the stamp's own bounded `orca` calls introduces a fatal infinite recursion hazard if the heartbeat interval is short. Furthermore, the design drops the Plan's mandated `WIRE-PIN` connection enforcement tests, violating Axis B, and fails to map three AC identifiers from the spec.

| Spec ID | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-1.4 | implemented-as-written |
| AC-1.5 | implemented-as-written |
| AC-2.1 | implemented-as-written |
| AC-2.2 | implemented-as-written |
| AC-2.3 | implemented-as-written |
| AC-2.4 | implemented-as-written |
| AC-2.5 | implemented-as-written |
| AC-3.1 | implemented-as-written |
| AC-3.2 | implemented-as-written |
| AC-3.3 | absent |
| AC-4.1 | implemented-as-written |
| AC-4.2 | implemented-as-written |
| AC-4.3 | implemented-as-written |
| AC-4.4 | absent |
| AC-5.1 | implemented-as-written |
| AC-5.2 | implemented-as-written |
| AC-5.3 | implemented-as-written |
| AC-5.4 | absent |
| AC-6.1 | implemented-as-written |
| AC-6.2 | implemented-as-written |
| AC-6.3 | implemented-as-written |

## Must-fix
- **Axis A (Gaps) / Infinite Recursion Hazard**: The design proposes reusing `_exec_run` for both the main agent dispatch and the bounded `orca` calls made *by* the stamp emitter. Because `_exec_run` contains the heartbeat hook (`_exec_stamp beat`), a nested `_exec_run` call inherits the heartbeat logic. If a test or user sets `HMAD_EXEC_HEARTBEAT_SEC` to a value smaller than `$stamp_timeout` (e.g., 1s), the inner `_exec_run` executing an `orca` call will trigger its own heartbeat, calling `_exec_stamp beat` again, leading to infinite recursion (`_exec_stamp` -> `_exec_run` -> `_exec_stamp`). The design must explicitly disable heartbeats for the inner calls (e.g., via `local HMAD_EXEC_HEARTBEAT_SEC=0` inside `_exec_stamp`).
- **Axis B (Connection Enforcement) / Cross-doc drift**: The Plan explicitly mandated that `W1–W5` must be tested using wire-scoped reverts (testing the removal of the call site while leaving the callee intact) with specific `WIRE-PIN` assertions about caller-observable behavior. The Design's Test Plan completely omits these `WIRE-PIN` tests and the wire-scoped revert methodology, relying only on content mutation. This violates the Axis B Connection Enforcement invariant and silently drops a stated requirement from the Plan.
- **Axis C (Spec Reconciliation)**: `AC-3.3` is absent by identifier. While the design functionally tests this via "all surfaces stubbed failing", the identifier `AC-3.3` must be explicitly mapped in the test plan to satisfy the spec reconciliation requirement.
- **Axis C (Spec Reconciliation)**: `AC-4.4` is absent by identifier. The design covers mutation verification, but the identifier `AC-4.4` must be explicitly mapped in the test plan.
- **Axis C (Spec Reconciliation)**: `AC-5.4` is absent by identifier. The design states the documentation updates, but the identifier `AC-5.4` must be explicitly mapped to the corresponding deliverables.

## Should-fix
None

## Nit
None
