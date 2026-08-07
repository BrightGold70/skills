## Summary
The design provides a robust, pure-core verifier that elegantly solves the empty-selection problem by partitioning pins before running them, and it correctly adopts the base invariants (J18 live-file protection, two-way connection enforcement). However, the design omits the technical mechanism for the FR-5 diff-parsing shape challenge, and it fails to specify the runtime read-back required by the Mutation Verification invariant inside its architecture description.

| Spec ID | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-1.4 | implemented-as-written |
| AC-2.1 | implemented-as-written |
| AC-2.2 | implemented-as-written |
| AC-2.3 | implemented-as-written |
| AC-2.4 | implemented-as-written |
| AC-2.5 | implemented-as-written |
| AC-3.1 | implemented-as-written |
| AC-3.2 | implemented-as-written |
| AC-3.3 | implemented-as-written |
| AC-3.4 | implemented-as-written |
| AC-4.1 | implemented-as-written |
| AC-4.2 | implemented-as-written |
| AC-4.3 | implemented-as-written |
| AC-4.4 | implemented-as-written |
| AC-5.1 | implemented-as-written |
| AC-5.2 | implemented-as-written |
| AC-5.3 | implemented-as-written |
| AC-5.4 | implemented-as-written |
| AC-6.1 | implemented-as-written |
| AC-6.2 | implemented-as-written |
| AC-6.3 | implemented-as-written |

## Must-fix
- Axis A (Gap): Missing technical mechanism for FR-5 (Shape challenge) — The design includes the FR-5 shape challenge in the Test Plan and Implementation Order but completely omits the architectural mechanism for achieving it. Detecting a "call crossing a declared module boundary" from a diff is non-trivial and requires a concrete design (e.g., regex against `git diff`, AST parsing, and how boundaries are configured/mapped) before it can be implemented.
- Axis B (Mutation verification): Missing runtime read-back step — The Test Plan promises "registration verified by read-back", but the architecture for `h_mad_wire_pin_gate.main()` / `registry.register()` omits the actual runtime read-back step. The base invariant requires the production code that mutates state to re-read it to prove success. The design must explicitly state that the writer performs this read-back at runtime.

## Should-fix
- Axis A (Gap): `successor_pin` execution flow — The design states a `renamed` tombstone's `successor_pin` must "pass in the run", but `partition()` is only described as separating "records" into resolving/missing. The design should clarify that `partition()` explicitly extracts `successor_pin`s from tombstones and injects them into the `resolving` set so the second subprocess actually executes them.
- Axis A (Unstated assumption): Distinguishing `git show` errors — To fulfill "A BASE at which the file did not exist yields an empty base set" while keeping an invalid `--base` as an exit 2, the implementation will need to parse `git show`'s stderr because both cases exit 128. The design should note this parsing requirement to prevent an invalid SHA from silently yielding an empty base set.

## Nit
None
