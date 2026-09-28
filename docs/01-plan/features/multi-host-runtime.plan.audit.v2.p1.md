AUDIT-multi-host-runtime-plan-v2-BEGIN
## Summary
The plan covers FR-1 through FR-12, but FR-11 and FR-12 narrow verification that the spec requires; the rollback procedure also lacks a verified recovery path. The remaining issues concern a smoke assertion deferred until implementation and an unnamed analysis artifact.

| FR | Classification |
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
| FR-11 | restated: V-11.2 and V-11.3 checks are narrower |
| FR-12 | restated: byte identity is measured under injected root overrides |

Evidence: 12 files opened, 10 greps run; the install checker, budget and decision entry points, dispatch wrapper, skill contract, current install roots, and both documents were read. 🌱 graft saved ~20,513 tokens (~$0.01) this turn, 1 call.

## Must-fix
- FR-11 restates V-11.3 from whole-state sha256 identity to equality of one parsed feature record — a write to another key or a byte-only rewrite of the ignored state file passes the proposed smoke while the spec requires it to fail. Add a before/after sha256 comparison of the entire state file, or revise the spec explicitly.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `and the sha256 of `docs/.bkit-memory.json` is unchanged.`
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `The V-11.3 state observable is `orchestrator_state[$F]` in the main checkout's`
- FR-11 restates V-11.2 as substring checks and explicitly declines to compare null fields — a final message can contain the expected text while reporting the wrong status, and a wrong non-null value passes when the record is null. Require parsed output fields equal to both state fields, including null, or change V-11.2 in the spec.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `These equal what `docs/.bkit-memory.json` holds for it, read directly.`
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `each grepped in `$S/out` when non-null, with a null value printed as "not`
- FR-12's byte-identity probe is restated under injected root overrides, while AC-12.2 requires the new options at their specified defaults — the existing CLI fixtures use h-mad/handoff names, so the four pre-step links point to a different checkout and add issue lines at the real defaults; the agy root also has a measured debugger collision detail. Reconcile the two spec requirements and test the chosen contract in the actual default-root state.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `produce byte-identical stdout and exit codes with `HMAD_HOST` unset and the new options at their`
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `sets both variables to non-existent paths under `tmp_path`. Every subprocess inherits them, so no test`
- The failure path promises to revert the unpushed merge without verifying the resulting main tree — the smoke may dirty tracked files, in which case revert can refuse or conflict, and a zero exit alone would not prove the intended state. Specify a recovery branch for dirty trees and re-read HEAD, merge ancestry, and working-tree state after a successful revert before reporting recovery; this is required by the base mutation-verification invariant.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `**On any `HALT` or `FAIL`:** do not run 7e; `git -C "$REPO" revert -m 1 --no-edit "$MERGE"``

## Should-fix
- The V-11.1 transcript assertion is deferred until the merged log format is known — the executable check for adapter-before-script order is a core smoke gate, yet its parser and failure observation are not specified. Pin an exact prompt and log assertion against the merged wrapper before 7f.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `Written as their own `|| exit 1` lines once the merged log format is known, and never omitted:`
- Name the Phase-6 analysis artifact path in the deliverable table — the plan gives a concrete path for the live-smoke record but only a generic document label for AC-4.5, AC-4.6 and AC-6.1, making the record hard to locate and verify.
  class: measurement
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `| Pre-change gap table (construct × adapter, `addressed`/`absent`, with its sha), the AC-4.6 record, the branch classification and the byte-identity reading | Phase-6 analysis document |`

## Nit
None
AUDIT-multi-host-runtime-plan-v2-END
