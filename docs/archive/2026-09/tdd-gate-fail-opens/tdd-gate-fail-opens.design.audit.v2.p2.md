## Summary
The design provides a robust target-normalisation strategy, clearly defines the CANON protocol, and accurately addresses the spec's requirements for unresolvable targets, patch headers, bounded reaps, and the resume oracle. However, the implementation plan lacks exact file paths for the new and modified tests, violating the strict pathing requirements, and contains a contradiction regarding the `compare_readings.py` output format for T0.

## Must-fix
- The design does not provide exact file paths for new and modified tests, grouping them vaguely in the Components table and failing to name the new differential test in T6 or the mutation spec files in T8. — Exact file paths are required to satisfy the writing-plans quality constraints.
  class: build
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › ``| `h-mad/tests/` | modify and new |``
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › ``new differential test importing `decision` and `hermetic_env` from `h-mad/tests/tdd_gate_support.py` ``

- The specified output for T0's self-comparison violates the script's exact output grammar (which requires `approved=N`) defined in the same section. — A missing `approved=N` field would cause the orchestrator or subsequent parsers to fail when verifying the comparison output.
  class: build
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › ``T0's self-comparison is `COMPARE: PASS softened=0` and exit 0.``

## Should-fix
None

## Nit
None
