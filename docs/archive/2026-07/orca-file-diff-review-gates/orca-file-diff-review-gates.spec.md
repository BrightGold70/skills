# Spec: orca-file-diff-review-gates

## Executive Summary
Add two Orca-only `hmad-dispatch` verbs (`file-diff`, `file-open-changed`) plus SKILL.md documentation that the orchestrator MAY surface diffs in the Orca editor at human review gates, best-effort and non-blocking, with cmux and off-Orca paths unchanged.

## Goal
Give the operator a native-editor review surface for Phase-5 diffs (and HemaSuite manuscript DOCX diffs) at H-MAD review gates, without making diff-surfacing a gate dependency or altering any non-Orca behavior.

## Functional Requirements

### FR-1: `file-diff` verb
- **Description**: `hmad-dispatch file-diff <path> [--staged] [--worktree <sel>]` wrapping `orca file diff <path> [--staged] [--worktree <sel>] --json`. Orca-only (`_require_orca` guard). Passes through the `--json` payload to stdout.
- **Acceptance Criteria**:
  - AC-1.1: `file-diff foo.py` (substrate=orca) → argv `orca file diff foo.py --json`.
  - AC-1.2: `file-diff foo.py --staged --worktree wt-3` → argv `orca file diff foo.py --staged --worktree wt-3 --json`.
  - AC-1.3: canned `--json` stdout is passed through to the verb's stdout (via the shared `_json_extract`).
  - AC-1.4: substrate=cmux (or no orca) → non-zero exit, no `orca` call captured.
  - AC-1.5: missing `<path>` arg → non-zero exit (via `_need`), no `orca` call.

### FR-2: `file-open-changed` verb
- **Description**: `hmad-dispatch file-open-changed [--mode edit|diff|both] [--worktree <sel>]` wrapping `orca file open-changed [--mode …] [--worktree …] --json`. Orca-only.
- **Acceptance Criteria**:
  - AC-2.1: `file-open-changed` → argv `orca file open-changed --json`.
  - AC-2.2: `file-open-changed --mode diff --worktree wt-3` → argv `orca file open-changed --mode diff --worktree wt-3 --json`.
  - AC-2.3: substrate=cmux → non-zero exit, no `orca` call.

### FR-3: Best-effort review-gate documentation (SKILL.md)
- **Description**: SKILL.md documents that at human review gates (Phase 3 plan approval, Phase 4 design approval, Phase 6a verification) the orchestrator MAY call `file-open-changed --mode diff` (or `file-diff <path>`) to surface the diff in Orca's editor. The call is **best-effort and non-blocking**: a non-zero result (off-Orca, no editor) is logged and the gate proceeds unchanged. It is never a gate precondition.
- **Acceptance Criteria**:
  - AC-3.1: SKILL.md contains a section naming both verbs and the gates at which surfacing is offered.
  - AC-3.2: The text states explicitly that surfacing is best-effort / non-blocking and that a failure never blocks the gate or alters the cmux path.
  - AC-3.3: A doc-presence test asserts the verbs and the "best-effort"/"non-blocking" wording are present.

### FR-4: Additive / no non-Orca behavior change
- **Description**: Feature is purely additive — no existing verb, the cmux path, or gate logic changes behavior when the new verbs are not invoked.
- **Acceptance Criteria**:
  - AC-4.1: Existing `test_hmad_dispatch.py` tests stay green (no existing verb touched).
  - AC-4.2: With substrate=cmux, no new verb invokes `orca`; the documented gate flow is unchanged from today.

## Non-Functional Requirements
- Performance: N/A (single Orca call per invocation; only at operator gates).
- Security: path arg passed through the args array (no shell interpolation), consistent with Tier-3 verbs.
- Compatibility: additive; reuses the shipped `_json_extract` helper; no new dependency (`orca` + `jq` only).

## Out-of-Scope
- Live-Orca e2e (deferred carry, shared gap).
- Any HemaSuite code change — HemaSuite consuming the verb to surface a manuscript DOCX is documented usage only.
- Auto-blocking editor opens or making a gate depend on the diff being surfaced.

## Assumptions
- `orca file diff --json` returns a payload safe to pass through (diff text or an editor-open ack); reconciled at design.
- The shipped `_json_extract` helper is the single extraction surface for any JSON passthrough.

## Version History
- v1.0: Initial specification draft.
