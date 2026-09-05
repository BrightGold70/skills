# Handoff — doc-block-exec: Phase 5b EXITED at `4512615` on the operator's cap decision (r19 = last document round); h-mad class-scored gate + two-round cap MERGED `f2b3d74`; main pushed at `0afe254`, suite 2599 green

**Date:** 2026-09-06
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-05-main__doc-block-exec-r18-batch-landed.md (branch predecessor — read in full at resume; every open item walked below), 2026-09-03-main__hmad-audit-evidence-gate.md, 2026-09-05-main__audit-loop-never-runs-repo-suite.md and 2026-09-05-main__hmad-audit-loop-evidence-from-gateway-consolidation.md (taken over 09-03 / 09-05 by earlier sessions; their items carried through the predecessor and re-emitted below — not re-read this session; they still appear in `carry-forward-sources`, see #65)

## Session Summary

Resumed from the r18-batch-landed handoff, ran the **r18 gating** (six legs, FAIL ×3, 15 distinct musts,
16/16 orchestrator-verified — sheet C4/C5/C6, `d27d2ce`), then the **r19 revision batch** (two waves,
six reopens, three delta reviews — `7fc5f94`). Mid-round the operator ordered two things: **apply the
audit-system recommendations to the h-mad skill as top priority**, and **cap the document loop — r19 is
the last document round**. Both are done: `feature/hmad-class-scored-gate` (finding class build vs
measurement, `GATE-CLASS:` line, two-round cap with `OPEN-DECISION` routing, changed-documents-only
re-audit, codex-gates-plus-delta-review, measurement layer in probes) is **merged at `f2b3d74`**, and
**Phase 5b exited at `4512615`** after a codex-only r19 gating pass (plan 1 measurement-class must;
impl-plan 3 + design 3 build-class musts → five `OPEN-DECISION (r19, 5d)` lines on impl-plan Tasks
2/3/4; sidecars v91/v100/v51 gate PASS). Merged main went 1 failed on a size fixture, re-anchored at
`0afe254`, **2599 passed**, pushed. Next is Phase 5c/5d.

## Key Learnings

- **A gate that scores the self-measurement layer like a design defect cannot converge on a document
  that publishes numbers about a tree it moves.** Measured across r18 and r19: 9 of 15 and 12 of 12
  (delta) musts in that layer; two model families found DISJOINT must sets on the design and impl-plan
  three rounds running. The class test ("would the code or tests a 5d/5e implementer writes differ?")
  partitioned r18 as 9/6 and r19 as 1/6 — the class rule did what it was written to do.
- **The oversize trigger fired live:** the design no longer assembles at `--vh-tail 1` (1,051,233 chars);
  `--vh-tail 0` is read as "no trim". The last transport was built with `--docs-dir` pointing at staged
  copies of the paired spec/plan whose Version History is replaced by an omission note (bodies intact).
  No further document round on this feature is assemblable without the measurement-layer extraction.
- **The tooling merge moves the documents' own trip-wires** (design `a8e0372` screen 8 → 11+, plan `.py`
  censuses) — so the merge had to wait until the last gating pass was collected, and the docs are not
  re-stamped afterwards (they are not re-audited again). Merging h-mad while a document round is open
  silently invalidates every stamped census.
- **Sequential waves create phantom divergences:** the impl-plan author (wave 2) correctly recorded the
  design's wrong killer; the design was then reopened; the impl-plan's divergence prose became false of
  the shipped bytes. Rule-3 collisions are caught only by value-grepping ALL FOUR documents at collection,
  and a reopen on one document can owe a restatement on another that already finished.
- **A test that resolves its inputs through the live checkout can pass in a worktree and fail on merge**
  (`test_size_warning_fires_before_the_cliff_not_only_past_it`: +~1 KB head-duplicated template).
  Always run the full suite on the MERGED tree, not only on the branch.
- **`$s:h-mad/…` in zsh is the `:h` (dirname) modifier** — every per-sha count read 0 and looked like a
  clean result; write `${s}:h-mad/…`. The C3-warned `set -- $spec` no-word-split reappeared once too.
- **Orchestrator error #49w:** three sheet entries certified "no scoped census moved" over `b39d9dc`
  while the design's own published `expect 0` screen read 8 there. Run every published `expect 0`
  screen at the sha before certifying a freeze.
- **The state schema's phase vocabulary is `step5|step6|step7|null`** — `step5` covers all of 5a–5e; a
  `phase=step5c` write is refused. Not a defect.
- **`h_mad_state_write.py --set` refuses the WHOLE write when one key is undeclared** (`gate_5b`), so a
  bundled write with a bad key writes nothing.

## Next Steps

1. **#110 — Phase 5c/5d, Task 1 RED**: claim `doc-block-exec` (`h_mad_resume_decision.py` → `--claim`),
   then `python3 ~/.claude/skills/h-mad/scripts/h_mad_assemble_tdd.py --phase red --task 1
   --expect-fail N --expect-pass M --test-path h-mad/tests/test_h_mad_doc_block_exec.py` (counts
   re-derived from the impl-plan's Task 1 AC list, never from prose), dispatch the printed
   `hmad-dispatch exec codex … --sandbox workspace-write` block (never read-only for pytest), verify the
   RED summary independently. Inputs: `docs/01-plan/features/doc-block-exec.impl-plan.md` v1.55 (Tasks
   1–5, 87 mutation rows), design v1.111, spec v1.64, plan v1.106.
2. **Resolve the five `OPEN-DECISION (r19, 5d)` lines as their Tasks are reached** — impl-plan :2635
   (Task 2, shared key predicate), :2871 (Task 3, `preamble-composed-with-unsubstituted-text` seam),
   :2873 (Task 3, `OverflowError` / timeout upper bound), :3374 (Task 4, alias-refusal unlink
   read-back), :3376 (Task 4, `--help` bypass). Premises are "as filed by codex, re-derive before
   choosing".
3. **Remove the merged tooling worktree when convenient** — `git worktree remove
   /Users/kimhawk/orca/skills-hmad-gate && git branch -d feature/hmad-class-scored-gate` (destructive;
   left to the operator).
4. **#65 — fix `handoff_paths.py carry-forward-sources`**: the three taken-over briefs still list after
   two handoffs named them in `**Supersedes:**` (this doc names them a third time).
5. **#100 — the taken-over H1–H9 brief**: fold-or-not into `hmad-audit-evidence-gate` (#66/#91);
   defects A (`handoff/scripts/handover_landed.py:107-116`) and B (`h_mad_assemble_audit.py:453`) are the
   cheapest first moves. Unchanged.
6. **`[suggested]` #105 — codify "self-counting screens run last, per instrument"** in
   `h-mad/agents/*-author.md` (still the dominant delta-review class: 12/12 at r18 and r19).

## Open / Blocked Items

**doc-block-exec (this lane) — `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`**

- **Phase 5b EXITED at `4512615`** on the operator's cap decision, NOT on a two-surface clean (sheet
  C8/C10 say so). Batch `7fc5f94` (design v1.111 / plan v1.106 / impl-plan v1.55 / spec v1.64; fifth
  probe tracked, 5 total). Sidecars `plan.audit.v91.md`, `design.audit.v100.md`, `impl-plan.audit.v51.md`
  gate PASS under both gates. Suite 2574 at `7fc5f94`; 2599 at `0afe254` (merged main). State:
  `phase=step5` (covers 5a–5e), `codex_status=available`.
- **Claim on `doc-block-exec`: RELEASED at this handoff** (owner None). Claim before working.
- **#110 — 5c/5d NOT started.** Five OPEN-DECISIONs owed to the implementer (Next Step 2).
- **#108 tooling batch — DONE, merged `f2b3d74`** (commits `3fbf0e7` `29ce8b4` `9d78101` `2f937a3`;
  reviewer M1/M2/m1–m7 applied; fixture re-anchor `0afe254`). Worktree `skills-hmad-gate` still exists
  (Next Step 3).
- **Reviewer-side `class:` tagging starts with the next audit on ANY feature** (template + doc-auditor
  now carry it); the gate prints `GATE-CLASS:` on every PASS/FAIL. No feature has run the new gate on a
  real cycle yet — a field measurement is owed on the first one.
- **#109 — DONE.** #106 (r18 result) DONE. #103 DONE. #98 DONE. #14 (stamp gate) DONE by the cap route.
- **Orchestrator errors this session:** #49w (three sheet entries vs the design's live trip-wire, task
  #107); near-misses caught: zsh `$s:h`, `set -- $spec` again; one advisor-predicted error avoided
  (handing the r19 authors "88/88" after my own commit moved it to 89/89 — C6).
- **Codex quota — did NOT bind** (six codex legs ran across r18/r19, 0 `usage limit` hits). The 09-03
  window note is stale.
- **Standing "same model family" limit** — settled at r19 by construction: the same-family surface is
  now the delta review, not a second full gate.
- **agy leg — still not dispatched (#77).** Unchanged.
- **#61 `COLLECT: MISSING` marker-name defect** — unchanged. **#48 Effort figures unverifiable** —
  unchanged; blocks #4/#13. **#42 INHERITED-UNVERIFIED register** — the plan's register moved again this
  round (author re-ran the ledger series, the `.py` figures 415/5/2, the changed-`.py` 6→8); carry what
  remains. **#36 `tree delta`** — 88 untracked `.done` markers (unchanged count; do not commit).
- **Evidence-gate corpus OUTSIDE the repo, not backed up** (`~/.h-mad-corpora/evidence-gate/`) — unchanged.
- **#27, #7, #30, #32, marker-aware reaping** — unchanged from the predecessor (see it for text).
- **#49 AUTOMATION SCOUT — bounded this WRITE** (see the scout step below); candidates from THIS session:
  run every published `expect 0` screen before certifying a freeze; merge tooling only after the last
  gating pass is collected; value-grep all four documents after ANY reopen, not only at first
  collection; full suite on the merged tree; `${s}:` not `$s:` in zsh; a sequential wave's divergence
  prose expires when the earlier document is reopened. Plus the predecessor's carried candidates.
- **#9, #5, #8 P5 backlog** — unchanged. #5 is a foreign lane.
- **HemaSuite skill-candidate row handed over** — brief
  `HemaSuite/docs/handoffs/2026-09-04-main__wrapper-rc-row-is-probably-a-duplicate.md`, not re-checked.
  `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none`. Unchanged; ownership already moved.
- **`.claude/agents/` CLOSED** — unchanged. **r15 sheet's false scope clause** — unchanged.

**Taken over 09-05 by `adb05ac8` — `**Handover-From:** HemaSuite · main · session cab14393` · `**Taken-Over-By:** skills · main · session adb05ac8 · 2026-09-05`**
(`docs/handoffs/2026-09-05-main__hmad-audit-loop-evidence-from-gateway-consolidation.md`; `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`; task **#100**)

- **H1–H9 + tooling defects A/B — status: owned here, NOT started; unchanged since 09-05.** The class
  rule and the round cap landed this session address part of the same evidence (audit loops running
  40–50 cycles); whether H1–H9 are subsumed is the fold-or-not decision still open. Overlaps
  `hmad-audit-evidence-gate` (#66/#91).

**Inherited — `**Handover-From:** HemaSuite · main · session f0b69d8d` · `**Taken-Over-By:** skills · main · session ca259110 · 2026-09-03`**
(`docs/handoffs/2026-09-03-main__hmad-audit-evidence-gate.md`; `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none`; feature `hmad-audit-evidence-gate`, phase 0, task #66)

- **Both original fixes — not started, unchanged since 09-03**: (1) move rejections out of the gated
  set; (2) evidence check in `h-mad/scripts/h_mad_audit_gate.py` — NOTE the gate file was substantially
  edited this session (`classify_detail`, class parsing); re-read it before designing the evidence check;
  (3) tighten the contract; (4) mutation-test against the sender's corpus; (5) `[suggested]` agy-only
  `--passes N` gating.
- **Evidence corpus in the sender's scratchpad, not durable** — unchanged.

**Inherited — `**Handover-From:** HemaSuite · main · session 9d8394fb` · `**Taken-Over-By:** skills · main · session ee549bb1 · 2026-09-05`**
(`docs/handoffs/2026-09-05-main__audit-loop-never-runs-repo-suite.md`; folded into `hmad-audit-evidence-gate` as its THIRD defect, task #91)

- **Phase 3–4 audit cycle never runs the project test suite** — unchanged as a skill defect; this
  session ran the suite on every committed tree by hand (four runs) and it caught one real red (the
  size fixture on merge).

**Related lanes, not owned here**

- **`exec agy` lingers after its `result` event** — `docs/handoffs/2026-09-03-main__exec-agy-hang-after-report.md`,
  session `cd979362`. Unchanged. `repo: /Users/kimhawk/orca/skills · branch: main`.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_audit_gate.py`, `h-mad/tests/test_h_mad_audit_gate.py` (+24 tests),
  `h-mad/SKILL.md` (two exit clauses, §"Finding class", §"Document-audit round cap", §"The measurement
  layer lives in probes", §"Never gate on one audit pass" revision-cycle routing, script catalog),
  `h-mad/audit-prompt.template.md`, `h-mad/agents/doc-auditor.md`, `h-mad/agents/{spec,plan,design,implplan}-author.md`,
  `h-mad/tests/test_h_mad_assemble_audit.py` (fixture re-anchor)
- `docs/02-design/features/doc-block-exec.design.md` (v1.111), `docs/01-plan/features/doc-block-exec.{plan,impl-plan}.md`
  (v1.106 / v1.55) — by the authors; `docs/03-analysis/probes/doc-block-exec/substitution_independence_search.2026-09-06.51a2b6f7.py`
- `docs/03-analysis/doc-block-exec.gating-decision-sheet.r18.md` (C4–C10), `docs/03-analysis/doc-block-exec.r18-gating.{orchestrator-brief,verification-ledger}.md`,
  `docs/03-analysis/doc-block-exec.r19-gating.verification-ledger.md`, `docs/03-analysis/doc-block-exec.r19-batch.collection-crosscheck.md`
- twelve audit reports/sidecars under `docs/01-plan/features/` and `docs/02-design/features/` (v89/v90/v91, v97…v100, v48/v49/v50/v51)
- `docs/.bkit-memory.json` (claim taken then released; gitignored)

**Uncommitted changes:** none besides 88 untracked `.done` markers. `origin/main` = `0afe254`, in sync.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
/handoff read
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"; hmad-dispatch env
python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature doc-block-exec --session-id <you>   # then --claim
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests -q -p no:cacheprovider    # 2599 passed at 0afe254; bare python3 is 3.14, no pytest
grep -n '^\*\*OPEN-DECISION (r19, 5d):\*\*' docs/01-plan/features/doc-block-exec.impl-plan.md   # five lines
python3 ~/.claude/skills/h-mad/scripts/h_mad_assemble_tdd.py --help
```

**Related docs:**
- `docs/03-analysis/doc-block-exec.gating-decision-sheet.r18.md` — C8 (class rule + cap decision, blind), C9 (r19 dispatch), C10 (5b exit)
- `h-mad/SKILL.md` §"Finding class — build vs measurement", §"Document-audit round cap — Phase 5 is the gate"
- Commits this session: `d27d2ce` `c7a75eb` `0021c77` `b6fc2ee` `7fc5f94` `42a089b` `4512615` `b6b68e8` `f2b3d74` `0afe254` (+ branch `3fbf0e7` `29ce8b4` `9d78101` `2f937a3`)
- Task ledger: #98 ✓ #103 ✓ #106 ✓ #108 ✓ #109 ✓ #14 ✓; **#110 next**; #107 (#49w) open; #100 #65 #105 open
