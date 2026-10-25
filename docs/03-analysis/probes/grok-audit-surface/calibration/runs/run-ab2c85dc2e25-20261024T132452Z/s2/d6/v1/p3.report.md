## Summary
The impl plan is executable on task shape, paths, and RED/GREEN splits, and its stated departures (bash 3.2 `printf -v`, interpreter probe, T10 split) are internally consistent. Four acceptance instructions would make a 5d/5e implementer write the wrong assertion or omit a fail-closed branch the current design body requires. The design file the plan names as its contract is v1.6; the plan still implements the v1.2 root-open and arm-2 component rules and does not list the later decisions as departures.
Evidence: 6 files opened, 26 greps run.

## Must-fix
- T4 AC-4.4 tells the implementer that `test_codex_control_byte_header_is_judge_error` denies `no-test-resolved`, while the same task's header rule says a path that still contains U+0000–U+001F or U+007F is a bad header and a governed bad header refuses `judge-error`. On the unfixed `PATCH_TARGET` `(.+)` capture, `src/n.py\x1f` is already a production target and denies `no-test-resolved`, so that assertion is green at RED, and CX-CTRL (control-byte check removed) keeps `no-test-resolved` and survives. The test name, the empty-path sibling, and the design's bad-header rule all require `kind=judge-error`.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md › `test_codex_control_byte_header_is_judge_error[m20]` and `[u0001]` deny `no-test-resolved`.
- T5 AC-5.1 says the reap-failure run returns in under 2.0 s with deadline `start + 2.0`. The same paragraph then waits out that deadline and a post-kill `communicate(timeout=REAP_GRACE_S)` of 1.0 s, so a correct runner returns after about 3 s. The design's bound is 4.0 s (`2.0 + REAP_GRACE_S + 1.0`). An implementer who asserts `< 2.0` writes a test the fixed tree fails.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md › `It returns in under 2.0 s with `reap_failed=True``
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `fixed: returns in under `2.0 + REAP_GRACE_S + 1.0` s = 4.0 s`
- Arm-2 `component` is specified as the spelled path. T1's AC-3.6 unit test expects the spelled component for on-disk `Tests/` spelled `tests/newmod.py`, and T2 sets the root component to the pre-resolve string handed to `canonical_directory`. The design's arm-2 rule is the on-disk spelling from `_on_disk_component` (spelled fallback only when that lookup raises). The `Tests`/`tests` case is the one where those strings differ, and the plan never names `_on_disk_component` or `test_unresolvable_component_is_reported_in_on_disk_spelling`.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md › `spelled component. The mode is restored in teardown.`
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `At `arm` `2` it is the failing component, as a path, in its on-disk spelling as`
- A root that cannot be entered is governed-only in this plan, which is the fail-open the design closed. T2's arm-2 branch scans phase status and `inactive` returns 0, so mode `000` (rglob yields nothing, status `inactive`) allows. T3 runs `_chain_may_hold_state` on an unresolvable root and `_allow`s when ungoverned. The design refuses `project root (CLAUDE_PROJECT_DIR) cannot be entered` before that call whenever the root is absent or not enterable, and D-2 refuses the Codex root before `_any_phase5_status` when `os.access(root, X_OK)` is false, whatever the phase (`test_codex_mode_000_root_refuses_whatever_the_phase`, `CX-ROOT-ENTER`). Neither check, pin, nor mutation is in any task, and the departure list does not exempt them.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md › ``inactive` returns 0. The branch returns in every case, so neither `_targets` nor`
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `before any state walk, the Codex gate refuses `judge-error` ("project root cannot be entered") when the selected root is not traversable (`os.access(root, X_OK)` false), whatever the phase.`

## Should-fix
- T0's closed cell inventory (M-1 through M-23, plus leaf-symlink, the three FR-8 forms, the OQ-P1 cells, and R-3) does not name the seventh approved cell `M-18 M-14`. T9 requires `softened=7 approved=7`. A probe that emits `cell=M-14` or `cell=M-18` for that codex/step3 softening will not hit `APPROVED`, and a comparator that only approves the compound token will `COMPARE: FAIL` the real key.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md › `The cells are M-1 through M-23,`
- T10b's forced arm asserts that the recording git stub saw no `rev-parse`, and it says the stdout token stays `owned_elsewhere` when the read's result is discarded. The design's unconditional arm for the same wire substitutes the minted owner and prints `enter_autonomous`. That departure is not in the refinements list. The plan calls the design the contract, so a 5d author can write the token assertion, which stays green when the read runs and the id is thrown away.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md › `discriminate: an unconditional read whose result is discarded still prints `owned_elsewhere`.`
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `and an unconditional read substitutes the minted owner and prints`
- `session_id_from_git_dir` returns `None` on `OSError` from the id-file read and does not name `UnicodeDecodeError`. A text-mode read of a non-UTF-8 id file raises `UnicodeDecodeError` (`ValueError`), which escapes that arm, so `main` does not see `None` and does not print `cannot_judge`.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md › ``subprocess.TimeoutExpired`, the id file absent, `OSError` on the read, and an`
- Design v1.6 N-1 is absent from every task: the `..` walk must take `os.path.dirname` for an existing non-symlink directory (an x-only directory on the way is not arm 2), and the walk must skip `.` components. A kept `.` makes `tests/./../src/prod.py` resolve under `tests/` and the Claude gate allows it. The plan has no pin (`test_dot_component_does_not_shift_dotdot`, `test_claude_dot_then_dotdot_into_production_denies`, `test_dotdot_through_unreadable_directory_is_lexical`) and no TI10. Searched the impl plan for `TI10`, `dot_component`, and `_on_disk_component`; the only hit was the unrelated `%FF` `UnicodeDecodeError` assertion.
  class: build
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `so `tests/./../src/prod.py` resolved under tests/ and the Claude gate allowed it`

## Nit
- T10a says the reader returns `None` on five failure arms and the list omits a non-zero `git` exit, while the same task's parametrised ids include `[outside-repo]`. The acceptance test already requires that case; the arm count in the prose is the stale part.
