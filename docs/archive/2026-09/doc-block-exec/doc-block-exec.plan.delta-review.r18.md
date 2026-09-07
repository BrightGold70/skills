# doc-block-exec — plan delta review, r18 (v1.104 → v1.105, incl. one reopen)

Subject: `git diff cac6edc -- docs/01-plan/features/doc-block-exec.plan.md` (19 hunks, staged, working tree == index).
Pass is ADVISORY. Reviewer shares a model family with the authoring surface; a real codex leg is still owed on this tree.

## Summary

Every published figure this batch re-stamps reproduces exactly: the design-matrix derivation prints
`81/85/85` for `09e9307`/`cb4fe99`/`cac6edc` and `86` for the batch with `skill-md-target=1` at all
four, the two committed probes print `new_only=0 titleless=0` on both corpora at the freeze, the
collect counts return 2836 and 2574 in separate shell invocations, and the register walk returns 9
over the shipped body with the `6 + 2 + 1` partition holding bullet by bullet. The three musts below
are not digits: one published derivation command does not run as written, the batch re-points a
phrase the document defines as bound to another sha, and one new cross-document claim is false for
the fourth document by the same revision's own measurement.
Verdict: FAIL (must=3, should=4, nit=2).
Evidence: 9 files opened, 46 greps/commands run.

## Must-fix

- The `8`-row derivation published in the narrowed carve-out **does not run as written and names no
  blob** — it is `grep -oE` with `\|` between the alternatives, which under ERE is a *literal* pipe,
  and it carries no `git show` and no file operand. Run verbatim against the design blob at the
  freeze it returns nothing: `git show cac6edc:docs/02-design/features/doc-block-exec.design.md |
  /usr/bin/grep -oE 'a fifth, \`[a-z-]+\`\|a sixth, …'` → no output, `rc=1`; the same regex with bare
  `|` prints the four ordinals. The paragraph's own rule is that such a figure "carries the command
  that reads it out of that sibling and the sha it was read at", so an unrunnable command breaks the
  invariant the hunk exists to install, and the sibling it names is the wrong one: "over the same
  blob" resolves to the impl-plan blob quoted immediately before, which contains **0** of the four
  ordinals (`git show cac6edc:…impl-plan.md | grep -oE 'a fifth, …'` → no output). Prescription:
  `git show cac6edc:docs/02-design/features/doc-block-exec.design.md | grep -oE 'a fifth, \`[a-z-]+\`|a sixth, \`[a-z-]+\`|a seventh, \`[a-z-]+\`|an eighth, \`[a-z-]+\`'`, and say "over the design blob at `cac6edc`" rather than "the same blob".
  **Close the class**: the two commands this revision publishes *in prose* (this one and the
  `29 names` one) were not extracted and executed, while the two it publishes in the fenced
  derivation block were — the VH says so in as many words. The rule over the set: every command a
  revision publishes is extracted from the shipped body and executed, fenced or inline, and the
  residual is that an inline command inside double backticks can carry markdown-motivated escaping
  (`\|`) that a fenced one cannot.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `` ``grep -oE 'a fifth, `[a-z-]+`\|a sixth, `[a-z-]+`\|a seventh, `[a-z-]+`\|an eighth, `[a-z-]+`'`` ``

- **The batch gives *the freeze* a second referent, which is the exact drift the document defines
  the phrase to refuse**, and the screen the revision ran cannot see it. The body states "The phrase
  *the freeze* in this document means `4e4a00c` throughout and is deliberately not repointed";
  three added sites attach it to `cac6edc` instead: "All three re-derived at the freeze under the
  narrowed rule" (the three readings are at `cac6edc` and at the batch), "**THE FREEZE READING, same
  committed probe, run at `cac6edc`**", and "the `fbc2ea0` reading is kept beside the freeze
  reading". Measured over the newline-collapsed body, `the freeze` with no sha after it goes **31 →
  36** (`the freeze \`4e4a00c\`` is 16, down from 17) — five new bare uses, of which two are the
  pre-existing generic sense ("touching `h-mad/` moves the freeze", "the freeze is the landing") and
  three are the new referent. The VH nevertheless records the vocabulary as protected.
  **Close the class**: the revision screened the term by sweeping *term + sha* (`the freeze
  \`cac6edc\`` → 0 body-scoped, which I confirm), and a defined term is broken by the *bare* form,
  which that sweep cannot reach. The rule: a defined-term protection is screened on the bare term
  with each hit's referent read from context, never on term-plus-value. Residual: the generic plural
  ("at each freeze") is a third sense already in the body and is not repaired by this.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `**THE FREEZE READING, same committed probe, run at `cac6edc`, and ONE FIELD MOVED ON EACH`

- **"ALL FOUR DOCUMENTS STATE IT IDENTICALLY" is false on both halves, and this revision's own VH
  says so.** The spec carries no site at all — `new_only`, `titleless` and `vacuously` are each **0**
  in `docs/01-plan/features/doc-block-exec.spec.md` — and the VH states "the spec has no site for any
  FACT 3 value", so the body and the VH contradict each other inside one revision. The three
  documents that do carry it are not byte-identical either: the plan quotes the invariant with
  single quotes (`'each `new_only` member is a heading under CommonMark'`) where the design and the
  impl-plan use double quotes, so a reader diffing the three on the quoted span sees a mismatch.
  Prescription: "stated in the words the round decided, so the three documents with a site state it
  identically; the spec has no site for any FACT 3 value", and align the quote marks with the two
  siblings. This is the shared-string half of C2 iii and it is the one surface where a
  cross-document string can only be checked by comparison.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `**A SECOND RESIDUAL, WRITTEN IN THE WORDS THE ROUND DECIDED SO THAT ALL FOUR DOCUMENTS STATE IT`

## Should-fix

- The Deliverables cell points at "the FR-6 table **below**", and that table is **above** it: the
  FR-6 mutation table sits at `docs/01-plan/features/doc-block-exec.plan.md:850–870`, inside
  §Implementation Strategy (`## Implementation Strategy` at :445), while §Deliverables opens at :945
  and the cell is :959. The pair it names is correct — `docsections-heading-lookup-reverted` (:860)
  and `docsections-delegation-reverted` (:862) both bind
  `tests/test_docsections.py::test_docsections_delegates_to_the_authoritative_bounder` — so only the
  direction is wrong, and the same batch states the rule against this ("the pointer names this block
  by its bolded lead-in rather than by position"). Prescription: name it by its lead-in, e.g. "the
  FR-6 wire-mutation table under §Implementation Strategy".

- The `29 names` derivation's exclusivity clause is short by one member, and its count is a line
  count. At `cac6edc` the impl-plan also states `__all__` "stays at **28 names**" — Task 3's
  intermediate, the same class as Task 1's `25` the clause does name — so "no competing `N names`
  figure but Task 1's own intermediate `25`" enumerates one of two intermediates. Separately, the
  published `tr '\n' ' ' | grep -c '29 names'` → **1** is a *line* count over a file collapsed to one
  line, so it returns 1 for any nonzero number of occurrences; the occurrence count is **2**
  (`grep -o … | wc -l`). Prescription: name both intermediates (`25` and `28`) and publish the
  occurrence count with `grep -o`.

- The batch stamp is stated at six sites and its expiry at one. "the tree this batch ships" occurs
  **6** times body-scoped, while the obligation that makes it re-derivable — "after which the same
  command must be re-run as `git show <batch-commit>:$D`" — is stated once, at the derivation block.
  A reader landing on the Deliverables cell or the carve-out gets a stamp with no route back to a
  sha. Prescription: state the expiry once and point at it from the other five, or name the six
  sites in the residual so the set is enumerable rather than asserted.

- The VH's claim that `the freeze \`4e4a00c\`` is "still 16 body-scoped, unmoved" is right about the
  digit and wrong about the word. The count was **17** at `cac6edc` and is **16** on the shipped
  body: the rewritten Deliverables cell dropped the old ``git grep -c 'the mutation targets
  `SKILL.md`' 4e4a00c`` reading, which carried one of the 17. Losing it is correct — that command was
  superseded — but "still … unmoved" describes a set that moved by one in this revision.

## Nit

- "while this document named **0** and gave that pin only as a shell command" carries no sha on the
  `0`, while the two sibling counts beside it are stamped at `cac6edc`; the shipped document now
  names the node **3** times, so a reader reaching that clause out of its past-tense frame reads a
  live count that is false. Suggest "named 0 at `cac6edc`".

- The VH reproduces the retired string `the freeze \`cac6edc\`` verbatim while the same entry
  explains that two other retired strings were described rather than quoted "because reproducing a
  retired string verbatim puts it back into every value sweep of this document". Defensible, since
  the entry counts body and Version History separately and VH entries are historical by
  construction, but the asymmetry is worth one clause.
