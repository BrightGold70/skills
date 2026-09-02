## Summary
The implementation plan is thoroughly detailed and correctly incorporates prior audit fixes. However, several mutation `find` strings in Task 6 have drifted from the updated code blocks in Tasks 1 and 2, which will cause them to fail silently and leave guards unenforced. Additionally, the `WIRE-PIN` declarations in Tasks 3 and 4 are missing the skill directory prefix, breaking path consistency.

## Must-fix
- Task 3 and 4 `WIRE-PIN` paths omit the `h-mad/` prefix — `tests/test_hmad_dispatch.py` is not a valid repo-relative path. They should be `h-mad/tests/test_hmad_dispatch.py` to maintain path consistency with the repo-relative `WIRE` declarations and ensure the wire-pin gate resolves them correctly.
- Task 6 `stub-branch-ignores-env-var` mutation `find` string is missing `; _prev=""` — The `find` string specifies `_h=""`, but the Task 1 code block was updated to `_h=""; _prev=""`. The mutation will silently fail to match and leave the guard unenforced.
- Task 6 regex mutations (`tail-re-unanchored`, `tail-re-unanchored-agy`, `tail-re-widened-to-launch-line`, `tail-re-widened-to-launch-line-agy`) use outdated regex patterns in their `find` strings — They specify the older grammar (e.g. `(\.[0-9]+)*`) which no longer matches the updated line-complete grammar (e.g. `(\.[0-9]+)+`) prescribed in the Task 2 `_agent_tail_re` code block. These mutations will fail to apply silently.

## Should-fix
None

## Nit
None
