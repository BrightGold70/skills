# Gap analysis — pin-agents-tail-banner

**Date:** 2026-09-02 · **Phase:** 6a · **Base (5c):** `03c66d55` · **Head (5g):** `4775c5d`

## Match rate: 100% (16 of 16 spec acceptance criteria implemented and passing)

Measured against `docs/01-plan/features/pin-agents-tail-banner.spec.md`, which carries 16 ACs
across FR-1..FR-5. Every one maps to at least one passing test node in
`h-mad/tests/test_hmad_dispatch.py`.

| evidence | value |
|---|---|
| spec ACs | 16 |
| implemented and passing | 16 |
| feature test nodes added | 45 (2 + 11 + 18 + 5 + 4 + 1, plus 3 corpus positives) |
| module suite | 335 passed |
| full repo suite | 2663 passed, 0 failed |
| mutations | 49/49 ALL_CAUGHT, 0 survived |
| mutation anchors | 49/49 resolving exactly once |
| wire registry | PASS — 10 registered, 10 verified, 0 broken |
| live check | PASS — real codex pane bound by tail evidence |
| 6a-prime | READY_TO_MERGE, 36 tool calls (evidence gate passed) |

## Traceability note — one AC is covered but uncited

`grep` for inline `(spec AC-x.y)` citations in the impl-plan finds 15 of 16. **Spec AC-4.4 is
implemented; it is the CITATION that is missing, not the coverage.** The spec and the impl-plan
use INDEPENDENT AC numbering and both happen to have an `AC-4.4`, which is what makes a
citation-based check misleading here:

- spec AC-4.4 — an envelope exiting 0 while carrying `"ok": false`, and a `.terminal.tail` that
  is not an array. Both are FR-4 directions that would RESOLVE rather than decline.
- plan AC-4.4 — rival rejection happening before counting. A different requirement entirely.

Verified by content rather than by citation: spec AC-4.4's two directions are
`test_tail_sig_rejects_ok_false_envelope` and `test_tail_sig_rejects_non_array_tail`, both
passing, and both mutation-pinned (`envelope-ok-false-accepted`, `non-array-tail-accepted`).

Carried as a documentation follow-up: add `(spec AC-4.4)` to those two plan rows so a future
citation sweep does not re-raise this. It is not a merge blocker — the behaviour is enforced.

## What the offline gates could not see

Every gate above except the live check was green while `_agent_tail_re` could not match ANY
real agent banner. The corpus held only idealised shapes, so 53 impl-plan audit cycles, two
clean audit surfaces, 335 unit tests and 46 mutations all agreed on a grammar that had never
been shown the string it exists to match. The live check is the only step that found it, and
the corpus now carries the three real strings as positives (36 negatives / 15 positives).

That is the fifth revision of this rule; the impl-plan records four earlier ones, each falsified
by a shape its corpus lacked. The difference this time is that the falsifying shape came from a
running pane rather than from imagination.
