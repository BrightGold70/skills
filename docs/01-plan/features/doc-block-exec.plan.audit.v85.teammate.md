## Summary

GATING pass on plan v1.100 at `b3be433` (HEAD, working tree byte-identical for this path). Every
property claim v1.100 newly shipped was **executed, not read**, and all of them reproduce exactly:
the fence-aware cross-document walk (`hits 3 | body 2 | fenced 1 | prose 1` with controls `1 of 2`
and `2 of 2`) at `8c6539a` **and** at `b3be433`; the row-selector series `8 / 8 / 13 / 13` across
`1cbddb7` / `700c599` / `8c6539a` / `b3be433` plus the working tree; the row-shape form `15` with
`74e126f` in `0` of them; the unanchored form `25`; the paragraph-scoped surface screen `3` union /
`5` line-scoped with per-branch ordinals `9 11 19 / 9 11 19 / 9 11 / 19 / 11` at `700c599` and
`6` / `16` with ordinals `9 11 13 14 15 24 / … / 11 13 14 15` over the working tree; the stamp-driven
driver `15 / 11 / 8` union `32` at `700c599` and `28 / 13 / 8` union `47` at `8c6539a` and at HEAD;
and `0` literal U+0085/U+2028/U+2029/U+007F bytes. The tree-derived pins reproduce too (`_gate_bash_block()`
def+3, `returncode` 0, 3 importers, `6/6/8/9/1` on `docsections`, census `73`/`88`, extractor census
`2`/`6`/`24`/`4`/`411`, `49` AC anchors with the duplicate check silent, `37` scripts, `2`
parametrisations, block census `blocks 7 | gate [4] | exec codex [2]`). The three musts below are
**not** in the newly-written prose: two are self-imposed obligations that v1.99 and v1.100 both
skipped and that are now provably stale at HEAD, and one is a cross-document grammar divergence on
an emittable detail line.

Axis C — FR reconciliation (plan granularity):

| FR | Classification |
|---|---|
| FR-1 Address a block by document, heading, explicit tag | implemented-as-written |
| FR-2 Substitute an explicit map, refuse a non-applying substitution | implemented-as-written |
| FR-3 Execute in a disposable cwd under a declared shell mode | implemented-as-written |
| FR-4 Verdict-token CLI following the established gate contract | implemented-as-written |
| FR-5 Bounded execution without an external time-bounder | implemented-as-written |
| FR-6 Migrate the existing inline harness onto the helper | implemented-as-written |

Evidence: 13 files opened, 118 greps run.

## Must-fix

- §Next Steps' codex-leg ledger is **stale at the commit the document lives at**, and the paragraph that
  publishes it declares re-measurement mandatory on every revision — an obligation neither v1.99 nor
  v1.100 discharged (neither Version History entry mentions the ledger at all). Run at four shas with the
  document's own published command,
  `git ls-tree -r --name-only <sha> -- docs/01-plan/features/ | grep -E 'doc-block-exec\.plan\.audit\.v[0-9]+\.teammate\.md$' | sed 's/.*audit\.v//;s/\.teammate\.md//' | sort -n | tail -1`:
  `1cbddb7` → **83**, `700c599` → **83**, `8c6539a` → **84**, `b3be433` (HEAD) → **84**; the codex half is
  **72** at all four. So the body's `83` was already wrong at `8c6539a`, the commit v1.100 was authored
  against, and is wrong at HEAD. This is the figure the same paragraph calls "stale by construction the
  moment the next report is written", so it is the one figure a skipped revision provably breaks.
  Prescription: re-run both halves at this round's freeze and re-stamp; if a revision does not re-run it,
  the entry must say so, since the register below is the only other place a non-run is admissible.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `it must be re-measured on every revision, without exception.`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `**codex `72` against teammate `83` at `1cbddb7`` 

- The inherited-unverified register is stamped at a commit **older than v1.100's own measurement commit**,
  which the same sentence names as the defect it exists to repair, and it excludes five figures on a
  "this revision" deixis that v1.100's own entry contradicts. The register reads
  `Inherited-unverified at `700c599`, the commit v1.99 is measured at`; v1.100 is authored against
  `8c6539a` (`git rev-list --oneline 700c599..8c6539a` → exactly one commit, `8c6539a`), and no
  `(700c599, 8c6539a]` interval argument was published, so by the paragraph's own rule the stamp is
  detached. Worse, the register keeps the five `700c599` stdlib probes **out** of its population because
  "this revision" executed them — true of v1.99, false of the body as v1.100 ships it: v1.100's Version
  History lists `the five 700c599 stdlib probes' own outputs` under `NOT RE-RUN`. That is exactly the
  softer failure the register says it closes — a figure named as un-re-run that quietly keeps a verified
  status. Prescription: move the stamp to this round's measurement commit with the interval argument run,
  and either re-run the five or enter them as members; replace `this revision` with the revision number.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `Inherited-unverified at `700c599`, the commit v1.99 is measured at`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `the five added at `700c599` were every one of them executed in`

- **Cross-document, base Single-source contract**: the `pgid` diagnostic has two incompatible grammars
  across the four documents, and the plan's exhaustiveness claim about the bare-field set is what the
  divergence falsifies. This plan, the design and the impl-plan all specify a **quoted detail line**
  `pgid: "<n>"` (design's verdict table carries ``(+ `pgid: "<n>"` when `stage=reap` or `stage=collect`)``
  → 1 body-scoped hit; the impl-plan's `DETAIL_KEYS` carries `"pgid:",` → 1 hit, and renders
  `pgid: "4242"`), while spec AC-4.6 specifies a **bare `=` field on the verdict line**, `pgid=<n>`. The
  plan asserts its bare list is exhaustive and lists exactly seven members (`rc=`, `blocks=`, `count=`,
  `keys=`, `shell=`, `stage=`, `reason=`) with `pgid:` explicitly among the JSON-quoted; an implementer
  following AC-4.6 emits an eighth bare `=` token, and — because AC-4.5 pins detail lines to registry rows
  bidirectionally — emits no `pgid:` line for the registry row to match. Independent statements of one
  rule that have already diverged is the base §"Single-source contract" violation, and the base layer
  auto-classifies it Must-fix. Prescription: re-spell spec AC-4.6 as `pgid: "<n>"` (a detail line, the
  grammar every other detail key uses); no change is needed in the plan's own words beyond, optionally,
  naming the spec as the surface that was repaired.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `the helper-produced numbers `seconds=` and `pgid:` included, is`
  quote: docs/01-plan/features/doc-block-exec.spec.md › `carries `pgid=<n>` so the operator can act`

## Should-fix

- **Cross-document**: spec AC-6.4's Phase-5f gate command still publishes the exact figure this plan
  measured as non-reproducing, inside the command this plan points at by name. The plan's §Success
  Criteria reproduces the gate command with the comment `# from the REPOSITORY ROOT, as the spec's AC-6.4
  spells it`; the spec's own spelling of that command carries `from h-mad/ the same command collects 2486`,
  with no command of its own and no sha, while this plan states the `h-mad/` figure is **2547** at
  `6f0ee85` and that `2486` "does not reproduce". Body-scoped `2486` counts at HEAD: spec 1, design 1,
  plan 1 (the sentence retiring it), impl-plan 6. Prescription: strike `2486` from spec AC-6.4 or replace
  it with a sha-stamped figure; the impl-plan's six are its own round's item.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `was a bare `2486` with no command and no sha: it does not reproduce`
  quote: docs/01-plan/features/doc-block-exec.spec.md › `from h-mad/ the same command collects 2486`

- **Cross-document**: `BAD_ARGS` is absent from AC-4.2's enumerated exit-0 row list, and this plan cites
  AC-4.2 for the whole partition. AC-4.2's list runs `NOT_FOUND, AMBIGUOUS, AMBIGUOUS_HEADING, BAD_INDEX,
  BAD_TIMEOUT, BAD_SUBST, SUBST_MISSING, SUBST_OVERLAP, BAD_INFO and TIMEOUT` — ten tokens, no `BAD_ARGS`
  — while the spec's own FR-4 description, the design's verdict table (`| DOCBLOCK: BAD_ARGS message="<m>" | 0 |`)
  and this plan's CLI-contract paragraph all require `BAD_ARGS` at exit 0. AC-4.2 is the AC whose test
  "enumerates the verdict table and asserts the code of every row", so the one verdict this plan's
  "there is no non-`DOCBLOCK` exit" claim most depends on is outside that enumeration. Not a Must because
  `BAD_ARGS`'s exit-0 behaviour *is* pinned elsewhere by named tests (`test_malformed_invocation_is_a_verdict`,
  `test_parser_rejects_all_dir_and_abbreviations`), so the gap is in the AC text rather than in coverage.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `(FR-4, AC-4.2)`
  quote: docs/01-plan/features/doc-block-exec.spec.md › ``SUBST_OVERLAP`, `BAD_INFO` and `TIMEOUT` each`

- The cardinal list of "every cardinal this document fixes over one of its own surfaces" carries a member,
  `"admissible are …"`, that occurs **nowhere else in this document**: `grep -cF '"admissible are …"'`
  over the whole file returns **1** — the list entry itself — and the paragraph-joined form returns 1 as
  well, so it is not a wrapped span either. The nearest real surface is the `audited` sweep's
  `the three admissible categories`, which returns **1** body-scoped. The list is presented as a set of
  quotations of this document's own surfaces, and this is the same unfindable-quotation class the document
  already repaired twice (the `re.escape` nit and the wrapped `re.search` pointer name). It is also the
  only member of the list carrying no cardinal, in a sentence whose subject is cardinals.
  Prescription: replace with `the three admissible categories`, which a literal `grep` locates.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `"admissible are …"`

- The both-screens re-run obligation is un-discharged for two consecutive revisions, and screen one's
  live reading is now far outside its last published triage. §Measurements states
  `Re-run both screens at the commit that lands each revision, and read the delta.`; neither v1.99's nor
  v1.100's Version History records running either screen (v1.100's entry does not mention the screen-two
  legs at all, while the body still names the six as register members carried at `6f0ee85` and unverified).
  Run at HEAD, screen one's published program returns **92** body lines against the last published triage
  of **32** over the `6f0ee85` body. The 92 is not itself a finding — the document says its hits are read
  and never counted, and most will be self-matches — but 60 lines have accumulated with no round reading
  them, which is what the obligation exists to prevent. Prescription: run both screens at this round's
  landing commit and publish the delta, or enter the omission in the register.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `Re-run both screens at the commit that lands each revision, and read the delta.`

## Nit

- In the register, the five-name enumeration (`argparse's exit_on_error routing (§Scope), rmtree on a
  0o000 directory (AC-3.14), the reader-less FIFO (AC-3.10), the naturally emptied group (AC-5.5) and the
  AC-5.2 group-kill-and-escape probe`) is separated from its head noun — "the five OS- or
  runtime-determined probes of the carve-out table's `cf3a862` block" — by a ~45-word aside that itself
  ends on a **different** "five" ("the five added at `700c599`"). On a first reading the list attaches to
  the nearer antecedent, and that reading is false. The arithmetic behind the aside is correct (12 exempt
  − 5 = 7, and the seven resolve to the five `700c599` stdlib probes plus the `awk` boundary probe and the
  grammar corpus); only the placement misleads. Close the aside before the enumeration, or repeat the head
  noun after it.

- The `25` reading is described as "stamped to a working tree and to nothing else", but that working tree
  landed as `b3be433` and reproduces there
  (`awk '/^## Version History/{exit}{print}' <doc> | grep -cE '`git ls-files [^`]'` → 25). A reader is told
  the figure is uncheckable when it is in fact checkable at a named commit; saying "stamped to the working
  tree this revision produces, which lands as `<sha>`" costs one clause and removes the discouragement.
