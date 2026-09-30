## Architectural Review: tdd-gate-fail-opens

### Cross-module coupling violations
- **No violations:** The implementation adheres strictly to the single-source contract by placing the path resolution logic in `h_mad_target_identity.py`. Both Claude and Codex gates use this module (`emit_canon` via Python subprocess in bash, and `_load_identity` within Python). Dependencies are clear and no circular imports exist.

### Pattern violations
- **No violations:** The new modules and scripts follow the established stdlib-only requirement. `h_mad_resume_decision.py`'s argparse changes, as well as `h_mad_tdd_judge.py`'s `BoundedRun` and `reap_failed` logic, perfectly align with the project's explicit error handling and structure conventions. 

### Invariant compliance
- **Axis B Compliance:** The design ensures that failure modes are fail-closed. Empty spellings, bad parse structures, and unresolvable components explicitly yield `judge-error`. The prompt's strict time bounds (`GIT_DIR_BOUND_S = 10.0` and `REAP_GRACE_S = 1.0`) are met and rely only on Python's built-in `timeout` and `killpg` instead of external shell tools, respecting portability.
- **Documentation:** The changes appropriately update `codex-runtime.md`, `agy-runtime.md`, `grok-runtime.md`, and `SKILL.md` (specifically, integrating `judge-timeout` and simplifying the empty-id oracle prose).

### Dead code and unused imports
- **None found:** The imports in the new files (`fcntl`, `os`, `stat`, `subprocess`) are all active. The `TargetParse`, `BoundedRun`, and `Identity` named tuples are properly unpacked and utilized.

### Missing integration tests
- **Comprehensive coverage provided:** Both gates have detailed wire connection tests (testing canonicalise removal, `fold_py_suffix` bypass). The cross-gate differential correctly enforces parity constraints with `test_h_mad_tdd_gate_differential.py`. Shell and subprocess detachment corner cases are verified under the budget constraints.

### Security and safety
- **No violations:** `canonical_directory` operates safely by opening files with `O_RDONLY` and executing `fcntl.F_GETPATH` without `O_NOFOLLOW` explicitly for symlinks, accurately extracting underlying referents. Inputs from patches and paths are safely validated without expanding scope. No new OS traversal exploits were introduced, and authorization checks remain strictly intact.

ASSESSMENT: READY_TO_MERGE
