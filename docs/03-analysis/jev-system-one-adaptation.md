# Jev (TypeSafe System One) — fit against `handoff` and `h-mad`

Investigated 2026-09-21. Source: eigent.ai blog post + primary docs
(`docs.typesafe.ai/concepts/system-one`, `/concepts/state`, `/models`,
`/introduction/quickstart`). Nothing below has been run against the live API —
no key has been obtained. Every measurement of this repo is reproduced with the
command that produced it.

## What Jev actually is

A decision model, not a text model. One `POST https://api.typesafe.ai/v1/systemone`
carries a `state` (string / JSON object / array of text) plus N named questions,
and returns typed answers with per-option probabilities and a `confidence` field.
Three question types, and only three:

| Primitive | Shape | Returns |
| --- | --- | --- |
| `choice` | one option from a named set (≤255) | chosen option, probability per option, confidence |
| `score` | a 2–10 level scale described in words | a float that may land between levels (`1.4`) |
| `noul` | a yes/no criterion | probability of yes, 0–1 |

Hard constraints from `/models` (`jev-1.13.0`):

- **64k tokens per request; 32k for `state` plus the single longest question.**
- $0.042 per Mtok input, output free. Rate limits 250k tok/s, 1200 req/min,
  explicitly "adjusting dynamically… can change without notice".
- Text only. English-primary; **CJK accepted with lower accuracy** (`/models#language-support`).
- A self-serve key page is documented (`console.typesafe.ai/keys`) and the endpoint is
  public; **access on signup is not confirmed** — `/models` says limits move "as
  upcoming large GPU deals land and we let in more users".
- Accuracy is documented to shift as `state` grows (`/model-jaggedness/jev-1.13`).

Two limits decide most of what follows:

1. **No world knowledge, no retrieval.** Jev sees only the state handed to it.
   It cannot read the working tree.
2. **Calibration is a group property.** TypeSafe states plainly that calibration
   holds across many predictions and does not make any single answer correct.

## The load-bearing conclusion

**Jev cannot hold any leg that gates in h-mad**, and this is not a matter of
tuning. Every gating verdict in h-mad is *defined* as a verdict about the tree:

- `agents/doc-auditor.md:28` — "a clean verdict from you is worth nothing unless
  you read"; `:45` — "read the tree before you write a finding".
- Phase 6a-prime exists because a review that read nothing returned
  `ASSESSMENT: READY_TO_MERGE` in 1510 fluent bytes and rc, the extractor and the
  Phase-7 gate all took it (`h-mad/SKILL.md` §6a-prime). The fix was
  `h_mad_review_evidence.py` counting tool calls that reached `DONE` — an
  *evidence* gate, not a better judgment.

A model that structurally cannot read is the 1510-byte defect with a schema
around it. The typed envelope makes the wrong answer *parse*; it does not make
it *right*. That is the exact failure this repo has already paid for repeatedly
(`feedback_presence_is_not_measurement`, `feedback_wire_can_overclaim_its_callee`).

Second structural fact: the 6a-prime archreview prompt runs ~740 KB
(`h-mad/SKILL.md:974`, #153) ≈ 185k tokens against Jev's **32k** state cap — it
does not fit by ~6×. Doc-audit prompts have not been sized here, but they inline
the phase documents plus the invariants rubric, so the same order applies. Any
Jev use in h-mad is per-finding, not per-audit.

Third: the volume argument does not apply. Jev's economics are built for
millions of decisions/day at 70–500 ms. An h-mad round is ~95 min and produces
on the order of two findings per audit report. Latency and $0.042/Mtok are
irrelevant at this scale — **whatever is worth adopting is worth adopting for
calibration, never for cost or speed.**

## What h-mad already does that Jev sells

This is the notable finding. h-mad's verdict discipline is already Jev's design
philosophy, implemented deterministically and offline:

- Closed enumerated verdict tokens: `INSTALL:`, `PRECONDITION:`, `BASELINE:`,
  `INTEGRATE:`, `GATE:`, `PHASE7:`.
- "Read the token, never `$?`" — every verdict exits 0 by design.
- A `cannot_judge` / `UNREADABLE` / `NO_EVIDENCE` third state that is *neither*
  pass nor fail (`handoff/SKILL.md:573`, `h-mad/SKILL.md:99`).
- A deliberately **closed** token list, because a catch-all bullet is fail-open
  (`handoff/SKILL.md:589`).

Jev would add one thing these do not have: a **calibrated probability attached
to a judgment call**. Everything else it markets, this repo already has, in a
form that needs no network and no vendor.

## Per-site fit table

| Site | Question shape | Input fully in-hand as text? | Volume | Fit |
| --- | --- | --- | --- | --- |
| `handoff` LEARN categorisation (`handoff/SKILL.md:1039-1043`, `scripts/learn.py:21-25`) | `choice(gotcha\|solution\|pattern\|other)` | **Yes** — the pattern text is the whole input | 1,676 rows, all carrying a category | **Best fit.** Backtestable today. |
| `handoff` LEARN confidence | `score` over the four levels | Yes | 1,440 rows carry a confidence, but 97% are 0.7 or 0.9 | Weak — effectively a two-level scale; see below. |
| doc-auditor 7b finding class (`agents/doc-auditor.md:137-148`) | `choice(build\|measurement)` | Yes — the finding text is the input | 322 tagged findings (deduped), 513 `class: build` + 152 `class: measurement` raw | Marginal — real labels, imbalanced, and the auditor emits it for free. |
| Audit finding *validity* (real vs rejected) | `noul` | **No** — validity is a fact about the tree | ~71 rejection-ledger entries | **No fit.** The one decision that would pay is the one Jev structurally cannot make. |
| 6a-prime `YES/WITH_FIXES/NO` | `choice` | No — verdict about a diff + tree | — | **No fit**, same reason. |
| `handoff` TAKEOVER queue triage | `choice` over briefs | No — a brief's premises must be re-run | — | **No fit**, and `handoff/SKILL.md` explicitly forbids bulk-stamping briefs that were not checked. Jev *is* bulk-stamping. |
| `h_mad_extract_verdict` | — | — | — | **No.** Replacing a deterministic extractor with a probabilistic model is backwards; the failure it guards (fluent-nothing) is caught by counting tool calls, which Jev cannot do. |

### Measurements behind that table

```bash
# audit reports, excluding graft/ mirrors, .omc/, node_modules, .git
find ~/orca \( -path '*/graft/*' -o -path '*/.omc/*' -o -path '*/node_modules/*' \
  -o -path '*/.git/*' \) -prune -o -type f -name '*.md' -print \
  | grep -E '\.audit\.' | wc -l                       # 9992 files, 294 features
#   9852 "## Must-fix"  /  9849 "## Should-fix"  /  ~20797 bullet lines total
#   225 "GATE: FAIL"  /  159 "GATE: PASS"
#   513 "class: build"  /  152 "class: measurement"  (raw, clones not deduped)
#   deduped by report basename: 3713 reports, 5986 findings, 322 tagged (5.4%)
#   tagging concentrates in 7 of 198 features — the rule shipped 2026-09-06 (f2b3d74),
#   and features audited since tag at ~100% (124/124, 72/72, 41/41, 21/21).
#   The 5.4% is adoption over time, NOT non-compliance.

# LEARN corpus (one row per learning), the two distinct files
grep -cE '^- [0-9]{4}-' ~/orca/HemaSuite/docs/learnings.md   # 1219 rows, 983 with [confidence]
grep -cE '^- [0-9]{4}-' ~/orca/skills/docs/learnings.md      #  457 rows, 457 with [confidence]
# confidence distribution over both: 0.3 x1 | 0.5 x48 | 0.7 x819 | 0.9 x572
# legacy rows without [confidence] are preserved as-is (learn.py:40-41) and carry no label
grep -c '[가-힣]' <either file>                               # 0 — corpus is English

# rejection ledgers (negative labels), deduped across the three HemaSuite clones
find ~/orca -name '*.rejections.md' -not -path '*/graft/*'   # ~71 unique entries
```

Note the clone hazard: `HemaSuite`, `HemaSuite-wsg` and
`workspaces/HemaSuite/agent-backend-routing` each carry a copy of the same
ledgers and `learnings.md`. Counting without deduping inflates every figure ~3×.

## Recommendation

**Do not wire Jev into the h-mad gating spine. Do not adopt it for cost.**

Two things are worth doing, in order:

1. **Adopt confidence-gated routing at the one site that already has a
   probability — for free.** Jev's portable idea is a threshold *per action*,
   scaled to what being wrong costs, with escalate as a third route rather than a
   binary. h-mad's deterministic gates emit no probability, so there is nothing
   there to threshold — the idea does not transfer to them, and claiming it does
   would be adopting a pattern with nothing to apply it to. `learn.py`'s
   confidence field is the only probability axis in either skill. Concretely:
   LEARN entries below 0.5 are never auto-persisted and are always surfaced for
   confirmation; 0.9 persists silently. That is one rule in one file and needs no
   API call. Note the corpus says the axis is barely used — 97% of labelled rows
   sit at 0.7 or 0.9, and 0.3 appears once in 1,440 rows — so the first question
   is whether the four levels discriminate at all.

2. **One measured tracer bullet, if and only if a key is obtained: handoff
   LEARN.** It is the only site whose full input is already in-hand text, and it
   is the only one with a labelled corpus large enough to *measure* calibration
   rather than take the vendor's word for it. Procedure:
   - Sample ~200 rows from the 1,676 `learnings.md` entries across the two
     distinct files (`HemaSuite` and `skills`; `HemaSuite-wsg` and
     `workspaces/HemaSuite/agent-backend-routing` are clones of the first).
     Cost is negligible — ~200 rows x ~100 tokens ~ $0.001 — so a key is the only
     real gate.
   - State = the pattern text. Questions =
     `choice(gotcha|solution|pattern|other)` + `score` over the four confidence
     levels, described in the words of `learn.py:21-25`.
   - Compare against the recorded label. Report agreement on category, and
     reliability of the score against the recorded confidence.
   - Decide on the number. A tracer bullet that runs is worth more than this
     whole document.

   Two biases to declare up front: existing confidences were assigned by
   hand-rules, so agreement measures agreement-with-the-rules, not correctness;
   and with 97% of the labels at 0.7/0.9 a score backtest is near-degenerate —
   run the `choice` half first and treat the `score` half as secondary.

**Owed, not done:** no live call has been made, so every performance claim here
is TypeSafe's own, and the LEARN backtest is unrun. Do not cite this document as
evidence that Jev works or does not work — only as evidence about where it could
and could not be placed.
