## Summary
The design delivers a robust, well-specified mechanism for executing tagged bash blocks with strict bounds, verified cleanup, and comprehensive timeout race handling. The CLI contract precisely follows the base signal discipline invariants, and the mutation spec mapping is exhaustively detailed. However, the explicitly dictated sequential substitution mechanism introduces the exact silent order dependency the design claims to prevent, and the `docsections.py` migration is missing from the task plan.

## Must-fix
- Sequential `str.replace` creates a silent order-dependency when a substitution's value contains another key — violating the stated design principle ("rather than picking an order... which only moves the surprise"). If `--subst A=B --subst B=C` is applied to text `"A"`, order `A, B` yields text `"C"` with no missing keys; order `B, A` yields `SUBST_MISSING key=B`. The design refuses overlapping keys to prevent order dependency but dictates sequential replacement, creating the exact same failure class. Validation of missing keys must occur on the original block text, and replacements should be simultaneous or order-independent.
- The `docsections.py` migration is missing from the Implementation Order. The Components table and FR-1 specify dropping its duplicate bounder and updating `docsections.json`, but these required steps are not assigned to any of the five tasks.

## Should-fix
None

## Nit
None
