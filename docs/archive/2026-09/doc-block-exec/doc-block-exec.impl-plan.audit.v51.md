# doc-block-exec impl-plan audit v51 — operator override sidecar over impl-plan audit v50 (codex)

## Summary
Operator override sidecar for the round-nineteen gating pass (sheet C8 iii: r19 is the last document
round). Every finding below is carried with its `[key]`; measurement-class findings and deferred
should-fixes are acknowledged by key with their re-run command; build-class musts are NOT acknowledged
here — they are carried as `OPEN-DECISION` lines on the owning impl-plan Task and settled in 5d.
Evidence: the codex report this sidecar answers, re-derived by the orchestrator where stated.

## Must-fix
None

## Should-fix
- [strict-flags-collateral] `strict-flags-dropped` also breaks `test_pipefail_strict_vs_plain`; the collateral enumeration is incomplete (impl-plan c50 codex should 1).
  class: measurement
- [close-only-collateral] The close-only test is misclassified as a collateral killer of `final-write-close-not-in-finally` (impl-plan c50 codex should 2).
  class: measurement
- [task2-ten-vs-eleven] Later RED accounting still says Task 2's tests are "ten" (impl-plan c50 codex should 3).
  class: measurement
- [in-process-cli-tests] Four no-injection CLI tests call `main` in-process against the subprocess-transport rule (impl-plan c50 codex should 4).
  class: build

## Nit
None

## Carried to OPEN-DECISION (5d) — build-class, not acknowledged here
- impl-plan c50 codex must 1 (`preamble-composed-with-unsubstituted-text` has no distinction at `run_block`) → Task 3 OPEN-DECISION 1.
- impl-plan c50 codex must 2 (alias-refusal rollback deletion unverified) → Task 4 OPEN-DECISION 2.
- impl-plan c50 codex must 3 (`--help` bypass; also design c99 must 2) → Task 4 OPEN-DECISION 3.

## Acknowledged-not-fixed
- [strict-flags-collateral] re-run: both documented fixtures under `bash -euo pipefail -c` and `bash -c` → rc 1 / 0 each (codex's execution); the enumeration is re-derived by the 5d implementer from the real mutation run, which is the only authoritative source of collateral reds.
- [close-only-collateral] re-run: in-memory pair, close-only failure → `stream_write_failed` under both implementations (codex's execution); settled by the mutation harness in 5e.
- [task2-ten-vs-eleven] re-run: `grep -n "Task 2's ten" docs/01-plan/features/doc-block-exec.impl-plan.md`; the Task 2 AC list says eleven; the later block's word is stale — the 5d RED count is derived from the AC list, not this sentence.
- [in-process-cli-tests] deferred: the 5d implementer writes these four as subprocess tests if the transport rule holds at that point, or documents the exception in the test module; a should-fix, deferrable by the skill's own rule.
