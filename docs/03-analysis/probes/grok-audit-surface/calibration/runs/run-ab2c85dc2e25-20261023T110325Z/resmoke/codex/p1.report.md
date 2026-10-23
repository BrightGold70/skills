AUDIT-audit-report-docs-copy-plan-v3-BEGIN
## Summary
FR coverage: FR-1 `implemented-as-written`; FR-2 `implemented-as-written`; FR-3 `implemented-as-written`; FR-4 `implemented-as-written`; FR-5 `implemented-as-written`; FR-6 `implemented-as-written`. The plan is not internally buildable as written because its success criteria demand 25 mutations while its requirements, deliverables, and source spec define 23; the implementation test in this tree also pins 23. Evidence: 4 files opened, 5 greps run.

| Functional requirement | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

## Must-fix
- Resolve the mutation-count conflict: the success criterion requires 25 mutations, but the plan's FR-6 and deliverables and the source spec require 23, so an implementer cannot satisfy both release gates. The local test also enforces exactly 23. — a contradictory acceptance target makes the required mutation battery indeterminate.
  class: build
  quote: Plan: audit-report-docs-copy › `MUTATION: ALL_CAUGHT on collect_report.json (25 mutations, every connection dropped AND forced, fall-through paths included).`
  quote: Plan: audit-report-docs-copy › `mutation spec with 23 named-test mutations`
  quote: Source spec: # Spec: audit-report-docs-copy › `h_mad_mutation_harness.py reports MUTATION: ALL_CAUGHT.`

## Should-fix
None

## Nit
None
AUDIT-audit-report-docs-copy-plan-v3-END
