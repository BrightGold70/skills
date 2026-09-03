# hmad-audit-evidence-gate — corpus measurement (2026-09-03)

**Feature:** `hmad-audit-evidence-gate` (task #26; Handover-From HemaSuite `f0b69d8d`)
**Measured by:** session `b66afa9c` · repo `/Users/kimhawk/orca/skills` · branch `main`
**Verdict:** **the brief's Next Step 2 (evidence check in the gate) is NOT shippable on this
evidence.** Its premise — "a quote check would have caught every fabrication, mechanically" — is
falsified by re-measurement. Next Steps 1 and 3 stand and are unaffected.

## What was measured

The labelled corpus is HemaSuite `#18 gateway-consolidation` design audit cycles 45–77, both
surfaces:

- **Evidence source (haystack):** the assembled prompts — the exact bytes each surface read.
  Copied out of the sender's non-durable scratchpad to
  `~/.h-mad-corpora/evidence-gate/prompts/` (64 files, c45–c76, byte-compared against source).
- **Findings source:** the collected reports, durable at
  `…/HemaSuite/hematology-paper-writer/docs/02-design/features/gateway-consolidation.design.audit.v{45..77}.{agy,codex}.md`.
  Must-fix bullets extracted through the gate's **own** machinery (`h_mad_audit_gate.classify`
  section walk, `_bullet_remainder`, `_is_none_sentinel`), not a hand-rolled parser.
- **Labels:** `gateway-consolidation.design.md` Version History, which records each cycle's
  rejections. Used as the **label** source only — never as the evidence haystack (see the trap
  below).

Counts re-derived, not carried: **37 must-fix bullets over 31 reports — agy 12, codex 25.**
Codex's 25 matches the brief exactly. agy's 12 vs the brief's 11 is **c76, one cycle outside the
brief's c45–75 window** — settled, not a double-count. The 12 keys are c48, c55, c58, c60, c62,
c64×2, c69×2, c72, c74, c76. Six are labelled rejected: c62[0], c64[0], c64[1], c69[1], c72[0],
c74[0].

## Result 1 — no occurrence rule discriminates

Rule shape: *a must-fix bullet with ≥1 absent span of class X scores `INVALID`.*

| span class | catches fabrications | kills real findings |
|---|---|---|
| `path:line` | 1 / 6 | 0 / 31 |
| prose-quote (double-quoted ≥12 chars) | 2 / 6 | 9 / 31 |
| code-span (backtick) | 3 / 6 | 8 / 31 |
| elided (contains `...` / `…`) | 0 / 6 | 9 / 31 |

| combined rule | catches | kills |
|---|---|---|
| `path:line` only | 1 / 6 | 0 / 31 |
| `path:line` + prose-quote | 2 / 6 | 9 / 31 |
| every class except elided | **4 / 6** | **13 / 31** |
| zero spans present in the document at all | 1 / 6 | 2 / 31 |

**43% of real must-fixes carry an absent backtick span.** The brief itself sets the acceptance
bar — "a change that invalidates any real finding is worse than the defect" — and every rule that
catches more than one fabrication clears that bar by a wide margin.

**Two fabrications are invisible to any occurrence check.** c62 quotes *nothing* (0 spans); c72's
three spans are all present — it paraphrases the claim it invents rather than quoting it.

## Result 2 — the one zero-cost rule is vacuous

`path:line` scores 1 catch / 0 kills, but **0 of 31 real must-fix bullets carry a `path:line` span
at all.** The zero-kill is untested, not safe. (Memory: prove a surface can produce a non-zero
before reading its null as absence.)

Scored against `design.md` — the file the gate would actually hold as `--gated` — the same rule
catches **0 / 6**, because recording each rejection wrote the fabricated `tools/nlm_cli.py:186`
into the design's Version History. This reproduces the brief's own documented trap exactly. It does
**not** bite in the live loop (the gate runs before the rejection is recorded), but it means this
corpus cannot validate a gated-file-scoped check at all.

## Result 3 — why the check cannot work under the current contract

The contract does not distinguish *quoting the document* from *proposing a fix* or *reporting a
command that was run*. Absent spans in **real** codex findings are overwhelmingly:

- proposed code — c69's real bullet's absent span is its own suggested regex `(?:-[0-9a-f]{4}){3}`;
- constructed test inputs — `{"sources": null}`, `-> list[dict]`;
- commands the reviewer ran — `git log -1 -G ...`, `git show "$A^:cli/_preflight.py" … | grep -c …`;
- stdlib/tree symbols the prompt never carried — `BaseSubprocessTransport.close()`.

All four are legitimate. A span-occurrence check cannot separate them from a fabricated citation
because nothing in the report marks which spans are *claims about the gated document*. This is a
contract defect, not a threshold to tune.

**Consequence for sequencing:** the check (Step 2) is only measurable *after* the contract (Step 3)
forces a distinguishable quote marker. Measuring the check against pre-contract reports validates
only the fail-closed direction — what it would kill today.

## What stands

1. **Next Step 1 — move rejections out of the `--gated` set.** Untouched by any of this, no script
   change required, and it halves the cost of a fabrication (2 cycles → 1) by keeping the streak.
2. **Next Step 3 — the contract sentence**, with an explicit verbatim-quote marker so a claim about
   document content is machine-separable from proposed code. Belongs in
   `h-mad/audit-prompt.template.md` under the `Output framing (mandatory` anchor — **not**
   hand-written into `h_mad_assemble_audit.py`, whose `:168` comment says the head copy is sliced
   from the template, never authored.
3. **Next Step 2 — deferred**, with these numbers, until a post-contract corpus exists.

## The operator decision this surfaces

Fabrication rate by surface over c45–75: **agy 6 / 11 must-fixes, codex 0 / 25.** The defect is not
evenly distributed across the two-surface gate; it is one surface. That is direct evidence for
**task #13** — *make the agy document-audit pass evidence-first, or drop it from the two-surface
gate* — and it is a larger lever than #26's check, which at best catches 1 fabrication for free.

Not pre-decided here: dropping a surface weakens the union that
`feedback_never_gate_on_one_audit_pass` exists to protect.

## Reproduce

```bash
# corpus  (durable): ~/.h-mad-corpora/evidence-gate/prompts/   (64 prompts, c45-c76)
# scripts (durable): ~/.h-mad-corpora/evidence-gate/measure_spans.py, measure_spans2.py
# reports (durable): HemaSuite .../gateway-consolidation.design.audit.v{45..77}.{agy,codex}.md
#
# Run with python3.11 (python3 has no pytest/importable test helpers here).
# measure_spans.py  — rule 1: any absent backtick span.
# measure_spans2.py — rule 2: absent span BY SHAPE CLASS, plus the per-fabrication detail.
```
