## Summary
The design document's assertions and measurements were verified against the current repository state, confirming the differential script outputs and census numbers. However, a declared non-exempt rule regarding ordinals remains unenforced in the Version History entries.

## Must-fix
- Version History ordinals violate the ordinal-base rule — v1.96 states that the ordinal-base rule remains non-exempt in Version History, but entries like v1.12 and v1.23 still contain bare ordinals that fail to name both the index convention and the span.
  quote: docs/02-design/features/doc-block-exec.design.md › `the ordinal-base rule remains non-exempt`
  quote: docs/02-design/features/doc-block-exec.design.md › `the second named fault injection`

## Should-fix
None

## Nit
None
