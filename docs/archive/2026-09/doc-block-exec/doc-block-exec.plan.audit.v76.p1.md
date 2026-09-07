AUDIT-doc-block-exec-plan-v76-BEGIN
## Summary
The Plan is highly precise, properly tracks its metrics with commit shas, and defines strict API contracts and fallback behaviors. However, there is a cross-document inconsistency where the Spec failed to propagate the updated bash fence census count, leaving a stale measurement that violates its own documentation rules.

## Must-fix
- The Spec carries a stale bash fence census count in its Out-of-Scope section, contradicting the Plan's updated count (73 at a8e0372) and violating its own "Rule for every tree-derived count in this document" by lacking both a runnable command and a commit sha on the same surface.
  quote: docs/01-plan/features/doc-block-exec.spec.md › `(re-measured this session, excluding archive);`

## Should-fix
None

## Nit
None
AUDIT-doc-block-exec-plan-v76-END
