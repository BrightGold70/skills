# doc-block-exec design delta review — r18 (v1.109 → v1.110)

Subject: `git diff cac6edc -- docs/02-design/features/doc-block-exec.design.md` (+407/−79, 24 hunks).
Tree: staged/uncommitted batch, freeze `cac6edc`, HEAD `f6849bb`. ADVISORY pass, not gating.

**VERDICT: FAIL — must=5 should=4 nit=2.**

## Summary

Every *substantive* design change in this batch closes its finding and closes it as a class, not as
an instance: the lookahead span scan, the single-field `OverlappingSubstitution`, the AC-3.14
`__cause__` rule, the three-type `LaunchFailed.err`, the FACT-3 past-tense specimen, and the
matrix 85→86 all re-derive exactly against the tree and against all three siblings. I re-ran ten of
the document's published commands and probes verbatim; nine reproduce byte-identically, including
the 13,104-case residual search (`194` over-refusals, `0` missed silent failures) and the
intersecting-span probe's whole output block. The failures are all in the *self-measurement* layer
this revision moved by writing 407 lines into its own corpus: the document's own entry-naming
screen is red on the file it ships, five published figures are wrong, and four of those are
falsified by the sentences that state them.

Evidence: 9 files opened, 58 greps/commands run.

## Must-fix

- **The document's own entry-naming screen is RED on the file this revision ships, and the body still asserts it is green.** Run verbatim over the folded head it returns two versions — `17 after the v1.109 entry` and `4 after the v1.110 entry` — where the stated acceptance rule requires one. The same command over `cb4fe99` returns a single version (`21 after the v1.109 entry`), so the screen was clean at v1.109 and this batch broke it by re-stamping four sites and leaving thirteen. The v1.110 entry takes no exemption and enumerates no sites, so the exemption branch does not apply. This is the one screen the document ships specifically to catch a stale stamp, and it is the screen this revision fails.
  quote: docs/02-design/features/doc-block-exec.design.md › `Every hit must name either the current entry or a version the stamp exemption stated in`
  quote: docs/02-design/features/doc-block-exec.design.md › `every stamp now reads v1.109, every attributional deictic is written as the`
  Prescription: re-run each of the thirteen screens on the shipped file after the v1.110 entry lands and re-stamp them, or take the exemption explicitly in the v1.110 entry and enumerate the thirteen sites. Do not re-stamp without re-running — the stamp is a claim that the reading was taken after the entry. Sampled one (`grep -cF '(first|second|third'` → `3` whole-file / `2` head, unchanged from `cb4fe99`), so at least that figure is mis-stamped rather than stale; the other twelve are unverified either way.
  instance of: the class the screen itself defines — a document-self figure naming an entry that a later entry has superseded.

- **The Executive Summary's new addend list does not sum to the total it exists to make checkable.** `7 functions + Block + RunResult + 19 exception rows` is 28, not 29. The exception table in §Error Handling has exactly 19 rows (counted mechanically: `awk` over the rows between the header and the following blank line returns 19; the first row is `DocUnreadable`, the last `LaunchFailed`), and `DocBlockError` — the base class — has no row. §API states the correct decomposition 2,150 lines below. So the sentence added to spare a reader that trip gives a decomposition that fails, and it contradicts §API.
  quote: docs/02-design/features/doc-block-exec.design.md › `29 public names, and the four addends are named here so the total is checkable without reading §API 800 lines below: 7 functions + `Block` + `RunResult` + 19 exception rows`
  quote: docs/02-design/features/doc-block-exec.design.md › ``__all__` names all seven functions, plus `Block`, `RunResult` and the whole `DocBlockError` hierarchy — the base class and its 19 subclasses — 29 names`
  Prescription: `7 functions + Block + RunResult + the DocBlockError base + 19 exception-table rows`. The same wrong decomposition is repeated in the v1.110 Version History entry and must be corrected there too.

- **The raised-line hop series reports its own hop as empty, and the reconciliation built on that is wrong by one.** The document states the hop `cb4fe99`→working as `none` under the counting rule it names in the same sentence. Run: `diff <(git show cb4fe99:"$D" | grep -E "$RAISE") <(grep -E "$RAISE" "$D")` prints `3c3,4`, `23a25`, `57a60`, `61a65` — six `<`/`>` lines, of which one is a rewording (the `grammar_corpus` citation line, `ls-files` → `ls-tree`). Consequences, both wrong as published: the per-hop rewordings sum to **seven**, not six; and **two** positions were reworded twice — position 61 (v1.106 + v1.109) and position 3 (v1.109 + v1.110) — which is what actually reconciles seven against the cumulative five. Every *other* hop in the series reproduces exactly (2 / 0 / 2 / 0 / 0 / 0 / 0 / 8, hunk headers `60c60`, `61c61`, `3,4c3,4` `37c37` `61c61`), so the series is right everywhere except at the revision writing it.
  quote: docs/02-design/features/doc-block-exec.design.md › ``09e9307`→`cb4fe99` **eight**, and `cb4fe99`→working none.`
  quote: docs/02-design/features/doc-block-exec.design.md › `61 was reworded twice**, so a cumulative differential sees it once.`
  instance of: the class the paragraph itself names — a hop differential whose right-hand side is the working file, taken before this document's own §Version History entry was written.

- **The extension tally published for the fifth blind form mixes two corpora, and two of its five figures are wrong on the shipped file.** Re-run over the head: `.py` 76, `.md` 55, `.json` 13, `.log` **3**, `.bak` **3**. At `cb4fe99` the same command returns `.py` 73, `.md` 49, `.json` 13, `.log` 2, `.bak` 2. So the first three figures were re-derived after the paragraph landed and the last two were carried from before it — and the extra occurrence of each is line 1959, the residual sentence in the very same paragraph, which cites `/tmp/doc_block_exec_suite.log` and `/tmp/R.bak`. The paragraph is *about* re-deriving an extension set from the corpus rather than from memory.
  quote: docs/02-design/features/doc-block-exec.design.md › `over the head, extensions tallied, gives `.py` 76, `.md` 55, `.json` 13, `.log` 2 and `.bak` 2.`
  Prescription: `.log` 3 and `.bak` 3, re-taken after the v1.110 entry, with the rule stated: this tally's corpus includes the sentence stating it.

- **Four "verify-only" readings in the v1.110 entry are `cac6edc` readings published in the present tense, and all four are false on the file the revision ships.** Measured at both corpora:

  | reading as published | at `cac6edc` | on the shipped file |
  |---|---|---|
  | "all ten `collect-only` occurrences … nine spelled with the flag, one prose" | 10 / 9 | 12 / 10 |
  | "`wire-unconditional` occurs twice" | 2 | 3 |
  | "2552, 2814, 2574 and 2836 occur ZERO times here" | 0 | 4 |
  | "`intersections` … zero here" | 0 | 4 |

  Three of the four are falsified by the entry sentence itself: all four numeric tokens and the third `wire-unconditional` occur on line 4535, the entry line. The `intersections` occurrences were added by this revision's own body. This is the same self-reference the document legislates against two sections away, applied to the disposal prose rather than to a needle.
  quote: docs/02-design/features/doc-block-exec.design.md › `VERIFY-ONLY ROWS, REPORTED WITH THEIR COMMAND RATHER THAN ASSUMED: all ten collect-only occurrences refer to --collect-only`
  Prescription: stamp each of the four at `cac6edc` explicitly (they are correct there), or re-take them on the shipped file. Do not leave them present-tense and unstamped; FACT 1's conclusion ("the design has no suite-count site") rests on the third row and is *still true* on both corpora, so only the figures need repair, not the conclusion.

## Should-fix

- **The AC-coverage paragraph sends the reader to the wrong section for AC-3.4 and AC-3.5.** §Architecture Overview is lines 99–216; `grep` for `strict`, `exit 3` and `pipefail` over exactly that span returns nothing. The strict-versus-plain pair is at line 230, under §Detailed Design › Info-string grammar; `exit 3` occurs in the head only in the AC-3.1–3.10 Test Plan row and in the coverage paragraph itself. The coverage claim is true — both ACs are covered — but the locator this batch added is wrong, and this paragraph exists precisely so a reviewer can check coverage without reading the document.
  quote: docs/02-design/features/doc-block-exec.design.md › `AC-3.5's `pipefail` are the strict-versus-plain pair under §Architecture Overview`

- **"each is now named at the site that covers it" is false on the literal reading, for all seven.** Every one of AC-1.2, AC-2.3, AC-3.2, AC-3.4, AC-3.5, AC-4.4 and AC-6.3 occurs only inside the coverage paragraph (lines 3827–3835); none is written at the row, section or test that covers it. The paragraph is candid elsewhere that it is what fills the grep ("The second line is empty because this paragraph fills it"), which contradicts the "named at the site" reading in the next sentence. The seven-label reading at `cb4fe99` reproduces exactly, and the script prints `spec 49 covered 49 uncovered [] not-in-spec []` verbatim, so the fix itself lands.
  quote: docs/02-design/features/doc-block-exec.design.md › `by behaviour, and each is now named at the site that covers it`

- **"whose `a` hunks are v1.110's four additions" is wrong: only two of the four are `a` hunks.** The cumulative differential prints `3,4c3,5`, `23a25`, `37c39`, `57a60`, `60,61c63,65`. The `a` hunks carry one added line each; the other two additions sit inside `3,4c3,5` (2→3) and `60,61c63,65` (2→3). The headline figures either side of that clause — five hunks, five replaced, four added, nothing removed, 63/61 → 67/65 — all reproduce exactly. Relatedly, "the four non-empty hops" is five once the working hop is counted (see Must-fix 3).

- **The enumeration of v1.110's four additions names the replaced line and omits one of the additions.** The differential's added lines are: the heading differential's freeze output block (`new_only` column), the fifth-blind-form sentence, the AC-coverage sentence, and the slicer sweep's untracked-`.py` control. The `grammar_corpus` citation line is the **replacement** (`ls-files` → `ls-tree`), not an addition — its `` `0` `` count is one before and one after. The published list swaps those two, so the clause "a fifth is a replacement of an existing line and adds nothing" names the wrong line. Net total (four) is unaffected.
  quote: docs/02-design/features/doc-block-exec.design.md › `the `grammar_corpus` citation gains one when its sha-scoped arm is respelled `ls-tree``

## Nit

- Line 3517 stamps its measurement "after the v1.109 entry" three lines above the `$P` 37 / `$W` 11 figures that this batch correctly re-stamped to v1.110 — two stamps for one reading in one paragraph. Instance of Must-fix 1, listed separately only because it is the most confusing of the thirteen.
- The v1.110 entry's "Sibling debt created here: the plan says 81 and the impl-plan says 85" is correctly scoped (the entry says the sibling readings were taken with `git show cac6edc:<path>`, and both figures are right there), but a reader at the landing commit will find plan and impl-plan both reading 86, since all four documents are staged together. One clause naming the batch would close it.

---

### Verified clean (re-run, not read)

Recorded because a clean verdict on these is worth nothing unless the command was run.

- FACT 3: `grep -c '^#$' h-mad/SKILL.md` → `1` at `a8e0372`, `fbc2ea0`, `cb4fe99`; `0` at `cac6edc`. The passage is past tense throughout and the residual is stated with N and sha.
- The in-document heading differential fence, extracted and run: byte-identical to the new published output block (`30 / 35 / new_only 0` on both arms, empty identity lists).
- The committed probe `heading_differential.2026-09-04.b66afa9c.py`: `files=30 both=292 old_only=82 new_only=0 titleless=0` tracked, `files=35 both=297 old_only=82 new_only=0 closing_hash=5` glob — exactly as the new paragraph claims.
- The intersecting-span probe: all four arms, both scan forms, byte-identical to the published block including `'aaab' … bare=[] lookahead=[(2, 'aa', 'ab')]`.
- The residual search: 52 non-substring pairs × 252 texts = 13,104 cases; lookahead-only refusals **194**; neither form missed a silent failure. Reproduces exactly.
- Matrix: the published `awk` returns **86** over the shipped file; exactly one row's mechanism names `SKILL.md`. Plan (`86 mutations … 85 of the helper's source and 1 of h-mad/SKILL.md`) and impl-plan (`25 + 7 + 26 + 28 = 86 rows`) agree; the spec carries no matrix count.
- `intersect:` grammar is identical in all four documents — `intersect: "<a>" "<b>" "<offset>"`, `"1"` for `abc`, `"2"` for `aaab`. No live `at "0"` survives; the one occurrence is the AC row's own quoted correction.
- `__suppress_context__`: 10 occurrences over 9 head lines (168, 186, 1775, 1776, 1780×2, 1786, 1789, 1790, 4033). None is an assertion — two are language prose, one a probe's printed column, one a mutation-row description, the rest the new rule. No sibling carries one inside an `assert` either (spec 407–408 and impl-plan 2650/2776 are all descriptions). The spec at `cac6edc` returns 0, as the entry claims.
- `LaunchFailed.err` three types: impl-plan:2081 annotates `OSError | subprocess.TimeoutExpired | ValueError`. Consistent.
- Single-field `OverlappingSubstitution`: impl-plan:2413 states "no second `intersections` argument". Consistent.
- Slicer sweep: prints **23** on the working tree, the single arrival `h-mad/scripts/h_mad_assemble_audit.py _trim_version_history` is present, and `git ls-files --others --exclude-standard` over the three roots returns 0 `.py`. The trip-wire scope claim holds: `git diff --name-only a8e0372 cb4fe99 -- h-mad handoff` is exactly two `.py` files and no `.md`.
- Both walks: 132 fenced / 71 marker-word on the shipped file; 106/62 at `fbc2ea0`, 104/60 at `b3be433`, 126/70 at `cb4fe99`. The `+6` fence delta is 6 added and 0 removed against `cb4fe99`, and the in-fence marker split is 2, leaving 69 — all mechanical, all reproduced.
- `$P` / `$W`: 37 / 11 head and 13 / 7 tail on the shipped file; 30 / 8 at both `cb4fe99` and `cac6edc`. The `29 → 30` correction is real and the correction is right.
- The raised-line series: 63 whole-file / 61 head at every one of `700c599`, `8c6539a`, `b3be433`, `00b961f`, `59cc2ad`, `7b182b0`, `3f70eb3`, `09e9307`, `cb4fe99`, `cac6edc`; 67 / 65 on the working file. `git rev-list --reverse 700c599..cac6edc -- "$D"` returns exactly the eight commits named, in the order named.
- No `path:NN` line pin was added by this diff, in either the extension-alternation form or the backticked bare form. Rule 2 holds.
