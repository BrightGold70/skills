## Summary
Plan v1.5 (`docs/01-plan/features/tdd-gate-fail-opens.plan.md`) is well-structured and grounds its decisions in reproducible measurements, but it lags behind Spec v1.6 (`docs/01-plan/features/tdd-gate-fail-opens.spec.md`) on two normative requirements in FR-1 and FR-3 (unconditional pre-state refusal when the project root cannot be entered, and pre-walk `.` removal with lexical `..` out of non-symlink directories). It also contains an internal self-contradiction in `§"Implementation Strategy"` over whether an unparseable canonicaliser output in the Claude gate is refused as `judge-error` or `judge-timeout`.

| Spec item | Plan location | Disposition |
|---|---|---|
| FR-1 | G-1, PD-1, T1, T2, T3 | `restated` (omits Spec v1.6 N-1 rule in step 2 dropping `.` components before the prefix walk and taking lexical parent without opening on `..` out of an existing non-symlink directory) |
| FR-2 | G-2, T2, T3, T4 | `implemented-as-written` |
| FR-3 | G-3, PD-1, T1, T2, T3 | `restated` (omits Spec v1.6 D-1/D-2/D-3 unconditional pre-state `judge-error` refusal when the project root cannot be entered, and Spec v1.6 N-1 rule that `..` out of a plain directory is not an arm-2 site) |
| FR-4 | G-4, PD-4, T4 | `implemented-as-written` |
| FR-5 | G-5, PD-2, T5 | `implemented-as-written` |
| FR-6 | G-6, PD-3, T6 | `implemented-as-written` |
| FR-7 | G-7, T8 | `implemented-as-written` |
| FR-8 | G-9, PD-4, T10, T11, T12 | `implemented-as-written` |

## Must-fix
- Plan G-3, PD-1, T2, and T3 restate Spec v1.6 FR-3 by gating all unresolvable/arm-2 root refusals on governing Phase 5 state ("when governed, allowed when not"), omitting Spec v1.6's unconditional pre-state refusal when the project root cannot be entered (D-1/D-2/D-3) — the plan is narrower than the spec on the refusal domain because under the plan an absent, non-directory, or non-traversable (e.g. mode `000`) project root is allowed when ungoverned instead of being refused `judge-error` before any state lookup in both gates regardless of phase or root case spelling.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `when the root is absent, not a directory, or not traversable (no `x`, e.g. mode 000), the state under it cannot be read, so whether the write is governed is unknowable. Both gates then refuse `judge-error` ("project root … cannot be entered") whatever the phase, before any state lookup.`
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `An existing, resolvable root or target component on which the primitive's open (FR-1 step 3) or the listing of the leaf's canonical parent (FR-1 step 4) raises `OSError` is **unresolvable**: refused `judge-error` when governed, allowed when not.`
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `FR-3 refusal (both arms) gated on `_any_phase5_status` ∈ {`active`, `unknown`}`
- Plan T1, G-3, PD-1, and Next Steps item 3 restate Spec v1.6 FR-1 step 2 and FR-3 (N-1) by deferring `.` and `..` lexical collapse to the non-existing remainder and leaving open whether intermediate directories are opened — the plan is narrower than the spec on FR-1 step 2 (omitting the rule that drops `.` components before walking and takes the lexical parent for `..` out of an existing non-symlink directory, which Spec v1.6 notes left `tests/./../src/prod.py` as a fail-open) and broader than the spec on FR-3 arm-2 sites (allowing an `x`-only plain directory exited via `..` to be treated as unresolvable).
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `Walk the target's components from the left, asking the kernel at each prefix (so `..` is taken after the preceding symlink, as the kernel takes it; out of an existing non-symlink directory `..` is its lexical parent, which is not opened; `.` components are dropped from the walk first, so a `.` never absorbs the next `..` — v1.6, N-1).`
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › ``..` out of an existing non-symlink directory takes its lexical parent, which is the kernel's once `.` components are dropped from the walk (a kept `.` made `tests/./../src/prod.py` resolve under `tests/`: a fail-open present before v1.6 and fixed with it), and does not open it, so an `x`-only directory on the way does not make the target unresolvable.`
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `Shared canonicaliser: component walk, F_GETPATH on existing directories, leaf inode match returning **every** entry of the canonical parent that shares the leaf's `(st_dev, st_ino)` (the hard-link contract, below the table: the canonicaliser returns all names and never evaluates an exemption), remainder append + lexical collapse, unresolvable predicate over both FR-3 arms.`
- `§"Implementation Strategy"` contradicts itself on the refusal kind the Claude gate must emit when the single Python canonicaliser call fails or prints an unparseable output: the hard-link contract (and `§"Risks and Mitigation"`) states that an unparseable output is refused as `judge-error` and points to "the fail-closed rule below", but that rule states that the Claude gate refuses `judge-timeout`, violating the spec contract that reserves `judge-timeout` for post-kill test-runner pipe reap failures.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `It must carry any byte a directory entry can hold except NUL (a newline, a space), and a list the gate cannot parse is `judge-error`, never a fallback to the spelled leaf (the fail-closed rule below).`
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `On the Claude side the new Python call must print a line the gate parses, or the gate refuses `judge-timeout`.`
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › ``judge-timeout` means "the runner could not reap the test process's pipes within the grace"; the caller refuses the write and reports it separately from a slow test (`timeout`).`

## Should-fix
- `PD-2` misnames `test_name_map_runs_under_the_budget` (in `h-mad/tests/test_h_mad_tdd_judge.py` and Spec AC-5.2) as `test_name_map_stays_under_the_budget`, disagreeing with both the spec and the plan's own `§"Verified premises"` and `§"Architecture Considerations"`.
  class: measurement
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › ``test_name_map_stays_under_the_budget` calls `judge.judge`, does not unpack, and keeps its assertions (`timeout`, `< 6.0 s`) unchanged.`
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › ``test_name_map_runs_under_the_budget` calls `judge.judge` and does not unpack, so its assertions (kind `timeout`, `< 6.0 s`) are unchanged.`
- `§"Overview"`, `T6`, `T8`, and `§"Success Criteria"` still cite `spec v1.4` (`644f8bf6`) even though Plan v1.5 already cites `spec v1.5` in `PD-4`, `§"Implementation Strategy"`, `§"Risks and Mitigation"`, and `§"Version History"` (and the spec in the repository is at `v1.6`), and `§"Next Steps"` item 1 still refers to the plan itself as `v1.4`.
  class: measurement
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `The spec (`docs/01-plan/features/tdd-gate-fail-opens.spec.md` v1.4 at commit `644f8bf6`; v1.3 at `766860ba`; v1.2 at `e26466a8`; v1.0 and OD-1…OD-5 operator-approved at commit `662b1ce1`; OD-6 folded by the operator 2026-09-29, spec v1.4) fixes WHAT the gates must decide.`
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `1. Operator review of v1.4, the corrective revision after plan audit cycle 2 (the second and last gating round; v1.4 is not re-audited).`

## Nit
None
