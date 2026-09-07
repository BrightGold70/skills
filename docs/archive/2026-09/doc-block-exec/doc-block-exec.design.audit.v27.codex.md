## Summary
The design covers every supplied acceptance criterion as written; its one authoritative bounder and the explicit wire mutations are consistent with the plan. Two implementation-critical verification gaps remain: the AC-2.6 mutation has no observable discriminating outcome, and successful stream artifacts are never read back despite the design promising that they exist.

| AC identifiers | Classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-1.8, AC-1.9 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.7, AC-2.8 | implemented-as-written |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7, AC-3.8, AC-3.9, AC-3.10, AC-3.11, AC-3.12, AC-3.13, AC-3.14 | implemented-as-written |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | implemented-as-written |

## Must-fix
- AC-2.6's `replacement-sequential` mutation is not discriminated by its stated fixture — the design says `substitute` first refuses any missing key, yet its test uses only `A` with `A→B, B→C` and says it both yields `B` and reports `SUBST_MISSING key=B`. A conforming API raises `MissingSubstitution` before returning a `Block`, and a sequential implementation that performs the same precheck raises identically; the proposed mutation therefore need not make the named test RED, violating the Mutation verification and Test discrimination invariants. Use a fixture where both original keys occur (for example `A B`) and assert simultaneous output `B C` in both map orders; the sequential order then produces a distinguishable wrong result.
- Successful stream artifact writes are not verified after mutation — the design promises that a spawned block is reported only when every promised artifact exists, but `_final_write` only seeks/truncates/writes/flushes/closes and `main` immediately emits `RAN`; it never re-reads the artifact to establish existence and exact content. This violates the Mutation verification invariant and permits a successful no-op/stale-write mutant (or a disappeared artifact) to be reported as a measurement. Specify a post-close read-back and byte/text comparison for each requested artifact, map a missing/mismatched artifact to `stream_write_failed`, and add a named mutation/test that makes the final writer succeed without producing the expected artifact.

## Should-fix
None

## Nit
None
