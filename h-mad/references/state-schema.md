# State Schema — orchestrator_state in docs/.bkit-memory.json (v2.2)

Per-feature state under top-level key `orchestrator_state`. Pre-existing bkit fields preserved.

## Shape

```json
{
  "existing_bkit_fields": "...",
  "orchestrator_state": {
    "<feature-slug>": {
      "feature": "<feature-slug>",
      "started_ts": "2026-05-22T15:32:01Z",
      "last_completed_phase": 4,
      "current_phase": 5,
      "phase": "step5",
      "autonomous_entry_ts": "2026-05-22T16:10:44Z",
      "audit_cycles": { "plan": 2, "design": 3, "impl_plan": 1 },
      "iterate_cycles": 0,
      "production_paths_needing_red_tests": [],
      "halt_reason": null,
      "halt_ts": null,
      "last_marker": "[H-MAD] <feature> phase4 gate_passed"
    }
  }
}
```

## Field semantics (v2.2)

| Field | Type | Description |
|---|---|---|
| `feature` | string | Feature slug (matches key in `orchestrator_state`) |
| `started_ts` | ISO datetime | When Phase 1 was entered |
| `last_completed_phase` | int 0–7 | Last phase that passed its gate |
| `current_phase` | int 0–7 | Phase currently executing (same as last_completed_phase+1 during normal flow) |
| `phase` | `"step5"` \| `"step6"` \| `"step7"` \| `null` | Hook-arm flag. Non-null = TDD gate active. Set to `null` on phase completion or halt. |
| `autonomous_entry_ts` | ISO datetime \| null | When Phase 5 autonomous block was entered. Used by `/h-mad status` stale-flag heuristic. |
| `audit_cycles` | object | Count of audit iterations consumed per doc type. Keys: `plan`, `design`, `impl_plan`. |
| `iterate_cycles` | int | Count of inline iterate cycles consumed in Phase 6b. |
| `production_paths_needing_red_tests` | string[] | Paths that still need failing tests (populated by 5d, cleared by 5e). |
| `halt_reason` | string \| null | `"<phase>:<sub>:<desc>"` when halted; null otherwise. |
| `halt_ts` | ISO datetime \| null | When halt occurred. |
| `last_marker` | string | Last `[H-MAD]` marker emitted. |

## Concurrency rule

Only one feature may have `phase != null` at a time per machine. The PreToolUse TDD gate hook checks ALL features in `orchestrator_state` for a non-null `phase` — if any is active, it arms for that feature. Running two features through Phase 5 concurrently is not supported.

## Validation

Schema lives at `~/.claude/skills/h-mad/scripts/h_mad_state_schema.json`. Validate before writing:

```bash
python3 -c "
import json, jsonschema
schema = json.load(open('$HOME/.claude/skills/h-mad/scripts/h_mad_state_schema.json'))
state = json.load(open('docs/.bkit-memory.json'))
for feat, fs in state.get('orchestrator_state', {}).items():
    jsonschema.validate(fs, schema)
print('OK')
"
```
