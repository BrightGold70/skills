# Plan: preflight-read-enforcement

## Executive Summary

Add a fingerprinted preflight receipt written by `hmad-dispatch env` on PASS and required by
`hmad-dispatch send`, plus an agent-conflict guard at dispatch, so a passing preflight against the
current handle set becomes a precondition of dispatching rather than an instruction an orchestrator
may skip.

## Overview

Wave 2 shipped a canonical `PREFLIGHT: PASS|FAIL` token and mandated in `SKILL.md` that the
orchestrator assert it before dispatching. The mandate has no enforcement: the orchestrator is an
LLM reading prose, `env` exits 0 on both verdicts by design, and so `hmad-dispatch env && send …`
remains a non-guard. This is the Wave-2 report's own carry item and was independently confirmed a
real residue by the 6a-prime reviewer. It matters now because the failure it protects against is not
hypothetical — a dispatch has been observed reporting `Sent 7293 bytes` into a rotated handle and
vanishing with no error, no report file, and no work done.

## Scope

In scope: the `hmad-dispatch` wrapper's preflight and dispatch paths, the receipt artifact and its
lifecycle, the two new environment overrides, the wrapper's test suite, and the `SKILL.md` /
`references/agent-substrate.md` prose that currently describes a mandated read.

User-visible behavior: `env` gains a side effect (receipt write/removal) but its stdout contract is
unchanged and additive-only. `send` gains refusal modes, each with a distinct stderr reason and a
documented recovery. No other verb changes behavior.

## Goals

- Make a passing, current preflight a mechanical precondition of dispatch — FR-1, FR-2, FR-3
- Ensure the receipt cannot outlive the handle set it attests to — FR-4, FR-5
- Preserve operator control and existing test independence — FR-6, FR-8
- Close the agent-conflict case that `env` detects but `send` cannot see — FR-7
- Leave the documentation describing the machinery that now exists, not a superseded obligation — FR-9

## Requirements

- FR-1: `env` emits a receipt on a passing preflight
- FR-2: A failing preflight leaves no usable receipt
- FR-3: Dispatch fails closed without a valid receipt
- FR-4: Fingerprint mismatch invalidates a receipt (rotation detection)
- FR-5: Receipt freshness window
- FR-6: Documented operator opt-out
- FR-7: Agent-conflict guard at dispatch
- FR-8: Receipt path override for isolation
- FR-9: Documentation states machinery, not protocol

## Implementation Strategy

Change one layer only: the `hmad-dispatch` shell wrapper. No Python helper, no new script, no change
to the audit gate, the assembler, or state handling. The feature is small enough that a new file
would add a cross-file contract without buying anything, and `hmad-dispatch.sh` already owns every
input needed — substrate detection, agent resolution, and liveness.

Follow the patterns the wrapper already establishes rather than inventing parallel ones:

- **Override-by-environment with a file default**, exactly as `_pin_file` does at
  `hmad-dispatch.sh:91-92`. This is what makes FR-8's isolation a one-line concern instead of a
  refactor, and it is the shape the J7 fix already proved out.
- **Refuse on positive evidence only.** The existing `_orca_handle_live` three-way contract
  (0 live / 1 provably absent / 2 unknown) exists because a pin must keep working when the listing
  cannot be read. Receipt validation must inherit that stance: an unreadable listing is not evidence
  of rotation and must not invalidate a receipt.
- **Refusal shape mirrors `terminal_handle_stale`** (`hmad-dispatch.sh:757-759`): stderr diagnostic
  naming the condition and the recovery, non-zero return, nothing sent.

Deliberately not touched: `_cmd_env`'s stdout lines and their ordering; the `PREFLIGHT:` token
grammar; `send`'s size-based inline-vs-indirection selection; the exit-0-on-verdict rule for every
gate. The `ASSEMBLE:` mandated read is out of scope this pass.

## Architecture Considerations

- **Enforcement point.** `_send_text` is shared plumbing used by `clear` and `interrupt` as well as
  by dispatch. Placing the receipt requirement there would make it impossible to clear a wedged pane
  without first running a preflight — obstructing the documented recovery path. The requirement
  therefore belongs at the dispatch verb, while the conflict guard's correct altitude is a separate
  question the design must answer rather than assume.
- **Signal discipline boundary.** `invariants.base.md` reserves non-zero exits for operational
  errors on *gates whose verdict the orchestrator consumes*. `env` remains such a gate and keeps
  exit 0 on both verdicts. A refused dispatch is an operation declining to act — the same category
  as the existing stale-handle refusal — so non-zero is correct there and no requirement may be met
  by changing `env`'s exit status.
- **Fingerprint domain.** The fingerprint must cover both agents including unresolved ones, so that
  pinning a previously-unresolved agent invalidates the receipt. This is what makes the mechanism
  agree with `SKILL.md`'s existing "re-assert after any re-pin" instruction instead of quietly
  contradicting it.
- **Substrate applicability.** The `PREFLIGHT:` token is emitted under both cmux and orca, but the
  rotation and conflict hazards are orca-specific. Whether enforcement applies under cmux is a real
  fork with a compatibility consequence for cmux users, and the design must state and justify a
  choice rather than let it fall out of the implementation.
- **Test-suite coupling.** The suite is 530 tests and many exercise `send`. A fail-closed default
  will break them unless the receipt path is isolated per invocation. This is the J7 failure mode
  recurring in a new place; the mitigation is known and must be applied deliberately, and the
  independence must be *measured*, not assumed from a green run.

## Deliverables

| Deliverable | Type | Satisfies |
|---|---|---|
| Receipt write on passing preflight | CLI behavior (`env`) | FR-1 |
| Receipt removal/withholding on failing preflight | CLI behavior (`env`) | FR-2 |
| Receipt requirement at dispatch, fail-closed | CLI behavior (`send`) | FR-3 |
| Fingerprint computation + match check | internal function | FR-1, FR-4 |
| Freshness window + configuration variable | CLI behavior + env var | FR-5 |
| `HMAD_SKIP_PREFLIGHT` bypass with stderr notice | env var | FR-6 |
| Agent-conflict refusal at dispatch | CLI behavior (`send`) | FR-7 |
| Receipt path override variable | env var | FR-8 |
| Test-suite isolation for the receipt path | test harness | FR-8 |
| `SKILL.md` Phase-5 preflight section update | docs | FR-9 |
| `references/agent-substrate.md` receipt documentation | docs | FR-9 |

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| Fail-closed default breaks a large share of the 530-test suite | High — blocks the whole feature at 5f | Isolate the receipt path per invocation as J7 did for pins; measure suite counts with and without a receipt at the default path rather than inferring independence from one green run |
| The opt-out becomes the de facto production path | High — silently restores the status quo | Enforce that the *unset* default refuses, as an explicit AC; emit a stderr notice on every bypass so its use is visible in logs |
| An unreadable terminal listing is treated as rotation | Medium — breaks the deliberate "pin works when listing does not" behavior | Inherit `_orca_handle_live`'s three-way contract; only positive evidence of a changed handle invalidates |
| Enforcement placed on shared plumbing blocks recovery verbs | Medium — cannot clear a wedged pane | Fix the enforcement altitude in design; `clear`/`interrupt` are explicitly not dispatches |
| Guards written so they pass vacuously | Medium — ships an unenforced feature behind green tests | Every guard carries a negative-case AC asserting it does *not* fire when it should not; assert the refusal path exists before asserting what it lacks |
| Conflict guard misfires on a legitimate cmux surface arrangement | Low | Require two equal, non-empty resolved values; settle cmux applicability in design |
| Scope drifts into the audit assembler | Medium — invalidates the dogfood measurement | `ASSEMBLE:` enforcement held out of scope and recorded as such in the spec |

## Convention Prerequisites

- Feature branch `feature/NNN-preflight-read-enforcement` cut at Phase 5c from current `main`.
- Base Axis B invariants apply: audit-gate signal discipline, single-source contract, backward
  compatibility, operator-override preservation, marker discipline.
- Project Axis B applies: skill self-containment (no cross-skill imports, no hardcoded paths outside
  the skill directory) and skill manifest integrity (`SKILL.md` frontmatter stays valid).
- Tests run under an interpreter with `jsonschema` available (`/opt/anaconda3/bin/python3`).

## Success Criteria

- All 37 ACs in the spec pass automated tests, except AC-8.3 which is verified by measurement and
  reported as such
- Full suite green with zero regressions against the 530-test pre-feature baseline
- Suite pass/fail counts identical with and without a receipt present at the default path
- A dispatch attempted with no preflight is refused with nothing sent, demonstrated live
- A dispatch attempted after a handle rotation is refused with `preflight_handles_rotated`,
  demonstrated against a rotation rather than only a synthesized receipt
- Phase 6a-prime returns `READY_TO_MERGE`

## Out-of-Scope (confirmed from spec)

- Wave 2's FR-5 — the `ASSEMBLE: PASS` mandated read
- Making any gate exit non-zero
- `stablyai/orca#9870` — per-terminal identity, blocked upstream; this feature mitigates the
  consequences of misresolution, not resolution itself
- A test asserting AC-8.3, which cannot honestly be asserted from inside the suite it describes
- Enforcement on the `clear` / `interrupt` recovery verbs

## Next Steps

Plan v1.0 approval, then the Phase-3 audit cycle: assemble via `h_mad_assemble_audit.py --phase
plan`, assert `ASSEMBLE: PASS`, dispatch to agy, run `h_mad_audit_gate.py`, and cycle until both
must-fix and should-fix reach zero.

## Version History
- v1.0: Initial plan draft.
