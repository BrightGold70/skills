## Summary
The plan is mostly reconciled to the v1.3 spec, but FR-4 still contains one unresolved internal contradiction: the body allows diagnostic counts while a later prerequisite bans all cannot-judge counts. Axis C reconciliation:

| FR | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | restated |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

## Must-fix
- FR-4 is restated inconsistently inside the plan — Spec form: "A cannot-judge carries no count that could be read as a measured result ... but may carry a diagnostic count ... which is why `AMBIGUOUS` carries `blocks=<n>`" and AC-4.4 says "`AMBIGUOUS` carries `blocks=<n>`"; plan form under Convention Prerequisites says "Verdict-token discipline: read the token, never `$?`; a cannot-judge carries no counts." The plan's Convention Prerequisites wording is narrower because it forbids the diagnostic `blocks=<n>` count the spec requires, so downstream work can satisfy that bullet while violating AC-4.4.

## Should-fix
- The deliverable "Wire mutations for the migrated call site (both directions)" has no exact file path — the table names `h-mad/tests/mutation-specs/doc_block_exec.json` for FR-1..FR-5 but leaves FR-6's mutation location implicit, which is avoidable ambiguity for an implementation plan focused on wiring quality.

## Nit
None
