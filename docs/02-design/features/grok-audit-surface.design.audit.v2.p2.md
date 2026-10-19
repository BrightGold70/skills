AUDIT-grok-audit-surface-design-v2-BEGIN
## Summary
`docs/02-design/features/grok-audit-surface.design.md` (v1.2) resolves all 24 must-fixes and 5 should-fixes from cycle 1 and is fully consistent with `docs/01-plan/features/grok-audit-surface.spec.md` (v1.7), `docs/01-plan/features/grok-audit-surface.plan.md` (v1.5), and operator decision D4 (`docs/03-analysis/grok-audit-surface.decision-2026-10-19-d4.md`). All nine probe modes and their token grammars, the calibration-data inclusion/exclusion set (`auditcycle.txt` included), `extract`'s dual-input and placement-mapped quote resolution, `delivered=out` acceptance, per-cycle `root.txt` provenance, observational `SHOULD:` and `SPLIT:` outputs, and mutation anchors verified cleanly against the repository at `28ec5bfc` with `PRECHECK: PASS issues=0`.

## Must-fix
None

## Should-fix
None

## Nit
- In `## Overview` (line 7), the prose still introduces the inputs as `spec v1.6 (94a4fd2c) and plan v1.3 (ab3c9f32)` even though v1.2 incorporates the D4 version-agnostic updates from spec v1.7 and plan v1.5.
AUDIT-grok-audit-surface-design-v2-END
