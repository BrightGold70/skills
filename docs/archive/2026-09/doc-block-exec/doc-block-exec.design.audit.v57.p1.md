## Summary
The design presents a highly robust, specification-compliant architecture for bounded, isolated bash block execution. The state machine safely maps operational errors, enforces strict process group containment without unhandled races, and verifies artifact creation and cleanup stringently. A critical control flow contradiction in the timeout exception handling must be resolved to preserve the cleanup verification guarantees.

## Must-fix
- Timeout handler control flow — The Detailed Design section for Execution states that the post-kill drain times out and "raises BlockTimeout as it would have anyway". This explicitly contradicts the Architecture Overview's rule that `run_block` "never raises from inside the timeout handler" and instead records the pending outcome. Raising directly from the handler would bypass the post-`finally` `lexists` read-back, preventing a silent directory retention from being caught and reported as a `CleanupFailed` error.

## Should-fix
- Missing `stream-write-oserror-unwrapped` mutation — While the design explicitly verifies that OS errors from stream reservation and backstop closures are safely mapped (via the `stream-open-oserror-unwrapped` and `backstop-close-unmapped` mutations), there is no equivalent mutation to verify that the `except OSError` mapping block inside `_final_write` is intact. A mutation should be added to ensure a write error doesn't escape as a traceback.

## Nit
- API export count — The API Changes section states "`__all__` names all seven", but there are nine core public symbols defined in that block (`Block`, `RunResult`, `extract`, `select`, `substitute`, `run_block`, `main`, `fence_aware_end`, `find_heading`), plus the custom exception classes.
- Outdated `str.replace` reference — In AC-2.8, the justification for refusing empty keys states "`str.replace("", v)` would insert `v` at every character boundary". While the rationale is correct, the design specifies that the implementation uses a simultaneous single-pass `re.sub` alternation, so this should reference `re.sub` instead.
