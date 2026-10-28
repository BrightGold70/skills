## Summary
`docs/01-plan/features/grok-audit-surface.plan.md` (v1.7) has not propagated the `docs/01-plan/features/grok-audit-surface.spec.md` v1.13 changes to AC-11.6 and AC-11.7 (`internal:<ExceptionName>` as the sixth quarantine refusal form and its two required fixtures, plus the two AC-11.6 working-directory placement tests for AC-11.3). In addition, the plan's version references, S0c entry condition, `Still open` section, `Next Steps`, and `R21` reading still treat `spec v1.13` as unwritten and count five quarantine refusal reasons instead of six.

## Must-fix
- AC-11.7 quarantine refusal contract and AC-11.6 test inventory in `docs/01-plan/features/grok-audit-surface.plan.md` restrict `h_mad_grok_containment.py quarantine` to five refusal reasons (`quarantine_exists`, `move_failed:<n>`, `residue:<n>`, `count_mismatch`, `unreadable`) across `S0c in detail`, `Containment`, `Deliverables`, and `R21`, and specify `one fixture per quarantine reason plus a verified run and a residue:1 plant` — `docs/01-plan/features/grok-audit-surface.spec.md` v1.13 AC-11.7 defines six refusal reason forms by adding `QUARANTINE: REFUSED reason=internal:<ExceptionName>` for usage errors and escaping exceptions, and AC-11.6 requires fixtures for all six forms with `internal` planted both by an injected exception and separately by a usage error, so a 5d/5e implementer following the plan omits the sixth refusal form and its two required tests.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `with its five refusal reasons.`
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `or refused with exactly one of six reason forms. The first five are checked in this order:`
- S0c's AC-11.6 test inventory in `docs/01-plan/features/grok-audit-surface.plan.md` (`Containment`, `Tests (AC-11.6, AC-6.6, AC-5.5)`) lists only `AC-11.3 staging, removal on exit and TMPDIR;` and omits the two working-directory placement tests added by `docs/01-plan/features/grok-audit-surface.spec.md` v1.13 AC-11.6 — `spec.md` v1.13 requires one placement test for an export root (prompt and `TMPDIR` in the root) and one for a git work tree (both under `<git toplevel>/.h-mad/`, asserting `git status --porcelain` is unchanged after `exec` exits), so an implementer following the plan's S0c test list will omit those two tests.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `That is owed to spec v1.13 and then to the design.`
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `Residuals stated: a work tree that does not ignore .h-mad/, and a cd below the top level, where strict refuses the prompt file. AC-11.6 gains placement tests.`

## Should-fix
- Stale spec version references, open-item tracking, and `R21` reading across `docs/01-plan/features/grok-audit-surface.plan.md` — `Executive Summary` and `Scope` cite `spec v1.9–v1.12`, `Scope` states `going into spec v1.13`, `S0c` entry condition cites `spec v1.12`, `Still open` and `Next Steps` item 3 state that `spec v1.13` is still owed to record `<git toplevel>/.h-mad/` placement and the subdirectory `--cd` case (both already encoded in `docs/01-plan/features/grok-audit-surface.spec.md` v1.13 AC-11.3), and `R21` cites `Spec v1.12` with `5` quarantine refusal reasons via an `awk` command that only matches bulleted reasons and misses the prose-defined sixth form `internal:<ExceptionName>`.
  class: measurement
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `Spec v1.12 AC-11.4 canary reason forms; AC-11.7 quarantine refusal reasons`
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `- v1.13: Small revision at 37df3ccc (design v1.6 and plan v1.6 committed; sole author). It encodes two texts owed verbatim by the design v1.6 report and one orchestrator ruling.`

## Nit
None
