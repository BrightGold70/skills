## Summary

Plan v1.104 at freeze `cb4fe99` is exceptionally well-verified on the tree axis: I re-ran the
`pgid=` census, both interval closures, the `.py` fence/file censuses, the fence census (73/10 and
control 88), the codex-leg ledger series at all ten shas, the SCRIPT_DIR census, the docsections
locators, the AC anchor count and the Second-surface block census, and **every one reproduced
exactly at its stamped sha and at the freeze**. The two defects I found are both **cross-document
contradictions landed in the same commit as the plan**: the plan states a design-derived mutation
count of 81 against a design matrix that carries 85 at `cb4fe99`, and it spells the AC-1.8 pin as a
command that runs `test_docsections.py` when spec v1.63 makes that pin collection-only and forbids
running the file. Neither is visible from the inlined text alone; both required reading the sibling
blobs at the freeze.
Evidence: 12 files opened, 78 greps run.

## Must-fix

- The §Deliverables mutation-spec row states **81 mutations / 80 helper-source + 1 `SKILL.md`** while
  naming the design's Test Plan matrix as "the authoritative matrix this row points at" — and that
  matrix carries **85 data rows** at the freeze `cb4fe99`, with the design's own Deliverables cell
  reading 85 (84 + 1). The move landed in `cb4fe99` itself, the same commit as plan v1.104: counting
  matrix rows under the `entry by entry` lead-in gives **81 at `4e4a00c`, `6f0ee85` and `09e9307`,
  85 at `cb4fe99`**, and diffing the row names between `09e9307` and `cb4fe99` shows five arrivals
  (`cleanup-chain-selection-flipped`, `intersect-check-removed`, `rollback-identity-check-removed`,
  `spawn-valueerror-unmapped`, and a rewritten `field-escape-removed`) against one departure. The
  1-of-`SKILL.md` half is still right: `git grep -c 'the mutation targets \`SKILL.md\`' cb4fe99 -- <design>`
  returns **1**, and that row is `registry-row-removed` as the plan says. **Prescription**: 81 → 85 and
  80 → 84 at both sites, re-derived at `cb4fe99` rather than at `4e4a00c`/`6f0ee85`. **The class**, and
  it is closed by the plan's own enumeration: §Measurements names exactly three design-derived
  contract values — "`29` names, `81` mutations, `8` rows". I re-derived all three at `cb4fe99`; the
  29 holds (impl-plan Task 1's `__all__` is 5 + 20 at Task 1 and 29 complete, with 6+3+4+5+1 = 19
  subclasses) and the 8 holds (design: "6 + 2 = 8"), so **`81` is the only member that drifted** and the
  class has no unenumerated residual. **Residual**: that enumeration is a hand list, so a fourth
  design-derived value adopted later joins the class only if it is added to that sentence.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `FR-1..FR-5 — 81 mutations with a full-node-ID `test` binding each — **80 of the helper's source and 1 of `h-mad/SKILL.md`**`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `design-derived counts of
artifacts that do **not exist yet** (`29` names, `81` mutations, `8` rows)`
  quote: docs/02-design/features/doc-block-exec.design.md › `guards for FR-1..FR-5 — 85 mutations (85 rows: 84 of the helper's source, 1 of `h-mad/SKILL.md``

- §Implementation Strategy spells the AC-1.8 pin as **`pytest h-mad/tests/test_docsections.py -q`**, a
  command that *runs* the file, while spec v1.63's AC-1.8 — landed in the same commit `cb4fe99` —
  makes that pin **collection-only** and states in terms that it must not run the file. The spec's
  reason is load-bearing rather than stylistic and the plan's own §Success Criteria carries the
  premise it turns on: AC-6.4 adds `test_docsections_delegates_to_the_authoritative_bounder` to
  `test_docsections.py`, and AC-6.5 requires that node to go RED under `docsections-delegation-reverted`,
  so a subprocess that runs the file cannot stay green under the mutant the wire pin exists to fail.
  As written the plan prescribes a pin that is red by construction in exactly the state the mutation
  harness creates. **Prescription**: replace the run form with the spec's
  `[sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "h-mad/tests/test_docsections.py"]`
  from the repository root, requiring exit 0, and say that the pre-existing tests in that file are no
  longer run in isolation and are covered by the AC-6.4 floor and the 5e module-scoped run.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `they are the AC-1.8 collect-alone pins Success Criteria names:
`pytest h-mad/tests/test_docsections.py -q` run as a subprocess from the
repo root (collected **alone**)`
  quote: docs/01-plan/features/doc-block-exec.spec.md › `**The collect-alone pin is collection-only, and that is a contract rather than an
    implementation detail.**`
  quote: docs/01-plan/features/doc-block-exec.spec.md › `It must
    not run that file, because AC-6.4 adds a node to it`

## Should-fix

- The `81` in the §Deliverables row is the one `docs/`-scoped figure in this document that skipped
  v1.104's measurement commit, and the row says so about itself: it declares the figure "re-derived at
  every freeze" while its derivation command names `4e4a00c` and `6f0ee85` only, against §Measurements'
  "v1.104 is measured at `fbc2ea0`, and at nothing else". That is the mechanism behind the first
  must-fix, and it is separable from the digit: the row's derivation command counts only the
  `SKILL.md`-target rows and never the matrix total, so the total had no re-derivation obligation
  attached to it at all. **Prescription**: give the total its own command in the same cell (count the
  data rows under the design's `entry by entry` lead-in at a named sha) so both halves of "84 + 1"
  are re-derivable rather than one.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `The figure is derived from a **sibling under `docs/`**, so the §Measurements closure does not reach it and it is re-derived at every freeze`

- **Owed by the impl-plan, not by this document, and reported rather than filed against the plan**:
  spec v1.63 and the design now route a NUL-byte `ValueError` at the spawn into
  `LAUNCH_FAILED stage=spawn` — the design's error table says the constructor wraps "an `OSError`
  **or** the `ValueError` a NUL byte in the composed shell text raises, both mapped to the `spawn`
  stage" — while `h-mad/tests/…`'s source form in the impl-plan still annotates
  `def __init__(self, stage: str, err: OSError | subprocess.TimeoutExpired, pgid: int | None = None)`.
  A `ValueError` is neither member, so the annotation is narrower than the contract it implements.
  The plan's own API table names `LaunchFailed` without an `err` type and is therefore correct as it
  stands; this needs routing to the impl-plan author.
  quote: docs/02-design/features/doc-block-exec.design.md › `an `OSError` **or** the `ValueError` a NUL byte in the composed shell text raises, both mapped to the `spawn` stage`
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `def __init__(self, stage: str, err: OSError | subprocess.TimeoutExpired,`

- The §Deliverables `test_docsections.py` row names the delegation spy as killing
  `docsections-delegation-reverted` alone, while both the design's spec paragraph and this plan's own
  FR-6 table bind **two** rows to that one test — `docsections-heading-lookup-reverted` as well. The
  Deliverables cell is the surface a 5c task split reads first, and a task that provisions one RED
  where two are required under-scopes the test. **Prescription**: name both rows in that cell, or point
  at the FR-6 table the way the Risks row points at the block census.

## Nit

- §Scope writes the AC-1.8 deliverable as `mutation-specs/docsections.json`, a root-relative path with
  no root; §Deliverables writes the same artifact as `h-mad/tests/mutation-specs/docsections.json`.
  The bare form does not resolve from the repository root, where every other command in this document
  runs. One spelling throughout.

- The §Deliverables `docsections.json` cell states "8 rows" as a free-standing figure beside a
  description whose own terms give it (four existing rows plus four named connection rows). This
  document's stated rule is that an integer about a surface is written as the arithmetic over that
  surface's values; writing it `4 + 4 = 8` makes the reader's check addition on the page. The value is
  correct: the file carries four mutations today and the design's paragraph says `6 + 2 = 8`.
