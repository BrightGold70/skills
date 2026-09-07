# r19 collection cross-check (rule 3 — only the orchestrator sees collisions)

Freeze 0021c77. Wave 1: plan v1.106 DONE (PRECHECK PASS, 388+/115-), design v1.111 in progress. Wave 2: impl-plan v1.55 after design DONE.

## From the plan author's tail
- [ ] If the design ADDS the kind-selection rendering row: matrix 86 -> 87; the plan publishes 86 rows / 86 distinct / SKILL.md-target 1 "read at 0021c77" — must be re-derived against the BATCH commit (plan author says so). Value-grep 86/87 across all four docs at collection.
- [ ] Plan took NO working-tree reading of the design this round (deliberate); design owes only the shipped row decision.
- [ ] r18 impl-plan teammate report said b39d9dc "adds two .py files": actually A=1 (test_h_mad_agent_definitions.py) + first-change=1 (test_hmad_dispatch_exec.py). Reviewer mechanism error; counts 6->8 unaffected. Record in C8, not a doc defect.
- [ ] Ledger pair will move AGAIN when the r19 reports land (89/89 -> 90/90). The plan now names both movers. The r19 gating brief must NOT hand the author "89/89" as current after the reports land (advisor's point at r18).

## Shared strings to value-grep at collection
- killer test of any NEW matrix row (design names it; impl-plan must match)
- the rmtree fault-injection sentence (design's shipped wording -> impl-plan copy)
- any-pair offset wording (spec:183 / design:1408 form) in impl-plan :2094/:2463
- name of the new Task 4 CLI test split from test_invalid_utf8_document_is_unreadable (impl-plan chooses; grep all four)
- 30/292/82/0 stamped cac6edc in impl-plan
- TimeoutExpired at design:1854 region

## After batch
- delta self-review x3 (doc-auditor ADVISORY on each diff) -> reopen for musts -> commit batch -> FULL SUITE on the committed tree (#102) -> C8 (blind class rule, before verdicts) -> r19 gating c99/c90/c50 on the OLD template -> collect -> score with class rule via sidecar -> merge feature/hmad-class-scored-gate.

## Design v1.111 shipped (DONE 07:16, PRECHECK PASS, +404/-113, probe substitution_independence_search.2026-09-06.51a2b6f7.py runs: 13104/194/0)
- fake contract (design:1965, hard-wrapped after `ignore_errors`): "the injected `rmtree` must honour `ignore_errors` — raise the injected error only when `ignore_errors` is falsy, and return silently when it is true."
- row `intersect-kind-ignored` (design:4293) killed by `test_substitute_refuses_intersecting_spans` (AC-2.7); matrix 86 -> 87 (86 helper + 1 SKILL.md)
- timeout=-1 corrected to TimeoutExpired with paired probe fence (2 sites incl VH)
- design's own tree contradictions: $P is 39 not 40 (its own edits moved it); "the plan's mutation-total debt was …" (tail requested)
- Plan reopen sent 07:2x: add batch reading 87/87/1 with row name + killer; keep 86 at 0021c77.
- Wave 2 implplan-author dispatched with strings 1-4 + decisions a-d.
- Worktree suite at 29ce8b4 (branch): 2593 passed, 2 skipped (2574 + 21 new = 2595 collected).

## Design tail (07:18)
- [ ] BATCH COMMIT MUST INCLUDE docs/03-analysis/probes/doc-block-exec/substitution_independence_search.2026-09-06.51a2b6f7.py (design states probe count 4 at freeze / 5 on the batch tree).
- design's own contradictions of C7: v1.110 owed-list said plan carries 81 — plan body already said 86 at 0021c77 (debt is 86->87); $P 39 not 40; compliance walks 126/70 at cac6edc, 132/71 from ccd8ebd, 144/72 shipped.
- impl-plan's one remaining "85 rows" = historical cac6edc stamp, NOT drift — do not let the impl-plan author or a delta reviewer sweep it.
- design owes list == wave-2 brief items 1-4 (a: any-pair wording :2094/:2463; b: fake sentence; c: row + killer; d: 86->87 re-derived from the design table). plan owes 86->87 only (reopen sent). spec nothing.

## Wave 2 landed (impl-plan v1.55 DONE 07:39; PRECHECK FAIL issues=11 grammar, PINDRIFT 0; ast fences 9/0 errors; +283/-81)
- RULE-3 COLLISION #1 (caught by the impl-plan author): design:4293 killer `test_substitute_refuses_intersecting_spans` is Task 2's exception-data test (impl-plan:3439) -> cannot see a renderer mutant. Decision: killer = `test_cli_subst_overlap_detail_lines` (Task 4, impl-plan:3322). Design reopen + plan reopen #2 sent 07:4x. VALUE-GREP at collection: `test_cli_subst_overlap_detail_lines` must be >0 in design and plan; `intersect-kind-ignored` row killer identical in all three.
- new Task 4 test `test_cli_invalid_utf8_document_is_unreadable`: impl-plan 4, others 0 (correct — no sibling names it).
- impl-plan any-pair wording uses "ANY" (spec/design use `*any*`): same value, different emphasis — measurement-class nit at most; not reopened.
- impl-plan delta review (doc-auditor ADVISORY) dispatched on /tmp/r19_implplan.diff; design + plan delta reviews wait for their reopens.

## Delta reviews (ADVISORY, same-family surface)
- plan delta: must=4 should=2 nit=2 (Evidence 8 files / 57 greps) — all in the v1.106 VH entry or a self-count grammar; every v89 finding closed; every tree figure reproduced. Reopen #3 sent. Pattern: reopen screens were BODY-scoped and the VH entry carried the pre-reopen text — the r18 class again (12/12).
- impl-plan delta: pending. design delta: pending.
- impl-plan delta: must=3 should=4 nit=2 (12 files / 28 greps / 9 commands) — every figure reproduced; musts: phantom divergence (design reopened after impl-plan DONE — the sequential-wave ordering created it), 7/8 screen stamps v1.54, VH second CLI leg mismatch. Reopen sent.
- design delta: must=5 (all measurement) should=3 (1 build: mirror-constant residual only in VH) nit=1 (8 files / 61 greps) — every executable self-measurement reproduced (13104/194/0, trip-wire 8 x7 shas, matrix 87/87/1, 39/12, 144/72, import 89/13/14/48, expect-0 screens 0). Musts: fifth probe untracked (batch commit discharges), offset needle hard-wrapped (2/4 unreachable), marker split 3/2 not 2/1, 3.14.7 mis-attributed to codex (it was the orchestrator's probe, C5 ii), impl-plan:3322/:3438 phantom (impl-plan reopen). Reopen #2 sent.
- Round tally of delta musts: plan 4 + impl-plan 3 + design 5 = 12, of which build-class by reviewer tag: plan 2, impl-plan 1, design 0 (+1 should). Same 12 as r18 — the class is structural, not incidental.

## r19 GATING dispatched (batch 7fc5f94, C9 = 42a089b)
- design c99 codex: docs-dir staged VH-omitted spec/plan copies at scratchpad r19_docs_vh0/, --vh-tail 1, 1,011,624 chars
- plan c90 codex: --vh-tail 3, 676,634 chars
- impl-plan c50 codex: --vh-tail 1, 958,810 chars
- no doc-auditor full pass (C8 iii a). Suite on 7fc5f94 running (bup1ztbxd).
- After collection: classify per C8 i; sidecars `.audit.v{100,91,51}.md` with `## Acknowledged-not-fixed` [key] + re-run command for measurement-class; OPEN-DECISION reopen for build-class; stamp 5b; merge branch.

## r19 GATING results
- plan c90 codex: GATE FAIL must=1 should=3 nit=2 (14 files / 10 greps), collected plan.audit.v90.codex.md (delivered=out). M1 VERIFIED: composite probe heredoc plan:3984-3992 prints five "composite minus" lines and NO version line, while its recorded output block (:3993) carries `python 3.11.8` and the stamp accounting counts it. CLASS: measurement (no implementer code/test changes). Shoulds: draft-vs-shipped killer wording at Measurements (measurement), register 4.2.0-leg exclusion expired (measurement), ledger gap-growth claim (measurement). => plan build-class must = 0. Sidecar v91: [probe-version-line] ack with re-run `python3.11 -c 'import sys;print("python",sys.version.split()[0])'` + note; [killer-draft-wording]; [register-4.2.0-leg]; [ledger-gap-growth]; nits.
