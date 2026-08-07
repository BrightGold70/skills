AUDIT-regression-provenance-ledger-design-v6-BEGIN
## Summary
The design provides a robust, testable architecture with a pure core and thin I/O shells, correctly resolving the subprocess scaling issue. However, it contains a critical gap in how static AST nodes are mapped to file-based boundary globs, and fails to account for deleted files crashing the AST parser. It also misses an invariant-mandated probe for a load-bearing `git diff` assumption.

Axis C Spec Reconciliation:
| AC | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-1.4 | implemented-as-written |
| AC-2.1 | restated |
| AC-2.2 | implemented-as-written |
| AC-2.3 | implemented-as-written |
| AC-2.4 | implemented-as-written |
| AC-2.5 | implemented-as-written |
| AC-3.1 | implemented-as-written |
| AC-3.2 | implemented-as-written |
| AC-3.3 | implemented-as-written |
| AC-3.4 | implemented-as-written |
| AC-4.1 | implemented-as-written |
| AC-4.2 | restated |
| AC-4.3 | implemented-as-written |
| AC-4.4 | implemented-as-written |
| AC-5.1 | implemented-as-written |
| AC-5.2 | implemented-as-written |
| AC-5.3 | implemented-as-written |
| AC-5.4 | implemented-as-written |
| AC-6.1 | implemented-as-written |
| AC-6.2 | implemented-as-written |
| AC-6.3 | implemented-as-written |

## Must-fix
- **Axis A (Gap - AST mapping to boundaries undefined)** — The design specifies boundaries as file globs (e.g., `{"h-mad/scripts/*": "scripts"}`) but uses `ast` to extract static import names and call roots (e.g., `Import(name='h_mad_wire_registry')`). It states "the target resolves to a different boundary" without providing any mechanism for how a Python module namespace (with dots and underscores) maps to a file path (with slashes and hyphens) so it can be evaluated against the glob. Without semantic analysis or a defined heuristic mapping, the glob-based boundary config cannot evaluate AST targets.
- **Axis A (Gap - Deleted files crash the AST challenge)** — The changed-file set for the AST challenge is derived from `git diff --name-only <base> HEAD -- '*.py'`, which includes files that were deleted in HEAD. The design states it parses "the BASE and HEAD versions" for each changed file. Attempting to read and parse the HEAD version of a deleted file will raise a `FileNotFoundError` (or equivalent), crashing the verifier at 5f. The diff must be filtered (e.g., `--diff-filter=AM`) or deletions must be gracefully skipped.
- **Axis B (Assumption verification / Wrapper-runtime reconciliation)** — The design assumes `git diff --name-only` emits repo-relative paths to support the load-bearing file-matching normalization logic. However, this assumption is asserted without evidence; unlike the `pytest` and `git show` behaviors, there is no cited throwaway command output proving this behavior against the external runtime.
- **Axis C (AC-2.1 restated)** — Spec: `WIREREG: PASS|FAIL registered=N verified=K broken=J missing=M`. Design: `WIREREG: PASS registered=N verified=K broken=0 missing=0 unverified_renames=0 exit 0`. The design is wider/additive, extending the mandatory output grammar with an `unverified_renames` counter.
- **Axis C (AC-4.2 restated)** — Spec: "...and for superseded the feature that supersedes it." Design Data Model: Requires `removed_by_feature` for *all* tombstones (including `pinned-a-defect` and `renamed`), not just `superseded`. The design is stricter/narrower.

## Should-fix
None

## Nit
- If a file existed at BASE as a non-Python file (e.g. a shell script) and was renamed to `.py` in HEAD, parsing the BASE version with `ast` will raise a `SyntaxError`. Gracefully catching parse errors on historical files would prevent unexpected challenge crashes.
AUDIT-regression-provenance-ledger-design-v6-END
