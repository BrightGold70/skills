AUDIT-exec-path-hardening-plan-v1-BEGIN
## Summary
The plan cleanly addresses the spec's functional requirements and identifies the primary integration risks, such as the shared worktree comment field and the regression risks of unifying the execution path. All Functional Requirements from the spec are implemented as written in the plan. However, the plan violates Base Invariants regarding assumption verification and connection enforcement.

| Spec Identifier | Plan Coverage | Classification |
|---|---|---|
| FR-1 | Checkpoint emitter (start / heartbeat / exit), Orca stub | implemented-as-written |
| FR-2 | Unified background-and-poll execution path, heartbeat comment | implemented-as-written |
| FR-3 | Exit notification call | implemented-as-written |
| FR-4 | Non-interference test set + mutation spec | implemented-as-written |
| FR-5 | `--log` contract decision applied to code and docs | implemented-as-written |
| FR-6 | `--cd` → worktree-selector resolver | implemented-as-written |

## Must-fix
- Assumption verification (Axis B Base Invariant) — The plan asserts load-bearing assumptions about existing states without citing the observed output of throwaway commands. Specifically, it asserts the path-to-selector mapping can be extracted "off `worktree ps`" and that `_cmd_worktree_comment` already carries `_require_orca`. These assumptions must be executed live and their exact outputs cited in the document to prove the intended strategy matches reality.
- Connection enforcement (Axis B Base Invariant) — The plan introduces new connections by calling `_cmd_notify` and `_cmd_worktree_comment` from within `_cmd_exec`. While the plan mentions mutation-verifying guards, it must explicitly mandate a test that fails when these specific call sites (the connections) are removed or forced to fire unconditionally while the callee is left intact.

## Should-fix
None

## Nit
None
AUDIT-exec-path-hardening-plan-v1-END
