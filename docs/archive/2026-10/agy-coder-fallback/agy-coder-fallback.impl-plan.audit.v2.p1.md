AUDIT-agy-coder-fallback-impl-plan-v2-BEGIN
## Summary

The wiring-shape gate and current-tree FR-3/FR-6 probes pass, but three test contracts cannot distinguish the required behavior from a broken implementation, and one acknowledged base-invariant violation lacks an operator deferral. All 23 tasks were reviewed; the repository remains unchanged.

Evidence: 179 files opened (including 160 mutation specs), 3 greps run.

## Must-fix

- Task 6's key-presence mutant survives its prescribed killer after OD-2 — In an in-memory control using the live canonicaliser and the planned T2a, all eight specified no-target fixtures produce identical decisions and kinds with the value guard present or weakened to key presence. The empty string becomes the root directory and T2a denies it; the active non-string cases raise into the same judge-error denial. This violates Test discrimination and prevents the promised ALL_CAUGHT result. Add a discriminator such as null under inactive (correct: allow; key-presence mutant: judge-error), or assert a distinct no-target diagnostic; update the RED split accordingly.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › `| `fr4-class-b-target-presence-only` | the non-empty-`str` test weakened to key presence | `tests/test_h_mad_agy_tdd_gate.py::test_class_b_no_target` |`
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › `The check is **T2a**, right after T2: `Path(resolved.target).is_dir()` → `judge-error` under`
- Task 20's captured run_command test cannot verify the workdir key — If CommandLine is unchanged but the captured workdir key differs from Cwd, the unmodified reader defaults to the root and still allows ls. The live shared policy returned True for ls under the root, an outside directory, a nonexistent directory, and MALFORMED_WORKDIR. Thus the declared F for a new workdir key is false, and GREEN cannot prove that key is consumed, violating Test discrimination and Connection enforcement. Add a captured-envelope fixture whose decision changes with the workdir, or observe the workdir passed to policy; derive RED counts from those discriminating assertions.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › `the captured `run_command` envelope with its command set to `ls`, under `active`: allowed.`
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › `- item 3: P when the captured keys are `CommandLine` and `Cwd` (Task 7's reads), F otherwise;`
- Task 9 does not enforce the budget-to-floor connection — Its 59/60 fixtures give identical results for the required formula and a hardcoded floor of 60. Removing the budget dependency therefore survives the purported derivation test, violating Connection enforcement. Change the budget source in a fixture, for example to 41.1: timeout 61 must be rejected and 62 accepted. Verify a mutant replacing the derived floor with 60 is caught.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › `4. `tests/test_h_mad_hook_wiring_agy.py::test_timeout_floor_is_derived_from_the_judge_budget` —`
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › `   `59` (`timeout-below-floor`), `60` (`WIRED`). 2 nodes.`
- Task 4's preserved Codex self-check violation needs correction or an explicit operator sidecar deferral — The plan expressly retains a normal shell-policy FAIL with exit 2. A controlled invocation of the existing gate confirmed PASS uses stdout/exit 0, while forcing the policy failure produces no stdout, a stderr FAIL token, and exit 2. Audit-gate signal discipline requires stdout/exit 0 for that verdict; recording it as a residual does not activate the Acknowledged-not-fixed escape hatch. Correct the normal-verdict contract and its tests, or obtain the explicit operator acknowledgement required for deferral.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › `- The Codex gate's existing `--self-check` `FAIL shell-policy` returns 2 for a verdict, against`
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › `This feature does not change it`

## Should-fix

- Keep Task 20's suite assertions independent of the archivable probe directory — Item 1 requires reading the capture record under docs/03-analysis/probes, so archiving that directory removes an input needed by six suite nodes. Task 22 deliberately avoids this dependency for its formula probe. Put suite-required capture metadata beside the payload fixtures and retain the human-readable probe record separately.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › `record `docs/03-analysis/probes/agy-coder-fallback/fr8_payload_capture.md` holds, per tool: the`
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › `   and the capture record states `workspacePaths` present or absent for it. 6 nodes.`
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › `test, so archiving the probe directory cannot break the suite).`

## Nit

None

🌱 graft saved ~107,690 tokens this turn (3 calls).
AUDIT-agy-coder-fallback-impl-plan-v2-END
