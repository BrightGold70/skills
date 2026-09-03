## Summary
The design provides an exceptionally rigorous, structurally sound implementation for extracting, substituting, and safely executing tagged markdown bash blocks. The architecture for managing process lifetimes, descriptor closures, and timeout races is well-thought-out and comprehensive. A few discrepancies were identified primarily around the test requirements for exception construction and the JSON serialization of dynamic numeric fields.

## Must-fix
- The `StreamPathUnwritable` exception is given a default argument `leftover=None` to make it "constructible with no arguments, as the type-walk tests require", but other exceptions (e.g., `BadInfoString(key)`) have required arguments without defaults — if the type-walk test instantiates all subclasses with no arguments, it will crash with a `TypeError` on the others, meaning either the test must supply dummy arguments or all subclasses must have defaults.
- `_field(value)` must cast numeric values to strings before dumping (`json.dumps(str(value), ensure_ascii=False)`) — the design explicitly promises that helper-produced numbers like `seconds=` and `pgid:` are rendered as double-quoted JSON strings (e.g., `seconds="1.0"`), but calling `json.dumps()` natively on an `int` or `float` returns an unquoted string, which breaks the parsing contract.

## Should-fix
- `StreamPathUnwritable`, `PreambleUnreadable`, and `DocUnreadable` wrap underlying `OSError`s or decode errors but omit the `os_error: <text>` detail line in their verdict output — adding this detail (as is done for `LaunchFailed` and `StreamCloseFailed`) would expose whether a stream failure was due to `EACCES` vs `ENOTDIR`, significantly aiding operational troubleshooting.

## Nit
- The `## Executive Summary` lists `extract / substitute / run_block / main` as the exposed functions; updating this to include `select`, `fence_aware_end`, and `find_heading` would better reflect the complete public API surface declared in `__all__`.
