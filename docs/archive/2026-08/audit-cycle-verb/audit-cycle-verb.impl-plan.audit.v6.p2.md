## Summary
The plan is highly rigorous and provides exceptional coverage of connection mutations, correctly handling edge cases like torn writes and isolated passes. However, the in-process read logic in `gate()` violates the Single-source contract by re-implementing the prose fallback, and the assembly parsing block contains a case-sensitivity bug that will silently miss `UNVERIFIED` tokens. Finally, the test for the under-count trap relies solely on a synthetic fixture, missing the requirement to replay against real historical artifacts.

## Must-fix
- Single-source contract violation in `gate()` — The plan explicitly states that `premise_items` "deliberately mirrors the gate's prose fall-back", making it a re-implementation. The test `test_premise_items_match_gate_count` only asserts count equivalence (`len(items) == must`), which is not byte-equivalence. Independent re-implementations that can silently diverge are an Axis B violation. `h_mad_audit_gate.py` must provide a single authoritative function that extracts the items, or the test must assert exact extraction equivalence, not just matching counts.
- Incident replay violation in `test_prose_plus_bullet_not_concatenated` — The concatenated under-count was a specific observed incident (measured 2026-08-20) that motivated the per-pass gating architecture. AC-10.3 specifies testing this using a synthetic fixture (`p1 prose-only finding, p2 one bullet`). The invariant requires replaying fixes for observed incidents against the *real artifacts on disk* that motivated them; synthetic cases alone are a violation.
- Case-sensitivity bug in Step 5 (`hmad-dispatch.sh`) — The token array `${tok[$i]}` is populated by stripping `ASSEMBLE: ` from the output, leaving uppercase tokens like `UNVERIFIED` or `HALT`. The check `case "${tok[$i]}" in *unverified*)` uses lowercase, which will fail to match `UNVERIFIED` because bash `case` statements are case-sensitive by default. This will silently leave `size_status` as `"verified"` on an unverified assembly. Change the pattern to `*UNVERIFIED*`.

## Should-fix
None

## Nit
- Terminology mismatch on Mutation 2 — Removing the token-emptiness guard (`[ -n "${tok[$i]}" ]`) is an output-validation guard mutation, not a "force it to fire unconditionally" connection mutation. For an unconditional connection like the assembly loop, only the "drop" direction is required to certify the connection. The mutation is still valuable for coverage, but labeling it as a connection-force is slightly inaccurate.
