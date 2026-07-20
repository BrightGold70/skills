# Report: orca-file-diff-review-gates

## Executive Summary
Shipped Medium M1 of the Orca adaptation arc: two Orca-only `hmad-dispatch` verbs (`file-diff`, `file-open-changed`) plus best-effort SKILL.md documentation that the orchestrator may surface diffs in Orca's editor at human review gates. Full suite 100/0, agy 6a-prime READY_TO_MERGE.

## Summary
Added `_cmd_file_diff` and `_cmd_file_open_changed` reusing the shipped `_require_orca` guard and `_json_extract` helper (single-source — no new helpers), with two `main()` cases and a best-effort/non-blocking review-gate section in SKILL.md. Off-Orca the verbs refuse (non-zero) and the orchestrator logs `diff_surface_skipped`; the gate proceeds unchanged, keeping the cmux path byte-identical. HemaSuite consumes `file-diff <manuscript.docx>` as documented usage (no HemaSuite code in this feature).

## Metrics

| Metric | Value |
|---|---|
| Plan audit cycles | 2 |
| Design audit cycles | 2 |
| Impl-plan audit cycles | 1 (clean first pass) |
| Iterate cycles (Phase 6b) | 0 (100% first pass) |
| Final match rate | 100% |
| Tests | 100 passing / 0 failing |
| Phases with back-propagation | None |

## What Went Well
- Reusing the shipped Tier-3 `_json_extract` + Tier-1 `_require_orca` kept the single-source contract trivially satisfied — no back-propagation this feature.
- Design audit caught a real short-circuit bug pre-code: `_cmd_file_open_changed` guard was missing `|| return $?` (would have called `orca` off-Orca, breaking FR-4).
- Plan audit caught the unaddressed G4 schema-reconciliation goal early — resolved as an explicit manual-authoring-time policy (consistent with Tier-3).

## What To Improve Next Time
- Copy the guard `|| return $?` idiom consistently across sibling verbs in the design's first draft (the file-diff guard had it; file-open-changed didn't — an easy symmetry check pre-audit).

## Carry Items
- **Live-Orca e2e** — the two verbs + the best-effort gate integration are stub-tested only; no real Orca editor runtime has surfaced a diff. Standing gap shared with Tier 1/2/3/launch-profile. Deferred (non-blocking).
- **HemaSuite `file-diff` usage** — documented but not wired into a HemaSuite review command; a follow-on could call `hmad-dispatch file-diff <manuscript.docx>` from HemaSuite's desk-check gate.

## Version History
- v1.0: Initial report draft.
