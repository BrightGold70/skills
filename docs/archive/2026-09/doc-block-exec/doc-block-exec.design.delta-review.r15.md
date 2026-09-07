# Delta self-review r15 — design v1.105 → v1.106 (`00b961f`)

ADVISORY. Not a gate. Subject: `git show 00b961f -- docs/02-design/features/doc-block-exec.design.md`,
read against the working tree at `dfae038` (the four documents are byte-identical between `00b961f`
and HEAD; confirmed by `git diff 00b961f..HEAD` over the four paths returning empty).

## Summary

Every published figure this round added or re-stamped reproduces except in three places, and all
three sit inside text v1.106 itself wrote. I re-derived the candidate sweep (whole-file and head, at
five corpora), the blob series, the head-scoped companion, all three sha-description arms folded and
unfolded at four corpora, the widened cardinality arm, residual (iv)'s fold, the `pgid=` triage arm
with each hit's section, both compliance walks and the fence-aware split of the second, the
entry-naming stamp screen, the span-ordinal `$P`/`$W` series at six corpora, the re-anchor adjective
series, the ten-sha unstripped-fold ladder, the tail seam-ordinal screen, the `-F` needle, and both
sibling readings of the plan — 150+ of them reproduced byte-for-byte. The four must-fixes below are
one false differential, one stale figure two sentences from the figure that superseded it, one wrong
cardinal, and one present-tense claim about a sibling the same commit repaired. Worth noting for the
orchestrator: must 4 has a mirror — the spec's own v1.61 entry carries an `OWED ELSEWHERE` about the
design's AC-4.6 bare `pgid=` that `00b961f` fixed in the same commit, so each document now reports
the other's already-closed defect; the spec's copy sits in §Version History, which this feature
treats as a dated record, so it is not sibling breakage.

Evidence: 6 files opened, 150+ greps run.

## Must-fix

- The hop-by-hop differential this revision added is **false at its last hop**: `b3be433`→working
  prints a changed-line hunk, not nothing. Run exactly as the paragraph defines it,
  `diff <(git show b3be433:"$D" | grep -E "$RAISE") <(grep -E "$RAISE" "$D")` prints `61c61` — the
  §Test Plan re-anchor line, which carries a bracketed zero and is therefore raised by `$RAISE`, and
  which **this revision reworded** when it published the adjective count. So the accompanying
  attribution is wrong in the same sentence: v1.106 did change the raised set. The mechanism is this
  round's own signature — the DECISION-K sweep found the Test Plan withholding site after the entry
  landed, rewrote that raised line, and the differential three sections away was never re-run. The
  claim is load-bearing: it is what the paragraph offers instead of the pair of totals, and it says
  it is "checked here rather than inferred from the endpoints". Prescription: `b3be433`→working
  prints one changed-line hunk (the re-anchor line); `700c599`→working prints one hunk of **two**
  changed lines, not one; "v1.104 reworded one and the other two changed the raised set not at all"
  → v1.104 reworded one and v1.106 reworded one; the v1.106 §Version History entry repeats the error
  ("the raised-set differential empty on both hops after `8c6539a`") and takes a bracketed appended
  correction per this feature's practice since round six.
  quote: docs/02-design/features/doc-block-exec.design.md › `→working prints nothing.`

- The compliance-walk triage still states **`58`** as its mechanical prose-line count while the
  sentence two sentences above it publishes **`60`** — the figure this revision moved. Re-derived
  fence-aware on the shipped bytes: the prose walk raises `62`, `2` of them inside a fence, leaving
  `60`, of which five are disposed of by name and `55` remain — so `55` is right and the `58`
  justifying it is the superseded value. This is a wrong figure standing in a live body sentence, in
  a form a reader can lift and read as current, which is the exact shape this document's own v1.98
  rule forbids. Prescription: `58` → `60`.
  quote: docs/02-design/features/doc-block-exec.design.md › ``the `58` is mechanical and the disposition of each line``

- The new `pgid` grammar paragraph publishes a **wrong cardinal**: the AC-4.6 cell spelled the
  emitted field the other way **once** more, not twice. Measured on the blob the sentence describes:
  `git show b3be433:"$D" | grep '^| AC-4.6' | grep -oE 'pgid[=:]' | sort | uniq -c` returns exactly
  `1 pgid:` and `1 pgid=`; on the working file the same row returns `2 pgid:` and no bare form. The
  spec's independently authored v1.61 entry reaches the same reading in words — it names the collect
  clause, singular, as the row's other spelling. This is a new wrong figure in the round whose stated
  headline is that no published figure was wrong, and it is repeated verbatim in the v1.106
  §Version History entry. Prescription: "twice more" → "once more" at both sites, the entry by
  bracketed appendix.
  quote: docs/02-design/features/doc-block-exec.design.md › `inside a table cell that spells the same emitted field the other way twice more`

- The new paragraph's **`OWED ELSEWHERE` is false on the working tree and carries no stamp of any
  kind**, which breaks the rule this same revision states about a hundred lines earlier. The spec's
  FR-4 policy sentence now reads `` carries `pgid: "<n>"` so the operator can act `` — the
  constructor form is gone, and the spec body holds zero bare `pgid=`
  (`awk '/^## Version History$/{exit} {print}' <spec> | grep -c 'pgid='` → `0`; at `b3be433` the
  same sentence read `` carries `pgid=<n>` `` at line 378, under §FR-4, so the characterisation was
  exactly right when written). The spec was repaired in **this same commit**, `00b961f`. The
  violation is not merely the same-commit case that must 3's own residual concedes: the sentence
  carries neither a blob reading nor a working-file re-check, where the rule this revision publishes
  is that *every* stamped claim about a sibling's bytes carries both, run last. Prescription:
  v1.105 already settled the precedent for exactly this — the plan's `_field` discharge in the same
  commit was recorded as a discharge rather than left as a debt. Strike the body debt and record the
  discharge with its readings (`b3be433` 1, working plan 0); the §Version History copy is a dated
  record and stays.
  quote: docs/02-design/features/doc-block-exec.design.md › `the spec's FR-4 policy sentence describes *the verdict's detail* and then spells the field in the constructor form`

## Should-fix

- **Two residuals this revision added are written in the present tense about a state this same
  revision closed** — a class, not two instances. The withholding residual says the refusal *has*
  three sites and that the arm reaches only one of them; on the shipped bytes it has zero, and the
  arm returns `0` (it returns `1` at `b3be433`, so the measurement is right and only the corpus is
  unnamed). Residual (i) says two *live* members of the unreached shape *shipped* in §Test Strategy;
  the folded third arm returns `0` over the working head and `3` over the `b3be433` head, so no live
  member survives. Both paragraphs resolve themselves within a few sentences ("Both are now
  published with their corpora"; "That half of the residual is closed by a third arm"), which is why
  this is not a must — but each is an unstamped document-self claim of exactly the kind the
  entry-naming rule exists to prevent. Prescription: past-tense them and name the corpus they were
  true at (`b3be433`), as the v1.106 entry already does in its own prose ("THE WITHHOLDING CLASS
  HAD THREE SITES").

- **The new withholding arm is line-scoped and its target contains spaces**, against the rule
  residual (iv) invokes against arms (1) and (2) in the same revision — a detector whose target can
  contain a space folds first. Measured rather than assumed: folding the head changes nothing today
  (`1` at `b3be433` folded and unfolded, `0` on the working file folded and unfolded), so this is a
  rule-consistency gap and not a live miss. But it is the same class the round closed for the two
  older arms and left open on the arm it shipped: a hard wrap falling between `not restated` and
  `for the working file` defeats it silently. Prescription: fold the arm (its expected output is
  nothing, so folding cannot convert it into a triage list the way it would arm (2)), or state the
  wrap exposure as a named part of its residual.

- **Pre-existing, not fix-introduced, and reported because it is the class this round hunts**:
  §Invariant Compliance residual (iii) says "this revision did it from the shipped bytes" of the
  python-fence re-execution. The `6` / `4` / `2` figures are not in dispute — the head still holds
  10 python fences, unchanged since `8c6539a`, and this diff touches none of their bodies — but the
  deictic no longer resolves. v1.105's entry claims a sweep over "the shell screens as well as the
  python fences"; the v1.106 entry lists shell screens only, so on the shipped revision the sentence
  claims work its own record does not report. (That half is inferred from the entry's silence, not
  verified against a run.) Prescription: name the entry, as the eighteen neighbouring stamps do.

## Nit

- With the folded third arm shipped, "**Both shipped arms** are line-scoped" and "the shipped pair"
  in residual (iv) are a cardinal that the same paragraph then contradicts ("the only folded screen
  here is the third arm above"). Nobody is misled — arm (2) is named explicitly where the
  measurement matters — but "the two line-scoped arms" would cost one word and stop the reader
  reconciling it.
