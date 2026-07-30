## Summary
The plan properly operationalizes test verification through prompt updates, establishes robust doc-tests for literal validation, and commits to incident replay against the historical defects. However, it violates the "Single-source contract" base invariant by applying the FR-1 rule to two independent surfaces (`codex-implementer-prompt.md` and `codex-verifier-prompt.md`) without guaranteeing byte-equivalence. Additionally, the plan restates and narrows key criteria from FR-1 and FR-3, requiring explicit reconciliation with the spec.

Axis C - Spec Reconciliation:
| Requirement | Classification |
|---|---|
| FR-1 | `restated` |
| FR-2 | `implemented-as-written` |
| FR-3 | `restated` |
| FR-4 | `implemented-as-written` |

## Must-fix
- Axis B (Base Invariants) / Single-source contract — The plan duplicates the FR-1 RED-test-quality rule across two separate files (`codex-implementer-prompt.md` and `codex-verifier-prompt.md`) without establishing a single authoritative implementation or adding a test that asserts byte-equivalence of the rule text across both surfaces. Independent reimplementations that can silently diverge are a violation.
- Axis C (Spec Reconciliation) / FR-1 restated (narrowed) — Spec form: "For each PASSING test: would it still pass if the behaviour it names were deleted? If yes, it is vacuous." Plan form: "each pass is non-vacuous". The plan narrows the rule by summarizing the concrete, executable criteria (hypothetically deleting the behavior) into an abstract label ("non-vacuous"), which provides weaker guidance to the LLM author.
- Axis C (Spec Reconciliation) / FR-1 restated (expanded) — Spec form: "FR-1 — RED-side acceptance gate (codex-implementer-prompt.md, RED variant)". Plan form: "codex-verifier-prompt.md (the 5e anti-gaming verifier — gains an explicit RED-test-quality check per FR-1...)". The plan expands the scope of FR-1 by applying it to the 5e verifier prompt as well, which diverges from the spec's explicit scoping to only the implementer RED variant.
- Axis C (Spec Reconciliation) / FR-3 restated (narrowed) — Spec form: "do not restructure a string literal, identifier, or import to change how a source-level assertion counts it". Plan form: "restructure a literal to fool a source count". The plan narrows the evasion protection by omitting "identifier, or import", protecting only literals.

## Should-fix
None

## Nit
None
