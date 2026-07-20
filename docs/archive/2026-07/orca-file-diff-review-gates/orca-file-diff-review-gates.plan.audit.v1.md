# Plan Audit v1 — orca-file-diff-review-gates

Reviewer: agy (Gemini 3.1 Pro High). Cycle 1.

## Summary
The plan clearly defines the two Orca-guarded verbs (file-diff, file-open-changed). It introduces a build-time schema-reconciliation goal (G4) that is unaddressed in the implementation strategy and deliverables.

## Must-fix
- Unaddressed Goal 4 (schema reconciliation) — G4 requires every `orca file …` argv be reconciled against `agent-context --json` schema v1 at build time, but neither the implementation strategy nor the deliverables say how. Hard gap: either add an implementation step/deliverable, or state the reconciliation is a manual authoring-time policy (as in Tier-3) so G4 is not an unmet automated requirement.

## Should-fix
None

## Nit
None
