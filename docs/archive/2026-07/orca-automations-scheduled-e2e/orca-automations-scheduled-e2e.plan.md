# Plan: orca-automations-scheduled-e2e

## Executive Summary
Add `_cmd_automation_create/run/list/remove` to `hmad-dispatch.sh` (Orca-only, reusing the shipped `_require_orca` + `_json_extract`, `--prompt-file` indirection for the long prompt) with four `main()` cases, plus a SKILL.md HemaSuite scheduled-e2e usage section; additive, cmux/off-Orca behavior unchanged.

## Overview
The final Orca-adaptation candidate: four thin Orca-guarded lifecycle verbs wrapping `orca automations *`, letting HemaSuite's long operator-triggered validation runs be scheduled/triggered/enumerated/cleaned as Orca automations. HemaSuite consumption is documented usage (blocked on Orca-hosted HemaSuite), consistent with M1's scoping.

## Scope
- In: `automation-create` (prompt via `--prompt-file`), `automation-run`, `automation-list`, `automation-remove` verbs; four `main()` cases; a SKILL.md HemaSuite scheduled-e2e usage section; stub tests.
- Out: live-Orca e2e; HemaSuite code; `automations show/runs/edit`.

## Goals
- G1: create/run/list/remove verbs drive `orca automations *` (FR-1..FR-4).
- G2: HemaSuite scheduled-e2e usage documented; off-Orca-safe (FR-5, FR-6).
- G3: reuse shipped `_require_orca` + `_json_extract` (single-source, no forked guard/extractor).
- G4: long prompt via `--prompt-file` file-indirection (F-12); no bare argv blob.
- G5: every `orca automations …` argv reconciled **manually at authoring time** against the **orca automations** usage strings enumerated in `orca agent-context --json` schema v1 (the schema inventory that lists the `automations create/run/list/remove` commands). Policy; argv pinned via stub tests; no automated build-check deliverable — per Tier-3/M1.

## Requirements
- FR-1 create; FR-2 run; FR-3 list; FR-4 remove; FR-5 HemaSuite usage docs; FR-6 additive.

## Implementation Strategy
- **Layer 1 — verbs** (`h-mad/scripts/hmad-dispatch.sh`): add `_cmd_automation_create/run/list/remove` following the Tier-3/M1 shape — `_require_orca <verb> || return $?` guard, `_need` for required args, a `while [ $# -gt 0 ]` flag loop building an `args=(automations …)` array, always append `--json`. For `create`: parse each value-taking flag with its OWN explicit 2-arg `case` branch (`--name`, `--trigger`, `--provider`, `--precheck`, `--repo`, `--workspace`, `--project` each `shift 2`; `--prompt-file` `shift 2`) so targeting flags are captured cleanly, never mis-parsed as unrecognized; `--prompt-file` → `[ -f "$f" ] || return 2` then `args+=(--prompt "$(cat "$f")")`; extract id via `_json_extract '.result.id // .result.automationId // .id'`. **Note (schema-verified):** `orca automations create` exposes only `--prompt <text>` (no native `--prompt-file` flag in schema v1), so `--prompt "$(cat "$f")"` is the required form; e2e prompts are small, so ARG_MAX is not a practical concern — the file-indirection is at the hmad-dispatch boundary (F-12), which is the discipline the invariant targets. For `list`: `_json_extract '.result | tojson'`. For `run`/`remove`: `_need id`, pass id through, run. Add four `main()` cases. **Reuse `_require_orca` + `_json_extract` verbatim — no new helpers** (single-source).
- **Layer 2 — SKILL.md** HemaSuite scheduled-e2e usage section: document `automation-create --name <e2e> --trigger cron --prompt-file <p> --provider agent --precheck "hpw doctor" --workspace <ws>` + run/list/remove; state HemaSuite wiring is documented-usage-only and needs an Orca workspace.
- **Deliberately untouched**: existing verbs, cmux path, Tier-1/2/3/M1 verbs.

## Architecture Considerations
- **Single-source**: reuse shipped `_json_extract` + `_require_orca` — a second extractor/guard would breach the Axis-B single-source contract.
- **File-indirection (F-12)**: the automation `--prompt` (a long e2e instruction) comes from `--prompt-file`, never a bare argv blob — the same discipline the worktree-create verb uses.
- **Opaque targeting**: `--repo`/`--workspace`/`--project` are passed through as the operator provides them; the verb does not interpret them (reconciled against schema at design).
- **Best-effort / no gate coupling**: these verbs are operator/HemaSuite-invoked, not wired into an H-MAD gate — no cmux-path impact.

## Deliverables
| Deliverable | Type | Satisfies |
|---|---|---|
| `_cmd_automation_create` verb | CLI subcommand | FR-1 |
| `_cmd_automation_run` verb | CLI subcommand | FR-2 |
| `_cmd_automation_list` verb | CLI subcommand | FR-3 |
| `_cmd_automation_remove` verb | CLI subcommand | FR-4 |
| 4 `main()` cases | CLI routing | FR-1..FR-4 |
| SKILL.md HemaSuite usage section | doc | FR-5, FR-6 |
| Stub tests | pytest (`test_hmad_dispatch.py`) | FR-1..FR-4, FR-5 (doc), FR-6 |

## Risks and Mitigation
| Risk | Impact | Mitigation |
|---|---|---|
| Live-Orca e2e gap | Verbs unvalidated against real automations runtime | Stub-test argv/JSON; deferred carry |
| `create --json` id key unknown | id parse breaks | Defensive `_json_extract` alternation `.result.id // .result.automationId // .id` (Tier-3 precedent); test pins canned key |
| Long prompt on argv leaks/fragments | Security / correctness | `--prompt-file` indirection; test asserts file contents reach `--prompt`, missing file → exit 2 |
| Targeting flag mis-modeled | Wrong workspace scheduled | Pass through opaquely; document HemaSuite-recommended `--workspace` form |

## Convention Prerequisites
- Feature branch `feature/182-orca-automations-scheduled-e2e` (Phase 5c).
- Tier-1 + Tier-3 shipped (`_require_orca`, `_json_extract` on main).

## Success Criteria
- All spec ACs pass (stub argv + id/passthrough + guard + prompt-file + doc-presence).
- `test_hmad_dispatch.py` full file green (existing verbs untouched).
- SKILL.md documents the HemaSuite scheduled-e2e usage with `--precheck`/`--provider agent`.
- Every `orca automations …` argv matches schema v1.

## Out-of-Scope (confirmed from spec)
- Live-Orca e2e; HemaSuite code; `automations show/runs/edit`.

## Next Steps
Approve plan v1.0 → agy audit → Phase 4 design.

## Version History
- v1.0: Initial plan draft.
- v2.0: Plan-audit-v1 fixes — G5 now references the orca automations usage strings within `agent-context --json` (should-fix); noted orca has no native `--prompt-file` flag so `--prompt "$(cat)"` is required + ARG_MAX non-concern (nit 1); each value-taking create flag gets an explicit 2-arg case (nit 2).
