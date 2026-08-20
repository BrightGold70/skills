## Summary
The implementation plan is exceptionally rigorous, meticulously carrying forward all design constraints and presenting a bulletproof verification strategy with 12 bidirectional connection mutations. Two issues remain: a test name that contradicts its required end-to-end assertion, and a Bash syntax error that will crash the verb if the dispatcher sits at the global scope.

## Must-fix
- Contradictory test name vs. behavior (Task 4) — The AC dictates that `test_combine_invalid_yields_unverified` must assert the end-to-end `AUDITCYCLE: UNVERIFIED reason=no_gate_sections:p<i>` string, but the `test_combine_` prefix strongly implies a unit test of the `combine()` function (which only returns a tuple, not the final formatted string). Given the plan's explicit warning that `combine()` unit tests bypass `main()`-level logic, this naming is misleading and contradicts its required end-to-end scope. Rename it to `test_main_invalid_yields_unverified` to match the convention established by `test_main_delivered_none_is_unverified`.
- Fatal Bash syntax error at the global scope (Task 5) — The shell code block dictates `local here="..."` for resolving the script directory. In Bash, the `local` keyword is strictly forbidden outside of a function. Because the `audit-cycle)` block is injected directly into the main dispatcher, executing `local` at the top level will instantly crash the script with `bash: local: can only be used in a function`. Use a standard assignment `here="..."` without the `local` keyword.

## Should-fix
None

## Nit
None
