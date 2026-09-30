# Phase 6a-prime Architectural Review Report: tdd-gate-fail-opens

## Overview
I have reviewed the Phase 5 diff for the `tdd-gate-fail-opens` feature against the audited design. The Python components (`h_mad_target_identity.py`, `h_mad_codex_tdd_gate.py`, `h_mad_tdd_judge.py`, and `h_mad_resume_decision.py`) and their tests map perfectly to the design rules. However, there is a **Critical Invariant Violation** in the Claude Bash gate (`h-mad-tdd-gate.sh`).

## Findings

### 1. CRITICAL: Unconditional `judge-error` refusal bypasses FR-3 governed-only rule
**File**: `h-mad/hooks/h-mad-tdd-gate.sh`
**Lines**: ~237-240 (inside the `unresolvable=yes` block)
```bash
  if [ "$CANON_ARM" = 2 ] && [ "$CANON_COMPONENT" = "$CANON_ROOT" ] &&
     { [ ! -d "$CANON_ROOT" ] || [ ! -x "$CANON_ROOT" ]; }; then
    _refuse judge-error "project root (CLAUDE_PROJECT_DIR) cannot be entered"
  fi
```

**What's wrong & Why it matters (Invariant Compliance)**:
The implementation adds a branch that unconditionally refuses writes with `judge-error` if the root cannot be entered (absent or not executable), completely bypassing `_chain_may_hold_state`.
This directly violates FR-3's governed-only rule and contradicts the audited design, which explicitly states: *"A root-open failure is the arm-2 record above, exit 0, and FR-3's governed-only rule applies to it, including an ungoverned allow."*
The design mandates that the Bash gate must branch ONLY on `unresolvable`. By short-circuiting the check for an absent or `000` root, the gate inappropriately overrides the state chain and forces a `judge-error` (fail-closed) even on an ungoverned write, violating the design's prescribed order.
Note: The test `test_claude_root_open_failure_refuses_only_when_governed` only passed because it uses mode `0o311` (executable but unreadable), which causes `[ ! -x "$CANON_ROOT" ]` to evaluate to false and skip this illegal block.

**How to fix**:
Remove the `if [ "$CANON_ARM" = 2 ] ...` block entirely. The subsequent `_chain_may_hold_state "$ROOT_ABS" "$CANON_PREFIX" || _allow` and `_read_state` commands already correctly evaluate whether an unreadable/missing root is governed or ungoverned, and will produce the exact `unresolvable arm=<N> component=<decoded component>` reason mandated by the design when governed.

## Conclusion
The Python components accurately implement the gap analysis requirements. The single bash violation is structural but trivial to fix. The change is acceptable with this fix.

ASSESSMENT: WITH_FIXES
