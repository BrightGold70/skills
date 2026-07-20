# Report: orca-native-transport

## Executive Summary
Corrected the `hmad-dispatch` Orca transport verbs to Orca's confirmed `agent-context` schema v1 — fixing latent bugs (broken `wait`, guessed liveness JSON path) that shipped with the original wrapper — through the full 7-phase H-MAD workflow, 100% match, green suite.

## Summary
Four surgical Orca-arm corrections in `h-mad/scripts/hmad-dispatch.sh`: `wait` → `orca terminal wait --for tui-idle --timeout-ms`; `read` → native `--limit` (dropped `tail`); `alive` + `_orca_find` → real `.result.terminals[].handle` path (were guessed `.[]|select(.id)`). `agent-substrate.md` marked schema-confirmed. cmux arms byte-identical. TDD by Codex (surface:4); audits + 6a-prime by agy (surface:5), dispatched via the very `hmad-dispatch` wrapper being corrected (over cmux — no self-break). Suite 73/0.

## Metrics
| Metric | Value |
|---|---|
| Plan audit cycles | 2 (1 back-propagation) |
| Design audit cycles | 1 |
| Impl-plan audit cycles | 1 |
| Iterate cycles | 0 |
| Match rate | 100% |
| Tests | 73 passing / 0 failing |
| Back-propagation | Phase 3: design-time schema probe expanded FR-3 to a real fix |
| 6a-prime | READY_TO_MERGE (0 cycles) |

## What Went Well
- The design-time live `orca terminal list --json` probe caught that FR-3's "already correct" assumption was false — the guessed `.[]|select(.id)` never matched the real `.result.terminals[].handle` shape. Back-propagation fixed the plan before code.
- The wrapper's env-pin escape hatch (from the first skill feature) is confirmed as the reliable Orca identity path — no `terminal list` field names the running program, so handle pins beat substring matching.

## What To Improve Next Time
- The original wrapper shipped Orca verbs by *guessing* the CLI; a `agent-context --json` reconciliation should have been a build-time gate. This feature is that reconciliation.

## Carry Items
- Tier 2 (`orca-native-orchestration`): the native `orchestration` layer (dispatch/send/check/gate/task) — structured coordination replacing screen-scraping — is the next feature.
- Live Orca-hosted-agent e2e still not exercised (unit tests assert argv against the confirmed schema); a real Orca run would confirm end-to-end.

## Version History
- v1.0: Initial report draft.
