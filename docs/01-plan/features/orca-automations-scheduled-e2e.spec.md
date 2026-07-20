# Spec: orca-automations-scheduled-e2e

## Executive Summary
Add four Orca-only `hmad-dispatch` automation-lifecycle verbs (create/run/list/remove) plus SKILL.md documentation of the HemaSuite scheduled-e2e usage, reusing the shipped `_require_orca` + `_json_extract`, additive with no non-Orca behavior change.

## Goal
Give operators a scriptable way to schedule, trigger, enumerate, and clean up long HemaSuite live-e2e / regression runs as Orca automations, without HemaSuite code changes and without altering any non-Orca path.

## Functional Requirements

### FR-1: `automation-create` verb
- **Description**: `hmad-dispatch automation-create --name <n> --trigger <preset|cron|rrule> --prompt-file <path> [--provider <agent>] [--precheck <cmd>] [--repo <sel>|--workspace <sel>|--project <id>]` wrapping `orca automations create --name <n> --trigger <t> --prompt <text> [--provider <p>] [--precheck <c>] [target] --json`. Orca-only. Prompt via file-indirection. Returns the automation id (via `_json_extract`).
- **Acceptance Criteria**:
  - AC-1.1: `automation-create --name nightly --trigger cron --prompt-file /tmp/p --provider agent` (contents of `/tmp/p` = `RUN E2E`) → argv `orca automations create --name nightly --trigger cron --prompt RUN E2E --provider agent --json`.
  - AC-1.2: `--precheck "hpw doctor"` and a targeting flag (`--repo r1`) are passed through in argv when given.
  - AC-1.3: canned `{"result":{"id":"auto_9"}}` → verb stdout `auto_9` (via `_json_extract` alternation `.result.id // .result.automationId // .id`).
  - AC-1.4: missing `--prompt-file` file → non-zero exit (returncode 2), no `orca` call.
  - AC-1.5: substrate=cmux → non-zero, no `orca` call.
  - AC-1.6: missing required `--name` or `--trigger` → non-zero exit, no `orca` call.

### FR-2: `automation-run` verb
- **Description**: `hmad-dispatch automation-run <id>` wrapping `orca automations run <id> --json`. Orca-only.
- **Acceptance Criteria**:
  - AC-2.1: `automation-run auto_9` → argv `orca automations run auto_9 --json`.
  - AC-2.2: missing `<id>` → non-zero (via `_need`), no `orca` call.
  - AC-2.3: substrate=cmux → non-zero, no `orca` call.

### FR-3: `automation-list` verb
- **Description**: `hmad-dispatch automation-list` wrapping `orca automations list --json`; passes through `.result`.
- **Acceptance Criteria**:
  - AC-3.1: `automation-list` → argv `orca automations list --json`.
  - AC-3.2: canned `.result` → stdout is that JSON (via `_json_extract '.result | tojson'`).
  - AC-3.3: substrate=cmux → non-zero, no `orca` call.

### FR-4: `automation-remove` verb
- **Description**: `hmad-dispatch automation-remove <id>` wrapping `orca automations remove <id> --json`. Orca-only.
- **Acceptance Criteria**:
  - AC-4.1: `automation-remove auto_9` → argv `orca automations remove auto_9 --json`.
  - AC-4.2: missing `<id>` → non-zero, no `orca` call.
  - AC-4.3: substrate=cmux → non-zero, no `orca` call.

### FR-5: HemaSuite scheduled-e2e usage docs (SKILL.md)
- **Description**: SKILL.md documents the HemaSuite usage: schedule a long live-e2e as a nightly Orca automation via `automation-create --name <e2e> --trigger cron --prompt-file <e2e-prompt> --provider agent --precheck "hpw doctor" --workspace <hemasuite-ws>`, trigger ad-hoc with `automation-run`, enumerate with `automation-list`, clean up with `automation-remove`. Explicitly states HemaSuite wiring is documented usage (no HemaSuite code) and requires HemaSuite executing in an Orca workspace.
- **Acceptance Criteria**:
  - AC-5.1: SKILL.md contains a section naming the four verbs and the HemaSuite scheduled-e2e usage (with `--precheck` + `--provider agent`).
  - AC-5.2: The section states HemaSuite wiring is documented-usage-only and needs an Orca workspace.
  - AC-5.3: A doc-presence test asserts the four verb names and `hpw doctor` appear in SKILL.md.

### FR-6: additive / no non-Orca change
- **Description**: Purely additive — no existing verb, the cmux path, or gate logic changes.
- **Acceptance Criteria**:
  - AC-6.1: Existing `test_hmad_dispatch.py` tests stay green.
  - AC-6.2: substrate=cmux → no automation verb invokes `orca`.

## Non-Functional Requirements
- Performance: N/A (single Orca call per invocation).
- Security: the long prompt goes through `--prompt-file` indirection (F-12); targeting/precheck passed through the args array (no shell interpolation).
- Compatibility: additive; reuses shipped `_require_orca` + `_json_extract`; no new dependency (`orca` + `jq`).

## Out-of-Scope
- Live-Orca e2e (deferred carry).
- HemaSuite code changes / wiring into a HemaSuite command (documented usage only; blocked on Orca-hosted HemaSuite).
- `automations show/runs/edit` subcommands (additive follow-on).

## Assumptions
- `orca automations create --json` returns the automation id under one of `.result.id` / `.result.automationId` / `.id` (defensive `_json_extract` alternation).
- Targeting flags (`--repo`/`--workspace`/`--project`) are passed through opaquely as the operator provides them.

## Version History
- v1.0: Initial specification draft.
