# Plan: orca-native-orchestration

## Executive Summary
Add five opt-in orchestration-mode `hmad-dispatch` verbs — `task-create`, `dispatch`, `await`, `gate-create`, `gate-resolve` — wrapping the native `orca orchestration task-create/dispatch/check/gate-create/gate-resolve` respectively (the `await` verb wraps `orca orchestration check --wait`), plus a coordinator-handle + mode indicator, agent-prompt `worker_done` emission, and docs — additive, Orca-only, with the scrape transport untouched as the universal fallback.

> **Verb naming**: `hmad-dispatch` verb names are used throughout this plan (`task-create`, `dispatch`, **`await`**, `gate-create`, `gate-resolve`). Each wraps the like-named `orca orchestration` command, except **`await` → `orca orchestration check --wait`**.

## Overview
On Orca, replace screen-scraping for dispatch/verdict/gates with the native structured `orchestration` layer. The change is additive: new verbs that error on cmux, a mode indicator in `env`, agent-prompt instructions gated on orchestration mode, and documentation. Existing transport verbs are unchanged.

## Scope
In: new verbs + coordinator detection in `hmad-dispatch.sh`; `worker_done` blocks in the Codex/agy prompt refs; `SKILL.md` orchestration section; `references/orchestration-mode.md`; tests. Out: replacing the scrape loop, default-wiring the SKILL flow, coordinator auto-registration, `run`/`inbox`/`reply`/`task-update`.

## Goals
- G1 — five orchestration verbs wrap the native commands (FR-1).
- G2 — coordinator pin + `env` mode indicator (FR-2).
- G3 — agents emit `worker_done` in orchestration mode (FR-3).
- G4 — docs: SKILL section + orchestration-mode.md (FR-4).
- G5 — Orca-only verbs; scrape transport non-regressed (FR-5).

## Requirements
FR-1..FR-5 per spec.

## Implementation Strategy
1. `hmad-dispatch.sh`:
   - Add `_require_orca()` guard (non-zero + message on non-orca).
   - `_cmd_task_create`, `_cmd_dispatch`, `_cmd_await`, `_cmd_gate_create`, `_cmd_gate_resolve` — each calls `_require_orca`, resolves handles via the existing `_resolve_target`/coordinator pin, emits the schema-v1 `orca orchestration *` argv, and (task-create/await) parses `--json` via `jq` (tolerant paths).
   - `_orchestration_active()` (orca AND `HMAD_ORCA_COORDINATOR_TERMINAL` set); extend `_cmd_env` to print `orchestration: on|off`.
   - Wire the five verbs into `main`'s case.
2. Prompt refs (`codex-implementer-prompt.md`, `agy-spec-reviewer-prompt.md`): add an "Orchestration mode" block instructing the `worker_done` emission.
3. `SKILL.md`: "Orchestration mode (Orca)" section + reference link; `references/orchestration-mode.md`: full flow doc.
4. Tests (`test_hmad_dispatch.py`): stub `orca` (argv capture + canned `--json`); assert each verb's argv + JSON parse; assert cmux → non-zero; assert `env` mode indicator; assert existing transport verbs unchanged.

Untouched: `send`/`read`/`wait`/`alive`/`clear`/`notify`, detection, identity resolution, all cmux arms.

## Architecture Considerations
- Additive verbs — the public surface grows but no existing verb/semantic changes, so the scrape transport and cmux users are unaffected (base backward-compat).
- Orchestration mode is *opt-in*: verbs are Orca-only and require the coordinator pin; H-MAD's default loop is unchanged until a later wiring feature adopts it. This bounds risk given orchestration mode cannot be live-validated in this cmux session.
- Self-contained within `h-mad/` (Axis B). `SKILL.md` contract stays valid — new verbs documented; frontmatter unchanged.

## Deliverables
| Deliverable | Type | Satisfies |
|---|---|---|
| 5 orchestration verbs + `_require_orca` | shell | FR-1 |
| coordinator pin + `_orchestration_active` + `env` indicator | shell | FR-2 |
| `worker_done` blocks in codex/agy prompt refs | doc | FR-3 |
| `references/orchestration-mode.md` + `SKILL.md` section | doc | FR-4 |
| Orca-only guard + non-regression | shell/test | FR-5 |
| verb argv + JSON-parse + guard + env tests | test | FR-1..5 |

## Risks and Mitigation
| Risk | Impact | Mitigation |
|---|---|---|
| No live-Orca validation here | untested-against-real-orchestration | stub-argv + JSON-parse unit tests; explicit live-Orca-e2e carry item |
| `worker_done`/task correlation subtlety | await returns wrong/no message | follow schema notes verbatim (`--task-id`, sender=assignee); document the pin; `await` filters by task_id |
| Scope creep into the SKILL loop | over-build | ship verbs + opt-in docs only; default-wiring explicitly out-of-scope |

## Convention Prerequisites
- Feature branch `feature/orca-native-orchestration` (Phase 5c).
- Full `h-mad/tests/` green at Phase 5f.

## Success Criteria
- FR-1..5 ACs pass automated tests.
- Existing `test_hmad_dispatch.py` transport + detection tests stay green.
- `env` reports `orchestration: on/off` correctly.

## Out-of-Scope (confirmed from spec)
- Replacing the scrape transport; default-wiring the SKILL flow; coordinator auto-registration; `run`/`inbox`/`reply`/`task-update`.

## Next Steps
Agy plan audit → Phase 4 design.

## Version History
- v1.0: Initial plan draft.
- v1.1: Plan audit v1 fix — resolved verb-naming inconsistency; the plan now uses hmad-dispatch verb names (`task-create`/`dispatch`/`await`/`gate-create`/`gate-resolve`) consistently, with an explicit note that `await` wraps `orca orchestration check --wait`.
