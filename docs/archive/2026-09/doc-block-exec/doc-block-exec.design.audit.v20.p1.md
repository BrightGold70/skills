## Summary
The design and implementation plan are exceptionally rigorous, correctly handling complex edge cases around subprocess lifecycle, stream truncation, timeout bounding, and file descriptor reservation. The split between `extract` and `select` resolves prior API contradictions, and all base invariants are strictly satisfied. The document thoughtfully specifies its testing strategy with precise fault injections and explicitly bounds its scope.

## Must-fix
None

## Should-fix
None

## Nit
None
