## Summary
Spec reconciliation: all AC-1.1–AC-1.9, AC-2.1–AC-2.8, AC-3.1–AC-3.14, AC-4.1–AC-4.6, AC-5.1–AC-5.6, and AC-6.1–AC-6.6 are implemented-as-written; none is restated or absent.

| Classification | ACs |
|---|---|
| implemented-as-written | AC-1.1–1.9; AC-2.1–2.8; AC-3.1–3.14; AC-4.1–4.6; AC-5.1–5.6; AC-6.1–6.6 |
| restated | None |
| absent | None |

The design otherwise maintains the required single authoritative bounder and connection pins, but it contains one contradictory description of the AC-1.8 test strategy.

## Must-fix
None

## Should-fix
- AC-1.8’s test model is described inconsistently: the design correctly says a differential test is “not achievable” and specifies delegation to the authoritative bounder, but later says “the AC-1.8 differential test covers the assumption from the other side.” — Remove or correct the latter wording; it can send implementation toward the expressly impossible differential/parity test rather than the specified delegation test.

## Nit
None
