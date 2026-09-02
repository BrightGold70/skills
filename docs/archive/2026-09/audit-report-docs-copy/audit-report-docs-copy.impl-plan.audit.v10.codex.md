## Summary
The impl-plan is generally coherent with the paired design and the repository’s current collector/gate/wrapper structure. I found one hard output-contract mismatch in the mutation acceptance criteria, plus smaller exact-token/clarity drift that should be tightened before implementation.

## Must-fix
- `docs/01-plan/features/audit-report-docs-copy.impl-plan.md` AC-6.3 requires the mutation harness to print `MUTATION: ALL_CAUGHT mutations=23 caught=23 survived=0 refused=0`, but the current `h-mad/scripts/h_mad_mutation_harness.py` always appends `unreadable=<n>` on measured mutation verdicts (`... refused=0 unreadable=0`) — the plan’s required evidence line cannot be produced by the existing harness unless an out-of-scope harness change is made, violating assumption-verification/output-shape accuracy. Update the AC to include `unreadable=0` or relax it to a prefix/token check.

## Should-fix
- Task 3’s blanket marker AC says every exit path prints `[H-MAD] <feature> collect <verdict|usage_error|operational_error|readback_failed>`, while the code structure explicitly says argparse `SystemExit` prints `[H-MAD] unknown collect usage_error`; missing `--feature` cannot supply `<feature>`. Tighten the final AC to `<feature|unknown>` or call out argparse paths separately so exact-token tests do not inherit an impossible placeholder.
- The parent plan still says transport-gate refusals emit `[H-MAD] <feature> gate INVALID`, while the audited design and impl-plan intentionally use the dot-free transport `<stem>`. This is not blocking for the impl-plan because its Task 2 contract is correct, but the stale source-plan wording can mislead cross-doc readers and future sweeps.

## Nit
- The paired design’s Version History order is visually mixed (`v1.17`, `v1.16`, `v1.0`, then `v1.15`...), which makes the impl-plan’s “newest Version History entry” phrasing harder to audit by inspection even though the highest version is still identifiable.
