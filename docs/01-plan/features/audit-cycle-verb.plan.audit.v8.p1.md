## Summary
The plan is well-reasoned and thoroughly documented, with commendable probes validating its load-bearing assumptions (the `exec agy` overwrite guard and the concatenation under-count). However, it contains gaps in the connection mutation tests: the test for dropping `h_mad_report_wait.py` will spuriously pass unless the test explicitly delays file delivery, and the mutation tests for `h_mad_audit_gate.py` are structurally identical, missing the required "force it to fire unconditionally" direction.

**Spec Reconciliation (Axis C):**

| Requirement | Classification | Note |
|---|---|---|
| FR-1: One verb, one cycle | `implemented-as-written` | Addressed in section "Implementation Strategy" and Deliverables. |
| FR-2: Assembly is gated, and its size signal is relayed | `implemented-as-written` | Addressed in section "Implementation Strategy". |
| FR-3: Two independent passes, isolated per-pass channels | `implemented-as-written` | Addressed in section "Architecture Considerations". |
| FR-4: Report collection tries report-file, falls back to `--out` | `implemented-as-written` | Addressed in section "Architecture Considerations". |
| FR-5: Union gating by per-pass gate runs, never by concatenation | `implemented-as-written` | Addressed in section "Architecture Considerations". |
| FR-6: Cannot-judge is a distinct verdict carrying no counts | `implemented-as-written` | Addressed in section "Architecture Considerations". |
| FR-7: Premise-check checklist | `implemented-as-written` | Addressed via the Python helper in "Implementation Strategy". |
| FR-8: Verdict line and signal discipline | `implemented-as-written` | Addressed in section "Implementation Strategy". |
| FR-9: Documentation, including the report-file correction | `implemented-as-written` | Addressed in section "Deliverables". |
| FR-10: Tests | `implemented-as-written` | Addressed in section "Architecture Considerations" and Deliverables. |

## Must-fix
- **Axis A (Gap) — Spurious connection mutation for `h_mad_report_wait.py`** — The plan claims that dropping the wait call will make the `delivered=report-file` test fail. However, the "reap first" design explicitly bypasses the wait call if the file is already present (Step 2 checks the path directly). If the test creates the file before the script checks it (which is the standard way to mock a successful file delivery), the wait call is never reached and dropping it will NOT fail the test. The plan must mandate a "delayed report-file delivery" test (where the file is created *after* the wait begins) to ensure this connection mutation is caught.
- **Axis B (Connection enforcement) — Missing unconditional mutation for `h_mad_audit_gate.py`** — The invariant requires mutating the connection in both directions (remove it, and force it to fire unconditionally). The plan provides two mutations for the gate call: "drop the per-pass gate call for pass 2" and "remove the caller's per-pass loop so only pass 1 is gated", stating both fail the same cycle failure test. These are the exact same removal mutation phrased in two different ways. The plan fails to provide the "force it to fire unconditionally" direction (e.g., forcing it to gate a pass even when `delivered=none`, which should fail a cannot-judge/`UNVERIFIED` test).

## Should-fix
- **Axis A (Weak claim) — The shell-to-helper boundary unconditional mutation** — The plan proposes "drop the `--halt-reason` no-pass invocation and let the shell echo its own line" as a mutation for the `h_mad_audit_cycle.py` boundary. While this effectively tests the formatting boundary, it isn't an "unconditional connection" mutation. A true unconditional mutation would be removing the shell's guard and forcing it to invoke the helper for gating even when assembly failed, which should fail an `assemble_halt` test.

## Nit
None
