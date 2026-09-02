## Summary
The plan remains highly detailed, but it is not dispatch-ready: one prescribed mutation is behaviorally equivalent, and live count/cross-document surfaces still contradict their authoritative sources. The core production algorithm is otherwise coherent, with the remaining non-blocking gaps concentrated in verification safety and fixture precision.

## Must-fix
- `tail-empty-guard-dropped` is behaviorally equivalent after v1.17 changed the type fallback to `else empty` — for a missing tail, both the prescribed filter and the mutant emit zero bytes and `jq -e` exits 4 (verified as a controlled pair), because the downstream type branch discards `null` either way. The named AC-2.3 test therefore cannot kill this mutant, so AC-6.9 cannot reach `MUTATION: ALL_CAUGHT`; the plan and design also falsely call `// empty` independently load-bearing, violating Test discrimination. Remove the redundant mutant/claim or replace it with a mutation that actually changes accepted behavior.
- The live RED-count instructions still annotate the authoritative row-count command as `# 38 total nodes` and discuss feeding `27/11`, while the same document's table and the command itself produce 40 nodes, 29 FAIL, and 11 PASS — this directly contradicts the v1.17 claim that the count sweep was completed and breaches the Counts-a-dispatch-reports invariant. Correct every non-history count surface to 40 / 29 / 11.
- The paired design's Components table still reports `14 ACs`, and its 14-row Test Plan omits spec v1.8 AC-4.4, although the spec contains 15 ACs and explicitly adds the `ok:false`/non-array safety cases — this is a stale cross-document contract and count-invariant breach. Update the design count and add the missing malformed/error-envelope scenario, mapped to the implementation plan's AC-2.9 and AC-2.10 coverage.

## Should-fix
- The live verification clears the repository's real pin file but never snapshots/restores prior pins or uses an isolated `HMAD_ORCA_PIN_FILE` — a successful check can erase operator state unrelated to the feature. Run against a dedicated temporary pin path, or preserve and restore the original file with separate state re-reads.
- AC-3.6 does not explicitly require title and preview evidence to be blind in its Pass-0 fixture — after `wire-force-fire-after-pass0` disables Pass 0, Pass 1 or Pass 2 could still resolve before the tail pass, leaving the required force-direction mutation alive. Pin a generic/nonmatching title and empty or nonmatching preview so the mutant necessarily reaches `terminal read`.

## Nit
None
