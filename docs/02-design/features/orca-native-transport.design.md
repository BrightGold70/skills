# Design: orca-native-transport

## Executive Summary
Four surgical corrections to the Orca case-arms of `h-mad/scripts/hmad-dispatch.sh` — `_cmd_wait` (native `--for tui-idle --timeout-ms`), `_cmd_read` (native `--limit`), `_cmd_alive` and `_orca_find` (real `.result.terminals[].handle` JSON path) — plus updated `agent-substrate.md` and tests. Every cmux arm is byte-identical.

## Overview
The Orca verbs were guessed at original-build time. Against the confirmed `orca agent-context` schema v1 and a live `orca terminal list --json`, four emitted commands are wrong: `wait` (bad flag form), `read` (redundant `tail`), and `alive`/`_orca_find` (guessed `.[] | select(.id …)` vs real `.result.terminals[]` keyed by `.handle`). This corrects all four. Verb names and semantics are unchanged, so `SKILL.md` and callers are unaffected.

## Architecture Overview
```
_cmd_wait  orca arm:  orca terminal wait --terminal <h> tui-idle          →  orca terminal wait --terminal <h> --for tui-idle --timeout-ms <ms>
_cmd_read  orca arm:  orca terminal read --terminal <h> | tail -n <n>     →  orca terminal read --terminal <h> --limit <n>
_cmd_alive orca arm:  list --json | jq '.[]|select(.id==$id)'             →  list --json | jq '.result.terminals[]|select(.handle==$id)'
_orca_find:           list --json | jq '.[]|select(.command/.name)|.id'   →  list --json | jq '.result.terminals[]|select(.preview/.title)|.handle'
```
cmux arms of every verb: unchanged.

## Detailed Design

### D1 — `_cmd_wait` Orca arm (FR-1)
Replace the arm
`orca) orca terminal wait --terminal "$target" tui-idle ;;`
with
`orca) orca terminal wait --terminal "$target" --for tui-idle --timeout-ms "$(( timeout * 1000 ))" ;;`
The existing `--timeout <s>` parse (default 300) is reused; `timeout * 1000` yields ms. Exit status propagates (0 idle / non-zero timeout). The cmux poll-until-stable arm is unchanged.

### D2 — `_cmd_read` Orca arm (FR-2)
Replace the arm
`orca) orca terminal read --terminal "$target" | tail -n "$lines" ;;`
with
`orca) orca terminal read --terminal "$target" --limit "$lines" ;;`
The existing `--lines <n>` parse (default 50) supplies `--limit`. No shell pipe in the emitted command. cmux arm unchanged.

### D3 — `_cmd_alive` Orca arm (FR-3)
Replace the jq in the orca arm
`orca terminal list --json | jq -e --arg id "$target" '.[] | select(.id == $id)' >/dev/null 2>&1`
with
`orca terminal list --json | jq -e --arg id "$target" '.result.terminals[] | select(.handle == $id)' >/dev/null 2>&1`
(kept inside the existing `if … then return 0 else return 1 fi`). Real terminals live under `.result.terminals[]` keyed by `.handle`.

### D4 — `_orca_find` JSON path (FR-3)
Replace the jq
`.[] | select(((.command//"") + " " + (.name//"")) | test($t)) | .id`
with
`.result.terminals[] | select(((.preview//"") + " " + (.title//"")) | test($t)) | .handle`
No field names the running program, so the substring match uses `.preview` (live screen) + `.title` (best-effort); the returned identity is `.handle`. Zero/multiple-candidate handling (the `n` count + pin-hint on stderr) is unchanged. The explicit `HMAD_ORCA_<AGENT>_TERMINAL=<handle>` pin still bypasses `_orca_find` in `_resolve_target` (the reliable path).

### D5 — `agent-substrate.md` (FR-4)
Rewrite the "Open items" bullets: state that `terminal wait --for exit|tui-idle [--timeout-ms]`, `terminal read [--limit <n>] [--cursor <n>]`, and `terminal list --json → .result.terminals[].handle` are confirmed against `orca agent-context` schema v1; keep the note that no field names the running program so a handle pin is the reliable identity.

## Components Changed / Added
| Component | File path | Change type | Purpose |
|---|---|---|---|
| `_cmd_wait` orca arm | `h-mad/scripts/hmad-dispatch.sh` | modify | native idle-wait |
| `_cmd_read` orca arm | `h-mad/scripts/hmad-dispatch.sh` | modify | native `--limit` |
| `_cmd_alive` orca arm | `h-mad/scripts/hmad-dispatch.sh` | modify | real `.result.terminals[].handle` |
| `_orca_find` jq | `h-mad/scripts/hmad-dispatch.sh` | modify | real path + `.handle` |
| tests | `h-mad/tests/test_hmad_dispatch.py` | modify | argv + shape assertions |
| reference | `h-mad/references/agent-substrate.md` | modify | schema-v1-confirmed forms |

## Implementation Order
1. D1 `_cmd_wait` + test. 2. D2 `_cmd_read` + test. 3. D3/D4 `_cmd_alive`/`_orca_find` + update `test_orca_identity_resolves_from_list_json` to real shape + alive test. 4. D5 doc.

## Data Model / Schema Changes
None (shell-only; no serialized schema). The Orca `terminal list --json` shape (`.result.terminals[].handle`) is an external contract, not owned here.

## API / Interface Changes
None to the `hmad-dispatch` CLI surface — verb names, args (`--lines`, `--timeout`, agent names), and exit contracts are unchanged. Only the Orca-side emitted command strings change.

## Error Handling Strategy
- `wait`/`read`: return the underlying `orca` exit status (unchanged contract).
- `alive`: `jq -e` non-zero (no match) → `return 1`; match → `return 0` (unchanged 0/1 contract; the jq path is what's fixed).
- `_orca_find`: zero/multiple matches → non-zero exit + pin-hint on stderr (unchanged); the pin path bypasses it entirely.

## Test Strategy
All tests stub the `orca` executable on `PATH` (echo argv to a capture file; emit canned `--json` on stdout) — no live Orca, no network (consistent with the existing harness).
- `wait`: assert argv `orca terminal wait --terminal <id> --for tui-idle --timeout-ms 300000`; `--timeout 30` → `--timeout-ms 30000`.
- `read`: assert argv `orca terminal read --terminal <id> --limit 50`; no `tail` (assert the emitted argv, and that the stub's stdout passes through unmodified).
- `alive`: canned stdout `{"result":{"terminals":[{"handle":"term_x"}]}}`; pin `term_x` → exit 0; pin `term_y` → exit 1.
- `_orca_find`/identity: **update** `test_orca_identity_resolves_from_list_json` to canned `{"result":{"terminals":[{"handle":"term_c","preview":"codex ..."},{"handle":"term_a","preview":"agy ..."}]}}` and assert the resolver returns `term_c`/`term_a`; assert the `HMAD_ORCA_*_TERMINAL` pin bypasses resolution.

## Test Plan
- `h-mad/tests/test_hmad_dispatch.py`: add `test_wait_orca_*`, `test_read_orca_limit`, `test_alive_orca_handle_*`; update `test_orca_identity_resolves_from_list_json`.
- Verify: `python3 -m pytest h-mad/tests/test_hmad_dispatch.py -v`, then the full `h-mad/tests/` suite at Phase 5f.

## Invariant Compliance
- **Skill self-containment**: all edits within `h-mad/`; no cross-skill import, no path outside the skill dir. Complies.
- **Skill manifest integrity**: verb names/semantics/`SKILL.md` contract unchanged (only Orca-side emitted commands corrected). Complies.
- **Base — backward compatibility**: every cmux arm byte-identical; the Orca arms were non-functional-as-guessed, so correcting them cannot regress a working path. Complies.
- **Base — audit-gate / marker / single-source / operator-override / doc-template**: unaffected (no gate/marker/template change). Complies.

## Version History
- v1.0: Initial design draft.
