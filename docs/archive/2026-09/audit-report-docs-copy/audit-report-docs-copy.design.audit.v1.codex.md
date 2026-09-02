AUDIT-audit-report-docs-copy-design-v1-BEGIN
## Summary
Axis C reconciliation: the design covers the paired plan's FR-level scope, but two spec ACs do not reconcile cleanly: one is restated incompatibly and one is not specified beyond a passing reference. Classification table:

| Classification | Items |
|---|---|
| implemented-as-written | AC-1.1-AC-1.6; AC-2.1-AC-2.7; AC-2.9-AC-2.12; AC-3.1, AC-3.2, AC-3.4, AC-3.5, AC-3.5a, AC-3.6, AC-3.7; AC-4.1-AC-4.3; AC-5.1-AC-5.4; AC-6.1-AC-6.5 |
| restated | AC-2.8 |
| absent | AC-3.3 |

## Must-fix
- AC-2.8 is restated incompatibly by the AC-2.11 short-circuit in `collect()` — spec: "When `--report` resolves (`Path.resolve()`) to the derived docs path itself: no copy is attempted; verdict `OK` iff the file is non-empty and `<path>.done` exists; the `.done` marker is removed ... otherwise `MISSING`." Design: "# AC-2.11: already collected — report present, marker or not, bytes identical" followed by a byte-identical short-circuit before `_has_complete_report`. The design's earlier branch is broader on the OK condition and makes the same-file marker-removal path unreachable for a docs-path `$RP`, so AC-2.8 would return OK with no marker and leave an existing marker behind.
- AC-3.3 is absent as a satisfiable downstream contract — the spec requires `h_mad_audit_cycle.gate()` on a transport-stem path to return `(\"INVALID\", 0, 0, [])` and `combine()` to render `UNVERIFIED` with reason `no_gate_sections:p<i>`, but the design only says `_gate_token` keeps matching. A regex compatibility note does not pin the `gate()` return tuple or `combine()` reason, so the audit-cycle consumer path can drift while the gate CLI tests stay green.

## Should-fix
None

## Nit
None
AUDIT-audit-report-docs-copy-design-v1-END
