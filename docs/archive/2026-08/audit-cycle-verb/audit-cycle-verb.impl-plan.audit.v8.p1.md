## Summary
The plan is exceptionally thorough, demonstrating a deep understanding of shell mechanics, process isolation, and adversarial edge cases. The test strategy and mutation harness design are rigorous. However, there are three critical shell execution (`set -e`) and routing flaws in Task 5 that bypass custom error handling and incorrectly convert valid verdicts into operational crashes.

## Must-fix
- Task 5, Step 4: `set -e` bypasses the `arc=$?` operational error routing — The script runs under `set -euo pipefail`. If `h_mad_assemble_audit.py` exits non-zero (e.g. an internal failure), `set -e` will immediately abort the bash script with that exit code. The subsequent `arc=$?` and `[ "$arc" -eq 0 ] || exit 4` lines are bypassed, failing AC-2.4 (which requires `exit 4`). Fix by suppressing the abort during capture (e.g., `if python3 ... >"${asm[$i]}"; then arc=0; else arc=$?; fi`).
- Task 5, Step 4: Unconditional prompt existence check crashes valid `HALT` verdicts — The `[ -s "${prompt[$i]}" ] || exit 4` check runs for *every* assembly token. If `h_mad_assemble_audit.py` legitimately emits `ASSEMBLE: HALT` without writing a usable prompt file, this `-s` guard will trip and trigger an `exit 4` crash. This breaks AC-2.2 by converting a valid halt verdict into an operational error. Fix by guarding the check to apply only to `PASS` tokens.
- Task 5, Step 3: `set -e` bypasses unremovable path error handling — Unguarded `rm -f` commands will exit non-zero if a file cannot be removed due to permissions (e.g. read-only parent). Under `set -e`, this immediately aborts the script (exit 1), entirely bypassing the explicit `[ ! -e "$p" ]` assertion block designed to catch this and emit `exit 3`. This fails AC-3.3's `test_verb_unremovable_path`. Fix by appending `|| true` to the `rm -f` commands so execution reaches your custom assertions.

## Should-fix
- Task 5, Steps 6 & 7: No-pass routing omits context arguments — The plan explicitly claims "Every context arg is forwarded unconditionally, including in no-pass mode". However, the code blocks for the `assemble_halt` and `prompt_divergence` invocations omit `--grace` (and `--ack-file`). While harmless because `collect()` isn't executed on these paths, it contradicts the stated design constraint and creates signature inconsistency.

## Nit
- None
