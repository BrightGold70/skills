AUDIT-pin-agents-tail-banner-impl-plan-v12-BEGIN
## Summary
The plan is close, but the new rival-side SIGPIPE regression node is not specified strongly enough to exercise the branch it claims to guard. The RED counts have also drifted on three nonhistorical surfaces, and the live pin-clear mutation is not directly verified.

## Must-fix
- AC-4.5 leaves the long-tail rival fixture vacuous — a tail carrying only the rival banner fails the preceding `$tail_re` check and never exercises rival rejection, while putting both banners early can make the wanted-signature pipeline fail first and still produce the expected decline. This also contradicts the table's `RED: FAIL`: a rival-only decline is green before the feature exists. Require a clean wanted-only candidate plus a ≥200 KB decoy carrying the rival signature first and the wanted signature near the end, then assert resolution to the clean candidate; in a controlled 243,028-byte probe that layout gave wanted-check rc 0 and rival-check rc 141, whereas putting both signatures early gave wanted-check rc 141. Without that exact fixture, the node does not satisfy the base Test-discrimination invariant or the previous audit's requested rival-branch regression proof.
- The load-bearing RED counts are stale on three active surfaces — the plan says the selector covers “all 35” nodes and later claims its commands were verified as `35 / 11 / 24`, while those commands actually return `37 / 11 / 26`; the paired design's Verification body likewise still says `24 of 35`. These contradictions violate the base Counts-a-dispatch-reports rule and can misconfigure 5d; update the nonhistorical plan and design surfaces to 37 total, 11 pass, and 26 fail.
- The live check runs `hmad-dispatch pin-agents --clear`, which mutates the pin file, but then verifies only that no `HMAD_ORCA_*_TERMINAL` environment variables are exported — that does not re-read the file that `rm -f` was meant to remove. Record the exact pin-file path and check its absence in a separate read before proceeding; otherwise the step violates the base Mutation-verification invariant and can silently retain the short-circuit the live check is trying to exclude.

## Should-fix
- AC-6.11 says the test asserts the exact root string `"../.."`, but its prescribed assertion only checks `not os.path.isabs(spec["root"])`; many other relative strings pass. Either assert `spec["root"] == "../.."` or narrow the AC to relative-only, so the claimed contract matches the test.

## Nit
None
AUDIT-pin-agents-tail-banner-impl-plan-v12-END
