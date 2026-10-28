## Summary
Plan v1.9 cleanly propagates the design v1.8 and spec v1.14 alignment items—including the S0c live round trip and its evidence file, `h_mad_grok_containment.py require` with `audit-cycle --halt-file`, the `calibration/runs/<run-id>/` reading namespace, the `list_changed` run-record trigger (c), and the seven-form canary contract with no `internal` reason. No blocking `build`-class defects remain; only stale version-status notes marking already-landed spec v1.15 items as pending (and `v1.8` in Next Steps item 5) plus a minor sentence-splice typo were found.

## Must-fix
None

## Should-fix
- Plan v1.9 in `docs/01-plan/features/grok-audit-surface.plan.md` still marks the reading namespace, `require`, and the `list_changed` (c) trigger as pending spec v1.15 ("Owed by the spec") and refers to `v1.8` in Next Steps item 5, whereas `docs/01-plan/features/grok-audit-surface.spec.md` already carries the v1.15 reading-namespace update — leaving the plan's cross-doc status notes and version self-reference one revision behind the spec (no implementation or test impact because the plan already states the design v1.8 / spec v1.15 values).
  class: measurement
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `**Reading namespace** (v1.15, from design v1.8): each run's records are one reading`
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `The design's value is three triggers, pending spec v1.15.`

## Nit
- In §"Leak control (AC-2.6): what the plan carries" ("Which list version"), inserting the `list_changed` trigger count left a sentence fragment starting with lowercase `so` after a period (`...not a form (design v1.8 D2). so the check is a probe refusal...`).
