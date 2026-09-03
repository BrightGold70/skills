## Summary
The design implements every spec acceptance criterion as written; the reconciliation is complete below. A cross-document audit found one blocking conflict in the paired implementation plan's parser-error behavior.

| Spec AC identifiers | Classification |
|---|---|
| AC-1.1–AC-1.9 | implemented-as-written |
| AC-2.1–AC-2.8 | implemented-as-written |
| AC-3.1–AC-3.14 | implemented-as-written |
| AC-4.1–AC-4.6 | implemented-as-written |
| AC-5.1–AC-5.6 | implemented-as-written |
| AC-6.1–AC-6.6 | implemented-as-written |

## Must-fix
- The paired implementation plan’s “Exit-code partition” says “argparse usage errors are the only non-`DOCBLOCK:` exit 2,” while the design explicitly requires `exit_on_error=False` plus an overridden `error()` that emits `DOCBLOCK: BAD_ARGS …`, exit 0; AC-5.6 in the spec says the same. This is a material implementation-plan contradiction: following it would reintroduce the exact non-verdict exit that the design’s `argparse-error-unrouted` mutation and `test_malformed_invocation_is_a_verdict` are meant to prevent.

## Should-fix
None

## Nit
None
