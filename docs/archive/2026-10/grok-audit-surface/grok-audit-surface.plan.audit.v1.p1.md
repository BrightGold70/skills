## Summary
The plan addresses FR-1 through FR-10, including the conditional delivery branches, so each is implemented-as-written at plan granularity. It still leaves four build-critical enforcement contracts unspecified: prompt-diff authority, discrimination of pins over unchanged code, smoke normal-verdict exit behavior, and the committed calibration artifact lifecycle.

| Spec item | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |
| FR-7 | implemented-as-written |
| FR-8 | implemented-as-written |
| FR-9 | implemented-as-written |
| FR-10 | implemented-as-written |

Evidence: 9 files opened, 11 greps run.

## Must-fix
- The AC-3.2 prompt-diff predicate is planned as a second implementation in the probe without making the wrapper authoritative or pinning equivalence. The wrapper already owns the operational `prompt_divergence` decision; two independently maintained predicates can silently diverge and either certify prompts the wrapper would halt or reject a cycle the wrapper dispatched. Choose one authority (for example, consume the wrapper halt) or specify a shared corpus/byte-equivalence test that fails for either divergence.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `The probe's AC-3.2 check applies the same rule.`
- The S0 tests that pin already-shipped FR-8/FR-9/FR-10 behavior have no stated observed-failure method. The plan explicitly leaves the relevant implementation unchanged and records a RED run only for AC-6.2a; ordinary TDD cannot make the new behavior-preservation tests red against that unchanged code. Specify verified, scoped mutants (and for each connection test both remove-wire and force-wire directions) plus the expected failing test, then restore and run GREEN.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `- **Deliberately untouched**: `exit_check`, `round_check`, `combine`, `scan_grok`, the wrapper's `--surfaces` grammar, the codex-unavailable route, and `fallback_agent` semantics (spec NFR Compatibility). FR-8, FR-9 and FR-10 add tests over existing behaviour and no code.`
- The smoke token has no normal-verdict exit contract. The plan says stages consume tokens rather than `$?`, but explicitly grants exit 0 only to score verdicts; a smoke failure implemented with a non-zero exit would trigger tool/plugin failure before the orchestrator can route on `SMOKE: FAIL`. Require `SMOKE: PASS|FAIL` on stdout and exit 0 for both normal outcomes, reserving non-zero for unreadable/operational errors.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `**The outcome branch** is read from token lines, never from `$?`: first the AC-1.7 `SMOKE:` line, then, only if the smoke passed, the AC-5.1 `SEEDSCORE:` line (PASS, MISS and INCONCLUSIVE all exit 0).`
- The plan requires committed seed data and later re-scoring from it while also prohibiting those seeded documents from being merged into `main`, but never defines the retained calibration ref/branch, how its sha is preserved, or how the published mainline reading points to it. Without that lifecycle, S3 cannot both publish a reproducible named-sha run and obey the no-merge security boundary; implementation and re-run tests would necessarily guess where the ledger, labels, key, and archive source are retained.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `- Feature branch off `main` at Phase 5c. S1 and S2 run in non-git export roots built from the calibration sha, outside every git work tree, never in the branch's working tree or a worktree. Seeded documents and the export roots are never merged into `main` (spec NFR Security), and the committed seeded copies live only under the probes directory.`

## Should-fix
None

## Nit
None
