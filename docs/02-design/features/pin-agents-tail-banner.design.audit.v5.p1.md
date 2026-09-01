## Summary
The design correctly incorporates the structural fixes from previous audits, particularly placing the new tail-evidence pass after Pass 2 without being gated by `n == 0` or `lsof`. It firmly establishes the exact `hmad-dispatch run --timeout` command, the load-bearing `--cursor 0`, and the stdout capture contract for the helper. Axis C verification confirms all 13 Acceptance Criteria from the Spec are implemented as written. However, there is a documentation-update gap where a promised `SKILL.md` update is missing from the component table and implementation steps.

| AC | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-2.1 | implemented-as-written |
| AC-2.2 | implemented-as-written |
| AC-2.3 | implemented-as-written |
| AC-3.1 | implemented-as-written |
| AC-3.2 | implemented-as-written |
| AC-3.3 | implemented-as-written |
| AC-4.1 | implemented-as-written |
| AC-4.2 | implemented-as-written |
| AC-4.3 | implemented-as-written |
| AC-5.1 | implemented-as-written |

## Must-fix
- Missing `SKILL.md` from Components and Implementation Order — The "Invariant Compliance" section promises that the `_orca_find` prose in `SKILL.md` is updated to say "four-plus-one passes", but `h-mad/SKILL.md` is absent from the "Components Changed / Added" table and the "Implementation Order". An implementer following the steps will miss this required documentation update.

## Should-fix
None

## Nit
- Inaccurate exit code documented for `_orca_tail_sig` — The API block states `rc 1 = read failed/unreadable`, but if the time-bounder fires, `hmad-dispatch run --timeout` exits 124. Documenting this as "non-zero = read failed/unreadable/timeout" is safer and prevents confusing a debugger expecting exactly `1`.
