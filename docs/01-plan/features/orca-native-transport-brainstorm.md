# Brainstorm: orca-native-transport

## Executive Summary
Harden the `hmad-dispatch` Orca branches by reconciling them against Orca's confirmed `agent-context` command schema — fixing the guessed `wait` syntax, adopting native `terminal wait --for tui-idle` and `terminal read --limit`, and keeping structured `terminal list --json` liveness — so the Orca transport is correct and deterministic (Tier 1). The richer native `orchestration` layer is deferred to a separate spec (Tier 2).

## Problem Statement
The `hmad-dispatch` wrapper's Orca branches were authored by **guessing** the Orca CLI syntax (the original build's documented open-items). Reconciled against `orca agent-context --json` (schema v1, 202 commands), two are wrong/suboptimal and were never live-tested:
- `wait`: emits `orca terminal wait --terminal <t> tui-idle` — **incorrect**; the real contract is `orca terminal wait [--terminal <h>] --for exit|tui-idle [--timeout-ms <ms>]`. As written it would error, silently defeating the one feature (native idle) that motivated Orca support.
- `read`: pipes `orca terminal read --terminal <id> | tail -n N`; Orca has a native `--limit <n>` (and `--cursor <n>`), so the pipe is redundant/less correct.

Separately, this session showed that **screen-scraping is the root of H-MAD's transport fragility** (the `alive` string-match false-positives; verdict `read`+grep matching prompt-echo and stale scrollback). Orca exposes structured alternatives; Tier 1 adopts the cheap ones (`terminal wait`, `terminal list --json`), Tier 2 (separate) adopts the full `orchestration` layer.

## Proposed Approach
**Tier 1 — Orca transport hardening (this feature):**
- Correct every Orca verb to the confirmed schema: `wait` → `orca terminal wait [--terminal <h>] --for tui-idle [--timeout-ms <ms>]`; `read` → `orca terminal read --terminal <h> --limit <n>` (drop the `tail` pipe); confirm `send` (`--text --enter`), `alive`/`_orca_find` (`terminal list --json`) already match (they do).
- Make the Orca `wait` the native deterministic idle-wait (no poll), with a bounded `--timeout-ms`.
- Update `references/agent-substrate.md`: remove the "confirm against live CLI" open-items now that the schema is pinned (schema v1).
- **cmux path untouched** — the cmux `wait` poll-until-stable stays (cmux has no native idle).

**Tier 2 — native `orchestration` layer (deferred, separate spec authored alongside):** dispatch/verdict/gate/task via `orca orchestration dispatch|send|check|gate-*|task-*` — agents emit structured `worker_done` with `--report-path`; the coordinator reads via `check --wait --types worker_done --json` (no scraping); audit-gate/halt become native `gate-create/resolve`. Genuine architecture shift → its own H-MAD cycle.

## Alternatives Considered
- **Leave the Orca verbs as-guessed** — rejected: `wait` is broken; the orca paths are untested; a latent-bug ship.
- **Jump straight to Tier 2 (orchestration layer)** — rejected: it changes the agent-report contract + skill flow (Codex/agy must speak the protocol); too large to bundle with a syntax fix; deserves its own audited cycle.
- **Tier 1 now + Tier 2 spec** (chosen) — fixes real bugs immediately, keeps cmux intact, and records the bigger design for a deliberate follow-on.

## Risks & Mitigations
| Risk | Likelihood | Mitigation |
|---|---|---|
| Orca CLI version drift changes flags | M | `agent-context` is versioned (`schemaVersion`); pin to v1 semantics; verbs already tolerate missing fields; explicit env pins remain the escape hatch |
| Can't fully live-e2e without an Orca-hosted agent pane | M | Unit tests assert exact argv against the confirmed schema (stub `orca` on PATH), same harness as the existing suite; syntax is now schema-confirmed, not guessed |
| Editing the wrapper mid-workflow could break dispatch | L | This workflow dispatches over **cmux** (surfaces 4/5); Tier 1 edits only the **orca** branches — no self-break |

## Dependencies
- `orca` CLI present for schema reference (installed). No new runtime deps. Change is confined to `h-mad/scripts/hmad-dispatch.sh` + `h-mad/tests/test_hmad_dispatch.py` + `h-mad/references/agent-substrate.md`.

## Open Questions
- Default `--timeout-ms` for the Orca `wait` (proposal: mirror the cmux poll default of 300s = 300000ms).
- Whether to also expose `--cursor` for incremental reads (proposal: no — YAGNI for the current gate-read usage).

## Version History
- v1.0: Initial brainstorm draft.
