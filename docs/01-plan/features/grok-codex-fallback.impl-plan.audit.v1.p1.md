AUDIT-grok-codex-fallback-impl-plan-v1-BEGIN
## Summary
The plan has four gates that can pass without collecting the evidence they claim to require. They affect cross-surface agreement, both directions of wire testing, preservation of existing tests, and the live runtime smoke.
Evidence: 11 files opened, 9 greps run; 🌱 graft saved ~159k tokens (~$0.08) this turn.

## Must-fix
- Make Task 16 depend on Task 13 — the full-suite gate can run before the 23 cross-surface agreement tests are authored, leaving the single-source contract unverified at merge.
  class: build
  quote: docs/01-plan/features/grok-codex-fallback.impl-plan.md › `**Dependencies on other tasks**: Task 14, Task 15`
- Execute and score every stated wire-scoped removal, with the callee intact, in addition to the force-fire mutations — Task 14 gates only the six mutation specs, so the required remove-connection direction can remain unobserved.
  class: build
  quote: docs/01-plan/features/grok-codex-fallback.impl-plan.md › `**Description**: Author the six spec files with exactly the 43 rows below, then for each spec run`
- Compare every pre-existing test file against BASE_SHA directly — the proposed node-id floor and no-deleted-lines check allow an added skip decorator to disable a pre-existing test while the claimed “unmodified” gate passes.
  class: build
  quote: docs/01-plan/features/grok-codex-fallback.impl-plan.md › `git diff --numstat "$BASE_SHA" -- h-mad/tests handoff/tests | awk '$2 != 0'   # must print nothing`
- Turn Task 17's pass conditions into executable assertions that halt on failure — the smoke command ends with `echo`, and the subsequent reads only print results, so a failed real dispatch or missing `b.txt` does not stop the recipe before recording a pass.
  class: build
  quote: docs/01-plan/features/grok-codex-fallback.impl-plan.md › `--cd "$S" --effort low --timeout 300 --out "$S/smoke.out" --log "$S/smoke.log"; echo "rc=$?"`

## Should-fix
- Replace Task 10's `<program>` placeholder with the actual jq renderer or an exact pseudocode algorithm — the most complex reader is left for the implementer to design, making its run coalescing and failure handling hard to review against the plan.
  class: build
  quote: docs/01-plan/features/grok-codex-fallback.impl-plan.md › `$_GROK_JQ_DEFS<program>`

## Nit
None
AUDIT-grok-codex-fallback-impl-plan-v1-END
