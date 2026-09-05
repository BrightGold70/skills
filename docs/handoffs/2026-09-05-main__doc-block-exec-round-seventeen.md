# Handoff — doc-block-exec 5b round seventeen: four authors, thirty-nine sheet corrections, gating FAIL on every phase with the codex class re-opened; audit-loop handover taken over

**Date:** 2026-09-05
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-05-main__doc-block-exec-rounds-fifteen-sixteen.md (branch predecessor — read in full at resume; every open item walked below), 2026-09-05-main__audit-loop-never-runs-repo-suite.md (inbound handover, TAKEN OVER this session — stamped `34ed5ef`, claimed, items re-emitted under their origin below), 2026-09-03-main__hmad-audit-evidence-gate.md (taken over 09-03 by `ca259110`; its items carried through the predecessor and re-emitted below — not re-read this session)

## Session Summary

Round seventeen of the 5b gating loop, complete: revisions `cb4fe99` (design v1.109 / plan v1.104 /
impl-plan v1.53 / spec v1.63, freeze `fbc2ea0`) and gating `fa64031` at design c97 / plan c88 /
impl-plan c48 — **FAIL on every phase, both surfaces, union must 15** (teammate 6 / codex 11, the plan's
two identical on both surfaces). Four parallel authors closed all 21 r16 musts; the spec was revised
for the first time in three rounds because four codex findings moved cross-document contracts. The
decision sheet accumulated **39 dated corrections during the round**, about twenty of them to the
orchestrator's own sheet, every one found by an author or a cross-document comparison. The codex
class is **re-opened**, not closed: 11 new codex musts, all premises verified, three of them
cross-document contradictions the batch itself introduced. Separately: the inbound HemaSuite handover
(Phase 3–4 audit loop never runs the suite) was **taken over** and folded into
`hmad-audit-evidence-gate`. Loop stopped by operator instruction at ~65% context.

## Key Learnings

- **A FACT table with a "—" cell is a silent routing gap.** FACT 8 said the plan owed nothing for
  collect-only and for the 81→85 count; the plan restates both, so plan-author was never told and
  both surfaces filed both as musts (#49u). Fill an ownership table from a grep of the shared VALUE
  across all four documents, never from which document the finding was raised against.
- **A value sweep must try every SPELLING of the value.** Three misses in one round from one cause:
  `<offset>` placeholder vs the instantiated `at "0"` (design :3548); `heading_differential.py` vs the
  extension-less form inside grep alternations (9 body sites, `.py` form 0); `81 rows` vs `81
  mutations`. Sweep by the shortest form the name takes anywhere in the document.
- **A freeze whose closure predicates pass for the roots they name can still move a census that
  names no root.** The probe commit `fbc2ea0` touched only `docs/03-analysis/probes/`, passed every
  `h-mad`/`handoff` predicate, and moved every repo-wide `*.py` census (fences 6→8, files 24→25) and
  an unscoped `git ls-files` census (0→3) in three documents. Enumerate every census COMMAND the four
  documents publish and re-run each at the candidate sha (#49t). Attribute a delta per commit — the
  +5 collection was `af19d53`'s, not the probes' (C14).
- **A "failed: Prompt is too long" subagent notification is recoverable, not death.** design-author-r17
  resumed from its transcript and wrote seven times while a successor I had spawned watched; the
  successor asserted-before-write and made zero edits. Rule ownership explicitly BEFORE spawning a
  successor (#90). Authors must never call advisor() and must read a 3,500-line document in slices.
- **A slow leg is not a dead leg — for the second time.** The plan c88 teammate delivered at 57 minutes
  against siblings' 12; re-dispatched to a DISTINCT path per #49o and the original then landed. The
  `-b` leg is still running at handoff (no report yet) and is a second reading, not a replacement.
- **Cross-family convergence is now a pattern on the plan** (c86 4/4, c88 2/2), and this round added a
  cross-document instance: `OverlappingSubstitution`'s three representations were filed by codex from
  the impl-plan side and by the teammate from the design side, independently.
- **A discrimination matrix scores the ASSERTIONS its tests make, never the rendering a probe prints.**
  The design's `_field` matrix was wrong three times in one revision (line-count model vs the tests'
  quoted-form and spelling assertions) and died only at the first cross-document diff against the
  impl-plan's matrix. Two documents carrying one matrix are checked by diffing them.
- **`re.finditer` enumerates non-overlapping occurrences per key**, so the prescribed span scan misses
  `aa` at `[1,3)` in `aaab` and the cross-key intersection with `ab` — use the lookahead form
  `(?=…)` with `(m.start(), m.start()+len(k))`. This also falsified my own 3a residual.
- **`raise err from X` always sets `__suppress_context__ = True`**; a test asserting it False while
  prescribing explicit chaining rejects the prescribed implementation (impl-plan AC-3.14).
- **The c1 second pass escapes LF** (`unicodedata.category("\n") == "Cc"`), so a "quotes kept, json.dumps
  escaping dropped" mutant frees exactly `"` and `\` — the row needed a new isolating killer.
- **The teammate `EMPTY`/silent-notification problem has a benign shape too**: two auditor DONE messages
  arrived ~45 minutes after their `.done` markers. The report file is the deliverable; collect on the
  marker, not the message.

## Next Steps

1. **r18 sheet** — `docs/03-analysis/doc-block-exec.gating-decision-sheet.r18.md`. Freeze = `fa64031`
   (or HEAD after any tooling commit — if #87 lands first, re-run EVERY census command the four documents
   publish, not only the `h-mad handoff` predicates). Carry r17 FACT 2 (freeze clauses), FACT 5
   (reopen rule), FACT 6 (bump-first/DONE-once), and the r17 lessons above as rules. Build the
   ownership table by grepping the shared values across all four documents (C32/#49u).
2. **r18 routing — the codex class as design changes, ONE decision each, stated once:** (a)
   `OverlappingSubstitution` — pick ONE representation (recommend the design's single tagged `pairs`
   list of `(kind, a, b, offset|None)`; the impl-plan's `pairs`+`intersections` and Task 1's bare
   pairs go); (b) span scan enumerates overlapping occurrences via `(?=…)` lookahead, fixture `aaab`
   under `{aa,ab}` → `intersect: "aa" "ab" "2"`; withdraw sheet 3a's self-intersection residual;
   (c) AC-3.14 asserts `__cause__ is cleanup_error`, not `__suppress_context__ False`; (d)
   `LaunchFailed.__init__` err annotation `OSError | subprocess.TimeoutExpired | ValueError`
   (impl-plan :1973); (e) Task 2's intersection test asserts exception data; the emitted detail line
   is asserted in Task 4; (f) Task 5 scaffold keeps the exactly-one-gating-fence guard (three
   `_gating[0]` sites); (g) Task 2's `AttributeError` REDs vs `codex-implementer-prompt.md:52` — a
   TOOLING fix (scope line 52 to `wiring`-shape tasks) in the #87 batch, and the impl-plan states why
   a new-symbol task's RED is `AttributeError` by construction.
3. **r18 routing — the routing gaps and prose class:** plan AC-1.8 pin → `--collect-only`, `81
   mutations` → 85 (two sites) [C32]; design `at "0"` at the AC matrix row (:3548), `22` → 23 slicer
   sweep, stale `29`/`69`/"prints nothing" self-measurements, five spec ACs never named (2.3, 3.4,
   3.5, 4.4, 6.3); impl-plan `_field` docstring 19 → 20, wire-row carve-out gains `wire-unconditional`,
   Task 2 nine/ten count; plan register statuses and the closure chronology (both broke at
   `af19d53`). Reports: `docs/02-design/features/doc-block-exec.design.audit.v97.{teammate,codex}.md`,
   `docs/01-plan/features/doc-block-exec.plan.audit.v88.{teammate,codex}.md`,
   `docs/01-plan/features/doc-block-exec.impl-plan.audit.v48.{teammate,codex}.md`.
4. **Collect the `-b` leg if it landed** — `hmad-dispatch collect-report --surface teammate-b --feature
   doc-block-exec --phase plan --cycle 88 --report /tmp/audit_doc-block-exec_plan_cycle88_teammate-b.report.md
   --out /tmp/audit_doc-block-exec_plan_cycle88_teammate-b.out.txt --project-root /Users/kimhawk/orca/skills`;
   gate it; a must the original missed goes into r18 (r15 precedent).
5. **Assemble r18 gating with `--vh-tail 3`** (design was 1,027,802 chars — 20 KB under codex's 1 Mi
   ceiling; `--vh-tail 1` gives 945 KB if it grows). Cycles: **design c98 / plan c89 / impl-plan c49**.
   One report path per leg; codex via `hmad-dispatch exec codex … --sandbox read-only --timeout 1800`
   backgrounded with `--log`; teammates `doc-auditor` by prompt path, told the freeze sha AND the
   actual HEAD (C37).
6. **Author dispatch rules for r18** (from #90/C22): no advisor() inside an author; sliced reads only;
   rule ownership before any successor; every DONE message puts the literal `DONE` line FIRST (four r17
   reports were truncated before their DONE).
7. **#87 tooling batch (touches `h-mad/`, moves the freeze — do it BEFORE the r18 sheet or after r18
   gating, never mid-round):** SKILL.md 5.5 names `--vh-tail`; `hmad-dispatch exec` surfaces
   `input_too_large`; repair the bare `#` at `h-mad/SKILL.md:984`; scope `codex-implementer-prompt.md:52`
   to wiring tasks; agent definitions: forbid advisor(), mandate sliced reads.
8. **#65 carry-forward displacement — reproduced again this WRITE**: `carry-forward-sources --branch
   main` printed the two handover briefs and NOT the branch predecessor
   `2026-09-05-main__doc-block-exec-rounds-fifteen-sixteen.md`. Fix `handoff/scripts/handoff_paths.py`
   so the branch's newest non-handover handoff is always returned in addition to pending briefs.

## Open / Blocked Items

**doc-block-exec (this lane) — `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`**

- **5b gate NOT met.** design v1.109 / plan v1.104 / impl-plan v1.53 / spec v1.62→v1.63 at `cb4fe99`;
  r17 gating at `fa64031`: design 2+3, plan 2+2 (same set), impl-plan 2+6. Union 15.
- **Claim on `doc-block-exec` HELD by this session `ee549bb1`** (claimed at resume). Released at this
  handoff — see the release line under To Resume. `phase=step5` flag is 50h+ old with no halt (the loop
  is genuinely in 5b; staleness SUSPECT is expected).
- **Claim on `hmad-audit-evidence-gate` HELD by this session** (taken over today). Released at this
  handoff too.
- **auditor-plan-c88-b** — a second plan c88 teammate leg dispatched 16:06 to a distinct path; no
  report at handoff time. Next Step 4.
- **Probes committed** at `fbc2ea0` under `docs/03-analysis/probes/doc-block-exec/` (two
  `heading_differential` versions, `grammar_corpus`, `setext_census`). markdown-it-py claims in the spec
  are measured at 2.2.0 (the probe's interpreter); the 4.2.0 venv is unreconstructable. r18 debt: five
  grammar-probe cases (C20).
- **Codex quota — OPEN and used**: three codex legs this round, all delivered via `--out` (no report
  file written, as in r16).
- **Standing "same model family" limit — plan settled twice over (c86, c88); design/impl-plan codex
  still finds a population the teammate leg does not, and vice versa.**
- **agy leg — still do not dispatch for gating until #77 addressed** (unchanged).
- **Orchestrator errors this session: #49s (grammar/asserted-scope in the sheet), #49t (freeze moved
  repo-wide censuses + misattributed +5), #49u (FACT 8 "—" routing gaps), #90 (spawned a successor
  without ruling ownership; treated an overflow notification as death), plus C37 (HEAD claim one
  commit stale) and C25 (my newline-test mechanism wrong twice).** Tasks #88, #89, #90, #93.
- **#61 `COLLECT: MISSING` marker-name defect** — unchanged since 09-05 predecessor.
- **#48 `tools=N` / Effort figures unverifiable from repo** — unchanged. Blocks #4/#13.
- **#42 INHERITED-UNVERIFIED register** — the plan's register moved 7 → 10 members this round; codex
  plan c88 should 1 says its statuses contradict the measurements section (Setext re-run recorded but
  listed un-re-run). Carry.
- **#36 `tree delta: N` cannot signal agent writes** — unchanged; 77 untracked `.done` markers.
- **Evidence-gate corpus OUTSIDE the repo, not backed up** (`~/.h-mad-corpora/evidence-gate/`) —
  unchanged.
- **#27 deferred evidence check** — unchanged.
- **#7 `docsections.py` `_fence_aware_end` dedupe** — unchanged; closes with 5e.
- **Marker-aware reaping for `exec`** — unchanged, deliberately not built.
- **#30 awk boundary fix HALF done** — unchanged.
- **#32 re-dispatch two agy legs round five** — stale; likely withdraw; unchanged.
- **#49 AUTOMATION SCOUT — SKIPPED this WRITE (`--skip-scout`, context budget).** Census last measured
  09-05 morning (194/194 parsed, 15 open `yes` rows). Candidates from this session to append next time:
  spelling-complete value sweep (bare + filename + placeholder + instantiated forms); census-command
  enumerator for freeze checks; author-definition rules (no advisor, sliced reads); `DONE`-first message
  contract; `pending-handovers`-style check for stale FACT-table "—" cells.
- **#9, #5, #8 P5 backlog** — unchanged. #5 (101 HemaSuite rows) is a foreign lane.
- **HemaSuite skill-candidate row handed over** — brief
  `HemaSuite/docs/handoffs/2026-09-04-main__wrapper-rc-row-is-probably-a-duplicate.md`, not re-checked.
  `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none`. Unchanged.
- **`.claude/agents/` remains CLOSED** — five agents at `h-mad/agents/`, user-scope symlink. Unchanged.
- **`.done` markers untracked** — deliberate; do not commit.
- **r15 sheet's false scope clause** — C5 in `…delta-decision-sheet.r15.md`; unchanged.

**Inherited — `**Handover-From:** HemaSuite · main · session f0b69d8d` · `**Taken-Over-By:** skills · main · session ca259110 · 2026-09-03`**
(`docs/handoffs/2026-09-03-main__hmad-audit-evidence-gate.md`; `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none`; feature `hmad-audit-evidence-gate` in `docs/.bkit-memory.json`, phase 0 — **now THREE defects**, task #66)

- **Both original fixes — not started, unchanged since 09-03**: (1) move rejections out of the gated
  set; (2) evidence check in `h-mad/scripts/h_mad_audit_gate.py`; (3) tighten the contract; (4)
  mutation-test against the sender's corpus; (5) `[suggested]` agy-only `--passes N` gating.
- **Evidence corpus in the sender's scratchpad, not durable** — unchanged.

**Inherited — `**Handover-From:** HemaSuite · main · session 9d8394fb` · `**Taken-Over-By:** skills · main · session ee549bb1 · 2026-09-05`**
(`docs/handoffs/2026-09-05-main__audit-loop-never-runs-repo-suite.md`, stamp committed `34ed5ef`; folded into `hmad-audit-evidence-gate` as its THIRD defect, task #91; `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none`)

- **Phase 3–4 audit cycle never runs the project test suite** — premises re-verified at `fbc2ea0`
  (gate 407 lines, 0 execution hits; `pytest` in SKILL.md only at 437/463/597/832/1787/2350). Next
  Steps (the brief's): decide gate vs SKILL.md Phase 3/4 step; decide verdict semantics (per-cycle
  block / non-blocking line / exit-gate-only) — beware the concurrent-suite trap
  (`docs/skill-candidates.md:1277`); scoped test root mandatory; TDD + mutation-test with #66. Field
  evidence here: #77 (an agy auditor died running pytest at the 285s timeout).

**Related lanes, not owned here**

- **`exec agy` lingers after its `result` event** — `docs/handoffs/2026-09-03-main__exec-agy-hang-after-report.md`,
  taken over by session `cd979362`. Unchanged. `repo: /Users/kimhawk/orca/skills · branch: main`.

## Context for Next Session

**Files touched this session:**
- `docs/02-design/features/doc-block-exec.design.md` (v1.108 → v1.109), `docs/01-plan/features/doc-block-exec.plan.md` (v1.103 → v1.104), `docs/01-plan/features/doc-block-exec.impl-plan.md` (v1.52 → v1.53), `docs/01-plan/features/doc-block-exec.spec.md` (v1.62 → v1.63)
- `docs/03-analysis/doc-block-exec.gating-decision-sheet.r17.md` (FACT 1–8 + corrections C1–C39 + gating result)
- `docs/03-analysis/probes/doc-block-exec/{heading_differential.2026-09-03.cd979362,heading_differential.2026-09-04.b66afa9c,grammar_corpus.2026-09-03.cd979362,setext_census.2026-09-04.b66afa9c}.py` (new, `fbc2ea0`)
- 6 gating reports: `…design.audit.v97.{teammate,codex}.md`, `…plan.audit.v88.{teammate,codex}.md`, `…impl-plan.audit.v48.{teammate,codex}.md`
- `docs/handoffs/2026-09-05-main__audit-loop-never-runs-repo-suite.md` (`Taken-Over-By:` stamp, `34ed5ef`)
- `docs/.bkit-memory.json` (claims on `doc-block-exec` and `hmad-audit-evidence-gate`; gitignored)

**Uncommitted changes:** none besides the untracked `.done` markers and this doc until committed.
`origin/main` at `fa64031`, 0/0 before this handoff commit.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
/handoff read
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"; hmad-dispatch env
python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature doc-block-exec --session-id <you>   # claim before working
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/ -q -p no:cacheprovider    # 2552 at fbc2ea0; bare python3 is 3.14, no pytest
for f in docs/02-design/features/doc-block-exec.design.md docs/01-plan/features/doc-block-exec.{plan,impl-plan,spec}.md; do tr '\n' ' ' < $f | /usr/bin/grep -oE -- '- v1\.[0-9]+' | tail -1; done   # re-derive, never trust a pin; ugrep shadows grep
```

**Related docs:**
- `docs/03-analysis/doc-block-exec.gating-decision-sheet.r17.md` — read the Corrections section before writing r18's sheet; C32–C36 hold the verified codex/teammate findings, C22/C24 the author-overflow record
- `h-mad/SKILL.md` §"The four rules that are the ORCHESTRATOR's", §"Never gate on one audit pass"
- Commits this session: `fbc2ea0` (probes), `cb4fe99` (r17 revisions), `34ed5ef` (takeover stamp), `fa64031` (r17 gating)
- Task ledger #84–#94 carries the round records, #88/#89/#90/#93 the orchestrator errors, #91 the taken-over defect
