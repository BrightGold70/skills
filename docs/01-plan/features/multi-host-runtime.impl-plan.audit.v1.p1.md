## Summary
The implementation plan has seven blocking gaps in its sequencing, probe contracts, rebase response, and wire verification. The wire-pin parser reports `WIREPIN: PASS tasks=19 wiring=3`, but that check cannot establish the behavioral gaps below. Evidence: 16 files opened, 10 greps run; graft saved ~97,115 tokens in 1 call.

## Must-fix
- The probe sidecar is scheduled after the 5c implementation-plan commit, although the binding design requires it before the design gate clears — this reverses a prerequisite without a design revision and leaves the gate unable to clear under its stated order.
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › The design gate cannot clear under this order until it does.
  quote: docs/01-plan/features/multi-host-runtime.impl-plan.md › sequence directly after the 5c impl-plan commit and before any RED (orchestrator decision).
- Task 0 runs both probes against `BASE_SHA` before Task 1 derives that variable — the first task has no defined SHA, so its required baseline reading cannot be executed in task order. Derive and validate the SHA before Task 0's probe-run step, then keep Task 1's other readings afterward.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.impl-plan.md › It is derived once, in Task 1, as the parent of the sha that
- `seed_coverage.py` specifies one verdict field per entry, yet control C0.4 requires the same `advisor` entry to contribute both a stale and an undeclared count — an implementation following the stated single-valued verdict cannot produce the required control result. Define a multi-finding encoding or per-skill verdict lines and pin it in the control.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.impl-plan.md › SEEDCOV: FAIL entries=22 stale=1 undeclared=1
- The AC-4.6 false-hit branch has no implementation owner: Task 1 permits narrowing an axis or exclusion with a new control, but Task 2 lands fixed checker constants and tests and Task 3 edits only the registry plus tests for added entries. A newly measured false hit therefore cannot be corrected under the task/file contract; assign the checker edit, discriminating control, and affected mutation rows before Task 3 GREEN.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.impl-plan.md › exclusion narrowed with a new control. A false hit is never registered.
- The retirement branch adds a `RETIRED_IDS` reason but leaves `test_registry_branch_samples` parametrized over every seed id, including the retired one — the test has no registry pattern to expand and Task 3's promised GREEN split cannot hold. Specify the retired-id behavior for this sample test and a positive control for the retirement reason.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.impl-plan.md › it retires one, it adds a `RETIRED_IDS` key with the reason, and the Phase-6 record names the
- W3's claimed force-fires are not force-fires of its two `main` to `check` root connections: I1 reverses agy name partitioning and I2 applies that partition to the Claude root. Neither tests that optional agents or agy root checks stay off when the corresponding connection is absent; add one unconditional-fire mutant and a killing negative-path assertion for each root wire.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.impl-plan.md › **Force-fires**: I1 (the name split inverted, killed by
- Task 16 expects arm B to report `links_absent`, although Task 1 halts the entire run until all four links exist — no valid run can reach Task 16 in the stated absent-link state. Make arm B's Task 16 result a real closed-diff PASS, retaining `links_absent` as a separate negative control.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.impl-plan.md › 4. `--arm install-b` → `BYTE-IDENTITY: UNREADABLE reason=links_absent` while the four links are

## Should-fix
- Task 3 publishes fixed 30-RED and 24-GREEN counts while explicitly allowing AC-4.6 to add a registry entry and a branch-sample test node — the published count becomes stale on that authorized path. State counts as formulas from the actual entry set or require a re-derived ledger after the base reading.
  class: measurement
  quote: docs/01-plan/features/multi-host-runtime.impl-plan.md › GREEN, 24 pass: `test_live_registry_and_skill_files_are_clean`,

## Nit
None
