## Summary
The implementation plan is substantively consistent with the paired spec/design and passes the cheap structural checks I re-derived: 45 RED-table nodes at 32/13, 46 embedded mutations with mechanisms, balanced line-start fences, and the prescribed matcher block passes the 36/12 corpus under `grep -Ei`. I found no blocking invariant breach, but two stale accounting/provenance surfaces should be cleaned up before dispatch so readers do not follow the wrong revision or proof inventory.

## Must-fix
None

## Should-fix
- `docs/01-plan/features/pin-agents-tail-banner.impl-plan.md:3-4` cites the paired design as v1.38 and spec as v1.19, but the checked-in paired files now end at design v1.39 and spec v1.20 — the substantive content appears synchronized, so this is not a hard gate, but stale provenance keeps sending reviewers to the wrong source revision.
- The AC-6.12…AC-6.20 paragraph says there are "NINE proofs across seven nodes" and enumerates only a subset, while the authoritative Test-name contract table lists 13 green-at-RED rows and the embedded JSON maps 16 mutations to RED:PASS nodes — this is not currently a coverage hole because the table and JSON are correct, but the paragraph is a stale competing inventory and omits proofs such as `stub-read-env-not-array`, `stub-read-dir-writes-one-file`, `resolve-on-ge-1`, `wire-force-fire-after-pass0`, `pool-whole-listing`, `rival-re-prose-unsafe`, and `wire-rival-matcher-forced-empty`.

## Nit
- AC-3.2's rationale says the old form asserted "banner-only also resolves"; the AC is about launch-command-only tails, and banner-only is supposed to resolve, so this should say "launch-only" to avoid a local contradiction.
