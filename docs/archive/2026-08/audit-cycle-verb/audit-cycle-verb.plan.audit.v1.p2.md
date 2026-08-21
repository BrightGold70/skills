## Summary
The plan accurately covers the core architectural requirements for the `audit-cycle` verb, explicitly addressing all Functional Requirements (FR-1 to FR-10) and properly identifying the risks of naive union concatenation. However, it misses the CLI parameter plumbing necessary to maintain existing operator capabilities, specifically the `--ack-file` override mechanism which violates a Base Invariant.

**Axis C — Spec reconciliation:**

| Requirement | Classification |
|---|---|
| FR-1: One verb, one cycle | `implemented-as-written` |
| FR-2: Assembly is gated, and its size signal is relayed | `implemented-as-written` |
| FR-3: Two independent passes, isolated per-pass channels | `implemented-as-written` |
| FR-4: Report collection tries report-file, falls back to `--out` | `implemented-as-written` |
| FR-5: Union gating by per-pass gate runs, never by concatenation | `implemented-as-written` |
| FR-6: Cannot-judge is a distinct verdict carrying no counts | `implemented-as-written` |
| FR-7: Premise-check checklist | `implemented-as-written` |
| FR-8: Verdict line and signal discipline | `implemented-as-written` |
| FR-9: Documentation, including the report-file correction | `implemented-as-written` |
| FR-10: Tests | `implemented-as-written` |

## Must-fix
- **Missing `--ack-file` forwarding (Axis B: Operator-override preservation)** — The plan does not specify that the `audit-cycle` verb must accept and forward the `--ack-file` argument to the underlying gate script. Without this, the `## Acknowledged-not-fixed` sidecar mechanism will be inaccessible via the new unified verb, violating the operator-override preservation base invariant. The plan must explicitly state how `--ack-file` is surfaced and passed down.
- **Missing CLI context parameters (Axis A: Gap)** — The plan mentions "one command that runs a cycle" but fails to specify that the verb must accept the necessary context arguments (`--feature`, `--phase`, `--cycle`, `--project-root`, and `--passes`) to forward to the underlying scripts. The CLI signature must be explicitly defined to ensure all composed scripts receive their required inputs.

## Should-fix
- **Ambiguity in orchestration vs helper responsibilities (Axis A: Clarity)** — The plan states the verb "shells out" to the four existing scripts, but also says "Collection and gating logic that needs real parsing is delegated to a small stdlib-only Python helper". It is unclear if the shell wrapper or the Python helper is responsible for invoking `h_mad_report_wait.py`, `h_mad_extract_report.py`, and `h_mad_audit_gate.py`. Clarify the exact process boundary.

## Nit
None
