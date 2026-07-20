# Implementation Plan: orca-automations-scheduled-e2e

> Source: docs/02-design/features/orca-automations-scheduled-e2e.design.md (post-audit v2)
> Branch target: feature/182-orca-automations-scheduled-e2e

## Executive Summary
One task: add `_cmd_automation_create/run/list/remove` (+ 4 `main()` cases) to `hmad-dispatch.sh` reusing the shipped `_require_orca`/`_json_extract`, plus a SKILL.md HemaSuite scheduled-e2e usage section, with stub tests. Additive.

## Task 1: automation-verbs-and-usage-docs

**Production file**: `h-mad/scripts/hmad-dispatch.sh` (+ `h-mad/SKILL.md`)
**Test file**: `h-mad/tests/test_hmad_dispatch.py` (additions)

**Description**: Add four Orca-only automation lifecycle verbs following the Tier-3/M1 shape (each `_require_orca <verb> || return $?`; `create` builds argv via explicit per-flag 2-arg cases + `--prompt-file` indirection + `_json_extract` id; `list` uses `_json_extract '.result | tojson'`; `run`/`remove` emit raw `orca … --json`), wire four `main()` cases, add a SKILL.md HemaSuite usage section. Reuse the shipped `_require_orca` + `_json_extract` — no new helpers.

**Code structure**:
```bash
_cmd_automation_create() {   # --name <n> --trigger <t> --prompt-file <p> [--provider <a>] [--precheck <c>] [--repo|--workspace|--project <sel>]
  _require_orca automation-create || return $?
  local name="" trig="" pf="" prov="" pre="" repo="" ws="" proj=""
  while [ $# -gt 0 ]; do case "$1" in
    --name) name="$2"; shift 2 ;;      --trigger) trig="$2"; shift 2 ;;
    --prompt-file) pf="$2"; shift 2 ;; --provider) prov="$2"; shift 2 ;;
    --precheck) pre="$2"; shift 2 ;;   --repo) repo="$2"; shift 2 ;;
    --workspace) ws="$2"; shift 2 ;;   --project) proj="$2"; shift 2 ;;
    *) shift ;; esac; done
  _need "$name" name || return $?; _need "$trig" trigger || return $?; _need "$pf" prompt-file || return $?
  [ -f "$pf" ] || { echo "hmad-dispatch: prompt file not found: $pf" >&2; return 2; }
  local args=(automations create --name "$name" --trigger "$trig" --prompt "$(cat "$pf")")
  [ -n "$prov" ] && args+=(--provider "$prov")
  [ -n "$pre" ]  && args+=(--precheck "$pre")
  [ -n "$repo" ] && args+=(--repo "$repo")
  [ -n "$ws" ]   && args+=(--workspace "$ws")
  [ -n "$proj" ] && args+=(--project "$proj")
  args+=(--json)
  orca "${args[@]}" | _json_extract '.result.id // .result.automationId // .id'
}

_cmd_automation_run() {   # <id>
  _require_orca automation-run || return $?
  _need "${1:-}" id || return $?
  orca automations run "$1" --json
}

_cmd_automation_list() {
  _require_orca automation-list || return $?
  orca automations list --json | _json_extract '.result | tojson'
}

_cmd_automation_remove() {   # <id>
  _require_orca automation-remove || return $?
  _need "${1:-}" id || return $?
  orca automations remove "$1" --json
}

# main() case additions:
#   automation-create) _cmd_automation_create "$@" ;;
#   automation-run)    _cmd_automation_run "$@" ;;
#   automation-list)   _cmd_automation_list "$@" ;;
#   automation-remove) _cmd_automation_remove "$@" ;;
```
```markdown
# SKILL.md — new "Scheduling HemaSuite live-e2e as Orca automations (Orca only)" subsection:
# automation-create --name anemia-e2e --trigger cron --prompt-file <p> --provider agent --precheck "hpw doctor" --workspace <ws>
# automation-run <id> / automation-list / automation-remove <id>
# HemaSuite wiring is documented-usage-only (no HemaSuite code) and needs HemaSuite executing in an Orca workspace.
```

**Acceptance Criteria**:
- [ ] AC-1.1: `automation-create --name nightly --trigger cron --prompt-file /tmp/p --provider agent` (`/tmp/p`=`RUN E2E`) → argv `orca automations create --name nightly --trigger cron --prompt RUN E2E --provider agent --json`.
- [ ] AC-1.2: `--precheck "hpw doctor" --repo r1` appended in argv.
- [ ] AC-1.3: canned `{"result":{"id":"auto_9"}}` → stdout `auto_9`.
- [ ] AC-1.4: `--prompt-file /tmp/nope` (missing) → returncode 2, no orca call.
- [ ] AC-1.5: missing `--name` (or `--trigger`) → non-zero, no orca call.
- [ ] AC-1.6: substrate=cmux → non-zero, no orca call.
- [ ] AC-2.1: `automation-run auto_9` → argv `orca automations run auto_9 --json`; raw stub stdout passed through.
- [ ] AC-2.2: `automation-run` (no id) → returncode 2, no orca call.
- [ ] AC-3.1: `automation-list` → argv `orca automations list --json`; canned `{"result":{"x":1}}` → stdout `{"x":1}`.
- [ ] AC-4.1: `automation-remove auto_9` → argv `orca automations remove auto_9 --json`; `automation-remove` (no id) → returncode 2.
- [ ] AC-5.1: substrate=cmux for run/list/remove → non-zero, no orca call.
- [ ] AC-6.1: doc-presence test `test_skill_documents_automation_usage` asserts SKILL.md contains `automation-create`, `automation-run`, `automation-list`, `automation-remove`, and `hpw doctor`.
- [ ] AC-6.2: existing `test_hmad_dispatch.py` tests stay green.

**Dependencies on other tasks**: None

## Version History
- v1.0: Initial implementation plan draft.
