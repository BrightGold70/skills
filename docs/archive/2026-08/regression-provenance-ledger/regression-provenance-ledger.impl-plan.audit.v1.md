## Summary
The implementation plan is highly detailed, rigorously traces the design's invariants, and structures the work cleanly bottom-up. However, there are a few gaps regarding write-time validation for `renamed` tombstones and missing token/halt grammar for the `undeclared removals` and `unverified renames` failure modes, which would leave the orchestrator unable to legibly halt on them.

## Must-fix
- **Missing write-time validation AC for `successor_pin` (Gap)** — Task 1 correctly mandates write-time rejection for tombstones missing `removal_provenance` (AC-4.2a), `superseding_feature` (AC-4.2b), and `removed_by_feature` (AC-4.2c). However, it omits an AC to reject a `renamed` tombstone that is missing a `successor_pin`, leaving this schema requirement (defined in the Design) unvalidated at write time.
- **Undeclared removals missing from token grammar (Contradiction)** — Task 3 / AC-4.1 states that an undeclared removal yields `FAIL`. However, the `WIREREG:` token grammar defined in Task 4 does not contain an `undeclared_removals=U` count. Per the Design's cycle 6 rule ("a count that drives a FAIL must be in the grammar"), this count MUST be included so a `FAIL` verdict with all other error counts at 0 is structurally sound and legible.
- **Missing halt reasons for FAIL conditions (Gap)** — Task 4 explicitly lists exactly three halt reasons (`wire_regression:<id>`, `wire_pin_missing:<id>`, `registry_untracked`). It provides no `[H-MAD]` halt reason for an `undeclared removal` (AC-4.1) or an `unverified_rename` (AC-4.3b). Since verdicts exit 0, these `FAIL` conditions must map to an explicit orchestrator halt marker to comply with the Marker discipline invariant.

## Should-fix
- **`verify()` signature lacks `repo: Path` (Type consistency)** — Task 4 defines `verify(registry: Path, base: str, rootdir: Path)`, omitting a `repo: Path` argument. However, `verify` must pass `repo` down to `trackedness(path, repo)` and `load_base(sha, path, repo)`. It should either take `repo: Path` in its signature or explicitly construct it from `rootdir`.
- **Doc test mutation wiring omitted (Gap)** — Task 7 introduces doc tests to pin the `SKILL.md` contract, but omits the explicit `h_mad_mutation_harness.py` wiring required to verify them. The Design's Invariant Compliance section dictates that "Every new guard is mutated to its permissive value, including the doc guards... via h_mad_mutation_harness.py".

## Nit
- **Task 2 `run_pins` return type phrasing** — The description states `run_pins()` returns `(verified=0, broken=0)` (which implies raw counts), but the signature correctly returns `tuple[list, list]`. This is semantically fine since counts can be derived via `len()`, but the phrasing slightly mismatches the code structure.
