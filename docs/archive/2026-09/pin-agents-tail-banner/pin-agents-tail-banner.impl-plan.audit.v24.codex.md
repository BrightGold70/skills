AUDIT-pin-agents-tail-banner-impl-plan-v24-BEGIN
## Summary
The prescribed production flow, 29-entry mutation JSON, 290-test baseline, and 40-node 28/12 RED split are otherwise coherent. Two stale count/proof descriptions remain, one inside Task 6 and one in the declared source plan, and the latest live-check cleanup was not back-propagated.

## Must-fix
- Task 6's “Six mutations target T2's time-and-extraction controls” paragraph is internally impossible after `tail-empty-guard-dropped` was removed — the family the paragraph itself enumerates now has five mutations (`tail-array-not-joined`, `timeout-default-dropped`, `time-bound-removed`, `timeout-override-ignored`, and `harness-ambient-timeout-not-scrubbed`), four in the wrapper and one in the Python harness, targeting three RED nodes (AC-2.1, AC-2.5, AC-2.6); the same paragraph nevertheless says six, five in the helper, and four nodes, while “removing any one leaves the other four” correctly implies five. This breaches the Counts-a-dispatch-reports invariant and leaves an implementer unable to tell whether a mutation is missing or the prose is stale.
- `pin-agents-tail-banner.plan.md` reports 12 green-at-RED nodes but says only that “each of the 11” is tied to a mutation, never accounting for the twelfth — the impl-plan's authoritative table shows 11 mutation-backed nodes plus `test_tail_no_timeout_binary_invocation`, whose reject direction is the AC-2.8 insert/observe/remove procedure. Leaving the declared source plan one proof short contradicts the paired design and the impl-plan and creates a Test-discrimination gap on that surface; state the 11-plus-1 split explicitly.

## Should-fix
- The impl-plan now requires removal of the isolated pin file's `mktemp -d` directory, but the source plan and paired design still end the live check after terminal cleanup — back-propagate the temporary-directory cleanup so following either upstream document does not leak one directory per run.

## Nit
None
AUDIT-pin-agents-tail-banner-impl-plan-v24-END
