## Summary

Plan v1.83 read in full against the tree at base commit `e8eaf6f`, with every cited existing
path:symbol, test name, census and count re-derived by command. The tree-facing citations hold —
the fence census (68/10, control 83), the extractor census (2 narrow, 5 broad, the three fixture
hits at the exact lines named), the docsections importer census (three files, all using only
`titled_section`/`section_from`), `:270`/`:281`/`:309`/`:368`/`:412`/`:22`, the four-blocks-in-the-
Second-surface measurement, the AC count (49), the mutation-harness contract (`target_command +
[test]`, exact-once refusal, exit 0 on `SURVIVED`), and `hmad-dispatch run --timeout` (rc 3
propagated, rc 124 on expiry). Two things do not: the AC-6.4 suite-floor baseline is stale by one
test at HEAD, which falsifies the plan's own no-hidden-deletion guarantee, and the plan is the one
document of four that states the exit-code contract without the `--help` carve-out.

## Must-fix

- **The AC-6.4 suite-floor baseline no longer reproduces, and the guarantee the plan draws from it
  is false by one test.** The plan cites `2747` collected and passing at `6b4df35`, and `2485` from
  `h-mad/`. Re-derived at the audited base commit `e8eaf6f`, from the repository root:
  `python3.11 -m pytest --collect-only -q` → `2748 tests collected in 0.36s`, and with
  `-p no:cacheprovider` → `2748 tests collected in 0.32s`; from `h-mad/` → `2486 tests collected`.
  The delta is `b59e05e`, which took `h-mad/tests/test_h_mad_assemble_audit.py` from 5 to 6 test
  functions after the baseline commit (`grep -c '^def test_'`: 6 at HEAD, 5 at `6b4df35`; the
  working tree is content-identical to HEAD — `git diff --stat` is empty, the ` M` entries in
  `git status` are stat-only). Because `test_suite_floor_holds` asserts
  `full_collected >= 2747 + new_module + 7` and the pre-existing count is 2748, exactly one
  pre-existing test can be deleted with the floor still green — which is precisely what the plan's
  closing sentence promises cannot happen. The floor is defined as the *pre-change* count and 5c
  has not branched, so the pre-change count is HEAD's, not `6b4df35`'s; a frozen literal can only
  be right if it is re-derived at the branch commit rather than carried. The same pair of numbers
  is carried on five surfaces inside this document (the two code blocks, the `AC-6.4's floor is
  2747` sentence, the `2485` parenthetical, and the `test_suite_floor_holds` assertion) and again
  in spec AC-6.4 and impl-plan §Task 5, so a spot-fix on one of them re-opens the others. Note: I
  re-ran only the *collected* half, which is the half `test_suite_floor_holds` asserts; the passing
  half (`2747 passed in 397.40s`) was not re-run.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `2747 tests collected in 2.03s`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `test cannot hide behind the additions.`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `from `h-mad/` the same command collects 2485, a different tree`

- **The plan is the only one of the four documents that states the exit-code contract without the
  `--help` carve-out, and read literally it prescribes dropping a capability the spec preserves.**
  The plan asserts, unqualified, that there is no exit without a `DOCBLOCK:` line. Spec AC-5.6,
  design §API and impl-plan §Conventions all state the same rule *with* the exception — `--help`
  alone keeps argparse's own exit-0 help text and emits no `DOCBLOCK:` line. `add_help` defaults
  to `True` and the help action bypasses the overridden `error()`, so the plan's absolute form is
  not satisfiable by the design as specified; the only way to make it literally true is
  `add_help=False`, which removes the help output the other three documents keep. The impl-plan
  swept exactly this sentence in its own document at v1.31 (the most recent commit, `f6345c4`);
  the plan was not swept with it, which is the unswept-surface failure the paired-document gate
  exists to catch.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `there is no non-`DOCBLOCK` exit`
  quote: docs/01-plan/features/doc-block-exec.spec.md › `there is no non-`DOCBLOCK` exit (`--help``
  quote: docs/02-design/features/doc-block-exec.design.md › ``--help` alone keeps argparse's`

## Should-fix

- **"changes at exactly two points" is contradicted by the list that immediately follows it, and
  the hoist it describes orphans two locals the plan does not account for.** The same paragraph
  then specifies: the added `import h_mad_doc_block_exec as dbe` line, the `_gate_block()` /
  `_gate_bash_block()` split, the hoist of `run_recipe` to a module-level `_run_recipe`, and the
  removal of the in-test `import subprocess` (line 304) — and the impl-plan adds six new tests to
  the same file. That is at least five edit points plus six additions, not two. Separately: today
  `collector` and `gate` are locals of the *enclosing test* at `:306`–`:307`, not of `run_recipe`
  (which closes over them); once `_run_recipe` derives them itself, both lines are dead and must be
  deleted, so "nothing else in the file moves" does not hold as written. The plan's own phrase
  "the locals today's nested `run_recipe` computes the same way" also mis-describes who computes
  them.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `changes at exactly two points`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `so the hoist leaves no unbound name and "nothing else in the file moves" still holds`

- **"match zero blocks" is measured false.** Tagging only the gate fence leaves `:270`'s
  `re.findall(r"```bash\n(.*?)```")` matching 3 of the section's 4 bash blocks, not zero — measured
  by applying the tag to the live section text: `before tag: 4 blocks; 1 gating` →
  `after tag: 3 blocks; 0 gating`. What goes to zero is the *gating* subset, and the loud failure
  is the `assert gating` at `:271`, not an empty `blocks` list. The conclusion (it fails loudly,
  so the tag and the migration must land together) survives; the stated mechanism does not, and it
  is the sentence an implementer would reason from when deciding what the RED looks like.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `match zero blocks`

- **`__all__` is stated as 29 names but the plan's own enumeration yields 28.** Seven functions +
  `Block` + `RunResult` = 9, and the design's exception table has 19 `DocBlockError` *subclasses*
  (`DocUnreadable`, `BadInfoString`, `BlockNotFound`, `AmbiguousBlock`, `AmbiguousHeading`,
  `BadIndex`, `BadTimeout`, `BadArgs`, `BadSubstArg`, `MissingSubstitution`,
  `OverlappingSubstitution`, `StreamPathUnwritable`, `StreamPathsAlias`, `PreambleUnreadable`,
  `StreamWriteFailed`, `StreamCloseFailed`, `BlockTimeout`, `CleanupFailed`, `LaunchFailed`) →
  28. The 29th is the base class itself: the impl-plan's Task 1 `__all__` literal leads with
  `"DocBlockError"` and its comment reads "DocBlockError + 19 subclasses". So the number is right
  and the enumeration behind it is wrong; it should read "the `DocBlockError` hierarchy", which is
  how design line 6 puts it. Design line 689 carries the identical wrong wording, so both surfaces
  need the sweep. (The parenthetical attributes 29 to design v1.85, which said 28; 29 landed at
  design v1.86.)
  quote: docs/01-plan/features/doc-block-exec.plan.md › `plus `Block`, `RunResult` and every `DocBlockError` subclass`
  quote: docs/02-design/features/doc-block-exec.design.md › `plus `Block`, `RunResult` and every `DocBlockError` subclass — 29 names`

- **The docsections.json "two leave / two stay" split is wrong: none of the four `find` anchors
  survives verbatim.** The plan contrasts the two mutations whose anchor lines leave
  `tests/docsections.py` with two that "stay where they are" / "anchor on lines that remain
  there". Both of the latter change text: `section_from`'s line becomes
  `return text[offset:_dbe.fence_aware_end(text, offset, level)]`, and `titled_section`'s
  `assert match, f"missing section {heading!r}"` becomes `assert found, …` once the local
  `re.search` is deleted (the plan itself specifies both changes two sentences earlier). The
  impl-plan already writes both new anchors (`offset-anchored-bound-runs-to-end-of-file` finds the
  `_dbe.` form; `missing-heading-returns-empty-instead-of-failing` finds `assert found, …`). The
  work is covered by the plan's "re-reads the landed lines to set each `find`" sentence, but the
  two-leave-two-stay characterisation is stated twice and is what an implementer would use to
  decide which rows to leave alone — and a left-alone row is a harness refusal, not a silent pass.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `that remain there`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `the other two stay where they are`

- **The extractor-census control no longer reproduces.** `grep -rl '```' --include='*.py' . | wc -l`
  returns 23 at HEAD, not 21 (`git grep -l '```' a469493 -- '*.py' | wc -l` → 21, so the figure is
  the one measured at the cited commit and has drifted since). The control's job — showing the
  narrow pattern is not under-matching — is unaffected, but the plan's Measurements preamble makes
  citing the output the point ("a cited output is checkable by a reviewer"), and this one now fails
  the check. The two figures beside it were re-derived and are current (narrow census: exactly the
  two `:270`/`:412` hits; broad literal: 5 hits, the other three at `test_docsections.py:27`,
  `test_h_mad_assemble_tdd.py:489` and `:551`, exactly as stated).
  quote: docs/01-plan/features/doc-block-exec.plan.md › `21 `.py` files contain a fence literal`

- **The `## Scope` section's "In scope" list omits three of the ten Deliverables rows.** It
  enumerates the helper module, the tag convention, the one tagged fence and the one migrated call
  site, and stops there — while Deliverables carries `h-mad/tests/docsections.py`,
  `h-mad/tests/mutation-specs/docsections.json` and `h-mad/tests/test_docsections.py`, which
  Implementation Strategy itself calls "a scope increase the design audit forced". Scope is the
  section a reader consults to answer "what does this feature touch", and it currently answers
  wrongly; the correction belongs there, not only in a paragraph 170 lines further down.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `In scope: one new helper module with an importable API and a verdict-token CLI`

## Nit

- **The four-backtick premise is true but is the one measurement in the document with no command
  behind it, and it is stated two different ways.** Verified by probe: `titled_section` over a
  section containing a ` ````markdown ` block that quotes a ` ```bash ` fence returns
  `'\nbefore\n\n````markdown\n```bash\n'` — the section ends at the quoted opener, so both
  `"after"` and `"not alpha"` are outside it. Every other load-bearing premise in this plan carries
  its command and output; this one carries neither, and the two phrasings ("stops early inside an
  unbalanced four-backtick fence" at Implementation Strategy, "mis-tracks an unbalanced inner quote
  inside a four-backtick fence" at Measurements) describe different failures.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `the existing toggle stops early inside an unbalanced four-backtick fence`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `mis-tracks an unbalanced inner quote inside a four-backtick fence`

- **`docsections-local-bounder-restored` is described as restoring a symbol that does not exist.**
  `h-mad/tests/docsections.py` at HEAD has no `_find_heading`; the heading lookup is an inline
  `re.search` inside `titled_section` (line 53), which is how the plan names it in the
  `docsections-heading-lookup-reverted` sentence and in the FR-6 table. The impl-plan's mutant
  payload *introduces* a helper by that name, so "restored" is the wrong verb — the row adds a
  `_find_heading`, it does not put one back.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `the old `_fence_aware_end` toggle and `_find_heading``

- **The injection ordinals point into a list the plan never gives.** The parenthetical reads as if
  the named-fault-injection list ends at six; the design and spec both put it at eight (seven
  module-level seams plus the instance-level `Popen` wrapper). The ordinals themselves are correct
  against the design's numbering — a reader just cannot check them from this document.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `the fifth named injection (the sixth is the `_close_stream` seam for the backstop close)`

- The Risks-table reap sequence stops at `rmtree(cwd)` in `finally`, while the Measurements
  paragraph 200 lines later extends it with "close pipes → `wait(timeout=DRAIN_SECONDS)`". The
  abbreviated form is not wrong, but it is the one a reader skimming Risks would implement from.

- The collect-alone and unrelated-cwd pins are written as `python3 -c "import docsections"` while
  every other command in the document pins `python3.11`. A test would use `sys.executable`; the
  bare `python3` reads as a second interpreter.

- The Deliverables row points at the design's authoritative matrix "under the heading" *Helper
  mutation spec — …, entry by entry*. That is a bold paragraph in the design, not a heading, so a
  reader searching for a `##` will not find it. (The matrix itself checks out: 81 rows, and every
  helper-matrix mutation name the plan cites occurs in it.)
