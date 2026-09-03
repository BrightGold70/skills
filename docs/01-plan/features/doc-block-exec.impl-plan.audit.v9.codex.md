## Summary
The plan is unusually concrete, but its heading-address API is internally inconsistent at the two intended consumers. That inconsistency makes the Task 5 gate resolver select no block under the stated scanner semantics.

## Must-fix
- The `heading` representation is contradictory — Task 1 says `_fence_events` compares parsed ATX heading text (with the opening hashes absent; the existing `docsections.titled_section` contract explicitly takes text after the hashes), and its delta passes the bare `"Section"`; yet AC-1.5 calls `extract`/`find_heading` with `"## A"`, while Task 5 hard-codes `"## Second surface — the codex leg"` in `_gate_block` and its WIRE-PIN. With the stated event text, those marked strings cannot match the real heading text, so `extract` returns `[]`, `select` raises `BlockNotFound`, and the required migrated recipe cannot run. Choose one canonical input form and update the public docs, ACs, CLI fixtures, `docsections` wire, and Task 5 call/pin together (the least disruptive form is plain heading text, changing Task 5 to `"Second surface — the codex leg"`).
- `_FenceEvent` has no source-span/offset field, although `find_heading` must return the exact offset after a heading and `fence_aware_end` must return an exact boundary offset using the `>= start` rule; the plan simultaneously says consumers read only the listed event fields. `lineno` plus the listed metadata cannot recover character offsets for variable-width/CRLF input without a second line walk outside that contract. Add explicit `start`/`end` offsets (or an equally explicit source-span contract) to `_FenceEvent`, require `_fence_events` to populate them, and update the event-trace expectation so both public consumers can meet their declared signatures without re-tokenising source positions.

## Should-fix
- Make `wire-revert-run`'s replacement self-contained — after `_run_recipe` is hoisted, the current consumer imports `subprocess` only inside `test_documented_gate_recipe_halts_instead_of_gating_an_empty_path`, while the planned module-level `_run_recipe` has no such import. State that the mutant includes a local/module import (or add the normal module import) so its WIRE-PIN fails on the missing `dbe.run_block` record rather than an unrelated `NameError`.

## Nit
None
