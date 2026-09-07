# The second surface-disagreement mechanism — measured, and it is not hollowness

**Date:** 2026-09-07 · **Lane:** `orca/skills` @ `main` · **Corpus:** HemaSuite `#18
gateway-consolidation`, `docs/01-plan/features/gateway-consolidation.*.audit.v*.{agy,codex}.md`
read in place at `feature/18-gateway-consolidation`. Nothing in that lane was edited.

## The question

H6 ("hollow legs are invalid, not clean") shipped, and does not explain the case the
`audit-loop-cycle-count-evidence` brief carried: on impl-plan v1.0 — a fresh document, never
audited, one assembled prompt, one commit — **agy filed `must=0` while codex filed `must=3`, all
`class: build`, with zero overlap**. agy's pass scored `EVIDENCE: PASS tools=41 ok=41 failed=0
thinking=18471`, far above the low-evidence floor, so the hollow-leg instrument would have called
that pass trustworthy.

The brief recorded this as `n=1` and said so. That framing was right about the *confound-removed*
case and wrong about the corpus: **32 paired cycles** exist in that directory, each with an agy and
a codex report against the same prompt. The mechanism is measurable, and this is that measurement.

## The premise reproduces

Verified directly rather than carried. `gateway-consolidation.impl-plan.audit.v1.agy.md` is 11
lines and every section reads `None`; the codex report for the same cycle carries three Must-fix
bullets and the summary "Three build-blocking inconsistencies remain between the implementation
plan, the design, and the current manager implementation." The three musts were acted on — the
revision to v1.1 is what cycle 2 then found the 88-vs-94 contract defect inside — so they were real
findings, not noise.

## What the corpus shows

n = 32 paired cycles (plan and impl-plan), 65 reports.

| measure | agy | codex |
|---|---|---|
| reports | 32 | 33 |
| filed **no** Must-fix | **27 (84 %)** | 4 (12 %) |
| filed nothing at any severity | 18 | 4 |
| mean report size | 1,039 B | 1,776 B |
| refers to a sibling document | 23 (72 %) | 12 (36 %) |
| cites a code file — **all reports** | 5 (16 %) | 18 (55 %) |
| cites a code file — **controlled**, finding bodies only | **4/14 (29 %)** | **18/29 (62 %)** |

**The disagreement is one-directional.** Of 32 paired cycles, 27 disagreed on whether any must
existed. **25 of those 27 are agy-clean-while-codex-files. Two are the reverse.** This is not two
surfaces seeing different things; it is one surface seeing almost nothing.

**The control matters and is stated.** The raw code-citation gap (16 % vs 55 %) is confounded: agy
files nothing in 18 of 32 reports, so it has nothing to cite. Restricting to reports that actually
filed a finding, and scanning only the finding bodies, the gap narrows but survives — **29 % vs
62 %**, about 2.1×.

## The hypothesis I had, and its refutation

The impl-plan v1 agy report has `## Summary` → `None`. A genuine clean audit still says what it
checked, so "schema-valid but content-empty" looked like the signature: it would pass H6's evidence
check *and* its schema check while carrying nothing.

**Refuted by the corpus.** Only **1 of agy's 27 clean passes** has an empty Summary. The impl-plan
v1 report is an outlier on that axis, not an instance of a class. Recorded because a plausible
mechanism that survives one example and dies against thirty-two is exactly what this loop keeps
producing, and the next reader should not re-derive it.

## The mechanism the data supports

**H6 asks whether a leg read *anything*. It does not ask whether the leg read the artifact the
findings must come from.**

Build-class findings on an impl-plan do not live in the impl-plan. They live in the gap between the
plan and the code it plans: codex's three musts were the fallback resolver's bare `PATH` token
against `_resolve_cli()`'s `shutil.which` behaviour, a synchronous `is_cli_available()` inside an
`async def` against the design's bounded off-loop contract, and a RED/GREEN count that miscounts
because a criterion is non-discriminating. Each requires opening the implementation.

A leg that spends 41 tool calls reading *documents* is fully evidenced by H6 — `tools=41 ok=41` —
and structurally unable to reach those findings. And agy is not failing at cross-document reading,
which was the other obvious candidate: it refers to sibling documents **more** than codex does
(72 % vs 36 %). The deficit is specifically code-grounding.

So the instrument gap is precise: **the evidence gate counts tool calls, not their targets.** A
pass that opened only `docs/` and a pass that opened the module under discussion are the same
number today.

## What this does NOT establish

- **One feature, one surface pair.** Everything here is `#18` with agy and codex. It does not
  generalise to other features or other second surfaces without the same measurement.
- **The 41 tool calls were never inspected**, because the transcripts are not retained — no agy
  log survives under the repo or `.h-mad/`. The evidence gate scores a transcript that is then
  discarded, so its own verdict cannot be re-audited later. That is a second, smaller instrument
  gap, and it is why the mechanism above is inferred from report content rather than from what the
  leg actually opened.
- **Whether codex over-files is untested here.** The brief cites a rejections ledger holding 18 agy
  findings against 1 codex; no such ledger exists at `docs/03-analysis/*reject*` in that repo today,
  so that number is uncorroborated and is not used above.
- `cites_a_code_file` is a **regex over report text** — a proxy for grounding, not a measure of
  reading. A leg could read the code and not name a file.

## The check this argues for

Not a new gate yet — one feature is not enough to gate on. The cheap next step is to make the
evidence gate record **what a pass opened**, not just how many calls it made: a per-leg count of
distinct paths read, split by whether they are under the documents directory or under the code the
document plans. That number would separate a genuine clean from a document-only read, and it is the
input any future hypothesis here needs. It also requires retaining the transcript the gate already
scores, which is worth doing on its own.

Until that exists, "two surfaces, union" on an impl-plan is a cost whose benefit is carried almost
entirely by one surface: **25 of 27 disagreements resolved in codex's favour by the revision that
followed.**
