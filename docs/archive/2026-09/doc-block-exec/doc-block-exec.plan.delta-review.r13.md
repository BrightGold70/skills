# Delta review — plan v1.96 → v1.97 (`git show 1cbddb7 -- docs/01-plan/features/doc-block-exec.plan.md`)

**This pass is ADVISORY. It is not a gate and it stamps nothing.** Subject is the diff only, not
v1.97 as a whole.

## Summary

Both must-fixes are closed on their stated axes and both go beyond the instance the v83 reviewer
named: MUST 1's three-grep table reproduces in **8 of its 9 published cells** — I re-ran every one —
including the third member the audit report and the orchestrator brief both got wrong (`four
screen-two legs` is present body-scoped at **1** at *both* `7982c18` and `06ef40f` and absent at
`8909ec4`, so v1.94 shipped it and v1.95 carried it, exactly as v1.97 says); MUST 2's ledger
re-derives as `72`/`83` at `7d8e797` and still reads `72`/`83` at HEAD `1cbddb7`, with both stated
residuals confirmed (`grep -c` gives 72/**11**; `git status --porcelain docs/01-plan/features/ |
grep -c 'doc-block-exec.plan.audit'` → **0**, so the old `ls` form agrees only by accident today).
The ninth cell does not reproduce and it falsifies the revision's own DECISION Q self-score, which
is Must-fix 1 below. The revision broke no sibling: all **13** impl-plan sibling locators still
return exactly **1** at `1cbddb7`, and every member of the `docs/`-scoped closure returns its
published value at `4e4a00c`, `7d8e797` **and** `1cbddb7`. On the v83 report's `ELEVEN`/`TEN`: it is
**internally consistent**, not contradictory — must-2 enumerates nine items of which one is
"AC-6.1's two spec greps", giving ten sibling-derived figures, plus the codex ledger as the eleventh
member that moved. v1.97's list differs from it by *membership*, not just count: it adds the
spec-immobility premise and drops the ledger (handled in §Next Steps), so ten grammatical items.
Evidence: 6 files opened, 97 greps run.

## Must-fix

- The new members table publishes a figure that its own stated command does not return, and the
  revision's DECISION Q self-score of 22/22 rests on it. Row 3, column 2 (line 870) publishes
  `three importing test files` → **2** at `7982c18`. The command the table names for every cell
  (lines 878–879) is `git show <commit>:<doc> | awk '/^## Version History/{exit}{print}' | grep -cF
  '<needle>'`; run at `7982c18` it returns **1** (the single hit is body line 1005, `document's
  feet.** The re-derivation paragraph above reads "three importing test files". Fed to`). Whole-file
  returns **4**; body-scoped at `06ef40f` returns **1**; body-scoped at `1cbddb7` returns **4**. No
  scope reaches 2. The *conclusion* survives — 1 ≥ 1, so the multi-word-gap probe was indeed already
  in that body and the six-leg walk is unaffected — but the published integer is refuted, and so is
  the Version History claim at line 2529 that all 22 property claims were executed. This is one
  finding at two spans: the cell and the self-score. `instance of:` the class the table itself
  exists to close (a cardinal published without running the command beside it) — the residual the
  table does not state is that its own cells are property claims subject to the same rule, so the
  rule should read "every cell in this table is re-run when the table is edited", with residual "a
  cell whose command differs from the stated form is outside the check" (see the Should-fix below).
  quote: docs/01-plan/features/doc-block-exec.plan.md › `both already in that body (`three importing test files` → **2**, `printf 'zero files` → **1**)`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `DECISION Q for v1.97: 22 property/population claims shipped, 22 executed`

- The closure paragraph publishes a cardinal over its member list in the sentence immediately before
  the sentence that says it deliberately publishes none, and gives the reason a cardinal there would
  be a defect. Line 811–812 leads with "as ten re-stamps"; line 812–814 then says the members are
  "listed, never counted" because "a cardinal over it would be exactly the population-short-by-N
  claim the paragraph above writes a rule against". The number is not *wrong* — I count ten
  grammatical members (design `seven-plus-two-plus`; design mutation-target; the 49 AC anchors;
  AC-6.1's two spec greps; spec `len(tuple)`; spec `^  $ awk ` locator; the enumeration-residual
  needle; the spec opener census; impl-plan `find_heading`; the spec-immobility premise) — but under
  the v83 report's own convention, which counts AC-6.1's two greps as two figures, the same list is
  eleven. So the lead sentence is both forbidden by its successor and ambiguous under the counting
  convention the finding it answers used. Prescription: drop the numeral ("stated as one closure
  rather than as one re-stamp per member"), which costs nothing and removes a figure that must be
  maintained on every future edit to the list.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `**The `docs/`-scoped figures this revision re-derived, stated as one closure rather than as ten`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `re-stamps.** The members are **listed, never counted**, and that distinction is the point: this`

## Should-fix

- "Every grep cell above is one command, `<the grep -cF form>`" (lines 878–879) is false for column 2
  of rows 1 and 2. Row 1 col 2's **13** *does* reproduce — I ran it — but only with a different
  command, the `-E` stamp driver `grep -cE '(python3?[.:]? ?[0-9]+\.[0-9]+\.[0-9]+|awk version
  [0-9]|markdown-it-py [0-9])'` over the `8909ec4` body (whole-file gives 16). Row 2 col 2's **five**
  is a hand reading of the eight-row carve-out table at `7982c18` (I confirmed the five OS/runtime
  rows at body lines 1137, 1139, 1140, 1141, 1142; the other three are the `awk` probe, the scanner
  corpus and the wrapper) and involves no grep at all. The defect is the blanket claim, not the
  figures. Scope the sentence to the cells written in `<needle> → N` form, and name the driver for
  row 1 col 2 inline so the cell is runnable without scrolling.

- The register's population statement no longer describes its members, and v1.97 widened the gap.
  Line 846–847 says the population "is driven by the carve-out table below, not by recall". The
  member added this revision — the body-scoped `74e126f` self-counts — is not a carve-out row:
  `74e126f` appears in **0** of the eight table rows at lines 1526–1533. Nor are the `doc-auditor.md`
  fence-toggle readings, the Setext differential, or the six screen-two legs. Restate the driver as
  the union of the carve-out table and the figures the closure paragraph excludes, or the statement
  reads as a completeness claim the list does not satisfy.

- The register re-states `30`/`26`/`11` (lines 912–913) while lines 764–781 already own those three
  figures with their commands, and the register copy carries no derivation for "narrowed" — I had to
  read lines 776–777 to find `... | grep '74e126f' | grep -cE 'h-mad|handoff'` and reproduce **11**
  at `4e4a00c` (also 11 at `cf3a862` and at `1cbddb7`; whole-file 30 and body 26 at `4e4a00c` both
  reproduce). This document's own rule at line 162 is that "a pointer to the one surface that owns a
  measurement never drifts, a second copy does". Make the register entry a pointer to the owning
  paragraph rather than a second copy of its integers.

- The round names two shas and the ledger reads differently at each. Version History line 2529 says
  "freeze sha 6dcb70f, authored against 7d8e797"; the body names `6dcb70f` **0** times and `7d8e797`
  **23** times and states "v1.97 is measured at `7d8e797`". At `6dcb70f` the teammate half of the
  ledger is **82**, not 83. Nothing published is wrong, because the body's measurement-commit rule is
  explicit and the figure carries `7d8e797` inside its command — but a reader who re-derives at the
  freeze sha the Version History names gets a different number, which is the two-referent hazard the
  same paragraph was written to refuse. One clause in the VH entry ("figures in this revision are
  measured at 7d8e797, not at the freeze") closes it.

- The register's justification for moving its stamp cites an interval that does not contain the
  stamp being replaced. Lines 909–912 replace `68a70d6` with `7d8e797` and justify it with "this
  document's body is byte-identical across `f91a74b..7d8e797`". `68a70d6` is an ancestor of
  `f91a74b` (`git merge-base --is-ancestor 68a70d6 f91a74b` succeeds) and the document *did* change
  in that head span (`git diff --stat 68a70d6 f91a74b -- <doc>` → 149 insertions, 30 deletions).
  The cited interval is the right one for the lifetime of the v1.96 text being edited, and the
  members are external facts whose unverified status is unaffected, so this is a stated-evidence gap
  and not a wrong claim — but as written the reader checks a span that excludes the old stamp.

## Nit

- The register calls its new member "the **body-scoped `74e126f` self-counts**" and then lists
  "whole-file **30**" among the three. A whole-file count is by construction not body-scoped; the
  owning paragraph at lines 768–770 makes the distinction load-bearing.

- The inline residual at line 764 ("**Residual, stated because it is not closed:**") still stands
  unchanged, while the register entry at lines 914–917 describes it in the past tense — "through
  v1.96 those three were handled by an inline ... sentence, and an inline residual is not a register
  entry". Both surfaces are now live. If the register entry is the fix, the inline sentence should
  say so and point at it; if the inline sentence is retained deliberately, the past tense is wrong.

---

### Things checked that hold (no finding)

- All nine MUST-1 table greps re-run: `Five members` 1@`8909ec4` / 0@`6f0ee85`; `Seven members`
  1@`7982c18`; `three OS probes` 1@`7982c18` body, 2 whole-file, 0@`8909ec4`; `**five** OS- or
  runtime-determined probes` 1@`06ef40f`; `four screen-two legs` 1@`7982c18`, 1@`06ef40f`,
  0@`8909ec4`; `**six** screen-two legs` 1@`f91a74b`; `printf 'zero files` 1@`7982c18`.
- The `-F` claim: without it, `**five** OS- or runtime-determined probes` on the `06ef40f` body
  exits 2 with `grep: repetition-operator operand invalid`. Reproduced.
- All four landing commits from `git log --oneline --reverse -S'- v1.NN: Plan audit' -- <doc> | head
  -1`: v1.93→`8909ec4`, v1.94→`7982c18`, v1.95→`06ef40f`, v1.96→`f91a74b`.
- Ledger: `72`/`83` at `7d8e797` and at `1cbddb7`; `grep -c` form 72/**11**; porcelain **0**.
- Interval closure re-run: `git diff --name-only 74e126f 7d8e797 -- h-mad handoff` and the same with
  `4e4a00c` both empty; both piped forms print `docs` alone; body `4e4a00c` count **60** at
  `7d8e797`; `git diff --stat f91a74b 7d8e797 -- <doc>` empty.
- "the freeze" body-scoped at `7d8e797`: **32** lines, **20** with `4e4a00c`, **12** without.
- Every closure member at `4e4a00c` / `7d8e797` / `1cbddb7` identically: design
  `seven-plus-two-plus` 1; design mutation-target 1; spec AC anchors **49** with the `uniq -c | awk
  '$1>1'` form printing **0** lines; `stated here rather than by reference` 1 and `same sweep as the
  plan` 0; spec `len(tuple)` 2; spec `^  $ awk ` 1 with design 0 and impl-plan 0; spec `Residual on
  the enumeration itself` 1; spec openers 21 over 11 distinct tokens; impl-plan `found =
  _dbe.find_heading(text, heading)` 4; `git diff --stat cf3a862 <sha> -- <spec>` empty at all three.
- All 13 impl-plan sibling locators return exactly **1** at `1cbddb7`, against the post-revision
  design and plan bytes.
- `git diff --stat 6dcb70f 7d8e797` over all four gated documents prints nothing.
- No agy report exists for plan cycle 83 (`docs/01-plan/features/` holds `v83.teammate.md` only);
  the VH entry states this correctly.
- The eight-row / "Seven members" carve-out table is explained in the body ("The table is eight rows
  because the wrapper is listed with the seven it does not belong among") — not a count defect.

### Limits on this pass

I did not re-audit v1.97 as a whole; I read the diff hunks and the paragraphs they land in. I did
not verify row 1 column 2's "resolving to **seven** distinct probes" as a derivation — the 13
matching lines reproduce, but resolving them to seven probes is a reading, and I confirmed only that
`Seven members` → 1 at `7982c18`. `unverified`. I did not re-run the `doc-auditor.md` fence-toggle,
Setext, grammar-corpus or OS-probe register members; the diff does not touch them.
