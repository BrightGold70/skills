AUDIT-audit-cycle-verb-plan-v7-BEGIN
## Summary
The plan demonstrates excellent invariant discipline (Axis B), particularly in connection enforcement, mutation verification, and single-source contracting. All functional requirements from the spec are implemented as written. However, adversarial review (Axis A) reveals one critical gap where the deterministic fallback channel is left unprotected against stale data.

**Axis C: Spec Reconciliation (Plan audit — FR-N granularity)**

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
- **Stale `--out` path exposes the fallback channel to previous-run data (Axis A - Gaps)** — The plan rigorously clears `<report-path>` and `<report-path>.done` to prevent a crashed dispatch from scoring a previous cycle's report, and explicitly relies on `--out` as the fallback collection channel (FR-4). However, because the `--out` path is deterministic per phase/cycle/pass (e.g., `/tmp/audit_..._cycle1_p1.txt`), a re-run of the same cycle will reuse the same path. If the new dispatch crashes before writing, `h_mad_extract_report.py` will silently extract the *previous run's* report from the uncleared `--out` file. The verb must clear and assert the removal of the `--out` path before dispatch, exactly as it does for the report-file.

## Should-fix
None

## Nit
None
AUDIT-audit-cycle-verb-plan-v7-END
