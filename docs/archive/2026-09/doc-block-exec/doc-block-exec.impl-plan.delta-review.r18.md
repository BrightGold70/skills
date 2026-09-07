# doc-block-exec impl-plan — delta self-review r18 (v1.53 → v1.54, incl. reopen)

Subject: `git diff cac6edc -- docs/01-plan/features/doc-block-exec.impl-plan.md` (834 diff lines).
Pass type: **ADVISORY**, per dispatch. Base `cac6edc`, HEAD `f6849bb`, batch staged and uncommitted
(`git status --short` reads `M ` for this file, so working tree == index).

## Summary

Every tree-fact in the dispatch's "known facts" list reproduces exactly, and every design-logic
repair (one tagged `pairs` list, the lookahead span scan, `__cause__` identity, the three-member
`LaunchFailed` annotation, Task 5's restored guards, the eleven-test Task 2 RED, `_field` 20, the
`wire-unconditional` carve-out) is closed at the class rather than at the instance — I re-derived
each one from the tree or by executing the property on 3.11.8. Two findings are live: the per-needle
self-reference sweep was **not** re-run after the reopen's own body edit and now publishes two
integers the tree contradicts, and a bare-phrase population that moved 6 → 5 in this revision is
still described as six three lines below its own list. Both are the exact class the entry claims to
have enforced ("every screen this revision's own new text can move was re-run AFTER the last body
edit").

Evidence: 12 files opened, 94 greps run.

## Must-fix

- **The per-needle debt-word sweep publishes `29 / 1 / 1 / 0 = 31` where the tree it ships reads
  `30 / 1 / 1 / 0 = 32`, and 32 is what this same document publishes 49 lines below.** The screen
  was re-run before the reopen and not after it: the reopen's own edit at L2661 added the
  eighth whole-word `owed` ("the design owed the row"), which is exactly the +1. The composition
  bullet at L1367 WAS re-run and reads 32; this one was not. Ran, on the shipped working tree:
  `awk '/^## Version History/{exit}{print}' docs/01-plan/features/doc-block-exec.impl-plan.md > body`
  then `grep -c 'owed' body` → **30**, `grep -c 'spec\.md:' body` → **1**,
  `grep -c 'design\.md:' body` → **1**, `grep -c 'plan\.md:' body` → **0**, and
  `grep -c 'owed\|spec\.md:\|design\.md:\|plan\.md:\|line [0-9]' body` → **32** (the four-needle form
  also reads 32). The prescription is `29` → `30` and `31` → `32` at L1318–1319, re-run after the
  final edit. **Close the class, not the member**: the rule is that a screen whose needle matches
  prose the revision is still writing must be the LAST thing run before DONE, and the residual is
  that this document has ten such self-counting instruments — the reopen re-ran some and not others,
  which is a per-instrument checklist, not a re-count.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `body, by line: the debt word **29**, `spec\.md:` **1**, `design\.md:` **1**, `plan\.md:` **0** —`
- **The bare-phrase locator population moved 6 → 5 in this revision and the justification sentence
  three lines below still says six.** L1176 lists five members and calls them five; L1179 reasons
  from six. Verified by counting the list and by re-running the substituted needle:
  `git show fbc2ea0:docs/02-design/features/doc-block-exec.design.md | grep -c 'guard it removes'`
  → **1**, the same at `cac6edc` → **2**, and
  `grep -cE '^\| mutation \| guard it removes \(mechanism\) \| killed by'` → **1** at `fbc2ea0`,
  **1** at `cac6edc` and **1** on the design's working body — so the 8+6 → 9+5 move is real and only
  the trailing cardinal is stale. Prescription: `six times` → `five times`, or restate the clause
  without a cardinal. `instance of:` the value-sweep class this document already names — a
  cardinal restated in prose downstream of the list it counts.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `document violates six times at the commit it ships is a rule that gets ignored, so the`

## Should-fix

- The v1.54 Version History screen summary repeats both wrong integers from must 1 **and** gives a
  whole-word bin of 7 where the body's own mechanical classifier gives 8. It reads
  `the per-needle sweep 29 / 1 / 1 / 0 = 31, re-classified mechanically as 22 confound + 7
  whole-word + 2 sibling-filename`. Classifying the 32 hits in order (whole word → substring →
  sibling-filename), I get **22 / 8 / 2** with none unclassified, which is what the body publishes.
  22+7+2 = 31 closes arithmetically, which is how a wrong bin survived: the internal check passes
  against the wrong total. The eight whole-word members are at L1241, L1252, L1257, L1259 (the
  rule's own text, four, as the body says), L2299, L3148 (the two new ACs), L2661 (the reopen) and
  L4023 (§Verification) — the body's four-way account of the live uses is exactly right.
- The restated-cardinal screen publishes a before-reading at `fbc2ea0` (v1.53's base) beside an
  after-reading on "the tree v1.54 ships", and its conclusion still attributes the pair to v1.53's
  edits. Re-run at all three points with the document's own `V`/`N` block: body 0 lines / 0
  occurrences and whole file 2 lines / 3 occurrences at `fbc2ea0`, at `cac6edc` and on the working
  tree alike. **No integer is wrong** — this is a stamp defect only, and it is the same
  before-at-the-previous-base shape the entry says it corrected at the per-needle site. The base
  should be `cac6edc`, or the conclusion should name both revisions' edits.
- Version History item (9) justifies citing the implementer prompt by needle with "because a copied
  pin into that file is task #29", but the standing control is `SKILL.md`-scoped — I read
  `h-mad/tests/test_h_mad_precheck_doc.py:299-310`, whose assertion is
  `assert "SKILL.md:" not in joined`. And this document already carries
  `references/codex-implementer-prompt.md:62` eight lines below the new needle citation, so the
  "never by line" claim is contradicted by its own body. That pin is CORRECT — `sed -n '62p'` on
  the file at `fbc2ea0` and on the working tree both print the expected-counts STOP rule, and
  `git diff --stat fbc2ea0 cac6edc -- h-mad/references/codex-implementer-prompt.md` is one line
  changed in place — so nothing is broken; the stated reason is. Prescription: attribute the
  needle-form preference to the LINEPIN advisory class, not to task #29, and either re-stamp the
  `:62` pin to `cac6edc` (the freeze commit edited that file) or convert it to a needle too.
- The v1.54 entry publishes `25 + 6 + 26 + 28 = **85**` in one paragraph and `25 + 7 + 26 + 28 =
  **86**` in the next, with nothing at the first pointing forward. The chronological-amendment
  device is legitimate and the reopen paragraph is explicit, but a reader grepping the entry for the
  matrix total finds two answers. A bracketed forward marker on the 85 sentence — the device the
  v1.51 entry already uses — would cost one clause.

## Nit

- The `cleanup-chain-selection-flipped` row characterises its mutant as producing
  `__cause__ is None` **and** `__suppress_context__ True`. Measured on 3.11.8: the CORRECT
  implementation (`raise err from cleanup_error` inside an `except`) also sets
  `__suppress_context__` to True, so only the first clause discriminates. Since AC-3.14 just
  withdrew its `__suppress_context__` assertion for precisely this reason, listing the
  non-discriminating property beside the discriminating one at the row invites a 5e implementer to
  assert it again.
