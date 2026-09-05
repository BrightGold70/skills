# r19 gating — verification and classification ledger (batch 7fc5f94, C9 42a089b)

Class test (sheet C8 i): would the code or tests a 5d/5e implementer writes differ if this finding were fixed? yes = build, no = measurement.

## Verdicts (codex only; delta reviews were the same-family surface — sheet C8 iii a)
| leg | GATE | must class | disposition |
|---|---|---|---|
| plan c90 codex | FAIL must=1 should=3 nit=2 | measurement | sidecar plan.audit.v91.md |
| impl-plan c50 codex | FAIL must=3 should=4 | build ×3 | OPEN-DECISION 1, 2, 3 on Tasks 3 / 4 / 4; sidecar impl-plan.audit.v51.md for the shoulds |
| design c99 codex | FAIL must=3 should=1 | build ×3 (must 2 = impl-plan must 3) | OPEN-DECISION 4, 3, 5 on Tasks 3 / 4 / 2; sidecar design.audit.v100.md for the should |

## Verification
- plan c90 M1 VERIFIED by reading: heredoc at plan:3984-3992 prints five `composite minus` lines and no version line; recorded output at :3993 carries `python 3.11.8`; the stamp accounting at :4292 counts it. Measurement.
- impl-plan c50 / design c99 build-class musts: quotes present (8/8 impl-plan, 6/6 design); premises as filed by codex (two executed on 3.11.8: `communicate(timeout=1e300)` OverflowError; argparse `--bogus --help` exits 0 with help). Carried as OPEN-DECISIONs for re-derivation in 5d — the cap policy makes a wrong premise cost a probe, not a round.
- Cross-leg agreement: the `--help` bypass was found by codex in BOTH the design and the impl-plan (r16, r18, r19 pattern: a design-logic class found in two documents by the independent family).

## Suite
- `pytest h-mad/tests -q` on 7fc5f94: 2574 passed in 379.35s.

## Round shape (for the skill's record)
- authors: 3 (design, plan parallel; impl-plan after the design); reopens: 6 (plan ×3, design ×2, impl-plan ×2 incl. the OPEN-DECISION one); delta reviews: 3 (12 musts, 3 build-tagged); gating legs: 3 codex.
- oversize trigger fired: design HALTs at --vh-tail 1 (1,051,233); transport assembled with paired-document Version Histories omitted (1,011,624). No further document round is assemblable without the measurement-layer extraction (branch rule).
