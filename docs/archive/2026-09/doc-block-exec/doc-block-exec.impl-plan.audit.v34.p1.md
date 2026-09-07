AUDIT-doc-block-exec-impl-plan-v34-BEGIN
## Summary
The implementation plan is exceptionally thorough, precise, and entirely free of TBD placeholders or vague requirements. Code blocks perfectly align with referenced functions, file paths are exact, and exceptions are meticulously mapped. However, the exhaustive list of bare fields incorrectly categorizes the `keys` slot (which holds caller-provided substitution keys) as a helper-produced int/enum, breaking the escaping invariant.

## Must-fix
- The `keys` field is classified as a bare int/enum safely produced by the helper, but it actually contains the caller-provided `--subst` keys (a list of strings or tuples), violating the exemption rule and potentially exposing unescaped data in the verdict line.
  quote: docs/03-impl-plan/features/doc-block-exec.impl-plan.md › `The 7 bare ones are \`rc\`, \`blocks\`, \`count\`, \`keys\`, \`shell\`, \`stage\` and \`reason\`: ints and enums the helper itself produces, never derived from a caller argument or a document, so there is nothing in them to escape.`

## Should-fix
None

## Nit
None
AUDIT-doc-block-exec-impl-plan-v34-END
