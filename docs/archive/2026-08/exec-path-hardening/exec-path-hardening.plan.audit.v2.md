AUDIT-exec-path-hardening-plan-v2-BEGIN
## Summary
The plan is highly rigorous, backing its strategy with live probe evidence (A1-A5) and mandating strict wire-scoped reverts for connection enforcement. It explicitly addresses test discrimination and ensures observability remains non-interfering. All functional requirements from the spec are mapped to deliverables. However, there are critical gaps in how the `--log` contract is resolved and logical contradictions in the comment composition strategy that must be addressed to prevent data loss and NFR violations.

| Requirement | Classification |
|---|---|
| FR-1 | `implemented-as-written` |
| FR-2 | `implemented-as-written` |
| FR-3 | `implemented-as-written` |
| FR-4 | `implemented-as-written` |
| FR-5 | `implemented-as-written` |
| FR-6 | `implemented-as-written` |

## Must-fix
- Vague Requirement (FR-5): The spec requires resolving the `--log` truncation asymmetry into a single stated contract (either make codex append, or state truncation as the contract). The Plan lists "--log contract decision applied" as a deliverable but fails to actually declare *what* the decision is. As a strategy document, it must state the chosen contract rather than leaving a TBD placeholder.
- Contradiction in comment composition (A4): The plan correctly identifies the clobber hazard where a heartbeat would destroy a `handoff` resume checkpoint. However, the proposed mitigation is to "obey the same rule" where "skill stamps may be replaced". If the heartbeat replaces existing skill stamps under this rule, it will still destroy the `handoff` checkpoint. The plan must explicitly establish a convention where `h-mad` heartbeats can coexist with a `handoff` checkpoint rather than replacing it.
- NFR Violation (FR-1): The spec mandates that the overhead from start + exit stamps must be "≤ 2 bounded orca calls". The Plan's read-then-compose strategy requires a `worktree ps` call to read the comment and a `worktree set` call to write it for *each* stamp. This totals at least 4 bounded calls for start and exit, silently violating the performance NFR. The plan must reconcile this (e.g., by explicitly claiming the NFR breach as a necessary consequence of the A4 constraint).

## Should-fix
None

## Nit
- W3's `WIRE-PIN` description mandates checking that no comment carrying `rc=<n>` is emitted. Consider explicitly adding the verdict token extraction to the assertion, as AC-1.2 requires the exit comment to contain both the `rc` and the extracted verdict.
AUDIT-exec-path-hardening-plan-v2-END
