## Summary

Read the `35698f9..6f0ee85` design delta in full (230 insertions), then swept the whole document,
re-deriving every published figure at the freeze sha `6f0ee85` rather than reading its stated
output. The delta discharges the three things the dispatch named: the `##`-slicer override is
complied with (scope rule + AST sweep + no slicer cardinality, and the sweep is a *different*
predicate from the 8/8 one — it prints 22 including `telemetry_section` and both `_section`s the
mechanical predicate missed, and excludes `write_done_report`/`_plan`); the v1.95 bracketed note
quoting 13/11 is untouched and is correct at `335f535`; v87's should-fix 3 produced no edit.
Almost everything else reproduces exactly — invariant `0` at four shas, unscoped pairs 13/11 ·
18/16 · 25/23 (and 31/29 at `6f0ee85`, unpublished and correctly so), scoped diff empty
`74e126f..6f0ee85`, head `0` / tail `8` / unstripped `1` with the hit being the alternation's own
source, positive control `4` vs the predecessor's `3`, dotted fixture `1`/`0`, true-negative `0`,
the Setext fence byte-exact with all three controls run against the *shipped* `census()`
(2 / 0 / 0-where-old-gives-1), the heading differential byte-exact, `_titled_section` at 8 call
sites, line-pin `0` and `0` with the same two `lines …` output hits, consumer census 3 files, and
all four over-count members plus the one under-count member verified by opening the bodies. Two
things do not: a seam-composition count contradicted by the document's own enumeration and
carried verbatim from the v87 report, and a residual whose corpus claim is false in one of its
two arms.
Evidence: 17 files opened (plus the 30 tracked and 35 globbed `.md` the published census reads
programmatically), 51 greps/commands run.

## Must-fix

- `seven of the eight seams are dotted module paths` is false — **five** of the eight are. The
  document's own canonical enumeration at :1661 is `os.killpg`, `shutil.rmtree`,
  `tempfile.mkdtemp`, `os.chmod`, `os.unlink`, `_final_write`, `_close_stream` plus the
  instance-level `Popen` wrapper; `_final_write`, `_close_stream` and the `Popen` wrapper carry no
  dot, so the dotted members are five. The figure is a conflation of "**seven** module-level
  seams" (true, and stated eight lines above the site) with "dotted" (five). It is load-bearing
  where it sits: it is the stated reason the `[^.]{0,60}` gap was "the natural phrasing for this
  very set", i.e. the warrant for control #2. The conclusion survives — five of eight is still the
  majority — but this is the same shape as v87 MUST 1, where a figure whose conclusion survived
  was still a must. Two aggravations: (a) the figure is **carried verbatim from the v87 teammate
  report** ("seven of the eight seams are dotted module paths"), while the v1.97 entry opens
  "Every figure re-derived at 35698f9; none carried from the report" — so the one figure that is
  wrong is the one that was not re-derived, and the entry's own honesty claim is falsified by it;
  (b) it appears at two sites, the body and the v1.97 Version History entry, and Version History
  is exempt for line pins only, never for factual claims, so the entry needs the bracketed
  correction the document already uses twice. Prescription: "five of the eight seams are dotted
  module paths (`os.killpg`, `shutil.rmtree`, `tempfile.mkdtemp`, `os.chmod`, `os.unlink`); the
  three undotted ones are `_final_write`, `_close_stream` and the `Popen` wrapper" at the body
  site, plus a bracketed note on the v1.97 entry. Sibling cross-check run: the spec (`:425–430`)
  and impl-plan (`:34–52`) both enumerate the identical eight and both say "seven module seams",
  so no sibling repair is owed.
  quote: docs/02-design/features/doc-block-exec.design.md › `seven of the eight seams are dotted module paths`

- The new two-arm residual on `census()` states `The corpus has none of either`, and that is
  **half false**: arm (1) is right (I measured 0 info-string openers read as closers over the 30
  tracked `.md`), but arm (2) has **four** live instances — three fences opened inside numbered
  list items in `h-mad/SKILL.md` (openers at `:2122`, `:2134`, `:2140`; closers `:2124`, `:2136`,
  `:2143`) and one in `handoff/SKILL.md` (`:216`, closer `:222`), together putting **9** lines
  through the prose scanner that CommonMark holds inside a fence. Both files are in the census
  corpus. The blindness is reachable, not theoretical: the shipped `census()`, run verbatim over a
  fixture whose list-item fence contains a column-0 paragraph plus `===`, returns `1` where
  CommonMark says `0`. This breaks the invariant the paragraph exists to serve — the residual is
  the reader's only statement of what the `0` is worth, and "the corpus has none" converts an
  *exercised* blind spot into a claimed-unexercised one, which is exactly the recurrence the
  dispatch named. Why the published `0` nevertheless stands, and the sentence that should replace
  the false one: all 9 prose-scanned lines sit at indent ≥ 4 (measured: 4, 4, 4, 6, 4, 4, 8, 4,
  8), so `UND`'s `^ {0,3}` cannot match them and `SKIP`'s `^    ` alternative refuses their
  predecessors — the figure is structurally safe, not lucky, and the false-positive path needs
  content dedented *below* the fence's own indent, which the corpus does not have. Prescription:
  replace "The corpus has none of either" with "arm (1) is unexercised on the corpus (0
  instances); arm (2) is exercised — 4 list-item fences, 9 lines scanned as prose in
  `h-mad/SKILL.md` and `handoff/SKILL.md` — and the `0` survives only because `UND` and `SKIP` are
  themselves indent-bounded at 0–3, so a false positive needs content dedented below the opener."
  `instance of: a 0–3-column indent bound in a published fence tracker, shipped without a
  residual for the fences it cannot see.` **Class closed, both members named**: the seam-check's
  `$STRIP` carries the identical `^ {0,3}(\`{3,}|~{3,})` bound and also states no residual for it.
  Its residual is `0` today — `awk '/^## Version History$/{v=1} !v' <design> | grep -cE '^ {4,}(\`{3,}|~{3,})'`
  returns `0`, and `0` over the whole file — so the class needs one added sentence at `$STRIP`
  (bound stated, corpus 0) and the correction above at `census()`, not two fixes.
  quote: docs/02-design/features/doc-block-exec.design.md › `at all and its contents are scanned as prose. The corpus has none of either`

## Should-fix

- The stamp `35698f9` is used in two incompatible senses inside this one revision, and at one site
  the explicit sense names a blob that does not contain the thing being validated. At :2044 the
  tail count is derived as `git show 35698f9:$D` and is *labelled* "the blob this revision edits" —
  correct, and it prints 8 (verified). But at :992 the newly added fourth-blind-form fence says
  `It was checked rather than assumed, at 35698f9`, and that fence does not exist in the
  `35698f9` blob; the same applies to :980 (blind-form re-sweep) and to the unlabelled "The head
  returns `0`". Read in the `git show` sense a reader gets a result about v1.96. Nothing moves —
  I re-ran all of them on the shipped `6f0ee85` file and got `0`, `0`, two `lines …` hits, tail
  `8` — but the ambiguity is the same axis the revision is trying to close. Prescription: adopt
  the phrasing the tail site already reaches for, "on the working file, after the v1.97 entry",
  for every document-self figure, and reserve a bare sha for tree-derived ones.

- `(It was 2 before this revision, when the alternation was written out twice; hoisting it into a
  shell variable is why one copy remains.)` — **unverified**. It describes an intermediate
  drafting state that exists at no commit: the `35698f9` blob carries the old line-scoped check,
  not a twice-written alternation, so there is no sha at which the `2` can be reproduced. Every
  other figure in this revision is re-derivable; this one is a narrative aside dressed as a
  measurement. Prescription: either drop the parenthesis or mark it as a drafting note rather than
  a run.

## Nit

- :1665 says the eight-injection list is `the canonical taxonomy the spec and the impl-plan repeat
  verbatim`. Membership is identical in all three at `6f0ee85` (checked), but impl-plan `:34–36`
  lists them in a different order (`_final_write`, `_close_stream`, `tempfile.mkdtemp`, `os.chmod`,
  `shutil.rmtree`, `os.killpg`, `os.unlink`) from the design's, so "verbatim" overclaims. Harmless
  because the document's own rule is that seams are named and never numbered precisely so that
  reordering is not load-bearing — but the sentence states what a sibling currently says, and both
  siblings were revised in this same commit. "repeat as a set" would be exact.

- The `$STRIP` awk normalises with `sub(/^ +/, "", m)` after `substr($0, RSTART, RLENGTH)`, but
  `RSTART` is already 1 and the match includes the leading spaces, so the `sub` is doing real work
  and is not obvious on a first read; a two-word comment ("drop the indent before comparing runs")
  would spare the next reader deciding whether it is dead.
