AUDIT-doc-block-exec-design-v83-BEGIN
## Summary
The design provides a comprehensive specification and implementation order with exact file paths and consistent type definitions across tasks. However, two function signatures in the API code blocks lack trailing colons, violating Python syntax and the consistency requirement for referenced functions.

## Must-fix
- Missing trailing colons in function signatures in the `## API / Interface Changes` section — Python syntax requires a colon after the return type, but the `run_block` and `main` signatures omit it, rendering the code blocks invalid.
  quote: # Design: doc-block-exec › `timeout: float = 30.0) -> RunResult`
  quote: # Design: doc-block-exec › `def main(argv: Sequence[str] | None = None) -> int`

## Should-fix
None

## Nit
None
AUDIT-doc-block-exec-design-v83-END
