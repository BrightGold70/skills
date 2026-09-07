+## Summary

The plan covers every functional requirement, but its claimed mutation discipline is not executable as written: two planned source guards have no corresponding mutation row or named RED binding. Repository checks confirm the cited current consumers (two bare-fence extractors and the duplicate bounder) and the 68-fence census.

| FR | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

## Must-fix
- The implementation plan’s “every guard … carries a mutation row” claim is false for two load-bearing guards: `test_no_mktemp_invocation_in_source` and the `allow_abbrev=False`/abbreviated-option rejection. The 63-row list contains `timeout-invocation-planted` but no shell-`mktemp` mutant, and no `allow_abbrev` mutant; neither the plan nor design assigns either test a mutation-spec `test` binding. Add exact-once mutations that introduce each prohibited behavior and bind them to the respective named test, then require their observed RED result. Without that, the base Mutation verification/Test discrimination invariant and the plan’s own guard-mutation promise are unmet.

## Should-fix
- Cross-document test naming drifts: the plan names `test_cli_rejects_abbreviated_options`, while the implementation plan specifies `test_parser_rejects_all_dir_and_abbreviations`. Choose one name and use it on both surfaces so the planned evidence remains directly traceable.

## Nit
None

