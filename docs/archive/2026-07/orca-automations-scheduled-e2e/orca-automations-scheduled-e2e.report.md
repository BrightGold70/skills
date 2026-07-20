# Report: orca-automations-scheduled-e2e

## Executive Summary
Shipped Medium M2 — the final Orca-adaptation candidate: four Orca-only `hmad-dispatch` automation lifecycle verbs (`automation-create/run/list/remove`) letting HemaSuite's long operator-triggered live-e2e / regression runs be scheduled as Orca automations. Full suite 111/0, agy 6a-prime READY_TO_MERGE.

## Summary
Added `_cmd_automation_create/run/list/remove` reusing the shipped `_require_orca` guard and `_json_extract` helper (single-source — no new helpers), with four `main()` cases and a HemaSuite scheduled-e2e usage section in SKILL.md. `create` extracts the automation id and passes its long prompt via `--prompt-file` file-indirection (F-12); `list` extracts `.result`; `run`/`remove` emit orca's raw `--json` ack (matching the plan's pass-through). HemaSuite consumption (`--precheck "hpw doctor" --provider agent --workspace <ws>`) is documented usage — no HemaSuite code, gated on HemaSuite executing in an Orca workspace.

## Metrics

| Metric | Value |
|---|---|
| Plan audit cycles | 2 |
| Design audit cycles | 2 |
| Impl-plan audit cycles | 1 (clean first pass) |
| Iterate cycles (Phase 6b) | 0 (100% first pass) |
| Final match rate | 100% |
| Tests | 111 passing / 0 failing |
| Phases with back-propagation | None |

## What Went Well
- Design audit caught three real internal contradictions pre-code: run/remove prose drifting to `_json_extract` while the plan/diagram said raw pass-through, and a false "verbs emit `[H-MAD]` markers" claim — all resolved by aligning the design to the plan (no back-propagation needed).
- Reusing the shipped `_require_orca` + `_json_extract` kept single-source trivially satisfied.
- Proactively pre-empting M1's G4/G5 findings (F-12 prompt-file + manual-schema-reconciliation policy) in the plan meant the plan audit only surfaced a wording nuance, not a structural gap.
- agy 6a-prime explicitly verified the `--prompt "$(cat "$pf")"` passthrough is injection-safe (double-quoted subshell into an array element).

## What To Improve Next Time
- Keep verb-body prose, the architecture diagram, and code snippets in lockstep in the design's first draft — the run/remove `_json_extract` contradiction was a prose/snippet mismatch the audit had to catch.

## Carry Items
- **Live-Orca e2e** — the four verbs + HemaSuite scheduling usage are stub-tested only; no real Orca automations runtime has scheduled/triggered a HemaSuite e2e. Standing gap shared across the whole arc. Deferred (non-blocking).
- **HemaSuite wiring** — documented usage only; a follow-on (blocked on Orca-hosted HemaSuite) would wire `automation-create` into a HemaSuite command to schedule the anemia-jmj / review-pipeline / regression runs nightly.
- **`automations show/runs/edit`** — deferred additive follow-on verbs (not in the create/run/list/remove MVP).

## Version History
- v1.0: Initial report draft.
