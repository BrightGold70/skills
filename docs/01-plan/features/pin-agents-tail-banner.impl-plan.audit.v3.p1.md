## Summary
The implementation plan translates the design carefully into shell scripts and test assertions, rigorously maintaining state boundaries and extraction rules. However, the Python regex introduced in AC-2.7 to prevent `timeout` commands contains a syntax blind spot that permits the forbidden use case to pass undetected. Fixing this ensures full invariant compliance and test discrimination.

## Must-fix
- AC-2.7's `_INVOKE` regex misses bash keywords — The regex `re.compile(r"(?:^|[;|&(]|\$\()\s*g?timeout\s")` requires `timeout` to be preceded by specific non-alphanumeric characters or start-of-string, completely missing `if timeout...`, `then timeout...`, or `! timeout...`. This violates the **Portable time bounds** and **Test discrimination** invariants, as the exact prohibited behaviour (`if timeout 2 orca...`) would pass the test vacuously. Fix: Use a whitespace-aware boundary check, e.g., `r"(?:^|[\s;|&()!])g?timeout(?:$|\s)"`.

## Should-fix
None

## Nit
- T1 `_orca_read_dir` encoding: `write_text(text)` lacks an explicit `encoding="utf-8"`, relying on the environment's default encoding.
- T3 obsolete syntax: `head -1` is obsolete; POSIX prefers `head -n 1`.
