# Architectural Review Phase 6a-prime: tdd-gate-fail-opens

## Findings

### Critical: Missing on-disk spelling derivation for Codex root failures
**File**: `h-mad/hooks/h-mad-codex-tdd-gate.py`
**Context**: `_canonical_root` function

**What's wrong**:
The `_canonical_root` function constructs an arm-2 `Identity` on `canonical_directory` failure, but it passes `str(path)` as the `component` argument. This is the spelled root, not the on-disk spelling.

**Why it matters**:
The design explicitly requires that for an arm-2 result, the component must be in its on-disk spelling. It specifically states for Codex: "An `OSError` from `canonical_directory` on the selected root is the arm-2 `Identity` (`component` the root in its on-disk spelling, the spelled root when that lookup fails)." Failing to do this means Codex uses the raw spelled string of the root in the `judge-error` refusal, violating the requirement to use the on-disk spelling and breaking parity with the Claude gate.

**How to fix**:
Use `identity._on_disk_component(str(path))` to derive the component field for the fallback `Identity`. It should be:
```python
        return identity.Identity(str(path), "", str(path), (), True, 2, identity._on_disk_component(str(path)))
```

**Override**: Not recommended. This directly violates the specification for how arm-2 component names must be reported.

ASSESSMENT: WITH_FIXES
