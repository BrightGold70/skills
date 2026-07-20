# Design: orca-native-orchestration

## Executive Summary
Add five Orca-only `hmad-dispatch` verbs (`task-create`, `dispatch`, `await`, `gate-create`, `gate-resolve`) wrapping `orca orchestration *` with `jq`-parsed JSON output, a coordinator-handle helper + `env` mode indicator, `worker_done` emission blocks in the Codex/agy prompt refs, and docs — all additive within `h-mad/`; the scrape transport is untouched.

## Overview
Orchestration mode is opt-in and Orca-only: each new verb calls `_require_orca` (non-zero on cmux), resolves handles via the existing `_resolve_target` / the `HMAD_ORCA_COORDINATOR_TERMINAL` pin, emits the schema-v1 `orca orchestration *` command, and parses `--json` with tolerant `jq`. The six existing transport verbs and all cmux arms are unchanged.

## Architecture Overview
```
task-create <label> <specfile> → orca orchestration task-create --spec "$(cat file)" --task-title <label> --json → taskId
dispatch <agent> <task_id>     → orca orchestration dispatch --task <id> --to <handle> --return-preamble --json
await <task_id> [--timeout s]  → orca orchestration check --terminal <coord> --wait --types worker_done --timeout-ms <ms> --json
                                  → jq filter messages where taskId==<id> → first match (report-path/files-modified)
gate-create <task_id> <q> [opts]→ orca orchestration gate-create --task <id> --question <q> [--options <json>] --json → gateId
gate-resolve <gate_id> <text>  → orca orchestration gate-resolve --id <gate> --resolution <text> --json
```

## Detailed Design

### D1 — Guards + helpers
```bash
_require_orca() {  # $1 verb-name — non-zero + message unless substrate=orca
  local sub; sub="$(_detect_substrate)" || return 1
  [ "$sub" = "orca" ] || { echo "hmad-dispatch: '$1' requires orchestration mode (substrate=orca); current substrate=$sub" >&2; return 2; }
}
_coordinator() {  # echo the coordinator handle or fail with a message
  if [ -n "${HMAD_ORCA_COORDINATOR_TERMINAL:-}" ]; then printf '%s\n' "$HMAD_ORCA_COORDINATOR_TERMINAL"
  else echo "hmad-dispatch: set HMAD_ORCA_COORDINATOR_TERMINAL (the H-MAD coordinator's Orca terminal handle)" >&2; return 1; fi
}
_orchestration_active() {  # 0 iff substrate=orca AND coordinator pinned
  local sub; sub="$(_detect_substrate)" 2>/dev/null || return 1
  [ "$sub" = "orca" ] && [ -n "${HMAD_ORCA_COORDINATOR_TERMINAL:-}" ]
}
```

### D2 — Verb implementations (FR-1)
A small arg-guard helper is used by every verb (Should-fix — no empty required args reach `orca`):
```bash
_need() {  # $1 value, $2 name — non-zero + message if empty
  [ -n "${1:-}" ] || { echo "hmad-dispatch: missing required argument: $2" >&2; return 2; }
}
```
**Coordinator injected into the task spec (Must-fix).** The worker runs in its own shell that may NOT have `HMAD_ORCA_COORDINATOR_TERMINAL` exported. So `task-create` — run by the orchestrator — **requires** the `HMAD_ORCA_COORDINATOR_TERMINAL` pin (via `_coordinator`, failing fast if unset) and **prepends** the coordinator handle into the spec text it registers; the worker reads it from its dispatched task/preamble. Because the pin is enforced, a successfully-created task always carries the `[H-MAD]` line. The `worker_done` prompt block (D4) references "the coordinator handle in your task spec", never an env var.
```bash
_cmd_task_create() {  # $1 label, $2 specfile
  _require_orca task-create || return $?
  _need "$1" label || return $?; _need "$2" specfile || return $?
  [ -f "$2" ] || { echo "hmad-dispatch: spec file not found: $2" >&2; return 2; }
  local coord spec
  coord="$(_coordinator)" || return 1   # ENFORCED: orchestration mode requires the coordinator pin,
                                        # so the [H-MAD] line is always present in a successfully-created task
  spec="[H-MAD] worker_done coordinator handle (use as --to): ${coord}

$(cat "$2")"
  orca orchestration task-create --spec "$spec" --task-title "$1" --json \
    | jq -r '.result.taskId // .taskId // .result.id // .id // empty'
}
_cmd_dispatch() {  # $1 agent, $2 task_id
  _require_orca dispatch || return $?
  _need "$1" agent || return $?; _need "$2" task_id || return $?
  local target; target="$(_resolve_target "$1")" || return 1
  orca orchestration dispatch --task "$2" --to "$target" --return-preamble --json
}
_cmd_await() {  # $1 task_id, [--timeout <s>]
  _require_orca await || return $?
  _need "$1" task_id || return $?
  local task="$1"; shift
  local timeout=600
  while [ $# -gt 0 ]; do case "$1" in --timeout) timeout="$2"; shift 2 ;; *) shift ;; esac; done
  local coord; coord="$(_coordinator)" || return 1
  orca orchestration check --terminal "$coord" --wait --types worker_done --timeout-ms "$(( timeout * 1000 ))" --json \
    | jq -c --arg t "$task" '(.result.messages // .messages // []) | map(select((.taskId // .payload.taskId // .["task-id"]) == $t)) | .[0] // empty'
}
_cmd_gate_create() {  # $1 task_id, $2 question, [$3 options-json]
  _require_orca gate-create || return $?
  _need "$1" task_id || return $?; _need "$2" question || return $?
  if [ -n "${3:-}" ]; then
    orca orchestration gate-create --task "$1" --question "$2" --options "$3" --json | jq -r '.result.gateId // .gateId // .result.id // .id // empty'
  else
    orca orchestration gate-create --task "$1" --question "$2" --json | jq -r '.result.gateId // .gateId // .result.id // .id // empty'
  fi
}
_cmd_gate_resolve() {  # $1 gate_id, $2 resolution
  _require_orca gate-resolve || return $?
  _need "$1" gate_id || return $?; _need "$2" resolution || return $?
  orca orchestration gate-resolve --id "$1" --resolution "$2" --json
}
```
`main`'s case gains: `task-create) _cmd_task_create "$@" ;;` `dispatch) _cmd_dispatch "$@" ;;` `await) _cmd_await "$@" ;;` `gate-create) _cmd_gate_create "$@" ;;` `gate-resolve) _cmd_gate_resolve "$@" ;;`.

### D3 — `env` mode indicator (FR-2)
`_cmd_env`, after printing the substrate + agent mapping, appends one line: `if _orchestration_active; then echo "orchestration: on"; else echo "orchestration: off"; fi`.

### D4 — Agent `worker_done` emission (FR-3)
Add a delimited "Orchestration mode (Orca)" block to `references/codex-implementer-prompt.md` and `references/agy-spec-reviewer-prompt.md`. **The coordinator handle comes from the task spec** (the orchestrator's `task-create` prepends a `[H-MAD] worker_done coordinator handle (use as --to): <handle>` line — D2), NOT from an env var the worker's shell may lack:
> **Orchestration mode (Orca only).** If this task was delivered via `orca orchestration dispatch` (you were given a `task-id`), then on completion — in addition to printing your STATUS/verdict — emit:
> `orca orchestration send --to <COORDINATOR_HANDLE> --type worker_done --task-id <task-id> --report-path <your-report-file> --files-modified <comma-separated-paths>`
> where `<COORDINATOR_HANDLE>` is the value on the `[H-MAD] worker_done coordinator handle (use as --to):` line at the top of your task spec (do NOT rely on a shell env var). The `--from` sender must match your dispatched terminal handle. This lets the coordinator collect your result structurally (no screen scrape). If that line is absent from your spec, skip the `worker_done` emission and just print your STATUS/verdict as usual (the coordinator falls back to reading your terminal).

### D5 — Docs (FR-4)
- `references/orchestration-mode.md` (new): the five verbs, the coordinator pin, the `task-create → dispatch → worker_done → await → gate` flow, the worker_done contract, and the fallback rule (scrape transport when cmux or no coordinator).
- `SKILL.md`: a short "Orchestration mode (Orca)" subsection under the dispatch docs — states that on Orca with a coordinator pin, dispatch/verdict/gates SHOULD use the orchestration verbs (structured, no scrape), pointing to `references/orchestration-mode.md`; the scrape flow (`send`/`read`/`wait`) is the universal fallback. (Additive; frontmatter unchanged.)

## Components Changed / Added
| Component | File path | Change type | Purpose |
|---|---|---|---|
| guards + 5 verbs + `_orchestration_active` + `env` line + main-case arms | `h-mad/scripts/hmad-dispatch.sh` | modify | FR-1, FR-2, FR-5 |
| `worker_done` block | `h-mad/references/codex-implementer-prompt.md` | modify | FR-3 |
| `worker_done` block | `h-mad/references/agy-spec-reviewer-prompt.md` | modify | FR-3 |
| orchestration-mode flow doc | `h-mad/references/orchestration-mode.md` | new | FR-4 |
| orchestration-mode section | `h-mad/SKILL.md` | modify | FR-4 |
| tests | `h-mad/tests/test_hmad_dispatch.py` | modify | FR-1..5 |

## Implementation Order
1. D1 guards/helpers. 2. D2 verbs + main-case + tests. 3. D3 `env` indicator + test. 4. D4 prompt blocks. 5. D5 docs.

## Data Model / Schema Changes
None owned here. External `orca orchestration *` `--json` shapes are parsed tolerantly (`.result.taskId // .taskId // …`) so field-name drift degrades to `empty` rather than a crash.

## API / Interface Changes
Additive `hmad-dispatch` verbs: `task-create <label> <specfile>`, `dispatch <agent> <task_id>`, `await <task_id> [--timeout <s>]`, `gate-create <task_id> <question> [<options-json>]`, `gate-resolve <gate_id> <resolution>`. New env var `HMAD_ORCA_COORDINATOR_TERMINAL`. `env` output gains an `orchestration: on|off` line. No existing verb changes.

## Error Handling Strategy
- Non-orca substrate → `_require_orca` exits 2 with a message (FR-5). 
- Missing coordinator (for `await`) → `_coordinator` exits 1 with a message naming the env var.
- Missing/short JSON → tolerant `jq` yields `empty` (no crash); `await` timeout → underlying `orca` non-zero propagates.

## Test Strategy
All tests stub `orca` on an isolated PATH (argv capture + canned per-subcommand `--json` via `HMAD_STUB_ORCA_STDOUT`); no live Orca/network/coordinator (consistent with the existing harness).
- `task-create`: canned `{"result":{"taskId":"task_1"}}` → assert argv `orchestration task-create --spec <contents> --task-title <label> --json` and stdout `task_1`.
- `dispatch`: assert argv `orchestration dispatch --task task_1 --to <handle> --return-preamble --json` (with a pinned agent handle).
- `await`: canned `{"result":{"messages":[{"taskId":"task_1","report-path":"/r"}]}}` + `HMAD_ORCA_COORDINATOR_TERMINAL=term_coord` → assert argv `orchestration check --terminal term_coord --wait --types worker_done --timeout-ms 600000 --json` and stdout contains the task_1 message; `--timeout 60` → `--timeout-ms 60000`; missing coordinator → non-zero.
- `gate-create`/`gate-resolve`: assert argv (with/without options) and parsed `gateId`.
- Guard: under `HMAD_SUBSTRATE=cmux`, each verb exits non-zero (2) with the "requires orca" message.
- `env`: orca + coordinator → line `orchestration: on`; cmux → `orchestration: off`.
- Non-regression: the existing `send`/`read`/`wait`/`alive`/detection tests stay green (unchanged verbs).
- Validation: missing required args (empty `task_id`/`label`/`gate_id`/…) and a non-existent spec file each exit 2 with the naming message; a coordinator-pinned `task-create` embeds the `[H-MAD] worker_done coordinator handle` line in the `--spec` text (assert against the argv capture).

## Test Plan
- `h-mad/tests/test_hmad_dispatch.py`: add `test_task_create_*`, `test_dispatch_orch`, `test_await_*`, `test_gate_*`, `test_orch_verb_requires_orca`, `test_env_orchestration_indicator`.
- Verify: `python3 -m pytest h-mad/tests/test_hmad_dispatch.py -v`, then full `h-mad/tests/` at 5f.

## Invariant Compliance
- **Skill self-containment**: all edits within `h-mad/`; no cross-skill import. Complies.
- **Skill manifest integrity**: `SKILL.md` updated to document the new verbs; frontmatter `name`/`description` unchanged; the public contract grows additively. Complies.
- **Base — backward compatibility**: existing verbs/arms byte-identical; new verbs are additive and Orca-only. Complies.
- **Base — audit-gate / marker / single-source / operator-override / doc-template**: unaffected. Complies.

## Version History
- v1.0: Initial design draft.
- v1.2: Fix per `orca-native-orchestration.design.audit.v2.md` should-fix — `task-create` now ENFORCES the coordinator pin (via `_coordinator`, fail-fast if unset) so the `[H-MAD]` line is guaranteed present; worker prompt gains a fallback (absent line → skip worker_done, print STATUS as usual).
- v1.1: Fixes per `orca-native-orchestration.design.audit.v1.md` — Must-fix: coordinator handle is injected into the task spec by `task-create` (prepended `[H-MAD] worker_done coordinator handle` line) and the worker prompt reads it from the spec, not an env var. Should-fix: added `_need` arg-guard + spec-file existence check to every orchestration verb.
- v1.3: Design audit v3 (`orca-native-orchestration.design.audit.v3.md`) clean — no findings.
