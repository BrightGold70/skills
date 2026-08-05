AUDIT-exec-path-hardening-plan-v4-BEGIN
## Summary
The plan provides a comprehensive and accurate strategy that addresses all functional requirements from the spec, including the deliberate NFR performance amendment for safe composition. However, there is a critical logic gap in the composition rule that violates the stated idempotency requirement, along with test stub limitations that would hide this defect, requiring corrections before implementation.

| Requirement | Classification | Notes |
|---|---|---|
| FR-1 | `implemented-as-written` | Checkpoint emitter covers start/exit |
| FR-2 | `implemented-as-written` | Unified background-and-poll execution path covers heartbeat |
| FR-3 | `implemented-as-written` | Exit notification deliverable |
| FR-4 | `implemented-as-written` | Non-interference + mutation testing |
| FR-5 | `implemented-as-written` | Codex `--log` append contract in code/prose |
| FR-6 | `implemented-as-written` | `--cd` selector resolver |

## Must-fix
- Composition rule contradiction — The plan states that composition must be idempotent ("never grow the string once per interval"), but the table's rule replaces only if the string "starts with `h-mad`". If a human comment exists ("Fixing issue"), the first heartbeat appends the stamp at the end ("Fixing issue · h-mad: running"). The next heartbeat sees the string does *not* start with `h-mad`, hits the "anything else" rule, and appends it again, resulting in runaway string growth. The rule must detect and replace the `h-mad` stamp wherever it appears.
- Test stub statefulness gap — The plan proposes using static `HMAD_STUB_ORCA_WT_PS_STDOUT` fixtures for the `worktree ps` read. If the stub is static, a multi-interval heartbeat test will read the same initial comment every tick and append exactly once, hiding the runaway string growth defect described above. To satisfy the "Test discrimination" invariant, the stub must be stateful (e.g., `worktree set` writes to a temp file that `worktree ps` reads) so the read-modify-write loop is genuinely exercised.
- Read-failure clobber hazard — The plan introduces a `worktree ps` read before writing to prevent clobbering existing comments (A4), but does not state the failure mode of the read itself. If the bounded read fails or times out, and the script falls back to treating the comment as empty before executing the write, it will blindly overwrite and destroy the existing checkpoint. The plan must explicitly state that a read failure aborts the entire checkpoint update attempt.

## Should-fix
None

## Nit
- In the connection enforcement table, W2 states "a multi-interval run produces exactly one fewer than the expected stamp count" if the heartbeat call is removed. Since a multi-interval run would normally produce N heartbeats, removing the call produces N fewer stamps (or 0 heartbeats, resulting in exactly 2 stamps for start/exit), rather than "exactly one fewer".
AUDIT-exec-path-hardening-plan-v4-END
