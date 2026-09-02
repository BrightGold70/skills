## Summary
The design provides a robust, zero-dependency Python implementation that comprehensively addresses all functional requirements and bounds. Spec reconciliation reveals no gaps in coverage; every Acceptance Criterion from FR-1 through FR-6 is fully supported without narrowing. However, the design explicitly introduces a duplicated markdown parsing rule without the mandatory differential test required by the base invariants.

| Spec | Design Classification | Notes |
|---|---|---|
| AC-1.1 to AC-6.6 | `implemented-as-written` | All acceptance criteria are fully covered by the design. |

## Must-fix
- Single-source contract violation — The design explicitly introduces an independent re-implementation of the markdown fence and section bounder (duplicating `_fence_aware_end` from `tests/docsections.py`) because "unifying the two is explicitly out of scope." The "Single-source contract" base invariant forbids independent re-implementations that can silently diverge *unless* they are covered by a test asserting byte-equivalence across surfaces. The design omits this mandatory differential test.

## Should-fix
- Unstated ATX heading assumption — The design specifies that a heading's level is "the count of leading `#`". This assumes ATX-style headings exclusively and would misread Setext-style (underlined) headings. While ATX is the repo convention, this structural assumption should be explicitly documented as a known parser limitation (or verified against the existing `docsections.py` implementation in the differential test) to prevent silent bounds failures.

## Nit
- Ambiguous token serialization for multiple missing substitutions — When `MissingSubstitution(keys)` carries multiple absent keys, the design specifies the verdict line as `SUBST_MISSING key=<k> + missing_key: <k> per key`. It is slightly ambiguous whether the main token's `key=<k>` will contain just the first key or a joined list; specifying that it uses the first key will eliminate any ambiguity for downstream parsers.
