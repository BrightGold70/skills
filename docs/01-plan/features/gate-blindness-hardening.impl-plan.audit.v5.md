## Summary
The implementation plan is solid, correctly correcting the implementation order to guarantee the schema accepts the override value before it is ever written. There is exactly one bash-execution gap in the hostile-corpus stub that would mask a validation failure and silently succeed, violating the requirement to loudly reject an unknown corpus.

## Must-fix
- **Masked error path in Task 5 stub** — The `jq` command invokes `_hostile_comment` via inline command substitution (`"$(_hostile_comment)"`). In bash, a failing command substitution passed as a command argument does not terminate the parent shell (even with `set -e`). If an unrecognised corpus name is passed, `_hostile_comment` will print to stderr and exit 2, but `jq` will run successfully with an empty `comment`, yielding a valid JSON envelope and allowing the test to silently proceed with empty data. To enforce the non-zero exit, isolate the substitution into an explicit variable assignment before calling `jq` (e.g., `COMMENT="$(_hostile_comment)" || exit 2`).

## Should-fix
None

## Nit
None
