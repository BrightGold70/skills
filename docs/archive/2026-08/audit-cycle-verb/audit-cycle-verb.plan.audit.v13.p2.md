## Summary
The plan is highly rigorous and thoroughly addresses the functional requirements, particularly in its deep analysis of testing connections and process boundaries. Axis C reconciliation shows one requirement (FR-4) restated in a way that creates a functional gap, dropping a critical mitigation specified in the Spec.

| Requirement | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | restated |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |
| FR-7 | implemented-as-written |
| FR-8 | implemented-as-written |
| FR-9 | implemented-as-written |
| FR-10 | implemented-as-written |

## Must-fix
- FR-4 is restated (narrower) — The Plan's collection logic omits the `.done` marker check.
  - *Spec AC-4.1*: "non-empty **and** `<report-path>.done` exists → `delivered=report-file`, no wait at all; anything else — absent, empty, or non-empty with no `.done` — → `h_mad_report_wait.py`"
  - *Plan wording*: "test the report path directly. Non-empty → `delivered=report-file`, no wait at all... Empty or absent → `report_wait`..."
  - *Why it breaks*: The Plan drops the `.done` marker requirement, falling back to a naive "non-empty" check. The Spec explicitly requires `.done` to prevent gating a torn write caught mid-flush; the Plan's logic would accept the truncated report on size alone.
- Missing CLI signature for `h_mad_audit_cycle.py` (Axis A gap) — The Plan specifies the exact CLI signature for the `audit-cycle` shell verb, but completely omits the signature/contract for the new Python helper script it introduces.
  - *Why it breaks*: The shell→helper boundary is the load-bearing process boundary that owns "collection, gating and reporting." The helper must receive context (`--feature`, `--phase`, `--cycle`), paths (reports, `--out`), and aggregate state (like worst `size_status=` and `--halt-reason` for no-pass mode). Defining this internal contract is required for a complete plan to ensure the implementation is not left TBD and is type-consistent across the boundary.

## Should-fix
None

## Nit
None
