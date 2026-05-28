# Plan Audit v1 — h-mad-audit-surfaces-reconcile

> Reviewer: agy (Reviewer.adversarial_consistency). Cycle 1. Target: plan.md v1.1.

## Summary

The plan outlines a robust design to transition the audit gate to a token-based signal and extend phase templates into bkit-compliant supersets. It addresses the core causes of false gate-FAILs and OMC retry noise while maintaining zero runtime external dependencies. However, it requires an explicit guarantee on `[H-MAD]` logging-marker compliance and clarification on scope details to avoid silent failures.

## Must-fix

- H-MAD log-marker omission in the gate-step rewrite — the proposed `SKILL.md` gate-step rewrite (token parsing) does not explicitly mandate that the rewritten step emit the required `[H-MAD]` log markers on failure/halt. Marker discipline (Axis B) requires state transitions and halts be diagnosable from logs alone; omission is a hard-gate violation.

## Should-fix

- Ambiguity around the "three reader surfaces" — Scope says "the audit-gate verdict logic + its three reader surfaces", but the changes detail only two that actually *count* bullets (the `SKILL.md` orchestrator gate-step and `h_mad_do_preconditions.py`). The third surface (the template) authors guidance, it does not read. Identify the third surface precisely and state whether it parses the token, so nothing silently mis-reads the new `exit 0` as PASS.
- Platform-divergence risk from D-a (awk vs python) — if D-a resolves to retain the awk one-liner alongside the python parser (even with a byte-equivalence test), GNU vs BSD awk divergence persists. Resolving D-a to a single python stdlib unit for both surfaces robustly enforces the Single-source contract and removes the platform risk.
- Unspecified test directory path — the deliverables include test files but no path. Tests must live in the skill's own hierarchy (`~/.claude/skills/h-mad/tests/`) to keep the skill portable and standalone.

## Nit

- Inconsistent terminology — the plan uses "Axis-2 resolution" (D-b) and "Axis-2 alignment" (a risk row) for Must/Should parity, which risks confusion with the "Axis B" project invariants. Use "Single-source contract" or "Must/Should parity" consistently.
