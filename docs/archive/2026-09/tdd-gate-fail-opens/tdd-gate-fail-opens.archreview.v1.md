# Architectural Review: tdd-gate-fail-opens (Phase 5)

## Overview
The Phase 5 implementation successfully centralizes path canonicalization in `h_mad_target_identity.py`, bounded judge reaps, and `--session-id-from-git-dir` logic. However, there are significant invariant and pattern violations in how the TDD gates integrate the path canonicalization logic.

## Findings

### 1. Invariant Violation: Canonicalized Payload CWD Escapes Containment Check
**Location:** `h-mad/hooks/h-mad-codex-tdd-gate.py` in `_relative_target()`
**Issue:** The audited design mandates: "On that success the caller passes the already-canonical cwd, so `_payload_cwd_base` still tests containment". The current implementation sets `base = Path(identity.canonical_directory(...))` but skips calling `_payload_cwd_base` on this canonicalized result. If canonicalization of the CWD resolves to a path outside the project root, it bypasses the containment check, leading to an invariant violation (sandbox escape).

### 2. Invariant Violation: Unconditional Refusal on Root Open Failure
**Location:** `h-mad/hooks/h-mad-tdd-gate.sh` in the Claude TDD gate hook
**Issue:** The hook unconditionally refuses with `judge-error` if the root cannot be entered:
```bash
  if [ "$CANON_ARM" = 2 ] && [ "$CANON_COMPONENT" = "$CANON_ROOT" ] &&
     { [ ! -d "$CANON_ROOT" ] || [ ! -x "$CANON_ROOT" ]; }; then
    _refuse judge-error "project root (CLAUDE_PROJECT_DIR) cannot be entered"
  fi
```
This check happens before `_chain_may_hold_state`, which causes an **ungoverned** write to incorrectly fail-closed. This violates the FR-3 governed-only rule specified in the design: "A root-open failure is the arm-2 record above, exit 0, and FR-3's governed-only rule applies to it, including an ungoverned allow."

### 3. Pattern Violation: Redundant `scandir` in Unresolvable Branch
**Location:** `h-mad/hooks/h-mad-codex-tdd-gate.py` in `_main_guarded()`
**Issue:** In the `if resolved.unresolvable:` block, the gate attempts to run `os.stat` and `os.scandir` on `resolved.component` to find an alternative hard link. The canonicaliser already handles the scan for resolvable targets. For an unresolvable path, `component` is simply the spelled component that failed. Running a manual stat/scandir block here re-implements path resolution logic outside the `canonicalise` module's single-source contract and introduces dead code (the operations will likely fail with `OSError`). The gate should use `resolved.component` directly in the `_deny()` reason.

ASSESSMENT: WITH_FIXES
