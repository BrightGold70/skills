# Plan: orca-file-diff-review-gates

## Executive Summary
Add `_cmd_file_diff` and `_cmd_file_open_changed` to `hmad-dispatch.sh` (Orca-only, reusing `_require_orca` + the shipped `_json_extract` helper) with two `main()` cases, plus a best-effort SKILL.md review-gate section; additive, cmux/off-Orca behavior unchanged.

## Overview
This is a small ergonomic sibling to Tier-3: two more thin Orca-guarded verbs following the exact established pattern, and documentation that the orchestrator may surface a diff in Orca's editor at human review gates. The value is human-review quality (native editor vs scrollback), including HemaSuite manuscript DOCX diffs as a documented consumer.

## Scope
- In: `file-diff` + `file-open-changed` verbs (argv construction, `_require_orca` guard, `_json_extract` passthrough), two `main()` cases, a SKILL.md best-effort review-gate section, stub tests.
- Out: live-Orca e2e; HemaSuite code changes; blocking/auto editor opens; making a gate depend on surfacing.

## Goals
- G1: `file-diff` + `file-open-changed` verbs surface diffs via the Orca editor (FR-1, FR-2).
- G2: Review-gate surfacing is best-effort, non-blocking, and off-Orca-safe (FR-3, FR-4).
- G3: Reuse the shipped `_json_extract` (no new extractor); reuse `_require_orca` (single-source, no forked guard).
- G4: Every `orca file …` argv reconciled **manually at authoring time** against `agent-context --json` schema v1 (policy, per the Tier-1 lesson — no automated build-check deliverable; tests pin the argv via stub capture). See Implementation Strategy.

## Requirements
- FR-1 `file-diff`; FR-2 `file-open-changed`; FR-3 best-effort gate docs; FR-4 additive / no non-Orca change.

## Implementation Strategy
- **Layer 1 — verbs** (`h-mad/scripts/hmad-dispatch.sh`): add `_cmd_file_diff` and `_cmd_file_open_changed` following the Tier-3 shape — `_require_orca <verb>` guard, `_need` for the required `<path>` (file-diff only), a `while [ $# -gt 0 ]` flag loop building an `args=(file diff …)` / `args=(file open-changed …)` array, always append `--json`, pipe through the shared `_json_extract '.result | tojson'` for passthrough. Add two `main()` cases. **Reuse `_json_extract` and `_require_orca` verbatim — no new helpers** (single-source).
- **Layer 2 — SKILL.md** best-effort review-gate section: document that at Phase 3/4 approval + Phase 6a the orchestrator MAY call `file-open-changed --mode diff`; the call is best-effort/non-blocking; a non-zero (off-Orca/no-editor) is logged (`[H-MAD] … diff_surface_skipped`) and the gate proceeds unchanged. Note HemaSuite consumes `file-diff <manuscript.docx>` as a documented usage.
- **Schema reconciliation (G4)**: manual at authoring time — the `orca file diff` / `file open-changed` usage strings were verified against live `orca agent-context --json` (schema v1) when writing the verbs; there is NO automated schema-validation deliverable (consistent with the Tier-3 design decision). The stub tests pin the exact argv, so a future schema drift surfaces as a test diff. A live-schema-drift check is a deferred carry alongside the live-Orca e2e gap.
- **Deliberately untouched**: existing verbs, cmux path, gate logic (surfacing is additive and optional), Tier-2/3 verbs.

## Architecture Considerations
- **Single-source**: reuse the shipped `_json_extract` (Tier-3) and `_require_orca` (Tier-1) — introducing a second extractor or guard would breach the Axis-B single-source contract (the exact finding back-propagated in Tier-3).
- **Best-effort boundary**: the gate must never depend on the verb succeeding — off-Orca the verb returns non-zero and the orchestrator logs+continues. This keeps the cmux path byte-identical.
- **File-indirection**: paths are passed as array elements (no shell interpolation), consistent with Tier-3.

## Deliverables
| Deliverable | Type | Satisfies |
|---|---|---|
| `_cmd_file_diff` verb | CLI subcommand | FR-1 |
| `_cmd_file_open_changed` verb | CLI subcommand | FR-2 |
| 2 `main()` cases | CLI routing | FR-1, FR-2 |
| SKILL.md best-effort review-gate section | doc | FR-3, FR-4 |
| Stub tests | pytest (`test_hmad_dispatch.py`) | FR-1, FR-2, FR-3 (doc), FR-4 |

## Risks and Mitigation
| Risk | Impact | Mitigation |
|---|---|---|
| Live-Orca e2e gap | Verbs unvalidated against real editor | Stub-test argv/JSON; deferred carry |
| Gate accidentally made dependent on surfacing | cmux path regresses | Doc + design state surfacing is best-effort; a failed verb logs + gate proceeds; test asserts cmux path unchanged |
| `file diff --json` payload shape unknown | Passthrough wrong | Reuse `_json_extract '.result | tojson'` defensive passthrough; test pins the canned-stub shape |

## Convention Prerequisites
- Feature branch `feature/181-orca-file-diff-review-gates` (Phase 5c).
- Tier-1 + Tier-3 shipped (`_require_orca`, `_json_extract` present on main).

## Success Criteria
- All spec ACs pass (stub argv + passthrough + guard + doc-presence).
- `test_hmad_dispatch.py` full file green (existing verbs untouched).
- SKILL.md documents best-effort/non-blocking surfacing at the named gates.
- Every `orca file …` argv matches schema v1.

## Out-of-Scope (confirmed from spec)
- Live-Orca e2e; HemaSuite code changes; blocking editor opens; gate-depends-on-surfacing.

## Next Steps
Approve plan v1.0 → agy audit → Phase 4 design.

## Version History
- v1.0: Initial plan draft.
- v2.0: Plan-audit-v1 fix — clarified G4 schema reconciliation is a MANUAL authoring-time policy (no automated build-check deliverable; argv pinned via stub tests), with a matching Implementation Strategy bullet (must-fix).
