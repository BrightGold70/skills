AUDIT-doc-block-exec-plan-v78-BEGIN
## Summary
The plan, design, and impl-plan documents are generally consistent with each other and accurately describe the state of the codebase. However, the impl-plan contains several line pins into `h-mad/` source that lack the required accompanying symbol names, breaking the self-repair invariant for drifted pins.

## Must-fix
- Line pins into `h-mad/` source without an accompanying symbol name — breaks the invariant that every such pin must carry its symbol name beside it so it can self-repair when drifted.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `via \`str.replace\` — \`h_mad_mutation_harness.py:645\` — so a multi-site revert must be expressed`
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `kill (\`h_mad_mutation_harness.py:609–623\`), against AC-1's last bullet, which requires`
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `(\`h_mad_mutation_harness.py:606-607\`), so \`command\` never selects a killer`
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `at \`h_mad_mutation_harness.py:679\`, which asks "what else noticed" after a row already survived;`
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `(\`h_mad_mutation_harness.py:660–669\`); \`test_h_mad_doc_block_exec.py\` imports only \`dbe\` and`
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `and \`test_suite_collection.py:81\` rglobs \`test_*.py\` from inside a body`

## Should-fix
None

## Nit
None
AUDIT-doc-block-exec-plan-v78-END
