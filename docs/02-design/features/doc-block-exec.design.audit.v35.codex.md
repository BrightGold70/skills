## Summary
The design covers all 49 specification acceptance criteria as written, and the cited suite baseline re-derives to 2747 collected tests. However, its full CommonMark fence-state rule is independently specified for `extract` and `fence_aware_end`, which leaves a second single-source gap inside the proposed helper.

| Spec ACs | Classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-1.8, AC-1.9 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.7, AC-2.8 | implemented-as-written |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7, AC-3.8, AC-3.9, AC-3.10, AC-3.11, AC-3.12, AC-3.13, AC-3.14 | implemented-as-written |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | implemented-as-written |

## Must-fix
- The full fence-state grammar is defined separately in `extract` (candidate scanning) and `fence_aware_end` (section bounding), while only `docsections → fence_aware_end` is made authoritative — the shared rule covers marker kind, run length, indentation, valid closers, and prefix state; the design neither requires both surfaces to call one private scanner/state transition nor specifies a parity test. A future change can therefore make extraction accept a quoted tag or end a section differently from the delegated bounder, violating the base Single-source contract despite AC-1.8’s cross-module delegation. Require a shared internal fence parser/state transition used by both functions (and mutation anchors against it), or add a construct-complete equivalence guard across both consumers.

## Should-fix
None

## Nit
None
