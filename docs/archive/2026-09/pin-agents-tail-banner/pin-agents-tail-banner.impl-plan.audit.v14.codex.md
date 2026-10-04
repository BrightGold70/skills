AUDIT-pin-agents-tail-banner-impl-plan-v14-BEGIN
## Summary
The production design is detailed and the stated 37/11/26 aggregate reproduces, but the execution instructions do not derive the per-task counts that Phase 5d actually consumes. The plan also bypasses its own wiring classification and leaves a user-facing identity claim stale, so it is not ready to dispatch unchanged.

## Must-fix
- The RED-count instructions derive aggregate counts and then call them “the dispatch inputs,” contradicting the preceding requirement that each 5d dispatch use its per-task counts — `h_mad_assemble_tdd.py` cuts one `Task N` and accepts that task's `--expect-fail/--expect-pass`; feeding 26/11 to T1 (expected 3/3), T2 (6/1), etc. guarantees `step5d:red_not_all_failing`. This violates the Counts-a-dispatch-reports invariant; prescribe a mechanical per-task derivation from the authoritative node map, and reserve 37/11/26 for the aggregate check.
- Task 3 is mislabeled `new-behaviour` even though the plan explicitly identifies its deliverable as the `_orca_find` → `_orca_tail_sig` call-site connection and later adds both connection-direction mutants — as written, the wire-pin gate reports `wiring=0`, so the task bypasses the required `WIRE`/`WIRE-PIN`, wire registry, and wire-specific RED failure-mode checks. This is a Connection-enforcement gap; mark/split the connection as a `wiring` task and name `test_tail_pass_resolves_single_vendor_banner` (or an equivalent caller-observable node) as its wire pin.
- Task 5 leaves `h-mad/SKILL.md`'s adjacent claim that Codex is detected “only on a fresh pane's `gpt-N` banner, which scrolls off once it works” unchanged — the feature's purpose is precisely to resolve after preview decay from the banner retained at the start of tail scrollback. Updating only the pass enumeration ships a contradictory user-facing contract for changed entry behaviour, breaching cross-document consistency and Skill manifest integrity; update and test that sentence as part of T5.

## Should-fix
- The provenance header cites design v1.11 and spec v1.5, while the paired files now contain v1.12 and v1.6 history entries — refresh the source versions so implementers know which audited contracts the plan incorporates.
- AC-6.12…AC-6.20 denotes nine items but names only the seven green-at-RED mutants, omitting the two here-string-to-pipeline mutants that the surrounding prose says complete the range — enumerate all nine or narrow the range so the acceptance contract matches the mutation set.

## Nit
- The withdrawn Task 4 AC-4.2 still has the orphaned continuation “this pass: no handle…” beneath it; remove that leftover sentence so a withdrawn criterion does not read like a fifth T4 requirement.
AUDIT-pin-agents-tail-banner-impl-plan-v14-END
