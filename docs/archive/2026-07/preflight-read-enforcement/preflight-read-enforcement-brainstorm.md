# Brainstorm: preflight-read-enforcement

## Executive Summary

Convert the `PREFLIGHT:` token from an advisory signal into machinery: `env` writes a receipt when
it passes, `send` refuses to dispatch without a fresh matching one — and close the one hazard
`send` still cannot see, two agents resolving to a single **live** handle.

## Problem Statement

Wave 2 (`787aecf`) gave `hmad-dispatch env` a canonical `PREFLIGHT: PASS|FAIL` token and mandated in
`SKILL.md` that an orchestrator assert it before dispatching. Nothing enforces that mandate. The
orchestrator is an LLM reading markdown prose, so FR-4/FR-5 shipped as *protocol, not machinery* —
the Wave-2 report's own carry item, confirmed as a real residue by the 6a-prime reviewer. A scripted
`hmad-dispatch env && send …` still walks into a stale handle, because `env` exits 0 on both verdicts
by design (base invariant: audit-gate signal discipline reserves non-zero for operational errors).

Separately, `_send_text` (`h-mad/scripts/hmad-dispatch.sh:743-763`) guards exactly one failure:
a target handle the listing proves is gone (`terminal_handle_stale`, rc=1, nothing sent — `912b93a`).
It performs no cross-agent comparison, so the CONFLICT case `_cmd_env` detects at line 303-306
(codex and agy resolving to the same handle) is invisible at dispatch time. Both agents return a
well-formed sentinel report, so handing Codex's TDD work to agy is silent.

## Proposed Approach

**A preflight receipt, written by `env` on PASS and required by `send`.**

- `env`, on `PREFLIGHT: PASS`, writes a receipt recording the verdict, a **fingerprint of the
  resolved handle set** (codex + agy, including `UNRESOLVED` as a value), and a timestamp.
- `env`, on `PREFLIGHT: FAIL`, writes **no** receipt and removes any existing one — a failed
  preflight must not leave a usable token behind.
- `send` refuses (rc=1, nothing sent) unless a receipt exists, is within its freshness window, and
  its fingerprint still matches resolution *at send time*. Refusal reasons are distinct:
  `preflight_not_run`, `preflight_expired`, `preflight_handles_rotated`.
- Escape hatch `HMAD_SKIP_PREFLIGHT=1`, logged on use, for the wrapper's own tests and for a
  deliberate operator override.
- Independently, `_send_text` refuses when the target agent's handle equals the other agent's
  resolved handle (`preflight_agent_conflict`).

Why this over the alternatives: the fingerprint is what makes the receipt more than a rubber stamp.
A receipt cannot survive the exact failure this exists to catch — handles rotating between preflight
and dispatch — because rotation changes the fingerprint. It also preserves the operator-visible
preflight *step* rather than deleting it, which matters because the step is what a human reads.

Enforcement posture is **fail-closed with a documented opt-out**, matching the shape the codebase
already uses for a stale handle. A refusal that sends nothing is safe by construction.

Scope is deliberately **PREFLIGHT + CONFLICT only**. FR-5 (the `ASSEMBLE: PASS` mandated read) stays
protocol this pass — see Out-of-scope rationale under Risks.

## Alternatives Considered

- **`send` self-checks, no receipt**: move stale+conflict detection inline into `_send_text` so every
  dispatch validates itself — rejected as the *primary* mechanism because it makes the mandated read
  redundant rather than enforced. The FR-4/FR-5 carry would be closed by obsolescence, and the
  operator-facing preflight step would remain advisory, which is the exact status quo being fixed.
  (The conflict half of this idea is adopted anyway, as FR-2.)
- **Receipt + full inline re-verification on every send**: strongest guarantee, rejected on cost —
  roughly doubles the terminal-listing calls per dispatch and doubles the surface under test, to
  close only the narrow receipt→send window. The fingerprint check already re-resolves, which covers
  most of that window at a fraction of the cost.
- **Warn first, fail closed in a later release**: rejected because an unread warning is precisely the
  failure mode Wave 2 diagnosed. Shipping one here would reproduce the defect the feature exists to
  eliminate, and the deferred flip may never happen.
- **Fail closed with no opt-out**: rejected as inconsistent with an existing deliberate decision —
  `_orca_handle_live` returns 2 for an unreadable listing and the send still proceeds, because a pin
  must keep working when the listing cannot be read. An absolute requirement also makes the wrapper's
  own 530-test suite awkward for no safety gain.
- **Making `PREFLIGHT: FAIL` exit non-zero**: forbidden outright by `invariants.base.md`
  §"Audit-gate signal discipline" — a non-zero exit registers as a Claude Code `PostToolUseFailure`
  and leaks into coexisting plugins. Signals are strengthened by mandated reads, never by `$?`.

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| The 530-test suite breaks en masse — many tests exercise `send` with no preflight | H | Mirror the J7 fix: a `HMAD_PREFLIGHT_RECEIPT_FILE` override, defaulting to a per-invocation path in tests, so pinning and testing stay independent. Measure pass/fail counts with and without a receipt present. |
| The opt-out silently becomes the production path | M | Log every `HMAD_SKIP_PREFLIGHT` use to stderr; assert in tests that the unset default refuses. A green suite proves nothing if the escape hatch is globally exported — check the default explicitly. |
| Receipt becomes a rubber stamp (run `env`, ignore the token, dispatch anyway) | M | A receipt is written **only** on PASS, so an ignored FAIL leaves no receipt and the send refuses. The token cannot be bypassed by not reading it. |
| Freshness window mis-tuned — too long is a stamp, too short is friction | M | The fingerprint, not the TTL, is the real guard; the TTL is a backstop. Make it configurable and pick a default from measured run lengths (the Wave-2 run took 110 min end to end). |
| CONFLICT guard fires on a legitimate cmux setup where both agents share a surface | L | Gate the conflict check on the resolved values genuinely being equal AND non-empty; verify the cmux surface model separately before enforcing there. |
| Scope creep into the audit assembler mid-run | M | FR-5 held out of scope: this run is *dogfooding* `h_mad_assemble_audit.py`, and changing the instrument during the measurement invalidates both. |
| Existing untracked `.h-mad/orca-pins.env` pattern means the receipt is also untracked and invisible to review | L | Follow the established pin-file convention deliberately and document it; the receipt is session state, not project state, and must never be committed. |

## Dependencies

None external. Builds on Wave 1 (`5fa96ba`) and Wave 2 (`787aecf`), both shipped and on `main`.
Touches `h-mad/scripts/hmad-dispatch.sh`, its test suite, and `h-mad/SKILL.md` prose.

## Open Questions

- **Receipt location and format.** `.h-mad/preflight.receipt` alongside `.h-mad/orca-pins.env`, with
  an `HMAD_PREFLIGHT_RECEIPT_FILE` override mirroring `HMAD_ORCA_PIN_FILE` (`hmad-dispatch.sh:91-92`)?
  Flat `key=value` like the pin file, or JSON? Resolve in design.
- **Does the requirement apply on cmux, or orca only?** The `PREFLIGHT:` token is emitted on both,
  but the stale/conflict detection that motivates it is orca-specific. Enforcing on cmux is
  consistent; enforcing only where the hazard exists is narrower. Resolve in design.
- **Exact freshness default.** Needs a number, not a shrug.
- **Which verbs beyond `send` require the receipt?** `clear` and `interrupt` both route through
  `_send_text`. Refusing to `/clear` a pane because no preflight ran would be actively unhelpful
  during recovery — likely the requirement belongs at `_cmd_send`, not `_send_text`. Resolve in
  design; it changes where the code lands.
- **Should an `UNRESOLVED` agent be part of the fingerprint?** `env` PASSes with an agent unresolved
  (the ordinary state of a non-dispatching session). Including it means pinning an agent invalidates
  the receipt — which matches `SKILL.md`'s "re-assert after any re-pin", so probably yes.

## Version History
- v1.0: Initial brainstorm draft.
