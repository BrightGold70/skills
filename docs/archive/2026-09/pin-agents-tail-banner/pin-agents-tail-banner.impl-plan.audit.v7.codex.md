AUDIT-pin-agents-tail-banner-impl-plan-v7-BEGIN
## Summary
The implementation plan captures the intended pass ordering and most shell hazards, but it is not implementation-ready. Its private-function harness is nonfunctional as described, its test-discrimination procedure is unsatisfiable for already-green negative tests, and the mutation and upstream-document contracts still contain blocking inconsistencies.

## Must-fix
- The `run_fn` harness description is factually wrong and omits an executable body — with no positional arguments, the live wrapper's `main` takes the default case, prints `unknown verb ''`, and returns 2; with the function call in the shell's positional arguments, `source` passes those same arguments to `main`, so they do not make it a no-arg invocation. Under the wrapper's `set -e`, either shape prevents the requested private function from running unless the harness explicitly saves the call argv, clears argv while sourcing, neutralizes only the terminal `main` result, and then restores/invokes the saved function; T2's tests otherwise have no viable implementation path.
- The blanket “every new test fails against the unfixed wrapper” requirement cannot be satisfied — preservation and negative tests such as legacy stub behavior, launch-command-only decline, zero-match decline, rival-only decline, and unchanged frontmatter are already true before this feature exists. The plan must give each such test an explicit verified reject-direction mutation (or a per-test discrimination table distinguishing unfixed-code RED from guard-stub RED); otherwise it violates the base Test discrimination invariant while claiming a RED phase that will necessarily contain unexpected passes.
- The `jq-r-not-jq-re` mutation changes two independent controls — it removes `-e` and changes `// empty` to `// "null"`. Removing only `-e` already makes the missing-key path return rc 0 with empty output, so the proposed named-test failure cannot establish that the `-e` guard itself bit; isolate the flag change and leave the filter unchanged to satisfy mutation-mechanism attribution.
- The upstream documents remain internally inconsistent after AC-5.2 was added — the phase plan's Success Criteria still requires only 13 ACs and omits AC-5.2, while the design's Components table also says “13 ACs” although the paired spec has 14. More seriously, the phase plan's risk table says tail evidence proves what a pane “IS RUNNING,” contradicting the spec/design/implementation plan's accepted stale-pane behavior that tail is historical and may resolve an exited agent's shell; these stale count and safety surfaces must be reconciled before implementation.

## Should-fix
- Replace “the worst case stays a few seconds even on a busy pool” with the actual sequential bound (`candidate_count × HMAD_TAIL_READ_TIMEOUT`, plus overhead), or state a hard candidate cap — no current requirement bounds the scoped candidate count tightly enough to justify “a few seconds.”

## Nit
- Keep Task 3's ACs in numeric order; AC-3.15 currently appears before AC-3.13 and AC-3.14.
AUDIT-pin-agents-tail-banner-impl-plan-v7-END
