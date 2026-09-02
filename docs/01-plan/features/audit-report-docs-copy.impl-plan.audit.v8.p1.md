AUDIT-audit-report-docs-copy-impl-plan-v8-BEGIN
## Summary
The implementation plan provides a robust and well-tested design for adding the codex audit leg collection and gate refusal logic. However, there is a critical gap in the CLI's error handling for command-line parsing failures. The proposed outer try/except block does not catch the `SystemExit` exception raised by `argparse`, which would allow it to bypass the marker print and violate the Marker discipline invariant.

## Must-fix
- CLI `SystemExit` unhandled by outer try — Task 3 and D2 state that `argparse`'s `SystemExit` is caught and prints a `usage_error` marker, but the pseudo-code's outer try block only catches `(OperationalError, OSError, ValueError)`. Since `SystemExit` inherits from `BaseException`, it will escape the handler unhandled, terminating the process without printing the required `[H-MAD]` marker and violating the Marker discipline invariant. Add an explicit `except SystemExit:` clause to the outer try, or wrap the `argparse` call in its own handler.

## Should-fix
None

## Nit
None
AUDIT-audit-report-docs-copy-impl-plan-v8-END
