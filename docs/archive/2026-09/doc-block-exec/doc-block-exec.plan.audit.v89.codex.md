## Summary

The plan addresses every functional requirement, but its measurement accounting and verification-status prose still contain contradictions. Repository reads confirmed the 86-row current mutation matrix and the corrected collection-only pin; the read-only session prevented report-file delivery.

Evidence: 12 files opened, 4 greps run.

| Requirement | Classification | Coverage |
|---|---|---|
| FR-1 | implemented-as-written | Tagged extraction, selection, shared bounder |
| FR-2 | implemented-as-written | Literal simultaneous substitution and refusals |
| FR-3 | implemented-as-written | Disposable cwd, declared shell, separate streams |
| FR-4 | implemented-as-written | Verdict grammar, exit partition, registry checks |
| FR-5 | implemented-as-written | Validated timeout and bounded process cleanup |
| FR-6 | implemented-as-written | Atomic tagging/migration and discriminating wire tests |

## Must-fix

- The heading-differential explanation attributes the historical zero to an incorrect measurement without supporting evidence — violating **Assumption verification**’s causal-evidence requirement. The plan itself records exact reproduction at `1861157`, and reading that commit confirms no bare-hash specimen existed there; the specimen appears later. Separate the genuinely empty historical corpus from the later incorrectly carried absence claim.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `zero meant *the shape had not been looked for correctly*;`

## Should-fix

- The softened-set conclusion contradicts its own corpus accounting — the executed probe returns `closing_hash=5` on GLOB, so only TRACKED has an empty softened-identity set at `cac6edc`. Restrict the conclusion accordingly; `new_only=0` does not establish identity equivalence.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `the softened set is empty again on both corpora`

- The Deliverables census incorrectly assigns 85 distinct names to every historical reading — the committed matrix contains 81 rows and 81 distinct names at `09e9307`, then 85/85 at `cb4fe99` and `cac6edc`. The current 86-row requirement is correct, but its historical derivation contradicts the authoritative walk.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `with **85** distinct names in column 1 at each`

- Verification-status passages were not advanced with v1.105 — the register still identifies v1.104’s measurement commit, and the ledger still calls that revision’s commit “this revision’s.” The ledger reads 88/88 at `cac6edc`; v1.105 neither publishes that reading nor explicitly records skipping it. Preserve the historical rows while stating the current revision’s status separately.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `Inherited-unverified at `fbc2ea0`, the commit v1.104 is measured at`

## Nit

- The register-walk residual says its stop address is the residual paragraph’s opening, but the published command stops at `**ONE MEMBER LEFT THIS REGISTER`. Update the description to match the command.
