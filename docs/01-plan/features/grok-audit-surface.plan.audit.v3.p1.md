## Summary
The plan is strong on staging, token contracts, live-versus-synthetic separation, and the PASS/MISS outcome split, but FR-2 and FR-3 are restated rather than implemented as written. The two divergences affect the leak-closed calibration root and the independently required prompt-equality check.

Evidence: 10 files opened, 12 greps run.

| Spec item | Classification | Reconciliation |
|---|---|---|
| FR-1 | implemented-as-written | Smoke modes, exit contract, and failure delivery are staged. |
| FR-2 | restated | The required minimum exclusion population is not carried into the root-builder plan. |
| FR-3 | restated | AC-3.2's direct prompt comparison is replaced with consumption of the wrapper token. |
| FR-4 | implemented-as-written | Extraction, blind labelling, advisory hints, and scoring are planned. |
| FR-5 | implemented-as-written | The stdlib probe, verdicts, and synthetic branch fixtures are planned. |
| FR-6 | implemented-as-written | Outcome-specific publication and unconditional command correction are staged. |
| FR-7 | implemented-as-written | Routing remains conditional on `SEEDSCORE: PASS`. |
| FR-8 | implemented-as-written | Union and third-pass evidence-floor pins are planned. |
| FR-9 | implemented-as-written | Existing exit/round behavior is pinned without code changes. |
| FR-10 | implemented-as-written | Three-surface wrapper wiring is covered with two-direction mutations. |

## Must-fix
- FR-2 / AC-2.6 is restated with an incomplete declared-exclusion contract: the plan's root builder says the list covers only the probes directory, but the spec requires source archives, every final component beginning `grok-audit-surface`, and `docs/03-analysis/agy-coder-fallback.authoring/` as well. Define those required entries and the version of the main-held list that S0b/S1/S2 and the re-score consume; otherwise the first export contains answer-key/source copies and must fail its scan, or the operator can silently vary the root across the cited calibration sha.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `Remove the declared exclusion list, which covers `docs/03-analysis/probes/grok-audit-surface/` and so the calibration directory under it.`
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `The list holds at least each source feature's `docs/archive/*/<feature>/` directory, `docs/03-analysis/probes/grok-audit-surface/`, every path anywhere in the tree whose final component begins with `grok-audit-surface` (this covers `grok-audit-surface-brainstorm.md` as well as the `grok-audit-surface.<phase>.md` files and the measurement doc), and `docs/03-analysis/agy-coder-fallback.authoring/`.`
- FR-3 / AC-3.2 is silently narrowed from validating retained prompts to treating the wrapper's `AUDITCYCLE:` token as conclusive. The spec requires the probe to compare pass 1 with every later prompt and fail an empty/foreign diff; the proposed opposed fixtures deliberately require the probe to ignore exactly those conflicting prompt artifacts. Amend the spec to adopt wrapper-token authority, or plan the specified prompt comparison (and reconcile it with the single-authority rule) before implementation.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `The probe decides AC-3.2 per cycle from that recorded `AUDITCYCLE:` line alone: a cycle that reached dispatch passed the wrapper's check, and a `reason=prompt_divergence` cycle failed it, is published, and goes through AC-3.4. The probe does not diff prompts and carries no report-path mask.`
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `Comparing pass 1 with each later pass, there must be at least one differing line, and every differing line must contain, as a fixed string, one of the two passes' report paths. An empty diff fails the cycle, and so does any other differing line.`

## Should-fix
None

## Nit
None
