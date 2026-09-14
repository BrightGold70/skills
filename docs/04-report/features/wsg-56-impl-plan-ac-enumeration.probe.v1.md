# #56 — the eleven impl-plan rows naming a different AC

**Date:** 2026-09-14
**Feature:** `wsg-56-impl-plan-ac-enumeration` (claimed, skills:docs/.bkit-memory.json)
**Brief:** `docs/handoffs/2026-09-14-main__wsg-56-impl-plan-ac-enumeration.md` (`da63499`)
**Supersedes as evidence:** `docs/04-report/features/wsg7-carried-claims.probe.v1.md` §8 (`c21e63e`), whose `CANNOT PROBE` verdict this report retires.

## Verdict

**The claim is TRUE, and it did not need re-deriving. The enumeration EXISTS.**

The brief's central premise — *"The eleven rows were never enumerated in any of the four handoffs
that carried the row, in the WSG audit reports, or anywhere in either repo… neither lane holds the
list. #56 is not a lookup — it is a re-derivation"* — is **FALSE**.

The census is in the impl-plan itself, at
`website-source-grounding.impl-plan.md:6643`, inside the **v1.12 Version History entry**, item (5).
That entry is a single **8485-character line**. It is not in a section, not under a heading, and not
findable by any of the searches either lane ran, which is why two lanes and one prior probe all
concluded it did not exist.

It says, verbatim:

> ELEVEN further rows cite an AC whose criterion is a different property, including two clean SWAPS
> (`ac_2_2` carries AC-2.3's subject while `ac_2_3` carries AC-2.2's; `ac_3_1` carries AC-2.1's
> set-equality subject while an `ac_2_1` row carries an `admitted_registry_ref` property AC-2.1 does
> not state). SIX of those eleven are ALREADY SHIPPED as test functions in committed code […] so
> re-spelling them in this document would desynchronise it from the tree and would need a code
> rename this author may not make. Rows 5 and 7 are unshipped, which is why they are the two that
> move.

Both figures in the carried claim — **eleven**, and **six already shipped** — are confirmed at their
origin, not reconstructed.

## The rows — 8 of 11 named, with provenance

Located in the impl-plan by node id. "SHIPPED" is the census's own classification.

| # | task | row | prefix | node id | why it mismatches | shipped |
|---|---|---|---|---|---|---|
| 1 | Task 1 | 1 | `AC-3.1` | `test_ac_3_1_admitted_classes_set_equality_per_setting` | carries **AC-2.1's** set-equality subject | yes |
| 2 | Task 1 | 2 | `AC-3.1` | `test_ac_3_1_monotonicity_as_set_containment` | same prefix class | yes |
| 3 | Task 1 | 9 | `AC-2.1` | `test_ac_2_1_admitted_registry_ref_admits_none_under_both_settings` | asserts an `admitted_registry_ref` property **AC-2.1 does not state** | yes |
| 4 | Task 3 | 3 | `AC-9.3` | `test_ac_9_3_fixture_mtimes_are_set_explicitly_not_inherited_from_checkout` | named by the census | yes |
| 5 | Task 12 | 6 | `AC-1.4` | `test_ac_1_4_korean_negative_resolves_to_no` | named by the census | yes |
| 6 | Task 12 | 7 | `AC-1.5` | `test_ac_1_5_strike_through_and_colour_residual_pins_to_yes` | named by the census | yes |
| 7 | Task 14 | 20 | `AC-2.2` | `test_ac_2_2_quorum_enforcing_site_and_claim_like_predicate_are_unmoved_by_the_flag` | **SWAP** — carries AC-2.3's subject | no |
| 8 | Task 14 | 21 | `AC-2.3` | `test_ac_2_3_resolve_quorum_is_zero_point_eight_with_the_environment_unset` | **SWAP** — carries AC-2.2's subject | no |

**Rows 1–6 are the census's "SIX already shipped", recovered by name.** Rows 7–8 are the two clean
swaps, recovered from the swap description and confirmed present at those node ids.

**Three rows remain unnamed.** The census states the count (eleven) but enumerates only the six
shipped ones plus the swap pairs; item (5) says the full list *"IS IN THE REVISION REPORT, NOT FIXED
IN PLACE"*. **That revision report is in neither repo** — searched across
`HemaSuite/hematology-paper-writer/docs` and `skills/docs`; the six node ids appear in exactly one
file, the impl-plan. So the last three are the only part of #56 that is genuinely a re-derivation.

## The residue — FOUR found where the census implies three (2026-09-14)

The census names eight of eleven, so three were expected. **Four rows classify as mismatches on a
full reading of the AC text**, which makes the measured total **twelve**, not eleven. Per the brief's
own instruction — *"If the true count is not eleven, that is a finding worth filing — report the
number you measured and the rows behind it, rather than forcing the figure"* — it is reported as
twelve rather than trimmed to fit.

| # | task | row | prefix | the AC's actual criterion | what the row asserts |
|---|---|---|---|---|---|
| 9 | Task 5 | 4 | `AC-5.3` | a committed fixture manifest, byte-copy of the live `MANIFEST.yaml`, loads and validates after the schema bump | `effective_from` equals `retrieved_on`; `effective_to` is `None`, passed explicitly |
| 10 | Task 6 | 8 | `AC-7.6` | **exactly one** outcome line per call, asserted `== 1` | two ingests in one run with different `strict` values do not share a cache entry |
| 11 | Task 13 | 2 | `AC-1.6` | the resolved value round-trips synopsis → registry → `EngineConfig`, as caller-side propagation | dataclass **field order**, read from the dataclass at test time |
| 12 | Task 14 | 17 | `AC-2.1` | set equality over all five admitted class names | the AXIS-1 grounding gate, `Yes` arm |

None is a near-miss: in each case the AC's criterion and the row's subject are about different
objects entirely — manifest loading vs row field values, line cardinality vs cache-key identity,
value propagation vs declaration order, class-set equality vs a grounding outcome.

### Method, and its calibration

A token-overlap screen ranked all 177 prefixed rows by how much of each row's vocabulary its own
prefix AC's spec text shares. **Calibrated against the eight already known** before being trusted:
all eight rank within **61 of 177** (median 44, best 1). Rows 1–70 were then read by hand against
the AC text. The screen is a NARROWING device only — every one of the four above was decided by
reading, which is the distinction the brief drew when it warned that the prefix-vs-test-name proxy
"measures a different property".

The AC extraction was verified against the raw spec before any row was judged (`grep -n '^  - AC-'`,
97 definitions, four spot-checked verbatim) — a misaligned extractor would have produced confident
nonsense at every row.

### Still open: borderline rows, not counted above

Four rows are arguable and are deliberately **not** included in the twelve, because each could be
read as the AC's positive control rather than a different property. They need a second opinion:

- Task 13 r6 and Task 14 r24, both `AC-5.8` — the AC pins that ingest is reached from *every* call
  site; the rows pin that the `strict` argument *at* each site is a `current_source_policy` read.
- Task 4 r3, `AC-9.1` — the AC rejects `..` before any filesystem call; the row asserts a valid
  multi-segment relative path is *accepted*.
- Task 15 r9, `AC-10.1` — the AC pins that `RunReport` gains two populated fields; the row asserts
  an unbound read equals `resolve_strict_grounding(None, _ABSENT)`.

Rows 71–177 were not read AT THE TIME OF WRITING. **They were read on 2026-09-14 — see §"ROWS 71–177 WERE READ" below.** The calibration bounds the risk rather than removing it: the known eight
all fell inside the range that was read, so an unread mismatch below rank 70 is possible but would
be the first of its kind in this corpus.

### SECOND OPINION RETURNED 2026-09-14 — the borderline framing was WRONG for three of four

The four rows above were parked on the hypothesis that *"each could be read as the AC's positive
control rather than a different property."* Three fresh readers were dispatched, one per AC, and
**that hypothesis holds for exactly one of the four.**

**How the contamination was avoided, because it is the only reason these answers are worth
anything.** Each reader received the criterion verbatim with its `path:line`, the row verbatim, and
nothing else. None was told a prior reading existed, none saw the words *positive control*,
*mismatch*, *borderline*, *eleven* or *twelve*, and each was explicitly forbidden to open anything
under `docs/` in this repo — where this document, the brief, and four handoffs all carry the
leaning. They were asked two counterfactual questions instead of being handed the categories:
*could the criterion hold while the row is false*, and *could the row hold while the criterion is
violated*. Both-yes is a different property; only-Q2-no is narrower. The classification is an
output of that structure, not a category anyone supplied.

| task | row | prefix | verdict | why |
|---|---|---|---|---|
| Task 13 | 6 | `AC-5.8` | **DIFFERENT** | AC-5.8's predicate is *reachability* — "ingest is **reached** from **every** call site". The row's predicate is the AST **shape of one keyword argument**. The AC's text never mentions `strict`. |
| Task 14 | 24 | `AC-5.8` | **DIFFERENT** | Different module, different function, different callee, and **no site enumeration at all**. |
| Task 4 | 3 | `AC-9.1` | **GUARD** | It does not assert AC-9.1, but its absence would let a predicate that rejects *everything* satisfy AC-9.1's own tests. |
| Task 15 | 9 | `AC-10.1` | **DIFFERENT** | AC-10.1's subject is `RunReport`'s two fields being populated on every run; the row's subject is the *resolver's* unbound-read return value. |

**Both AC-5.8 rows are decided by counterexamples in BOTH directions**, which is what rules out
`NARROWER` as well as `SAME`:

- *AC holds, row false*: all four `_seed_guidelines_once` sites reach `ingest_corpus` exactly as
  today, but each is written `strict=True`. AC-5.8 is fully satisfied; the row fails at all four.
- *Row holds, AC violated*: at one site the `ingest_corpus(..., strict=current_source_policy().strict)`
  call sits behind an early `return` or a dead guard. The AST still sees the `Call` node with the
  pinned shape, so the row passes everywhere — and ingest is never reached from that site.

The reader verified the sites in code rather than arguing from the text: four
`_seed_guidelines_once` sites at `_ko_notebooks.py:114,247,350,436`, each with an adjacent
`ingest_corpus` at `:123,254,359,443`; Row 24's target is `admitted_registry_ref:818`, inside
`_seed_guideline_sources`, **downstream of the very set AC-5.8 quantifies over**.

**Row 24's own text names its real source**, which is the sharpest evidence in the whole exchange:
*"design v1.10's 'Structural, registry wire' bullet"* and the design's *"at BOTH wires"*
requirement. It inherits `ac_5_8` **from Task 13's row 6, not from the AC** — a label propagating
sideways between siblings rather than upward from a criterion. That is a distinct defect mechanism
from the swaps and the subject-drift already recorded here, and it is worth naming because a census
that looks only at prefix-vs-AC cannot see the direction the label travelled.

**Task 4 row 3 is the one the parked framing got right, and `GUARD` is not a euphemism for
mismatch.** The row's own subject column says it: *"the positive control — without it, a predicate
that rejects everything passes tests 1 and 2."* Its `ac_9_1` label is defensible precisely because
the test exists to keep AC-9.1's other tests non-vacuous; stripping the prefix would orphan it from
the criterion it protects.

**Consequence for the count: the measured total moves from twelve to fifteen**, and the three that
move are *not* the three the census left unnamed — those remain unnamed. The count is reported,
not reconciled to any prior figure, on the same instruction that produced twelve rather than eleven.

**One caution about `GUARD`, raised by an unrelated reader in the same round.** A separate pass over
the wider corpus classified **Task 15 row 2** as a `GUARD` against this same `AC-10.1`, on the
ground that a collector↔emitter correspondence can hold while both fields are `None`. That is a
different row from row 9 and does not touch its verdict — but it means `AC-10.1` now carries one
row that asserts a different property (row 9) *and* one that guards it (row 2). A count that
recorded only "two `ac_10_1` rows look wrong" would collapse two different situations, and only one
of them is a defect.

## ROWS 71–177 WERE READ, 2026-09-14 — and the tail was as safe as the calibration promised

The open item said the enumeration was bounded, not exhaustive, because rows 71–177 had not been
read. **They have now been read — and so has every other row.** All 173 prefixed rows outside the
four borderline ones were judged by seven independent readers, each given only a verbatim criterion
and a verbatim row, each forbidden to open this repo's `docs/`, none told what any other found.

### The instrument first: three properties, none of them assumed

**1. The corpus reproduces, and one published figure does not.** 97 AC definitions and **177**
prefixed rows both reproduce exactly. The row total does **not**: this document says *"202 test rows
extracted as `| N | test_… | subject |`"*, and the real count is **200**. 202 is
`grep -c 'AC-[0-9]\+\.[0-9]\+'` over the impl-plan — the **line** count of AC references. That is the
same figure §"Method, and two instruments that failed" already flags as mislabelled *in the brief*,
reused one section later as this document's own row total. The number was borrowed, not measured.
Nothing downstream depends on it — 177, the load-bearing figure, is independently correct.

**2. Calibration: 12 of 12, not 8 of 8.** Every previously-known mismatch was planted blind in the
batches. All twelve came back `DIFFERENT`, at ranks **2–58** — inside the 1–70 band the earlier pass
read, which reproduces the original calibration claim and extends it from eight rows to twelve.

**3. A negative control nobody had to build.** Batches were cut in ascending token-overlap order, so
each reader saw a band and no reader knew which. The `DIFFERENT` density came back **monotonic in
overlap**:

| batch | mean overlap | DIFFERENT | n |
|---|---|---|---|
| 1 | 0.070 | **19** | 25 |
| 2 | 0.198 | 7 | 25 |
| 3 | 0.397 | 5 | 25 |
| 4 | 0.550 | 1 | 25 |
| 5 | 0.667 | 0 | 25 |
| 6 | 0.779 | 1 | 25 |
| 7 | 0.905 | 0 | 23 |

This matters more than the calibration does. A reader pool with a uniform bias toward `DIFFERENT`
would produce a **flat** row, and the top two bands returned **0 of 48** between them. The gradient
is therefore evidence about the corpus rather than about the readers, and it validates the
token-overlap screen far more strongly than "the knowns rank inside 61" ever could — that claim is
consistent with a screen that merely fails to be anti-correlated.

### The answer to the question that was actually open

**33 rows were called `DIFFERENT` in total. Exactly 2 of them sit at rank > 70.**

They are **Task 1 row 7** (rank 136) and **Task 1 row 8** (rank 99) — and they were found by two
different readers, in two different batches, with the same stated mechanism: the row drives
`admit(None, …)`, the **unresolved** population, while the criterion's population is explicitly a
**resolved** class for which `admit` is False, asserted on the union. One defect mechanism, two
adjacent rows, corroborated across readers who never saw each other's work.

So the unread tail held **2 findings in 107 rows**, against **31 in the 70 rows already read**. The
earlier pass's judgement that the risk was *bounded but not removed* is confirmed in both
directions: something was there, and it was the first of its kind, exactly as predicted.

### The part that is NOT settled, and is not counted here

The remaining **19** new `DIFFERENT` calls fall at ranks 1–62 — **inside the band the earlier pass
read and judged.** That is not newly-explored territory; it is two reads of the same rows
disagreeing, and the disagreement is large. It is recorded as an open question rather than folded
into any total, because a count published from one lane's reading is the thing this whole document
exists to be sceptical of. A blinded adjudication set — the new calls, the knowns as positive
controls, and rows a different reader called `SAME` as negative controls — is the instrument for
deciding it, and until it returns **the measured total stands at fifteen**.

One reader flagged its own divergence axis unprompted, which is the most useful line in the round:
rows 1.14 / 1.20 / 1.21 / 1.22 are *fallback-acceptance* rows sitting under a *rejection* criterion,
and it called them `DIFFERENT` while noting that a reader weighing "vacuity control" more heavily
would call them `GUARD`. That is a real definitional seam, not a mistake, and it accounts for four
of the nineteen on its own.

### ADJUDICATION RETURNED — the new calls mostly do NOT survive, and the reason is precise

Nine of the new calls were put to two further readers inside a **blinded** 22-pair set: the 9 new
calls, the 4 knowns as **positive** controls, and 9 rows a different reader had called `SAME` as
**negative** controls, shuffled, with no indication which was which.

| control | adj-1 | adj-2 |
|---|---|---|
| negative (rows called `SAME`) | **9/9 `SAME`** | **9/9 `SAME`** |
| positive (known mismatches) | 3/4 | **4/4** |

**Eighteen of eighteen negative controls came back `SAME`.** Whatever else is true, these readers do
not call `DIFFERENT` indiscriminately — which is what the nineteen in-band calls had to be tested
against, and the test exonerates the *method* while convicting most of the *calls*.

Of the nine new calls: **2 unanimously `DIFFERENT`, 5 unanimously not, 2 split.**

| row | adj-1 | adj-2 | |
|---|---|---|---|
| **T1 r7** | DIFFERENT | DIFFERENT | **CONFIRMED** |
| **T6 r10** | DIFFERENT | DIFFERENT | **CONFIRMED** |
| T6 r29 | GUARD | DIFFERENT | split |
| T5 r3 | DIFFERENT | GUARD | split |
| T8 r7 | GUARD | GUARD | refuted |
| T9 r7 | GUARD | GUARD | refuted |
| T6 r9 | NARROWER | NARROWER | refuted |
| T14 r15 | NARROWER | NARROWER | refuted |
| T14 r16 | NARROWER | NARROWER | refuted |

So the batch readers were **not** over-calling `SAME` rows as `DIFFERENT` — they were over-calling
`GUARD` and `NARROWER` rows as `DIFFERENT`. **The variance lives entirely at the
`DIFFERENT`/`GUARD`/`NARROWER` boundary, and not at all at the `SAME` boundary.** That is the same
seam the batch-1 reader named on its own, and it is a property of the question, not of any reader:
deciding whether a row *asserts a different property* or *guards the criterion's other tests*
requires knowing why the row was written, and the row text does not always say.

**`T1 r7` is the load-bearing result.** It sits at rank **136**, deep in the tail that had never been
read, and it is now confirmed by **three independent readers** — the batch-6 reader that first
flagged it and both adjudicators. Its sibling `T1 r8` (rank 99) was found separately by a fourth
reader with the same mechanism but arrived after the adjudication set was built, so it is
corroborated-but-unadjudicated. **Reading rows 71–177 found a real mismatch, and the pair it belongs
to is the first of its kind in this corpus — exactly the outcome the earlier pass called possible.**

### The single most instructive error in the round, and it is the adjudicator's

adj-1's one miss was **T14 r20**, a row the census itself names as a clean SWAP. It called it `SAME`,
reasoning: *"Both: quorum value unmoved by the flag, driven under both settings."* Read the two
criteria:

- **AC-2.2** — `HEMASUITE_NLM_QUORUM` resolves to the same value under both settings, and is `0.8`
  with the environment unset.
- **AC-2.3** — `enforcing_site`, `is_claim_like`, `CLAIM_LIKE_VOCABULARY`, `CLAIM_LIKE_MIN_CHARS` are
  not read by and do not change with the flag.

The row is `test_ac_2_2_quorum_enforcing_site_and_claim_like_predicate_are_unmoved_by_the_flag`. What
it asserts is **AC-2.3's** property. It carries `ac_2_2`. The census is right and adj-1 is wrong —
and **the word that misled it is `quorum`, which appears in the row name only because
`enforcing_site` lives in the `tools.grounding_quorum` module.** A module-path token, not a subject.

That is worth more than the verdict it got wrong. The reader failed by **lexical overlap with the
wrong AC** — which is the precise mechanism the token-overlap screen is built on, and plausibly the
mechanism that produced the original mislabelling in the first place. adj-2, reading the same pair,
got it right, so this is per-reader error and not a systematic bias. **The corollary is the one that
should govern how this document is used: no single reader is authoritative on a lexically-confusable
row, mine included, and the errors run in BOTH directions.** The five refuted calls may therefore
contain genuine mismatches that two conservative readers downgraded, which is why the confirmed
count is stated as a **floor**.

### Where the count actually stands

**Seventeen confirmed** — the twelve published, plus the three borderline rows resolved above, plus
`T1 r7` and `T6 r10`. Not counted, and listed so nobody has to re-derive them: 2 split, 5 refuted,
`T1 r8` corroborated-but-unadjudicated, and **12 further new calls never put to adjudication at
all**. The floor is seventeen; the ceiling is not established by this document.

## Two adjacent rows, already FIXED — not part of the eleven

Task 13 rows 5 and 7 carried `ac_10_9` prefixes for properties `AC-10.9` does not state. They were
re-spelled onto `test_d_11b_…` and `test_d_11a_…` at impl-plan v1.12. The census calls the eleven
*"further"* rows, i.e. beyond these two. Spec §Contradictions **Item 17** is where the defect was
first ruled on, and it declines to enumerate by row in so many words: *"the same mismatch applies to
it and is not separately enumerated, because the axis is the prefix and not the row."*

## Method, and two instruments that failed

- **Row grammar.** 202 test rows extracted as `| N | test_… | subject |`; 177 carry a parseable
  `ac_X_Y` prefix. The impl-plan's own `grep -n '^  - AC-'` (L114) does **not** match this document —
  it describes the **spec's** AC-definition grammar at `daed4229`, and returns 0 here.
- **The brief's warned-against proxy was not used.** Prefix-vs-test-name measures a different
  property than prefix-vs-AC-semantics.
- **A structural narrowing was tried and FAILED, and the failure is informative.** Flagging rows
  whose prefix AC is absent from their own task's declared `**ACs**:` line returns **0 of 177**.
  Every mismatched row sits in a task that *declares* the AC it mis-cites, so the defect is invisible
  at task level. This is independent confirmation that no cheap screen exists — the remaining three
  need each row read against the spec's AC text.
- **A count in the brief is mislabelled.** It states *"202 `AC-x.y` occurrences"*. 202 is the
  `grep -c` **line** count; occurrences are **341** (`grep -o … | wc -l`). Its own reproduce command
  is `grep -c`, so the number is right and the label is wrong.

## Closure — CLOSED 2026-09-14 by operator decision

**#56 is closed.** The row asked for the eleven rows to be enumerated on the premise that no
enumeration existed. That premise is false, so the task as framed is moot: the census was recovered
rather than re-derived, and its two load-bearing figures — **eleven**, and **six already shipped** —
are confirmed at their origin.

**The residue is TRACKED SEPARATELY, not absorbed.** Three of the eleven are named nowhere,
*including at the origin*: the v1.12 author counted eleven and enumerated eight, deferring the rest
to a "revision report" that was never written into either repo. Those three are not work this lane
declined — they were never recorded by anyone.

Closing #56 retires the framing (*"re-derive an enumeration that exists nowhere"*), which was false.
It does **not** retire the residue, which is carried as its own item rather than inherited silently
inside a closed row — the failure mode this whole row is an instance of. Whoever takes it starts
from §Method below: the row grammar, the confirmed count, the eight already named, and the measured
fact that no mechanical screen narrows what is left.

## What was owed, at the time of writing

1. The remaining **three** rows, by reading each of the 169 not-yet-classified prefixed rows against
   the spec's AC text. No mechanical screen narrows this further — measured above.
2. Nothing else. The count and the shipped-six are settled at their origin and should not be
   re-derived again.

## Why this was missed three times

The census sits inside a Version History bullet, which is prose in a section every document-level
search treats as a changelog rather than as content. `handoff`'s own `pending-handovers` scan
deliberately reads only a document's **header** block for the same reason. A finding filed into a
changelog line is durable but unfindable; the lesson generalises past this row.
