## Summary
The task chain, 38-node RED table, and caller/callee wiring are internally well developed, but the plan is not dispatch-ready. It uses an impossible runtime fixture, leaves several explicitly load-bearing helper guards without discriminating mutations, and carries a stale current-suite count.

## Must-fix
- AC-3.16 requires a stubbed tail with at least 3,000 lines even though the spec, design, and pass comment establish that Orca hard-caps `.terminal.tail` at 2,000 lines — this violates the base invariant that a stub model the state the real system consumes. Keep the SIGPIPE discriminator at at least 200 KB, but build it within the measured 2,000-line cardinality (and use the same realizable shape for AC-4.5).
- Task 6 says every new guard is mutated to its permissive value, but its 19 mutations do not exercise the array `join("\n")`, the independent `// empty` guard, the `${HMAD_TAIL_READ_TIMEOUT:-2}` default, the `_cmd_run` bound/override, or the new ambient-environment scrub. AC-2.1 is also too weak: bare `jq -r '.result.terminal.tail'` prints `alpha` and `beta` on separate lines inside pretty-printed JSON, so “contains both … on separate lines” accepts the exact wrong extraction the plan warns about. Require exact `alpha\nbeta\n` output, add one mutation per independent extraction/time control, and make the scrub test seed an ambient timeout so deleting `e.pop("HMAD_TAIL_READ_TIMEOUT", None)` observably fails; otherwise these guards breach Test discrimination.
- The plan reports “284 existing tests” in four live statements, but a read-only collection of `h-mad/tests/test_hmad_dispatch.py` currently yields 290 tests (`-k` confirms 0/290 for the feature selector and 2/290 for the broad `tail` selector) — the base Counts invariant requires re-deriving reported counts. Update all four live sites or replace the carried count with a collection command/result.

## Should-fix
- Task 6 first says `"../.."` resolves to the repository root, then correctly says it resolves from `h-mad/tests/mutation-specs/` to the `h-mad/` skill directory and warns not to use repo-root paths — correct the first statement so the anchor base has one meaning.
- The SIGPIPE rationale says every fixture is short and all 38 nodes would pass the broken pipeline, but AC-3.16/AC-4.5 and their two pipeline-reversion mutations are explicitly long-tail discriminators. Recast this as the pre-regression-test failure mode rather than a current property of the plan.
- AC-2.6 calls its evidence “Ten trials” but lists only eight timings, and the helper's prescribed comment says `timeout`/`gtimeout` are “absent from this file” although the repaired contract is only that they are never invoked. Reconcile the evidence count and use the cross-document “never invoked” wording.

## Nit
None
