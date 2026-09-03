## Summary
The design, spec, and plan are thoroughly specified, highly consistent, and provide rigorous mutation bindings and exception handling contracts for the `doc-block-exec` feature. I found one must-fix naming mismatch between the plan and the design's mutation table regarding the invalid UTF-8 preamble test, which would break the mutation harness due to an invalid node ID.

## Must-fix
- Test name discrepancy for invalid UTF-8 preamble — The Plan specifies `test_cli_invalid_utf8_preamble_refuses_before_running`, but the Design's mutation table maps the `preamble-decode-error-unwrapped` mutation to `test_invalid_utf8_preamble_is_unreadable`. This creates a hard gap because the mutation harness requires an exact node ID match, and a discrepancy will cause it to crash trying to find the missing test.

## Should-fix
None

## Nit
- Missing `heading=<h>` in Plan's prose — The Plan's text omits the `heading=<h>` field in its examples for `DOCBLOCK: NOT_FOUND` and `DOCBLOCK: AMBIGUOUS blocks=2`, whereas the Design's verdict table correctly specifies it.
- Missing type hint in Plan API — The Plan defines `select(blocks, index: int | None = None) -> Block`, omitting the `Sequence[Block]` type hint for `blocks` present in the Design.
- Case discrepancy in CLI usage doc — The Plan uses `[--preamble-file <path>]` while the Design uses `[--preamble-file PATH]`.
