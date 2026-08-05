## Summary
The design is exceptionally thorough, defensive, and meticulously addresses the edge cases of the plan. All 24 Acceptance Criteria across FR-1 to FR-6 are `implemented-as-written` and explicitly mapped in the test plan. The design actively caught and documented minor contradictions in the plan (such as the unification removing the second codex invocation), replacing them with the correct behavior that satisfies the invariant. The attention to detail on descriptor inheritance, base64 null parsing, and unbounded recursion is excellent.

## Must-fix
None

## Should-fix
None

## Nit
- The detailed design heading for `_exec_run` states its signature as `_exec_run <secs> <cmd...>`, but the preceding text introduces the `--heartbeat` flag (`_exec_run --heartbeat "$timeout" codex …`). Updating the heading signature to include the flag would fully align the section header with the text.
