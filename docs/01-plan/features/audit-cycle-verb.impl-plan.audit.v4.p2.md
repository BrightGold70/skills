## Summary
The plan is exceptionally robust, strictly enforcing every architecture constraint, accurately specifying mutation specs, and demonstrating deep foresight into error routing and test discrimination. Three structural defects in the bash code blocks require correction to prevent literal transcription from causing unbound variable crashes or cross-platform execution failures.

## Must-fix
- Task 5 step ordering contradiction — Step 6 computes `size_status` but is physically placed *after* step 5, which uses `$size_status` in its `h_mad_audit_cycle.py` invocation (`--size-status "$size_status"`). This contradicts the doc's own comment ("computed before step 5 uses it") and will pass an unbound variable (empty string) to the helper during an assembly halt. Step 6 must be moved above step 5.
- Unassigned scalar variables in bash loops — In Tasks 5, 6, and 7, the per-pass loop bodies (steps 3, 4, 7, 8, 10) use scalar variables (`$report_i`, `$out_i`, `$prompt_i`, `$asm_i`). These are defined only in a comment in step 2 ("per pass i:") and are never assigned inside the loops. Bash does not dynamically evaluate `$report_i` based on the loop index `i`. A literal transcription will evaluate these to empty strings or stale values. Prescribe either reconstructing the paths inside every loop or using bash arrays in step 2 (e.g., `report[$i]="${stem}_p${i}.report.md"`).
- Cross-platform divergence failure (`seq 2 "$passes"`) — Task 5 step 7 uses `for i in $(seq 2 "$passes")` for the prompt divergence check. On macOS/BSD, `seq 2 1` counts backwards (yielding `2` then `1`). When `--passes 1` is used, the loop will run for `i=2`, causing `diff` to fail on a non-existent `$prompt_2` and erroneously halting the cycle with a prompt divergence verdict. Replace with a safe `while` loop (e.g., `i=2; while [ "$i" -le "$passes" ]; do ... i=$((i+1)); done`), consistent with the idiom already used in steps 8 and 9.

## Should-fix
None

## Nit
None
