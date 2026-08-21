## Summary
The design correctly incorporates all requirements from the spec, mapping them explicitly into a robust boundary between shell (assembly/dispatch) and Python (collection/gating). All Spec ACs have been implemented as written with no absent or restated items. However, there is a clear internal contradiction in the Test Strategy regarding the responsibilities of `premise_items` and `gate()` which was left over from a previous revision.

| Spec AC | Classification | Spec AC | Classification |
|---|---|---|---|
| AC-1.1 | implemented-as-written | AC-5.3 | implemented-as-written |
| AC-1.2 | implemented-as-written | AC-5.4 | implemented-as-written |
| AC-1.3 | implemented-as-written | AC-5.5 | implemented-as-written |
| AC-1.4 | implemented-as-written | AC-5.6 | implemented-as-written |
| AC-2.1 | implemented-as-written | AC-6.1 | implemented-as-written |
| AC-2.2 | implemented-as-written | AC-6.2 | implemented-as-written |
| AC-2.3 | implemented-as-written | AC-6.3 | implemented-as-written |
| AC-2.4 | implemented-as-written | AC-6.4 | implemented-as-written |
| AC-2.5 | implemented-as-written | AC-6.4b | implemented-as-written |
| AC-3.1 | implemented-as-written | AC-7.1 | implemented-as-written |
| AC-3.2 | implemented-as-written | AC-7.2 | implemented-as-written |
| AC-3.3 | implemented-as-written | AC-7.3 | implemented-as-written |
| AC-3.3b| implemented-as-written | AC-7.4 | implemented-as-written |
| AC-3.4 | implemented-as-written | AC-7.5 | implemented-as-written |
| AC-3.5 | implemented-as-written | AC-8.1 | implemented-as-written |
| AC-4.1 | implemented-as-written | AC-8.2 | implemented-as-written |
| AC-4.1b| implemented-as-written | AC-8.3 | implemented-as-written |
| AC-4.2 | implemented-as-written | AC-8.4 | implemented-as-written |
| AC-4.3 | implemented-as-written | AC-9.1 | implemented-as-written |
| AC-4.4 | implemented-as-written | AC-9.2 | implemented-as-written |
| AC-4.4b| implemented-as-written | AC-9.3 | implemented-as-written |
| AC-4.5 | implemented-as-written | AC-9.4 | implemented-as-written |
| AC-4.6 | implemented-as-written | AC-9.5 | implemented-as-written |
| AC-5.1 | implemented-as-written | AC-10.1| implemented-as-written |
| AC-5.2 | implemented-as-written | AC-10.2| implemented-as-written |
| AC-10.2b| implemented-as-written | AC-10.4| implemented-as-written |
| AC-10.2c| implemented-as-written | AC-10.5| implemented-as-written |
| AC-10.3 | implemented-as-written | AC-10.5b| implemented-as-written |

## Must-fix
- Contradiction regarding `premise_items` parsing — The "Detailed Design" section states that following the v1.9 fix, extraction was moved entirely to `gate()` and that "`premise_items` does no parsing at all: it consumes those findings and only formats each entry". However, the "Test Strategy" contradicts this by explicitly stating that `test_premise_items_match_gate_count` exists because "`premise_items` deliberately mirrors the gate's prose fall-back, which makes it a reimplementation". This breaks Axis A (Contradictions inside the doc). The test should be testing the in-process read inside `gate()`, not `premise_items`.

## Should-fix
None

## Nit
None
