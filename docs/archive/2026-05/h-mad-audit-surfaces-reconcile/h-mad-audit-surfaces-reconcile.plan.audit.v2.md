# Plan Audit v2 — h-mad-audit-surfaces-reconcile

> Reviewer: agy (Reviewer.adversarial_consistency). Cycle 2. Target: plan.md v1.2.
> Prior cycle (v1): 1 must-fix + 3 should-fix + 1 nit — all confirmed resolved this cycle.

## Summary

The revised plan (v1.2) resolves all findings from the prior cycle (python-stdlib verdict unit, test-path specification, `[H-MAD]` marker mandate, three-surface clarification, terminology). The new Thrust C (two-layer base + project invariants) is clean and aligns with the repo goals, but introduces one ambiguity about how base-layer non-overridability interacts with the operator override escape hatch.

## Must-fix

- Ambiguity in base-invariant non-overridability vs operator overrides — the plan specifies base invariants are "non-overridable" (FR-9 / Thrust C / Risk row). It must explicitly clarify that this restriction blocks only *project-file* downgrade of a base rule, and does NOT disable the operator `## Acknowledged-not-fixed` sidecar escape hatch for base-layer findings. Ignoring the sidecar for base invariants would violate the Operator-override-preservation invariant (Axis B).

## Should-fix

None

## Nit

- Assembly-artifact (not a source bug): the D-f decision text contains the literal audit-prompt slot tokens, which the prompt-assembly `.replace()` substituted mid-sentence, splitting a clause in the staged prompt. Reword D-f so the plan does not embed the raw slot tokens, preventing recurring prompt corruption on each audit cycle.
