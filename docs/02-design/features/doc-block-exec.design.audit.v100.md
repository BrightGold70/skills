# doc-block-exec design audit v100 — operator override sidecar over design audit v99 (codex)

## Summary
Operator override sidecar for the round-nineteen gating pass (sheet C8 iii: r19 is the last document
round). Every finding below is carried with its `[key]`; measurement-class findings and deferred
should-fixes are acknowledged by key with their re-run command; build-class musts are NOT acknowledged
here — they are carried as `OPEN-DECISION` lines on the owning impl-plan Task and settled in 5d.
Evidence: the codex report this sidecar answers, re-derived by the orchestrator where stated.

## Must-fix
None

## Should-fix
- [ac27-table-rendered-assertions] The AC-2.7 test-table row still assigns rendered-line assertions to API tests while the impl-plan limits those tests to exception data and moves rendering to Task 4 (design c99 codex should 1).
  class: measurement

## Nit
None

## Carried to OPEN-DECISION (5d) — build-class, not acknowledged here
- design c99 codex must 1 (`communicate(timeout=1e300)` → `OverflowError` escapes the `err` mapping) → impl-plan Task 3 OPEN-DECISION 4.
- design c99 codex must 2 (`--help` with other arguments bypasses the malformed-invocation verdict; also impl-plan c50 must 3) → impl-plan Task 4 OPEN-DECISION 3.
- design c99 codex must 3 (empty-key predicate prescribed twice, Single-source contract) → impl-plan Task 2 OPEN-DECISION 5.

## Acknowledged-not-fixed
- [ac27-table-rendered-assertions] re-run: `grep -n 'asserting one \`intersect: "ab" "bc" "1"\` line and nothing executed' docs/02-design/features/doc-block-exec.design.md` and impl-plan:2593 region (AC-2.7 asserts exception data); the table wording lags the r18 decision the design itself records; the implementer follows the impl-plan's Task 2 / Task 4 split.
