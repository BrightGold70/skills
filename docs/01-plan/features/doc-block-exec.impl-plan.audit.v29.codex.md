## Summary

The implementation plan is unusually concrete about task ordering, wire-only reverts, type-correct mutation payloads, and verification gates. I found no plan-internal blocker, but its paired design/plan still contain stale parser-test wording and a divergent preamble-test name.

## Must-fix

None

## Should-fix

- Align the paired design's `allow-abbrev-restored` mutation-table entry with Task 4: it still says the abbreviation “must be a usage error,” while the plan requires one `DOCBLOCK: BAD_ARGS message=…` line, exit 0, and no argparse usage text — this is a cross-document expected-outcome ambiguity for the same named test and mutant.
- Reconcile the unreadable-preamble test name in the paired plan (`test_cli_unreadable_preamble_refuses_before_running`) with this implementation plan's `test_unreadable_preamble_path_refuses` — the plan should name one canonical node so implementers and later mutation/review references do not split coverage.

## Nit

None

