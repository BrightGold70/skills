# Adversarial review — `5af7aaf`

`fix(h-mad): rebuild the Version History boundary on the repo's strict anchor, after a fresh review found 10 defects in a8b9e4e`

Fresh context. The authoring session's reasoning was treated as a claim to test, and the
prior review (`docs/04-report/features/precheck-version-history-boundary.review.v1.md`) as
prior art to verify rather than trust.

**Worktree:** `/Users/kimhawk/orca/skills/.claude/worktrees/agent-a7a3a8a815841095e`, HEAD
`404377d` (the review-doc commit, whose parent is `5af7aaf`). All `python3.11`.

---

## What I read and ran

**Read (whole or in the relevant range):**

- `h-mad/scripts/h_mad_precheck_doc.py` (724 lines) at `5af7aaf` — `_line_of`,
  `_version_history_bounds`, `scan()` :379–666, `hard()`, `historical_by`, `_PATHISH`,
  `_LINE_TAIL`, `_line_digits`, `main()`'s `--allow-historical` help
- `h-mad/scripts/h_mad_version_history.py` in full (297 lines) — `ANCHOR`, `HEADER`,
  `RULE`, `find_anchor`, `section_bounds`, `Refusal`
- `h-mad/scripts/h_mad_assemble_audit.py` — the deleted `version_history_start`, the
  rewritten `VH_MARKER` comment
- `h-mad/scripts/h_mad_doc_block_exec.py` — `_fence_events` :178, `fence_aware_end` :216
  (this repo's own CommonMark fence scanner)
- `h-mad/tests/test_h_mad_precheck_doc.py` — the 182 added lines in full, plus the
  helpers (`run`, `write`, `_root_commit`, `_TWO_PINS`, `_COLON_PIN`) and `tests/conftest.py`
- all three touched mutation specs in full
- `h-mad/SKILL.md:2846` (the shipped paragraph, not the diff)
- the full `git show 5af7aaf` and the prior review report (406 lines)

**Ran:**

| # | command / probe | result |
|---|---|---|
| 1 | `cd h-mad && python3.11 -m pytest tests/ -q` (on a **quiescent** tree) | `3273 passed, 1 warning in 517.53s` — matches the commit's claim |
| 2 | `python3.11 -m pytest tests/test_h_mad_precheck_doc.py -q` | `57 passed in 16.24s` |
| 3 | 45 hostile fixtures through `h_mad_precheck_doc.py --json` in a purpose-built two-commit scratch repo (`scratchpad/lab`, so `PINDRIFT` is live) — `exp1.py` (F1/F2/F6 re-reproduction), `exp2.py` (seam: fences, heading variants, degenerate docs, CRLF, front matter, terminators), `exp4.py` (fence grammar vs `_fence_events`), `exp5.py` (section END), `exp6.py` (the 16-row `--allow-historical` spelling matrix) |
| 4 | **17 mutation rows re-scored independently** across the three touched specs, each with a git-restore + clean-tree assertion before and after, and a clean-tree baseline run of the named test — `mut2.py` |
| 5 | `_line_of` exhaustive: 6,390 texts (all products of an 11-symbol break alphabet to length 3, plus 4,000 random, plus hand cases) × **every prefix position**, against three independent ground truths | 0 mismatches |
| 6 | differential of the local fence mask against `section_bounds`' own fence scanner over 20,000 random documents | 0 disagreements |
| 7 | corpus A: all 235 markdown files under `docs/01-plan/features` + `docs/02-design/features` (a **superset** of the 44 phase documents — it also contains `*.audit.vN.*.md` reports), shipped boundary vs a boundary built on `h_mad_doc_block_exec._fence_events` | 40 resolve a section, **0 differ** |
| 7b | corpus B: the same files, `a8b9e4e`'s `version_history_start` (reconstructed, section running to EOF) vs `5af7aaf`'s `_version_history_bounds` — the direction the commit's "0 verdict moves" claim lives in | all 235: `found→refused=0`, `none→found=0`, `span_changed=0`. The 44 phase documents alone: 32 resolve a section, 12 do not, **0 moves** |
| 8 | fuzz: 60,000 random line-lists through `_version_history_bounds` | 0 crashes, 0 invalid ranges |
| 9 | `grep -rn "version_history_start"` across **all of** `/Users/kimhawk/orca` (EconoSuite, HemaSuite, HemaSuite-wsg, skills, workspaces, worktrees) | 2 hits, both prose |
| 10 | F7 re-check: 5 in-process `scan()` calls, `len(sys.path)` before/after | 8 → 9 (was +1 per scan) |

**A measurement of my own that was invalid, recorded rather than quietly redone.** My first
two mutation-scoring runs disagreed with each other (`the-fence-mask-is-removed` and
`the-sha-loop-…` swapping CAUGHT/SURVIVED, and one named test failing on a "clean" tree).
The cause was a background process of my own still alive and mutating
`h_mad_precheck_doc.py` underneath both runs — a `pgrep` said it was gone and the task
notification arrived minutes later. Both runs are **discarded**; every number in §4 and in
the suite row above comes from a re-run on a tree I asserted clean before and after each
row. The first full-suite run (`7 failed, 3266 passed`) was contaminated the same way and
is not reported as a result.

**5 findings — Critical: 0 · Major: 3 · Minor: 2.** All CONFIRMED by execution.

**Nothing here is a defect this commit introduced, and I looked for one specifically.**
Every finding is a residual of `a8b9e4e` that `5af7aaf` **narrowed rather than closed**
(Findings 1, 2, 3, 4), or a pre-existing upstream asymmetry that this commit newly makes a
precheck verdict input (Finding 5). Under `a8b9e4e` a `~~~`- or ` ```` `-fenced heading
silenced the body too (there was no fence tracking at all) and `## Open Questions` after the
history was silenced *unconditionally*, not only behind an indented literal fence. On every
hostile case I built, `5af7aaf` is strictly better than or equal to its parent. That is a
materially different verdict on the change than the finding count alone suggests, and it is
the one the evidence supports.

The one direction an introduced regression could have hidden — the commit newly *refuses*
anchors `a8b9e4e` accepted (ambiguity, a masked heading, a `###` or indented heading), which
on a real document would be a `PASS → FAIL` move against the commit's "0 verdict moves"
claim — is measured in §*Checked and found correct* and is **0 in both directions over all
44 phase documents**.

---

## First: did F1–F10 actually get fixed?

Re-run of the prior reviewer's own reproductions (`exp1.py`, `exp2.py`, `exp6.py`, `mut2.py`).

| | verdict | evidence |
|---|---|---|
| **F1** line-break unit mismatch | **FIXED** | all 8 exotic breaks (`\x0c \x0b \x1c \x1d \x1e \x85` U+2028 U+2029) above the heading now `FAIL issues=1` where `a8b9e4e` gave `PASS issues=0`; the 3-form-feed scaling case gives `FAIL issues=3`. Fixed *by construction* (line indices, not arithmetic), and `_line_of` closes the sha loop's second basis — see §5 below |
| **F2** no section END | **FIXED** | `## Next Steps` after the history → `FAIL issues=2`; `---` after the history → `FAIL issues=2`; two headings → `FAIL issues=2`, nothing demoted. But see **Finding 2**: one indented literal fence re-opens it |
| **F3** false justification | **HALF-FIXED** | the code genuinely delegates to `h_mad_version_history`, and `VH_MARKER`'s comment is corrected. But the sentence the commit message quotes as the false one still ships, verbatim, at the rule's own call site — **Finding 3** |
| **F4** `:L12` not interchangeable | **FIXED** for single-line pins | 16-row matrix: all four single-line combinations demote; 4 negative controls (`:112` vs `:L12`, `:12` vs `:L1`, `:L112` vs `:L12`, `:2` vs `:L20`) all correctly refuse. The added arm cannot over-silence. Ranges remain asymmetric — **Finding 4** |
| **F5** no test bit | **FIXED** | 17/17 mutation rows CAUGHT, independently re-scored. Details in §6 |
| **F6** fenced heading | **FIXED for ` ``` ` only** | the ` ``` ` case now `FAIL issues=2`. `~~~`, ` ```` `, and a trailing-text closer still silence the body — **Finding 1** |
| **F7** `sys.path` leak | **FIXED** | 5 `scan()` calls add exactly 1 entry (was 5) |
| **F8** retracted rationale in test + spec | **FIXED in those two** | both rewritten. A third copy survives — **Finding 3** |
| **F9** `SKILL.md:2846` | **FIXED** | the paragraph now states the demotion, names it *the one exception* to "`--allow` is an input, never inferred", says two headings demote nothing, and says "a `PASS` may be a demoted `FAIL`; read the `ALLOWED:` lines". Accurate, with one overstatement noted in Finding 1 |
| **F10** `1-L9` invisible | **FIXED** | `1-L9` now parses as a line pin and produces a `PINDRIFT` |

---

## Major

### Finding 1 — CONFIRMED — F6 is closed for exactly one fence spelling; three others still let a quoted `## Version History` silence the whole document body

The new mask is

```python
if line.lstrip().startswith("```"):
    fenced = not fenced
```

which is not the fence grammar. Three shapes defeat it. All three were executed against the
shipped script in the scratch repo (`exp4.py`); each document's real body carries a `TBD` and
a drifted pin, and the control with no fence at all is `FAIL issues=2`.

```
CASE m1_backtick4_quotes_backtick3          -> PASS issues=0
     ALLOW PLACEHOLDER TBD L10 (in `## Version History`)
     ALLOW PINDRIFT src/target.py:2 L11 (in `## Version History`)
CASE m2_trailing_text_closer                -> PASS issues=0
     ALLOW PLACEHOLDER TBD L10 (in `## Version History`)
     ALLOW PINDRIFT src/target.py:2 L11 (in `## Version History`)
CASE m4_tilde_wraps                         -> PASS issues=0
     ALLOW PLACEHOLDER TBD L8 (in `## Version History`)
     ALLOW PINDRIFT src/target.py:2 L9 (in `## Version History`)
CASE m5_control                             -> FAIL issues=2
     FIND PLACEHOLDER L4 TBD — unresolved slot
     FIND PINDRIFT L5 `src/target.py:2` — … changed since the document's provenance
```

- **m1** is `` ````markdown `` wrapping a ` ``` ` block that quotes the heading. This is not an
  exotic shape: it is *the only way* to quote a fenced template in markdown, and the commit's
  own stated reason for the mask is "this repo quotes its own templates". The likeliest
  instance of the scenario F6 names is the one F6's fix does not cover.
- **m2** is a ` ```trailing ` line, which CommonMark does not accept as a closer. The naive
  scanner closes on it, un-masks the quoted heading below, and reads it as the section start.
- **m4** is a `~~~` fence, which the mask does not recognise at all.

**The repo already owns the correct scanner and says so.** `h_mad_doc_block_exec._fence_events`
(:178) and `fence_aware_end` (:216) implement backtick **and tilde** runs of ≥3, closers of
≥ the opening run followed by nothing but whitespace, 0–3-space indent, and info-string rules.
`docs/02-design/features/doc-block-exec.design.md` states the rule the new mask breaks:

> **The fence grammar has one home**: a private generator `_fence_events(text)` that both
> `extract` and `fence_aware_end` consume, so the two surfaces cannot diverge by construction

and that feature ships mutation rows named `tilde-fence-not-tracked`,
`closer-trailing-text-accepted` and `indented-opener-accepted`, plus a test
`test_bounder_ignores_a_heading_inside_a_tilde_fence`. Driven directly, `_fence_events`
disagrees with the mask on all three:

```
m1: VH line idx=2 naive_fenced=False  events=[('open','`',4),('body',…),('body',…),('body',…),('close',…)]
m2: VH line idx=2 naive_fenced=False  events=[('open','`',3),('body',…),('body',…),('close',…)]
m4: VH line idx=1 naive_fenced=False  events=[('open','~',3),('body',…),('close',…)]
```

**Latent, not live — measured, not assumed.** Over all 235 markdown files under
`docs/01-plan/features` and `docs/02-design/features` — a superset of the 44 phase documents,
since it also sweeps the `*.audit.vN.*.md` reports — the shipped
boundary and a boundary built on `_fence_events` agree on every one (40 resolve a section,
195 resolve none, 0 differ). No corpus document carries a `~~~` or ` ```` ` fence; two carry a
four-space-indented ` ``` ` and neither moves the boundary. This is the same standing the
prior reviewer gave F1, F2 and F6 themselves.

**Also:** `SKILL.md:2846` now says the section is bounded "fence-aware". That is true of
` ``` ` only, and the operator-facing contract does not say which.

**Failure scenario.** An impl-plan whose "how to write your history" section quotes the
template inside a ` ```` ` wrapper (the standard way), or a design document using `~~~`. Every
`TBD`, unfilled slot, past-EOF pin and `PINDRIFT` below that quote is demoted, and the gate
prints `PRECHECK: PASS issues=0`.

---

### Finding 2 — CONFIRMED — a four-space-indented literal fence inside the history extends the section past a real `##` heading, re-opening F2 in the fail-OPEN direction

`section_bounds` uses the same naive rule for the section's END, and this one the mask cannot
help with — it is upstream, and the precheck passes it the *unmasked* lines by design.

A four-space-indented ` ```bash ` is an indented code block under CommonMark (`_fence_events`
classifies the whole document as `prose`), and it is how this repo's own markdown shows a
fence opener without opening one. `section_bounds` reads it as a fence opening, so the
following real `## Open Questions` heading never terminates the section (`exp5.py`):

```
CASE n1_indented_fence_in_vh                -> PASS issues=0
     ALLOW PLACEHOLDER TBD L14 (in `## Version History`)
     ALLOW PINDRIFT src/target.py:2 L15 (in `## Version History`)
CASE n1b_control                            -> FAIL issues=2      # same doc, fence line removed
     FIND PLACEHOLDER L12 TBD — unresolved slot
     FIND PINDRIFT L13 `src/target.py:2` — … changed since the document's provenance
```

That is exactly the F2 failure the commit's `test_the_section_ENDS_at_the_next_heading` exists
to prevent, reachable by one indented line. The mutation row `the-section-runs-to-end-of-file-again`
does not cover it, because the row mutates the *call* to `section_bounds`, not its fence rule.

**The adjacent case, reported for honesty rather than as a defect.** An *unclosed* ` ``` `
fence inside the history has the same effect (`exp2.py` `s2_unclosed_fence_in_vh` → `PASS
issues=0`; `s2b_closed_fence_in_vh` → `FAIL issues=2`). But an unclosed fence really does run
to the end of the document under CommonMark, so that one is the documented cost of honouring
fences, not a scanner bug. It is untested all the same, and it is the cheapest way for an
author to silence the tail of a document.

**Latent, not live**: the same 235-document measurement above. Two documents carry an indented
literal ` ``` `; neither is inside a Version History section.

---

### Finding 3 — CONFIRMED — the F3 justification the commit declares false still ships, verbatim, at the rule's own call site

The commit message says:

> **F3 — the justification was false.** The commit rested the rule on sharing the assembler's
> anchor, **"the two agreeing is the whole point"**. The review falsified it four ways …

and `_version_history_bounds`' new docstring (`:286-292`) retracts it in full. One hundred
lines below that docstring, the comment block immediately above the call still says:

```
h-mad/scripts/h_mad_precheck_doc.py:394
    # Everything from the `## Version History` heading to the end of the document
    # is a DATED RECORD, …
:398
    # The basis is the assembler's recorded position on the same section —
    # `_trim_version_history`: …
:419
    # This is NOT the document-side marker `historical_by` refuses. That refusal is
    # about an author granting THEMSELVES a silencer; here the precheck follows a
    # decision the ASSEMBLER already made about the same section, and the two
    # agreeing is the whole point.
    vh_bounds = _version_history_bounds(lines)
```

Three separate problems in one block:

1. **":394 is now factually wrong about the code."** The section no longer runs "to the end of
   the document" — ending it is the whole of F2's fix, and `test_the_section_ENDS_at_the_next_heading`
   asserts the opposite of this sentence. A maintainer reading the rule top-down meets the
   pre-fix behaviour first.
2. **":398 names the wrong basis.** The basis is `h_mad_version_history`, not
   `_trim_version_history`; F3(a)/(b) established the assembler omits the *entries* and, for a
   table-shaped history, nothing.
3. **":419-422 is the retracted sentence itself**, and it is the one that answers the
   `historical_by` objection (F6-as-design-question in the prior review). With its premise
   gone, the file now contains no surviving answer to "why is this document-side silencer
   allowed when `historical_by` refuses one?" — it contains a *withdrawn* answer presented as
   the live one.

**This specific line was named in the report being remediated.** Prior review F6, closing
paragraph (`precheck-version-history-boundary.review.v1.md:305`):

> The in-code rebuttal ("here the precheck follows a decision the ASSEMBLER already made
> about the same section") is the claim F3 falsifies.

So it was quoted back at the author, by line, in the document this commit exists to answer.
The commit hunted F8's rationale into the test docstring and the spec `_why` — "the two
artifacts a reader reaches through a mutation spec's `test` key" — and left the copy that
had been pointed at directly.

A note on how to find it, because the obvious sweep says it is already gone: the sentence is
hard-wrapped across a comment break, so
`grep -n "the two agreeing is the whole point" h-mad/scripts/h_mad_precheck_doc.py` returns
**nothing**. It is found only by collapsing the wrap —
`python3 -c "import re,pathlib; print('the two agreeing is the whole point' in re.sub(r'\n\s*#\s*',' ',pathlib.Path('h-mad/scripts/h_mad_precheck_doc.py').read_text()))"`
→ `True` — or by grepping the tail alone, `grep -n "agreeing is the whole point"` → line 422.
A one-line value sweep for the retracted sentence would have reported it closed.

---

## Minor

### Finding 4 — CONFIRMED — a fully-`L`-spelled RANGE declaration is still ignored without an error

F4's fix adds one arm, `historical_by(f"{rel}:L{digits}")`, where `digits` is `_line_digits(tail)`
— so for a range it generates the hybrid `L2-3` and never `L2-L3`. Executed matrix
(`exp6.py`, 16 rows; `demoted=True` means the declaration was honoured):

```
doc=:2      decl=src/target.py:2        demoted=True
doc=:2      decl=src/target.py:L2       demoted=True     <- F4 direction, newly fixed
doc=:L2     decl=src/target.py:2        demoted=True
doc=:L2     decl=src/target.py:L2       demoted=True
doc=:2-3    decl=src/target.py:2-3      demoted=True
doc=:2-3    decl=src/target.py:L2-L3    demoted=False    <<<
doc=:2-3    decl=src/target.py:L2-3     demoted=True
doc=:L2-L3  decl=src/target.py:2-3      demoted=True
doc=:L2-3   decl=src/target.py:L2-L3    demoted=False    <<<
doc=:112    decl=src/target.py:L12      demoted=False    (correct — no over-silencing)
doc=:12     decl=src/target.py:L1       demoted=False    (correct)
doc=:L112   decl=src/target.py:L12      demoted=False    (correct)
doc=:2      decl=src/target.py:L20      demoted=False    (correct)
```

The operator writes the most natural L-spelling of a range and the flag is ignored **without
an error** — the precise failure the comment at `:576-580` claims to be closing, and the
reason F4 was filed. The shipped help now reads "The two line spellings are interchangeable —
`:12` and `:L12` declare the same pin" directly beside "A RANGE is declared by the whole
range", so a reader has every reason to expect `:L2-L3` to work.

Fix: normalise inside `historical_by` (apply `_line_digits` to `a`) rather than enumerating
spellings at the call site — four arms already enumerate three of four spellings.

**Checked and clean:** the added arm cannot silence a pin it should not. `historical_by` is
`/`-anchored equality-or-suffix, so `foo.py:L112` never ends with `/foo.py:L12`; all four
negative controls above refuse.

### Finding 5 — CONFIRMED — `ANCHOR` accepts a heading spelling that `HEADER` refuses, so a line can START a section that an identical line cannot END

`ANCHOR = r"^##[ \t]*Version History[ \t]*$"` makes the space optional; `HEADER = r"^#{1,6} "`
requires it. Executed (`exp2.py`):

```
CASE s4_nospace                    -> FAIL issues=2 + ALLOW PLACEHOLDER TBD L9   # `##Version History` DID anchor
CASE s8_nospace_header_terminator  -> PASS issues=0
     ALLOW PLACEHOLDER TBD L12 (in `## Version History`)     # `##Open Questions` did NOT terminate
     ALLOW PINDRIFT src/target.py:2 L13 (in `## Version History`)
```

Neither spelling is an ATX heading under CommonMark, so the pair is doubly wrong, in opposite
directions. Pre-existing and upstream in `h_mad_version_history`; this commit is what makes it
a precheck verdict input. Both shapes are unlikely in practice — filed so the asymmetry is on
the record rather than because either is likely to fire.

---

## Checked and found correct — recorded so the absence of a finding is not silence

- **`_line_of` is exhaustively correct.** 6,390 texts × every prefix position (≈40k
  evaluations), against three independent ground truths: a sentinel-`splitlines` definition,
  a hand-written break walk that treats `\r\n` as one break, and `enumerate(text.splitlines(), 1)`
  — which is the basis the per-line loop uses. **0 mismatches**, including position 0, position
  `len(text)`, a text ending in a break, `\r`, `\r\n` split across the cut, and every
  `splitlines`-only break character. The docstring's claim about the `\x00` sentinel is exact.
- **The two fence scanners provably cannot disagree, and do not.** `section_bounds` starts at
  `anchor + 1` with `fenced = False`; the mask's state at that same index is also `False`
  (the anchor was not masked, and an anchor line cannot be a fence line), and from there both
  apply the identical rule to the identical list. A differential over **20,000 random
  documents** built from a 12-symbol vocabulary found **0 disagreements**. The index arithmetic
  is also sound: the mask preserves line count, so `find_anchor(masked)` and
  `section_bounds(lines, …)` index the same rows.
- **The `anchor + 1, end` conversion is right.** `end` is a 0-based half-open bound, so 1-based
  the last line of the section is `end`, the terminator line is excluded, and an empty body
  collapses to the heading alone. Verified on the `---`-immediately-after-heading case
  (`s6_rule_after_heading` → `FAIL issues=2`, nothing demoted) and on a one-line document.
- **Degenerate documents behave.** One-line document that is only the heading → `PASS`, no
  crash. Heading as the last line, with no trailing newline → correct. Heading as the *first*
  line → now demotes correctly (`a8b9e4e` returned `None` here because its marker carried a
  leading newline). CRLF throughout → correct (`read_text()` normalises before either scanner).
  `---` front matter at the top → correct. `###`, indented `  ##` → not anchors, fail closed.
  Case (`## version history`), trailing whitespace, and a tab after `##` → all anchor, as
  `ANCHOR` documents.
- **Fail-closed directions hold.** Two headings → `None`, nothing demoted, `FAIL issues=2`
  (`f2_two_headings`). An unclosed fence *above* the heading masks it → `None`, `FAIL issues=3`
  (`s3_unclosed_fence_above`). Absence → `None`. 60,000 random line-lists through
  `_version_history_bounds`: 0 exceptions, 0 ranges outside `1 ≤ first ≤ len(lines)` /
  `first-1 ≤ last ≤ len(lines)`.
- **The mutation spec bites, and I re-scored it myself rather than reading its claim.** All
  **17** rows across the three touched specs: every `find` string occurs **exactly once** in
  the shipped source; every `test` key names a file that exists and a test name present in it;
  every named test **passes on the clean tree**; every mutation is **CAUGHT** with an
  `AssertionError` (`fail=1 err=0` — **0 crash-kills**, which is the failure mode that reads
  as a clean kill).
- **The two rows the commit says were re-fixtured genuinely discriminate.**
  `ambiguity-is-resolved-by-taking-the-first-heading` is killed by a test that asserts
  `PRECHECK: FAIL issues=3` *and* that no `ALLOWED:` line mentions the section — under
  first-match the template block's finding would be demoted and the count would be 2, so the
  count assertion is what does the work, exactly as its comment claims. `the-sha-loop-numbers-
  the-other-way-again` is killed by a fixture with **three** exotic breaks, and the commit
  states plainly why one was not enough (the sha sits two lines below the heading). Neither is
  tuned-until-green; both assert the property the mutation changes.
- **The commit's "0 verdict moves against `a8b9e4e`" claim is TRUE, verified independently
  and in the direction that could hide an introduced defect.** The new boundary *refuses*
  shapes the old one accepted (two headings, a masked heading, a `###` or indented heading),
  and every such refusal on a real document would be a `PASS → FAIL` move. I reconstructed
  `a8b9e4e`'s `version_history_start` in-process and compared its section (`start` → EOF)
  against `_version_history_bounds` on all 235 documents: `found→refused = 0`,
  `none→found = 0`, `span_changed = 0`. Restricted to the **44 phase documents** the commit
  names: 32 resolve a section, 12 do not, and **not one boundary moves in either direction**.
  Note this is the check my §*Corpus* differential could *not* make — there both sides call
  `find_anchor`, so a document that went found→refused would land in `both_none` and read as
  agreement. Measured separately for that reason.
- **The `version_history_start` deletion is clean.** `grep -rn` across *all* of
  `/Users/kimhawk/orca` — `EconoSuite/`, `HemaSuite/`, `HemaSuite-wsg/`, `skills/`,
  `workspaces/`, `worktrees/` — returns exactly two hits, both prose: the prior review report
  and the new mutation spec's `_why`. No code, no test, no spec `find` string, no doc block
  references it. `h_mad_archreview_cycle._trim_vh` reaches into `h_mad_assemble_audit` for
  `_trim_version_history`, not for the deleted helper.
- **F7's guard works and does not over-correct.** 5 `scan()` calls grow `sys.path` by 1, not 5.
  It still inserts at position 0, which is what the prior reviewer proposed.
- **`SKILL.md:2846` is accurate** about the demotion, the exception to "`--allow` is an input,
  never inferred", the two-headings rule, and "a `PASS` may be a demoted `FAIL`" — with the
  single "fence-aware" overstatement noted in Finding 1.
- **Suite is green on a quiescent tree**: `3273 passed, 1 warning in 517.53s`, matching the
  commit message's "suite 3273 passed" exactly. `tests/test_h_mad_precheck_doc.py` alone:
  `57 passed`.
- **The working tree was left clean.** `git status --short h-mad/` is empty after every
  mutation run.

---

## Suggested order of repair

1. **Finding 3** — delete or rewrite `h_mad_precheck_doc.py:394-422`. It costs nothing and it
   removes the only *false* sentence now in the change. While there, give the `historical_by`
   objection a live answer, since the one that stood was withdrawn.
2. **Finding 1 + Finding 2** together — they are one root cause. Replace the local mask and
   the `section_bounds` fence rule with `h_mad_doc_block_exec._fence_events`, which this repo
   built for exactly this and whose design states the one-home rule the new mask breaks. That
   closes `~~~`, ` ```` `, trailing-text closers and indented literal fences in both the START
   and the END direction at once. Add spec rows mirroring `tilde-fence-not-tracked`,
   `closer-trailing-text-accepted`, `indented-opener-accepted`. If the upstream asymmetry is
   deliberately left alone, say so against the *corpus measurement* (0 of 235 differ) rather
   than against the mask.
3. **Finding 4** — normalise inside `historical_by` instead of enumerating spellings; four
   arms currently generate three of four.
4. **Finding 5** — cheap and independent; upstream.
