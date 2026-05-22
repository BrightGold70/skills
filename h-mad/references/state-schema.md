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

| Field | Type | Purpose |
|---|---|---|
| `feature` | string | Slug (matches key) |
| `started_ts` | ISO 8601 | When `/h-mad "<feature>"` first ran |
| `last_completed_phase` | int 0–7 | Highest phase that passed its gate (v2.2: was 0–9 in v1) |
| `current_phase` | int 0–7 | Phase currently in progress |
| `phase` | enum `step5 \| step6 \| step7 \| null` | Hook-readable tag. Only `step5` arms hook. (v2.2: was step7/step8/step9 in v1) |
| `autonomous_entry_ts` | ISO 8601 \| null | Set on Phase 5 entry; enables future watchdog |
| `audit_cycles.plan` / `.design` / `.impl_plan` | int ≥ 0 | Per-phase cycle count for 5-cap. (v2.2: `impl_plan` key NEW for Phase 5b) |
| `iterate_cycles` | int ≥ 0 | Phase 6b cap |
| `production_paths_needing_red_tests` | array of strings | Captured by writing-plans parse; hook allowlist hint (deferred) |
| `halt_reason` | string \| null | `<phase>:<sub-step>:<short-description>` |
| `halt_ts` | ISO 8601 \| null | Populated alongside halt_reason |
| `last_marker` | string | Most recent `[H-MAD]` log line |

## Concurrency rule

Only ONE feature can have `phase = "step5"` at a time. If user tries `/h-mad do "<feature>"` for a second feature while another is in Phase 5, refuse with explicit error.

Other phases (manual) can be in-flight for multiple features simultaneously.

## Validation

Schema lives at `scripts/h_mad_state_schema.json`. Validate before writing:

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
