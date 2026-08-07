AUDIT-regression-provenance-ledger-impl-plan-v5-BEGIN
## Summary
The implementation plan is exceptionally thorough and demonstrates deep adversarial reasoning against the design doc, correctly fixing bugs around `git diff` flags and verdict grammars. The code structures, pure/IO boundaries, and acceptance criteria are highly detailed and well-isolated. A critical missing link was found regarding how the 5b gate receives the `--feature` flag from the orchestrator, and a few minor clarifications around `git diff` rename handling and token counts are suggested.

## Must-fix
- Task 7 ACs miss updating the 5b gate invocation in `SKILL.md` to include the new `--feature <feature_name>` flag. Task 5 mandates that without `--feature`, the gate registers nothing. If `SKILL.md` doesn't explicitly instruct the agent to pass this flag, the orchestrator will omit it, resulting in a silent no-op where wires are never registered in production, defeating the entire feature (Axis A: unstated assumption / gap).

## Should-fix
- Task 6 uses `git diff --name-only`, which outputs only the new path for a renamed file. When `challenge` calls `git_show(base, new_path)`, it will return `None` (absent at BASE), causing the script to treat the renamed file as entirely new and flag every pre-existing cross-boundary call as an addition. Consider using `--name-status` or separating `--diff-filter=A` from `--diff-filter=R` to correctly trace the old path and parse the old AST, preventing a flood of false positives on renames.

## Nit
- Task 6's AC-5.1e relates dangling claims to the `unattributed=U` count, but it is slightly ambiguous whether `U` is the mathematical sum of both unclaimed changed files and unmatched claims, or if a separate count like `dangling=D` is needed. Clarifying this mapping in the token grammar will prevent implementation drift.
- Task 6's prose states `git_show(base, path)` is used to read BASE versions, but the signature defined in Task 3 is `git_show(sha: str, path: str, repo: Path)`. Ensure `repo` is passed at the call site.
AUDIT-regression-provenance-ledger-impl-plan-v5-END
