## Summary
The plan addresses FR-1 through FR-6, but its execution sequence and verification leave blocking gaps in the proposed Phase 4 gate. Axis C classification is below; the findings also address the base invariants.

| Requirement | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | restated |
| FR-6 | implemented-as-written |

Evidence: 4 files opened (plan, spec, gate, and OneContext skill), 3 greps run. OneContext history was unavailable outside its dashboard environment. 🌱 graft saved ~58,154 tokens this turn, 1 call.

## Must-fix
- FR-5 removes the spec's exemption from the auditor's missing-section finding — the plan tells auditors to flag missing sections without limiting that rule to non-exempt designs, so legacy designs can be deterministically exempt yet blocked by the audit. Restore the exemption qualification in both prompt surfaces.
  class: build
  quote: docs/01-plan/features/hmad-test-boundaries.plan.md › `to require `Must-fix` findings when `## Test Boundaries` is missing/uncovered`
  quote: docs/01-plan/features/hmad-test-boundaries.spec.md › `## Test Boundaries` is missing (on a non-exempt design) or leaves any active spec `AC-X.Y[a-z]` uncovered;
- The feature cannot bootstrap its own Phase 4 design — the plan requires the design author to run a checker before DONE, but creates that checker in implementation after proceeding to Phase 4. Specify a viable, verified bootstrap path or sequence that preserves the intended gate without requiring nonexistent production code.
  class: build
  quote: docs/01-plan/features/hmad-test-boundaries.plan.md › `to run `h-mad/scripts/h_mad_test_boundaries_check.py` (verifying `TEST-BOUNDARIES: PASS`) before emitting `DESIGN-AUTHOR: DONE``
  quote: docs/01-plan/features/hmad-test-boundaries.plan.md › `Proceed to Phase 4 (Design) to author the Phase 4 design document`
- The gate connection lacks the required two-direction mutation tests — a generic mutation spec and RED/GREEN tests do not require a connection-only removal test and a forced-unconditional activation test, with the checker left intact and each mutation verified as landed. The base connection-enforcement invariant requires both, including a negative fixture that distinguishes unconditional activation.
  class: build
  quote: docs/01-plan/features/hmad-test-boundaries.plan.md › `mutation specification covering `h-mad/scripts/h_mad_test_boundaries_check.py` and the Phase 4 gate wiring in `h-mad/scripts/h_mad_audit_gate.py``
- The candidate design is specified as a single `--gated` path even though the existing gate accepts repeatable `--gated` paths and stamps all of them. A mixed or multiple-design invocation has no defined rule for selecting and checking each design, allowing an unchecked failing design to be stamped; define the selection and test multiple paths and ordering.
  class: build
  quote: docs/01-plan/features/hmad-test-boundaries.plan.md › `Detect Phase 4 design audits from `--gated <path>` ending with `.design.md` or any `<report>` matching `<feature>.design.audit.v<N>[.<leg>].md`.`
  quote: h-mad/scripts/h_mad_audit_gate.py › `Repeatable — a cycle that gates a design and an impl-plan must name both`

## Should-fix
- The declared scope omits two existing test files that the implementation strategy says to modify, making the change inventory misleading for downstream planning.
  class: build
  quote: docs/01-plan/features/hmad-test-boundaries.plan.md › `In-scope files to modify (`6` existing tracked files)`
  quote: docs/01-plan/features/hmad-test-boundaries.plan.md › `h-mad/tests/test_h_mad_audit_gate.py`, `h-mad/tests/test_h_mad_audit_spec_axis.py`

## Nit
None
