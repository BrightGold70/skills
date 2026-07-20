# Implementation Plan: worktree-parallel-multi-module-tdd

> Source: docs/02-design/features/worktree-parallel-multi-module-tdd.design.md (post-audit v2)
> Branch target: feature/180-worktree-parallel-multi-module-tdd

## Executive Summary
Two tasks: Task 1 adds the shared `_json_extract` helper + three `_cmd_worktree_*` verbs (+ verb cases) to `hmad-dispatch.sh` with stub-based tests (extending the orca stub for exit-code control); Task 2 documents the Phase-5 fanout protocol in `SKILL.md` + `references/orchestration-mode.md` with a doc-presence test. Task 2 depends on Task 1 (verb names).

## Task 1: worktree-verbs

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch.py` (additions) + `h-mad/tests/stubs/orca` (exit-code extension)

**Description**: Add one shared JSON-extraction helper and three Orca-only worktree verbs, each guarded by the existing `_require_orca`, routing all extraction through the single helper. Wire three new cases into `main()`. Extend the orca test-stub to honor an optional exit-code env so the rm-failure path is testable.

**Code structure**:
```bash
# hmad-dispatch.sh — new shared helper (single-source extraction)
_json_extract() {   # $1 = jq alternation expr; stdin JSON -> first non-empty match
  jq -r "${1} // empty"
}

_cmd_worktree_create() {   # <name> [--agent <id>] [--base <ref>] [--prompt-file <path>]
  _require_orca worktree-create || return $?
  _need "${1:-}" name || return $?
  local name="$1"; shift
  local agent="" base="" pf=""
  while [ $# -gt 0 ]; do case "$1" in
    --agent) agent="$2"; shift 2 ;; --base) base="$2"; shift 2 ;;
    --prompt-file) pf="$2"; shift 2 ;; *) shift ;; esac; done
  local args=(worktree create --name "$name")
  [ -n "$agent" ] && args+=(--agent "$agent")
  [ -n "$base" ]  && args+=(--base-branch "$base")
  if [ -n "$pf" ]; then [ -f "$pf" ] || { echo "hmad-dispatch: prompt file not found: $pf" >&2; return 2; }
    args+=(--prompt "$(cat "$pf")"); fi
  args+=(--json)
  orca "${args[@]}" | _json_extract '.result.worktree.selector // .result.worktree.handle // .result.selector // .result.handle // .result.id // .id'
}

_cmd_worktree_ps() {   # [--limit <n>]
  _require_orca worktree-ps || return $?
  local args=(worktree ps)
  while [ $# -gt 0 ]; do case "$1" in --limit) args+=(--limit "$2"); shift 2 ;; *) shift ;; esac; done
  args+=(--json)
  orca "${args[@]}" | _json_extract '.result | tojson'
}

_cmd_worktree_rm() {   # <selector> [--force]
  _require_orca worktree-rm || return $?
  _need "${1:-}" selector || return $?
  local sel="$1"; shift
  local args=(worktree rm --worktree "$sel")
  while [ $# -gt 0 ]; do case "$1" in --force) args+=(--force); shift ;; *) shift ;; esac; done
  args+=(--json)
  orca "${args[@]}" >/dev/null
  local rc=$?
  [ $rc -eq 0 ] || { echo "[H-MAD] worktree-rm failed selector=$sel rc=$rc" >&2; return $rc; }
}

# main() case additions:
#   worktree-create) _cmd_worktree_create "$@" ;;
#   worktree-ps)     _cmd_worktree_ps "$@" ;;
#   worktree-rm)     _cmd_worktree_rm "$@" ;;
```
```bash
# tests/stubs/orca — exit-code extension (additive, default 0 preserves all existing tests):
#   exit "${HMAD_STUB_ORCA_EXIT:-0}"   (replaces the hardcoded `exit 0`)
```

**Acceptance Criteria**:
- [ ] AC-1.1: `worktree-create m --agent a1 --base main` (substrate=orca) captures argv `orca worktree create --name m --agent a1 --base-branch main --json`.
- [ ] AC-1.2: canned stdout `{"result":{"worktree":{"selector":"wt-7"}}}` → verb stdout `wt-7\n`.
- [ ] AC-1.3: `--prompt-file <f>` (contents `X`) → argv contains `--prompt X`; missing file → returncode 2, no `orca` call captured.
- [ ] AC-1.4: substrate=cmux → returncode ≠ 0, capture file has no `orca worktree` line.
- [ ] AC-2.1: `worktree-ps --limit 3` → argv `orca worktree ps --limit 3 --json`; `worktree-ps` → `orca worktree ps --json`.
- [ ] AC-2.2: canned `{"result":{"a":1}}` → stdout is compact JSON `{"a":1}` (parseable).
- [ ] AC-2.3: substrate=cmux → returncode ≠ 0, no orca call.
- [ ] AC-3.1: `worktree-rm wt-7 --force` → argv `orca worktree rm --worktree wt-7 --force --json`.
- [ ] AC-3.2: `HMAD_STUB_ORCA_EXIT=1` → verb returncode 1, stderr contains `[H-MAD] worktree-rm failed`.
- [ ] AC-3.3: substrate=cmux → returncode ≠ 0, no orca call.
- [ ] AC-helper: `_json_extract` unit — via `worktree-create` selector parse (AC-1.2) exercises the one helper; empty match → empty stdout (create with `{"result":{}}` → empty stdout).

**Dependencies on other tasks**: None

---

## Task 2: fanout-protocol-docs

**Production file**: `h-mad/SKILL.md` (+ `h-mad/references/orchestration-mode.md`)
**Test file**: `h-mad/tests/test_hmad_dispatch.py` (doc-presence test appended)

**Description**: Document the Phase-5 parallel-fanout protocol: the partition rule (independent = `Dependencies on other tasks: None`), the engage-conjunction (orca ∧ orchestration-on ∧ ≥2 independent), the fanout loop (worktree-create → Tier-2 dispatch/await → per-module `git merge --no-ff` with conflict detection → worktree-rm), the `HMAD_ORCA_MAX_WORKTREES` cap (default 4), and the halt-path teardown of ALL fanout-group worktrees. Serial path remains the documented default/fallback. Add the three worktree verbs to any verb reference list in the docs.

**Code structure**:
```markdown
## Phase 5 parallel fanout (Orca only) — SKILL.md new subsection
- Engage IFF: `hmad-dispatch env` shows substrate=orca AND orchestration:on AND ≥2 impl-plan tasks with `Dependencies: None`.
- Loop (≤ HMAD_ORCA_MAX_WORKTREES, default 4): worktree-create → task-create+dispatch --to <sel> → await → git merge --no-ff → worktree-rm.
- Conflict: `git merge --no-ff` non-zero / unmerged paths → merge --abort → serial re-dispatch.
- Halt: worktree-ps enumerate → worktree-rm every group worktree (idempotent).
- Else: existing serial path (default).
```

**Acceptance Criteria**:
- [ ] AC-4.1: `SKILL.md` contains a Phase-5 fanout section naming the three verbs and the loop steps.
- [ ] AC-4.2: The engage-conjunction (all three conditions) is stated verbatim; any unmet → serial fallback documented.
- [ ] AC-4.3: `HMAD_ORCA_MAX_WORKTREES` with default `4` is documented.
- [ ] AC-4.4: Halt-path `worktree-rm` cleanup of the whole fanout group is documented.
- [ ] AC-4.5: Doc-presence test `test_skill_documents_fanout_conjunction` (in `h-mad/tests/test_hmad_dispatch.py`) asserts `SKILL.md` contains: (a) the engage-conjunction — all three conditions `substrate=orca`/`orchestration`/`≥2 independent` present in the fanout section; (b) `HMAD_ORCA_MAX_WORKTREES` with default `4`; (c) `worktree-create`; (d) the serial fallback is still described.

**Dependencies on other tasks**: Task 1 (verb names must exist before docs reference them)

## Version History
- v1.0: Initial implementation plan draft.
- v2.0: Impl-plan-audit-v1 fixes — Task 2 test file pinned to `h-mad/tests/test_hmad_dispatch.py` (removed OR ambiguity, must-fix); AC-4.5 renamed to `test_skill_documents_fanout_conjunction` and now asserts the engage-conjunction per the design test plan (should-fix).
