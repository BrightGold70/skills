# Plan: preflight-signal-discipline

## Executive Summary

Append a canonical `PREFLIGHT: PASS|FAIL` verdict to `hmad-dispatch env` without touching its exit
code, mandate reading that token (and `ASSEMBLE:`) at the dispatch gates they guard, and isolate the
session pin file inside the test harness — turning two already-detected, currently-advisory failure
conditions into ones an orchestrator must act on.

## Overview

`env` already knows when a pin is stale or when codex and agy have collided onto one pane; it just
says so in prose that nothing is required to read. That gap has a measured cost: a Task-2 RED
dispatch on HemaSuite reported `Sent 7293 bytes` into a rotated handle and vanished — no error, no
report, no tests. Folded in is J7, the same defect one layer down: the pin file the Phase-5 preflight
*requires* leaks into the suite the Phase-5f gate *requires*, so following the protocol produces a
red suite in the repo that owns those tests. This matters now because Wave 3 is a dogfood `/h-mad`
run, and it should exercise mandated reads that exist.

## Scope

In scope: `_cmd_env`'s stdout contract in `h-mad/scripts/hmad-dispatch.sh`; the Phase-5 preflight and
audit-assembly sections of `h-mad/SKILL.md`; the `env` documentation rows in
`h-mad/references/agent-substrate.md` and the automation precheck example in
`h-mad/references/orchestration-mode.md`; the environment isolation performed by
`run()` in `h-mad/tests/test_hmad_dispatch.py`.

User-visible behaviour: one additional final line on `env` stdout, and a suite that passes whether
or not agents are pinned. No exit code changes anywhere.

## Goals

- Give `env` a machine-readable verdict that distinguishes "something is wrong" from "not set up" — FR-1, FR-3
- Keep the verdict a *token*, never an exit status — FR-2
- Make the reads that guard dispatch mandatory in protocol — FR-4, FR-5
- Stop pinning and testing from being mutually exclusive — FR-6
- Give the Orca automation precheck a form that can actually fail — FR-7

## Requirements

- FR-1: `env` emits a canonical `PREFLIGHT:` token, appended last, naming `stale=` / `conflict=`
- FR-2: The verdict never changes the exit code; exit 0 on PASS and FAIL alike
- FR-3: `UNRESOLVED` is informational and never raises FAIL
- FR-4: Phase-5 preflight mandates asserting `PREFLIGHT: PASS`
- FR-5: Audit assembly mandates asserting `ASSEMBLE: PASS`
- FR-6: The session pin file cannot leak into the test suite (J7)
- FR-7: The automation precheck and substrate docs gate on the token

## Implementation Strategy

**Report what `env` already computes; do not re-detect.** `_cmd_env` currently accumulates `$stale`
and derives the conflict from `$seen_codex` / `$seen_agy`. The verdict is a function of those two
existing values, so the change is a terminal emission, not a second detection path. This keeps
`_orca_handle_live()` the single liveness oracle and prevents the token and the prose lines from ever
disagreeing — the "single-source contract" base invariant applied to a signal rather than a rule.

**Append, never restructure.** 38 tests invoke `run(["env"])` and read its lines. The token is added
after the existing `orchestration:` line; no existing line is reordered or reworded, so every current
assertion holds unchanged.

**Encode the prohibition where it will be violated.** The obvious "improvement" to a weak signal is
to make it exit non-zero. That is a base-invariant violation whose consequence (a `PostToolUseFailure`
leaking into coexisting plugins' error handling) is invisible from the call site. The comment stating
it belongs at the token site in the shell script, not only in `SKILL.md`, and a test must assert exit
0 on a FAIL verdict so the invariant is enforced rather than described.

**Close J7 at the boundary that leaked, mirroring F13.** F13 stripped `HMAD_ORCA_*` from `run()`'s
environment; the pin file is the second channel into the same function, reached through a
cwd-relative default rather than an env var. The fix belongs in the same place: `run()` supplies a
tmp-path default via `setdefault` semantics, so tests that pass their own value keep it and tests
that pass none can no longer reach the repo. `_pin_file()` itself is untouched — production
resolution and its documented default stay exactly as they are.

**What we deliberately do not touch**: `_pin_file()`, `h_mad_assemble_audit.py` (FR-5 is a
documentation mandate over an already-compliant token), `pin-agents`' rc=1 dispatch-readiness
contract, and the exit code of anything.

## Architecture Considerations

- **The signal-discipline invariant is the binding constraint.** `invariants.base.md`
  §"Audit-gate signal discipline" requires stdout-token + exit-0 for any verdict an orchestrator
  consumes, reserving non-zero for genuine operational errors. `env`'s existing non-zero on
  "no substrate detected" is exactly that permitted case and stays.
- **Token-shape consistency is the point.** `GATE:`, `ASSEMBLE:`, `STATE:`, `PHASE7:` and
  `STALENESS:` already exist. `PREFLIGHT:` joins a family, which is what lets one mandated-read
  convention cover it and `ASSEMBLE:` together rather than growing two idioms.
- **Two different questions must stay separate.** "Is anything wrong" (this token) and "am I ready to
  dispatch to both agents" (`pin-agents`, rc=1) have different right answers in the same session.
  Merging them would make `env` report FAIL in every ordinary session and earn the token the same
  ignore the STALE line already suffers.
- **Only positive evidence blocks.** `_orca_handle_live()` is three-valued — live / provably absent /
  unreadable-listing. An unreadable listing must yield PASS, otherwise a transient Orca hiccup halts
  a run that would have been fine, and the pin's whole value is surviving exactly that.
- **A doc-level mandate is not enforcement.** FR-4/FR-5 make the reads protocol; nothing in this wave
  makes an orchestrator perform them. That residue is deliberate and belongs in the report as a carry
  item, not papered over.

## Deliverables

| Deliverable | Type | Satisfies |
|---|---|---|
| `PREFLIGHT:` verdict emission in `_cmd_env` | shell function change | FR-1, FR-2, FR-3 |
| Prohibition comment at the token site | code comment | FR-2 (AC-2.4) |
| Phase-5 preflight mandated-read step | SKILL.md section | FR-4 |
| Audit-assembly mandated-read step | SKILL.md section | FR-5 |
| `HMAD_ORCA_PIN_FILE` isolation in `run()` | test-harness change | FR-6 |
| Token-aware automation precheck example | orchestration-mode.md | FR-7 (AC-7.1) |
| `env` row documenting the token | agent-substrate.md | FR-7 (AC-7.2) |
| Regression tests for all seven FRs | pytest | all |

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| A later change makes FAIL exit non-zero | Reintroduces the `PostToolUseFailure` leak the invariant exists to prevent | Comment at the token site naming the reason (AC-2.4) **plus** a test asserting exit 0 on FAIL (AC-2.2) |
| The token reads FAIL routinely and gets skimmed | The new signal inherits the old signal's fate | FAIL only on STALE/CONFLICT; `UNRESOLVED` explicitly excluded (FR-3, AC-3.3) |
| Harness default masks a test that meant to read a real pin file | A pinning test silently stops testing pinning | `setdefault` semantics preserve an explicit value; asserted directly (AC-6.3) |
| Appending a line breaks an unnoticed output consumer | Silent breakage of a caller | Grep established only one behavioural consumer (the automation precheck), which FR-7 updates; append-only placement (AC-1.5) keeps line-oriented readers valid |
| The 17 failures have a second cause hiding behind the leak | J7 declared closed while something remains | AC-6.2 demands pass/fail parity with the file present *and* absent, which a partial fix cannot satisfy |
| Mandated reads documented but never performed | The feature reads as solved while the gap persists | Recorded as an explicit carry; Wave 3's dogfood run is the exercise |

## Convention Prerequisites

- Branch `feature/NNN-preflight-signal-discipline` cut from `main` at Phase 5c.
- State scripts run under `/opt/anaconda3/bin/python3` (jsonschema present); `h_mad_telemetry.py` and
  `h_mad_cycle_counts.py` stay stdlib-only under bare `python3` (F8/J4).
- Agents identified by **content**, never title — two panes here share the tab title
  `Codex - skills repo`; the real Codex shows `gpt-5.6-*` in its status line (H5 / Orca #9870).
- Until FR-6 lands, keep `.h-mad/orca-pins.env` absent while running the suite and pass
  `HMAD_ORCA_CODEX_TERMINAL` / `HMAD_ORCA_AGY_TERMINAL` as env vars instead (J7 workaround).

## Success Criteria

- All 26 ACs pass automated tests
- `h-mad/tests/` passes with **identical** counts whether `.h-mad/orca-pins.env` is present or absent
  — the measured baseline to beat is 17 failed / 136 passed with it present
- `hmad-dispatch env` exits 0 in every verdict path, verified by test, not by inspection
- No pre-existing line of `env` output changes; the 38 existing `run(["env"])` call sites pass
  unmodified except those extended to assert the token

## Out-of-Scope (confirmed from spec)

- Changing `env`'s exit code under any circumstance
- Making `UNRESOLVED` a failure, or adding a `--require-agents` strict mode
- Moving the production pin file out of the repo, or changing `_pin_file()`'s default
- J1 (`launch` handle mis-capture), J8 (`elapsed_min` ≈ 56 years), J9 (flaky `test_alive_cmux_true`)
- Mechanically enforcing the mandated reads — protocol only this wave
- Any behavioural change to `h_mad_assemble_audit.py`

## Next Steps

User approves v1.0 → agy plan audit cycle (SKILL.md §"Audit prompt assembly") → Phase 4 design.

## Version History
- v1.0: Initial plan draft.
