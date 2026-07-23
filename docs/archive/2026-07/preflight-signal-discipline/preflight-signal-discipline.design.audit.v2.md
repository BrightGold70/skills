AUDIT-preflight-signal-discipline-design-v2-BEGIN
## Summary
The revised design successfully addresses the Cycle 1 Must-fix finding. By utilizing a static, non-existent path in the system temporary directory and defensively guarding it with `atexit`, the design avoids directory leaks while still effectively isolating the test suite from the repository's pin file. All ACs from the specification remain implemented as written, and the design remains strictly compliant with all base and project invariants.

| Acceptance Criterion | Status |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-1.4 | implemented-as-written |
| AC-1.5 | implemented-as-written |
| AC-1.6 | implemented-as-written |
| AC-2.1 | implemented-as-written |
| AC-2.2 | implemented-as-written |
| AC-2.3 | implemented-as-written |
| AC-2.4 | implemented-as-written |
| AC-3.1 | implemented-as-written |
| AC-3.2 | implemented-as-written |
| AC-3.3 | implemented-as-written |
| AC-4.1 | implemented-as-written |
| AC-4.2 | implemented-as-written |
| AC-4.3 | implemented-as-written |
| AC-4.4 | implemented-as-written |
| AC-5.1 | implemented-as-written |
| AC-5.2 | implemented-as-written |
| AC-6.1 | implemented-as-written |
| AC-6.2 | implemented-as-written |
| AC-6.3 | implemented-as-written |
| AC-6.4 | implemented-as-written |
| AC-6.5 | implemented-as-written |
| AC-7.1 | implemented-as-written |
| AC-7.2 | implemented-as-written |

## Must-fix
None

## Should-fix
None

## Nit
- While the static `_NO_PIN_FILE` path (`hmad-tests-absent-orca-pins.env` in the temp dir) avoids the directory leak, its static nature means that if two test suites run simultaneously on the same machine, and a rogue test in one suite accidentally creates the file, it could contaminate the concurrent run. Given that this is a defensive edge case, it does not block the design, but using a unique name (e.g., appending a PID or UUID) would make it fully parallel-safe.
AUDIT-preflight-signal-discipline-design-v2-END
