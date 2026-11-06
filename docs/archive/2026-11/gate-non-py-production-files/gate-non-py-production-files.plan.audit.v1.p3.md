## Summary
The plan addresses every FR, and the tree confirms the parser census, the six `ungated` tests, the five U1–U5 mutants, the 49 acceptance criteria, and the two `*.md|*.yaml` pin sites. Two build gaps remain: the in-process transport is described as a path the agy gate does not have, and FR-6/FR-7 drop the spec's smallest-listed-name selection. A test-pinned Phase 5 sentence that shell is never gated sits in the M6 corpus and is outside the recorded floor.

| FR | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | restated |
| FR-7 | restated |
| FR-8 | implemented-as-written |
| FR-9 | implemented-as-written |
| FR-10 | implemented-as-written |
| FR-11 | implemented-as-written |

Evidence: 20 files opened, 26 greps run. `git` could not be re-run here (worktree gitdir is outside this sandbox), and the Phase-5 command list refuses the M5 `python3 -c` census; those two published figures were not re-derived.

## Must-fix
- The strategy's "existing" in-process transport is not a path either Python gate takes for a code-like target, so wiring the listing matcher only where `_load_judge` is called today leaves agy, and codex's non-`.py` branch, unattached. Codex imports `_load_judge` and calls it only after `if not production: continue`, which is the production-`.py` selection; a code-like target returns before that call. Agy never imports `_load_judge`. It binds `import h_mad_tdd_judge as judge` inside `main` and calls `judge.read_chain` / `judge.judge` from that binding. The spec states the same transport, so correcting only the plan leaves the design to copy the false path. Name agy's real binding (or an explicit new `_load_judge()` call in the T6 loop) in spec FR-3 and in the plan's strategy, and state that codex's current call is not on the code-like path.
  class: build
  quote: docs/01-plan/features/gate-non-py-production-files.plan.md › `codex and agy reach it in-process through the existing `h_mad_target_identity._load_judge()` path`
  quote: docs/01-plan/features/gate-non-py-production-files.spec.md › `The codex and agy gates reach it in-process through `h_mad_target_identity._load_judge()`.`
  quote: h-mad/hooks/h-mad-agy-tdd-gate.py › `import h_mad_tdd_judge as judge`
  quote: h-mad/hooks/h-mad-codex-tdd-gate.py › `if not production:`
- FR-6, and FR-7 which applies FR-6's rule, replace the spec's selection with any listed code-like name. The spec keeps `min(production)` when any name is production Python and otherwise judges the smallest listed name. The plan's FR-6 bullet and the out-of-scope note that a mixed `.py` plus code-like target is judged by its `.py` name do not state that tie-break. No acceptance criterion observes which listed name is passed to the judge when several code-like canonical names qualify, so an implementation can satisfy D7, D8 and D10 while disagreeing with the spec. Put the spec sentence into the plan, or amend the spec if any listed name is the intended rule and record why the verdict cannot differ.
  class: build
  quote: docs/01-plan/features/gate-non-py-production-files.plan.md › `FR-6: codex gate skips a doc/data target first, then selects a listed code-like non-exempt name when no production-`.py` name exists.`
  quote: docs/01-plan/features/gate-non-py-production-files.spec.md › `If any name is production Python, the existing `min(production)` selection over the `.py` names is kept. Otherwise the smallest listed name is judged.`
  quote: docs/01-plan/features/gate-non-py-production-files.plan.md › `FR-7: agy gate applies FR-6's rule, doc/data skip included, in its write-class loop after unchanged T1–T5.`

## Should-fix
- M6's floor does not record the Phase 5 procedure sentence that shell is never gated, even though that file is inside the searched tree and `test_skill_states_the_docs_first_component_rule` pins the sentence through `doc_text`. The sweep regex `unconditionally|production-Python` cannot see it, and AC-10.2 only extends the Hook-bullet test. D9 can update the two named surfaces, leave `h-mad/references/phase5-substeps.md` stating the old rule, and keep that doc test green. The design's widened sweep is the spec's net for this residual, and nothing in the plan requires a branch that hits this sentence or says the pinning test asserts a stale contract. Add the sentence to the floor with its pre-change hit, and name the test update in the same Task as D9.
  class: build
  quote: h-mad/references/phase5-substeps.md › `Test files, docs, config, and shell are never gated; only production `.py`. A`
  quote: h-mad/tests/test_h_mad_tdd_gate_docs.py › `anchor = "Test files, docs, config, and shell are never gated; only production `.py`."`
  quote: docs/01-plan/features/gate-non-py-production-files.plan.md › `This sweep is a floor, not a closure: the design re-runs it with its own phrasing set (FR-10).`

## Nit
- R13 and M10 name the `*.md|*.yaml` marker in `test_py_suffixes_match_bash_fold`. The same test also requires `# M:H6` and `!= *.py`, each preceded by `_fold_py` within 300 characters. `!= *.py` is the `ALL_NON_PY` continue FR-5 rewrites. The Task that rewrites that loop should keep the marker or update the test in the same change, the way R13 already says for the first arm.
