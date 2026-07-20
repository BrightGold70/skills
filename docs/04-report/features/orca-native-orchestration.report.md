# Report: orca-native-orchestration

## Executive Summary
Added Orca's native multi-agent **orchestration mode** to `hmad-dispatch` — structured dispatch, verdict-collection (`worker_done` + `await`), and decision gates replacing screen-scraping on Orca — through the full 7-phase H-MAD workflow, 100% match, green suite.

## Summary
Five opt-in Orca-only verbs (`task-create`/`dispatch`/`await`/`gate-create`/`gate-resolve`) wrap `orca orchestration *`; `_require_orca` gates them; the coordinator handle is enforced and injected into the task spec so workers emit `worker_done` (read structurally via `await`, no scrape); `_need` guards required args; `env` reports `orchestration: on|off`. Codex/agy prompt refs gained `worker_done` blocks; `references/orchestration-mode.md` + a `SKILL.md` section document the flow. The scrape transport + cmux arms are untouched (universal fallback). TDD by Codex (surface:4); audits + 6a-prime by agy (surface:5), dispatched over cmux via `hmad-dispatch` itself. Suite 83/0.

## Metrics
| Metric | Value |
|---|---|
| Plan audit cycles | 2 (1 naming fix) |
| Design audit cycles | 3 (coordinator-injection + validation + pin-enforcement) |
| Impl-plan audit cycles | 1 |
| Iterate cycles | 0 |
| Match rate | 100% |
| Tests | 83 passing / 0 failing |
| 6a-prime | READY_TO_MERGE (0 cycles) |

## What Went Well
- The design audits caught the two hardest correctness issues before code: the worker can't read the coordinator from its own shell env (inject into the task spec) and the injection must be enforced not best-effort (fail-fast pin) — both would have silently broken `worker_done` collection live.
- Opt-in + additive scoping kept risk bounded: no live-Orca validation was possible in a cmux session, but the scrape transport stays the universal fallback and cmux is byte-identical.

## What To Improve Next Time
- The whole Tier-1/Tier-2 arc shows the original wrapper's Orca verbs were guessed; reconciling against `orca agent-context --json` at build time (now done) should be a standing gate for any Orca-touching change.

## Carry Items
- **Live-Orca e2e**: orchestration mode is unit-tested against stubs only; a real Orca session with Orca-hosted Codex/agy agents is needed to validate `dispatch → worker_done → await → gate` end-to-end.
- **Default-wiring**: the SKILL.md audit/TDD loop still defaults to the scrape flow; a later feature can make it prefer orchestration mode when `env` reports `orchestration: on`.

## Version History
- v1.0: Initial report draft.
