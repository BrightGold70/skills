## Summary
The design covers the stated work broadly, but omits one specified caller halt and leaves AC-7.3 without an executable attribution surface. Axis C: `implemented-as-written` — AC-1.1, AC-1.2, AC-1.3, AC-2.1, AC-2.2, AC-3.1, AC-3.2, AC-4.1, AC-4.2, AC-5.1, AC-5.2, AC-6.1, AC-7.1, AC-7.2, AC-8.1, AC-8.2, AC-9.1, AC-9.2, AC-9.3, AC-9.4, AC-X; `restated` — AC-7.3 (its fixtures are described but have no surface to execute them). Evidence: 3 files opened, 2 greps run.

## Must-fix
- The caller contract omits `step5:implementer_unresolved` for both `no-record` and `unreadable`, despite the spec requiring that halt; downstream orchestration could dispatch without resolving a record, and the failure-path tests would lack a required outcome.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.spec.md › `TDD-IMPLEMENTER: no-record feature=<pct-encoded> | no such feature in the state file | halt `step5:implementer_unresolved`; the feature name or root is wrong`
  quote: docs/02-design/features/agy-coder-fallback.design.md › `The orchestrator (SKILL.md, §"FR-10") reads the token and never dispatches on these two outcomes`
- AC-7.3 is restated without an executable surface: the design explicitly says attribution remains orchestrator prose and that the five fixtures have “no code surface to drive.” The spec requires those fixtures to go RED against named mutants and GREEN on the rule, so this AC cannot be verified as written until an executable attribution surface is assigned or the spec changes.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.spec.md › `AC-7.3 (v1.8): FR-7 §"Attribution" is pinned by fixtures, each RED against the mutant it names and GREEN on the rule`
  quote: docs/02-design/features/agy-coder-fallback.design.md › `they still have no code surface to drive, since attribution is orchestrator prose, and that surface is owed to the impl-plan`
- Several load-bearing behavioral claims cite deleted scratch probes without the exact command and observed output needed to re-derive them (including directory canonicalisation, containment exceptions, empty-path resolution, invalid `Path` inputs, and hard-link-name production detection). This breaches the behavioral-premise evidence requirement and leaves the target sequence's premises uncheckable.
  class: measurement
  quote: docs/02-design/features/agy-coder-fallback.design.md › `T6 has no name to judge (scratch call at `84ec2133`, deleted). A symlink to a directory is a directory here`

## Should-fix
None

## Nit
None
