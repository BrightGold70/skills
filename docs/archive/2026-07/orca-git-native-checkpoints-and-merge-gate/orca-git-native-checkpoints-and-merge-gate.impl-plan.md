# Implementation Plan: orca-git-native-checkpoints-and-merge-gate

> Source: docs/02-design/features/orca-git-native-checkpoints-and-merge-gate.design.md (post-audit)
> Branch target: feature/NNN-orca-git-native-checkpoints-and-merge-gate

## Executive Summary
One TDD code task (the two wrapper verbs + detection flip in `hmad-dispatch.sh`, with the stub + pytest), then three orchestrator-authored prose tasks (handoff protocol steps, the Phase-5 merge gate, follow-on docs). Only Task 1 has automated tests; Tasks 2–4 are SKILL/reference prose verified by gap-analysis + agy review.

## Task 1: hmad-dispatch worktree verbs + substrate-default flip  *(Codex TDD)*

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch.py` (+ stub `h-mad/tests/stubs/orca`)

**Description**: Add two additive verbs — `worktree-comment [<selector>] <text>` and `worktree-current` — each guarded by `_require_orca`, using capture-then-`jq -e '.ok==true'` (never a bare `orca … | _json_extract` pipe) so both a non-zero exit and an `ok:false` envelope surface on stderr. Flip `_detect_substrate` so both-binaries-present resolves to `orca` by swapping the two binary-presence branches. Register both verbs in `main()` and the header `# Verbs:` catalogue. No existing verb's behavior changes.

**Code structure**:
```bash
_cmd_worktree_comment() {   # [<selector>] <text>
  _require_orca worktree-comment || return $?
  local sel text
  if [ "$#" -ge 2 ]; then sel="$1"; text="$2"; else sel="active"; text="${1:-}"; fi
  _need "$text" text || return $?
  local out
  out="$(orca worktree set --worktree "$sel" --comment "$text" --json)" || { echo "$out" >&2; return $?; }
  printf '%s' "$out" | jq -e '.ok == true' >/dev/null 2>&1 || { echo "$out" >&2; return 1; }
}

_cmd_worktree_current() {   # (no args)
  _require_orca worktree-current || return $?
  local out
  out="$(orca worktree current --json)" || { echo "$out" >&2; return $?; }
  printf '%s' "$out" | jq -e '.ok == true' >/dev/null 2>&1 || { echo "$out" >&2; return 1; }
  printf '%s' "$out" | _json_extract '.result | tojson'
}

# _detect_substrate binary block — swap the two branches:
#   if [ "$has_orca" = 1 ]; then printf 'orca\n'; return 0; fi   # both present => orca
#   if [ "$has_cmux" = 1 ]; then printf 'cmux\n'; return 0; fi
#   return 1
# main(): worktree-comment) _cmd_worktree_comment "$@" ;;   worktree-current) _cmd_worktree_current "$@" ;;
```

**Stub update** (`h-mad/tests/stubs/orca`): handle `worktree set …` (echo an `{"ok":true,"result":{"worktree":{...}}}` envelope; honor `HMAD_STUB_CAPTURE` to record argv) and `worktree current --json` (echo `{"ok":true,"result":{"worktree":{"branch":"refs/heads/main","path":"/x","comment":"c"}}}`). Add an `ok:false` failure mode keyed off an env flag (e.g. `HMAD_STUB_FAIL=1` → print `{"ok":false,"error":"boom"}` exit 0) to test AC-1.5.

**Tests** (RED first, all failing without impl):
- `test_worktree_comment_orca_sets_comment` — `substrate=orca`, `worktree-comment id:w1 "hi"` → capture == `worktree set --worktree id:w1 --comment hi --json`, exit 0.
- `test_worktree_comment_default_selector_active` — one-arg form → capture has `--worktree active`.
- `test_worktree_comment_missing_text_exit2` — no text → exit 2, `missing required argument` on stderr, capture empty (no orca call).
- `test_worktree_comment_requires_orca` — `substrate=cmux` → exit 2, message names substrate, no orca call.
- `test_worktree_comment_propagates_ok_false` — `HMAD_STUB_FAIL=1` → wrapper exit non-zero, error text on stderr, no `OK`.
- `test_worktree_current_orca_reads` — `substrate=orca` → capture == `worktree current --json`; stdout is the payload; capture has no `set`/`create`/`rm`.
- `test_worktree_current_requires_orca` — `substrate=cmux` → exit 2.
- `test_worktree_current_propagates_ok_false` — `HMAD_STUB_FAIL=1` → non-zero, error surfaced.
- `test_detect_default_both_present_is_orca` — stub PATH has both `cmux`+`orca`, no env/marker → `env` prints `substrate: orca`.
- `test_detect_cmux_only_is_cmux`, `test_detect_orca_only_is_orca` — single-binary cases.
- `test_detect_override_forces_cmux` — `HMAD_SUBSTRATE=cmux` with both present → cmux.
- `test_detect_marker_forces_cmux` — `CMUX=1` with both present → cmux (marker precedence).

**Verification**: `pytest h-mad/tests/test_hmad_dispatch.py -v` all pass; `bash -n h-mad/scripts/hmad-dispatch.sh`; full suite `pytest h-mad/tests/ -q` no regression.

**Dependencies on other tasks: None.**

## Task 2: handoff WRITE stamp + READ reconcile  *(orchestrator-authored prose)*

**Production file**: `handoff/SKILL.md` (+ frontmatter description touch)
**Test file**: none (prose protocol; verified by gap-analysis + agy review)

**Description**: Add the WRITE-mode "Stamp an Orca checkpoint (best-effort)" step (D5) and the READ-mode "Worktree reconcile (Orca only)" sub-step (D6), each gated on `hmad-dispatch env` reporting `substrate: orca`, each emitting a `[handoff] *_skipped` marker and falling through on non-zero. Update the SKILL frontmatter/body so the manifest reflects the new behavior (project Axis B: manifest integrity). All Orca access via `hmad-dispatch worktree-comment`/`worktree-current`/`worktree-ps` — no raw `orca`.

**Verification**: `grep` shows the two steps + markers present; frontmatter still valid; no raw `orca ` token in `handoff/SKILL.md`. **Dependencies: Task 1 (verbs must exist).**

## Task 3: Phase-5 winner-merge decision gate  *(orchestrator-authored prose)*

**Production files**: `h-mad/SKILL.md` (Phase-5 fanout sub-section), `h-mad/references/orchestration-mode.md`
**Description**: Replace the unconditional `git merge --no-ff <module-branch>` with the D7 gated sequence: orchestration-off → unchanged serial merge; clean verdict + clean merge → `gate-create`+`gate-resolve yes` (audit trail, non-blocking) + `[H-MAD] merge_gate auto-resolved` marker; conflict → `git merge --abort` + blocking gate; DRIFT/non-clean → no merge + blocking gate. Document the contract in `orchestration-mode.md`.
**Verification**: `grep` shows the gated sequence + markers; the orchestration-off fallback is explicitly retained. **Dependencies: None (uses existing gate verbs).**

## Task 4: Follow-on docs — progress checkpoints, diff-anchor, ship path  *(orchestrator-authored prose)*

**Production file**: `h-mad/references/orchestration-mode.md`
**Description**: FR-7 progress-checkpoint calls in the fanout loop (RED/GREEN/audit → `worktree-comment <sel> "h-mad …"`); FR-8 note that review-diff surfacing anchors to the worktree base ref; FR-9 "Ship path (Orca)" subsection (commit → push `--force-with-lease` → hosted PR), restating the `never git push --force` invariant.
**Verification**: `grep` shows all three additions. **Dependencies: Task 1 (worktree-comment), Task 3 (adjacent section).**

## Implementation Order
1. Task 1 (Codex TDD) — RED → GREEN → suite green → commit.
2. Task 2 (handoff prose) — after verbs exist.
3. Task 3 (merge-gate prose).
4. Task 4 (follow-on docs).
Tasks 2–4 are prose on distinct files; serial, orchestrator-authored, each committed separately. Only Task 1 is a fanout candidate but it is a single module, so Phase-5 runs serial.

## Version History
- v1.0: Initial impl-plan draft.
