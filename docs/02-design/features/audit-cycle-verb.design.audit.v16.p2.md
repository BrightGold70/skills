## Summary
The design perfectly matches the requirements in both the Spec and the Plan. It defines a clean, dual-process architecture where the shell handles process control (assembly, dispatch, reap) and the Python helper encapsulates all text handling and gating logic. Every Acceptance Criterion from the Spec is explicitly satisfied, including edge cases like `GATE: INVALID` handling, torn-write prevention, and delayed-delivery test coverage.

## Must-fix
None

## Should-fix
None

## Nit
- In `Detailed Design -> premise_items`, the text states "premise_items does no parsing at all: it consumes those findings and only formats each entry and attaches its citation." Extracting the `path:line` citation from the finding string technically involves string parsing. The phrasing is slightly informal but clear in context (it means it avoids re-parsing the *document structure*), so this is merely a semantic nit.
