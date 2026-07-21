# Design: orca-git-native-checkpoints-and-merge-gate

## Executive Summary
Two new read-only-safe `hmad-dispatch` wrapper verbs plus a one-branch detection-default change, consumed by prose protocol steps added to `handoff/SKILL.md` and a gated merge sequence in the h-mad Phase-5 fanout — every Orca call fail-open and substrate-gated.

## Overview
The design keeps all Orca access inside `hmad-dispatch` (the chokepoint invariant), adds only additive verbs and protocol steps, and never changes an existing verb's contract. Key decisions: (1) new verbs mirror the exact shape of `_cmd_worktree_rm`/`_cmd_worktree_ps`; (2) the detection flip swaps the two binary-presence branches and touches nothing above them; (3) skill-side Orca enrichment is best-effort — a non-zero wrapper exit is logged via a greppable marker and swallowed, never propagated; (4) the merge gate only engages under `orchestration: on` and only blocks on conflict/DRIFT/dirty.

## Architecture Overview
```
handoff/SKILL.md ─┐                         ┌─ orca worktree set --comment   (FR-3 stamp)
                  ├─► hmad-dispatch <verb> ─┼─ orca worktree current --json  (FR-4 reconcile)
h-mad Phase 5 ────┘   (sole Orca surface)   ├─ orca worktree ps --json       (FR-4 reconcile, existing)
                                            └─ orca orchestration gate-*     (FR-6 merge gate, existing)
                          │
                  _detect_substrate (FR-2): both binaries present → orca
```
No skill body calls `orca` directly. Non-orca substrate → every wrapper returns non-zero at the `_require_orca` guard; callers log `_skipped` and continue.

## Detailed Design

### D1 — `_cmd_worktree_comment` (FR-1)
Mirrors `_cmd_worktree_rm`. Signature `worktree-comment [<selector>] <text>` with `<selector>` defaulting to `active`.
- Guard: `_require_orca worktree-comment || return $?`.
- Arg parsing: if one positional arg → selector=`active`, text=`$1`; if two → selector=`$1`, text=`$2`. `_need "$text" text || return $?` — `_need` prints exactly `hmad-dispatch: missing required argument: text` to stderr and returns 2, satisfying AC-1.3's `missing required argument` message contract, and makes no orca call. Rationale for the 1-or-2 form: callers stamp the active worktree in the common case (`worktree-comment "text"`) and name a fanned worktree in Phase-5 (`worktree-comment id:<id> "text"`).
- Call: capture-then-check (do NOT pipe orca straight into `_json_extract`, which would mask an `ok:false`). `out="$(orca worktree set --worktree "$sel" --comment "$text" --json)" || { echo "$out" >&2; return $?; }`; then `printf '%s' "$out" | jq -e '.ok == true' >/dev/null || { echo "$out" >&2; return 1; }`. On a non-zero orca exit OR an `ok:false` envelope → print orca's error text on stderr and return non-zero; never print success. (`set -euo pipefail` at the top of the wrapper already propagates a non-zero *exit*; the explicit `.ok` check is what additionally catches the exit-0-but-`ok:false` error envelope that pipefail cannot see.)

### D2 — `_cmd_worktree_current` (FR-1, FR-4)
Read-only; same capture-then-check contract as D1 so an error is surfaced rather than swallowed by the pipe (AC-1.5).
- Guard: `_require_orca worktree-current || return $?`.
- Call: `out="$(orca worktree current --json)" || { echo "$out" >&2; return $?; }`; then `printf '%s' "$out" | jq -e '.ok == true' >/dev/null || { echo "$out" >&2; return 1; }`; on success `printf '%s' "$out" | _json_extract '.result | tojson'` emits the worktree JSON payload on stdout. No selector, no mutation. Capturing before extraction (rather than `orca … | _json_extract`) is required because a bare pipe would surface `_json_extract`'s exit, not orca's, and could not see an `ok:false` envelope.

### D3 — `_detect_substrate` default flip (FR-2)
Only the binary-presence block changes; the `HMAD_SUBSTRATE` and session-marker blocks above are untouched. The change is a **swap of the two existing branches** on lines 20–21 — the `has_cmux → cmux` and `has_orca → orca` lines exchange order — plus the precedence comment `default cmux` → `default orca`. Before:
```bash
  if [ "$has_orca" = 1 ] && [ "$has_cmux" = 0 ]; then printf 'orca\n'; return 0; fi
  if [ "$has_cmux" = 1 ]; then printf 'cmux\n'; return 0; fi   # both present => cmux
  if [ "$has_orca" = 1 ]; then printf 'orca\n'; return 0; fi
```
After (the two marked lines swapped; the first line is now subsumed by the new second line and is dropped to keep the block minimal and non-redundant):
```bash
  if [ "$has_orca" = 1 ]; then printf 'orca\n'; return 0; fi   # both present => orca
  if [ "$has_cmux" = 1 ]; then printf 'cmux\n'; return 0; fi
  return 1
```
This matches the Overview's "reorders the two binary-presence branches" claim exactly: only the two binary branches move, nothing above the binary block is touched.

### D4 — `main()` + header (FR-1)
Add `worktree-comment) _cmd_worktree_comment "$@" ;;` and `worktree-current) _cmd_worktree_current "$@" ;;` to the `case`, and both verbs to the line-3 `# Verbs:` catalogue.

### D5 — handoff WRITE stamp (FR-3, FR-5)
New final step in the WRITE-mode protocol (`handoff/SKILL.md`), after the markdown is written:
> **Stamp an Orca checkpoint (best-effort).** If `hmad-dispatch env` reports `substrate: orca`, run
> `hmad-dispatch worktree-comment active "handoff: <slug> · <status> · next: <next-step>"`.
> A non-zero result is non-fatal: emit `[handoff] worktree_comment_skipped` and continue. Never fail the handoff on it.

The check uses `hmad-dispatch env` (already substrate-aware); the skill never calls `orca` directly.

### D6 — handoff READ reconcile (FR-4, FR-5)
New sub-step under the existing "Reconcile with reality" section:
> **Worktree reconcile (Orca only).** If `hmad-dispatch env` reports `substrate: orca`:
> - `hmad-dispatch worktree-current` → compare `.branch`/`.path` to the doc's branch/worktree; a mismatch is surfaced as a divergence line (same treatment as a branch mismatch).
> - `hmad-dispatch worktree-ps` → list all worktrees, each labeled `branch · comment`, so in-flight siblings are visible.
> Read-only: no `worktree-comment`/`create`/`rm`. A non-zero result emits `[handoff] worktree_reconcile_skipped` and the reconcile falls through to today's git+PID path unchanged.

### D7 — Phase-5 winner-merge gate (FR-6)
Replaces the bare `git merge --no-ff <module-branch>` step in the fanout loop (SKILL Phase-5 fanout + `references/orchestration-mode.md`). Pseudocode:
```
if NOT orchestration-on:            # serial/unpinned fallback — unchanged
    git merge --no-ff <mb>          # existing behavior, no gate
else:
    if verdict == DRIFT/non-clean:
        gate=gate-create <task> "Merge <module>? verdict=<v>" '["yes","no"]'   # BLOCKING
        await gate-resolve; act on resolution
    else:
        if git merge --no-ff <mb> succeeds AND git ls-files --unmerged empty:
            gate=gate-create <task> "Auto-record clean merge of <module>" '["yes","no"]'
            gate-resolve <gate> yes                       # audit trail, non-blocking
            emit [H-MAD] merge_gate auto-resolved module=<module>
        else:
            git merge --abort
            gate=gate-create <task> "Merge conflict in <module> — resolve?" '["yes","no"]'  # BLOCKING
            await human gate-resolve; on yes → serial re-dispatch, on no → skip+log
```
`[H-MAD]` markers on every branch (marker discipline).

### D8 — follow-on docs (FR-7, FR-8, FR-9)
- FR-7: in the fanout loop, after RED-verified / GREEN-verified / audit-complete, call `hmad-dispatch worktree-comment <module-selector> "h-mad <feature> · <module> · <RED|GREEN|audit> · <n>/<total>"` (best-effort, D5 degradation rule).
- FR-8: a note in `references/orchestration-mode.md` that `file-open-changed`/`file-diff` surfacing anchors to the worktree base ref under Orca; unchanged best-effort semantics.
- FR-9: a "Ship path (Orca)" subsection documenting commit → push `--force-with-lease` → hosted-review PR, restating the `never git push --force` invariant.

## Components Changed / Added
| Component | File path | Change type | Purpose |
|---|---|---|---|
| `_cmd_worktree_comment` | `h-mad/scripts/hmad-dispatch.sh` | new | FR-1 stamp verb |
| `_cmd_worktree_current` | `h-mad/scripts/hmad-dispatch.sh` | new | FR-1/FR-4 read verb |
| `_detect_substrate` | `h-mad/scripts/hmad-dispatch.sh` | modify | FR-2 default flip |
| `main()` + header verb list | `h-mad/scripts/hmad-dispatch.sh` | modify | FR-1 dispatch |
| `orca` test stub | `h-mad/tests/stubs/orca` | modify | handle `worktree set`/`worktree current` |
| dispatch tests | `h-mad/tests/test_hmad_dispatch.py` | modify | FR-1/FR-2 ACs |
| WRITE stamp step | `handoff/SKILL.md` | modify | FR-3 |
| READ reconcile step | `handoff/SKILL.md` | modify | FR-4 |
| Phase-5 merge gate | `h-mad/SKILL.md`, `h-mad/references/orchestration-mode.md` | modify | FR-6 |
| Progress checkpoints + diff-anchor note + ship-path | `h-mad/references/orchestration-mode.md` | modify | FR-7/8/9 |

## Implementation Order
1. `_cmd_worktree_comment` + `_cmd_worktree_current` + `main()`/header (FR-1) — with tests + stub.
2. `_detect_substrate` flip (FR-2) — with tests.
3. handoff WRITE stamp + READ reconcile (FR-3/4/5) — prose, consumes verbs from step 1.
4. Phase-5 merge gate (FR-6) — prose, consumes existing gate verbs.
5. Follow-on docs (FR-7/8/9).
(Steps 1–2 are the only testable-by-pytest modules and are independent → Phase-5 fanout candidates; 3–5 are prose and serial.)

## Data Model / Schema Changes
None. No `orchestrator_state` field added; no new config key. Worktree comment is free-text owned by the `handoff:`/`h-mad` prefix convention (documented, not schema-enforced).

## API / Interface Changes
- New CLI verbs: `hmad-dispatch worktree-comment [<selector>] <text>` and `hmad-dispatch worktree-current`. No flags beyond the selector positional.
- `_detect_substrate` return value for the both-present case: `cmux` → `orca` (behavioral change, documented in `agent-substrate.md`).
- No change to any existing verb signature.

## Error Handling Strategy
- Wrapper verbs: `_require_orca`/`_need` return non-zero (exit 2) with a stderr message (`_need` prints `missing required argument: <name>`) and make no `orca` call. Both new verbs use capture-then-check (`out="$(orca …)"` → `jq -e '.ok==true'`) rather than a bare `orca … | _json_extract` pipe, so BOTH a non-zero orca exit (also caught by the wrapper's `set -o pipefail`) AND an exit-0-`ok:false` error envelope surface orca's error text on stderr and return non-zero; success prints payload/nothing, never a false `OK`.
- Skill callers (handoff, Phase-5 checkpoints): treat any non-zero wrapper exit as a **non-fatal skip** — emit a single `[handoff] *_skipped` / `[H-MAD] *_skipped` marker and continue on the pre-feature path. Never a stack trace, never a non-zero skill exit (FR-5).
- Merge gate: a conflict is caught by `git merge` exit + `git ls-files --unmerged`; `git merge --abort` restores the tree before the blocking gate opens (no partial-merge state).

## Test Strategy
Unit tests via the existing `test_hmad_dispatch.py` harness (stub `orca` on an isolated PATH, `HMAD_STUB_CAPTURE` records the argv the stub received). Mock boundary = the `orca` binary (stub), so tests assert the exact subcommand+flags the wrapper emits without a live runtime. Prose-protocol changes (FR-3…FR-9) are not pytest-testable; they are verified by Phase-6 gap-analysis (≥90%) and the agy 6a-prime reachability review.

## Test Plan
- `test_worktree_comment_orca_sets_comment` — `substrate=orca`, `worktree-comment id:w1 "hi"` → stub captures `worktree set --worktree id:w1 --comment hi --json`, exit 0.
- `test_worktree_comment_default_selector_active` — one-arg form → captured `--worktree active`.
- `test_worktree_comment_missing_text_exit2` — no text → exit 2, stub NOT invoked (capture empty).
- `test_worktree_comment_requires_orca` — `substrate=cmux` → exit 2, message names substrate, no orca call.
- `test_worktree_comment_propagates_orca_failure` — stub returns `ok:false`/nonzero → wrapper non-zero, no `OK`.
- `test_worktree_current_orca_reads` — `substrate=orca` → captures `worktree current --json`, emits payload; assert no `set`/`create`/`rm` in capture.
- `test_worktree_current_requires_orca` — `substrate=cmux` → exit 2.
- `test_detect_default_both_present_is_orca` — stub PATH with both `cmux`+`orca`, no env/marker → `env` reports `substrate: orca`.
- `test_detect_cmux_only_is_cmux` / `test_detect_orca_only_is_orca` — single-binary cases.
- `test_detect_override_and_marker_precedence` — `HMAD_SUBSTRATE=cmux` and `CMUX=1` each still force cmux with both binaries present.
- Verification commands: `pytest h-mad/tests/test_hmad_dispatch.py -v` (all pass, 100%); full suite `pytest h-mad/tests/ -q` shows no regression.

## Invariant Compliance
**Base (Axis B):**
- Audit-gate signal discipline — no gate/verdict script changed; N/A, complies.
- Single-source contract — the two new verbs are the single implementation of their Orca calls; both skills call them, no re-implementation. Complies.
- Standalone / no plugin dependency — verbs are thin `orca` CLI wrappers; `handoff` calls `hmad-dispatch` as a CLI (not a library import), acquiring no runtime plugin dependency. Complies.
- No new external dependency — uses only `orca` (already the substrate) + `jq` (already used) + `bash`/`pytest`. No new package. Complies.
- Doc-template superset compliance — plan/design/report docs retain all h-mad sections + PDCA dirs. Complies.
- Operator-override preservation — no audit-gate change; the `## Acknowledged-not-fixed` sidecar is untouched. Complies.
- Backward compatibility — no audit-gate change; historically-passing audits unaffected. Existing verbs unchanged. Complies.
- Marker discipline — every merge-gate branch + every skipped enrichment emits a `[H-MAD]`/`[handoff]` marker. Complies.

**Project (Axis B):**
- Skill self-containment — no cross-skill internal import; `handoff` invokes the `hmad-dispatch` CLI by its installed path, not h-mad Python internals. The wrapper is a standalone script runnable from a bare clone. Complies. *(Note: `handoff` gains a soft runtime reliance on `hmad-dispatch` being on PATH; it degrades gracefully when absent — treated as environment, not a cross-skill code import.)*
- Skill manifest integrity — `handoff/SKILL.md` frontmatter + body updated to document the new WRITE/READ behavior; the entry contract reflects the change. Complies.

## Version History
- v1.0: Initial design draft.
- v1.1: Design-audit cycle-1 resolved. AC-1.3 — D1 now states `_need` emits the `missing required argument` string. AC-1.5 — D1 and D2 use capture-then-`jq -e '.ok==true'` instead of a bare pipe, so `ok:false` envelopes (invisible to pipefail) surface as errors. Should-fix — D3 rewritten as a true two-branch swap (redundant first branch dropped) matching the Overview's claim; Error Handling + Overview wording aligned.
