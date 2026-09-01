## Summary
The design correctly incorporates the structural corrections from the plan, placing the tail-evidence pass after Pass 2 and before Pass 3 (now Pass 4) without coupling it to OS evidence. However, it restates the spec's decline contract (`rc 1`) to explicitly avoid returning non-zero so execution can fall through to Pass 4. This divergence in the flow control contract must be explicitly reconciled with the spec.

| AC | Status |
|---|---|
| AC-1.1, AC-1.2, AC-1.3 | `implemented-as-written` |
| AC-2.1, AC-2.2 | `restated` |
| AC-2.3, AC-3.1, AC-3.2, AC-3.3, AC-4.1 | `implemented-as-written` |
| AC-4.2 | `restated` |
| AC-4.3, AC-5.1 | `implemented-as-written` |

## Must-fix
- Axis C (AC-2.1, AC-2.2, AC-4.2) `restated` — The spec explicitly mandates that the pass "declines (rc 1)" on ambiguity or zero matches (e.g., "the pass declines (rc 1) and prints no handle"). The design restates this: "Zero or more than one → fall through to Pass 4 unchanged. The pass never returns non-zero itself; falling through IS its decline." This is a narrower reading that correctly avoids short-circuiting `_orca_find` with a failure code so Pass 4 can still run, but the divergence from the spec's explicit `rc 1` mandate must be formally reconciled in the spec to prevent verification failures.

## Should-fix
- Undefined timeout variable — The read command uses `"$HMAD_TAIL_READ_TIMEOUT"`, but the design does not specify where this variable is defined or its default value. If it is unbound, `--timeout ""` will cause the `hmad-dispatch run` call to fail with a syntax error, breaking the pass. Define the variable or provide a fallback (e.g., `${HMAD_TAIL_READ_TIMEOUT:-2}`).

## Nit
None
