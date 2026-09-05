## Summary

ADVISORY delta review of `git show 00b961f -- docs/01-plan/features/doc-block-exec.plan.md`
(v1.100 → v1.101, 348 insertions / 91 deletions). This is **not a gate** and stamps nothing.
Every figure the diff publishes was re-executed at the shas it names: the `4e4a00c` self-count
(70 at `1cbddb7`/`700c599`/`8c6539a`/`b3be433`), the freeze triple (`32/20/12` · `32/21/11` ×2 ·
`37/21/16` ×2), the ledger series (`72/83` · `72/83` · `72/84` · `72/84`, `grep -c` teammate 11→12),
`rev-list 700c599..b3be433` = exactly `8c6539a` and `b3be433`, `--shortstat` 482/13, the row selector
`8/8/13/13`, the row-shape `15`, the unanchored `24`→`25`, screen one `32` at `6f0ee85` and
`84/84/92/92` with a `+8` delta, the ALL-CAPS control `3` and its `printf` positive `1`, screen two's
address `1` on the spec at five shas and `0` on the two siblings, its enumeration `122/225/228/262/271`,
the stamp driver `15/11/8`→`32` and `28/13/8`→`47`, the VH `screen-two leg` walk (v1.94–v1.99 + v1.101,
no v1.100), the `pgid` census verbatim, the design's `Verdict lines, one per run.` paragraph stating
exactly the plan's seven bare fields, the absence of any design heading matching `erdict`, and
`this revision` at `32`. All of those reproduce. The six musts below are the ones that do not, and
**five of the six are in text this diff wrote** — the fourth consecutive delta pass where every must
sits in the paragraph the previous round's must rewrote. Two of them are the round's own headline
claim falsified: a published figure that is wrong, and a cross-document state claim that the very
commit publishing it repaired. Out of scope and routed rather than filed: the spec's own v1.61
entry (`spec:1136`) carries the same stale owed-elsewhere claim about the design's AC-4.6 row, so
the class spans two surfaces and the spec author owes the matching correction.

Evidence: 8 files opened, 160 greps run.

## Must-fix

- The cardinal-list `≥ 2` check publishes **2** for the one member it was written to repair, and the
  tree gives **1** — so the check does not pass at the sha it is stamped at, for the member whose
  failure the check exists to prevent. Run exactly as the document spells it
  (`awk '/^## Version History/{exit}{print}' <doc> | tr '\n' ' ' | grep -oF <needle> | wc -l`),
  `the three admissible categories` returns **1** at `1cbddb7`, `700c599`, `8c6539a` and `b3be433`,
  in the joined grammar and line-scoped alike; the other five needles reproduce exactly
  (`2 2 5 2 2`). The parenthetical concedes the reading: at `b3be433` "the list still carried the
  broken member", so only the real surface exists and the count is 1, not 2. The v1.101 VH entry
  repeats the wrong `2`. This also breaks the sentence after it: at HEAD the six read `3 3 6 3 3 4`
  (re-derived), which is "exactly one higher" for five members and **three** higher for this one —
  its added occurrences are the list entry (`:1155`), the replacement sentence (`:1160`) and the
  check sentence (`:1168`), not the single self-quote the stated mechanism allows. Prescription:
  publish `1` at `b3be433`, state that this member alone fails the `≥ 2` check at the stamped sha
  *because* it is the member being repaired, and correct the delta sentence to `+1` for five and
  `+3` for the sixth with the three sites named.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `(the replacement's reading at that sha, where the`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `reads exactly one higher — 3, 3, 6, 3, 3 and 4 — because the sentence you are reading quotes each`

- The `pgid` denominator contradicts the census table printed three lines above it. The fenced
  census — re-run byte-for-byte at `b3be433` and reproducing exactly — gives `pgid=` 1 + 0 + 5 + 6 =
  **12** across the four documents, of which `LaunchFailed(` accounts for 0 + 0 + 4 + 6 = **10**. Ten
  of **twelve**, not ten of eleven. No reading of the table yields 11: the prose's own enumeration
  below it (spec one bare, design one bare + four kwargs, impl-plan six kwargs, plan none) sums to 12
  as well. The same "ten of the eleven" is in the v1.101 VH entry and in the commit message, so the
  error is carried on three surfaces. This is one published figure wrong in the round whose stated
  result is that none is. Prescription: `Ten of the twelve`, swept on all three surfaces.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `call and never reaches a verdict line, and a bare `=` field on the emitted line. Ten of the eleven`

- The paragraph's conclusion about the state of the feature is **false at the commit that lands it**,
  and the VH's owed-elsewhere list is false in the same two places. `00b961f` ships spec v1.61 and
  design v1.106 alongside this revision. Re-run at HEAD with the document's own census: spec `pgid=`
  **0** / `pgid:` **2**; design `pgid=` **4** of which `LaunchFailed(` **4**, i.e. **zero** non-kwarg
  bare hits; impl-plan unchanged quoted-only. The spec's AC-4.6 now reads `pgid: "<n>"` and its FR-4
  states the same seven bare fields exhaustively in both directions; the design's body says at
  `:2092` that the AC-4.6 row "is repaired at that row by this revision". So at the landing commit the
  four documents **do** agree, the design does **not** disagree with itself, and both repairs the
  sentence says are pending were made in the same commit. Prescription: keep the census stamped at
  `b3be433` and re-state the conclusion as a reading of that sha with the landing-commit outcome
  named — the two AC-4.6 repairs landed in `00b961f` — and append a bracketed correction to both
  `pgid` items in the VH's `OWED ELSEWHERE` list, which is this document's own convention for a
  landed entry (v1.97 and v1.98 both do it) rather than a strike. The other two items on that list
  are correct and still owed: the spec's
  `2486` in AC-6.4 and the absence of `BAD_ARGS` from AC-4.2's exit-0 enumeration both reproduce at
  HEAD (`:583`, `:367-368`).
  quote: docs/01-plan/features/doc-block-exec.plan.md › `quoted is **open across the feature** until the spec's AC-4.6 and the design's AC-4.6 row each`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `the spec owes its AC-4.6 pgid spelling and the 2486 in its AC-6.4 gate command and BAD_ARGS in AC-4.2's exit-0 enumeration; the design owes the bare pgid= in its own AC-4.6 row`

- A placement claim this diff wrote is refuted by this document 39 lines below it. `:939-941` says
  the two figures that moved are "beside it **in this section**"; the paragraph sits at `:939`, inside
  `§Measurements` (`:837`–`:2956` by `grep -nE '^#{2,4} '`), and the codex-leg ledger is published in
  `§Next Steps` (`:3183`+), which this same document states at `:979`. The `§Measurements` closure
  explicitly excludes the ledger's corpus (`:3199`: "Its corpus is `docs/01-plan/features/`, which the
  §Measurements closure explicitly excludes"), so the ledger is not merely elsewhere, it is
  definitionally outside this section. Only the `the freeze` triple is in-section. This is the same
  class as the impl-plan's round-fourteen must, in the paragraph this round rewrote. Prescription:
  "the two figures beside it — the `the freeze` triple in this section and the codex-leg ledger in
  §Next Steps — both did move".
  quote: docs/01-plan/features/doc-block-exec.plan.md › `not evidence it need not be re-taken**, and the two figures beside it in this section both did move`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `ledger in §Next Steps — go stale inside the sentence that forbids carrying it: its teammate half`

- The register's new per-member lead asserts a property of its own list that the same list's residual
  denies, and that four of the six bullets falsify on sight. `:1192-1193` claims **the revision and
  the commit**; `:1255-1257` states "only two of the six entries above name an executing *revision*
  … the other four name the **commit or version their reading is stamped at**"; bullet three
  (`:1232-1233`) names neither, being stamped "`markdown-it-py 2.2.0` and `4.2.0` and by no sha". The
  document already has the correct form 23 lines later at `:1215` ("the revision **or** commit its
  last execution is stamped at"), so the defect is one conjunction in the lead the must rewrote.
  **The residual at `:1255` discloses the gap and does not discharge it**: the register exists to be
  read by whoever decides what still needs re-running, and that reader takes the lead's promise at
  face value for four of the six members before ever reaching the residual 63 lines down — which is
  the same over-claim-then-retract shape this document files against itself elsewhere. Prescription: change
  `and` to `or` at `:1192` and add the corpus bullet's "neither" case explicitly, since `or` still
  over-claims for it.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `per-member statement: **every member below now names the revision and the commit at which it was`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `entries above name an executing *revision* (`v1.99` for the stdlib block, `v1.97` for the`

- Residual (2)'s new "no longer hypothetical" demonstration is published in a grammar that has no
  sha — the round's own GRAMMAR rule, broken in the one sentence whose subject is
  working-tree-versus-commit confusion. `git status --porcelain` reads the working tree and has no
  form that runs "at `b3be433`", so the published **2** is not re-derivable by any reader at any
  commit, and the sentence gives no other way to reconstruct the state it means. The consequence is
  visible immediately: run as written at HEAD, `git status --porcelain docs/01-plan/features/ |
  grep -c 'doc-block-exec.plan.audit'` returns **0**, because the two v85 reports landed in
  `00b961f`, so a reader following the instruction gets `0` where the document says `2` and both
  ledger forms read **85** (`git ls-tree` at HEAD: codex `72`, teammate `85`) with nothing
  diverging. The paragraph's own preceding residual predicted exactly that ("the teammate half
  becomes `85` the moment they land"), so the two sentences describe different worlds without
  saying which reader is in which. Prescription: record the `2` the way the `25`→`26`→`25` excursion two sections away is
  recorded — as an observation of an uncommitted intermediate tree, explicitly not a figure — and
  drop "right now"; the divergence itself is demonstrable at a sha only by pairing `git ls-tree
  <sha>` with a working-tree reading taken at a named moment.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `**It is diverging right`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `returned **0** when v1.98 wrote this sentence and returns **2** at `b3be433` — this round's two v85`

## Should-fix

- The spec-immobility premise is true at `b3be433` and broken at the landing commit, so it cannot be
  carried into v1.102 and the closure paragraph should say so now rather than have the next round
  discover it. `git diff --stat cf3a862 b3be433 -- <spec>` is empty as published, and the parenthetical
  "the spec is still at v1.60 at `b3be433`" reproduces; but `00b961f` ships spec v1.61 and
  `git diff --stat cf3a862 HEAD -- <spec>` reports 41 insertions / 15 deletions. The census *value*
  survives — `git show HEAD:<spec> | grep -oE '^  \$ [a-zA-Z0-9._-]+' | sort | uniq -c` still gives 21
  openers over 11 tokens — so nothing published is wrong; what is gone is the argument the value rests
  on. This is the same shape as the ledger must one round earlier: a premise about a sibling's
  immobility, taken at the freeze, invalidated by the revision's own commit. Prescription: one clause
  saying the premise is retired at `00b961f` and the census must be re-derived rather than argued next
  round.

- The screen-two re-run's scoping clause survives its own commit, and saying so costs one clause. The
  six legs are re-executed "against the spec's enumeration *as that document ships it at `b3be433`*",
  and the spec moved at `00b961f`. The enumeration block is in fact unaffected: `diff` of the fenced
  program and its 14 following lines between `b3be433` and HEAD differs only in `v1.60 draft` →
  `v1.61 draft`, prose below the fence, and `grep -cE '^  \$ awk '` still returns `1` on the spec at
  HEAD. So the re-run is still good — but the document's own rule is that a checker's stability is
  measured, not assumed, and it has already moved once. Prescription: state the `b3be433`→`00b961f`
  comparison, or say the legs re-enter the register at the next revision because the checker's
  document moved beneath them.

- The register's residual states a member's status with the deixis the register above it bans, in the
  paragraph defining the ban: `:1259` reads "it says the reading is not this revision's". The rule as
  written is "the revision is named by number and never by *this* one", and the exception the document
  grants — "a revision describing its own act at the moment it acts" — does not cover a sentence
  telling a *later* reader how to interpret every stamp in the list. Not a must because the stamps
  themselves carry their own shas and versions, so no member's status is actually ambiguous.
  Prescription: "not v1.101's".

## Nit

- `:1215` and `:1192` are two lead sentences for the same list, 23 lines apart, saying the same
  thing with different quantifiers (`or` vs `and`). Even once the `and` is fixed, one of the two is
  redundant, and a duplicated lead is the copy-that-drifts shape this document argues against
  everywhere else.
