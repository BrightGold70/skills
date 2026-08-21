## Summary
The plan successfully details a robust implementation for the `audit-cycle` verb, correctly distributing orchestration to the shell and text/verdict handling to a Python helper. It thoroughly maps against the functional requirements (all FRs are `implemented-as-written`) and explicitly addresses edge cases like shared `--out` race conditions and union gating miscounts. However, there is one contradiction regarding the exit-code discipline for prompt divergence that must be resolved to comply with the base invariants.

| Functional Requirement | Classification |
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
- **Contradiction in exit-code discipline for prompt divergence** — The plan states that a failed byte-identity assertion (prompt divergence) "is an operational error, not a verdict: the shell invokes the helper's no-pass mode with reason=prompt_divergence, which prints AUDITCYCLE: UNVERIFIED and exits 0". This contradicts the base invariant ("A non-zero exit is permitted ONLY for genuine operational errors") and Spec AC-8.2 ("Every verdict exits 0. A non-zero exit means an operational error and is accompanied by no AUDITCYCLE: line"). If prompt divergence is truly an operational error (inputs changing mid-cycle), it MUST exit non-zero and omit the `AUDITCYCLE:` token so it registers as a tool failure. If it exits 0 and emits a token, it is communicating a verdict to the orchestrator. You must choose one behavior and align the text.

## Should-fix
None

## Nit
None
