## Summary
The plan addresses all ten functional requirements (FR-1 through FR-10) from the spec, staging the instrument, non-git export-root leak controls, live operator smoke/calibration, and conditional delivery branches. However, it leaves four build-critical invariant contracts open: single-source authority for the AC-3.2 prompt-diff rule, observed-failure discrimination for the new S0 tests over unchanged code, the normal-verdict exit code contract for the `SMOKE:` token, and the git/repository lifecycle reconciling committed seeded copies and calibration artifacts with the no-merge security constraint.

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
- The AC-3.2 prompt-diff check in the probe is planned as a second implementation of the wrapper's `prompt_divergence` rule without establishing single-source authority or a byte-equivalence test across both surfaces — Base Invariant §"Single-source contract" requires that a rule applied by more than one surface have either one authoritative implementation that all surfaces call, or a test asserting byte-equivalence across surfaces. Deferring whether the probe re-implements the diff or reads the wrapper halt leaves independent implementations that can silently diverge. Pin either a single authority or a differential equivalence test across the wrapper and probe.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `_cmd_audit_cycle` in `h-mad/scripts/hmad-dispatch.sh` diffs pass 1's prompt against each pass i ≥ 2 before any dispatch. It halts with `--halt-reason prompt_divergence` when the diff is empty, or when any differing line contains neither pass's report path (a `grep -F` fixed-string match on `${report[1]}` and `${report[$i]}`). The probe's AC-3.2 check applies the same rule.
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `whether the probe re-runs the diff or reads the wrapper's `prompt_divergence` halt; and the exact report-path literal shapes produced by `prepend_output_contract`.`
- The S0 tests pinning existing behaviour for FR-8, FR-9, and FR-10 have no observed-failure (RED/mutation) mechanism — Base Invariant §"Test discrimination" requires every test or guard to be observed failing against unfixed/mutated code before it is trusted, and Base Invariant §"Connection enforcement" requires wiring tests (such as FR-10's `--surfaces codex,agy,grok` dispatch routing) to be mutated in both directions. Because the plan explicitly leaves `exit_check`, `round_check`, `combine`, `scan_grok`, and the wrapper's `--surfaces` grammar untouched and only specifies a RED run for AC-6.2a, the new FR-8/FR-9/FR-10 tests would ship green on arrival without ever being seen to fail. Specify scoped, verified mutations (including both remove-wire and force-wire directions for FR-10) that observe each new test failing before restoring and recording GREEN.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `- **Deliberately untouched**: `exit_check`, `round_check`, `combine`, `scan_grok`, the wrapper's `--surfaces` grammar, the codex-unavailable route, and `fallback_agent` semantics (spec NFR Compatibility). FR-8, FR-9 and FR-10 add tests over existing behaviour and no code.`
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `AC-8.1/8.2 tests; AC-9.1–9.4 tests; FR-10 tests; the AC-9.5 sentence; AC-6.2a (RED run of the new doc test against the uncorrected SKILL.md, then the correction)`
- The component that emits the `SMOKE: PASS` / `SMOKE: FAIL reason=…` token has no normal-verdict exit-code contract — Base Invariant §"Audit-gate signal discipline" requires any gate or check whose verdict the orchestrator/operator consumes to communicate PASS/FAIL via an explicit stdout token and exit 0 on both normal verdicts (PASS or FAIL), reserving non-zero exits for operational/unreadable errors. The plan states that `SEEDSCORE:` exits 0 on PASS, MISS, and INCONCLUSIVE, but never specifies that the `SMOKE:` emitter exits 0 on `SMOKE: FAIL`. State explicitly that the `SMOKE:` derivation component emits `SMOKE: PASS|FAIL` on stdout and exits 0 on both normal verdicts.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `**The outcome branch** is read from token lines, never from `$?`: first the AC-1.7 `SMOKE:` line, then, only if the smoke passed, the AC-5.1 `SEEDSCORE:` line (PASS, MISS and INCONCLUSIVE all exit 0).`
- The plan contradicts itself on whether seeded documents are merged into `main`: S0 (whose entry condition for S1 is "S0 merged") commits the seeded copies under `docs/03-analysis/probes/grok-audit-surface/`, and S3 runs CI re-score tests and the AC-6.4 re-run command against committed files at a named sha, yet Convention Prerequisites states that "Seeded documents and the export roots are never merged into `main` (spec NFR Security), and the committed seeded copies live only under the probes directory." If "Seeded documents" means the live-path placements inside the export roots while the committed copies under `docs/03-analysis/probes/grok-audit-surface/` ARE merged into `main` with S0, both the plan and spec NFR Security must distinguish "live-path seeded documents in export roots" from "committed seeded copies under the probes directory"; if the probes directory copies are also barred from `main`, the plan must define the unmerged ref/branch lifecycle that preserves the calibration sha and allows S3/AC-6.4 and Phase-7 archive survival to function on `main`.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `- Feature branch off `main` at Phase 5c. S1 and S2 run in non-git export roots built from the calibration sha, outside every git work tree, never in the branch's working tree or a worktree. Seeded documents and the export roots are never merged into `main` (spec NFR Security), and the committed seeded copies live only under the probes directory.`
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `- Security: audits run read-only in the AC-2.6 non-git export roots, which sit outside every git work tree. The seeded documents and the export roots are never merged into `main`. The ledger and the labels hold no secrets.`

## Should-fix
None

## Nit
None
