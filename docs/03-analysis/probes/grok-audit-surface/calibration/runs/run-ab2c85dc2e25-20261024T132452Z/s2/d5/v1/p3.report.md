## Summary

Three v1.6 decisions are not the contracts a T1/T2/T6 implementer would write from the live sections. A non-enterable Codex root is both "refuse before any state walk" and "still owed to the operator, allow when inactive"; the `.` / lexical `..` walk exists only in the changelog; and the test plan says unfixed M-18 allows on both gates where spec AC-3.3 and AC-6.1 say Codex denies `judge-error`. The approved seven-key softening table, the reap bound, and the resume flag match the spec and the plan.

## Must-fix

- Codex mode-`000` is three gates at once, so T2 can ship the allow spec FR-3 forbids. The call-site section closes D-2 (refuse `judge-error` before any state walk, whatever the phase) and then, in present tense, says this design does not close the gap and that the mode-`000` decision is still owed to the operator. Error Handling, which is not marked as history, maps every Codex arm-2 result to `judge-error` only when governed, and T2's rewrite list never adds the `os.access` check or `test_codex_mode_000_root_refuses_whatever_the_phase`. Spec FR-3 requires both gates to refuse before state lookup; the v1.5 measurement in the same section is that `Path.rglob` yields nothing, status stays `inactive`, and the gate allows.
  class: build
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `before any state walk, the Codex gate refuses`
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `this design does not close the`
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `only when governed. They do not propagate to`
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `whatever the phase, before any state lookup.`

- The canonicaliser walk an implementer builds from the body does not drop `.` or refuse to open `..` out of a non-symlink directory, so `tests/./../src/prod.py` stays the fail-open spec v1.6 closed. `canonicalise` is specified as `canonical_directory` on the root and the deepest existing directory; T1's rewrite is the leaf scan, symlink-entry exclusion, and the codecs. The test plan and T8 do not name TI10, `test_dot_component_does_not_shift_dotdot`, or `test_dotdot_through_unreadable_directory_is_lexical`. That rule is only in the v1.6 changelog, while spec FR-1 step 2 and FR-3 N-1 make it the walk.
  class: build
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `for the deepest existing directory of the target.`
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `The leaf scan follows a symlink leaf to the referent's parent and excludes symlink entries.`
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `components (mutation TI10`
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `v1.6, N-1`

- The AC-3.3 / AC-6.1 tests would encode the wrong unfixed Codex cell. The test-plan row for 3.1–3.3 says M-18 allows on both gates, fixed and unfixed, and the design's restatement of AC-6.1 says the unfixed gate-equality set is exactly M-4, M-5, M-6, M-7, M-8, M-11 and M-12. Spec AC-3.3 says unfixed Codex on M-14 denies `judge-error`, and AC-6.1 says that M-18 M-14 cell fails both unfixed assertions. The design's own ALLOW list already records the unfixed denial, so T6's "both failure sets" follow the test plan and drop the cell.
  class: build
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `M-18 both allow, fixed and unfixed`
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `gate-equality row is the unfixed run failing on exactly M-4, M-5, M-6, M-7, M-8, M-11 and M-12.`
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `the unfixed Codex gate denied this symlink loop outside Phase 5`
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `Unfixed: both allow, except the Codex`
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `fails both assertions on the unfixed tree (Claude allows, Codex denies`

## Should-fix

- `_tree_b` is attributed to `h-mad/tests/test_h_mad_tdd_gate_copy.py`, which is not in the tree. The function is defined in `h-mad/tests/test_h_mad_tdd_gate_judge.py`, the file the components table names, and T3 says only "Updates `_tree_b`". The fixture delta can be written against a path the suite does not call.
  class: build
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `h-mad/tests/test_h_mad_tdd_gate_copy.py`
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `h-mad/tests/test_h_mad_tdd_gate_judge.py`

- The Claude root-refuse history is still an instruction. After the live condition that drops the `CANON_COMPONENT` equals `CANON_ROOT` conjunct, the residual says this revision does not change the hook and that no pin covers mode `000`. The supersession sentence in that same paragraph names `test_mode_000_project_dir_refuses` for the on-disk and mis-cased members, and neither the test plan nor T3/T8 lists that pin. The mis-cased mode-`000` member can stay on the absent-root pin the history describes.
  class: build
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `this revision does not change the hook.`
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `the mode-000 and mis-cased mode-000 members are pinned by`

## Nit

- The overview still says Spec v1.4 (`644f8bf6`) and Plan v1.4 (`1254595a`) state what the gates decide. This design's changelog and the bound spec are v1.6, which is why the walk, the Codex root rule, and the M-18 unfixed cell were updated in the changelog and not in the sections above.
