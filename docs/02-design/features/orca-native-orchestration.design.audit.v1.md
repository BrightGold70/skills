# Design Audit v1 — orca-native-orchestration

Reviewer: agy (Gemini 3.1 Pro High), adversarial + cross-doc. Dispatched via hmad-dispatch (cmux surface:5). Cycle 1.

## Summary
The design faithfully implements the paired plan for Orca-native orchestration mode, wrapping the five native verbs and adding docs/indicators. Two gaps: how the worker resolves the coordinator handle, and missing argument validation.

## Must-fix
- Unstated coordinator-handle resolution in the worker prompt — D4 tells the worker to run `orca orchestration send --to "$HMAD_ORCA_COORDINATOR_TERMINAL"`, but the worker's separate shell may not have that env var exported, yielding an empty `--to`. The design must specify how the worker obtains the coordinator handle (e.g. the orchestrator injects it into the task spec / dispatch preamble).

## Should-fix
- Missing input validation — `_cmd_task_create` calls `cat "$2"` without checking the file exists / arg present; `dispatch`/`await`/`gate-create`/`gate-resolve` lack `-z` checks on required args (task_id, gate_id, etc.), allowing empty strings to reach `orca` and produce obscure errors.

## Nit
None
