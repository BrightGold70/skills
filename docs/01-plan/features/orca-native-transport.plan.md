# Plan: orca-native-transport

## Executive Summary
Correct the `hmad-dispatch` Orca branches (`wait`, `read`) to Orca's confirmed `agent-context` schema v1, lock structured `terminal list --json` liveness, and update `agent-substrate.md` — a bounded, corrective change confined to the `h-mad/` skill dir with the cmux path untouched.

## Overview
The Orca transport verbs in `h-mad/scripts/hmad-dispatch.sh` were authored by guessing the Orca CLI. Reconciled against `orca agent-context --json` (schema v1), `wait` is invalid (`terminal wait --terminal <t> tui-idle` vs real `--for tui-idle [--timeout-ms]`) and `read` pipes through `tail` where a native `--limit` exists. This corrects both, adds the missing native idle-wait semantics, and pins the syntax in the reference doc. Only Orca branches change; every cmux branch is byte-identical.

## Scope
In: the Orca branch of `_cmd_wait` and `_cmd_read` in `hmad-dispatch.sh`; a liveness regression test; `references/agent-substrate.md` open-items. Out: cmux path, verb names / CLI surface, the Tier-2 `orchestration` layer.

## Goals
- G1 — Orca `wait` emits schema-correct native idle-wait (maps FR-1).
- G2 — Orca `read` uses native `--limit` (maps FR-2).
- G3 — Structured `terminal list --json` liveness locked by test (maps FR-3).
- G4 — `agent-substrate.md` states the schema-confirmed Orca forms (maps FR-4).

## Requirements
- FR-1: `wait` → `orca terminal wait --terminal <h> --for tui-idle --timeout-ms <ms>` (default 300000).
- FR-2: `read` → `orca terminal read --terminal <h> --limit <n>` (no `tail`).
- FR-3: `alive`/`_orca_find` structured via `terminal list --json` (regression guard).
- FR-4: `agent-substrate.md` schema-v1-confirmed Orca syntax.

## Implementation Strategy
Three surgical edits + doc + tests:
1. `_cmd_wait` Orca arm: replace `orca terminal wait --terminal "$target" tui-idle` with `orca terminal wait --terminal "$target" --for tui-idle --timeout-ms "$(( timeout * 1000 ))"` (reuse the existing `--timeout <s>` parse; default 300 → 300000ms). Keep the cmux poll-until-stable arm unchanged.
2. `_cmd_read` Orca arm: replace `orca terminal read --terminal "$target" | tail -n "$lines"` with `orca terminal read --terminal "$target" --limit "$lines"`. Keep the cmux arm unchanged.
3. `_cmd_alive` Orca arm + `_orca_find`: correct the guessed JSON path. Both parse `orca terminal list --json` as `.[] | select(.id == …)`, but the real shape is `.result.terminals[]` keyed by `.handle` (no `.id`/`.command`/`.name`). Fix `_cmd_alive` to `.result.terminals[] | select(.handle == $id)`; fix `_orca_find` to iterate `.result.terminals[]`, match the agent token against `.preview`/`.title` (best-effort — no field names the running program), and return `.handle`. Explicit `HMAD_ORCA_<AGENT>_TERMINAL` handle pins bypass `_orca_find` (reliable path).
4. `agent-substrate.md`: rewrite the "Open items" bullets for `terminal wait`/`read`/`list` to state the schema-v1-confirmed forms (incl. the `.result.terminals[].handle` list shape).
5. Tests (`h-mad/tests/test_hmad_dispatch.py`): assert the exact Orca argv for `wait` (incl. `--for tui-idle --timeout-ms`, and `--timeout 30` → `30000`) and `read` (`--limit`); update/add orca `alive` + `_orca_find` tests to the `.result.terminals[]`/`.handle` shape; assert the identity-pin bypass.

Deliberately untouched: detection, `_resolve_target`'s pin path, `send`, `clear`, `notify`, and all cmux arms.

## Architecture Considerations
- The verb/CLI surface is stable — only the Orca-side *emitted command strings* change, so `SKILL.md` and every caller are unaffected (skill-manifest-integrity Axis B satisfied).
- The change is self-contained within `h-mad/` (skill-self-containment Axis B satisfied) — no cross-skill import, no path outside the skill dir.
- Back-compat: cmux users see zero behavioral change (the base-layer backward-compatibility invariant); the Orca `wait`/`read` were non-functional-as-guessed, so correcting them can only improve Orca behavior.

## Deliverables
| Deliverable | Type | Satisfies |
|---|---|---|
| `_cmd_wait` Orca arm correction | shell | FR-1 |
| `_cmd_read` Orca arm correction | shell | FR-2 |
| `_cmd_alive` + `_orca_find` JSON-path correction (`.result.terminals[]`/`.handle`) | shell | FR-3 |
| Orca `wait`/`read`/`alive`/`_orca_find` argv+shape tests (update existing `test_orca_identity_resolves_from_list_json` to real shape) | test | FR-1/2/3 |
| `references/agent-substrate.md` schema-confirmed update | doc | FR-4 |

## Risks and Mitigation
| Risk | Impact | Mitigation |
|---|---|---|
| Orca CLI flag drift | emitted command breaks | schema v1 is versioned + self-describing (`agent-context`); explicit env pins remain the escape hatch |
| No live Orca-agent e2e in CI | untested-against-real-CLI | stub-`orca` argv assertions against the confirmed schema (same harness as existing suite); syntax now schema-confirmed |
| Accidental cmux-arm change | regression for existing users | edits target only the `orca)` case arms; existing cmux tests must stay green |

## Convention Prerequisites
- Feature branch `feature/orca-native-transport` (Phase 5c).
- Full `h-mad/tests/` suite green via `python3 -m pytest` at Phase 5f.

## Success Criteria
- FR-1..4 ACs pass automated tests.
- Existing `test_hmad_dispatch.py` cmux + detection tests remain green (no regression).
- `agent-substrate.md` no longer carries the Orca-syntax "confirm against live CLI" open-items.

## Out-of-Scope (confirmed from spec)
- Tier-2 native `orchestration` layer (separate `orca-native-orchestration` spec).
- `terminal read --cursor` incremental reads.
- Any cmux-path or CLI-surface change.

## Next Steps
Agy plan audit → Phase 4 design.

## Version History
- v1.0: Initial plan draft.
- v1.1: Back-propagation from design-time schema probe — FR-3 expanded from a "lock/regression-guard" to a real fix: `_cmd_alive` and `_orca_find` parse a guessed `.[] | select(.id …)` shape, but real `orca terminal list --json` is `.result.terminals[]` keyed by `.handle` (no `.id`/`.command`). Both corrected; the existing `test_orca_identity_resolves_from_list_json` must be updated to the real shape. Identity-pin (handle) remains the reliable path.
