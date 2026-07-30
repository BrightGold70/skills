# Report: tdd-dispatch-verification-discipline

## Executive Summary
The h-mad TDD-dispatch prompts + SKILL.md now carry a RED-side acceptance gate, a revert-test definition of GREEN (restore-by-executing-the-symbol), two named-and-prohibited evasions, an author call-form rule, and a pin re-verification rule — closing the RED-side/GREEN-definition gap the 5e anti-gaming step never reached; shipped via H-MAD with 100% AC match, both coupled suites green, and the behavioral proof (incident replay vs real `feature/193`) passing both directions.

**Status:** COMPLETE · **Branch:** feature/212-tdd-dispatch-verification-discipline · **Base→Head:** d69d933 → 0f59a80
**Suite:** h-mad 760/0 · HemaSuite coupled 54/0 · **Match:** 100% · **6a-prime:** READY_TO_MERGE · **AC-IR:** proven both directions

## What shipped
Six literal instruction blocks across three prompt/protocol files (no scripts):
- **FR-1** (`codex-implementer-prompt.md` RED): per-test acceptance evidence — failure names the property / would a pass survive deleting the behaviour / name the method invoked and confirm it holds the behaviour.
- **FR-2** (`SKILL.md` §5e, authoritative): GREEN is the revert test (revert prod → RED returns exactly → restore → green returns), restoration verified by **executing the symbol, never by grepping** (the stale-`.pyc` trap); `codex-verifier-prompt.md` carries a pure pointer to it.
- **FR-3** (`codex-implementer-prompt.md` GREEN): two prohibited/reportable evasions (restructure a literal/identifier/import to fool a count; edit out-of-scope code for a count) + author rule in SKILL.md ("assert the call form, not an occurrence count over a whole method").
- **FR-4** (`SKILL.md`): re-verify every impl-plan pin against the tree at dispatch.
Locked by a new doc-test file (`test_h_mad_tdd_dispatch_discipline_prompt.py`), every literal mutation-verified.

## Phase ledger
- P2 spec adopted from the HemaSuite `feature/193` handover (`5c0dcaf`).
- P3 plan: 6 audit cycles — incident-replay + assumption-verification requirements, and a c3–c5 verifier-target oscillation resolved by a single-source pointer.
- P4 design: 2 cycles.
- P5 impl-plan: 6 cycles (single-source, fully-executable AC-IR steps); Codex RED (6 genuine failures) → GREEN (760/0). The GREEN verdict was lost when a 2-min tool cap killed the codex process — recovered by the verify-from-code discipline (the exec-missing-report feature shipped earlier this session).
- P6: **6a-prime WITH_FIXES → the feature caught its own build** — the single-source doc-test's global `count("grepping")==1` over-constrained SKILL.md and recruited the GREEN implementer into the exact out-of-scope evasion FR-3 forbids; fixed by asserting the call form (specific literals) and reverting the collateral, re-review READY_TO_MERGE. **AC-IR** incident replay vs real `feature/193`: GREEN-side `STATUS: BLOCKED` (refused the literal-split), RED-side flagged the vacuous test.
- P7: precondition gate READY · telemetry · merge · push.

## Verification evidence
- RED genuine: only the new test file added; 6 real AssertionErrors (literals absent).
- Anti-gaming: every literal mutation-tested (delete → its doc-test RED; restore → green); single-source enforced by specific-literal absence (not a fragile global count).
- Behavioral: both incident replays against the historical artifacts pass — the strongest proof the prompts change agent behavior, not just doc contents.

## Follow-ups / carry
- None owed. Rollout: `feature/212` merges to main with the analysis + this report.

## Version History
- v1.0: Phase 7 closure report.
