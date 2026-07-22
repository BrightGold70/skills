# Spec: dispatch-resolve-verb

## Executive Summary
`hmad-dispatch resolve <agent>` resolves a single agent (`codex`|`agy`) to its concrete terminal/surface handle on stdout, exiting `0`/`1`/`2` per the same contract `_resolve_target` already implements.

## Goal
Give scripts a machine-readable, single-agent handle lookup that reuses the exact resolution `env` performs, without parsing `env`'s two-agent human block.

## Functional Requirements

### FR-1: Resolve a single agent to its handle
- **Description**: `hmad-dispatch resolve <agent>` invokes the existing resolution (`_resolve_target`) for the one named agent under the active substrate (orca or cmux), honoring env-var pins (`HMAD_ORCA_<A>_TERMINAL` / `HMAD_CMUX_<A>_SURFACE`) and auto-detect exactly as `env` does.
- **Acceptance Criteria**:
  - AC-1.1: When the agent resolves, the resolved handle/surface is printed to **stdout** as a single line and the command exits `0`.
  - AC-1.2: The stdout is the handle **only** — no `"<agent> -> "` prefix, no trailing prose, nothing else on stdout.
  - AC-1.3: An explicit pin (`HMAD_ORCA_CODEX_TERMINAL=t-x hmad-dispatch resolve codex`) prints that pinned value and exits `0`.

### FR-2: Exit-code contract mirrors `_resolve_target`
- **Description**: The verb propagates `_resolve_target`'s return contract unchanged.
- **Acceptance Criteria**:
  - AC-2.1: Resolved → exit `0`.
  - AC-2.2: Unresolved (no matching pane, or ambiguous n>1) → exit `1`.
  - AC-2.3: Unknown agent token → exit `2`.

### FR-3: Stream discipline on failure
- **Description**: Failures never contaminate stdout; the actionable diagnostic goes to stderr.
- **Acceptance Criteria**:
  - AC-3.1: On UNRESOLVED, **stdout is empty** and **stderr** carries the existing `_orca_find`/`_cmux_find` diagnostic (candidate count + `pin HMAD_ORCA_<A>_TERMINAL` hint).
  - AC-3.2: On unknown agent, **stdout is empty** and **stderr** carries an unknown-agent message.

### FR-4: Argument validation
- **Description**: The verb accepts exactly the known agents and rejects everything else before/at resolution.
- **Acceptance Criteria**:
  - AC-4.1: `resolve codex` and `resolve agy` are accepted (subject to resolution outcome).
  - AC-4.2: `resolve <other-token>` exits `2` with a stderr message and empty stdout.
  - AC-4.3: `resolve` with no agent argument exits `2` (usage error) with a stderr message and empty stdout.

### FR-5: Parity with `env`
- **Description**: `resolve <agent>` and `env` compute identical resolution — they call the same `_resolve_target`, so a resolved handle from one equals the other.
- **Acceptance Criteria**:
  - AC-5.1: For a fixture where `env` prints `<agent> -> <H>`, `resolve <agent>` prints exactly `<H>` on stdout.
  - AC-5.2: For a fixture where `env` prints `<agent> -> UNRESOLVED`, `resolve <agent>` prints nothing on stdout and exits non-zero.

### FR-6: Verb registration
- **Description**: `resolve` is a registered verb in the wrapper's dispatch table and its verb list/usage comment, consistent with existing verbs.
- **Acceptance Criteria**:
  - AC-6.1: The `main` case dispatch routes `resolve)` to the handler.
  - AC-6.2: The wrapper's top-of-file `# Verbs:` comment lists `resolve`.
  - AC-6.3: An unknown verb still yields the existing `unknown verb` error + exit 2 (no regression).

## Non-Functional Requirements
- Performance: N/A (one `orca terminal list` call, same as `env` per agent).
- Security: N/A (no new external input beyond the agent token, which is validated).
- Compatibility: Additive only. No existing verb, flag, or output changes. Works under both `orca` and `cmux` substrates and the no-pane global fallback.

## Out-of-Scope
- No `--json` output surface (single bare handle is the contract).
- No new resolution logic — `resolve` must not reimplement `_orca_find`/`_cmux_find`; it delegates to `_resolve_target`.
- No change to `env`'s output format.
- No multi-agent form (`resolve codex agy`) — one agent per call.

## Assumptions
- `_resolve_target` remains the single resolution entrypoint returning `0` (resolved, echoes handle), `1` (unresolved, stderr diagnostic), `2` (unknown agent, stderr message).
- The test harness stubs `orca`/`cmux` via `HMAD_STUB_*_STDOUT` (existing pattern in `test_hmad_dispatch.py`).

## Version History
- v1.0: Initial specification draft.
