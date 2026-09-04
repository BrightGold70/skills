## Summary
The design document is robust and highly detailed, particularly regarding exception mappings, timeout handlers, and atomic file creation semantics. However, it contains two notable self-contradictions: it explicitly forbids numbering the fault-injection seams to avoid ordinal drift yet assigns numbers to three of them in the detailed design, and it refers to the test_suite_floor_holds tuple size interchangeably as seven and nine.

## Must-fix
- The document explicitly forbids numbering fault-injection seams to prevent ordinal drift, but then assigns ordinal numbers to them anyway (e.g., the fifth named injection) — this contradicts its own stated anti-drift rule and creates confusion about the canonical seam count.
  quote: doc-block-exec.md › `Both go through the **fifth named injection**`

- The Components table describes the floor-tuple of node IDs as having seven nodes, but Task 5 and the Test Plan accurately size it at nine nodes — this is a numerical contradiction that misstates the exact size of the test suite floor.
  quote: doc-block-exec.md › `one of the seven floor-tuple node IDs`

## Should-fix
None

## Nit
None
