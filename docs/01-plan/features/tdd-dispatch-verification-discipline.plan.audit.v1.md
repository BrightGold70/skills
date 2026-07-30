## Summary
The plan accurately maps all functional requirements from the spec into concrete prompt and protocol edits, applying a strong doc-testing strategy to lock the new literals. All Axis C FRs and ACs are correctly implemented as written. However, the plan breaches the "Incident replay" base invariant by relying solely on doc-tests without proposing to verify the new prompt instructions against the real historical defects that motivated them.

**Axis C — Spec reconciliation:**
| Requirement | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |

## Must-fix
- Incident replay invariant violation — The plan claims "a prompt's runtime behavior can't be unit-tested" and relies solely on static doc-tests to verify the new rules. The base invariants require that a fix motivated by a specific incident MUST be replayed against the real artifacts that motivated it. The plan must include a step to manually replay the new RED and GREEN prompts against the historical `feature/193` commits (`4298345c`, `d8ef251e`, `fd7be463`) to prove the prompt changes actually induce the agent to STOP and report the evasions, rather than just proving the instruction text exists in the files.

## Should-fix
None

## Nit
None
