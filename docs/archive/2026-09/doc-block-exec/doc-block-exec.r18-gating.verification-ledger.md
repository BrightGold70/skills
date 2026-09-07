# r18 gating — orchestrator verification ledger (freeze bc4688e, HEAD 093c3ee)

## plan c89 codex — GATE: FAIL must=1 should=3 nit=1 (collected plan.audit.v89.codex.md, delivered=out)
- M1 VERIFIED. quote present (plan:3462). h-mad/SKILL.md bare `#`: a469493 0, 1861157 0, bea1b60 1, fbc2ea0 1, cac6edc 0, HEAD 0
  (`git show "${s}:h-mad/SKILL.md" | grep -c '^#[[:space:]]*$'`; first probe used `$s:h` = zsh :h modifier -> every count read 0 -> caught).
  1861157 = 09-04 08:02; bea1b60 = 09-04 12:14. So the 1861157 zero was a TRUE zero (specimen not yet in the tree); plan:3462 calls it
  "the shape had not been looked for correctly" — conflates it with the closing_hash `## x ##` mis-corpus story. Route: plan author.
- S1..S3 quotes present (3/3). Not re-derived: softened set on GLOB (closing_hash=5) claim; 81/81 at 09e9307; register/ledger status prose.

## impl-plan c49 codex — GATE: FAIL must=4 should=3 nit=0 (collected impl-plan.audit.v49.codex.md, delivered=out)
- M1 VERIFIED. impl-plan:3178 prescribes a subprocess CLI invocation with "a `--preamble` argument containing `\x00`".
  Probe: subprocess.run(['/bin/echo','a\x00b']) -> ValueError: embedded null byte in the PARENT. The test cannot reach the CLI.
  Codex's own quote: line mis-spelled (its quote text is not the doc's spelling — it says so itself); the underlying span exists.
- M2 VERIFIED. design:1825 claims `cleanup-errors-ignored` (restore ignore_errors=True) killed by test_cleanup_failure_carries_the_os_error,
  which injects an rmtree that raises. Probe: fake rmtree raises under ignore_errors=False AND True -> mutant not discriminated
  by that test as written. Cross-doc: design row (design:4056) + impl-plan test prescription. Route: design (mock contract) + impl-plan.
- M3 VERIFIED (pending 2334 read): Task 1 AC-3.12 test_invalid_utf8_document_is_unreadable (:2334) gains its CLI half in Task 4 (:3163);
  Task 4 RED gate (:3413) says "every Task 4 test fails and Tasks 1–3 stay green" and --expect-pass = Task 3 GREEN passed figure (:3388-3389).
  A modified Task-1 test flips red in Task 4's RED -> the count and the "stay green" clause are both wrong by one. Route: impl-plan.
- M4 VERIFIED as a design-change item: quote present; impl-plan defers a kind-selection rendering mutation row to the design.
  Route: design decides (add row or state why not); impl-plan follows.
- S1..S3 quotes present (5/5).

## design c98 codex — GATE: FAIL must=3 should=2 nit=0 (collected design.audit.v98.codex.md, delivered=out)
- M1 VERIFIED. design:1516-1519 says the 13,104-case search was "run rather than reasoned" and publishes neither command nor output; the four probes committed at fbc2ea0 are grammar_corpus / heading_differential x2 / setext_census — none is this search; `git grep '13,104'` outside the design hits only the r18 design delta-review. Base invariant "Behavioural premises carry their command". Route: design (publish the enumeration script + its 13,104 / 194 output, or commit it as a fifth probe).
- M2 VERIFIED. design:1854 says `communicate(timeout=-1)` raises ValueError only after the child exists. Probe on 3.11.8 AND 3.14.7:
  timeout=-1 -> TimeoutExpired; timeout=1 -> ok. The premise is FALSE. Route: design (correct the claim, publish the paired probe).
- M3 VERIFIED (same defect as impl-plan codex M2; found independently in BOTH documents again, as at r16). design:1825-1827 quotes present.
- S1 (AC census command returns 0 not 7) / S2 ($P 40 vs 37): quotes present (4/4). Not re-run.
- All 9 quotes present.

## CODEX ROUND at bc4688e: plan 1/3, impl-plan 4/3, design 3/2 -> 8 musts, 8 shoulds; all three via --out (read-only sandbox), 0 quota hits.
## teammate legs — pending (design c98 / plan c89 / impl-plan c49)

## plan c89 teammate — GATE: FAIL must=2 should=4 nit=1 (collected plan.audit.v89.teammate.md, report-file; Evidence 12 files / 71 greps)
- M1 VERIFIED by re-run (see pipeline output above in session): codex/teammate ledger pair at fbc2ea0 vs cac6edc..093c3ee. Plan:4367 publishes 87/87 "this revision's one measurement commit" at fbc2ea0 while §Measurements binds v1.105 to cac6edc. OVERLAPS codex plan S3 (register/ledger not advanced to v1.105) — same defect, codex filed it as should, teammate as must. Route: plan.
- M2 VERIFIED by reading plan:4340 ("eight shas") vs the fenced series at :4359-4362 = 10 shas (1cbddb7 700c599 8c6539a b3be433 00b961f dfae038 3f70eb3 af19d53 09e9307 fbc2ea0). Route: plan.
- S1..S4 + nit: not re-derived; S2/S3 (repo-wide .py corpus moved at b39d9dc: 415/5/2 unchanged; changed-.py 6->8) are the #49t class again. S4 (batch stamp now dischargeable at ccd8ebd) is routing, not a defect.
- Auditor's own coverage caveat: §Measurements spans 1300-1382, 1460-1600, 2130-2530, 3100-3900 NOT read line by line.
- Teammate vs codex on the plan: codex M1 (1861157 zero) NOT found by teammate; teammate M2 (eight/ten) NOT found by codex; ledger-stale found by BOTH (codex should / teammate must). Union plan must = 3 distinct.

## design c98 teammate — GATE: FAIL must=4 should=2 nit=1 (collected design.audit.v98.teammate.md, report-file; Evidence 13 files / 46 greps)
- M1 VERIFIED by execution: `git diff --name-only a8e0372 <sha> | grep '\.md$' | grep -vc '^docs/'` -> cf3a862 0, fbc2ea0 0, cac6edc 8, ccd8ebd 8, bc4688e 8, 093c3ee 8
  (h-mad/SKILL.md, five h-mad/agents/*.md, two h-mad/references/*.md — all b39d9dc). Design publishes the screen with `# expect 0` and never stamps the 8. Route: design.
  NOTE: same root as #49t/#81 (a tooling commit moves a scoped census); C4 (i) of this round said "no phase document moved" — true — but the DESIGN's own trip-wire fired on b39d9dc and nobody read it, including me at C2/C3/C4.
- M2 VERIFIED by execution: `git diff --name-only b39d9dc^ b39d9dc -- h-mad handoff` = 13 files incl h-mad/SKILL.md; `-- '*.py'` = 4. Design prose "b39d9dc passed every scoped census predicate" is FALSE. Route: design (ground sentence only; the fixture decision stands).
- M3 VERIFIED by execution: 'shared by *any* intersecting span pair' design 1 / spec 1 / impl-plan 0; 'the two spans SHARE' impl-plan 3 at HEAD (:2094, :2463 body; :4146 VH) vs 2 at cac6edc — the r18 batch ADDED a retired-wording site. Cross-doc: design owes an owed-elsewhere entry; impl-plan owes the rewording. OVERLAPS codex impl-plan S3 (minimum over span pairs, offset 1 not 7) — same axis, codex filed it as a should on the impl-plan. Route: design (owed-elsewhere list) + impl-plan (two body sites).
- M4 VERIFIED by execution: `tr '\n' ' ' < design | grep -oF intersections | wc -l` = 5 whole file (2 body :1436/:2955 + 3 in the v1.110 VH entry), design says 4; cac6edc 0 correct. Route: design (self-count, the r18 class again — "self-counting screens run LAST").
- S1 (88 vs 89 test files at cac6edc; plan already re-stamped 89) / S2 (AC fence reads spec blob at cac6edc while batch ships v1.64; sets identical) / nit: not re-derived.
- Codex vs teammate on the design: ZERO overlap in musts (codex: 13,104 command, timeout=-1 FALSE, rmtree fake; teammate: trip-wire 8, b39d9dc ground FALSE, offset wording owed-elsewhere, intersections 4->5). Union design must = 7.

## impl-plan c49 teammate — GATE: FAIL must=2 should=2 nit=2 (collected impl-plan.audit.v49.teammate.md, report-file; Evidence 26 files / 61 greps)
- M1 VERIFIED by execution: committed probe heading_differential.2026-09-04.b66afa9c.py at HEAD prints TRACKED files=30 both=292 old_only=82 new_only=0 / GLOB files=35 both=297 old_only=82;
  impl-plan :1701/:1703 publish 25/263/76/268 in present tense + "no round having re-run them" while the plan (same batch) publishes 30/292/82/0 at cac6edc. #42 INHERITED-UNVERIFIED class; the plan's register retired it, the impl-plan's did not. Route: impl-plan.
- M2 VERIFIED by execution: ast.parse over the impl-plan's fenced python blocks — 8 ok, the Task 4 code-structure block at :3120 raises SyntaxError at :3153 (three bodiless defs :3152-:3154). Route: impl-plan (add ` ...`; add the ast screen to pre-publish).
- S1 = design teammate M3 = codex impl-plan S3 (offset over ANY intersecting pair) — three legs, one axis. S2 (Task 5 "alone" scope) + 2 nits not re-derived.
- Codex vs teammate on the impl-plan: zero must overlap (codex: NUL argv, rmtree fake, Task 4 RED count, kind-selection row; teammate: stale differential, unparsable block). Union impl-plan must = 6.

## ROUND UNION at bc4688e (all six legs collected, every must orchestrator-verified: 16/16)
- plan: codex 1 + teammate 2 (1 overlap with codex S3) = 3 distinct musts
- design: codex 3 + teammate 4, no overlap = 7 distinct musts
- impl-plan: codex 4 + teammate 2, no overlap = 6 distinct musts
- cross-doc pairs: rmtree fake (design codex M3 == impl-plan codex M2); offset wording (design tm M3 == impl-plan tm S1 == impl-plan codex S3)
- distinct union musts = 3 + 7 + 6 - 1 (rmtree counted once) = 15; two families found DISJOINT sets on design and impl-plan again (r16, r17, r18).
- No `orchestrator-stated` tag appeared in any report; no leg filed against a brief fact.
