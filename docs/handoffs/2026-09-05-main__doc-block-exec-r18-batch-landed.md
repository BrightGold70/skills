# Handoff — doc-block-exec: r18 revision batch LANDED at `ccd8ebd`, suite green again, gating freeze `bc4688e`; #98 gating NOT yet dispatched; inbound H1–H9 brief TAKEN OVER

**Date:** 2026-09-05
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-05-main__doc-block-exec-r18-sheet.md (branch predecessor — read in full at resume; every open item walked below), 2026-09-05-main__hmad-audit-loop-evidence-from-gateway-consolidation.md (TAKEN OVER this session by `adb05ac8`, read in full; its items re-emitted below under #100), 2026-09-03-main__hmad-audit-evidence-gate.md and 2026-09-05-main__audit-loop-never-runs-repo-suite.md (taken over 09-03 / 09-05 by earlier sessions; carried through the predecessor and re-emitted below — not re-read this session)

## Session Summary

Resumed from the r18-sheet handoff (session d16ef45c) with a fresh context, took over the pending
HemaSuite brief (H1–H9 + two tooling defects, task #100), then ran task #101 end to end: claimed
`doc-block-exec`, found the **h-mad suite RED on the committed tree since `b39d9dc`** (task #102 —
#87's assembler edit turned four impl-plan provenance pins into `PINDRIFT`; the prior handoff's "2574"
was measured pre-commit), wrote sheet C2 (shared strings + the suite-red routing) at `f6849bb`,
dispatched four fresh-context authors in parallel, caught **two parallel-author collisions** at
collection (matrix 85 → 86; one killer test named two ways), ran four advisory delta reviews (**12
musts, all in the self-measurement / Version History layer**), reopened every author twice, and landed
the batch as **`ccd8ebd`** — design v1.110 / plan v1.105 / impl-plan v1.54 / spec v1.64, **`2574 passed
in 377.47s`**. Sheet C3 (`bc4688e`) records the post-batch facts and is the freeze for gating. Stopped
at the h-mad 80 % context ceiling BEFORE dispatching #98; that is the next session's first move.

## Key Learnings

- **A tooling commit is a measurement event for provenance pins.** `b39d9dc` edited
  `h_mad_assemble_audit.py`; the impl-plan pinned `:247`/`:109` with provenance `fbc2ea0`, so the
  precheck's `PINDRIFT` went 0 → 4 and the noise-floor test (≤ 12 hard) went red on the COMMITTED tree
  while the handoff claimed 2574 green. Re-run the suite on the committed tree, never on the pre-commit
  working tree, and grep every phase document for pins into any file a tooling commit touched.
- **A shared-facts gate must paste strings in the documents' own spelling.** C2 iii handed the residual
  sentence with single quotes; two authors wrote double; the plan delta filed a must. Orchestrator error
  #49v (C3 ii).
- **Rule-3 collisions are real and only the orchestrator sees them.** The design author added a matrix
  row (85 → 86) and named its killer; the impl-plan author named the same test differently. Neither
  could know. Value-grep every new test name across all four documents at collection; choose the winner
  by edit cost and STATE the choice (design's name won: zero design edits vs two impl-plan renames).
- **Delta reviews on the diff found 12 musts and every one was self-measurement debris** (a self-count
  not re-run after the last edit, a tally mixing two corpora, a hop series called "none" that printed
  four hunks). The impl-plan author's rule, worth codifying: a screen whose needle matches the kind of
  prose a reviser is writing is run LAST, per instrument, after the final edit.
- **The design author's own instrument beat my value grep:** "five unnamed ACs" was seven; the AC-range
  expansion script is the right tool, not a grep over guessed labels (C3 ii).
- **#65 reproduced a THIRD time, in the other direction:** after `**Taken-Over-By:**` was stamped on the
  inbound brief, `carry-forward-sources --branch main` listed that brief plus the two older briefs and
  NOT the branch predecessor `…r18-sheet.md`. A handover under this branch's slug displaces the
  predecessor exactly as the task says; naming the older briefs in `**Supersedes:**` did not retire them.
- **`handover_landed.py` defect A confirmed in code** (`handoff/scripts/handover_landed.py:107-116`
  returns `taken` for any non-empty non-stamp comment) and **defect B confirmed**
  (`h_mad_assemble_audit.py:453` checks only the pane path). Both from the taken-over brief (#100).
- **`set -- $spec` does not word-split under zsh**; my precheck loop measured nothing and printed
  `usage:` for all four — read the token, and never trust a loop that prints the same line four times.

## Next Steps

1. **#98 — r18 gating at freeze `bc4688e`** (docs-only over the batch `ccd8ebd`). First
   `export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"; hmad-dispatch env` (codex pin
   `term_f483657a` was `state=done` at resume — verify live). Assemble design **c98** / plan **c89** /
   impl-plan **c49** with `--vh-tail 3` and **READ the size line** before dispatching anything: the design
   prompt was 1,027,802 chars at r17 (20 KB under the cap) and this batch added +384 net design lines,
   +263 plan, +52 spec — `--vh-tail 1` on `oversize` HALT (`h-mad/scripts/h_mad_assemble_audit.py`).
   Codex via `hmad-dispatch exec codex <prompt> --sandbox read-only --timeout 1800 --log <path>`
   backgrounded, plus one `doc-auditor` GATING leg per phase told freeze `bc4688e` + HEAD. No agy leg
   (#77). **Brief every leg with sheet C3 (v)'s measurable facts** (plan binds "freeze" to `4e4a00c`;
   impl-plan's AC-3.14 spelling; impl-plan's 11 grammar PLACEHOLDER slots; nobody writes "N passed").
   Collect on report files; `COLLECT: MISSING` is not evidence a leg failed (#61).
2. **Read sheet C2 + C3** — `docs/03-analysis/doc-block-exec.gating-decision-sheet.r18.md` (C2 i suite-red
   routing, C2 iii shared strings, C3 ii premises the authors falsified, C3 iii collisions, C3 v facts).
3. **#100 — the taken-over H1–H9 brief**: decide whether to fold into `hmad-audit-evidence-gate` (#66/#91;
   overlap is real). Tooling defects A and B are verified in code (Key Learnings) and are the cheapest
   first moves: `handoff/scripts/handover_landed.py` (gate the comment signal on the sender having
   stamped) and `h-mad/scripts/h_mad_assemble_audit.py` (Agent-tool ingestion warning ~700 KB + line
   ranges for windowed legs).
4. **#65 — fix `handoff/scripts/handoff_paths.py carry-forward-sources`**: a brief under this branch's
   slug displaces the branch predecessor; and naming a brief in `**Supersedes:**` did not retire it
   (three sessions running).
5. **`[suggested]` codify the impl-plan author's rule** ("self-counting screens run last, per
   instrument") in `h-mad/agents/*-author.md` — the class produced 12 of 12 delta musts this round.

## Open / Blocked Items

**doc-block-exec (this lane) — `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`**

- **5b gate NOT met.** design v1.110 / plan v1.105 / impl-plan v1.54 / spec v1.64 at `ccd8ebd`; gating
  freeze `bc4688e`; **r18 gating NOT dispatched** (#98). Suite `2574 passed` at `ccd8ebd`; precheck
  spec/design/plan PASS, impl-plan 11 hard (grammar) PINDRIFT 0.
- **Claim on `doc-block-exec`: RELEASED at this handoff** (`h_mad_state_write.py --release`, owner
  None). Claim before working. `phase=step5`, `codex_status=available`.
- **Claim on `hmad-audit-evidence-gate`: none** (owner None). Unchanged.
- **#102 — DONE at `ccd8ebd`** (suite red `b39d9dc..f6849bb`, fixed by the impl-plan re-pin).
- **#96 / #97 — DONE at `ccd8ebd`.** #101 — DONE.
- **Orchestrator errors this session:** #49v (shared string in the wrong quote style, C3 ii); the
  zsh `set --` precheck loop that measured nothing (caught, re-run); C2's claim that the SPEC asserted
  `__suppress_context__ False` (it never did — the impl-plan did). Prior ledger entries #88, #89, #93
  remain records.
- **Codex quota — OPEN** (no codex leg ran this session; four teammate authors + four doc-auditors only).
- **Standing "same model family" limit** — every leg this session was one family; the delta reviewers
  said so in their tails; the r18 gating codex legs are the second family. Unchanged.
- **agy leg — do not dispatch for gating until #77 addressed.** Unchanged.
- **#61 `COLLECT: MISSING` marker-name defect** — unchanged.
- **#48 `tools=N` / Effort figures unverifiable from repo** — unchanged; blocks #4/#13.
- **#42 INHERITED-UNVERIFIED register** — plan's register went 10 → 9 this round (the Setext member
  left by being RUN, v1.105). Carry the remaining 9.
- **#36 `tree delta: N` cannot signal agent writes** — unchanged; 88 untracked `.done` markers now
  (four delta-review markers added; deliberate, do not commit).
- **Evidence-gate corpus OUTSIDE the repo, not backed up** (`~/.h-mad-corpora/evidence-gate/`) — unchanged.
- **#27, #7, marker-aware reaping, #30, #32** — unchanged from the predecessor (see it for text).
- **#49 AUTOMATION SCOUT — SKIPPED this WRITE (`--skip-scout`, context ceiling)**; last census 09-05
  morning. Candidates from THIS session to append next time: suite re-run on the COMMITTED tree after
  any tooling commit that touches a pinned file; shared-string spelling taken from the documents, not
  typed; value-grep every NEW test name across all four documents at collection; self-counting screens
  run last per instrument; precheck loop must read the token, not a repeated line. Plus the
  predecessor's carried candidates (specimen-identity grep; per-commit lists pasted from `git log`;
  size gate reserves transport overhead; `-q -q` drops the summary; r17's five).
- **#9, #5, #8 P5 backlog** — unchanged. #5 is a foreign lane.
- **HemaSuite skill-candidate row handed over** — brief
  `HemaSuite/docs/handoffs/2026-09-04-main__wrapper-rc-row-is-probably-a-duplicate.md`, not re-checked.
  `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none`. Unchanged.
- **`.claude/agents/` CLOSED** — five agents at `h-mad/agents/`; the user-scope symlinks resolved to the
  edited files this session (every author obeyed the new rules — no `advisor()`, DONE-first, sliced
  reads; one design reopen stayed inside its context). Unchanged.
- **r15 sheet's false scope clause** — C5 in `…delta-decision-sheet.r15.md`; unchanged.

**Taken over THIS session — `**Handover-From:** HemaSuite · main · session cab14393` · `**Taken-Over-By:** skills · main · session adb05ac8 · 2026-09-05`**
(`docs/handoffs/2026-09-05-main__hmad-audit-loop-evidence-from-gateway-consolidation.md`; stamped + committed `7a56cb7`; `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`; task **#100**; no feature claim existed)

- **H1–H9 (nine h-mad proposals) + tooling defects A/B — status: owned here, NOT started.** Evidence
  in HemaSuite: `/Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/03-analysis/gateway-consolidation.audit-ledger.md`
  + `…audit-origins.jsonl` (both exist). Defect A premise VERIFIED (`handover_landed.py:107-116`);
  defect B premise VERIFIED (`h_mad_assemble_audit.py:453`). The brief's Next Step 5 ("sibling brief
  still unpicked") is STALE — that sibling was taken over 09-05 as #91.
- Overlaps `hmad-audit-evidence-gate` (#66/#91); fold-or-not is an open decision.

**Inherited — `**Handover-From:** HemaSuite · main · session f0b69d8d` · `**Taken-Over-By:** skills · main · session ca259110 · 2026-09-03`**
(`docs/handoffs/2026-09-03-main__hmad-audit-evidence-gate.md`; `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none`; feature `hmad-audit-evidence-gate`, phase 0, task #66)

- **Both original fixes — not started, unchanged since 09-03**: (1) move rejections out of the gated
  set; (2) evidence check in `h-mad/scripts/h_mad_audit_gate.py`; (3) tighten the contract; (4)
  mutation-test against the sender's corpus; (5) `[suggested]` agy-only `--passes N` gating.
- **Evidence corpus in the sender's scratchpad, not durable** — unchanged.

**Inherited — `**Handover-From:** HemaSuite · main · session 9d8394fb` · `**Taken-Over-By:** skills · main · session ee549bb1 · 2026-09-05`**
(`docs/handoffs/2026-09-05-main__audit-loop-never-runs-repo-suite.md`; folded into `hmad-audit-evidence-gate` as its THIRD defect, task #91; `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none`)

- **Phase 3–4 audit cycle never runs the project test suite** — unchanged. (This session's #102 is the
  same defect from the orchestrator's side: nobody ran the suite on the committed tree after #87.)

**Related lanes, not owned here**

- **`exec agy` lingers after its `result` event** — `docs/handoffs/2026-09-03-main__exec-agy-hang-after-report.md`,
  taken over by session `cd979362`. Unchanged. `repo: /Users/kimhawk/orca/skills · branch: main`.

## Context for Next Session

**Files touched this session:**
- `docs/02-design/features/doc-block-exec.design.md` (v1.110), `docs/01-plan/features/doc-block-exec.{plan,impl-plan,spec}.md` (v1.105 / v1.54 / v1.64) — by the four authors, committed `ccd8ebd`
- `docs/03-analysis/doc-block-exec.gating-decision-sheet.r18.md` (C2 at `f6849bb`, C3 at `bc4688e`)
- `docs/03-analysis/doc-block-exec.{design,plan,impl-plan,spec}.delta-review.r18.md` (new, committed with the batch)
- `docs/handoffs/2026-09-05-main__hmad-audit-loop-evidence-from-gateway-consolidation.md` (`**Taken-Over-By:**` stamp, `7a56cb7`)
- `docs/.bkit-memory.json` (claim taken then released; gitignored)
- scratchpad `r18_collection_crosscheck.md` (the collection checklist; not durable)

**Uncommitted changes:** none besides 88 untracked `.done` markers. `origin/main` in sync at `bc4688e`
before this handoff's commit.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
/handoff read
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"; hmad-dispatch env
python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature doc-block-exec --session-id <you>   # then --claim
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/ -q -p no:cacheprovider    # 2574 passed at ccd8ebd; ONE -q; bare python3 is 3.14, no pytest
for f in docs/02-design/features/doc-block-exec.design.md docs/01-plan/features/doc-block-exec.{plan,impl-plan,spec}.md; do tr '\n' ' ' < $f | /usr/bin/grep -oE -- '- v1\.[0-9]+' | tail -1; done   # v1.110 / v1.105 / v1.54 / v1.64
sed -n '/^- \*\*C3 /,$p' docs/03-analysis/doc-block-exec.gating-decision-sheet.r18.md    # the gating contract
```

**Related docs:**
- `docs/03-analysis/doc-block-exec.gating-decision-sheet.r18.md` — C2 (shared strings), C3 (post-batch record, gating facts)
- `docs/03-analysis/doc-block-exec.*.delta-review.r18.md` — what the fix round introduced
- `h-mad/SKILL.md` §"Teammate authors" (rules 1–4 all exercised this round)
- Commits this session: `7a56cb7` (takeover stamp), `f6849bb` (C2), `ccd8ebd` (batch), `bc4688e` (C3)
- Task ledger: #101 ✓ #102 ✓ #96 ✓ #97 ✓; **#98 next**; #100 taken over; #65 reproduced again
