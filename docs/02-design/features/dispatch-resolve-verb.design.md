# Design: dispatch-resolve-verb

## Executive Summary
Add a `_cmd_resolve` pure-forwarder handler and a `resolve)` dispatch entry to `hmad-dispatch.sh`, surfacing `_resolve_target`'s single-agent resolution (handle→stdout, `0/1/2`, stderr diagnostics) as a scriptable verb.

## Overview
The design is deliberately minimal: one new handler that defaults its argument and delegates to `_resolve_target`, one dispatch-table line, one `# Verbs:` comment update, and one line in `references/agent-substrate.md` so the documented verb set stays truthful. No resolution, validation, or diagnostic logic is added — all of it already lives in `_resolve_target` and its `_orca_find`/`_cmux_find` helpers. This keeps `env` and `resolve` computing identically (FR-5) and satisfies the Single-source invariant the v1 plan audit flagged.

## Architecture Overview
```
main "$@"                       # dispatch case
  └─ resolve) _cmd_resolve "$@" # NEW verb wiring, adjacent to env)
        └─ _cmd_resolve
              agent="${1:-}"     # default so a missing arg can't trip set -u
              _resolve_target "$agent"   # EXISTING single source
                 ├─ orca:  pin? → echo handle,0 | _orca_find → handle,0 / diag→stderr,1
                 ├─ cmux:  pin? → echo surface,0 | _cmux_find → surface,0 / diag→stderr,1
                 └─ *)     unknown/empty agent → "unknown agent" →stderr, 2
              return $?          # forward status verbatim
```
`_cmd_env` already calls `_resolve_target` in a loop over `codex agy`; `_cmd_resolve` calls the same function for one agent. Parity is structural, not coincidental.

## Detailed Design
`_cmd_resolve`:
1. `local agent="${1:-}"` — defaulting guarantees FR-4.3 (missing arg) is safe even if the script runs under `set -u`; the empty string then flows to `_resolve_target`.
2. `_resolve_target "$agent"` — the single source:
   - **Resolved**: `_resolve_target` (via pin, `_orca_find`, or `_cmux_find`) `printf '%s\n'`s the handle to **stdout** and returns `0`. `_cmd_resolve` adds nothing to stdout.
   - **Unresolved** (0 or >1 candidates): `_orca_find`/`_cmux_find` write the `resolved to N candidates … pin HMAD_ORCA_<A>_TERMINAL` diagnostic to **stderr** and return `1`.
   - **Unknown or empty agent**: the `case "$sub:$agent"` `*)` branch writes `unknown agent '<x>'` to **stderr** and returns `2`. An empty `agent` produces the key `<sub>:` which matches no specific case → `*)`, so missing and unknown collapse to the same `2` — exactly FR-4.2 + FR-4.3.
3. `return $?` — forward `_resolve_target`'s status unchanged (FR-2).

No allowlist is maintained in `_cmd_resolve` (the removed v1 guard); `_resolve_target` is the sole rejector of invalid agents.

## Components Changed / Added
| Component | File path | Change type | Purpose |
|---|---|---|---|
| `_cmd_resolve` | `h-mad/scripts/hmad-dispatch.sh` | new | pure-forwarder handler (FR-1..FR-4) |
| `resolve)` case entry | `h-mad/scripts/hmad-dispatch.sh` | modify | dispatch wiring (FR-6.1) |
| `# Verbs:` header comment | `h-mad/scripts/hmad-dispatch.sh` | modify | list `resolve` (FR-6.2) |
| verb documentation | `h-mad/references/agent-substrate.md` | modify | keep documented verb set truthful (manifest/contract integrity) |
| resolve tests | `h-mad/tests/test_hmad_dispatch.py` | modify | cover FR-1..FR-6 ACs |

## Implementation Order
1. Add `_cmd_resolve` function (near `_cmd_env`).
2. Add `resolve) _cmd_resolve "$@" ;;` to the `main` dispatch case.
3. Add `resolve` to the top-of-file `# Verbs:` comment.
4. Add a one-line `resolve <agent>` entry to `references/agent-substrate.md`'s verb list.
5. Add pytest cases.

## Data Model / Schema Changes
None.

## API / Interface Changes
New CLI verb: `hmad-dispatch resolve <agent>` where `<agent> ∈ {codex, agy}`.
- **stdout**: the resolved handle (orca terminal handle or cmux `surface:N`), single line, on success only.
- **exit**: `0` resolved · `1` unresolved · `2` unknown/missing agent.
- **stderr**: resolution diagnostic on `1`; `unknown agent` on `2`; empty on `0`.
No change to any existing verb, flag, or output (`env` unchanged).

## Error Handling Strategy
Return codes, not exceptions (shell). All error text is emitted by the delegated function to `>&2`; `_cmd_resolve` never writes to stdout itself. The caller contract is: read stdout for the handle iff exit `0`; otherwise consult stderr + exit code. This mirrors `_cmd_env` and every other `_cmd_*` handler.

## Test Strategy
Unit tests at the CLI boundary using the existing `run()` harness and `orca`/`cmux` stubs (`HMAD_STUB_ORCA_STDOUT` / `HMAD_STUB_CMUX_STDOUT`), which is the same seam the current identity tests mock. No new fixtures beyond term-list envelopes already produced by `_orca_terms`/`_orca_terms_full`. Streams are captured separately (`r.stdout` vs `r.stderr`) to assert FR-3.

## Test Plan
Add to `h-mad/tests/test_hmad_dispatch.py`:
- `test_resolve_orca_prints_handle_only` — orca fixture with an `agy` pane + `ORCA_PANE_KEY`; `resolve agy` stdout == handle, no `->` prefix, exit 0 (AC-1.1, AC-1.2, FR-2 resolved).
- `test_resolve_honors_pin` — `HMAD_ORCA_CODEX_TERMINAL=t-x`; `resolve codex` stdout == `t-x`, exit 0 (AC-1.3).
- `test_resolve_unresolved_empty_stdout_diag_stderr` — 0-match fixture; stdout empty, stderr contains `pin HMAD_ORCA_AGY_TERMINAL`, exit 1 (AC-2.2, AC-3.1).
- `test_resolve_unknown_agent_exit2` — `resolve bogus`; stdout empty, stderr non-empty, exit 2 (AC-2.3, AC-3.2, AC-4.2).
- `test_resolve_missing_agent_exit2` — `resolve` (no arg); stdout empty, exit 2 (AC-4.3).
- `test_resolve_parity_with_env` — one fixture; assert the handle from `resolve agy` equals the handle parsed from `env`'s `agy -> <H>` line (AC-5.1); and an UNRESOLVED fixture gives empty stdout + non-zero (AC-5.2).
- `test_resolve_registered_verb` — `resolve` is routed (not the `unknown verb` branch); a genuinely unknown verb still exits 2 (AC-6.1, AC-6.3).

Verification command: `python3 -m pytest h-mad/tests/test_hmad_dispatch.py -q` then the full `handoff/scripts/test_handoff_paths.py h-mad/tests/` suite.

## Invariant Compliance
- **Single-source contract (base)**: complies — `_cmd_resolve` delegates 100% of resolution AND agent-validation to `_resolve_target`; it holds no second copy of the `codex|agy` list (the exact v1-audit fix).
- **Audit-gate signal discipline (base)**: N/A — no change to gate/exit semantics of any script the gate parses.
- **No-plugin-dependency (base)**: complies — change is internal to the `h-mad` skill; no other skill referenced.
- **Doc-template superset compliance (base)**: complies — this design uses the full Phase-4 template.
- **Backward-compatibility (base)**: complies — purely additive verb; no existing verb/output altered; the `*)` unknown-verb branch is untouched.
- **Marker discipline (base)**: N/A — `_cmd_resolve` emits no `[H-MAD]` markers (it is a lookup, not a phase step).
- **Skill self-containment (project)**: complies — no path outside the `h-mad` skill dir; no cross-skill import.
- **Skill manifest integrity (project)**: complies — `hmad-dispatch`'s documented verb surface (`# Verbs:` comment + `references/agent-substrate.md`) is updated in lockstep with the new entry behavior, so the contract is not silently changed. `h-mad/SKILL.md` frontmatter is unaffected (no entry-behavior change to the skill itself).

## Version History
- v1.0: Initial design draft.
