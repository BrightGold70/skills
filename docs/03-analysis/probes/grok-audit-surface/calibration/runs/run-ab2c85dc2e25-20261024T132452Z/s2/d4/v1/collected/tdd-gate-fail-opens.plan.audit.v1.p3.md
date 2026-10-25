## Summary

Plan v1.5 addresses FR-2, FR-4, FR-5, FR-6, FR-7 and FR-8 in the spec's form. FR-6 stays implemented-as-written: spec v1.6's D-4 unfixed Codex `M-18 M-14` deny is already the seventh approved key in PD-4, and the current spec's AC-7.1 census is still 21 `(AC-` + 3 `separate mutations` + 1 `in each gate` = 25. FR-1 and FR-3 are narrower than spec v1.6, the numbered task order contradicts the Depends column the plan says is authoritative, and the Claude canonicaliser's parse failure is assigned two kinds.

| FR | Classification |
|---|---|
| FR-1 | restated |
| FR-2 | implemented-as-written |
| FR-3 | restated |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |
| FR-7 | implemented-as-written |
| FR-8 | implemented-as-written |

Evidence: 9 files opened, 12 greps run. Sha-stamped `git` commands were not re-run: this worktree has no `.git`.

## Must-fix

- FR-1 is restated. Spec v1.6 step 2 requires the component walk to drop `.` components before `..` is applied, and to take `..` out of an existing non-symlink directory as that directory's lexical parent without opening it. That is the close of the fail-open in which `tests/./../src/prod.py` resolves under `tests/`. `..` out of a symlink still opens the referent, and spec FR-3 states the same walk is not an arm-2 site. T1 specifies a component walk, `F_GETPATH`, inode names, and lexical collapse of the remainder, and its arm-2 guard treats an `OSError` from opening any existing component as unresolvable. Next Steps still leaves the design to say, per component kind, whether it is opened. A 5e implementer can keep `.` in the walk and open lexical `..`, so the pre-v1.6 allow ships or arm 2 fires on an `x`-only directory the spec leaves resolvable. No task AC schedules this rule.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `remainder append + lexical collapse, unresolvable predicate over both FR-3 arms.`
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `are dropped from the walk first`
- FR-3 is restated. Spec v1.6 requires both gates to refuse `judge-error` when the project root is absent, not a directory, or not traversable (mode 000 is the example), whatever the phase and before any state lookup, including when the root is spelled in a different case from its on-disk name. A root that can be entered but not listed (mode 0311) stays on the governed-only rule, and an absent `CODEX_PROJECT_DIR` is not this case. G-3 and the Requirements line define unresolvable as two arms, refused only when governed. T2 gates that refusal on `_any_phase5_status` being `active` or `unknown`. T3 places it after `_read_state` reports `active` or `unreadable`. Neither task schedules the before-lookup root refuse, so the 5e gates will not implement it.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `Unresolvable has two arms: a dangling symlink, a loop, or a failed resolution`
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `Project root that cannot be entered`
- The numbered sequence and the Depends column cannot both be followed. The plan says both are its own, and that the impl-plan may refine the task list while the order stays here. The table runs T7, then T8, then T9, then T10, T11, T12. T7's adapter re-check is after T12's oracle edit (Depends on T12). T8's acceptance is the per-guard census, and the FR-8 mutations it counts are committed in T10 and T11. T9 requires `COMPARE: PASS softened=7 approved=7`, and two of those seven keys are the FR-8 allows, which exist only after T10–T12. Running the printed order makes T8's floor fail and T9 report fewer than 7 softenings. One order that meets every Depends cell is T0–T6, then T10, T11, T12, T8, T7, T9, with T5 any time before T7.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `the order and the dependencies are this plan's.`
- The Claude canonicaliser's unparseable output has two refusal kinds. The hard-link contract says a name list the gate cannot parse is `judge-error`, and it calls that outcome the fail-closed rule below. That rule says the new Python call must print a line the gate parses or the gate refuses `judge-timeout`. Next Steps repeats `judge-error` for an unparseable list. A name list the gate cannot parse is a line the gate cannot parse, so T3's branch and its test assert different kinds under the two sentences.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `never a fallback to the spelled leaf (the fail-closed rule below).`

## Should-fix

- PD-2 attaches the "calls `judge.judge`, does not unpack, keep `timeout` and `< 6.0 s`" constraint to `test_name_map_stays_under_the_budget`. The verified-premises command in the same plan searches for `def test_name_map_runs_under_the_budget`, and that is the only definition in `h-mad/tests/test_h_mad_tdd_judge.py` (line 572). No test is named `stays`. The preservation note points at a symbol that is not in the tree.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `test_name_map_stays_under_the_budget`
  quote: h-mad/tests/test_h_mad_tdd_judge.py › `def test_name_map_runs_under_the_budget`
- The Requirements compatibility bullet says the spec's named deltas are AC-8.6's two. The spec names the deltas in AC-5.2, AC-5.5 and AC-8.6, and also the verdict changes FR-1 lists. T5 already requires the AC-5.2 six-field unpack, so the Requirements gloss is the sentence that under-lists the sanctioned edits.
  class: measurement
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `which names AC-8.6's two`
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `AC-5.2, AC-5.5 and AC-8.6`

## Nit

- Next Steps item 1 still directs operator review at plan v1.4 and says that revision is not re-audited. T6 still introduces the differential as spec v1.4 FR-6. Version History v1.5 says nothing else changes. The normative spec text is v1.6.
- The deliverable table lists D-10 before D-9.
