# Implementation Plan: orca-file-diff-review-gates

> Source: docs/02-design/features/orca-file-diff-review-gates.design.md (post-audit v2)
> Branch target: feature/181-orca-file-diff-review-gates

## Executive Summary
One task: add `_cmd_file_diff` + `_cmd_file_open_changed` (+ 2 `main()` cases) to `hmad-dispatch.sh` reusing the shipped `_require_orca`/`_json_extract`, plus a best-effort SKILL.md review-gate section, with stub tests and a doc-presence test — all additive.

## Task 1: file-verbs-and-gate-docs

**Production file**: `h-mad/scripts/hmad-dispatch.sh` (+ `h-mad/SKILL.md`)
**Test file**: `h-mad/tests/test_hmad_dispatch.py` (additions)

**Description**: Add two Orca-only file verbs following the Tier-3 shape (each `_require_orca <verb> || return $?` then argv array then `_json_extract '.result | tojson'`), wire two `main()` cases, and add a best-effort review-gate section to SKILL.md. Reuse the shipped `_require_orca` and `_json_extract` — no new helpers.

**Code structure**:
```bash
_cmd_file_diff() {   # <path> [--staged] [--worktree <sel>]
  _require_orca file-diff || return $?
  _need "${1:-}" path || return $?
  local path="$1"; shift
  local args=(file diff "$path")
  while [ $# -gt 0 ]; do case "$1" in
    --staged) args+=(--staged); shift ;;
    --worktree) args+=(--worktree "$2"); shift 2 ;;
    *) shift ;; esac; done
  args+=(--json)
  orca "${args[@]}" | _json_extract '.result | tojson'
}

_cmd_file_open_changed() {   # [--mode edit|diff|both] [--worktree <sel>]
  _require_orca file-open-changed || return $?
  local args=(file open-changed)
  while [ $# -gt 0 ]; do case "$1" in
    --mode) args+=(--mode "$2"); shift 2 ;;
    --worktree) args+=(--worktree "$2"); shift 2 ;;
    *) shift ;; esac; done
  args+=(--json)
  orca "${args[@]}" | _json_extract '.result | tojson'
}

# main() case additions:
#   file-diff) _cmd_file_diff "$@" ;;
#   file-open-changed) _cmd_file_open_changed "$@" ;;
```
```markdown
# SKILL.md — new "Surfacing diffs at review gates (Orca only)" subsection:
# At Phase 3/4 approval + Phase 6a, orchestrator MAY call:
#   hmad-dispatch file-open-changed --mode diff    (or file-diff <path>)
# Best-effort, NON-BLOCKING: non-zero (substrate!=orca / no editor) is logged
#   [H-MAD] <feature> diff_surface_skipped  and the gate PROCEEDS unchanged.
# Never a gate precondition; cmux review flow unchanged.
# HemaSuite usage: file-diff <manuscript.docx> to surface a generated DOCX (documented, no HemaSuite code here).
```

**Acceptance Criteria**:
- [ ] AC-1.1: `file-diff foo.py` (orca) → captured argv `orca file diff foo.py --json`.
- [ ] AC-1.2: `file-diff foo.py --staged --worktree wt-3` → `orca file diff foo.py --staged --worktree wt-3 --json`.
- [ ] AC-1.3: canned `{"result":{"d":1}}` → verb stdout `{"d":1}`.
- [ ] AC-1.4: substrate=cmux → returncode ≠ 0, no `orca` line captured.
- [ ] AC-1.5: `file-diff` with no path → returncode 2, no `orca` call.
- [ ] AC-2.1: `file-open-changed` → `orca file open-changed --json`; `--mode diff --worktree wt-3` → appends `--mode diff --worktree wt-3`.
- [ ] AC-2.2: canned `{"result":{"opened":2}}` → stdout `{"opened":2}` (passthrough, both verbs).
- [ ] AC-2.3: substrate=cmux → returncode ≠ 0, no `orca` call.
- [ ] AC-3.1: doc-presence test `test_skill_documents_diff_surface_gate` asserts `SKILL.md` contains `file-open-changed`, `file-diff`, and the wording `best-effort` and `non-blocking`.
- [ ] AC-4.1: existing `test_hmad_dispatch.py` tests stay green (no existing verb changed).

**Dependencies on other tasks**: None

## Version History
- v1.0: Initial implementation plan draft.
