AUDIT-doc-block-exec-impl-plan-v38-BEGIN
## Summary
The implementation plan is technically solid and type-consistent across tasks. However, it violates the exact file paths invariant by referencing several production and test files by their bare filenames instead of their full repository paths. No TBD placeholders or mismatched code blocks were found.

## Must-fix
- Vague file paths missing their directory prefix — `h_mad_assemble_tdd.py` and `h_mad_mutation_harness.py` are referenced without their `h-mad/scripts/` paths, violating the requirement for exact file paths.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `h_mad_assemble_tdd.py:238-243`
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `h_mad_assemble_tdd.py --phase red`
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `h_mad_mutation_harness.py:679`

## Should-fix
None

## Nit
None
AUDIT-doc-block-exec-impl-plan-v38-END
