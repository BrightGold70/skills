AUDIT-audit-report-docs-copy-plan-v3-BEGIN
## Summary
The plan addresses all six functional requirements in the spec without silently restating or omitting one; Axis C classification is below.

| Requirement | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

However, the proposed transport basename grammar is not disjoint from the plan's own allowed collected-name grammar, and one promised production import is left behaviorally unpinned.

## Must-fix
- `TRANSPORT_RE` overlaps a valid collected docs path — FR-1 permits any discriminator matching `[A-Za-z0-9][A-Za-z0-9_-]*` except `p\d+`, so `surface="report"` is valid, while no stated or enforced feature grammar excludes `feature="audit_f"`; `_collected_path` would therefore produce `audit_f.plan.audit.v8.report.md`, which both `^audit_.*\.report\.md$` and `_VERSION_RE` match. This falsifies the claimed two-direction separation and makes a legitimately collected artifact ungateable, so the spec and plan must establish a mechanically enforced disjoint namespace (and add this collision to AC-3.5a's corpus) before implementation.
- The promised CLI-to-gate regex import has neither defined behavior nor a drop/force test — the architecture says `h_mad_collect_report.py` imports `TRANSPORT_RE`, but the collector must also accept a docs path under AC-2.8, and the 15-mutation list tests only the gate's use of the regex, not removal or unconditional application of the CLI connection. An import is a connection under the base invariant; either specify the CLI behavior and add bidirectional connection mutations, or remove this production import requirement from both spec and plan.

## Should-fix
None

## Nit
None
AUDIT-audit-report-docs-copy-plan-v3-END
