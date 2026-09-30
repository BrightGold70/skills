# Architectural Review: tdd-gate-fail-opens

## Summary
The implementation successfully creates the single-source path identity canonicaliser, integrates it into both TDD gates, establishes appropriate workflow limits for shell commands, and correctly implements the bounded judge reap. However, the Codex gate violates the single-source contract by duplicating resolution logic.

## Violations & Defects

### Cross-module Coupling / Pattern Violations
**Defect: Duplicated Hard-link Resolution in Codex Gate**
In `h-mad/hooks/h-mad-codex-tdd-gate.py` (`_main_guarded` lines 461-474), when a target resolves to `unresolvable=True`, the gate attempts to perform its own `os.stat` and `os.scandir` loop to find non-symlink names and mutate the `component` string before returning a `judge-error` refusal.
This violates the **"Single-source contract. One canonicaliser for both gates."** The canonicaliser (`h_mad_target_identity.py`) is the sole authority on resolving these paths. The gate must not reimplement `os.scandir` to mutate the component. As specified in the design, the gate branches only on `unresolvable` and should use the `component` exactly as provided by the identity record.

### Invariant Compliance (Axis B)
- **Stdlib Only:** `h_mad_target_identity.py` successfully relies exclusively on standard libraries (`os`, `fcntl`, `stat`, `typing`).
- **Filesystem Abstractions:** `os.open` is used correctly without `O_SEARCH` or `ALLOW_MISSING`. `fcntl.F_GETPATH` is used correctly.
- **Judge Reap / Errors:** Both `judge-error` and `judge-timeout` deny types are correctly routed and reported without being swallowed.
- **Resume Oracle:** `h_mad_resume_decision.py` correctly handles the `--session-id-from-git-dir` token before evaluating `decide`, acting as a safe-listed path.

### Dead Code / Unused Imports
No dead code or unused imports detected. 
- All imports in `h-mad-codex-tdd-gate.py` are properly used (e.g. `stat` used for `_read_regular_text` and `os` / `shutil` properly routed). 

### Security / Safety
- The `SIMPLE_SHELL_COMMAND` allowlist and read-only / script verifications in the Codex gate safely limit Bash functionality during `step5`.
- Bounded run implementation effectively cleans up process groups (`os.killpg`) before hitting the final `REAP_GRACE_S` window, successfully preventing runaway subprocesses from avoiding timeouts.

ASSESSMENT: WITH_FIXES
