## Summary
The design correctly incorporates all functional requirements and acceptance criteria from the spec and plan, including the required doc-tests and the Phase-6 incident replay. However, there is a direct contradiction between the Detailed Design text and the Test Plan (as well as a violation of the Single-source contract base invariant) regarding the verifier prompt pointer.

| AC | Classification |
|---|---|
| AC-1 (RED-side acceptance gate) | `implemented-as-written` |
| AC-2 (revert-test definition) | `implemented-as-written` |
| AC-3 (evasions named) | `implemented-as-written` |
| AC-4 (re-verify plan pins) | `implemented-as-written` |
| AC-5 (doc-tests) | `implemented-as-written` |
| AC-6 (both suites green) | `implemented-as-written` |

## Must-fix
- Single-source contract / Internal contradiction — The Detailed Design for the FR-2 pointer in `codex-verifier-prompt.md` restates the full revert-test mechanism in parentheses: `(revert production → RED returns exactly → restore → green returns)`. This contradicts the Plan (v1.5: "pointer... reference, not restatement"), violates the Single-source contract base invariant, and contradicts the Design's own Test Plan which claims it "does NOT restate the full mechanism" and that the mechanism sentence count is 1 across the two files. Remove the parenthetical restatement so the pointer is strictly a reference.

## Should-fix
None

## Nit
None
