## Architectural Review: Phase 5 - `regression-provenance-ledger` (Cycle 2)

**Base:** d3bab41
**Head:** 499e33e

### Verification of Previous Findings

All 4 findings from the previous cycle have been correctly addressed and verified in the source:

1. **`run_pins()` failing closed (Critical 1)**: Verified. `run_pins()` now explicitly checks `outcomes.get(pin) == "PASSED"`. Anything else (ERROR, SKIPPED, XFAILED, or absent) falls through to the `broken` list, and its specific reason is printed in the detail line. A skipped pin no longer reports as a silent verified pass.
2. **`register` CLI stub (Critical 2)**: Verified. The `register` CLI is fully implemented with `--id`, `--caller`, `--callee`, `--pin`, `--feature`, and `--registry` arguments. It calls `register()` cleanly, performs the write + read-back, and prints `WIREREG: REGISTER`.
3. **`--registry` not scoping BASE (Important 1)**: Verified. The `load_base` call now resolves the registry path relative to the repo via `_registry_base_path(registry, repo)`, correctly mapping custom registry paths onto their BASE counterpart.
4. **Hardcoded `--testpath h-mad/tests` (Important 2)**: Verified. `SKILL.md` now documents `<project-test-root>` instead of the hardcoded `h-mad/tests` path.

### Design and Code Quality

- **Cross-module coupling**: The `h_mad_wire_pin_gate` calls `h_mad_wire_registry` for registration which is correct and expected. `challenge` imports `_parse_tasks` inline to avoid circular dependencies and re-implementations, adhering to the single-source constraint.
- **Error Handling**: `RegistryError` encapsulates failure cases correctly, ensuring that tool parsing errors exit with `2` and are never silently confused with test/pin failures.
- **Subprocess Discipline**: The 2-pytest-invocation limit is strictly maintained, and git is called sparsely and safely.
- **Tests**: The additions in `test_h_mad_wire_registry.py` and `test_h_mad_wire_pin_gate.py` comprehensively cover the new failure modes and CLI operations.

### Conclusion

The fixes are correct, complete, and introduce no new invariant violations or regression gaps.

ASSESSMENT: READY_TO_MERGE
