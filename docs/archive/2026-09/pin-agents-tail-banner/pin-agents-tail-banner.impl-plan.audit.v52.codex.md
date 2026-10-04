## Summary
The impl-plan is mechanically consistent on the core surfaces I checked: the embedded mutation JSON parses at 46 entries, all mechanisms name their pinned nodes, the RED table re-derives to 45 nodes with the advertised 32/13 split, and the prescribed matcher passes the 36/12 corpus. I found one hard verification gap in the mutation-run command path.

## Must-fix
- `docs/01-plan/features/pin-agents-tail-banner.impl-plan.md:2161`, `:2329`, and `docs/02-design/features/pin-agents-tail-banner.design.md:452` invoke `h_mad_mutation_harness.py` by basename for the required mutation run, but that command is not on `PATH` here and the repo script exists as non-executable `h-mad/scripts/h_mad_mutation_harness.py`; running the basename form exits 127 and cannot print `MUTATION: ALL_CAUGHT`. This contradicts the adjacent AC-6.10 rule that the harness path is repo-relative and leaves the required mutation-verdict verification unexecutable as written.

## Should-fix
None

## Nit
- Task 2's `_agent_tail_re` comment repeats the prefix constraint twice in the same "Now:" sentence; it is harmless, but trimming the duplicate would reduce future drift.
