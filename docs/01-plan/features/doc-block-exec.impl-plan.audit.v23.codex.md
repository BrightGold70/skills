## Summary
Task sequencing, wiring mutations, and the paired-document APIs are otherwise concrete and mutually aligned. Task 4 nevertheless contains a contradictory output-rendering requirement that cannot be implemented as written.

## Must-fix
- Task 4 says all 14 verdict-field values and all 11 detail values must pass through `_field`, while defining `_field` as quote-producing `json.dumps(...)`; in the next paragraph it requires seven of those same values (`rc`, `blocks`, `count`, `keys`, `shell`, `stage`, `reason`) to remain bare — an implementation cannot satisfy both the all-25/_field requirement and the required bare grammar. Make the trusted bare-field exemption explicit in the universal-renderer wording (and its historical restatement), reserving `_field` for the other 18 values; otherwise the plan contradicts its own line grammar and the paired design/plan.

## Should-fix
None

## Nit
- Task 4 says `DETAIL_KEYS` lets tests “enumerate all three” immediately after defining an 11-item tuple; correct the stale count for clarity.
