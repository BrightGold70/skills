AUDIT-grok-audit-surface-plan-v5-BEGIN
## Summary
All eleven FRs are addressed, but FR-6 introduces a canary-scan exception absent from the spec; other blockers concern conflicting interfaces and missing behavioural provenance. Three targeted tests passed; the Phase-5 hook blocked Graft, OneContext and shell searches, so historical stamps and censuses were not revalidated.

Evidence: 15 files opened, 0 greps run.

| Requirement | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | restated |
| FR-7 | implemented-as-written |
| FR-8 | implemented-as-written |
| FR-9 | implemented-as-written |
| FR-10 | implemented-as-written |
| FR-11 | implemented-as-written |

Validation: `/opt/anaconda3/bin/python3.11 -m pytest -q -p no:cacheprovider h-mad/tests/test_grok_audit_surface_smoke.py::test_smoke_pass h-mad/tests/test_grok_audit_surface_smoke.py::test_smoke_no_delivery h-mad/tests/test_hmad_dispatch_audit_cycle.py::test_verb_prompt_divergence` → `3 passed in 12.35s`.

## Must-fix
- FR-6 is restated: S0c adds a published diagnostic scan of the canary, while AC-6.6 excludes the canary from scanning and the plan's containment-halt branch repeats that exclusion. The plan narrows the exclusion to gating scans without saying so in the spec. Either remove the diagnostic scan or explicitly adopt its non-gating exception in the spec and reconcile the plan's blanket exclusion.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › ``3. `h_mad_tool_calls.py scan` on the canary log, published only. It gates nothing.``
  quote: docs/01-plan/features/grok-audit-surface.spec.md › ``The AC-11.4 canary is not a pass: it is asked to write and read outside its working directory, it is judged by its own token, and it is not scanned.``

- The smoke stdout contract conflicts with the implemented and tested interface. The plan requires one stdout line total, whereas the existing passing smoke test requires vocabulary, root-acceptance, timeout and binary lines before the final token. Following the plan literally would remove published output and break that test without establishing that it pinned a defect, contrary to base Regression provenance. Specify exactly one final SMOKE token while retaining the preceding observations, or explicitly reconcile an intentional interface change.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `and prints exactly one line on stdout:`
  quote: h-mad/tests/test_grok_audit_surface_smoke.py › `"published lines must follow the D11 order and end on the smoke token"`
  quote: docs/02-design/features/grok-audit-surface.design.md › `**Published lines, before the token:**`

- The probe's exclusive import list contradicts both the shipped gate-parser reuse and the shared containment scanner required by the derived design. It omits h_mad_audit_cycle, which the current probe imports, and h_mad_tool_calls, which the design imports to keep live and rescore scans authoritative in one place. Reconcile the permitted imports with those reuse boundaries; otherwise implementers must choose between conflicting instructions or replace existing shared implementations.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › ``and imports only the stdlib plus `h_mad_audit_gate` / `h_mad_audit_origins` / `h_mad_review_evidence` from `h-mad/scripts/```
  quote: docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py › `import h_mad_audit_cycle as _cycle`
  quote: docs/02-design/features/grok-audit-surface.design.md › ``and, new in v1.6, `h_mad_tool_calls` (`scan_log`, D19), so the cycle-end scan and the score's re-derivation are one function.``

- The three-shape prompt-divergence observation still lacks its exact runnable reproduction command. Calling it recorded-but-not-reproducible acknowledges rather than resolves the base Behavioural premises carry their command violation. R12 checks a mutation row, and the targeted passing wrapper test does not reconstruct all three historical observations; retain a complete reproduction invocation or script beside their outputs.
  class: measurement
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `the scratch probe that produced it was deleted, and no command here rebuilds it.`

## Should-fix
- Complete the codex tracer decision table for control-fails/treatment-passes. The other three combinations are explicit, but this one has no stated route. Define whether the successful treatment permits codex or the inconsistent pair requires a conservative unavailable outcome, keeping any causal attribution unverified.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `**Both pass**: codex runs.`

- Close the stale namespace-adoption debt. The plan still labels the reading namespace pending spec v1.15 although the supplied spec already adopts it; refresh the open-work list so completed reconciliation is not dispatched again.
  class: measurement
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `A later run adds its own namespace and never touches an earlier one (design v1.8 D8; spec v1.15 is adopting it).`
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `**Reading namespace** (v1.15, from design v1.8):`

## Nit
None
AUDIT-grok-audit-surface-plan-v5-END
