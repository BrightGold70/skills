# Design: orca-automations-scheduled-e2e

## Executive Summary
Add `_cmd_automation_create/run/list/remove` to `hmad-dispatch.sh` (Orca-only, reusing the shipped `_require_orca` + `_json_extract`, `--prompt-file` file-indirection, explicit 2-arg cases per value-taking flag) with four `main()` cases, plus a SKILL.md HemaSuite scheduled-e2e usage section; additive, cmux/off-Orca unchanged.

## Overview
Four thin Orca-guarded lifecycle verbs wrapping `orca automations *`, following the Tier-3/M1 shape and reusing the shipped helpers (no new guard/extractor). HemaSuite consumption is documented usage.

## Architecture Overview
```
Operator / HemaSuite (SKILL.md documented usage)
  automation-create --name <e2e> --trigger cron --prompt-file <p> --provider agent --precheck "hpw doctor" --workspace <ws>
  automation-run <id> / automation-list / automation-remove <id>

hmad-dispatch.sh (all Orca-only; substrate!=orca → _require_orca non-zero, no orca call)
  _cmd_automation_create ─ _require_orca ─ orca automations create … --json ─ _json_extract '.result.id // .result.automationId // .id'
  _cmd_automation_run    ─ _require_orca ─ orca automations run <id> --json
  _cmd_automation_list   ─ _require_orca ─ orca automations list --json ─ _json_extract '.result | tojson'
  _cmd_automation_remove ─ _require_orca ─ orca automations remove <id> --json
```

## Detailed Design

### `_cmd_automation_create` (FR-1)
- Signature: `automation-create --name <n> --trigger <preset|cron|rrule> --prompt-file <path> [--provider <agent>] [--precheck <cmd>] [--repo <sel>|--workspace <sel>|--project <id>]`.
- Guard: `_require_orca automation-create || return $?`.
- Flag parse: `local name="" trig="" pf="" prov="" pre="" repo="" ws="" proj=""`; `while [ $# -gt 0 ]` with an explicit 2-arg `case` branch per value-taking flag (`--name) name="$2"; shift 2 ;;` etc. for `--trigger`/`--prompt-file`/`--provider`/`--precheck`/`--repo`/`--workspace`/`--project`; `*) shift ;;`).
- Required checks: `_need "$name" name || return $?`; `_need "$trig" trigger || return $?`; `_need "$pf" prompt-file || return $?`; `[ -f "$pf" ] || { echo "hmad-dispatch: prompt file not found: $pf" >&2; return 2; }`.
- Build `args=(automations create --name "$name" --trigger "$trig" --prompt "$(cat "$pf")")`; append `--provider "$prov"` / `--precheck "$pre"` / `--repo "$repo"` / `--workspace "$ws"` / `--project "$proj"` when non-empty; append `--json`.
- Extract id: `orca "${args[@]}" | _json_extract '.result.id // .result.automationId // .id'`.
- Note (schema-verified): `orca automations create` has only `--prompt <text>` (no native `--prompt-file`); `--prompt "$(cat "$pf")"` is required; e2e prompts are small (ARG_MAX non-concern); F-12 file-indirection is honored at the hmad-dispatch boundary.

### `_cmd_automation_run` (FR-2)
- Signature: `automation-run <id>`. Guard `_require_orca automation-run || return $?`; `_need "${1:-}" id || return $?`.
- `orca automations run "$1" --json` — orca's raw `--json` ack goes to stdout; **no `_json_extract`** (matches the plan's "pass id through, run"). Only `list` (which the plan says "passes through `.result`") uses `_json_extract '.result | tojson'`.

### `_cmd_automation_list` (FR-3)
- Signature: `automation-list`. Guard `_require_orca automation-list || return $?`.
- `orca automations list --json | _json_extract '.result | tojson'`.

### `_cmd_automation_remove` (FR-4)
- Signature: `automation-remove <id>`. Guard `_require_orca automation-remove || return $?`; `_need "${1:-}" id || return $?`.
- `orca automations remove "$1" --json` — orca's raw `--json` ack to stdout; **no `_json_extract`** (matches the plan's "pass id through, run"). Consistent with `run`; only `list` extracts.

### `main()` verb cases
Four new lines: `automation-create) _cmd_automation_create "$@" ;;` etc. Additive.

### SKILL.md HemaSuite scheduled-e2e usage section (FR-5/6)
Document the four verbs + the HemaSuite usage: schedule a nightly live-e2e via `automation-create --name anemia-e2e --trigger cron --prompt-file <p> --provider agent --precheck "hpw doctor" --workspace <hemasuite-ws>`; trigger ad-hoc `automation-run <id>`; enumerate `automation-list`; clean `automation-remove <id>`. State HemaSuite wiring is documented-usage-only and needs HemaSuite executing in an Orca workspace (no HemaSuite code in this feature).

## Components Changed / Added
| Component | File path | Change type | Purpose |
|---|---|---|---|
| `_cmd_automation_create` | `h-mad/scripts/hmad-dispatch.sh` | new | FR-1 |
| `_cmd_automation_run` | `h-mad/scripts/hmad-dispatch.sh` | new | FR-2 |
| `_cmd_automation_list` | `h-mad/scripts/hmad-dispatch.sh` | new | FR-3 |
| `_cmd_automation_remove` | `h-mad/scripts/hmad-dispatch.sh` | new | FR-4 |
| 4 `main()` cases | `h-mad/scripts/hmad-dispatch.sh` | modify | route verbs |
| SKILL.md HemaSuite usage section | `h-mad/SKILL.md` | modify | FR-5, FR-6 |
| Verb + doc tests | `h-mad/tests/test_hmad_dispatch.py` | modify | FR-1..FR-4/5/6 |

## Implementation Order
1. `_cmd_automation_create` + case + tests (RED→GREEN).
2. `_cmd_automation_run` + `_cmd_automation_list` + `_cmd_automation_remove` + cases + tests.
3. SKILL.md HemaSuite usage section + doc-presence test.

## Data Model / Schema Changes
None. No state-schema change. These verbs emit **no** new markers — they are operator/HemaSuite-invoked lifecycle wrappers, not orchestrator phase transitions (the base marker-discipline invariant governs phase transitions, which these are not). Substrate-guard refusals surface via `_require_orca`'s own stderr + non-zero exit.

## API / Interface Changes
Four new `hmad-dispatch` verbs (above). No new env knob. No change to existing verbs or the cmux path.

## Error Handling Strategy
- Substrate guard: `_require_orca` non-zero + stderr off-Orca (no `orca` call) — AC-1.5/2.3/3.3/4.3.
- Missing required arg (`--name`/`--trigger`/`--prompt-file` for create; `<id>` for run/remove): `_need` returns 2, no `orca` call — AC-1.6/2.2/4.2.
- `--prompt-file` missing on disk: return 2 before any `orca` call — AC-1.4.
- Empty `_json_extract` output → empty stdout (create id parse failure → empty; caller treats as failure).

## Test Strategy
Unit tests only (live-Orca e2e deferred). Reuse the `test_hmad_dispatch.py` stub-on-PATH harness. Per verb: argv assertion (stub captures exact `orca automations …` argv) + id/passthrough (canned `.result` → stdout) + substrate guard (cmux → non-zero, empty capture) + required-arg/missing-file guards. Doc test asserts the four verb names + `hpw doctor` in SKILL.md.

## Test Plan
- `test_automation_create_argv` — `automation-create --name nightly --trigger cron --prompt-file /tmp/p --provider agent` (`/tmp/p`=`RUN E2E`) → `orca automations create --name nightly --trigger cron --prompt RUN E2E --provider agent --json`.
- `test_automation_create_targeting_and_precheck` — `--precheck "hpw doctor" --repo r1` appended in argv.
- `test_automation_create_parses_id` — canned `{"result":{"id":"auto_9"}}` → stdout `auto_9`.
- `test_automation_create_missing_prompt_file` — `--prompt-file /tmp/nope` → returncode 2, no orca call.
- `test_automation_create_requires_name_and_trigger` — missing `--name` (or `--trigger`) → non-zero, no orca call.
- `test_automation_create_refuses_cmux` — cmux → non-zero, empty capture.
- `test_automation_run_argv_and_requires_id` — `automation-run auto_9` → `orca automations run auto_9 --json`; missing id → returncode 2.
- `test_automation_list_argv_and_passthrough` — `automation-list` → `orca automations list --json`; canned `.result` → stdout that JSON.
- `test_automation_remove_argv_and_requires_id` — `automation-remove auto_9` → `orca automations remove auto_9 --json`; missing id → returncode 2.
- `test_automation_verbs_refuse_cmux` — run/list/remove under cmux → non-zero, no orca call.
- `test_skill_documents_automation_usage` — SKILL.md contains `automation-create`, `automation-run`, `automation-list`, `automation-remove`, and `hpw doctor`.
- Verification: `python3.11 -m pytest h-mad/tests/test_hmad_dispatch.py -v`.

## Invariant Compliance
- **Audit-gate signal discipline**: N/A — no new gate; verbs signal via exit code (operational).
- **Single-source contract**: reuses shipped `_json_extract` (one extractor) + `_require_orca` (one guard) — no forked helper. Complies.
- **Standalone / no plugin dependency**: only `orca` + `jq`. Complies.
- **No new external dependency**: `orca` + `jq` already depended on. Complies.
- **Doc-template superset compliance**: plan/design/report under standard dirs, h-mad sections retained. Complies.
- **Operator-override preservation**: no gate change. Complies.
- **Backward compatibility**: no gate change; existing verbs/tests untouched. Complies.
- **Marker discipline**: guard refusals surface via `_require_orca` stderr + non-zero; the orchestrator/operator sees the failure. Complies.
- **Skill self-containment** (project): all logic inside `h-mad/`. Complies.
- **Skill manifest integrity** (project): SKILL.md gains a HemaSuite-usage section; frontmatter unchanged. Complies.

## Version History
- v1.0: Initial design draft.
- v2.0: Design-audit-v1 fixes — aligned run/remove to raw `--json` pass-through (no `_json_extract`, matching the plan; only `list` extracts), resolving the run pipeline contradiction (must-fix 1+2); corrected the Data Model claim (verbs emit no new markers; guard refusals surface via `_require_orca` stderr) (must-fix 3).
