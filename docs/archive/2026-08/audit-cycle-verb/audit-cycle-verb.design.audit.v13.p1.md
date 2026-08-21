## Summary
The design for the `audit-cycle` verb is exceptionally robust and demonstrates a deep understanding of the problem space, edge cases, and `h-mad` invariants. The boundaries between the shell script (orchestration, concurrency) and the Python helper (collection, gating, formatting) are drawn sharply and cleanly. The rigorous treatment of subprocess exit codes vs. verdict tokens, the explicit connection mutations, and the exemption of the real gate for specific tests are all masterfully handled. Axis C reconciliation found one `restated` AC where the design correctly resolved a self-contradiction in the spec.

## Must-fix
- **Spec Reconciliation: AC-4.1 is `restated`** — The spec states: "Only an empty or absent file leads to `h_mad_report_wait.py`". The design states: "a non-empty report without its marker is a torn write... Requiring the marker sends that case to step 2, where `report_wait` blocks".
  *Reasoning*: The design is narrower than the literal text of the spec's "Only an empty or absent file" clause, as it will send a present, non-empty file to `report_wait` if the `.done` marker is absent. The design's logic is absolutely correct and resolves a self-contradiction in the spec itself (where the spec also stated "Without the marker the pass falls to `report_wait`"), but this divergence must be logged as `restated` to ensure the spec is formally reconciled.

## Should-fix
- **Missing explicit test for `--passes < 1` rejection (AC-3.1)** — The design explicitly validates `--passes K` where `K<1` (exiting 2), but the Test Plan lacks a test specifically anchoring this validation (e.g., `test_verb_invalid_passes`).
  *Reasoning*: An operational error path that guards against a zero-dispatch cycle (`K=0`) must be explicitly covered by a test to prevent the guard from being accidentally removed in the future.
- **AC-10.4 test scope in the Test Plan** — AC-10.4 requires asserting that a `## Must-fix`-less report yields `UNVERIFIED`. The Test Plan lists `test_gate_invalid_discards_counts` (verifying the gate returns `INVALID`), but does not explicitly list a test ensuring `combine` maps `INVALID` to `UNVERIFIED` (e.g., `test_combine_invalid_yields_unverified`).
  *Reasoning*: To fully satisfy the AC, the test plan should explicitly verify the end-to-end outcome (or at least the `combine` layer outcome) for a header-less report, rather than just the gate layer's `INVALID` return.

## Nit
- **Helper CLI `--grace` vs Verb CLI `--report-grace`** — The `h_mad_audit_cycle.py` CLI specifies `--grace 5`, while the `hmad-dispatch.sh` CLI specifies `--report-grace <sec>`. This is perfectly fine as the shell can just map the argument name when calling the helper, but worth noting for consistency.
