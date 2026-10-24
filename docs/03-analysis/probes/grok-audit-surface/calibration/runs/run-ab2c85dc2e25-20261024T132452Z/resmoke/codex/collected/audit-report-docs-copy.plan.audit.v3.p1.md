## Summary
Axis C: the plan addresses all six spec functional requirements as written; no FR is restated or absent. The planned transport refusal has a normal `INVALID` verdict but exits 2, conflicting with the base signal rule and the plan's own stated gate contract; the replay evidence also lacks exact commands, and the mutation count conflicts with the spec. Evidence: 3 files opened, 6 greps run.

| Spec FR | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

## Must-fix
- The transport refusal is a normal `INVALID` gate verdict, yet the plan requires exit 2; non-zero is reserved for operational errors, and the plan's own stated gate contract requires exit 0 for any verdict. Align the plan and spec with the base signal discipline (emit the verdict token and exit 0).
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `stem verbatim — a transport name has no reliable feature grammar), exit 2; <feature>.report.md (Phase 7) still`
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `exit 0 on any verdict`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `h_mad_collect_report.py)`, exit 2.`
  quote: h-mad/invariants.base.md › `exit is permitted ONLY for genuine operational errors (missing/unreadable input).`
- The incident replay is reported as completed, but its history entry records outputs only; it omits the exact commands required to re-derive this behavioral premise. Record the commands alongside the observations.
  class: measurement
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `AC-2.9h hand replay 2026-09-02 survivor=/tmp/audit_nlmpin_plan_cycle8_codex.report.md (scratch root, not HemaSuite): gate(RP)=GATE: INVALID must=0 should=0 rc=2 · collect=COLLECT: OK path=<R>/docs/01-plan/features/nlm-cli-version-pin.plan.audit.v8.codex.md delivered=report-file · cmp=identical · gate(docs)=GATE: FAIL must=3 should=1 rc=0`
  quote: h-mad/invariants.base.md › `MUST carry the exact command that produced it, inline and runnable, beside the observed output.`

## Should-fix
- The success criterion says 25 mutations while the requirements, deliverable, and source spec specify 23; this makes the required mutation count ambiguous and the published figure wrong. Use the re-derived count of 23 consistently.
  class: measurement
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `MUTATION: ALL_CAUGHT on collect_report.json (25 mutations, every connection dropped`
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `collect_report.json — 23 mutations, drop/force pairs per connection incl. fall-through paths and the grammar-disjointness property`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `23 mutations.`

## Nit
None
