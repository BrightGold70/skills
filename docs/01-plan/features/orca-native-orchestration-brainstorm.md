# Brainstorm: orca-native-orchestration

## Executive Summary
Add an **orchestration mode** to `hmad-dispatch` that, on Orca, routes agent dispatch, verdict-collection, and decision gates through Orca's native `orca orchestration *` layer (structured `task-create` → `dispatch` → `worker_done` → `check --wait` → `gate-*`) instead of screen-scraping — eliminating the scrape-fragility class (false-positive `alive`, verdict-grep matching echo/scrollback) that recurred throughout this session. Additive and opt-in: cmux and Orca-without-coordinator keep the existing transport.

## Problem Statement
H-MAD's dispatch is built on *screen-scraping* a terminal because cmux is a dumb multiplexer: send raw text, then poll-and-grep the screen for a verdict. This session repeatedly hit the failure modes that scraping causes — `alive` string-match false-positives (matched the wrong surface), and verdict polling that matched the prompt-echo and stale scrollback (3 mis-reads). Orca ships a native multi-agent coordinator (`orchestration task-create/dispatch/send/check/gate-*/task-update`) that makes dispatch and verdict-collection **structured** (JSON messages with `--report-path`/`--files-modified`, blocking `check --wait --types worker_done`, native decision gates). H-MAD hand-rolls all of this; on Orca it should use the native layer.

## Proposed Approach
Add **orchestration-mode verbs** to `hmad-dispatch` that wrap the native commands, plus the agent-side `worker_done` emission and a coordinator handle:
- `hmad-dispatch task-create <label> <spec-file>` → `orca orchestration task-create --spec <file-contents> --task-title <label> --json` → prints `task_id`.
- `hmad-dispatch dispatch <agent> <task_id>` → `orca orchestration dispatch --task <id> --to <agent-handle> --return-preamble --json` (structured dispatch; preamble injected into the agent's terminal).
- `hmad-dispatch await <task_id> [--timeout <s>]` → `orca orchestration check --terminal <coordinator-handle> --wait --types worker_done --timeout-ms <ms> --json`, filter for `task_id`, print the worker_done payload (`report-path`, `files-modified`) — **no screen read, no grep**.
- `hmad-dispatch gate-create <task_id> <question> [options-json]` → `orca orchestration gate-create` → prints `gate_id`; `hmad-dispatch gate-resolve <gate_id> <resolution>` → `orca orchestration gate-resolve`.
- **Coordinator handle**: the H-MAD orchestrator (Claude) registers/pins its own Orca terminal as `HMAD_ORCA_COORDINATOR_TERMINAL` — the `--to` target for `worker_done` and the `--terminal` for `check`.
- **Agent prompts** (`references/codex-implementer-prompt.md`, `agy-*-prompt.md`): add — "in orchestration mode, on completion emit `orca orchestration send --to <coordinator> --type worker_done --task-id <id> --report-path <file> --files-modified <csv>`".
- **Detection**: orchestration mode is active only when substrate=orca AND a coordinator handle is available; otherwise the existing `send`/`read`/`wait` scrape transport is used (cmux always; Orca without a coordinator).
- **SKILL.md**: an "Orchestration mode (Orca)" section documenting the structured flow as the preferred Orca path, with the scrape flow as the fallback; `references/orchestration-mode.md` for the full flow.

## Alternatives Considered
- **Rip out screen-scraping entirely, orchestration-only on Orca** — rejected: too invasive, and Orca-without-a-running-coordinator must still work; keep scrape as the universal fallback.
- **Leave H-MAD on scraping, ignore the native layer** — rejected: this session proved scraping is the root fragility; the native layer is exactly the fix.
- **Additive opt-in orchestration mode** (chosen) — structured path when available, scrape fallback otherwise; zero regression for cmux.

## Risks & Mitigations
| Risk | Likelihood | Mitigation |
|---|---|---|
| Cannot live-validate (no Orca-hosted agents in this cmux session) | H | Unit-test every verb's argv + JSON parsing against stubbed `orca orchestration *`; carry a live-Orca e2e item; same validation posture as Tier 1 |
| `worker_done` correlation subtlety (sender-handle vs task/dispatch id) | M | Follow the schema notes verbatim (worker_done carries `--task-id`/`--dispatch-id`; sender must match the dispatch assignee); document the pin requirement |
| Coordinator-handle bootstrap (Claude's own terminal id) | M | Explicit `HMAD_ORCA_COORDINATOR_TERMINAL` pin (like the agent pins); auto-detect deferred |
| Scope creep into the whole SKILL flow | M | Tier 2 ships the verbs + agent-prompt emission + docs + an opt-in SKILL section; wholesale replacement of the scrape loop is out-of-scope (a later wiring feature) |

## Dependencies
- Orca `orchestration` command group (confirmed in `agent-context` schema v1). No new runtime deps. Change confined to `h-mad/`.

## Open Questions
- Default `await` timeout (proposal: 600s = 600000ms — audits/TDD can run long).
- Whether to auto-register the coordinator handle vs require the pin (proposal: require the pin now; auto-register is a follow-on).

## Version History
- v1.0: Initial brainstorm draft.
