AUDIT-exec-path-hardening-impl-plan-v1-BEGIN
## Summary
The implementation plan accurately translates the vast majority of the design's constraints, including the `</dev/null` guards, base64 comment transport, and test assertions. However, there are architectural contradictions regarding the `_exec_stamp` signature that violate the wiring tasks, and a test sequencing error where a negative assertion is placed before its corresponding feature is wired.

## Must-fix
- **Task 4 `_exec_stamp` signature contradicts Task 6 and Design** — Task 4 defines the signature as `# $1=kind, ... $4=selector, $5=current comment, $6=state text`. This explicitly contradicts Task 6 (which states `_exec_stamp calls _exec_wt_target` to obtain these) and the Design (which specifies `_exec_stamp <kind> [rc] [verdict]`). If the stamp takes the target/comment as arguments, it forces the caller to invoke the resolver, breaking encapsulation. Likewise, requiring `$6=state text` forces the caller to format the state, violating the design's mandate that the emitter owns the entire format.
- **Untestable false-positive test in Task 5 (AC-5.6)** — Task 5 asserts that `_exec_run invoked without --heartbeat records zero stamp calls`. Because the actual call to `_exec_stamp beat` inside `_exec_run` is not wired until Task 9 (`wire-heartbeat`), this AC will trivially pass in Task 5 as the call does not exist yet. AC-5.6 must be moved to Task 9 where the heartbeat is wired and the flag's exclusion behavior can be genuinely tested.

## Should-fix
- **Omission of Unconditional-Fire Mutation Anchors** — The design's test plan explicitly requires unconditional-fire mutations to verify the substrate gate (`cmux`) and interval disable (`HMAD_EXEC_HEARTBEAT_SEC=0`). While the plan includes the negative tests for these (AC-4.3, AC-9.3), it omits the `MUTATION:` instructions necessary to enforce that the fall-through behaves correctly when forced, which is required by the `Connection enforcement` invariant.

## Nit
None
AUDIT-exec-path-hardening-impl-plan-v1-END
