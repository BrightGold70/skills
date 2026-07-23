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
| `substrate` | object \| null | **Optional.** Dispatch environment, written at Phase-5 start from `hmad-dispatch env`: `{"name":"orca","agents":{"codex":"term_…","agy":"term_…"}}`. Additive — records predating it stay valid, and `required` is unchanged. `h_mad_telemetry.py record` copies it onto the run row (J11). |

## Concurrency rule

Only one feature may have `phase != null` at a time per machine. The PreToolUse TDD gate hook checks ALL features in `orchestrator_state` for a non-null `phase` — if any is active, it arms for that feature. Running two features through Phase 5 concurrently is not supported.

## Validation

Two schemas live in `~/.claude/skills/h-mad/scripts/`:

| Schema | Governs |
|---|---|
| `h_mad_state_schema.json` | **strict** v2.2 — required of every new record |
| `h_mad_state_schema_historical.json` | **historical** — what pre-v2.2 runs actually wrote |

Validate a whole store:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_validate.py docs/.bkit-memory.json
# STATE: PASS strict=9 historical=55 invalid=0
```

Verify a record you just wrote meets v2.2:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_validate.py \
  docs/.bkit-memory.json --feature <feature> --strict-only
```

Parse the `STATE:` token, not the exit code — the validator exits 0 on any
verdict and reserves non-zero for operational errors (missing file, bad JSON,
unknown feature), so a FAIL never registers as a tool failure.

### Why two tiers

v2.2 was aspirational: nothing enforced it at write time, and
`additionalProperties: false` rejected every key a run invented. An
established store drifted to 38 distinct record shapes over 53 distinct keys —
five spellings of the merge sha (`merge_commit`, `merge_sha`, `merged_sha`,
`merged`, `shipped_sha`), six of "phase 7 finished" (`phase7_closure`,
`phase7`, `step7`, `step7_closure`, `"7"`, `7`), and timestamps as both ISO
strings and unix epochs. Single-tier validation therefore always failed, which
made the documented check useless, so it went unrun and the drift compounded.

The historical tier requires only `current_phase`, `last_completed_phase`, and
`phase` — the three fields present in every record observed — so historical
drift passes while a genuinely broken record still fails. The strict tier plus
`--strict-only` on the write path is what stops new drift.

**Never invent a key.** If a run needs a field v2.2 lacks, add it to
`h_mad_state_schema.json` first.
