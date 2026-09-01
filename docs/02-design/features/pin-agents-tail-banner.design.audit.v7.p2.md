## Summary
The design complies with all Axis B invariants and contains no generic adversarial gaps under Axis A. For Axis C (Spec reconciliation), the design implements all acceptance criteria as written, with one explicit exception: AC-3.2 is restated to narrow its candidate pool restriction based on the behavior of earlier passes.

| Acceptance Criterion | Classification |
|---|---|
| AC-1.1 | `implemented-as-written` |
| AC-1.2 | `implemented-as-written` |
| AC-1.3 | `implemented-as-written` |
| AC-2.1 | `implemented-as-written` |
| AC-2.2 | `implemented-as-written` |
| AC-2.3 | `implemented-as-written` |
| AC-3.1 | `implemented-as-written` |
| AC-3.2 | `restated` |
| AC-3.3 | `implemented-as-written` |
| AC-4.1 | `implemented-as-written` |
| AC-4.2 | `implemented-as-written` |
| AC-4.3 | `implemented-as-written` |
| AC-5.1 | `implemented-as-written` |

## Must-fix
- Axis C restatement: AC-3.2 — The Spec requires "The pass considers only handles surviving the earlier passes' filtering; a pane those passes excluded is never selected by this one." The Design restates this to "a pane excluded from `$scoped` is never selected". The Design's form is narrower because it removes the requirement to respect any candidate filtering from Passes 1 and 2, arguing that those passes are "MATCHERS, not filters" and therefore do not remove anything from consideration.

## Should-fix
None

## Nit
None
