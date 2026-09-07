## Summary

I re-derived every tree-claim in the v1.87→v1.89 delta at the frozen HEAD `335f535` (two commits
past the plan's measurement sha `a8e0372`, one of which touches `h-mad/` code) rather than at the
sha the plan names, and every number the revision landed holds there: fence census 73/10 control 88,
corpus 30 tracked / 35 glob with the surplus exactly the five `.pytest_cache/README.md` files and no
tracked member missing, extractor census 2 narrow / 6 broad with controls 24 and 4, AC count 49,
`def test_` 6 with six call sites, all four `docsections.json` `file` keys `tests/docsections.py`
with two anchoring inside `_fence_aware_end`, `seven-plus-two-plus` exactly one hit, the spec's two
by-reference greps 1 and 0, `scripts/*.py` 37, `parametrize("path", _SCANNED` 2 with `_SCANNED`
globbing only `scripts/` (so `len(tuple)`=9 is right), and the Second-surface census re-run by
importing `_second_surface()`: 7 blocks / 1 gating, 6 / 0 with the tag simulated, gate still block 4
and `exec codex` still block 2, each unique under its own filter. The AC-6.4 attribution matches
spec v1.56 verbatim. What did not hold is the *closure* the revision claims: four sha-less
tree-derived counts survive in the plan, one written by v1.89 itself, and the design is the one
surface of the four that the round-three sweep never reached.
Evidence: 16 files opened, 45 greps/probes run.

## Must-fix

- The sha-less tree-derived-count class is NOT closed — four members survive in the plan, and one of
  them was written by the v1.89 fix. Every one is *correct* at `335f535`, so this is a provenance
  defect, not an arithmetic one, which is exactly the state the class existed in before v1.88 too.
  (a) `plan:1003` states `37` with neither a command nor a sha — written by v1.89, in the very
  paragraph whose stated purpose is "so the next reader re-derives instead of carrying the number"
  (`ls h-mad/scripts/*.py | wc -l` → `37` at `335f535`). (b) `plan:226` states `three` with the
  command but no sha (`grep -rln 'from docsections import' --include='*.py' h-mad handoff` → 3 files
  at `335f535`). (c) `plan:372`/`plan:373` assert a caller count, three line pins and an *absence*
  on the bare word "measured", with no command and no sha — verbatim the "Re-measured this session"
  form the same revision struck from the Risks row on the grounds that a re-measurement without a
  commit is unfalsifiable (`grep -n '_gate_bash_block()' h-mad/tests/test_h_mad_collect_report_docs.py`
  → `267:def`, `281`, `310`, `368`; `grep -c returncode` → `0`, both at `335f535`). (d) `plan:383`
  repeats (c)'s form for the two text-pin callers. The rule over the axis: **every count or absence
  claim about the working tree carries its generating command AND the sha it was run at, on the same
  surface as the number** — "(measured)" is not a sha and a command is not a sha either. Residual
  after that fix, stated so the next sweep is checkable: Version-History entries keep their era's
  numbers; design-derived counts of artifacts that do not exist yet (`29 names`, `81 mutations`,
  `8 rows`) are out of class; and a bare `path:line` is a locator, but a locator asserted as
  "measured" is making a tree claim and IS in class — which is what (c) and (d) are.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `` `h-mad/scripts/*.py` is 37 files today ``
  quote: docs/01-plan/features/doc-block-exec.plan.md › `three files import it`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `` `.returncode` is read nowhere in the file (measured) ``

- LANDS IN THE DESIGN, NOT THIS FILE — the design is the fourth surface the round-three sweep did
  not reach, and it now contradicts the other three on both of that round's headline fixes.
  (1) `design.md:688` still says the delegation spy is "one of the **seven** floor-tuple node IDs",
  while spec v1.56 removed the total, plan v1.89 enumerates nine, and impl-plan v1.38 lists nine
  full node IDs with `len(tuple)`; `grep -no '2748 + new_module + [a-z_()0-9]*'` returns `len(tuple)`
  in the spec and the plan and nothing in the design, so `seven` is the only surviving total and it
  is wrong at `335f535`. This is the exact "OWED ELSEWHERE" item the plan's own v1.88 entry recorded
  and the round then swept in three documents out of four. (2) `design.md:1342` describes AC-6.1's
  test as "the plan's census sweep", which is the by-reference premise plan v1.88's MUST-1 removed
  from this document — and it is false in the design's own sentence, since the census is a
  filesystem glob with no dot-directory exclusion while the same row goes on to require one. Rule
  over the axis: a cross-document correction is applied to **all four** phase documents in the same
  commit, and the check is `grep` for the old wording across `docs/01-plan/features/*.md` and
  `docs/02-design/features/*.md`, not just the file the finding was filed against.
  quote: docs/02-design/features/doc-block-exec.design.md › `one of the seven floor-tuple node IDs (AC-1.8, AC-6.4)`
  quote: docs/02-design/features/doc-block-exec.design.md › `` (`test_exactly_one_tagged_fence_in_the_tree`, the plan's census sweep asserting cardinality 1) ``

## Should-fix

- §Next Steps defines this plan's own exit gate over a pair of surfaces that is no longer the pair
  the tree defines, and names as the tree-reader the surface that is quota-blocked until
  2026-09-07. `h-mad/SKILL.md:1353` reads ``unavailable (§"Teammate audit leg"): `doc-auditor`
  teammate + `agy`, with the teammate holding codex's leg and **gating**`` — verified at `335f535`
  — so the round producing this report is teammate+agy, a configuration the plan's stamp criterion
  does not admit. It matters now rather than cosmetically, because the next action on this document
  is to stamp `must=0 should=0` and the sentence that says what may stamp it names the wrong legs.
  Prescription that closes the class rather than swapping one name: state the criterion
  structurally — two surfaces per §"Never gate on one audit pass", at least one of which reads the
  working tree — so a leg substitution can never stale it again. Residual: the same sentence also
  asserts *what each surface does* ("codex reads the tree; agy reads for contradiction"), which is
  a behavioural claim about a surface and should go with the named surfaces.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `the tree; agy reads for contradiction)`

## Nit

- The docsections mutation rows are introduced fifth (`plan:294`), **eighth** (`plan:313`), then
  sixth and seventh (`plan:328`), so a reader meets "an eighth row" with five introduced. instance
  of: the class the v1.88 nit opened and then closed at one instance — it reordered the sixth/seventh
  pair and left the eighth ahead of both. The rule is either ascending introduction throughout, or
  drop the ordinals and name the rows, since §Deliverables already carries the total once as
  "8 rows".
  quote: docs/01-plan/features/doc-block-exec.plan.md › `**An eighth row keeps that local-restore revert**`

- `plan:813` names three of the four in-fence `#` lines in `h-mad/agents/doc-auditor.md` and writes
  "and one more" for the fourth. Verified at `335f535`: the four are `## Summary`, `## Must-fix`,
  `## Should-fix`, `## Nit`, and the other four agent documents carry none — naming the fourth costs
  four characters and makes the claim checkable without re-running the scan.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `and one more)`
