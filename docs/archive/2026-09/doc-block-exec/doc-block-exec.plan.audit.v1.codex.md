## Summary
Axis C reconciliation at FR granularity: | FR | Classification | Notes | |---|---|---| | FR-1 | implemented-as-written | Plan covers document + heading + explicit tag selection and excludes untagged fences. | | FR-2 | implemented-as-written | Plan covers explicit substitutions and refusal on missing anchors. | | FR-3 | implemented-as-written | Plan covers disposable cwd and fence-declared shell mode. | | FR-4 | implemented-as-written | Plan covers verdict-token CLI and cannot-judge handling. | | FR-5 | implemented-as-written | Plan covers bounded execution without `timeout`/`gtimeout`. | | FR-6 | implemented-as-written | Plan covers tagging the Second-surface gate block and migrating the existing inline harness. |
The plan tracks the spec at the FR level, but it leaves one base-invariant gap around proving the migrated call-site connection and one evidence gap around load-bearing measured claims.

## Must-fix
- The FR-6 migration is not covered by a connection-discrimination plan — the deliverables make `h-mad/tests/mutation-specs/doc_block_exec.json` satisfy only FR-1..FR-5, while the migrated `h-mad/tests/test_h_mad_collect_report_docs.py` call sites are a connection deliverable; H-MAD's Connection enforcement invariant requires a test/mutation that fails when the call-site/import connection alone is removed, and in the opposite direction when it is made unconditional, so callee tests could pass while the existing harness no longer reaches `h_mad_doc_block_exec`.
- Load-bearing measurements are asserted without cited command output in the document — claims such as the single existing harness/two extractor call sites and the `68` bash-fence count shape scope and success criteria, but the plan records conclusions rather than the observed commands/output; this violates the Assumption verification and count-rederivation invariants because downstream work would be asked to trust uncited measurements.

## Should-fix
- Clarify how the CLI exposes block stdout/stderr — the plan says an operator gets `rc`, `stdout`, and `stderr` with one command, but also says the CLI prints exactly one verdict line; without a stated transport, an implementation can satisfy one sentence while missing the other.
- Tighten the side-effect isolation wording — a fresh temp cwd protects ordinary relative writes, but it is not a sandbox against absolute paths or explicit `cd`, so “side effects cannot reach the repository” overstates the guarantee the plan actually tests.

## Nit
- The `68` fence wording should name the exclusions used for the count, especially tests/hidden state, so a reviewer rerunning a broad `h-mad/` + `handoff/` grep does not get an apparent mismatch.
