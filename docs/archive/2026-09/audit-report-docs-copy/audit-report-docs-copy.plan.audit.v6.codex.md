## Summary
Axis C reconciliation: no FR is absent or restated at FR granularity; the plan covers FR-1 through FR-6, but one covered mechanism is internally inconsistent and would make its AC/mutation tests non-discriminating.

| ID | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

## Must-fix
- AC-1.6 / the `_collected_path` disjointness assert is impossible as stated — the plan defines `TRANSPORT_RE = ^audit_[^.]+\.report\.md$` and argues every docs audit basename has dots, but also says `_collected_path` must refuse `audit_f.plan.audit.v8.report.md`. That basename cannot match the dot-free transport regex, so the proposed single-source import cannot make the removal mutant bite; adding a separate rejection would contradict the stated single-source grammar. Resolve whether AC-1.6 is a no-op defensive assertion or an additional feature/surface prohibition, then align the plan/spec/tests/mutation spec.

## Should-fix
- The FR-2 requirements line omits the `forced=1` output promised by AC-2.5/AC-2.6a — the plan mentions `--force`, but the machine-readable collector contract it tells implementers to build only lists `COLLECT: OK|MISSING|CONFLICT path= delivered=`, which makes the forced-output field easy to miss.

## Nit
- The Scope bullet says `_copy_collected_report` “stops clobbering differing content,” while Architecture later says `audit-cycle` keeps `overwrite=True`; qualify the Scope wording so it is clear the no-clobber rule is CLI/default-false behavior, not a change to audit-cycle redispatch semantics.
