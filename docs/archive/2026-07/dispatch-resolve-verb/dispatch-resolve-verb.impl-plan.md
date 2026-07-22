# Implementation Plan: dispatch-resolve-verb

> Source: docs/02-design/features/dispatch-resolve-verb.design.md (post-audit)
> Branch target: feature/190-dispatch-resolve-verb

## Executive Summary
One task: add the `_cmd_resolve` pure-forwarder handler + `resolve)` dispatch wiring + verb-comment/doc updates to `hmad-dispatch.sh`, covered by new pytest cases in `test_hmad_dispatch.py`.

## Task 1: resolve-verb

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch.py`

**Description**: Add a `_cmd_resolve` shell handler that defaults its single argument and delegates entirely to the existing `_resolve_target`, forwarding stdout (handle), stderr (diagnostic), and exit status (`0`/`1`/`2`) unchanged. Wire it into the `main` dispatch `case` as `resolve)`, list `resolve` in the top-of-file `# Verbs:` comment, and add a one-line `resolve <agent>` entry to `references/agent-substrate.md`'s verb list. No resolution or validation logic is added — `_resolve_target` (and its `_orca_find`/`_cmux_find` helpers and `*)` unknown-agent branch) is the single source for both resolution and agent-token rejection.

**Code structure**:
```bash
# New handler — place adjacent to _cmd_env. Pure forwarder; no agent allowlist.
_cmd_resolve() {
  # resolve <agent> — print the resolved handle/surface for ONE agent (codex|agy)
  # to stdout and exit 0; empty stdout + stderr diagnostic + exit 1 when
  # UNRESOLVED; empty stdout + stderr message + exit 2 for an unknown/missing
  # agent. Single-agent form of what `env` computes for both; delegates to
  # _resolve_target so the two cannot diverge.
  local agent="${1:-}"
  _resolve_target "$agent"      # echoes handle + returns 0 | stderr diag + 1 | unknown/empty + 2
}

# In main()'s dispatch case, adjacent to `env)`:
    resolve) _cmd_resolve "$@" ;;

# Top-of-file header comment (extend the existing "# Verbs:" line):
# Verbs: env | resolve | send | read | wait | alive | clear | interrupt | notify | ...
```

**Acceptance Criteria**:
- [ ] AC-1.1: orca fixture with an `agy` pane + `ORCA_PANE_KEY` → `resolve agy` prints the handle to stdout, exit 0.
- [ ] AC-1.2: stdout is the handle only (no `"agy -> "` prefix, no extra lines).
- [ ] AC-1.3: `HMAD_ORCA_CODEX_TERMINAL=t-x resolve codex` prints `t-x`, exit 0.
- [ ] AC-2.1 / AC-2.2 / AC-2.3: exit `0` resolved · `1` unresolved · `2` unknown agent.
- [ ] AC-3.1: UNRESOLVED → stdout empty, stderr contains `pin HMAD_ORCA_AGY_TERMINAL`.
- [ ] AC-3.2: unknown agent → stdout empty, stderr non-empty.
- [ ] AC-4.1: `resolve codex` / `resolve agy` accepted.
- [ ] AC-4.2: `resolve bogus` → exit 2, empty stdout.
- [ ] AC-4.3: `resolve` (no arg) → exit 2, empty stdout.
- [ ] AC-5.1: for a fixture where `env` prints `agy -> <H>`, `resolve agy` stdout == `<H>`.
- [ ] AC-5.2: for an UNRESOLVED fixture, `resolve agy` stdout empty + non-zero exit.
- [ ] AC-6.1: `resolve` routes to `_cmd_resolve` (not the `*)` unknown-verb branch).
- [ ] AC-6.2: the `# Verbs:` comment lists `resolve`.
- [ ] AC-6.3: an unknown verb still errors + exits 2 (no regression).

**Dependencies on other tasks**: None

## Version History
- v1.0: Initial implementation plan draft.
