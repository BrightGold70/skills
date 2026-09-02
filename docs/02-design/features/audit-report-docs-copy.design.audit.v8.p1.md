## Summary
The design provides a robust, comprehensive implementation for mechanically collecting codex audit reports and rejecting transport files at the gate, thoroughly covering the required failure paths, readbacks, and disjoint naming grammars. The specification ACs are cleanly addressed with only one restated divergence regarding the gate's feature extraction.

| Classification | Meaning |
|---|---|
| implemented-as-written | AC-1.1-1.6, AC-2.1-2.12, AC-3.2-3.7, AC-4.1-4.3, AC-5.1-5.4, AC-6.1-6.5 |
| restated | AC-3.1 |
| absent | None |

## Must-fix
- Spec AC-3.1 / FR-3 require the gate refusal to emit `[H-MAD] <feature> gate INVALID (transport file …)`. The design (D3) calculates `feature = args.audit_file.name.split(".")[0] or "unknown"`, which for a transport file (e.g., `audit_f_plan_cycle3_codex.report.md`) results in the entire dot-free stem (`audit_f_plan_cycle3_codex`), not the actual feature name (`f`). The emitted marker will log under the wrong feature name (Restated AC / Axis C).
- The design lists 17 logical mutations for connection and branch enforcement (AC-6.3), but does not explicitly include mutations that vary the separable parts of the gate refusal and CLI error outputs (e.g., keeping `exit 2` but stripping the `[H-MAD]` marker). This violates the "Mutation verification" base invariant, which requires one mutation per separable part of a guard's output to prove those assertions are load-bearing.

## Should-fix
None

## Nit
None
