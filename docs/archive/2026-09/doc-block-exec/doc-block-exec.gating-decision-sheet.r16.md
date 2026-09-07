# doc-block-exec — round sixteen decision sheet (shared facts for the r16 revision batch)

**Status:** input to three parallel authors. Not a gate. Stamps nothing.
**Freeze:** `af19d53` (HEAD, pushed). The four documents are byte-identical from `3f70eb3` through
`af19d53` — verified with explicit paths, because a wildcard `doc-block-exec.*.md` also matches the
audit reports and reports 323 inserted lines that are not the documents. Commits since `3f70eb3`
touched only audit reports and `h-mad/scripts/h_mad_assemble_audit.py` + its test.
**Inputs per author** (read both in full; the second column exists because two legs of one model
family disagreed on the must set in both directions, and that disagreement is the signal):

| author | document | gating reports (freeze `3f70eb3`) |
|---|---|---|
| design-author | design v1.107 → v1.108 | `docs/02-design/features/doc-block-exec.design.audit.v95.teammate.md` (must 4) · `…v95.teammate-b.md` (must 3, two new) |
| plan-author | plan v1.102 → v1.103 | `docs/01-plan/features/doc-block-exec.plan.audit.v86.teammate.md` (must 4) · `…v86.codex.md` (must 4, IDENTICAL set — a different model family) |
| implplan-author | impl-plan v1.51 → v1.52 | `docs/01-plan/features/doc-block-exec.impl-plan.audit.v46.teammate.md` (must 1) · `…v46.teammate-b.md` (must 3, two new) |

No finding is routed to the spec this round; it is not revised.

**Your run outranks this sheet.** Over rounds twelve to fifteen an author refuted the orchestrator's
decision sheet in every round, and in r15 two sheet claims became document musts. If a fact below
disagrees with your own run, your run wins and the disagreement is a finding — report it first.

## FACT 1 — codex is BACK, and it agreed with the teammate leg one-for-one

`codex_status=available` (probe PASS). The codex leg on plan c86 returned must=4 and the four are the
teammate leg's four exactly, plus the same should-fix, neither having seen the other. For the plan,
those four musts are doubly confirmed across model families; do not re-argue them, close them. Design
and impl-plan have no codex verdict at c95/c46 — their prompts exceeded 1,048,576 chars and codex
refused them (`input_too_large`). That is fixed as of `af19d53` (`--vh-tail`), so r16 gating will
carry codex on all three. Still: **claim no two-surface clean and no exit gate** in any entry.

## FACT 2 — the freeze-sha rule, COMPLETED. This is what the r15 broadcast got wrong.

Round fifteen's C2 said "the batch stamps `dfae038`" and "every reading stamped at a blob stays at its
blob". Correct and incomplete: it did not say what a reading taken over **your own new bytes** is
stamped to, and one author stamped such a reading to the batch sha. That became impl-plan must 1 —
a correct reading (23/25) carrying the wrong sha (`dfae038`, where the values are 24/26).

The complete rule, three clauses:

1. **An entry's own freeze-sha field** names the last commit before the batch was authored — here
   `af19d53`, the parent of the commit that will land this batch.
2. **A reading of a committed blob** stays stamped at that blob (`b3be433`, `00b961f`, `3f70eb3`, …).
   It does not move when the freeze moves.
3. **A reading taken over this revision's own post-edit body** is stamped to *the tree this revision
   ships* (or "the working file after the v1.NNN entry below was written") — **never** to
   `af19d53`, which does not contain your edits. A count of your own new text at `af19d53` is
   definitionally a different number.

HEAD, the working tree and the current branch are not endpoints for a **comparison**; a working-file
endpoint is admissible only when identified by the entry it was taken after (design v95 must 4 is
about the rule over-reaching this — read it before you write a rule about shas).

## FACT 3 — `dfae038` touches THREE files. Two documents still say "alone".

```
git show --name-only --format='' dfae038
  docs/handoffs/2026-09-05-main__doc-block-exec-rounds-twelve-to-fourteen.md
  docs/learnings.md
  docs/skill-candidates.md
```

The orchestrator wrote "`df04e8e` and `dfae038` touched only `docs/handoffs/`" into the r15 sheet
without measuring it; it propagated into eight surfaces and is now a must in two documents. Sites
that still carry it at `af19d53`, measured: **plan 2** (`:1074`, `:1320` and the v1.102 entry region),
**impl-plan 1** (the v1.51 entry's freeze-field justification), design 0, spec 0. The conclusion each
site draws — the four documents are byte-identical `00b961f..dfae038` — is TRUE and stays; only the
word "alone"/"only" is false. Fix the word, keep the conclusion, and say which file the sheet's error
came from so the correction is attributable.

## FACT 4 — `ten of the eleven`, measured once at `af19d53`

Whole-file, wrap-collapsed: **3**. Body-scoped (above `## Version History`), wrap-collapsed: **0**.
The plan's v1.102 entry says the sweep "returns 1". Both gating legs filed it. The three whole-file
hits are all Version History records of the retired denominator; the body is clean. Publish the
reading with the grammar that produced it, and do not "repair" the three records — they are dated.

## FACT 5 — the -b findings the orchestrator has NOT independently reproduced

Verify before acting; a -b must that does not reproduce is a finding about the -b report and you
report it rather than applying it.

- design-b must 1 (stamp census flat count / under-report against the document's own needle) and
  must 2 (the `-F` needle is the `tr` idiom, not `awk`) — **unverified by the orchestrator**;
  `ugrep` threw `exceeds complexity limits` on the check. design-b must 3 converges with design
  must 4 (fixed-pair rule violated in the same entry) — that one is doubly found.
- impl-plan-b must 1 (the v1.51 freeze-field justification asserts a false scope) — **VERIFIED**, it
  is FACT 3 in your document; the original leg missed it. impl-plan-b must 2 converges with the
  original's must 1. impl-plan-b must 3 (the Conventions residual routes to the wrong task) —
  **unverified**.

## FACT 6 — the version-number rule, from #49k

A version bump is the FIRST thing you write, not the last, and the orchestrator read it as completion
in r15. So: **bump the version when you start, send DONE once when you finish, and write nothing
after DONE.** If you must fix something after DONE, send a second message saying so before the edit.
Two different bodies self-identifying as one version number is what the impl-plan leg had to audit
around last round.

## Standing constraints

1. One author, one document. A sibling that owes something is REPORTED in your tail, not edited.
2. The tree is frozen until all three DONE messages arrive. Nothing commits under you.
3. Close the CLASS, never the instance — and check the previous round's own class rules for live
   members they missed (design must 2: the residual named two deictics, eight more were live).
4. A count is evidence only against another count at the same commit, same corpus, same grammar,
   in a shell whose state you did not inherit. Collapse newlines before counting a phrase; check
   which language construct a token sits in; `ugrep` shadows `grep` here and fails loudly on
   ordinary regexes — an unrun command's empty output is not a zero.
5. Run `h_mad_precheck_doc.py` on your document before DONE and paste its `PRECHECK:` line.
   impl-plan uses the six `--allow` grammar specimens.
