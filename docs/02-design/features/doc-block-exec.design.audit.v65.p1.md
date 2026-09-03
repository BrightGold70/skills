## Summary
The `doc-block-exec` design document is exceptionally thorough, precise, and internally consistent across all invariants, ACs, exception mappings, and mutation rows. The design defines rigorous boundaries for execution, stream handling, test orchestration, and failure isolation, leaving almost no room for implementation ambiguity.

## Must-fix
None

## Should-fix
None

## Nit
- `duplicate-heading-takes-first` mutation row — The introduction to the mutation spec states that "Every guard below carries one mutation and the one named test that must go RED under it", but the `duplicate-heading-takes-first` row lists two tests (`test_duplicate_headings_refuse`, `test_bare_form_duplicate_headings_refuse`). If the JSON spec format requires exactly one string for the `test` key, this either contradicts the JSON schema or requires splitting into two rows.
