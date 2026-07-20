# Implementation Plan: orca-native-orchestration

> Source: docs/02-design/features/orca-native-orchestration.design.md (post-audit v3, per orca-native-orchestration.design.audit.v1.md .. .audit.v3.md)
> Branch target: feature/orca-native-orchestration

## Executive Summary
Three tasks: (1) add the guards/helpers + five orchestration verbs + `env` indicator to `h-mad/scripts/hmad-dispatch.sh` with tests; (2) add `worker_done` blocks to the Codex/agy prompt refs; (3) write `references/orchestration-mode.md` + the `SKILL.md` section. All additive within `h-mad/`; scrape transport untouched.

## Task 1: Orchestration verbs + guards + env indicator (FR-1, FR-2, FR-5)

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch.py`

**Description**: Add `_need`, `_require_orca`, `_coordinator`, `_orchestration_active`, the five `_cmd_*` verb functions, the `main`-case arms, and the `_cmd_env` `orchestration: on|off` line — exactly as the design D1/D2/D3 code blocks specify. `task-create` enforces the coordinator pin and prepends the `[H-MAD] worker_done coordinator handle (use as --to): <handle>` line to the spec.

**Code structure**: use the design's D1 + D2 + D3 code blocks verbatim (`_need`, `_require_orca`, `_coordinator`, `_orchestration_active`, `_cmd_task_create` [enforced pin + arg/file guards + spec prepend], `_cmd_dispatch`, `_cmd_await`, `_cmd_gate_create`, `_cmd_gate_resolve`, the five `main`-case arms, and the `env` indicator line). Do NOT touch any existing verb, cmux arm, detection, or identity resolution.

**Acceptance Criteria**:
- [ ] AC-1.1: `task-create <label> <specfile>` (orca; `HMAD_ORCA_COORDINATOR_TERMINAL=term_coord`; canned `{"result":{"taskId":"task_1"}}`) → argv `orca orchestration task-create --spec <spec> --task-title <label> --json`, the `<spec>` begins with `[H-MAD] worker_done coordinator handle (use as --to): term_coord`, and stdout is `task_1`.
- [ ] AC-1.2: `task-create` with `HMAD_ORCA_COORDINATOR_TERMINAL` unset → non-zero exit (naming the env var); with a missing spec file → exit 2 ("spec file not found").
- [ ] AC-1.3: `dispatch <agent> task_1` (pinned agent handle) → argv `orca orchestration dispatch --task task_1 --to <handle> --return-preamble --json`.
- [ ] AC-1.4: `await task_1` (coordinator `term_coord`; canned `{"result":{"messages":[{"taskId":"task_1","report-path":"/r"}]}}`) → argv `orca orchestration check --terminal term_coord --wait --types worker_done --timeout-ms 600000 --json`, stdout contains the `task_1` message; `--timeout 60` → `--timeout-ms 60000`; coordinator unset → non-zero.
- [ ] AC-1.5: `gate-create task_1 "q?"` → argv `orca orchestration gate-create --task task_1 --question q? --json` → parsed `gateId`; with an options arg → adds `--options <json>`. `gate-resolve g1 "ok"` → argv `orca orchestration gate-resolve --id g1 --resolution ok --json`.
- [ ] AC-1.6: each verb under `HMAD_SUBSTRATE=cmux` → exit 2 with the "requires orchestration mode (substrate=orca)" message.
- [ ] AC-1.7: missing required args (`task-create` no label, `dispatch` no task_id, `gate-resolve` no gate_id/resolution) → exit 2 with "missing required argument".
- [ ] AC-1.8: `env` with orca + `HMAD_ORCA_COORDINATOR_TERMINAL` set → prints `orchestration: on`; cmux (or orca without the pin) → `orchestration: off`. Existing `env` substrate/agent lines unchanged.
- [ ] AC-1.9 (non-regression): existing `send`/`read`/`wait`/`alive`/detection tests remain green.

**Dependencies on other tasks**: None.

---

## Task 2: Agent `worker_done` prompt blocks (FR-3)

**Production files**: `h-mad/references/codex-implementer-prompt.md`, `h-mad/references/agy-spec-reviewer-prompt.md`
**Test file**: `h-mad/tests/test_hmad_dispatch.py`

**Description**: Add the delimited "Orchestration mode (Orca only)" block from design D4 to both prompt refs: the worker emits `orca orchestration send --to <COORDINATOR_HANDLE> --type worker_done --task-id <task-id> --report-path <file> --files-modified <csv>`, where `<COORDINATOR_HANDLE>` is read from the `[H-MAD] worker_done coordinator handle (use as --to):` line at the top of the task spec; fallback: if the line is absent, skip worker_done and print STATUS as usual.

**Acceptance Criteria**:
- [ ] AC-2.1: both `codex-implementer-prompt.md` and `agy-spec-reviewer-prompt.md` contain a block with the strings `worker_done`, `--task-id`, `--report-path`, and `[H-MAD] worker_done coordinator handle` (assert the substrings exist in each file).

**Dependencies on other tasks**: None.

---

## Task 3: Docs — orchestration-mode.md + SKILL.md section (FR-4)

**Production files**: `h-mad/references/orchestration-mode.md` (new), `h-mad/SKILL.md`
**Test file**: none (docs; existing doc-template test must stay green).

**Description**: Create `references/orchestration-mode.md` documenting the five verbs, the coordinator pin, the `task-create → dispatch → worker_done → await → gate` flow, the worker_done contract, and the scrape-fallback rule. Add a short "Orchestration mode (Orca)" subsection to `SKILL.md` under the dispatch docs, pointing to it; note the scrape flow is the universal fallback. Additive; SKILL.md frontmatter unchanged.

**Acceptance Criteria**:
- [ ] AC-3.1: `references/orchestration-mode.md` exists and contains the five verb names + `HMAD_ORCA_COORDINATOR_TERMINAL` + `worker_done`; `SKILL.md` references `references/orchestration-mode.md`.

**Dependencies on other tasks**: Task 1 (verbs), Task 2 (worker_done contract) — docs describe them.

## Version History
- v1.0: Initial implementation plan draft.
