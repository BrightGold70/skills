AUDIT-regression-provenance-ledger-impl-plan-v2-BEGIN
## Summary
The implementation plan is extremely thorough, accurately adopting the design's verifier core, I/O shell split, and conditional subprocess logic. It correctly integrates the Phase 6a-prime grammar amendments for missing halt markers. However, it misses a critical filtering step in the AST challenge that would create massive false-positive noise, and overlooks the explicit mutation harness requirement for the conftest guard.

## Must-fix
- Task 6 omits filtering `git diff` to production paths — The design explicitly states "filtered to production paths (test paths are never challenged)". By omitting this, test files modified in the PR will be passed to attribution, fail to match any `Production file` claims in the plan, and be loudly reported as `unattributed` on every run, creating false-positive noise. (Axis A: Contradiction / Gap)
- Task 1 J18 AC omits the `h_mad_mutation_harness.py` requirement — The J18 AC verifies the guard by running a test that re-introduces the leak, but the Invariants explicitly require that "Every new guard is mutated to its permissive value, including the doc guards and the conftest guard, via `h_mad_mutation_harness.py`". The guard itself must be mutation-tested to prove it is not decoration. (Axis B: Mutation verification)

## Should-fix
- Task 6 lacks an AC for unresolvable AST targets — The description correctly states that unresolvable targets (stdlib, third-party) are skipped, but there is no Acceptance Criterion to verify this behavior (e.g., asserting that calling a stdlib function does not trigger a challenge or crash).
- Task 1 defines `register` for a single entry (`entry: dict`) instead of a batch (`entries: list[dict]`) — The Design specified `register(entries, path)` to imply a batch write. A singular entry signature means `_register_wiring_tasks` will read, update, and write the `.jsonl` file N times in a loop, which is an O(N) I/O operation.

## Nit
- None
AUDIT-regression-provenance-ledger-impl-plan-v2-END
