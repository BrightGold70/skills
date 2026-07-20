# Design: orca-file-diff-review-gates

## Executive Summary
Add `_cmd_file_diff` and `_cmd_file_open_changed` to `hmad-dispatch.sh` (Orca-only, reusing the shipped `_require_orca` guard and `_json_extract` helper) with two `main()` cases, plus a best-effort SKILL.md review-gate section; additive, cmux/off-Orca behavior byte-unchanged.

## Overview
Two thin Orca-guarded verbs following the exact Tier-3 shape, and documentation that the orchestrator may surface a diff in Orca's editor at human review gates. No new helpers — `_require_orca` (Tier-1) and `_json_extract` (Tier-3, shipped `bba5123`) are reused verbatim.

## Architecture Overview
```
Human review gate (Phase 3/4 approval, Phase 6a) — SKILL.md, best-effort
  orchestrator MAY: hmad-dispatch file-open-changed --mode diff   (or file-diff <path>)
    substrate=orca  → orca opens editor; verb returns 0
    substrate≠orca  → _require_orca returns non-zero → orchestrator logs
                      [H-MAD] diff_surface_skipped, gate PROCEEDS unchanged
  (surfacing is NEVER a gate precondition)

hmad-dispatch.sh
  _cmd_file_diff         ─ _require_orca ─ orca file diff <path> [--staged] [--worktree] --json ─ _json_extract
  _cmd_file_open_changed ─ _require_orca ─ orca file open-changed [--mode] [--worktree] --json ─ _json_extract
```

## Detailed Design

### `_cmd_file_diff` (FR-1)
- Signature: `file-diff <path> [--staged] [--worktree <sel>]`.
- Guard: `_require_orca file-diff || return $?`.
- Arg: `_need "${1:-}" path || return $?`; `local path="$1"; shift`.
- Flags: `while [ $# -gt 0 ]` loop → `--staged` (append `--staged`), `--worktree <sel>` (append `--worktree "$sel"`).
- Build `args=(file diff "$path")`, append flags, append `--json`.
- `orca "${args[@]}" | _json_extract '.result | tojson'` — passthrough via the shared helper (single-source).

### `_cmd_file_open_changed` (FR-2)
- Signature: `file-open-changed [--mode edit|diff|both] [--worktree <sel>]`.
- Guard: `_require_orca file-open-changed || return $?` (early-return short-circuits off-Orca — same as `_cmd_file_diff`; without `|| return $?` the function would fall through and call `orca`, breaking FR-4).
- Flags: `while` loop → `--mode <m>`, `--worktree <sel>`.
- Build `args=(file open-changed)`, append flags, append `--json`.
- `orca "${args[@]}" | _json_extract '.result | tojson'`.

### `main()` verb cases
Two new lines: `file-diff) _cmd_file_diff "$@" ;;` and `file-open-changed) _cmd_file_open_changed "$@" ;;`. Additive.

### SKILL.md best-effort review-gate section (FR-3/4)
Document: at Phase 3 plan approval, Phase 4 design approval, and Phase 6a verification, the orchestrator MAY call `hmad-dispatch file-open-changed --mode diff` (or `file-diff <path>`) to surface the diff in Orca's editor. The call is **best-effort and non-blocking**: a non-zero result (substrate≠orca, no editor) is logged as `[H-MAD] <feature> diff_surface_skipped` and the gate proceeds exactly as today. Surfacing is NEVER a gate precondition; the cmux review flow is unchanged. Note: HemaSuite consumes `file-diff <manuscript.docx>` to surface a generated manuscript DOCX — documented usage, no HemaSuite code in this feature.

## Components Changed / Added
| Component | File path | Change type | Purpose |
|---|---|---|---|
| `_cmd_file_diff` | `h-mad/scripts/hmad-dispatch.sh` | new | FR-1 |
| `_cmd_file_open_changed` | `h-mad/scripts/hmad-dispatch.sh` | new | FR-2 |
| 2 `main()` cases | `h-mad/scripts/hmad-dispatch.sh` | modify | route verbs |
| SKILL.md review-gate section | `h-mad/SKILL.md` | modify | FR-3, FR-4 |
| Verb + doc tests | `h-mad/tests/test_hmad_dispatch.py` | modify | FR-1/2/3/4 |

## Implementation Order
1. `_cmd_file_diff` + case + tests (RED→GREEN).
2. `_cmd_file_open_changed` + case + tests.
3. SKILL.md best-effort review-gate section + doc-presence test.

## Data Model / Schema Changes
None. No state-schema change; surfacing emits only `[H-MAD]` markers.

## API / Interface Changes
Two new `hmad-dispatch` verbs (above). No new env knob. No change to existing verbs or the cmux path.

## Error Handling Strategy
- Substrate guard: `_require_orca` non-zero + stderr on substrate≠orca (no `orca` call) — AC-1.4/2.3.
- Missing `<path>` (file-diff): `_need` returns 2, no `orca` call — AC-1.5.
- A non-zero from the verb at a review gate is caught by the orchestrator, logged `diff_surface_skipped`, and the gate proceeds — surfacing is never fatal (FR-3/4).
- Empty `_json_extract` output → empty stdout; harmless (the editor-open is the side effect, not the stdout).

## Test Strategy
Unit tests only (live-Orca e2e deferred). Reuse the `test_hmad_dispatch.py` stub-on-PATH harness. Per verb: argv assertion (stub captures exact `orca file …` argv) + passthrough (canned `.result` → stdout) + substrate guard (cmux → non-zero, empty capture). Doc test asserts SKILL.md contains both verb names + the "best-effort"/"non-blocking" wording.

## Test Plan
- `test_file_diff_argv` — `file-diff foo.py` → `orca file diff foo.py --json`.
- `test_file_diff_flags` — `file-diff foo.py --staged --worktree wt-3` → `orca file diff foo.py --staged --worktree wt-3 --json`.
- `test_file_diff_passthrough` — canned `{"result":{"d":1}}` → stdout `{"d":1}`.
- `test_file_diff_refuses_cmux` — cmux → non-zero, empty capture.
- `test_file_diff_requires_path` — no path → returncode 2, no orca call.
- `test_file_open_changed_argv` — `file-open-changed` → `orca file open-changed --json`; `--mode diff --worktree wt-3` → appends those.
- `test_file_open_changed_passthrough` — canned `{"result":{"opened":2}}` → stdout `{"opened":2}` (via `_json_extract`; passthrough validated for both verbs).
- `test_file_open_changed_refuses_cmux` — cmux → non-zero, no orca call.
- `test_skill_documents_diff_surface_gate` — SKILL.md contains `file-open-changed`, `file-diff`, and `best-effort`/`non-blocking`.
- Verification: `python3.11 -m pytest h-mad/tests/test_hmad_dispatch.py -v`.

## Invariant Compliance
- **Audit-gate signal discipline**: N/A — no new gate; verbs signal via exit code (operational), correct for a dispatch wrapper.
- **Single-source contract**: reuses the shipped `_json_extract` (one extractor) + `_require_orca` (one guard) — no forked helper. Complies.
- **Standalone / no plugin dependency**: only `orca` + `jq`. Complies.
- **No new external dependency**: `orca` + `jq` already depended on. Complies.
- **Doc-template superset compliance**: plan/design/report under the standard dirs, h-mad sections retained. Complies.
- **Operator-override preservation**: no gate change. Complies.
- **Backward compatibility**: no gate change; existing verbs/tests untouched. Complies.
- **Marker discipline**: surfacing emits `[H-MAD] diff_surface_skipped` on the off-Orca path. Complies.
- **Skill self-containment** (project): all logic inside `h-mad/`. Complies.
- **Skill manifest integrity** (project): SKILL.md gains a review-gate section; frontmatter unchanged. Complies.

## Version History
- v1.0: Initial design draft.
- v2.0: Design-audit-v1 fixes — added `|| return $?` to the `_cmd_file_open_changed` guard (early-return off-Orca, must-fix 1); added `test_file_open_changed_passthrough` so both verbs validate passthrough (must-fix 2).
