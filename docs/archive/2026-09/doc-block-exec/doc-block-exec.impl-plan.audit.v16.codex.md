## Summary
The plan is unusually concrete, but it still contains a cross-document exception-contract contradiction and leaves an explicitly promised operational-error path without a mapping or discriminator. Its RED sections describe expected failures but do not require an observed RED run before each task is implemented.

## Must-fix
- `StreamPathUnwritable` has incompatible public constructors: this implementation plan defines `__init__(self, leftover: str | None = None)` (and requires zero-argument construction), while the paired design's error table specifies `StreamPathUnwritable(err, leftover=None)`. The reservation paths never supply an `err`, so following the design makes ordinary refusals/type-walk tests fail; following the plan leaves the design false. Choose one signature and update all raise/render/test descriptions together.
- Task 3 promises that helper I/O failures are converted to `LaunchFailed`, but calls `proc.poll()` on both timeout/collect recovery paths without an `OSError` mapping, precedence rule, or mutation-backed test. A `Popen.poll()` failure can therefore escape past cleanup as a traceback, contradicting the stated taxonomy and the no-own-`OSError` escape guarantee. Specify its pending-outcome behavior (including collect-vs-timeout precedence) and add a discriminating instance-wrapper test/mutation.

## Should-fix
- The task RED splits are assertions about what should fail, not a required, bounded RED execution and recorded result before each task's implementation. Add a per-task `hmad-dispatch run --timeout ... -- pytest ...` RED gate (and the expected named failures) before writing production code, so the required test-discrimination evidence is actually collected rather than inferred from the later mutation run.

## Nit
None
