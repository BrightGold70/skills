## Summary
The implementation plan is exceptionally thorough, structurally sound, and rigorously defends its constraints. Exception mapping, race condition handling (especially around process group reaping and timeout drains), fault injection seams, and the mutation matrix are all meticulously specified. The plan accurately conforms to all invariants and provides air-tight regression guards.

## Must-fix
None

## Should-fix
None

## Nit
- AC-5.6 asserts `BAD_TIMEOUT value=` is followed by the argument verbatim. For numeric inputs like `0` or `-1`, `float()` converts them to floats, so `run_block` will raise `BadTimeout(0.0)` instead of the verbatim string `"0"`. The CLI will therefore print `value=0.0` rather than the verbatim input. To strictly meet the AC, `main` could catch the `BadTimeout` from `run_block` and re-raise it with the raw string, or the AC wording could be slightly relaxed.
- The `StreamCloseFailed` exception carries a `stream: str` field, but `main` does not print it as a detail line (unlike `written:`, `failed:`, `skipped:` for write failures). This omits context about which stream failed to close, though the `os_error` likely provides enough context. Consider adding `stream:` to `DETAIL_KEYS` if that distinction is useful for debugging.
