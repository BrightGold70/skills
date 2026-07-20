# Design Audit v1 — orca-automations-scheduled-e2e

Reviewer: agy (Gemini 3.1 Pro High), adversarial_consistency + cross_doc_consistency. Cycle 1.

## Summary
The design faithfully translates the paired plan into the four Orca automation verbs and maintains the file-indirection boundary. But there are internal contradictions and silent drifts from the plan regarding the run/remove execution pipeline, plus an unbacked `[H-MAD]` markers claim, that must be resolved.

## Must-fix
- Silent drift in run/remove JSON handling — the plan specifies "For run/remove: `_need` id, pass id through, run" with no `_json_extract`, but the design adds `| _json_extract '.result | tojson'` to remove and mentions it in the run prose. Reconcile design to the plan.
- `_cmd_automation_run` pipeline contradiction — the Architecture Overview and the run code snippet (`orca automations run "$1" --json`) omit the `_json_extract` pipe, while the accompanying prose implies it. Internal contradiction; resolve.
- Unimplemented `[H-MAD]` markers claim — the Data Model section claims "verbs emit only `[H-MAD]` markers," but the four verbs' logic emits none. Resolve by correcting the claim (these lifecycle verbs are not phase transitions; guard refusals surface via `_require_orca` stderr).

## Should-fix
None

## Nit
- If JSON extraction were kept for run/remove, their test cases should assert the extracted output for parity with the list test — moot once run/remove are aligned to raw `--json` pass-through.
