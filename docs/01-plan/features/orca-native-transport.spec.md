# Spec: orca-native-transport

## Executive Summary
Reconcile the `hmad-dispatch` Orca branches with Orca's confirmed `agent-context` schema (v1): correct the `wait` verb to native `terminal wait --for tui-idle --timeout-ms`, use native `terminal read --limit`, keep structured `terminal list --json` liveness, and mark the syntax confirmed in `agent-substrate.md` — cmux path unchanged.

## Goal
The Orca transport in `hmad-dispatch` is correct, schema-confirmed, and deterministic (native idle-wait), fixing latent bugs from the originally-guessed Orca syntax.

## Functional Requirements

### FR-1: Correct Orca `wait` verb (native `--for tui-idle`)
- **Description**: The Orca branch of `_cmd_wait` must emit the schema-correct `orca terminal wait --terminal <handle> --for tui-idle --timeout-ms <ms>` (was the invalid `orca terminal wait --terminal <t> tui-idle`). Default timeout 300000ms (mirrors the cmux poll default of 300s).
- **Acceptance Criteria**:
  - AC-1.1: Under `HMAD_SUBSTRATE=orca`, `hmad-dispatch wait <agent>` invokes exactly `orca terminal wait --terminal <resolved-id> --for tui-idle --timeout-ms 300000` (assert full argv; no bare `tui-idle` positional token).
  - AC-1.2: `hmad-dispatch wait <agent> --timeout 30` maps to `--timeout-ms 30000`.
  - AC-1.3: The `wait` verb returns the underlying `orca terminal wait` exit status (0 idle reached / non-zero timeout).

### FR-2: Native Orca `read` bounding (`--limit`)
- **Description**: The Orca branch of `_cmd_read` must use the native `--limit <n>` bound instead of piping through `tail`.
- **Acceptance Criteria**:
  - AC-2.1: Under `HMAD_SUBSTRATE=orca`, `hmad-dispatch read <agent> --lines 50` invokes exactly `orca terminal read --terminal <resolved-id> --limit 50` (no `| tail`, no shell pipe in the emitted command).
  - AC-2.2: Default (no `--lines`) uses `--limit 50`.

### FR-3: Fix Orca liveness + identity JSON path (real schema)
- **Description**: The Orca `alive` path (`_cmd_alive`) and the identity resolver (`_orca_find`) parse `orca terminal list --json` with a **guessed** shape — `.[] | select(.id == …)` — but the real schema (confirmed live) nests terminals under `.result.terminals[]`, each keyed by `.handle` (a `term_<uuid>`), with `.title`/`.preview` but **no** `.id`/`.command`/`.name`. Both paths must be corrected to `.result.terminals[]` and match on `.handle`. Since no field names the running program, `_orca_find`'s substring match falls back to `.preview`/`.title` (best-effort) and the reliable identity path remains the explicit `HMAD_ORCA_<AGENT>_TERMINAL=<handle>` pin.
- **Acceptance Criteria**:
  - AC-3.1: `_cmd_alive` under orca invokes `orca terminal list --json` and resolves liveness via `.result.terminals[] | select(.handle == <pin>)` — exit 0 present / 1 absent (assert against a canned `{"result":{"terminals":[{"handle":"term_x"}]}}` stub).
  - AC-3.2: `_orca_find` parses `.result.terminals[]`, matches the agent token against `.preview`/`.title`, and returns the matched `.handle`; zero/multiple → non-zero exit with the pin hint (unchanged semantics).
  - AC-3.3: An explicit `HMAD_ORCA_<AGENT>_TERMINAL` handle pin bypasses `_orca_find` and is used verbatim as `--terminal <handle>` (regression guard — identity pin is the reliable path).

### FR-4: `agent-substrate.md` marks the Orca syntax confirmed
- **Description**: `references/agent-substrate.md` currently lists the `orca terminal …` shapes as "confirm against live CLI" open-items. Update it to state they are confirmed against `orca agent-context` schema v1, and record the exact `wait`/`read`/`list` flag forms.
- **Acceptance Criteria**:
  - AC-4.1: `agent-substrate.md` no longer lists `orca terminal wait`/`read`/`list` field shapes under an unresolved "Open items" heading; it states the schema-v1-confirmed forms (`terminal wait --for tui-idle --timeout-ms`, `terminal read --limit`, `terminal list --json`).

## Non-Functional Requirements
- Compatibility: the cmux branch of every verb is byte-for-byte unchanged (the cmux `wait` poll-until-stable stays — cmux has no native idle). Detection, identity resolution, `send`, `clear`, `notify` unchanged.
- Test isolation: all tests stub the `orca` executable on `PATH` (echo argv) — no live Orca runtime, no network. Consistent with the existing `test_hmad_dispatch.py` harness.
- Self-containment (Axis B): change stays within the `h-mad/` skill dir; no cross-skill import; `SKILL.md` contract unaffected (verb names/semantics unchanged — only the Orca-side emitted commands are corrected).

## Out-of-Scope
- The native `orchestration` layer (dispatch/send/check/gate/task) — Tier 2, its own spec/design/cycle (`orca-native-orchestration`, authored separately).
- `orca terminal read --cursor` incremental reads (YAGNI for the current gate-read usage).
- Any cmux-path change.
- Changing verb names or the public `hmad-dispatch` CLI surface.

## Assumptions
- `orca agent-context` schema v1 is the contract: `terminal wait [--terminal <h>] --for exit|tui-idle [--timeout-ms <ms>]`, `terminal read [--terminal <h>] [--cursor <n>] [--limit <n>] [--json]`, `terminal list [--worktree] [--limit] [--json]`, `terminal send [--terminal <h>] [--text <t>] [--enter] [--interrupt] [--json]`.
- Orca-managed terminals resolve to a stable `.id`/`.handle` (already used by `_orca_find`).

## Version History
- v1.0: Initial specification draft.
