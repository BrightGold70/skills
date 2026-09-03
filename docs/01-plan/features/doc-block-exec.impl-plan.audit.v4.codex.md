## Summary
The plan is unusually concrete, and the documented suite-floor baseline is reproducible (the stated root-level collection currently reports 2747 tests). Two incompatible implementation contracts remain: one across the paired documents and one in the fault-injected cleanup tests.

## Must-fix
- Task ownership of `RunResult` conflicts across the paired documents — this impl-plan requires the frozen dataclass in Task 1 (and makes Task 3 depend on it), while the paired design’s Implementation Order says Task 3 lands `run_block` **and `RunResult`**. That gives the TDD tasks incompatible file/type states; choose one placement and synchronize the design, plan, Task 1 code structure, Task 3 dependency, and RED narrative.
- The injected-cleanup tests do not specify a usable teardown after monkeypatching `dbe.shutil.rmtree` — `dbe.shutil` is the process-global `shutil` module, so the stated “removed by the test” cleanup will still call the raising/no-op fake. In particular, name a `real_rmtree = shutil.rmtree` binding before the patch and require it for the retained-cwd cleanup in `test_cleanup_readback_catches_silent_retention`, `test_cleanup_failure_outranks_timeout_injected`, `test_chmod_rollback_failure_is_cleanup_failed`, and any other failing-rmtree case; otherwise the tests leak state or cannot verify their own cleanup.

## Should-fix
- `test_extract_has_no_fence_state_of_its_own` is specified to allow `in_fence` and `marker` in only `_fence_events`, yet the declared `_FenceEvent` exposes `marker` and `extract` must distinguish a backtick opener from a tilde opener. Specify a scanner-derived eligibility field (or narrow the source predicate to grammar creation rather than consumer reads) so the implementation and its anti-duplication guard are simultaneously satisfiable and robust.

## Nit
None
