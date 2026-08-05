AUDIT-exec-path-hardening-plan-v3-BEGIN
## Summary
The plan is exceptionally thorough, proactively identifying critical integration risks such as the shared mutable comment field and the no-timeout path. It provides live probe evidence for its assumptions (Axis B) and establishes excellent `wiring`-shaped tasks for connection enforcement. Axis C reconciliation shows all functional requirements are fully addressed. There is one contradiction in the Scope section regarding flag changes that must be resolved.

| Functional Requirement | Classification |
|---|---|
| FR-1: Durable start/exit checkpoints | `implemented-as-written` |
| FR-2: Liveness heartbeat | `implemented-as-written` |
| FR-3: Desktop notification at exit | `implemented-as-written` |
| FR-4: Non-interference | `implemented-as-written` |
| FR-5: One stated `--log` contract | `implemented-as-written` |
| FR-6: Comment target resolution | `implemented-as-written` |

## Must-fix
- Contradiction in Scope regarding flags (Axis A) — The Scope section states "No change to `exec`'s stdout, `rc`, flags, prompt delivery, or verdict semantics." However, the Implementation Strategy explicitly changes the behavior of the `--log` flag for `codex` from truncation to appending to satisfy FR-5. The Scope section must explicitly carve out this intentional change to `--log`.

## Should-fix
- Incomplete connection enforcement for W3 — The `WIRE-PIN` for W3 specifies asserting `rc=<n>` and the `extracted verdict token` to satisfy AC-1.2. However, AC-1.2 also requires the exit comment to contain the agent token (`codex`/`agy`). W3 should be updated to assert that all three elements are present in the caller's output.
- Missing exact file paths in Deliverables table (Impl-plan quality) — While `scripts/hmad-dispatch.sh` is mentioned in the Scope, the Deliverables table relies on generic type categories like "wrapper internals", "tests", and "test plumbing". To meet the "exact file paths" requirement, update the table to map each deliverable to its explicit target file(s) (e.g., `tests/test_hmad_dispatch_exec.py`).

## Nit
- Explicit stub path — The "Orca-CLI invocation-counting stub" is an excellent test plumbing deliverable, but specifying exactly where this stub will be implemented (e.g., within an existing fixture in `test_hmad_dispatch_exec.py` or a dedicated `_bindir` script) would improve implementation clarity.
AUDIT-exec-path-hardening-plan-v3-END
