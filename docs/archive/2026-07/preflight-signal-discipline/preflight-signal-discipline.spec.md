# Spec: preflight-signal-discipline

## Executive Summary

`hmad-dispatch env` gains a canonical `PREFLIGHT: PASS|FAIL` stdout token (exit 0 on both verdicts),
`SKILL.md` mandates reading that token and `ASSEMBLE:` before the dispatches they guard, and the
session pin file stops leaking into the test suite — so the two conditions that silently destroy a
dispatch become consumable rather than advisory.

## Goal

Make a stale pin or a codex/agy handle collision stop a Phase-5 run at its preflight step instead of
printing a line nothing is required to read.

## Functional Requirements

### FR-1: `env` emits a canonical preflight verdict token

- **Description**: `_cmd_env` prints exactly one `PREFLIGHT:` line as the final line of its stdout,
  matching the `GATE:` / `ASSEMBLE:` / `STATE:` token shape already used elsewhere in the skill.
- **Acceptance Criteria**:
  - AC-1.1: With no stale pin and no conflict, `hmad-dispatch env` stdout contains a line matching
    `^PREFLIGHT: PASS$`.
  - AC-1.2: When at least one agent resolves to a handle absent from `orca terminal list`, stdout
    contains a line beginning `PREFLIGHT: FAIL` and naming the offending agent(s) via `stale=<a>[,<b>]`.
  - AC-1.3: When codex and agy resolve to the same handle, stdout contains a line beginning
    `PREFLIGHT: FAIL` and containing `conflict=<handle>`.
  - AC-1.4: When both conditions hold simultaneously, the single `PREFLIGHT: FAIL` line reports both
    `stale=` and `conflict=`.
  - AC-1.5: The `PREFLIGHT:` line is the **last** line of stdout, appended after the existing
    `orchestration:` line; no pre-existing output line is reordered, reworded, or removed.
  - AC-1.6: Exactly one `PREFLIGHT:` line is emitted per invocation.

### FR-2: The verdict never changes the exit code

- **Description**: The token is the signal; the exit status stays 0 for any verdict, per the base
  invariant on audit-gate signal discipline (`invariants.base.md` §"Audit-gate signal discipline").
- **Acceptance Criteria**:
  - AC-2.1: `hmad-dispatch env` exits 0 when the verdict is `PREFLIGHT: PASS`.
  - AC-2.2: `hmad-dispatch env` exits 0 when the verdict is `PREFLIGHT: FAIL`.
  - AC-2.3: `env` continues to exit non-zero **only** for the pre-existing operational error of no
    detectable substrate, and emits no `PREFLIGHT:` line in that case.
  - AC-2.4: A comment at the token site in `hmad-dispatch.sh` states that a FAIL must not become a
    non-zero exit, and names the reason (`PostToolUseFailure` leaking into coexisting plugins).

### FR-3: `UNRESOLVED` is informational, not a failure

- **Description**: An unpinned agent is the ordinary state of a session that is not dispatching, so
  it must not raise `FAIL`; dispatch-readiness remains `pin-agents`' job.
- **Acceptance Criteria**:
  - AC-3.1: With one or both agents `UNRESOLVED` and no stale handle and no conflict, the verdict is
    `PREFLIGHT: PASS`.
  - AC-3.2: The `<agent> -> UNRESOLVED` lines are still printed unchanged.
  - AC-3.3: A `PREFLIGHT: FAIL` line never contains an `unresolved=` field.

### FR-4: Phase-5 preflight mandates reading the token

- **Description**: `SKILL.md`'s Phase-5 substrate preflight requires the orchestrator to assert
  `PREFLIGHT: PASS` before the first dispatch of a run, and to re-assert after any re-pin.
- **Acceptance Criteria**:
  - AC-4.1: `h-mad/SKILL.md` §"Phase 5 (Implementation) sub-steps" instructs asserting
    `PREFLIGHT: PASS` before the first `send` of a run.
  - AC-4.2: The same section states the re-assert-after-re-pin requirement.
  - AC-4.3: The section names the halt taken on `PREFLIGHT: FAIL` (`<phase>:preflight_failed`).
  - AC-4.4: The instruction states that the verdict is read from the **token**, not from `$?`.

### FR-5: Audit assembly mandates reading `ASSEMBLE:`

- **Description**: `ASSEMBLE:` already complies with the token shape; it gains the same mandated
  read so one convention lands once.
- **Acceptance Criteria**:
  - AC-5.1: `h-mad/SKILL.md` §"Audit prompt assembly" requires asserting `ASSEMBLE: PASS` before
    dispatching an assembled prompt.
  - AC-5.2: That instruction states `ASSEMBLE: HALT` is a verdict to act on, not a tool failure, and
    that the exit code is 0 either way.

### FR-6: The session pin file cannot leak into the test suite (J7)

- **Description**: `test_hmad_dispatch.py::run()` isolates `HMAD_ORCA_PIN_FILE` the way F13
  isolated the `HMAD_ORCA_*` env vars, so pinning agents and running the suite stop being mutually
  exclusive.
- **Acceptance Criteria**:
  - AC-6.1: With a populated `.h-mad/orca-pins.env` present in the repo working directory, the full
    `h-mad/tests/` suite passes with zero failures.
  - AC-6.2: The suite result is byte-identical in pass/fail counts whether that pin file is present
    or absent.
  - AC-6.3: A test that explicitly passes `HMAD_ORCA_PIN_FILE` in its `env` still receives its own
    value — the harness default must not override an explicit one.
  - AC-6.4: The harness-supplied default points outside the repository working tree.
  - AC-6.5: `_pin_file()` continues to honour `HMAD_ORCA_PIN_FILE` and continues to default to
    `.h-mad/orca-pins.env`; production resolution behaviour is unchanged.

### FR-7: The automation precheck can gate on the verdict

- **Description**: `references/orchestration-mode.md` documents an Orca automation precheck of
  `hmad-dispatch env`, which gates on exit code and therefore cannot fail on a stale pin. It is
  updated to gate on the token.
- **Acceptance Criteria**:
  - AC-7.1: `references/orchestration-mode.md` shows the precheck as a form that tests for
    `PREFLIGHT: PASS` rather than bare `hmad-dispatch env`.
  - AC-7.2: `references/agent-substrate.md`'s `env` row documents the `PREFLIGHT:` token.

## Non-Functional Requirements

- **Performance**: N/A. `env` already calls `orca terminal list` for its liveness check; the token
  adds no new subprocess.
- **Security**: N/A.
- **Compatibility**: The `PREFLIGHT:` line is appended, so existing readers of `substrate:`,
  `<agent> -> <handle>`, `stale pins:`, `CONFLICT:` and `orchestration:` are unaffected. 38 existing
  tests invoke `run(["env"])` and must continue to pass unmodified except where they assert the new
  token. `env` under `substrate: cmux` keeps its current behaviour and emits `PREFLIGHT: PASS` when
  nothing is wrong (the liveness check is Orca-only).

## Out-of-Scope

- Changing `env`'s exit code under any circumstance — explicitly forbidden by the base invariant and
  the central trap of this feature.
- Making `UNRESOLVED` a failure condition, or adding a `--require-agents` strict mode.
- Moving the production pin file out of the repository, or changing `_pin_file()`'s default.
- J1 (`launch` mis-captures the handle), J8 (`elapsed_min` ≈ 56 years), J9 (flaky
  `test_alive_cmux_true`) — filed separately, untouched here.
- Enforcing the mandated reads mechanically. This wave makes them protocol; Wave 3's dogfood run is
  what exercises them. The gap is recorded, not closed.
- Any change to `h_mad_assemble_audit.py`'s behaviour; FR-5 is a documentation mandate only.

## Assumptions

- The verdict answers "is anything wrong", not "am I ready to dispatch" — `pin-agents` already fails
  loud (rc=1) on an unresolved agent and remains the dispatch-readiness gate.
- `_orca_handle_live()` remains the single liveness oracle; the token reports what `env` already
  computes rather than performing its own detection.
- Only positive evidence of death counts: when `orca terminal list` is unreadable, a handle is not
  treated as stale, so an unreadable listing yields `PASS` rather than a spurious `FAIL`.
- The 17 reproduced failures are entirely pin-file leakage; no other cause is hiding behind them.
  Verified by the absent/present A-B measurement, to be re-verified at Phase 6.

## Version History
- v1.0: Initial specification draft.
