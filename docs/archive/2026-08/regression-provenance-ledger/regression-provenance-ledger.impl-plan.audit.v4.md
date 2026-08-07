## Summary
This plan rigorously translates the design into verifiable tasks, successfully passing all pure-core constraints and invariant mutation checks. The remaining gaps are localized to the AST challenge's `git diff` filter omitting renamed files, a missing AC for unresolvable claims, and an unstated assumption on how the 5b gate acquires the active feature name.

## Must-fix
- Task 6 `git diff` filter misses renamed files (Gap / Assumption violation) — `--diff-filter=AM` includes only Added and Modified files. If git rename detection is active (which emits `R`), renamed files will be completely excluded from the AST challenge, allowing a rename to silently introduce unverified cross-boundary calls. The filter must be `--diff-filter=d` (exclude deleted) or `--diff-filter=AMCR`.
- Task 6 lacks an AC for unresolvable claims (Test discrimination) — The description explicitly states that an unresolvable claim (a plan path failing to match a changed file) is reported as `unattributed` and named. However, AC-5.1c only asserts this for "a changed file claimed by NO task." An AC must be added to enforce that dangling claims are also counted and reported.

## Should-fix
- Task 5 `feature` string acquisition is unstated (Unstated assumption) — `_register_wiring_tasks` requires `feature: str` to populate the `owning_feature` field, but the plan does not specify how `h_mad_wire_pin_gate.main()` acquires this string. State whether it parses the feature name from the plan's filename or requires a new `--feature` CLI flag.

## Nit
- Task 6 git command execution — Ensure `git diff` is explicitly executed with `cwd=repo` so the `'*.py'` pathspec reliably matches from the repo root rather than the caller's working directory.
- Task 6 ambiguous module reporting — The AC states an ambiguous module stem is "reported rather than silently resolved," but does not specify how (e.g., standard warning to stderr vs a distinct count). Clarifying the output shape prevents test ambiguity.
