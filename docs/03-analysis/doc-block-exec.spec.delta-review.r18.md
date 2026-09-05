# doc-block-exec spec delta review — r18 (v1.63 → v1.64)

Subject: `git diff cac6edc -- docs/01-plan/features/doc-block-exec.spec.md`, six hunks, +74/−22.
Freeze `cac6edc`, HEAD `f6849bb`, batch staged and uncommitted (working tree == index).
ADVISORY, not gating. No second surface, no exit-gate claim.

## Summary

Every substantive decision in this revision closes what it claims, and every tree-derived figure I
re-ran reproduced exactly: `2836`/`2574` from two separate shell invocations, the `+88` arithmetic
on the retired `2748`/`2486` pair, the `aaab`/`abc` span enumerations on 3.11.8, both
`__suppress_context__` branches reading `True`, the no-token triple `89`/`101`/`104`, the whole
value sweep at the freeze (`2814 1, 2552 1, 2809 3, 2547 3, 2836 0, 2574 0`), and the
`*.py`-unchanged freeze predicate (`0` and `0`). The two must-fixes are both in one sentence of the
v1.64 Version History entry, and both are the same species the entry was written to close: a
self-count stated in the present tense that the revision's own text moves, and a population
counted by token rather than by the construct the sentence names.
Verdict: FAIL to revision — 2 must, 3 should, 1 nit; the ACs themselves are sound.
Evidence: 4 files opened, 68 greps run, plus 2 pytest collections and 2 Python reproductions.

## Must-fix

- The v1.64 entry publishes `__suppress_context__` as `0 after this revision` and it is `6`
  (`2` in the body, `4` inside the entry itself) — a published absence claim contradicted by the
  same revision's own text, in a document whose standing rule is that every screen is re-run after
  the last edit. Measured: `git show cac6edc:$S | tr '\n' ' ' | grep -oF '__suppress_context__' | wc -l`
  → `0` (the freeze half is correct), and the same command over the working file → `6`; body-scoped
  (Version History cut) → `2`, at `doc-block-exec.spec.md:407` and `:408`, both lines this revision
  added. **instance of: a present-tense self-count of a token the revision's own prose introduces.**
  The class has a second member in the same sentence — `AC-3.14 has 7 sites here — one AC body, six
  Version History entries` — where `7` is correct at `cac6edc` (measured, collapsed: `7`) and the
  working file reads `11` (`7` + `3` in the v1.64 entry + `1` in the new AC body), so the
  two-part partition no longer accounts for the sites. The same entry's VALUE SWEEP does it
  correctly by labelling its readings `before`; the rule over the axis is that any self-count in
  this entry names the half it was taken at, and the residual is a count a *later* entry adds.
  Prescription: `0 at the freeze and 6 after this revision`, and `7 sites at the freeze, 11 after`.
  quote: docs/01-plan/features/doc-block-exec.spec.md › `Confirmed and reported rather than assumed: __suppress_context__ occurs 0 times in this document at the freeze (tr '\n' ' ' | grep -oF | wc -l) and 0 after this revision`
- `the eight sentences that assert False are design 4 / impl-plan 4` mischaracterises what was
  counted: `4` and `4` are occurrences of the **token** `__suppress_context__`, not sentences
  asserting `False`, and the design asserts `False` in **none** of its four. Measured at the freeze,
  `git show cac6edc:<doc> | tr '\n' ' ' | grep -oE '__suppress_context__.{0,200}' | grep -c 'False'`
  → design `0`, impl-plan `1`; widening from 30 to 200 characters does not change it, and the
  design does carry `False` 49 times elsewhere in the document, so the token is common and simply
  not attached to this one. Reading the four design spans: three assert `to **True**` / `True`, and
  the fourth is a Python format string (`% (pending, e.__cause__, e.__context__, e.__suppress_context__)`),
  which is not a sentence at all. The entry contradicts itself two sentences later, where it names
  the real population correctly — the impl-plan's `is False` plus its mutation-row restatement, and
  no design site. **instance of: counting a string without checking which construct it sits in**
  (the recorded GRAMMAR species). Prescription: `the token occurs 4 times in the design and 4 in
  the impl-plan; exactly one of those eight asserts False, in the impl-plan, restated once in its
  cleanup-chain mutation row, and the design asserts True in three and uses the fourth inside a
  Python format string`.
  quote: docs/01-plan/features/doc-block-exec.spec.md › `the eight sentences that assert False are design 4 / impl-plan 4 and belong to those authors`

## Should-fix

- The v1.64 entry carries no post-edit screen block, which is the mechanism that let both
  must-fixes through. Measured over the entry alone (line 1482): `PRECHECK` 0, `control string` 0,
  `opener` 0, `py-pin` 0, `split_only` 0, `awk needle` 0, `class-closure` 0 — where v1.61, v1.62
  and v1.63 each close with all of them. Only the VALUE SWEEP and the no-token move are published.
  Nothing is hidden behind the omission: I ran
  `python3.11 h-mad/scripts/h_mad_precheck_doc.py --phase spec --root /Users/kimhawk/orca/skills docs/01-plan/features/doc-block-exec.spec.md`
  → `PASS issues=0`, and every advisory is a known-exempt kind (LINEPIN on FR-6's bare ordinals,
  PATH on the modules 5d/5e build, STALESHA on the historic stamps, and every COUNT line at
  L1431–L1481, all inside the Version History that starts at L1416). The debt is the record, not
  the state; a re-run block would have moved `0` to `6` before the entry shipped.
- The design's offset wording is still v1.63's and now disagrees with the spec — a divergence the
  batch does not close. The spec's new rule is `the smallest character index shared by any
  intersecting span pair of the two keys`; the design's grammar paragraph in the working file still
  reads `<offset>` is the **smallest character index the two matched spans share**` and its next
  paragraph mandates the overlapping enumeration, which is exactly the condition under which one
  key pair can have several intersecting span pairs. The design's pseudocode agrees with the spec
  (`p, o = (a[2], b[2]), max(a[0], b[0])` then `first[p] = min(first...)`), so this is prose against
  prose on a diagnostic three documents must spell identically, not an algorithm defect. Routed to
  the design author, not to the spec.
- The OWED-BY-OTHER-DOCUMENTS paragraph is honestly stamped and already discharged by the same
  batch, which this document's own v1.62 correction (1) requires a note for. Both claims were TRUE
  at `cac6edc` — I confirmed the impl-plan carried `__suppress_context__` is False` there and the
  design carried `at "0"` once — and both are gone from the working files: the impl-plan now reads
  `__cause__` IDENTITY, and that is the whole of what it adds` with `is`, and the design's AC-matrix
  row now reads `intersect: "ab" "bc" "1"` with its two surviving `at "0"` occurrences quoted as
  retired history. After the batch commits, this paragraph wants a bracketed note that both were
  discharged in the same commit, with the one exception above (the design's offset wording) named
  as still open.

## Nit

- `101` at `cac6edc` — the value v1.63 published as its draft half` is loose on provenance. The
  v1.63 entry published `100` (`no-token scale 89 at fbc2ea0 and 100 over the draft`); its REOPEN
  moved the body figure to `101` and says so without restamping the entry. The number is right —
  measured `101` at `cac6edc` — so nothing published is wrong; the phrase should read "the value
  v1.63's body carried after its reopen".
