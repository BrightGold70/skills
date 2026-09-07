## Summary
The plan addresses all six source-spec functional requirements with concrete scope, deliverables, tests, and mutation-backed verification. Axis C reconciliation is complete at FR granularity, but the FR-6 caller pseudocode has a type-critical omission relative to its own API contract and the paired design.

| Spec item | Classification | Plan coverage |
|---|---|---|
| FR-1 | implemented-as-written | Explicit tagged-fence extraction, heading addressing, and the authoritative bounder are planned. |
| FR-2 | implemented-as-written | Explicit, simultaneous substitution with refusal paths is planned. |
| FR-3 | implemented-as-written | Disposable execution, declared shell modes, streams, preamble, and cleanup are planned. |
| FR-4 | implemented-as-written | Verdict-line grammar, exit partition, and registry parity are planned. |
| FR-5 | implemented-as-written | Pre-spawn validation and bounded process-group handling are planned. |
| FR-6 | implemented-as-written | The single tagged migration, retained non-executing scan, and bidirectional wire checks are planned. |

## Must-fix
- FR-6’s caller-change pseudocode omits the required tuple unpacking between `dbe.substitute(...)` and `dbe.run_block(...)` — the plan states that `substitute` returns `(Block, counts)` but then says to call `run_block(substituted_block, ...)` without defining `substituted_block`. This leaves the planned sequence type-incomplete and permits passing the tuple where `run_block` requires a `Block`; the paired design and implementation plan correctly require `substituted_block, _ = dbe.substitute(...)` before the run. Make that binding explicit in this plan’s migration prescription.

## Should-fix
None

## Nit
None
