## Summary
The design perfectly implements the plan and strictly adheres to the specification. It is a highly robust, secure, and thoughtfully orchestrated design that complies with all base and project invariants. The approach to error handling (e.g., distinguishing operational errors from cannot-judge verdicts) and invariant testing (especially using differential assertions for `premise_items` and testing shell-level guards) is excellent.

| AC | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-1.4 | implemented-as-written |
| AC-2.1 | implemented-as-written |
| AC-2.2 | implemented-as-written |
| AC-2.3 | implemented-as-written |
| AC-2.4 | implemented-as-written |
| AC-2.5 | implemented-as-written |
| AC-3.1 | implemented-as-written |
| AC-3.2 | implemented-as-written |
| AC-3.3 | implemented-as-written |
| AC-3.3b | implemented-as-written |
| AC-3.4 | implemented-as-written |
| AC-3.5 | implemented-as-written |
| AC-4.1 | implemented-as-written |
| AC-4.1b | implemented-as-written |
| AC-4.2 | implemented-as-written |
| AC-4.3 | implemented-as-written |
| AC-4.4 | implemented-as-written |
| AC-4.4b | implemented-as-written |
| AC-4.5 | implemented-as-written |
| AC-4.6 | implemented-as-written |
| AC-5.1 | implemented-as-written |
| AC-5.2 | implemented-as-written |
| AC-5.3 | implemented-as-written |
| AC-5.4 | implemented-as-written |
| AC-5.5 | implemented-as-written |
| AC-5.6 | implemented-as-written |
| AC-5.7 | implemented-as-written |
| AC-6.1 | implemented-as-written |
| AC-6.2 | implemented-as-written |
| AC-6.3 | implemented-as-written |
| AC-6.4 | implemented-as-written |
| AC-6.4b | implemented-as-written |
| AC-7.1 | implemented-as-written |
| AC-7.2 | implemented-as-written |
| AC-7.3 | implemented-as-written |
| AC-7.4 | implemented-as-written |
| AC-7.5 | implemented-as-written |
| AC-8.1 | implemented-as-written |
| AC-8.2 | implemented-as-written |
| AC-8.3 | implemented-as-written |
| AC-8.4 | implemented-as-written |
| AC-9.1 | implemented-as-written |
| AC-9.2 | implemented-as-written |
| AC-9.3 | implemented-as-written |
| AC-9.4 | implemented-as-written |
| AC-9.5 | implemented-as-written |
| AC-10.1 | implemented-as-written |
| AC-10.2 | implemented-as-written |
| AC-10.2b | implemented-as-written |
| AC-10.2c | implemented-as-written |
| AC-10.3 | implemented-as-written |
| AC-10.4 | implemented-as-written |
| AC-10.5 | implemented-as-written |
| AC-10.5b | implemented-as-written |

## Must-fix
None

## Should-fix
None

## Nit
- In the "Detailed Design" section, the heading `### Shell verb (hmad-dispatch.sh, new audit-cycle) case)` contains an unmatched closing parenthesis. It should be `new audit-cycle case)` or similar.
