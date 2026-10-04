## Summary
The design is exceptionally rigorous, correctly routing logs to stderr to avoid stdout corruption and fixing the `$scoped` candidate pool inconsistency from the plan. It correctly covers all Acceptance Criteria from the spec without any omissions or unauthorized narrowings, as mapped below.

| Spec AC | Classification |
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
None

## Should-fix
- Bash variable scope gotcha — The mandated call form `if out="$(_orca_tail_sig "$h")"; then` creates a global variable `out`. If an implementer attempts to practice clean scoping by writing `if local out="$(_orca_tail_sig "$h")"; then`, the `local` command will mask the command substitution's exit code (always exiting 0). This would silently break the error handling and violate FR-4. Recommend advising the implementer to declare `local out` on its own line preceding the `if` statement.

## Nit
- Exit code semantics — The API description states `rc 1 = read failed/unreadable`. Because `hmad-dispatch run --timeout` is used, a timeout will return `124` instead of `1`. The implementation safely treats any non-zero exit as a failure, but the doc comment technically misstates the timeout exit code.
