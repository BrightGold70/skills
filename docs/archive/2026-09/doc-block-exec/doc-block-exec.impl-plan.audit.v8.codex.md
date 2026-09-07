## Summary
The plan is unusually concrete, but two specified mechanics cannot satisfy their stated contracts as written. One can scan into an adjacent section, and the other makes its own mutation-isolation assertion false.

## Must-fix
- `fence_aware_end` is required to consider a boundary only at a line start **strictly after** `start`, while `find_heading` returns `start` immediately after the selected heading line. If the next same-or-shallower heading is immediately adjacent, its line starts exactly at `start`, so it is skipped; `extract` can then include and execute a tagged fence belonging to that next section. Define the boundary predicate to include the first line beginning at `start` (while still excluding a line that began before an arbitrary mid-line offset), and add an adjacent-heading extraction/bounder test and mutation coverage.
- The prescribed `docsections-delegation-reverted` replacement defines a local `_dbe` with only `fence_aware_end`, but the migrated `titled_section` also calls `_dbe.find_heading`. Thus the mutant raises `AttributeError` in every `titled_section` consumer, contrary to the repeated requirement that all helper behaviour tests remain green except the source guard; it also no longer isolates the delegation wire. Give the shim a behavior-compatible local `find_heading` (or mutate both calls coherently) so the WIRE-PIN is the intended failure and state the exact one-test harness binding.

## Should-fix
- `final-write-close-not-in-finally` is specified as killed by two tests although each mutation row is required to carry one full-node-ID `test` key. Select and record the canonical killer (the other may remain a regression test), so the JSON contract and the claimed 62-row accounting are unambiguous.

## Nit
None
