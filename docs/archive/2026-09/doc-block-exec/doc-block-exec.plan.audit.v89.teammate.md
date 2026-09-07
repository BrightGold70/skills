## Summary

I read the plan at the gating freeze `bc4688e` (the working tree is byte-identical to it for all
four feature documents) and re-ran its published commands against the tree rather than against the
inlined copy. Almost every tree-derived figure reproduces exactly: the design-matrix walk
(81/85/85 and batch 86, `SKILL.md`-target 1 at all four), the 29-names and 8-row derivation blocks
byte-for-byte, the fence census 73 across 10 files with its any-language control 88, tracked `*.md`
30 and glob 35, the repo-wide `.py` censuses 8 and 25, `ls h-mad/scripts/*.py` 37 with its tracked
control 37, the SCRIPT_DIR census 13 against 88/89, the collect counts 2836/2574 with the `+22`
attributed to `b39d9dc` at 15 added `def test_` lines, the 49 spec AC anchors with a silent
duplicate check, the `_gate_bash_block()` def-plus-three call sites with their enclosing test names,
the four `docsections.json` rows with their `_killed_by` node IDs, and the `_second_surface()` block
census 7 with gate [4] and exec-codex [2]. Two findings are hard defects, both in §Next Steps: the
codex-leg ledger is stale at this document's own measurement commit and mislabels which commit that
is, and a cardinal contradicts the list printed four lines below it.
Evidence: 12 files opened, 71 greps run.

## Must-fix

- The codex-leg ledger publishes 87/87 stamped `fbc2ea0` and calls `fbc2ea0` this revision's measurement commit, while §Measurements says v1.105 is measured at `cac6edc` and at nothing else — two answers to *measured at* inside one revision, which is exactly the defect this document records both round-fifteen gating legs filing against v1.102 and claims to have abolished. It is a stale value and not only a stale label: I re-ran the paragraph's own two `git ls-tree` pipelines and the pair reads 88/88 at `cac6edc`, at `ccd8ebd`, at the freeze `bc4688e` and at HEAD `093c3ee`, against the published 87/87 at `fbc2ea0`. The paragraph's rule is that the pair is re-run at the commit each revision is measured at or the revision's own entry records that it was not run, and the v1.105 Version History entry does neither — its only ledger mention is the body-scoped 85 sweep listing the retired 72/85 and 84/85 series as sites that must not move. The paragraph even predicts this expiry and promises the run. Prescription: add a `cac6edc` row (88/88) to the series, restamp the headline sentence, and rewrite the deixis as "v1.104's measurement commit"; or record the non-run in the v1.105 entry and in the register.
  quote: docs/01-plan/features/doc-block-exec.plan.md › at `fbc2ea0` — this revision's one measurement commit — with the
  quote: docs/01-plan/features/doc-block-exec.plan.md › `fbc2ea0` **87/87**.
  quote: docs/01-plan/features/doc-block-exec.plan.md › rather than the phrase beside it. v1.105 is measured at `cac6edc`, and at nothing else** — v1.104
  quote: docs/01-plan/features/doc-block-exec.plan.md › `the moment round seventeen's own reports are committed, so v1.105 re-runs it at its own measurement`

- §Next Steps says the ledger series reports eight shas while the series printed four lines below it carries ten. Extracted and counted off the shipped bytes with a sha regex piped through `sort | uniq -c` over that fenced span, the members are `1cbddb7`, `700c599`, `8c6539a`, `b3be433`, `00b961f`, `dfae038`, `3f70eb3`, `af19d53`, `09e9307` and `fbc2ea0`, each exactly once. This is the free-standing-figure class the document repairs at the `pgid` census and again at the Deliverables total: the cardinal is not written as arithmetic over the surface it summarises, so it went short by two when the series was extended. Prescription: re-derive the cardinal from the series, or drop it and write "the shas listed below".
  quote: docs/01-plan/features/doc-block-exec.plan.md › `the series below reports only the eight shas it was run`

## Should-fix

- §Next Steps points at "the register below" while the register lives under §Measurements, above it. The register's nine bullets sit at lines 1735 through 1802 and §Next Steps opens at line 4309; a `grep -n` for register mentions returns nothing after that sentence. This repeats the inverted pointer the same batch fixed in the Deliverables cell, which had named "the FR-6 table below" when that table is above it, so it is an instance of a class the round already declared closed. Class over the axis: every relative pointer here is a placement claim and this document's own rule is to locate by heading. Residual: "the register below" occurs four times and three are correct, so the sweep is per-pointer against each site's own line number and cannot be done by value.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `was not run**, the register below being the only other place a non-run is admissible. **Residual,`

- Three repo-wide `.py` figures stamped `fbc2ea0` sit outside both the `cac6edc` re-run enumeration and the register, which this document itself calls a defect in the register rather than a licensed gap. `b39d9dc` adds two `.py` files to that corpus, `h-mad/tests/test_h_mad_agent_definitions.py` and `h-mad/tests/test_hmad_dispatch_exec.py`, so the corpus moved between `fbc2ea0` and `cac6edc`, yet the enumerated re-run set names only the two fence censuses that read 8 and 25. The three unnamed figures are the outside-the-two-roots `.py` file count (415), the bash-fence-bearing `.py` file count (5) and the extractor census (2). I ran all three at `fbc2ea0`, `cac6edc` and `bc4688e` and every one is unchanged, so no published value is wrong and this is an accounting gap rather than a wrong number. Class: a corpus the freeze moved whose census was neither re-run nor registered. Residual, exact: the enumeration of distinctly-scoped corpora in this document is by hand, so a corpus nobody has named stays invisible to the rule.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `figure outside both the moved set and this re-run set is a defect in the register below rather than`

- The second closure, over the repo-wide `.py` corpus, stops its series at `fbc2ea0` while its own rule says the pair is re-run at each freeze. Running `git diff --name-only 74e126f <sha> -- '*.py' | wc -l` returns 8 at `cac6edc` and at `bc4688e` against the published 6 at `fbc2ea0`, the two additions being the same two `h-mad/tests/*.py` files `b39d9dc` landed. The sentence enumerating "those 6 files" is therefore a stale population at the measurement commit, although its conclusion still holds: neither new file appears in the bash-fence-bearing `.py` file list, which stays at 5. Instance of the class in the bullet above. Prescription: extend the series with a `cac6edc` reading and re-word the enumeration as a reading at its own sha.
  quote: docs/01-plan/features/doc-block-exec.plan.md › settled relation. Only one of those 6 files moves a count here — `grammar_corpus.2026-09-03.cd979362.py`,

- The batch stamp has come due and can now be discharged, which the document said only a later round could do. Six sites carry it, five in one spelling and one in the other over the newline-collapsed body, matching what the Version History reports, and the derivation block states the expiry rule. The batch landed as `ccd8ebd`; I ran the block's two working-tree invocations against that blob and they return total 86 and `skill-md-target` 1, identical to the published batch reading, so the values are right and only the stamp form is owed. Because the gating freeze `bc4688e` is a later commit than the batch, a reader at this freeze can name the sha, and the two working-tree invocations are no longer reproducible as written once the tree moves again.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `one**: a working-tree reading is reproducible only until the batch lands, after which the same`

## Nit

- The unanchored carve-out reading is published at 24 (`8c6539a`) and 25 (`b3be433`) and returns 27 over the body this batch ships. The document says that figure is stamped to the working tree each revision produces and that this lands as that revision's landing commit, and the Version History reports several other post-edit re-runs, so this one is an omission rather than a wrong value.
