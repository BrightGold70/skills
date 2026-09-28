AUDIT-grok-codex-fallback-plan-v1-BEGIN
## Summary
The plan addresses FR-1 through FR-11 in the spec's form, and the checked fixture hash, AC count, and dispatch census match the repository. Three blocking verification gaps remain: the new external-runtime wrapper has no live round trip, several wires omit the required force-fire check, and W6's proposed negative check cannot distinguish the wrong branch order.

| Axis C classification | Identifiers |
|---|---|
| implemented-as-written | FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-7, FR-8, FR-9, FR-10, FR-11 |
| restated | None |
| absent | None |

Evidence: 11 files opened, 18 greps run.
🌱 graft saved ~162,355 tokens this turn, 5 calls.

## Must-fix
- The plan excludes a live `hmad-dispatch exec grok` round trip before shipping; the committed probe used `hmad-dispatch run` to call grok directly, so it does not reconcile the new wrapper with the real CLI and stream envelope. Add a bounded live wrapper round trip before release, or explicitly name the unverified wrapper behavior and the reason a live run is impossible for an operator decision. — This breaches the base wrapper–runtime reconciliation invariant even if every stub test passes.
  class: measurement
  quote: docs/01-plan/features/grok-codex-fallback.plan.md › `- No task and no AC makes a live xAI call (D4).`
  quote: docs/03-analysis/probes/grok-codex-fallback/stream-json.2026-09-28.md › `HPW_AGENT_BACKEND=claude hmad-dispatch run --timeout 400 --`
  quote: h-mad/invariants.base.md › `- A wrapper verb over an **external runtime's CLI** MUST be exercised **live against that runtime**`
- W1, W3, W8, and W11 leave their force-fire column empty, despite the plan promising a mutation in both directions. Give each wire an unconditional-call mutation and a named negative observation, then verify the mutation landed and the test failed. — The base connection-enforcement invariant requires both directions; a dispatch `case` that appears to exclude other agents is not a force-fire test.
  class: build
  quote: docs/01-plan/features/grok-codex-fallback.plan.md › ``| W1 | `_cmd_exec` agent dispatch → grok argv builder | AC-3.1 fails: argv lacks `--prompt-file`, carries `--print` | — (grok arm unreachable for codex/agy by the `case`) |``
  quote: h-mad/invariants.base.md › `- Mutate the connection in **both directions**: remove it → the wire test must fail; force it to fire`
- W6's force-fire claim relies on existing agy-only CLI tests. On an agy-only log `scan_grok` returns `None`, so consulting it first and then falling through produces the same agy result; add a mixed agy-plus-F0 log whose CLI output must remain byte-identical to the agy path, and use it to kill the precedence mutation. — The proposed observation does not discriminate an unconditional early grok scan from the required agy-first route.
  class: build
  quote: docs/01-plan/features/grok-codex-fallback.plan.md › ``| W6 | evidence CLI `main` → `scan_grok` | AC-6.1 fails: F0 prints `UNREADABLE reason=unsupported_format` | `scan_grok` consulted before agy → existing agy CLI tests fail |``
  quote: docs/01-plan/features/grok-codex-fallback.spec.md › ``scan_grok` returns `None` when the text carries no JSON object whose `type` is one of the seven``

## Should-fix
None

## Nit
None
AUDIT-grok-codex-fallback-plan-v1-END
