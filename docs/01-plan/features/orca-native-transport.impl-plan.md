# Implementation Plan: orca-native-transport

> Source: docs/02-design/features/orca-native-transport.design.md (post-audit v1)
> Branch target: feature/orca-native-transport

## Executive Summary
Three tasks: correct the `_cmd_wait`/`_cmd_read` Orca arms (native `--for tui-idle --timeout-ms` / `--limit`), correct the `_cmd_alive`/`_orca_find` JSON path to `.result.terminals[].handle`, and update `agent-substrate.md`. All edits are within `h-mad/scripts/hmad-dispatch.sh` (Orca arms only) + tests + one doc; every cmux arm is byte-identical.

## Task 1: Orca `wait` + `read` native flags (FR-1, FR-2)

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch.py`

**Description**: Correct the Orca case-arms of `_cmd_wait` and `_cmd_read` to the schema-v1 native forms. `_cmd_wait` reuses the existing `--timeout <s>` parse (default 300); `_cmd_read` reuses `--lines <n>` (default 50).

**Code structure** (exact replacements):
```bash
# _cmd_wait — orca arm
    orca) orca terminal wait --terminal "$target" --for tui-idle --timeout-ms "$(( timeout * 1000 ))" ;;
# _cmd_read — orca arm
    orca) orca terminal read --terminal "$target" --limit "$lines" ;;
```

**Acceptance Criteria**:
- [ ] AC-1.1: Under `HMAD_SUBSTRATE=orca` (pin `HMAD_ORCA_<AGENT>_TERMINAL`), `hmad-dispatch wait <agent>` invokes exactly `orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 300000` (assert full argv; no bare `tui-idle` positional).
- [ ] AC-1.2: `hmad-dispatch wait <agent> --timeout 30` → `--timeout-ms 30000`.
- [ ] AC-1.3: `hmad-dispatch read <agent> --lines 50` invokes exactly `orca terminal read --terminal <handle> --limit 50` (no `tail`, no pipe); default (no `--lines`) → `--limit 50`.

**Dependencies on other tasks**: None.

---

## Task 2: Orca `alive` + `_orca_find` JSON path (FR-3)

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch.py`

**Description**: Correct the guessed `.[] | select(.id …)` JSON path to the real `.result.terminals[]` keyed by `.handle` in both `_cmd_alive` (liveness) and `_orca_find` (identity resolution). `_orca_find`'s substring match uses `.preview`/`.title` and returns `.handle`; zero/multiple → non-zero + pin hint (unchanged). The `HMAD_ORCA_<AGENT>_TERMINAL` pin still bypasses `_orca_find`.

**Code structure** (exact replacements):
```bash
# _cmd_alive — orca arm jq
      if orca terminal list --json | jq -e --arg id "$target" '.result.terminals[] | select(.handle == $id)' >/dev/null 2>&1; then
# _orca_find — jq
  ids="$(orca terminal list --json | jq -r \
    --arg t "$token" '.result.terminals[] | select(((.preview//"") + " " + (.title//"")) | test($t)) | .handle')"
```

**Acceptance Criteria**:
- [ ] AC-3.1: `_cmd_alive` under orca with canned stub stdout `{"result":{"terminals":[{"handle":"term_x"}]}}`: pin `term_x` → exit 0; pin `term_y` → exit 1.
- [ ] AC-3.2: `_orca_find` with canned `{"result":{"terminals":[{"handle":"term_c","preview":"codex ..."},{"handle":"term_a","preview":"agy ..."}]}}` resolves `codex`→`term_c`, `agy`→`term_a` (via `env` mapping output); the **existing** `test_orca_identity_resolves_from_list_json` is updated to this shape.
- [ ] AC-3.3: An explicit `HMAD_ORCA_CODEX_TERMINAL=term_pin` is used verbatim as `--terminal term_pin` and does not invoke `_orca_find` (regression guard).

**Dependencies on other tasks**: None (independent arm).

---

## Task 3: `agent-substrate.md` schema-confirmed (FR-4)

**Production file**: `h-mad/references/agent-substrate.md`
**Test file**: none (documentation; covered by the existing doc-template test if applicable).

**Description**: Rewrite the "Open items" bullets to state the schema-v1-confirmed Orca forms: `terminal wait --for exit|tui-idle [--timeout-ms]`, `terminal read [--limit <n>]`, `terminal list --json → .result.terminals[].handle`; keep the note that no field names the running program, so a handle pin is the reliable identity.

**Acceptance Criteria**:
- [ ] AC-4.1: `agent-substrate.md` no longer lists the `orca terminal wait`/`read`/`list` shapes under an unresolved "confirm against live CLI" open-item; it states the confirmed forms + the `.result.terminals[].handle` list shape.

**Dependencies on other tasks**: None.

## Version History
- v1.0: Initial implementation plan draft.
