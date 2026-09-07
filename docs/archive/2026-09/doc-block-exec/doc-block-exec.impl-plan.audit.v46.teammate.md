## Summary

Gating pass on `docs/01-plan/features/doc-block-exec.impl-plan.md` v1.51 at the corrected final
freeze **`3f70eb3`**. Every figure below was re-derived at `3f70eb3` after two freeze corrections
(`59cc2ad` → `7b182b0` → `3f70eb3`); I verified for myself that the impl-plan blob is
byte-identical at `7b182b0` and `3f70eb3` (`cmp` on the two `git show` blobs) rather than taking
that on report, and I re-read the v1.51 Version History entry in full at the new sha rather than
relying on the superseded `--stat` divergence figure. One must-fix survives the move unchanged;
it is a stamp error, not a wrong reading. The self-contradiction I filed at `59cc2ad` — a body
claiming to publish no glob cardinal while quoting one — is **genuinely repaired** and is withdrawn:
body hits are **0** at `3f70eb3` including wrap-collapsed, against **1** at `59cc2ad`.
Everything else I could re-derive reproduced exactly: all 54 `path:line` pins, the twelve secondary
AST-census pins, the 20-name exception hierarchy, the 25/29 `__all__` split, the 58-entry
`_SCANNED` / 37 `.py` / 160 collected-node figures, the four shipped `docsections.json` rows with
both mutation payloads, the marker / restated-cardinal / `.py:` / `SKILL` screens, the four-sha
sweep series read against each revision's own needle set, the `DETAIL_KEYS` ↔ design
cross-document correspondence, and `PRECHECK: PASS issues=0`.
Evidence: 27 files opened, 152 greps run.

## Must-fix

- **The per-needle sweep reading that closes delta must-3 is published under the wrong sha, and it survives the freeze correction unchanged: the values are this revision's own, not `dfae038`'s.** At `dfae038` the debt word reads **24** and the sweep returns **26**; the published 23 / 25 are the values at `59cc2ad`, `7b182b0` and `3f70eb3` alike. Re-derived at the final freeze in one script, same corpus, same body definition, same grammar, only the sha varying — `dfae038` 24 / 26, `59cc2ad` 23 / 25, `7b182b0` 23 / 25, `3f70eb3` 23 / 25 — with an assertion on body length so an empty read could not pass as a zero. The sentence still stands at `:1093`–`:1095` and `grep -cF 'the debt word **23**'` is **2** at `3f70eb3` (body site plus the Version History item (3) at `:3392`). **The document contradicts itself over this, twice**: at `:1111`–`:1113` it publishes the series as *`26` on the tree v1.50 ships and `25` on the tree v1.51 ships*, and `dfae038` **is** the tree v1.50 ships (`git show dfae038:<this file> | grep -oE '^- v1\.[0-9]+' | tail -1` → `v1.50`); the same contradiction sits inside the single v1.51 Version History entry, which publishes both figures. **This is not the `three`→`four` species — nothing was miscounted; a correct reading was stamped at the commit the C2 broadcast named rather than at the commit it was taken on.** Mechanism, because it will recur across the batch: C2 told the authors the batch stamps `dfae038`, and that instruction was applied to a reading taken over the author's own new bytes. **Close the class, not the instance**: a reading taken over *this revision's own body* is stamped to the tree the revision ships, and only an entry's own freeze-sha field takes the batch sha — which is the boundary C2 itself drew ("every reading stamped at a BLOB stays there"). Two sites carry the instance, `:1093`–`:1095` and the Version History item (3) at `:3392`; the residual is every other reading in this document taken over its own post-edit body, which is the population the first should-fix below enumerates. The sibling authors received the same C2 broadcast, so the class is worth screening for in design, plan and spec.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `the debt word **23**`
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `**26** on the tree v1.50 ships and **25** on the tree v1.51 ships`

## Should-fix

- **The shipping-revision stamp rule stated at `:398`–`:400` still has three live members at `3f70eb3` — the same shape impl-plan audit v45 filed against v1.49.** The rule is that a screen site is stamped to the revision that ships it, not to the revision whose repair last moved it; the cited precedent is v1.49 leaving a site reading `the tree v1.48 ships` while shipping further body edits. v1.51 ships further body edits and leaves three screen sites reading `the tree v1.50 ships`: the marker screen at `:394`, the restated-cardinal screen at `:587`, and the two `SKILL` screens at `:884` — the last of which states the rule it violates inside its own parenthesis. Positions re-derived at `3f70eb3`, not carried from `59cc2ad`. **Filed as a should and not a must on the precedent's own severity rather than on my assumption about it**: v45's item sits in that report's `## Should-fix` section (`docs/01-plan/features/doc-block-exec.impl-plan.audit.v45.teammate.md`, `## Should-fix` at `:19`, the item at `:24`, `## Nit` at `:32`), and **no published figure here is wrong** — run at both shas, the marker screen gives body **5** / file **5** / five per-marker lines each count **1**, and the restated-cardinal screen gives body **0** lines / **0** occurrences and whole-file **2** lines / **3** occurrences, identical at `dfae038` and at the shipping tree; both `SKILL` screens read **0** / **0** and the `.py:` screens read **49** occurrences / **0** bare-filename. The defect is the stamp, and the harm is the one the rule names: the site and the Version History disagree about which tree the readings belong to, since the v1.51 entry reports them re-run "after this revision's last edit". **Close the class**: the three sites move to `the tree v1.51 ships`, and the rule gains its enforcement condition — a screen site's stamp is rewritten in the same edit that re-runs it, so re-running and re-stamping cannot come apart. **Residual, stated because its disposition differs and I am not filing it**: `:964`'s locator census also reads `the tree v1.50 ships` but explicitly labels its two lists as v1.50's, which is a blob-stamped historical reading and not a re-run screen; `:768`, `:775`, `:781` and `:1111` are historical series members and are correct. `instance of: a reading over this document's own body stamped to a tree other than the one that ships it` — the same class the must above is the other half of.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `On the tree v1.50 ships, re-run **after** v1.50's own edits landed rather than`
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `both returning **0** on the tree v1.50 ships and both re-run after`

- **A count handed to me about this document is wrong in a way that matters for the next sweep, and it is a GRAMMAR error rather than an arithmetic one.** The dispatch states the Version History carries **3** occurrences of the glob cardinal. Measured at `3f70eb3`, the loose phrase `(three|3) of the (eight|8)` returns **4** Version-History lines — but only **2** of those four are the glob cardinal (`:3391` v1.50's original, `:3392` v1.51 quoting it as a dated record). The other two are different subjects entirely: `:3378` v1.37 counts *killers* in `docsections.json`, and `:3386` v1.45 counts *precheck spans* for the `os_error` specimen. So the true figures are **4** for the phrase and **2** for the cardinal, and **3** is neither. Nothing in the document is wrong — all four are correct in their own contexts and all are dated records — but a future sweep calibrated on `3` will read a correct document as drifted in one grammar and a drifted one as correct in the other. Prescription: state which construct is being counted whenever this phrase is swept, exactly as constraint 4 of the r15 sheet requires for `pgid=`.

## Nit

- The pre-mutation check's span is cited as `h-mad/scripts/h_mad_mutation_harness.py:630-642` in the body at `:1484` and as `:630-641` in the Version History at `:3378`. The body's span is correct — `:642` is the `continue` that makes the check a refusal — and the Version History is a dated record, so nothing is owed; noting it only because a 5d reader who takes the narrower span reads the row as skipped rather than refused.

- `:2405`'s three glob exclusions are now spelled uniformly (`references/*.md`, `hooks/*.sh`, `scripts/*.sh`) beside the one inclusion, which answers the r15 nit; the sentence still runs to seven clauses before the reader reaches the inclusion, so the thing the paragraph most needs a reader to see arrives last.

---

**Withdrawn at this freeze, recorded so the delta is readable.** At `59cc2ad` I filed a should-fix
that the `_SCANNED` paragraph asserted no cardinal of the glob sources is published *here* and then
published one verbatim inside a quotation of v1.50's wrong sentence. **That is repaired and I
verified it myself rather than accepting the author's report**: the body carries **0** hits for
`(three|3) of the (eight|8)` at `3f70eb3`, both line-scoped and after collapsing hard wraps
(`re.sub(r'\s+',' ')` over the whole body), against **1** at `59cc2ad` — and the promised bracketed
correction is present in the v1.50 entry, opening `[Bracketed correction, added at v1.51, delta
self-review r15: **the cardinal is wrong, and it is wrong against the list printed one line above
it in the body**`. The repair is the DESCRIBE-not-quote form, which is the right disposition.

**The two items flagged live in the dispatch, both re-derived at `3f70eb3`.**
*`DETAIL_KEYS` — HOLDS, and the pin I was given is stale rather than wrong.* The declaration is at
impl-plan `:2510`, not the `:2434` the r15 sheet pinned, and carries **11** members. The design's
alternation is at design **`:2102`**, not the `:2080` the dispatch names — `:2080` at this freeze is
the `--heading` field-forging paragraph, an unrelated subject. At `:2102` the alternation reads
``grep -oE '(missing_key|overlap|duplicate_key|os_error|pgid|written|failed|skipped|verify|stream|leftover)='``
and is **member-for-member identical to `DETAIL_KEYS`, order included** (compared programmatically,
`dk == alt` → `True`), with `duplicate_key` present, so the design's r15 must is landed and neither
document drifted. `grep -rn DETAIL_KEYS h-mad/` returns **0**, confirmed — there is no symbol to
test either document against before 5d/5e, so this correspondence is currently held by prose on
both sides and by nothing mechanical. That is the residual, and it is the one worth carrying into
5d: the first thing the module must do is make `DETAIL_KEYS` real so AC-4.5's registry walk has
something to walk.
*The plan's four design `§Scanning` citations — NOT CHECKED.* They are the plan's to fix and my leg
did not touch those sites; I am naming that rather than letting the silence read as clearance.

**Scope of this leg, and what I did not check.** One gating surface: `codex` is exhausted until
2026-09-07 11:28, so **no two-surface clean and no exit gate is claimed or supported by this
report**. I have never been scored against a labelled corpus and I share a model family with the
authoring surface, so a real codex round is owed on the same tree before anything gated here is
treated as settled.

Not checked, named rather than left to read as absence: the repository test suite (this loop still
never runs it); the Version History's 123-reading stamp table over its 17 shas and the
`h-mad/`/`handoff/` interval closures under it; nine of the roughly fifteen sibling
`§`-references — I re-derived six against both `dfae038` and the shipping tree (design
`§Test Strategy` last paragraph, `§API`, `§Implementation Order` Task 3, `§Test Plan` wire table,
plan `§Measurements` ×2, all six holding at both) and took the rest on the document's own stated
reading; the 81-row `doc_block_exec.json` and 8-row `doc_block_exec_wire.json`, which do not exist
before 5d; and the wrapped/flat precheck probe under both `bash` and `zsh`.

**File-integrity note.** An earlier copy of this report was overwritten on disk by a placeholder
stub reading `IN PROGRESS` with `None` in all three finding sections and `Evidence: 0 files opened,
0 greps run`. That stub was not mine and would have scored as a clean. This is the authoritative
content, re-derived at `3f70eb3`; the `.done` marker was re-created after this write.
