## Summary
The design correctly incorporates all ACs from the specification, providing a robust execution and cleanup model that carefully balances precedence among exceptions (e.g. `CleanupFailed` wrapping `BlockTimeout` or `LaunchFailed` as its cause). Spec reconciliation is 100% complete and mapped as `implemented-as-written`. However, an internal contradiction in the error handling table misrepresents the `StreamPathsAlias` implementation, which must be corrected to maintain the single source of truth for the codebase's error classification.

| AC | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-1.4 | implemented-as-written |
| AC-1.5 | implemented-as-written |
| AC-1.6 | implemented-as-written |
| AC-1.7 | implemented-as-written |
| AC-1.8 | implemented-as-written |
| AC-1.9 | implemented-as-written |
| AC-2.1 | implemented-as-written |
| AC-2.2 | implemented-as-written |
| AC-2.3 | implemented-as-written |
| AC-2.4 | implemented-as-written |
| AC-2.5 | implemented-as-written |
| AC-2.6 | implemented-as-written |
| AC-2.7 | implemented-as-written |
| AC-3.1 | implemented-as-written |
| AC-3.2 | implemented-as-written |
| AC-3.3 | implemented-as-written |
| AC-3.4 | implemented-as-written |
| AC-3.5 | implemented-as-written |
| AC-3.6 | implemented-as-written |
| AC-3.7 | implemented-as-written |
| AC-3.8 | implemented-as-written |
| AC-3.9 | implemented-as-written |
| AC-3.10 | implemented-as-written |
| AC-3.11 | implemented-as-written |
| AC-3.12 | implemented-as-written |
| AC-3.13 | implemented-as-written |
| AC-3.14 | implemented-as-written |
| AC-4.1 | implemented-as-written |
| AC-4.2 | implemented-as-written |
| AC-4.3 | implemented-as-written |
| AC-4.4 | implemented-as-written |
| AC-4.5 | implemented-as-written |
| AC-4.6 | implemented-as-written |
| AC-5.1 | implemented-as-written |
| AC-5.2 | implemented-as-written |
| AC-5.3 | implemented-as-written |
| AC-5.4 | implemented-as-written |
| AC-5.5 | implemented-as-written |
| AC-5.6 | implemented-as-written |
| AC-6.1 | implemented-as-written |
| AC-6.2 | implemented-as-written |
| AC-6.3 | implemented-as-written |
| AC-6.4 | implemented-as-written |
| AC-6.5 | implemented-as-written |
| AC-6.6 | implemented-as-written |

## Must-fix
- **Axis A (Internal Contradiction)**: The `Error Handling Strategy` table lists `StreamPathsAlias` as `main's pre-check (resolved-path compare)`, which directly contradicts the `Detailed Design` / `Execution` section that correctly states: "Aliasing is judged on the opened descriptors (AC-3.9): once both handles are held, os.fstat on each gives (st_dev, st_ino)... (A string-level pre-check is therefore not needed and is not performed; the earlier resolved-path comparison was both weaker and racy.)" — Update the table to reflect the `fstat` descriptor comparison to prevent implementation drift.

## Should-fix
None

## Nit
- In the `Error Handling Strategy` table, `StreamPathUnwritable` is mapped as `main's pre-check (wraps OSError)`. Since the path is verified by the actual `open(path, "a")` reservation step (which guarantees atomicity over a pre-check `exists()` / `access()` check), consider rephrasing "main's pre-check" to "main's stream reservation" to align perfectly with the `Detailed Design` text.
