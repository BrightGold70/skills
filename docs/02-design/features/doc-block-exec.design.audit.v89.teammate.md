## Summary
Gating pass on design v1.98 at freeze sha `8909ec4`. I re-ran every figure the delta ships rather
than reading it: the census differential harness, the five-kinds descriptor probe, the 6-gram
carried-text screen, the dotted-seam derivation, the four scoped/unscoped diff pairs, both line-pin
sweeps, the seam-ordinal head and tail, and the seam enumerations in all three documents. Almost
everything reproduces byte-for-byte at `8909ec4` — but the paragraph that exists to stop carried
figures publishes three wrong statements about its own screen's output, and the Version History
entry justifying the sibling-contract change makes a false claim about the impl-plan's bytes.
Evidence: 8 files opened directly (design, `h-mad/SKILL.md`, `handoff/SKILL.md`, `doc-block-exec.spec.md`,
`doc-block-exec.impl-plan.md`, the v87 teammate report, the saved delta, plus 35 corpus files read by
the shipped census harness), 47 greps/commands run.

Axis C — spec reconciliation, all 49 `AC-N.M` in `docs/01-plan/features/doc-block-exec.spec.md`,
derived at `8909ec4` by splitting the design at the line-anchored `## Version History` (line 2324 —
the string occurs 5 times in the file and only once as a heading line; a naive `str.split` truncates
the head to 87 023 of 288 681 bytes and reports 26 false absences, which is how I first got it wrong)
and expanding the Test-Plan ranges:

| Group | Spec ACs | Classification | Basis |
|---|---|---|---|
| AC-1.1–1.9 | 9 | implemented-as-written | Test Plan rows `AC-1.1–1.7`, `AC-1.8`, `AC-1.9`; spot-verified AC-1.1/1.2 against the `NOT_FOUND` and `AmbiguousBlock` prose (8 and 4 occurrences in the head) |
| AC-2.1–2.8 | 8 | implemented-as-written | rows `AC-2.1–2.7`, `AC-2.8`; spot-verified AC-2.1 substitution prose |
| AC-3.1–3.14 | 14 | implemented-as-written | rows `AC-3.1–3.10`, `AC-3.11–3.12`, `AC-3.13`, `AC-3.14`; spot-verified AC-3.4 (`shell=plain`, `exit 3`) and AC-3.10 (`stream_path_unwritable`, 16 occurrences) |
| AC-4.1–4.6 | 6 | implemented-as-written | rows `AC-4.1–4.5`, `AC-4.6`; spot-verified AC-4.1 (`RAN rc=`) |
| AC-5.1–5.6 | 6 | implemented-as-written | rows `AC-5.1–5.4`, `AC-5.5`, `AC-5.6`; spot-verified AC-5.1 (`TIMEOUT seconds`) |
| AC-6.1–6.6 | 6 | implemented-as-written | single row `AC-6.1–6.6`; spot-verified AC-6.3 — the `COLLECT: OK` token does not occur in the design head, but the four migrated behaviours are named in that row and the `never reaches GATE: PASS` measurement sits at `:1306` |

`restated` 0, `absent` 0. Honest scope: 49/49 are addressed by identifier or range and 8 were
individually read against their spec text; the remaining 41 are classified from the Test-Plan row
that names their range, not from a line-by-line reading of each AC in this pass.

## Must-fix
- The 6-gram screen's own accounting is wrong: the shipped screen prints **two** runs carrying the
  dottedness clause, not one. I extracted the fence at `docs/02-design/features/doc-block-exec.design.md:1811-1830`
  and ran it verbatim with `D`=this file, `R=docs/02-design/features/doc-block-exec.design.audit.v87.teammate.md`,
  `BASE=35698f9`, `HEAD=6f0ee85`: 23 runs, of which `and seven of the eight seams are dotted module paths so`
  and `0 60 and seven of the eight seams are dotted module paths so the` both carry the clause
  (`git diff 35698f9 6f0ee85 -- $D | grep '^+' | grep -c 'seven of the eight seams'` → `2`). The
  decomposition is 21 + 2, not 22 + 1. This is a count of the screen's own printed output published
  without re-deriving it, inside the paragraph whose stated rule is that a figure is not a
  measurement until this document re-derives it — and it is repeated at three sites (the body, the
  v1.97 bracketed note, and the v1.98 entry).
  quote: docs/02-design/features/doc-block-exec.design.md › `it prints **23 runs**. Twenty-two are commands, sha pairs,`
- The exculpation that clears 22 of the 23 runs is scoped to Version History, but **8 of the 23 runs
  are body-added lines**, where that rationale does not apply — and the shipped screen does not
  compute the partition, so the one body run it caught it caught by hand-reading. Partitioning the
  added lines of `35698f9..6f0ee85` on `^- v1\.[0-9]` and re-running the same tokeniser and gram set
  gives BODY 8 runs / VH 15 runs; the body runs are `git diff name-only 74e126f 35698f9 h-mad handoff`,
  `git diff name-only a8e0372 sha grep md grep vc docs/`, `a four-backtick fence containing a
  three-backtick line followed by`, `1 where commonmark says 0. the`, `invent a setext heading never
  hide one so`, `separated from its noun by a`, `and seven of the eight seams are dotted module paths so`,
  and `stated so the next author neither strikes a`. A screen whose verdict rests on a categorisation
  it does not compute cannot close the class it was shipped to close: the next carried figure lands in
  the body and is cleared by a Version-History rationale. Prescription: compute the partition inside
  the fence (two counts, labelled BODY and VERSION HISTORY, with units) and state that a body run is a
  finding while a VH run is a transcription.
  quote: docs/02-design/features/doc-block-exec.design.md › `fixture descriptions and quotations of the finding, all of which a Version History entry is`
- The v1.98 Version History entry justifies the NIT-1 sibling-contract change with a claim about the
  impl-plan's bytes that is false. I opened both files at `8909ec4`: the design's canonical taxonomy at
  `docs/02-design/features/doc-block-exec.design.md:1903-1904` reads `os.killpg, shutil.rmtree,
  tempfile.mkdtemp, os.chmod, os.unlink, _final_write, _close_stream`, and the impl-plan's canonical
  taxonomy at `docs/01-plan/features/doc-block-exec.impl-plan.md:46-52` reads the same seven in the
  **same** order; the design's transport-rule site at `:1945-1946` reads `_final_write, _close_stream,
  tempfile.mkdtemp, os.chmod, shutil.rmtree, os.killpg, os.unlink` and the impl-plan's transport-rule
  site at `docs/01-plan/features/doc-block-exec.impl-plan.md:34-36` reads those same seven in that same
  order. Both documents carry the same two orderings at the same two sites; the order never diverges,
  and the spec's list is order-identical too. `verbatim` is indeed false, but for a different reason —
  the impl-plan interleaves AC annotations (`os.killpg` (AC-4.6 reap only)) into its list. This is a
  present-tense sibling-state claim of exactly the kind the change it justifies exists to stop, and it
  was reasoned rather than run. Prescription: a bracketed correction on the v1.98 entry naming the two
  site pairs and the real reason `verbatim` fails, per the standing practice that a false entry is
  bracketed rather than rewritten.
  quote: docs/02-design/features/doc-block-exec.design.md › `membership is identical in all three but the impl-plan lists the same eight in a different order, so 'verbatim' is false`

## Should-fix
- `Four other runs carry a figure` publishes no unit and does not close under any reading — decision H.
  By the document's own three named facts it is **5 runs** (`names 18 files 16 of them md` ×2,
  `unscoped git diff name-only a8e0372 74e126f names 13 files 11 of them` ×2, `only three files in the
  two roots` ×1); by a mechanical count of runs carrying a number outside a sha it is **13**. Neither
  is four. Prescription: state the unit (`runs`, and separately `distinct figures`) and derive both
  from the screen rather than by hand.
- Same sentence, mislabelled run: the two 13/11 runs assert `13 files 11 of them` for
  `a8e0372..74e126f`, which is the false claim v1.97 was correcting, while the document glosses them
  as "`a8e0372..335f535` names 13 / 11". I re-derived all three figures at `8909ec4` and the *facts*
  hold (`a8e0372..74e126f` → 18/16, `a8e0372..335f535` → 13/11, 3 files under the two roots import
  `docsections` — 5 mention it, so the "import" unit is load-bearing and correctly chosen), but the
  run-to-fact mapping as written is wrong.
- The absence rule this revision adds is not swept across the document — instance of the class "a rule
  stated in the same revision that does not apply it". `git ls-files | grep -cE 'heading_differential|grammar_corpus'`
  returns `0` (I re-ran it at `8909ec4`: `0`) and carries its command but **no sha and no
  load-bearing/incidental label**; the `.md`-under-`docs/` invariant at `:206-215` carries command,
  four shas and a reason but no label; `The head returns 0 on the working file this revision ships` at
  `:1898-1899` carries a command and a reason but no label. Three absence sites do not meet the rule
  stated at `:733-735`.
- `N='(seam|injection|primitive)'` inside `\b$N\b` does not match the plurals `seams`, `injections`,
  `primitives`, which this document uses throughout, and residual item 3 names three under-match forms
  without naming this fourth — decision I, since the `\b` bound applies to every sibling of the
  alternation. Measured, not argued: substituting `(seams?|injections?|primitives?)` leaves the
  stripped/folded head at `0` and the Version History tail at `8` at `8909ec4`, so the blindness is
  currently **unexercised**; this is a gap in the stated residual, not a live miss.
- The sibling contract states an obligation but ships nothing runnable to detect its violation —
  `is found by enumerating all three` names no command, while this document's own axis rule requires
  every measurement to publish its command inline or name a script `git ls-files` can find. I did the
  enumeration at `8909ec4`: membership is identical across design `:1903`, `docs/01-plan/features/doc-block-exec.spec.md`
  and impl-plan `:46`, so the contract holds today and the residual is unexercised. Prescription: ship
  the three-way membership fence beside the contract.

## Nit
- `It is still 8 on the working file after the entry **this** revision appends` becomes ambiguous the
  moment v1.99 is appended — "this revision" is not resolvable from the bytes once a later entry
  exists. The neighbouring rule ("a document-self figure names the working file and the entry it was
  run after") is the right one; the sentence should name the entry, not "this revision".
- The four unscoped file/`.md` pairs at `:210-212` grow by one every revision by construction (they
  are 37/35 at `8909ec4`, unpublished), in a paragraph whose own instruction is **Do not publish the
  pair**. The demonstration carries the same force with the three original pairs plus a sentence
  saying why no further one is added.
- The Test-Plan table addresses ACs by range (`AC-1.1–1.7`, `AC-3.1–3.10`, `AC-6.1–6.6`). A reviewer's
  identifier sweep therefore reports 26 spec ACs as unreferenced unless it expands ranges — and the
  dash is an en dash, so an ASCII-hyphen range pattern silently expands nothing and the sweep reads as
  26 absences. Worth one sentence beside the table naming the expansion the reader must do.

### Verified and unmoved at `8909ec4` (re-run, not read)
Scoped `.md`-under-`docs/` invariant → `0` at all five shas; pairs 13/11, 18/16, 25/23, 31/29 all
confirmed. The census differential harness reproduces its published block byte-for-byte, including
`control arm1 shipped 1 repaired 0` / `control arm2 shipped 1 repaired 0`; I independently located the
8 deep-indent marker lines (`h-mad/SKILL.md:2122,2124,2134,2136,2140,2143`, `handoff/SKILL.md:216,222`),
confirmed all four fences open inside list items by reading the surrounding context, and confirmed the
9 body lines and that none sits below 4 columns — the vacuous/incidental distinction is sound. The
original census fence → `tracked files 30 setext_headings 0` / `glob files 35 setext_headings 0`. The
five-kinds descriptor probe reproduces all five rows and `3.11.8 darwin 25.6.0`. The dotted-seam
derivation prints the seven seams then `5`. `git show 35698f9:$D | grep -cF '(first|second|third'` → `2`
against `1` at `6f0ee85` — the v88 rejection was correct — and `git show 35698f9:$D | grep -cF "tr '\n' ' '"`
→ `0` against `1` at `6f0ee85`. Seam-ordinal head → `0` stripped, `1` unstripped with the hit being the
alternation's own source; tail → `8` at `35698f9`, `6f0ee85` and the working file alike, on entries
v1.12/23/48/49/69/76/95/96. `^ {4,}` fence bound → `0` at `6f0ee85` and on the working file. Both
line-pin fences → `0`; the three-blind-form sweep returns only `lines 159` and `lines 50`, the
block-census output fields.

### Not re-run, and therefore not verified
The agy leg's tool count in the v1.98 entry (the document says it is the orchestrator's dispatch record
and not derivable here — I did not attempt it). The `1861157` plan-§Measurements transcript
(`files=25`/`30`) is quoted as *not* re-derivable and I did not try. The `ENXIO` timing figure `0.0000s`,
the `finder/bounder 30 / 292 / 82 / 1` differential, and the `2748` suite floor were left unchallenged
from earlier rounds; unchallenged is not verified.
