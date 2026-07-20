# Brainstorm: orca-automations-scheduled-e2e

## Executive Summary
Add Orca-only `hmad-dispatch` automation verbs (`automation-create`, `automation-run`, `automation-list`, `automation-remove`) wrapping `orca automations *`, so HemaSuite's long operator-triggered live-e2e / regression runs can be scheduled as cron/preset Orca automations (with a `--precheck` like `hpw doctor`, `--provider agent`) instead of run by hand.

## Problem Statement
HemaSuite has several long, operator-triggered validation runs — anemia-jmj narrative e2e (~76 min), review-pipeline-correctness, full regression suites — that today are launched manually on a cmux surface. There is no way to schedule them (nightly / cron) or trigger them structurally. Orca has an `automations` command family (create/run/list/remove with cron/rrule/preset triggers + `--precheck` + `--provider agent`), but h-mad has no verb to drive it.

## Proposed Approach
Four Orca-only `hmad-dispatch` lifecycle verbs mirroring the Tier-2/3/M1 guard+argv pattern, reusing the shipped `_require_orca` guard and `_json_extract` helper:
- `automation-create --name <n> --trigger <preset|cron|rrule> --prompt-file <path> [--provider <agent>] [--precheck <cmd>] [--repo <sel>|--workspace <sel>|--project <id>]` → wraps `orca automations create …`; returns the automation id.
- `automation-run <id>` → wraps `orca automations run <id> --json`.
- `automation-list` → wraps `orca automations list --json`.
- `automation-remove <id>` → wraps `orca automations remove <id> --json`.

The long automation prompt is passed via **file-indirection** (`--prompt-file`, per CLAUDE.md §F-12), never a bare argv blob. Then document, in SKILL.md, the HemaSuite scheduling usage: create a nightly automation for a live-e2e with `--precheck "hpw doctor"` and `--provider agent`. HemaSuite consuming these verbs is **documented usage**, not HemaSuite code in this feature (same scoping as M1's manuscript-diff usage) — wiring into a HemaSuite command is gated on HemaSuite executing in an Orca workspace.

## Alternatives Considered
- **A HemaSuite-side cron/launchd scheduler** (no Orca): rejected — reinvents scheduling; loses Orca's `--provider agent` + `--precheck` + managed run history; not the Orca-adaptation goal.
- **Code the HemaSuite wiring now**: rejected — HemaSuite running under an Orca workspace is a blocked prerequisite (`--repo`/`--workspace`/`--project` targeting needs it); coding it would be unvalidatable. Keep it documented usage; ship the reusable verb primitive.
- **All 7 automations subcommands** (add show/runs/edit): deferred — create/run/list/remove are the lifecycle MVP; show/runs/edit are additive follow-ons, out of scope to keep this bounded.

## Risks & Mitigations
| Risk | Likelihood | Mitigation |
|---|---|---|
| Live-Orca e2e gap — no Orca-hosted-HemaSuite runtime to validate scheduling end-to-end | H | Stub-test argv/JSON; deferred live-Orca carry (shared gap) |
| Scope creep into HemaSuite code | M | HemaSuite scheduling = documented usage only; no HemaSuite change in this feature |
| Long `--prompt` fragments/leaks on argv | M | `--prompt-file` indirection (F-12); never a bare argv blob |
| `automations create` targeting flags mis-modeled (--repo vs --workspace vs --project) | M | Reconcile against `agent-context --json` at design; pass targeting through opaquely as provided |

## Dependencies
- Tier-1 `_require_orca` (substrate guard); Tier-3 `_json_extract` (shipped `bba5123`) — reused.
- Orca `automations` command family — verified in `agent-context --json` schema v1.

## Open Questions
- Does `automations create --json` return the automation id under `.result.id` / `.result.automationId`? Reconcile at design; use a defensive `_json_extract` alternation (as Tier-3 worktree-create did).
- Which targeting flag is canonical for HemaSuite (`--repo` vs `--workspace` vs `--project`)? Pass through opaquely; document the HemaSuite-recommended form in SKILL.md.

## Version History
- v1.0: Initial brainstorm draft.
