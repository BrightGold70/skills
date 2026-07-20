# Spec: orca-native-orchestration

## Executive Summary
Add opt-in **orchestration-mode** verbs to `hmad-dispatch` that route agent dispatch, verdict collection, and decision gates through Orca's native `orca orchestration *` layer (structured, no screen-scraping) when substrate=orca and a coordinator handle is pinned; cmux and Orca-without-coordinator keep the existing scrape transport.

## Goal
On Orca, H-MAD collects agent verdicts and gates via structured `orchestration` messages instead of screen-scraping — eliminating the scrape-fragility class.

## Functional Requirements

### FR-1: Orchestration-mode verbs (Orca)
- **Description**: `hmad-dispatch` gains five verbs that wrap the native commands. Each emits the schema-v1 form and requires substrate=orca (error otherwise, FR-5).
- **Acceptance Criteria**:
  - AC-1.1: `hmad-dispatch task-create <label> <specfile>` invokes `orca orchestration task-create --spec "<contents-of-specfile>" --task-title <label> --json` and prints the `task_id` parsed from the JSON (`.result.taskId` / `.taskId`, tolerant).
  - AC-1.2: `hmad-dispatch dispatch <agent> <task_id>` invokes `orca orchestration dispatch --task <task_id> --to <resolved-agent-handle> --return-preamble --json`.
  - AC-1.3: `hmad-dispatch await <task_id> [--timeout <s>]` invokes `orca orchestration check --terminal <coordinator-handle> --wait --types worker_done --timeout-ms <ms> --json` (default 600000ms), and prints the matching worker_done payload for `<task_id>` (surfacing `report-path`/`files-modified`); non-zero on timeout.
  - AC-1.4: `hmad-dispatch gate-create <task_id> <question> [<options-json>]` invokes `orca orchestration gate-create --task <task_id> --question <question> [--options <options-json>] --json` and prints the `gate_id`.
  - AC-1.5: `hmad-dispatch gate-resolve <gate_id> <resolution>` invokes `orca orchestration gate-resolve --id <gate_id> --resolution <resolution> --json`.

### FR-2: Coordinator handle + mode detection
- **Description**: A coordinator handle (the H-MAD orchestrator's own Orca terminal) is provided via `HMAD_ORCA_COORDINATOR_TERMINAL`. A helper reports whether orchestration mode is active: substrate=orca AND the coordinator handle is set.
- **Acceptance Criteria**:
  - AC-2.1: `hmad-dispatch env` additionally prints `orchestration: on` when substrate=orca and `HMAD_ORCA_COORDINATOR_TERMINAL` is set; `orchestration: off` otherwise (cmux, or orca without the pin).
  - AC-2.2: `await` uses `HMAD_ORCA_COORDINATOR_TERMINAL` as the `--terminal` handle; absent → non-zero exit with a message naming the env var.

### FR-3: Agent `worker_done` emission
- **Description**: The Codex and agy dispatch-prompt templates gain an orchestration-mode instruction: on completion emit `orca orchestration send --to <coordinator> --type worker_done --task-id <id> --report-path <file> --files-modified <csv>`.
- **Acceptance Criteria**:
  - AC-3.1: `references/codex-implementer-prompt.md` and `references/agy-spec-reviewer-prompt.md` each contain a clearly-delimited "Orchestration mode" instruction block emitting a `worker_done` with `--task-id` + `--report-path` (assert the strings exist).

### FR-4: Documentation
- **Description**: `SKILL.md` gains an "Orchestration mode (Orca)" section (preferred Orca path; scrape flow is the fallback), and `references/orchestration-mode.md` documents the full task-create → dispatch → worker_done → await → gate flow + the coordinator-pin requirement.
- **Acceptance Criteria**:
  - AC-4.1: `references/orchestration-mode.md` exists and documents the five verbs + the coordinator pin + the worker_done contract; `SKILL.md` references it.

### FR-5: Fallback + non-regression
- **Description**: The orchestration verbs are Orca-only; on cmux (or any non-orca substrate) they exit non-zero with an actionable message. The existing `send`/`read`/`wait`/`alive`/`clear`/`notify` scrape transport is unchanged (cmux byte-identical; Orca scrape path unchanged).
- **Acceptance Criteria**:
  - AC-5.1: Under `HMAD_SUBSTRATE=cmux`, each orchestration verb exits non-zero with a message stating orchestration mode requires orca.
  - AC-5.2: The six existing transport verbs' emitted commands are unchanged (regression guard — existing tests stay green).

## Non-Functional Requirements
- Compatibility: additive; no existing verb changes; cmux fully unaffected.
- Test isolation: all tests stub `orca` (echo argv, canned `--json`) — no live Orca, no network, no coordinator.
- Self-containment (Axis B): confined to `h-mad/`; `SKILL.md` frontmatter/contract still valid (new verbs are additive to the documented surface — SKILL.md updated accordingly).

## Out-of-Scope
- Ripping out / replacing the scrape transport (kept as universal fallback).
- Wholesale rewiring of the SKILL.md audit/TDD loop to *use* orchestration mode by default (this ships the verbs + opt-in docs; default-wiring is a later feature).
- Auto-registration/auto-detection of the coordinator handle (explicit pin now).
- `orchestration run` coordinator-loop, `inbox`, `reply`, `task-update` (not needed for the dispatch→verdict→gate flow).

## Assumptions
- Orca `orchestration` schema v1 forms (task-create/dispatch/check/gate-create/gate-resolve) as probed. `worker_done` messages carry `--task-id` and are retrievable by `check --types worker_done`.
- Agents run inside Orca-managed terminals with stable handles when orchestration mode is used.

## Version History
- v1.0: Initial specification draft.
