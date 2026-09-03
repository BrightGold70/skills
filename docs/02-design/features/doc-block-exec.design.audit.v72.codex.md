## Summary
The design covers all 49 source-spec acceptance criteria, with no absent or silently narrowed item found. It also remains aligned with the paired plan on the authoritative scanner/bounder, scoped FR-6 migration, and mutation-backed wiring checks.

| Spec AC identifiers | Classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-1.8, AC-1.9 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.7, AC-2.8 | implemented-as-written |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7, AC-3.8, AC-3.9, AC-3.10, AC-3.11, AC-3.12, AC-3.13, AC-3.14 | implemented-as-written |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | implemented-as-written |

## Must-fix
None

## Should-fix
- Normalize the verdict-table examples to the declared `_field` grammar — the table writes forms such as `BAD_INDEX index=<n>` and `NOT_FOUND heading=<h>`, while the governing rule says every non-enum/non-listed dynamic value is JSON-quoted (for example, `index="0"`, `heading="H"`). The global rule is clear enough to preserve the invariant, but literal table readers could implement contradictory wire output.

## Nit
None
