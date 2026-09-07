## Summary

The plan addresses FR-1, FR-2, FR-3, FR-5, and FR-6 as written, but silently narrows FR-4’s one-physical-line verdict contract. The current spec requires control-character escaping for every dynamic field; the plan promises one verdict line but does not plan the mechanism or its discriminator, despite claiming the field-escape row in its version history.

| FR | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | restated |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

## Must-fix
- FR-4 is silently restated: the spec says “The CLI prints one `DOCBLOCK:` line — one physical line, whatever the inputs: every dynamic field … is rendered with `\r`, `\n` and other control characters escaped”; the plan says only “The CLI prints exactly one `DOCBLOCK:` verdict line” and contains no `_field`/control-character escaping rule, hostile-field test, or `field-escape-removed` mutation (only a version-history claim that the row exists). The plan form is narrower: a newline in a heading, substitution key/value, path, or OS error can forge a second verdict line. Carry the authoritative escaper, all-field routing, and the corrected newline-bearing leftover-path test/mutation from design v1.76 into the plan before treating the paired documents as current.

## Should-fix
None

## Nit
None
