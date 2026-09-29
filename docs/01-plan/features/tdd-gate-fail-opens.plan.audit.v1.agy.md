## Summary
Evidence: 6 files opened, 8 greps/commands run.
The plan correctly incorporates all spec requirements and operator decisions, ensuring all Acceptance Criteria are assigned to implementation tasks without any narrowing. However, several behavioral premises violate the base invariant by omitting the exact, inline, runnable commands used to produce them (relying on deleted scratch scripts, prose descriptions of greps, or English instructions). Axis C is clean with all ACs implemented as written.

| AC | Classification |
|---|---|
| AC-1.1 to AC-1.10 | implemented-as-written |
| AC-2.1 to AC-2.5 | implemented-as-written |
| AC-3.1 to AC-3.6 | implemented-as-written |
| AC-4.1 to AC-4.7 | implemented-as-written |
| AC-5.1 to AC-5.5 | implemented-as-written |
| AC-6.1 to AC-6.3 | implemented-as-written |
| AC-7.1 | implemented-as-written |

## Must-fix
- Behavioral premises lack exact runnable commands — Several behavioral premises describe their observations but omit the inline, runnable command that produced them (or admit the script was deleted), violating the base invariant "Behavioural premises carry their command". This applies to the deleted scratch scripts in PD-1 and the verified premises, the English descriptions of `git grep` for test modules and helper symbols, the Python logic described for counting candidate markers, and the instruction to "read its final assertion".
  class: measurement
  quote: # Plan: tdd-gate-fail-opens › `The rest came from a scratch script that built the fixture in a tempfile.TemporaryDirectory and was deleted after the run.`

## Should-fix
None

## Nit
None
