## Summary

Design v1.105 at `b3be433` is the most heavily executed document I have audited here: I re-ran
essentially every published screen, fence and series from the shipped bytes and **over 150 figures
reproduced exactly** — the six-sha candidate-sweep series at both scopes, the ten-sha unstripped
fold, the seam-ordinal / span-ordinal / entry-naming / line-pin / taxonomy screens, the compliance
walks (104, 60, 2 fenced), the 30/35 corpus, `both=292 old_only=82 new_only=1` on both old guards,
the Setext census and its three controls, the eleven-shape ATX render, the `_field` per-member run,
the `argparse` matrix, the four-backtick bounder differential, the 81/81 mutation split and the
`7 of 49` AC sweep. Nothing I could execute was wrong. What I did find is three defects of a
different kind — prose that survived the edit around it: one paragraph that **contradicts a
paragraph v1.105 added 110 lines away** and still ships the per-revision premise that same
revision declares forbidden, two **round-relative sha descriptions** that went false on the version
bump and that the document's own screen states it cannot reach, and one **cross-document claim whose
sibling changed in the same commit** with no working-file re-check. All three sit at or beside the
site v1.105 rewrote, which is the shape the dispatch predicted.
Evidence: 14 files opened, ~95 greps/commands run.
(Files: design, plan, spec, impl-plan, `h-mad/SKILL.md`, `h-mad/tests/docsections.py`,
`docsections.json`, `test_h_mad_portable_timeout.py`, `test_h_mad_mutation_harness.py`,
`test_mutation_specs_clean.py`, `test_h_mad_context_budget_docs.py`,
`test_h_mad_collect_report_docs.py`, the prompt, plus the 30-file tracked corpus opened by two of
the document's own scripts; ~30 further blobs read through `git show`.)

## Must-fix
- **The candidate sweep's own definition still refuses to publish the working-file value, 110 lines
  above the new paragraph that publishes it — and the reason it gives is the exact per-revision
  premise v1.105 declares forbidden, and is false of v1.105.** §Scanning lines 809–812 read "Its
  value is stamped at `cf3a862` … and is deliberately not restated for the working file: this
  revision writes the labels into several of the candidate lines, so a working-file value would be a
  number this paragraph moved by being written." Lines 921–926 publish it (`63`) and lines 928–937
  state "a publication decision is never justified by what the current revision is about to write."
  Both are in the shipped blob: `git show b3be433:$D | grep -c 'deliberately not restated for the
  working file'` → `1`, and `grep -c 'The working-file value is published beside the blob series
  rather than withheld'` → `1` (`0` at `700c599` and `0` at `8c6539a` — the second sentence is
  v1.105's, the first is untouched by it: `git diff 8c6539a b3be433 -- $D | grep -c 'deliberately
  not restated'` → `0`). The surviving premise is also **falsified by the new paragraph's own
  differential**, which I ran: `diff <(git show 700c599:$D | grep -E "$RAISE") <(grep -E "$RAISE"
  $D)` prints one changed-line hunk, nothing added and nothing removed, and the whole-file count is
  `63` at `700c599` and `63` on the working file — so this revision wrote no new candidate line at
  all. This is v1.105's MUST 2 repaired at one of its two sites: the withholding claim lived in the
  definition paragraph *and* in the series paragraph, and only the series copy was struck.
  **Prescription**: strike "and is deliberately not restated for the working file" and its
  justification clause at the definition site, and point it at the published value below; the
  definition paragraph should carry only the needle, its scope (`over the head`) and the `cf3a862`
  stamp. **Class, and its residual**: the class is *a publication decision stated at more than one
  site*; the screen for it is that any sentence saying a figure is withheld must be greppable —
  `grep -c 'not restated for the working file\|deliberately not given for the working file'` over the
  head — and the residual is that a third phrasing of the same refusal is outside any such needle,
  so the real closure is that the figure is now published and no site may say otherwise.
  quote: docs/02-design/features/doc-block-exec.design.md › `and is deliberately not restated for the working file**: this revision writes the labels into` — and, 110 lines below it — `**The working-file value is published beside the blob series rather than withheld**`

- **Two live round-relative descriptions of a sha, both in the class §Scanning's sha-description
  rule forbids, both outside the shipped screen's reach, and one of them introduced by the very
  revision that added the screen.** The rule at lines 944–951 says a sha addressed by "its role in
  the current round" goes stale with no edit to the sentence and must be written as its hex.
  Residual (i) at line 966 names "the commit this revision answers" as the paradigm shape the
  shipped arm cannot see — and the document contains two instances of exactly that shape:
  (1) §Test Strategy line 2501, "the series reaches the freeze this revision answers instead of
  stopping three shas short of it". The ten-sha series ends at `700c599`. That was the freeze v1.104
  answered; v1.105's own entry says it is a delta self-review "authored against the working tree at
  `8c6539a`", so the description now denotes `8c6539a`, which the series does not include — it stops
  one sha short. The clause is **not present at `700c599`** and **is present at `8c6539a` and
  `b3be433`**, so v1.104's repair of this class introduced a new member of it, and v1.105's
  DECISION K sweep re-ran the ten *values* (`2/1/1/2/2/3/3/6/6/6`, which I reproduced exactly)
  without re-reading the description around them — "a true measurement inside a false description",
  this document's own name for the signature. For the record the fold is `6` at `8c6539a` too, so
  extending the series costs nothing.
  (2) §Test Strategy line 2550, "Evaluated against the blob this revision edits — `git show
  35698f9:$D`". `b3be433`'s parent is `8c6539a`; the blob this revision edits is not `35698f9`. The
  figure (`8`, which I reproduced at `35698f9`, at `8c6539a` and on the working file) is right; the
  description has been false since `6f0ee85`.
  **Prescription**: write both as hexes — "the series reaches `700c599`" (or extend it to `8c6539a`)
  and "Evaluated against the `35698f9` blob". **Class closure and its residual**: the shipped arm is
  `the (freeze|frozen|audited|stamped|current|latest|head) (sha|commit|blob)`, which requires the
  role word to be *followed* by the head noun; both instances put the head noun first and a
  round-deictic after it, so neither can ever be reached. A discriminating widened arm exists and I
  calibrated it: `grep -oiE '\b(the|that) (freeze|frozen|stamp|stamped|baseline|blob|commit|sha|tree)
  [a-z]{0,10} ?(this|the) (revision|round|entry|audit)'` over the folded head returns **3** on the
  working file and **1** over the `700c599` blob head — it discriminates. Residual, exactly: the
  third of those three hits is residual (i)'s own quoted example at line 966, so shipping this arm
  as a zero-expectation screen first requires that example to be *described* rather than reproduced,
  per this document's own rule that no screen's needle may be written literally in the scope it
  counts; and the arm is still a closed vocabulary, so "the tree under audit" or "the base this
  entry answers" remain unreached.
  quote: docs/02-design/features/doc-block-exec.design.md › `the drift is visible and dated rather than asserted, and the series reaches the freeze this` — and — `Evaluated against the blob this revision edits`

- **The new cross-document `_field` paragraph characterises a sibling that changed in the same
  commit, carries no working-file re-check, and its characterisation no longer matches the working
  plan.** Design lines 2042–2048 say the plan "states no `Cf` residual, which this document does",
  stamped `At 8c6539a`. That was true then: `git show 8c6539a:<plan> | grep -c 'the design states a
  residual this document does not carry'` → **0**. It is not the plan a reader will open:
  `git diff --stat 8c6539a b3be433 -- <plan>` reports 113 insertions, and at `b3be433` the plan's
  §Measurements carries a full mirror paragraph that names the design's `Cf` residual, publishes
  `grep -c 'Cf'` over the design (→ 1 body-scoped, 2 whole-file) and states that neither document
  adopts the other's residual — `grep -c` on that sentence at HEAD → **1**. So a reader following
  the design to the plan finds the plan visibly discussing `Cf`, against a design sentence that says
  it does not. This also breaks the rule the design adopted one revision earlier (v1.104 entry,
  decision E: two sibling-byte claims "now carry `700c599` **and a working-plan re-check**") and
  applies at its other cross-document site — §Test Plan lines 3080–3084 carry both arms ("returns
  `2` at `700c599` and `2` on the working plan"; "`1` and `1`"), which I verified. This new site
  carries the stamp only. **Prescription**: re-stamp to the working plan with a re-check command
  beside the `8c6539a` reading — e.g. `grep -c 'the design states a residual this document does not
  carry'` on the working plan → `1` — and reword to "the plan reports this residual as the design's
  and declines to adopt it" rather than "states no `Cf` residual". **Instance of**: the class is
  *every present-tense or stamped claim this design makes about a sibling's bytes*; the rule is that
  each carries a blob stamp **and** a working-file re-check, and the residual is that a sibling
  rewritten between the re-check and the commit is still missed — which is why the two arms must be
  the last thing run before the entry lands, as the setsid site's already are.
  quote: docs/02-design/features/doc-block-exec.design.md › `At \`8c6539a\` the plan's §Measurements carries a fence whose output line reads`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `states a residual this document does not carry — a code point some consumer treats as a boundary`

## Should-fix
- **A head-scoped screen's readings are labelled by a bare blob name in the same sentence that
  labels its sibling reading "the head of", 60 lines after the document legislates that exact
  distinction — no figure is wrong, the corpus name is.** Line 972: "over the `700c599` blob it
  returns three … over the head of the working file it returns two", under a premise that each is
  "named by its corpus". The screen is defined head-scoped (line 952, "The screen, run over the
  head:", with the `HEAD()` helper in the fence), so `3` and `2` are correct — I got them. But the
  literal corpus named yields different numbers: over the **whole** `700c599` blob the widened arm
  returns **7**, and the two shipped arms return **3** and **3** against the published "two lines and
  the second one" at line 963. Immediately above, lines 907–909 go out of their way to say the
  series corpus is "the **whole blob** … with no head/tail split, which is this series' corpus and is
  named here because it is *not* the head-only corpus the sweep's own definition above names" — so
  "blob" means whole-blob in one paragraph and head-of-blob two paragraphs later. A third site: the
  working-file `63` at lines 921–923 is published "beside the blob series" with a whole-file
  differential command, but the sentence never says whole-file, while the sweep's own definition
  (line 807) says "over the head" and the head-scoped working file is **61**. The v1.105 Version
  History entry gets this right ("63 whole-blob"); the body does not. **Prescription**: write "over
  the head of the `700c599` blob" at both screen sites and "whole-file" beside the `63`. **Class**:
  every reading of a scoped screen carries its scope word as well as its corpus; the residual is that
  a screen whose definition and reading agree still reads ambiguously when a neighbouring paragraph
  uses the same corpus noun at a different scope, so the scope word is not optional even when it is
  derivable.
  quote: docs/02-design/features/doc-block-exec.design.md › `rather than by "this file": over the \`700c599\` blob it returns three, one of which is the`

- **The `63` is explained by v1.104's edits alone while the command that carries it spans v1.104 and
  v1.105.** Line 922 stamps the reading "after the v1.105 entry below was written" and then explains
  the null with "because v1.104 reworded one raised line and added none". The differential it cites
  runs `700c599` → working file, which contains both revisions' edits; I ran it and it does show
  nothing added and nothing removed, so the figure holds — but the sentence leaves a reader unable to
  tell whether v1.105's own (large) entry was in scope. Say "because v1.104 reworded one raised line
  and neither it nor v1.105 added one".
  quote: docs/02-design/features/doc-block-exec.design.md › `bracketed needle after the v1.105 entry below was written: **63** — which is what the \`700c599\``

## Nit
- Line 971 stamps *both* widened-arm readings "each re-derived after the v1.105 entry below was
  written". A reading taken over a frozen blob cannot move with the working file's entry, so the
  stamp is vacuous on that arm and meaningful only on the working-file one; carrying it on both
  weakens the signal the stamp exists to give.
- Residual (i) at line 966 reproduces two literal instances of the shape it is telling the reader the
  screen cannot see ("the commit this revision answers", "the blob under audit"). Under this
  document's own rule that no screen's needle may be written literally inside the scope that screen
  counts, those examples should be described rather than quoted — and they are the sole reason the
  widened arm I calibrated above cannot be shipped at print-nothing today.
