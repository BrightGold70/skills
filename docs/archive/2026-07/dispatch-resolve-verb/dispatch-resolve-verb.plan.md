# Plan: dispatch-resolve-verb

## Executive Summary
Add a `resolve <agent>` verb to `hmad-dispatch.sh` that delegates to the existing `_resolve_target` and surfaces its handle/exit-code/stderr contract directly, with a thin `codex|agy` argument guard.

## Overview
`_resolve_target` already computes single-agent resolution (pins → auto-detect → 0/1/2 with stderr diagnostics), but the only surface that exposes it is `env`, which always prints both agents in a human block. This adds a first-class, scriptable single-agent lookup that reuses that function verbatim, so `env` and `resolve` cannot diverge.

## Scope
A new CLI verb in `h-mad/scripts/hmad-dispatch.sh` and its coverage in `h-mad/tests/test_hmad_dispatch.py`. No resolution logic is added; no existing verb or output changes. Both `orca` and `cmux` substrates plus the no-pane global fallback are covered by reusing `_resolve_target`.

## Goals
- Provide `hmad-dispatch resolve <agent>` printing the handle on stdout (FR-1).
- Propagate `_resolve_target`'s 0/1/2 exit contract (FR-2).
- Keep stdout clean on failure; diagnostics to stderr (FR-3).
- Validate the agent token to `codex|agy`, incl. the missing-arg case (FR-4).
- Guarantee resolution parity with `env` by shared delegation (FR-5).
- Register the verb in the dispatch table and `# Verbs:` comment (FR-6).

## Requirements
- FR-1 single-agent resolve to handle on stdout
- FR-2 exit codes 0/1/2 mirror `_resolve_target`
- FR-3 stream discipline (stdout empty on failure, stderr diagnostic)
- FR-4 argument validation (`codex|agy`, missing → usage error)
- FR-5 parity with `env`
- FR-6 verb registration

## Implementation Strategy
- Add a `_cmd_resolve` handler that is a **pure forwarder**: `local agent="${1:-}"; _resolve_target "$agent"` and return its status. It does **not** re-implement the `codex|agy` allowlist — `_resolve_target` already owns the single valid-agent list. `_resolve_target` echoes the handle on stdout and returns `0` (resolved), its `_orca_find`/`_cmux_find` helpers emit the UNRESOLVED diagnostic to stderr and return `1`, and its own `*)` branch handles both an **unknown** token and an **empty** token (an empty `$1` yields the `<substrate>:` key which matches no case → `*)` → stderr "unknown agent" + return `2`). So the handler adds no resolution logic, no diagnostic logic, and no argument allowlist — it only defaults `$1` to empty (so `set -u`, if in effect, cannot trip on a missing arg) and delegates.
- Register `resolve) _cmd_resolve "$@" ;;` in the `main` dispatch `case`, adjacent to `env)`.
- Add `resolve` to the top-of-file `# Verbs:` comment.
- Follow the existing handler conventions (`_cmd_*` naming, `local`-scoped vars, bare `return <code>`), mirroring `_cmd_env`.

## Architecture Considerations
- **Single source of contract (validation included)**: the verb must call `_resolve_target`, never `_orca_find`/`_cmux_find` directly, AND must not maintain its own copy of the valid-agent list — both the resolution and the unknown-agent rejection live in exactly one place. This is what makes FR-5 parity structural and satisfies the Single-source invariant flagged in the v1 audit. `_resolve_target` already branches on substrate, honors pins, and rejects unknown/empty agents.
- **Exit-code fidelity**: `0`/`1`/`2` are `_resolve_target`'s own returns, forwarded unchanged. FR-4.2 (unknown token) and FR-4.3 (missing arg) are both satisfied by `_resolve_target`'s `*)` branch — no duplicated guard, no divergent second list to drift.
- **No stdout contamination**: only `_resolve_target`'s success `printf` reaches stdout; every diagnostic (`_orca_find`/`_cmux_find`/`*)`) already writes to `>&2`.
- **Additive**: the wrapper's `*)` unknown-**verb** branch is untouched, preserving FR-6.3.

## Deliverables
| Deliverable | Type | Satisfies |
|---|---|---|
| `_cmd_resolve` handler (pure forwarder to `_resolve_target`) | shell function | FR-1, FR-2, FR-3, FR-4 |
| `resolve)` dispatch-table entry | CLI verb wiring | FR-6.1 |
| `# Verbs:` comment update | doc/comment | FR-6.2 |
| `resolve` tests (resolve/unresolved/unknown/missing/pin/parity) | pytest cases | FR-1..FR-6 ACs |

## Risks and Mitigation
| Risk | Impact | Mitigation |
|---|---|---|
| Handler re-implements the `codex\|agy` allowlist, duplicating `_resolve_target` (v1-audit must-fix) | Med | Handler is a pure forwarder — no second agent list; `_resolve_target`'s `*)` branch is the sole rejector. FR-4.2/4.3 tests assert exit 2 flows through it. |
| Handler calls `_orca_find`/`_cmux_find` directly, drifting from `env` | Med | Plan mandates delegation to `_resolve_target`; FR-5 parity test asserts `resolve` handle == `env`'s line for the same fixture. |
| Diagnostic leaks to stdout, breaking scriptability | Low | Only `_resolve_target`'s success `printf` hits stdout; its failure/`*)` paths are stderr-only; tests capture stdout/stderr separately. |

## Convention Prerequisites
- Branch `feature/NNN-dispatch-resolve-verb` off `main` at Phase 5c.
- Python env with pytest for the suite (`/opt/anaconda3/bin` per project note).
- No new dependencies.

## Success Criteria
- All spec ACs (FR-1..FR-6) pass automated tests in `test_hmad_dispatch.py`.
- Full h-mad + handoff suite green, no regressions.
- Live `hmad-dispatch resolve codex` / `resolve agy` return the same handles `env` reports.

## Out-of-Scope (confirmed from spec)
- No `--json` output surface.
- No reimplementation of `_orca_find`/`_cmux_find`.
- No change to `env`'s output format.
- No multi-agent form (`resolve codex agy`).

## Next Steps
User approves plan v1.0 → run the Phase-3 audit cycle (agy audit → gate) until must-fix=0 AND should-fix=0 → Phase 4 design.

## Version History
- v1.0: Initial plan draft.
- v1.1: Audit cycle 1 (must-fix). Removed the explicit `codex|agy` re-validation guard from `_cmd_resolve` — it duplicated `_resolve_target`'s unknown-agent list (Single-source violation). Handler is now a pure forwarder; `_resolve_target`'s `*)` branch rejects both unknown and empty tokens with exit 2. Risks/architecture/deliverable updated accordingly. Spec unchanged (all FR-4 ACs still satisfied via delegation).
