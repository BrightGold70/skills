# Design Audit v2 — orca-native-orchestration

Reviewer: agy (Gemini 3.1 Pro High). Cycle 2 (post-v1.1). One should-fix.

## Summary
Both v1 findings resolved (coordinator embedded in spec; arg validation added). One should-fix: best-effort coordinator injection edge case.

## Must-fix
None

## Should-fix
- Potential worker failure on unpinned task creation — `_cmd_task_create` treats coordinator injection as best-effort, but the worker prompt assumes the `[H-MAD]` line is present. Enforce the pin in task-create or add a worker fallback.

## Nit
None
