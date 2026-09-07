## Summary
The implementation plan is otherwise unusually concrete, but its two-form heading API has an unresolved ambiguity that makes part of the promised contract impossible to implement. It also retains a stale cross-document claim after the paired spec was updated.

## Must-fix
- `find_heading` overloads full and bare forms in one `str` without a discriminator — Task 1 says `"## Text"` is the full, level-pinned form and that every bare normalized text matches at any level. But `### ## Text` is a valid ATX heading whose bare title is `## Text`, so `find_heading(text, "## Text")` has two incompatible specified meanings (level-2 `Text` versus any-level title `## Text`). Define an unambiguous API (for example, an explicit form/mode) or a documented precedence plus an exclusion, and add a collision test; otherwise `docsections.titled_section` can silently select/refuse a valid title contrary to its stated unchanged bare-form contract.

## Should-fix
- The Phase 5f note at `doc-block-exec.impl-plan.md:1527` says the paired spec still lacks the repository-root pin and requests back-propagation, while the declared paired spec is v1.50 and `doc-block-exec.spec.md:458` already contains that exact root-pinned subshell. Remove or update the obsolete note so the three documents report the same state and do not prompt a redundant change.

## Nit
None
