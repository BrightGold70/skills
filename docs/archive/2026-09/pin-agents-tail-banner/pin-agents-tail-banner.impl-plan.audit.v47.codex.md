## Summary
The structural checks re-derive cleanly: the RED table has 45 nodes (32 FAIL / 13 PASS), the embedded JSON has 43 uniquely named mutations with mechanisms, and the existing module still collects 290 tests. The new per-arm coverage exposes one blocking mutation-discrimination gap, while two carried count/provenance claims are stale.

## Must-fix
- The version revert-mutants change multiple independent guards at once — `tail-re-version-loosened` simultaneously unpairs Codex parentheses and loosens dottedness in both parenthesized and bare versions, while `tail-re-version-loosened-agy` loosens the CLI-version and Gemini-parenthetical positions together. A corpus-node failure proves only that at least one changed guard bit; it cannot prove each independently encoded guard, directly contradicting the plan's one-control-per-mutation rule and the base Test-discrimination invariant. Split these into positive-preserving mutations that vary one field from the shared arm anchor; the Codex corpus also needs a parenthesized non-dotted probe such as `OpenAI Codex (v2026)` to discriminate that occurrence.
- The two unanchored-matcher mechanisms report false corpus counts — `tail-re-unanchored` mutates only the Codex arm but claims all 35 negatives match, while `tail-re-unanchored-agy` still says 10 AGY probes although the current table contains 21 Codex and 14 AGY negatives. AC-6.9 requires mechanism lines to describe what their own mutant demonstrates, and the base count invariant forbids carrying these unrederived figures; update them to the per-arm 21/14 effects after executing the mutants.

## Should-fix
- The provenance header cites design v1.37, but the paired design now ends at v1.38 after the same commit added the per-arm mutation rationale — update the source revision so dispatch uses the document this plan actually depends on.

## Nit
- The design's case-fold paragraph still says “all three wire mutations,” but the embedded spec now has four matcher-wire mutations (wanted/rival, disconnect/force); avoid the stale tally or name the intended set.
