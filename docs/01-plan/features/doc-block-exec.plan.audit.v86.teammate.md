## Summary

GATING leg on plan v1.102 at freeze `3f70eb3`, one surface only (codex exhausted until 2026-09-07
11:28) — no two-surface clean, no exit gate. The document is byte-identical at `59cc2ad`, `7b182b0`
and `3f70eb3` (`git diff` on this path empty across all three), so the two freeze corrections are
label changes and every reading below was re-checked at the corrected sha. I re-executed every figure
the v1.102 diff publishes at the shas it names and the great majority reproduce exactly: the
`b3be433` `pgid` census byte-for-byte (`1+0+5+6=12`, `0+0+4+6=10`, so "Ten of the twelve" is now
derived from the fence), the three `00b961f` `pgid`-discharge commands, the two still-owed spec
commands at `00b961f` (`2486` → 1, `BAD_ARGS` → 0 awk-scoped), the `700c599` three-surface screen
(paragraph-joined **3**, line-scoped **5**, per-branch ordinals `9 11 19 / 9 11 19 / 9 11 / 19 / 11`,
working-tree **6**), the cardinal-list `≥ 2` readings (`2 2 5 2 2 1` at `b3be433`, `3 3 6 3 3 4` at
`00b961f`), the freeze triple (`32/20/12 · 32/21/11 ×2 · 37/21/16 ×2`), `this revision` **32**, the
`rev-list b3be433..dfae038` three commits, `--shortstat` 348/91, the `74e126f`/`4e4a00c` → `dfae038`
interval closure (both empty, both `docs` alone), the spec-immobility retirement (41/15) with the
opener census surviving (21 openers / 11 tokens at `00b961f`), the screen-two checker diff (one line,
`v1.60`→`v1.61`), the AC-anchor **49** (unmoved from spec v1.59 through v1.62, duplicate check
silent), the `len(tuple)` = 7 + 2 = 9 arithmetic, and every `h-mad/` pin (`from docsections import` 3,
`_gate_bash_block()` def+3, `returncode` 0, `P<marks>` 1, `def test_` 6, assertions 9,
`titled_section(|section_from(` 6). Four musts do **not** reproduce, and all four sit in text v1.102
itself wrote — the fifth consecutive round of that pattern. Both cross-document items the orchestrator
routed to this leg came back **clean** and are recorded under Should-fix so their clearance is on
the record rather than inferred from silence.

Evidence: 19 files/blobs opened, 108 greps run.

## Must-fix

- `:3399` attributes the stale ledger pair to the wrong revision — v1.101 published `72`/`84`, not
  `72`/`83`, and the series four lines below on the same page says so. v1.102 introduced the
  attribution (the diff replaces `The published pair was` with `v1.101's published pair was` in the
  same hunk that re-stamps `84`→`85`). Re-derived: `git show 00b961f:<plan>` — v1.101's own body —
  carries `codex `72` against teammate `84` at `b3be433``; `72`/`83` is what v1.99 (`8c6539a`) and
  v1.100 (`b3be433`) published, both reading `codex `72` against teammate `83` at `1cbddb7``. The
  whole clause after it — "had been wrong since `8c6539a`… what two consecutive revisions then did" —
  is the v1.99/v1.100 recurrence and does not attach to v1.101 at all, so the sentence now names a
  revision that did the opposite of what it is charged with. Class, and it is the same axis as this
  revision's own MUST 2: a prose summary *restated* beside the series it summarises instead of
  *derived* from it; the rule the round wrote for integers ("written as the arithmetic over that
  surface's own values") has to cover attributions over the same surface, or the summary and the
  series drift independently exactly as they have here. instance of: every claim this document makes
  about which revision published a value, where the series is printed on the same page.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `**codex `72` against teammate `85` at `00b961f`. v1.101's published pair was `72`/`83` and the`
  quote: docs/01-plan/features/doc-block-exec.plan.md › ``700c599` **72/83** · `8c6539a` **72/84** · `b3be433` **72/84** · `00b961f` **72/85**. v1.99 landed at `8c6539a` and`

- `dfae038` does **not** touch `docs/handoffs/` alone, and the command printed beside the claim
  refutes it. `git show --name-only dfae038` returns
  `docs/handoffs/2026-09-05-main__doc-block-exec-rounds-twelve-to-fourteen.md`, `docs/learnings.md`
  and `docs/skill-candidates.md`; `git diff --name-only 00b961f dfae038` returns those three plus
  `df04e8e`'s handoff file. The document's own published output on the next line — `prints `docs` and
  `docs/handoffs`` — is exactly the evidence against it: the `docs` element *is* `docs/learnings.md`
  and `docs/skill-candidates.md`, and the directory-collapsing `sed 's|/[^/]*$||'` form cannot tell a
  top-level `docs/x.md` from a subdirectory, so a reader deriving the prose from the output would
  never write "alone". Three surfaces carry it: `:1074`, `:1320`, and the v1.102 Version History entry
  ("df04e8e and dfae038 touch docs/handoffs/ alone, **checked per commit**"), where the parenthetical
  asserts the check that would have caught it. **The conclusion is unaffected and should not be
  over-repaired**: only `00b961f` touches any of the four feature documents (verified per commit), so
  both the byte-identity argument and the register's interval argument stand. What is wrong is the
  word *alone*. instance of: every set claim this document derives from a path list collapsed to
  directories — the same collapse also hides any future top-level `docs/*.md` from the same sentence.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `commits between them touched `docs/handoffs/` alone`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `two, `df04e8e` and `dfae038`, touch `docs/handoffs/` alone. `00b961f`'s Version History entry`

- The `ten of the eleven` sweep published in the v1.102 Version History entry returns `1` at no
  commit, and the value it publishes is a reading of an uncommitted intermediate tree — which is
  precisely the class MUST 6 of the same entry writes the rule against, broken in the entry that
  states it. Run exactly as written (whole-file, newline-collapsed, no sha): **2** at `00b961f` and
  `dfae038` (the body sentence plus the v1.101 bracketed correction), and **3** at `59cc2ad`,
  `7b182b0` and `3f70eb3` — the v1.101 bracketed correction, the sweep command's own needle, and the
  entry's closing sentence "owes a bracketed correction for ten of the eleven in the next commit
  message". So the stated survivor set ("the surviving hit being the bracketed Version History
  entry") is a set of one where the tree gives three, two of them the sweep's own self-matches. The
  body itself is clean — `awk '/^## Version History/{exit}{print}' | tr '\n' ' ' | grep -oiF 'ten of
  the eleven' | wc -l` → **0** at `3f70eb3` — so the substantive claim that the retired value is gone
  from the body holds; the published figure does not. Prescription: either `awk`-scope the sweep to
  the body and publish **0**, or keep it whole-file and stamp it at a commit that predates the
  entry's own quotations, as this document's own rule for self-counting screens requires ("a screen
  whose published value is a count of members may not have its needle appear literally inside the
  scope it counts").
  quote: docs/01-plan/features/doc-block-exec.plan.md › `grep -oiF 'ten of the eleven' | wc -l returns 1, the surviving hit being the bracketed Version History entry.`

- The document names two different commits as the one v1.102 is measured at, and the collision is on
  the one reading it classifies as needing the *other* one. `:1069` states the rule and the value —
  "that commit is named once per revision… **v1.102 is measured at `dfae038`**" — and `:1078-1079`
  assigns the ledger by corpus: "a reading whose corpus is wider than the four is stamped `dfae038`.
  The wider-corpus readings this revision takes **are the codex-leg ledger**". The ledger's own site
  at `:3387` then calls `00b961f` "the one this revision is measured against", and both fenced
  commands at `:3391`/`:3394` carry `00b961f`. This is the round's own C2 correction landing on only
  one of its two surfaces: the ledger's corpus (`docs/01-plan/features/`) is wider than the four
  documents, which is exactly the case where byte-identity of the four licenses nothing. **No value
  moves** — I ran the ledger at `00b961f`, `dfae038`, `59cc2ad` and `3f70eb3` and it reads `72`/`85`
  at all four, and `:1081` says as much — so this is a defined-word defect, not a wrong figure; but
  this document devotes a whole paragraph to why a defined word with two referents is how a reader
  lands on the wrong tree ("**'Freeze' is a defined word here, and getting it wrong is how a reader
  lands on the wrong tree**"), and the ledger's site is the one place a re-runner is told the
  without-exception rule was obeyed. Prescription: at `:3387` name `00b961f` as the commit v1.101's
  bytes landed at and nothing else, publish the reading at the batch's freeze as `:1078` requires (or
  state the both-sha run at the site, which the entry claims and the body does not carry), and keep
  one answer to "measured at".
  quote: docs/01-plan/features/doc-block-exec.plan.md › `at `00b961f` — the commit v1.101 landed at and the one this revision is measured against — with the`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `rather than the phrase beside it. v1.102 is measured at `dfae038`.** **`00b961f` also appears in`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `corpus is wider than the four is stamped `dfae038`.** The wider-corpus readings this revision takes`

## Should-fix

- One surviving present-tense label asserts the spec still owes what spec v1.62 discharged. `:1093`
  calls the pair "the two **still-owed** spec commands", with no sha and in the present tense, which
  is the exact form this revision's own MUST 3 writes the rule against ("a claim about what another
  document currently states is written at a named sha and in the past tense"). At the freeze both are
  discharged: the spec body's `2486` hits are **2**, both retrospective ("the retired `2748`/`2486`
  pair"), and `BAD_ARGS` returns **2** inside the awk-scoped `AC-4.2`→`AC-4.3` range whose opening
  address occurs exactly once in that body, so the reading is not a range leak. **This is the only
  surviving surface, and the rest of the document is clean on the item** — `:178-179` states the pair
  as "**both still reproduce at `00b961f`**", a correctly sha-scoped reading that I re-ran and that
  reproduces (1 and 0), and the v1.102 Version History entry already records the v1.62 discharge as a
  dated observation of an uncommitted tree with the range-leak control named. Prescription: name the
  two commands by what they measure, or by their status at `00b961f`, rather than by a bare
  "still-owed".
  quote: docs/01-plan/features/doc-block-exec.plan.md › `measured: the three `pgid` discharge commands, the two still-owed spec commands, and the spec`

- The four sibling `§Scanning` citations routed to this leg were re-derived against the design at the
  freeze and **all four resolve**; recorded here rather than left silent, since silence would read as
  unverified. `### Scanning (`extract`)` exists at design `:184` and runs to `### Substitution` at
  `:1133` (`grep -nE '^#{1,6} '` at `3f70eb3`). Within that span: the tracked-corpus definition the
  plan cites at `:2212`, `:2225` and `:2577` is present verbatim — "**The corpus is defined by `git
  ls-files -- h-mad handoff` filtered to `*.md` with `archive/` excluded — never by a filesystem
  glob**" — and the `35 vs 30` tracked/glob pair sits in the same section; the heading-form precedence
  and ATX-prefix exclusion the plan cites at `:641` is present with its `form-precedence-bare-first`
  mutation; and the fourteen-case grammar corpus the plan cites at `:2711` is present with its
  "14 of 14 agreed". The one residual worth stating: the plan writes "design **v1.93** §Scanning" at
  `:2577` while the design ships v1.107, and the plan's version-label exemption at `:3177` is scoped
  in words to `spec v1.NN` labels only, so it does not cover this one — the definition it points at
  is byte-identical at `4e4a00c`, `b3be433`, `00b961f` and `3f70eb3` (fixed-string presence 1 at each),
  so nothing is wrong, but the label is outside its own document's stated cover. Inherited, not
  v1.102-introduced.

- The register's residual partitions its seven bullets `3` revision / `3` commit / `1` neither, and
  the bullets do not partition that way. Six of the seven name a commit — `35698f9`, `1861157`,
  `cf3a862`, `700c599`, `4e4a00c`, `b3be433` — and three of those six *also* name a revision, so
  "three name the **commit** their reading is stamped at" is true only under an unstated
  primary-label convention. Separately, the member assigned to the revision column contradicts its
  own bullet: `:1411` says the three `74e126f` self-counts were "**entered in v1.97**" and "stamped
  `4e4a00c`", while `:1421` lists "`v1.97` for the self-counts" as an *executing* revision — entering
  a figure in the register is the opposite of executing it, and the register exists to record
  non-execution. This is inherited from v1.101 (which wrote the same shape with `two`/`four`) rather
  than fix-introduced, and the totals still sum to seven, which is why it is not a must.

- Not checked, and named so its absence does not read as a clean finding: the body between roughly
  `:1696` and `:3385` — the carve-out sweep table, screen two and its enumeration legs, the
  stamp-driven `-E` driver, the scanner grammar corpus fence, the Setext differential and the
  `doc-auditor.md` fence-toggle readings — was not read or re-executed this pass, beyond the
  `§Scanning` citation sites at `:2212`, `:2225`, `:2577` and `:2711`. The v1.102 hunk list shows the
  revision touched nothing in that span and the register carries most of those figures as
  inherited-unverified, but that is an argument for deprioritising them, not evidence about them.
  Marked `unverified`, not clean.

## Nit

- The range-address class the round repaired is closed in this document, and that is a measured zero
  rather than an assumption: the only `sed` address range in the body is the repaired, `awk`-scoped
  `AC-4.2`/`AC-4.3` one at `:187`, and the only other range-shaped command is the fixed-context
  `grep -A14` at `:1444`, whose start address `^  \$ awk ` occurs exactly once in the spec at both
  shas it is run over. No second member survives.

- Recorded as a hazard I hit myself while verifying the `§Scanning` citations, because it is the
  round's own WRAPS rule and the falsifier is cheap: `grep -cF 'eleven-shape proxy'` over the design
  returns **0** at every sha including `3f70eb3`, and the phrase is present at all five — it straddles
  a hard wrap. Collapsed (`tr '\n' ' '`) it returns **1** at `74e126f`, `4e4a00c`, `b3be433`,
  `00b961f` and `3f70eb3`. No finding follows from it; the zero would have been reported as an
  absence if the collapse had not been run.
