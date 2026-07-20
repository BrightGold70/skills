# Design: worktree-parallel-multi-module-tdd

## Executive Summary
Add three `_cmd_worktree_*` bash functions to `hmad-dispatch.sh` (mirroring the existing `_cmd_task_create` guard+jq pattern) plus three `main()` verb cases, and a Phase-5 parallel-fanout protocol section in `SKILL.md` + `references/orchestration-mode.md`; the orchestrator applies the concurrency cap and engage-conjunction, the script stays a thin substrate-guarded Orca wrapper.

## Overview
The change is two-layered and additive. Layer 1 is pure `hmad-dispatch.sh` (three Orca-only verbs, each a ~10-line function following the codebase's established shape: `_require_orca` guard → `_need` arg checks → `orca worktree …` invocation → defensive `jq … // empty` extraction). Layer 2 is documentation the orchestrator follows (partition/engage/fanout/cap/halt-cleanup). No new files, no new dependencies, no changes to existing verbs or the cmux path.

## Architecture Overview
```
Phase 5 (orchestrator, SKILL.md protocol)
  partition impl-plan tasks: independent (deps=None) vs dependent
  IF substrate=orca ∧ coordinator-pin ∧ ≥2 independent:      ── fanout ──┐
    for each independent task (≤ HMAD_ORCA_MAX_WORKTREES live):          │
      wt = hmad-dispatch worktree-create <mod> --base <feat> ──┐         │
      hmad-dispatch task-create + dispatch  (Tier-2, --to wt)  │ per mod │
      hmad-dispatch await <task>            (Tier-2)           │         │
      git merge --no-ff <mod-branch>  → conflict? abort+serial │         │
      hmad-dispatch worktree-rm <wt>                          ─┘         │
    dependent tasks: serial (topological order, shared tree)  ───────────┘
  ELSE: existing serial Phase-5 path (unchanged)              ── fallback ──

hmad-dispatch.sh (Layer 1)
  _cmd_worktree_create ─ _require_orca ─ orca worktree create --json ─ jq selector
  _cmd_worktree_ps     ─ _require_orca ─ orca worktree ps --json     ─ jq .result
  _cmd_worktree_rm     ─ _require_orca ─ orca worktree rm --json     ─ exit passthrough
```

## Detailed Design

### `_json_extract` shared helper (single-source contract)
One authoritative extractor all three new verbs call — no inlined per-verb jq chains (resolves design-audit-v1 must-fix). Tier-2 verbs currently inline the `jq '… // empty'` idiom with no shared function; this feature adds the shared function for the NEW code (Tier-2 retrofit is out-of-scope).
```bash
_json_extract() {   # $1 = jq alternation expr; reads JSON on stdin, prints first non-empty match
  jq -r "${1} // empty"
}
```
All three verbs pipe `orca … --json` into `_json_extract '<alternation>'`. A single test asserts the helper's behavior; the verbs are tested for *which alternation* they pass, not a re-implemented chain — satisfying "exactly one authoritative implementation."

### `_cmd_worktree_create` (FR-1)
- Signature (positional + flags): `worktree-create <name> [--agent <id>] [--base <ref>] [--prompt-file <path>]`.
- Guard: `_require_orca worktree-create || return $?` (returns non-zero + stderr message on substrate≠orca; the `_require_orca` helper already emits the refusal — marker discipline satisfied by the caller/orchestrator emitting `[H-MAD]`, consistent with how `_cmd_task_create` behaves today).
- Arg check: `_need "${1:-}" name || return $?`.
- Flag parse: `shift`, then a `while [ $# -gt 0 ]` loop (same idiom as `_cmd_await`/`_cmd_read`) collecting `--agent`, `--base`, `--prompt-file` into locals.
- Build argv incrementally into a bash array `args=(worktree create --name "$name")`; append `--agent "$agent"`, `--base-branch "$base"` when set; for `--prompt-file`, `[ -f "$f" ] || return 2` then append `--prompt "$(cat "$f")"`; always append `--json`.
- Invoke + extract: `orca "${args[@]}" | _json_extract '.result.worktree.selector // .result.worktree.handle // .result.selector // .result.handle // .result.id // .id'` — the shared helper appends `// empty`; the alternation covers the plausible shapes (exact live key unverifiable without a real Orca; a test pins the canned-stub key).

### `_cmd_worktree_ps` (FR-2)
- Signature: `worktree-ps [--limit <n>]`.
- Guard: `_require_orca worktree-ps`.
- Build `args=(worktree ps)`; append `--limit "$n"` when `--limit` given; append `--json`.
- Invoke + passthrough: `orca "${args[@]}" | _json_extract '.result | tojson'` (compact JSON string of `.result`) — emits the JSON `.result` payload (parseable), not scrape text (AC-2.2). The shared helper is the single extraction surface.

### `_cmd_worktree_rm` (FR-3)
- Signature: `worktree-rm <selector> [--force]`.
- Guard: `_require_orca worktree-rm`; `_need "${1:-}" selector`.
- Build `args=(worktree rm --worktree "$sel")`; append `--force` when flag present; append `--json`.
- Invoke passing through exit: `orca "${args[@]}" >/dev/null` then `local rc=$?; [ $rc -eq 0 ] || { echo "[H-MAD] worktree-rm failed selector=$sel rc=$rc" >&2; return $rc; }` — a failed rm surfaces non-zero (AC-3.2), not swallowed.

### `main()` verb cases
Three new lines in the `case "$verb"` block: `worktree-create) _cmd_worktree_create "$@" ;;` etc. Additive; no existing case touched.

### Phase-5 fanout protocol (FR-4/5/6 — SKILL.md + orchestration-mode.md)
- **Partition**: read impl-plan; a task with `Dependencies on other tasks: None` is *independent*; anything else is *dependent*.
- **Engage-conjunction** (all three required, else serial fallback): `hmad-dispatch env` reports `substrate: orca` AND `orchestration: on` (coordinator pinned) AND ≥2 independent tasks.
- **Fanout loop**: for each independent task, up to `HMAD_ORCA_MAX_WORKTREES` (default **4**) live at once — `worktree-create <mod> --base <feature-branch> --prompt-file <staged Codex RED/GREEN prompt>`; drive TDD via Tier-2 `task-create`+`dispatch --to <worktree-selector>`; `await` the `worker_done`; `git merge --no-ff <mod-branch>` into the feature branch; `worktree-rm <selector>`. Tasks beyond the cap queue (log `[H-MAD] worktree_queued module=<m>`).
- **Merge-conflict detection**: `git merge --no-ff` non-zero exit OR `git ls-files --unmerged` non-empty → `git merge --abort`, `[H-MAD] merge_conflict module=<m>`, halt that module, re-dispatch it on the serial path after siblings merge.
- **Dependent tasks**: serial, topological order, shared working tree (current behavior).
- **Halt cleanup**: on any Phase-5 halt during an active fanout, enumerate via `worktree-ps` and `worktree-rm` every worktree in the group (idempotent — rm on a gone selector logs + no-ops).

## Components Changed / Added
| Component | File path | Change type | Purpose |
|---|---|---|---|
| `_json_extract` helper | `h-mad/scripts/hmad-dispatch.sh` | new | single-source extraction for all 3 verbs |
| `_cmd_worktree_create` | `h-mad/scripts/hmad-dispatch.sh` | new | FR-1 |
| `_cmd_worktree_ps` | `h-mad/scripts/hmad-dispatch.sh` | new | FR-2 |
| `_cmd_worktree_rm` | `h-mad/scripts/hmad-dispatch.sh` | new | FR-3 |
| 3 `main()` verb cases | `h-mad/scripts/hmad-dispatch.sh` | modify | route verbs |
| Phase-5 fanout section | `h-mad/SKILL.md` | modify | FR-4/5/6 |
| Orchestration fanout detail | `h-mad/references/orchestration-mode.md` | modify | FR-4 detail |
| Verb tests | `h-mad/tests/test_hmad_dispatch.py` | modify | FR-1/2/3 ACs |

## Implementation Order
1. `_cmd_worktree_create` + verb case + tests (RED→GREEN).
2. `_cmd_worktree_ps` + verb case + tests.
3. `_cmd_worktree_rm` + verb case + tests.
4. SKILL.md + orchestration-mode.md fanout protocol (doc; verified by a doc-presence test asserting the engage-conjunction + cap default strings).

## Data Model / Schema Changes
None. State schema unchanged; fanout emits only `[H-MAD]` log markers (optional telemetry), no new required `orchestrator_state` field.

## API / Interface Changes
Three new `hmad-dispatch` verbs (above). One new env knob `HMAD_ORCA_MAX_WORKTREES` (integer, default 4). No change to existing verbs, flags, or the cmux path.

## Error Handling Strategy
- Substrate guard: `_require_orca` returns non-zero + stderr on substrate≠orca (no `orca` invoked) — AC-1.3/2.3/3.3.
- Missing required arg: `_need` returns 2 + stderr.
- `--prompt-file` missing: return 2 before any `orca` call.
- `orca` non-zero (unknown selector, etc.): surfaced as the function's non-zero exit + `[H-MAD]` marker (rm) — never swallowed (AC-3.2).
- Empty jq extraction: `// empty` yields empty stdout; the orchestrator treats empty selector as a create failure and halts the module.

## Test Strategy
Unit tests only (live-Orca e2e is out-of-scope/deferred). Reuse the existing `test_hmad_dispatch.py` harness that puts a **stub `orca`** on `PATH` (records argv to a file, echoes canned `--json`). Per verb: (a) argv assertion — stub captures the exact `orca worktree …` argv; (b) JSON parse — canned stub output → asserted stdout (selector / `.result`); (c) substrate guard — with `HMAD_SUBSTRATE=cmux` (or stub `orca` absent) the verb exits non-zero and the stub argv file is empty (no `orca` call). Doc test: assert SKILL.md contains the engage-conjunction and `HMAD_ORCA_MAX_WORKTREES` default-4 strings.

## Test Plan
- `test_worktree_create_argv_orca` — substrate=orca stub; `worktree-create m --agent a1 --base main` → stub argv == `worktree create --name m --agent a1 --base-branch main --json`.
- `test_worktree_create_parses_selector` — canned stub JSON `{"result":{"worktree":{"selector":"wt-7"}}}` → stdout `wt-7`.
- `test_worktree_create_prompt_file` — `--prompt-file /tmp/p` with contents `X` → argv contains `--prompt X`; missing file → exit 2, no orca call.
- `test_worktree_create_refuses_cmux` — `HMAD_SUBSTRATE=cmux` → non-zero, empty stub argv.
- `test_json_extract_helper` — `echo '{"result":{"selector":"wt-9"}}' | _json_extract '.result.selector'` → `wt-9`; empty match → empty stdout (the one authoritative extractor).
- `test_worktree_ps_argv_and_passthrough` — `worktree-ps --limit 3` → argv `worktree ps --limit 3 --json`; canned `.result` → stdout is that JSON (via `_json_extract '.result | tojson'`).
- `test_worktree_rm_argv_and_force` — `worktree-rm wt-7 --force` → argv `worktree rm --worktree wt-7 --force --json`; stub non-zero → verb non-zero.
- `test_worktree_verbs_refuse_cmux` — ps + rm under cmux → non-zero, no orca call.
- `test_skill_documents_fanout_conjunction` — SKILL.md contains engage-conjunction + `HMAD_ORCA_MAX_WORKTREES` default 4.
- Verification command: `cd /Users/kimhawk/Coding/skills && python3 -m pytest h-mad/tests/test_hmad_dispatch.py -v`.

## Invariant Compliance
- **Audit-gate signal discipline**: N/A — no new gate; verbs signal via exit code (operational) which is correct for a dispatch wrapper, not an audit gate.
- **Single-source contract**: all three new verbs extract JSON through ONE shared `_json_extract` helper (no inlined per-verb chains that could diverge); substrate detection / coordinator resolution reuse the existing `_require_orca`/`_detect_substrate`/`_coordinator` as-is. Exactly one authoritative extractor for the new code. Complies (resolves design-audit-v1 must-fix).
- **Standalone / no plugin dependency**: verbs call only `orca` + `jq` (both already substrate/hook dependencies). No new plugin/skill runtime dependency. Complies.
- **No new external dependency**: only `orca` (existing substrate) + `jq` (already used by Tier-1/2 verbs) + `git` (already required by the workflow). No new package/CLI. Complies.
- **Doc-template superset compliance**: this design + its plan/report live under `docs/02-design`, `docs/01-plan`, `docs/04-report` with the h-mad sections retained. Complies.
- **Operator-override preservation**: no gate change. Complies.
- **Backward compatibility**: no gate change; existing verbs + tests untouched. Complies.
- **Marker discipline**: fanout transitions/halts emit `[H-MAD]` markers (merge_conflict, worktree_queued, worktree-rm failure). Complies.
- **Skill self-containment** (project): all new logic inside `h-mad/`; no path outside the skill dir except the documented `orca`/`git` binaries. Complies.
- **Skill manifest integrity** (project): SKILL.md gains a Phase-5 fanout section; frontmatter `name`/`description` unchanged (behavior extended, contract documented). Complies.

## Schema-pinning note (design-audit-v1 nit)
Schema pinning is **manual at build time**, by policy (the Tier-1 lesson: reconcile Orca argv against `orca agent-context --json` schema v1 when authoring the verb). There is no automated schema-validation step — the usage strings were verified against live `agent-context --json` output during design (see plan G4). Tests assert argv against the pinned strings via stub capture; a live-schema-drift check is a deferred carry alongside the live-Orca e2e gap.

## Version History
- v1.0: Initial design draft.
- v2.0: Design-audit-v1 fixes — introduced single shared `_json_extract` helper routed by all three verbs (single-source contract, must-fix); documented manual build-time schema pinning (nit). Paired with plan v3.0.
