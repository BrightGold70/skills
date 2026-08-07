AUDIT-regression-provenance-ledger-design-v7-BEGIN
## Summary
The design is robust, explicitly addresses the failures that plagued prior iterations, and demonstrates excellent invariant compliance (including the crucial J18 live-file guard and connection enforcements in both directions). There is exactly one gap on Axis C where the design's data model missed a required field from the spec.

## Must-fix
- **Missing successor feature field for `superseded` wires (Axis C, AC-4.2)** — The spec AC-4.2 states that a removal declaration must carry "additionally for `superseded` the feature that supersedes it... only `superseded` has a successor feature to name." The design's data model / schema changes table correctly adds `removed_by_feature` and `successor_pin` (for `renamed`), but completely omits a field for the superseding feature. This must be added to the schema and validation to fully implement the spec (e.g. `superseding_feature`).

## Should-fix
None

## Nit
None
AUDIT-regression-provenance-ledger-design-v7-END
