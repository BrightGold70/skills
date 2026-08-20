## Summary
The design provides a robust architecture for the `audit-cycle` verb, drawing clear boundaries between the shell orchestration and the Python helper's text parsing. The handling of corner cases, such as the torn write window for `.done` files and the prose fall-back for gating, are thoroughly analyzed and executed safely. However, the design drops critical connection-enforcement tests required by the plan and introduces an internal contradiction regarding which function filters the premise checklist findings.

| Spec AC | Classification |
|---|---|
| AC-1.1 | `implemented-as-written` |
| AC-1.2 | `implemented-as-written` |
| AC-1.3 | `implemented-as-written` |
| AC-1.4 | `implemented-as-written` |
| AC-2.1 | `implemented-as-written` |
| AC-2.2 | `implemented-as-written` |
| AC-2.3 | `implemented-as-written` |
| AC-2.4 | `implemented-as-written` |
| AC-2.5 | `implemented-as-written` |
| AC-3.1 | `implemented-as-written` |
| AC-3.2 | `implemented-as-written` |
| AC-3.3 | `implemented-as-written` |
| AC-3.3b | `implemented-as-written` |
| AC-3.4 | `implemented-as-written` |
| AC-3.5 | `implemented-as-written` |
| AC-4.1 | `implemented-as-written` |
| AC-4.1b | `implemented-as-written` |
| AC-4.2 | `implemented-as-written` |
| AC-4.3 | `implemented-as-written` |
| AC-4.4 | `implemented-as-written` |
| AC-4.4b | `implemented-as-written` |
| AC-4.5 | `implemented-as-written` |
| AC-4.6 | `implemented-as-written` |
| AC-5.1 | `implemented-as-written` |
| AC-5.2 | `implemented-as-written` |
| AC-5.3 | `implemented-as-written` |
| AC-5.4 | `implemented-as-written` |
| AC-5.5 | `implemented-as-written` |
| AC-5.6 | `implemented-as-written` |
| AC-5.7 | `implemented-as-written` |
| AC-6.1 | `implemented-as-written` |
| AC-6.2 | `implemented-as-written` |
| AC-6.3 | `implemented-as-written` |
| AC-6.4 | `implemented-as-written` |
| AC-6.4b | `implemented-as-written` |
| AC-7.1 | `implemented-as-written` |
| AC-7.2 | `implemented-as-written` |
| AC-7.3 | `implemented-as-written` |
| AC-7.4 | `implemented-as-written` |
| AC-7.5 | `implemented-as-written` |
| AC-8.1 | `implemented-as-written` |
| AC-8.2 | `implemented-as-written` |
| AC-8.3 | `implemented-as-written` |
| AC-8.4 | `implemented-as-written` |
| AC-9.1 | `implemented-as-written` |
| AC-9.2 | `restated` |
| AC-9.3 | `implemented-as-written` |
| AC-9.4 | `implemented-as-written` |
| AC-9.5 | `implemented-as-written` |
| AC-10.1 | `implemented-as-written` |
| AC-10.2 | `implemented-as-written` |
| AC-10.2b | `implemented-as-written` |
| AC-10.2c | `implemented-as-written` |
| AC-10.3 | `implemented-as-written` |
| AC-10.4 | `implemented-as-written` |
| AC-10.5 | `implemented-as-written` |
| AC-10.5b | `implemented-as-written` |

## Must-fix
- Missing Connection Enforcement tests (Axis A / Axis B) — The Design drops three core positive tests that the Plan explicitly required to anchor connection mutations: `passes=2 yields two distinct dispatches` (anchoring the `exec agy` connection), `FAIL in either pass fails the cycle` (anchoring the `h_mad_audit_gate.py` connection), and `a completed cycle emits an AUDITCYCLE: line` (anchoring the shell→helper boundary). Without these tests, the connection mutations defined in the Plan have no failing test to catch their removal, breaking the Connection Enforcement invariant and diverging from the Plan's explicit test requirements.
- Contradictory filtering responsibility for the premise checklist (Axis A) — The design states that `gate()` asserts `len(findings) == must` against the subprocess's count (which inherently excludes acknowledged items), meaning `gate()` MUST filter the findings before returning them in `PassResult.findings`. However, the design also assigns the filtering to `premise_items` ("It filters by `--ack-file`") and gives it an `acknowledged: set[str]` argument. If `gate()` already filtered them to make the count match, `premise_items` has nothing to filter; if `gate()` returned them unfiltered, the `len(findings) == must` assertion would crash on any acknowledged finding. Exactly one of these functions must own the filtering.
- Spec AC-9.2 is `restated` (Axis C) — Spec wording: "The report-file guidance at §6.6 ... is amended to record that the slot was measured empty on 8 of 8 impl-plan cycles, and that the verb therefore always arms the `--out` fallback." Design wording: "§6.6 correction" (in the Components Changed table). The Design narrows this by omitting the explicit requirement to record the "8 of 8 impl-plan cycles" measurement and the rationale for arming the fallback, leaving the nature of the correction undefined.

## Should-fix
None

## Nit
- `test_verb_writes_only_reports` is missing from the Test Plan table, despite being correctly referenced and described in the body text under the "Test Strategy" section.
