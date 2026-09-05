# Handoff — doc-block-exec: #87 tooling batch landed, r18 decision sheet written at `cac6edc`, authors NOT yet dispatched; one inbound handover pending

**Date:** 2026-09-05
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-05-main__doc-block-exec-round-seventeen.md (branch predecessor — read in full at resume; every open item walked below), 2026-09-03-main__hmad-audit-evidence-gate.md (taken over 09-03 by `ca259110`; items carried through two predecessors and re-emitted below — not re-read this session), 2026-09-05-main__audit-loop-never-runs-repo-suite.md (taken over 09-05 by `ee549bb1`, folded into `hmad-audit-evidence-gate`; re-emitted below — not re-read this session)

## Session Summary

Resumed from the round-seventeen handoff (session d16ef45c, ~4 h). Two deliverables, both committed and
pushed: (1) the **#87 tooling batch** at `b39d9dc` — `hmad-dispatch exec` surfaces codex's
`input_too_large` as a distinct `INPUT_TOO_LARGE` line and stops laundering it into `EMPTY final
message` + `tree delta`; the assembler reserves 64 chars of boundary headroom (a real gap: codex counts
the 30-char dispatch boundary); every "exec is uncapped" claim in `h-mad/` corrected; the implementer
prompt's ImportError/AttributeError rule scoped to `wiring` tasks; all five `h-mad/agents/*.md` forbid
`advisor()`, mandate sliced reads, DONE-first, assert-before-write; suite 2552 → **2574**. (2) the
**r18 decision sheet** at `34d00a8`, freeze `cac6edc`, with every published census re-run per commit
(#49t). The census pass found that **`b39d9dc` had deleted the bare `#` in SKILL.md that three
documents enumerate as the single live titleless-heading specimen** — the operator chose "keep the
repair, accounting → N=0" (task #99, sheet FACT 3). Stopped at the 80% context line BEFORE
dispatching the r18 authors; that is the whole of the next session's first move.

## Key Learnings

- **A tooling commit that passes every census predicate can still delete a corpus line the
  documents enumerate BY CONTENT.** `b39d9dc` checked the `h-mad`/`handoff`/`*.py` closures and the
  bare `#` removal was on the handoff's own to-do; design:353, plan:3046/3212 and impl-plan:1646–1656
  treat that line as the probe's one `new_only` member (`titleless=1`). Before deleting a line from a
  measured corpus, grep the four documents for its identity, not only for the census commands.
- **Paste the per-commit list from `git log <a>..<b>`, never type it.** My FACT 1 named three commits
  since `fa64031`; there were six — a handoff commit hid in the first column and another session
  pushed two commits (an inbound handover brief) to this branch mid-session. Sheet C1.
- **codex `exec` counts the wrapper's 30-char dispatch boundary against its 1,048,576-char limit**
  (1,111,059-char file refused as `actual_chars` 1,111,089). A size gate reserves the transport's own
  overhead. The old `len(text) > MAX` passed the last 30 chars of room.
- **`pytest -q -q` drops the `N passed` line**; exit 0 alone is then the only signal, which "score on
  the summary, never `$?`" forbids. One `-q`.
- **A pre-named freeze sha goes stale in one commit.** `b39d9dc` was named as the r18 freeze and
  superseded by a docs-only commit that an unscoped `git ls-files` counts. The freeze is `git rev-parse
  HEAD` when the sheet is written, and the authors are told THAT sha plus the actual HEAD (C37).
- **The value-grep ownership table works and is cheap** (one `for` loop, newline-collapsed, `grep -oF`).
  It confirmed the plan's `81 mutations` ×2 must, found `(?=` in NO document (the lookahead form is
  genuinely new text), and gave measured zeros where r17's "—" cells hid two musts. Spellings the grep
  could not confirm are listed in the sheet rather than reported as absent.
- **Mutation-test the guard in every direction it has, not two.** The refusal guard had three
  (neutered grep / unconditional / unscoped-to-prior-log); each mutation was killed by exactly the
  tests it should have been and no other.

## Next Steps

1. **Read the r18 sheet** — `docs/03-analysis/doc-block-exec.gating-decision-sheet.r18.md`, FACT 1
   (what moved, per commit), FACT 3 (the specimen decision — operator confirmed "keep the repair"),
   FACT 8 (ownership table), Corrections C1. Freeze for the authors: **`cac6edc`**; actual HEAD at
   dispatch: whatever `git rev-parse HEAD` says (this handoff's commit will be past `34d00a8`).
2. **Claim, then dispatch the four r18 authors in parallel** (tasks #96, #97) — `Agent(subagent_type:
   "design-author" | "plan-author" | "implplan-author" | "spec-author", prompt: …)`. Each prompt names:
   the sheet path, the reports (`…design.audit.v97.{teammate,codex}.md`,
   `…plan.audit.v88.{teammate,codex,teammate-b}.md`, `…impl-plan.audit.v48.{teammate,codex}.md`), the
   freeze `cac6edc` AND the actual HEAD, the author's rows from FACT 8, and — restated verbatim, because
   agent definitions may be cached — no `advisor()`, sliced reads (≤ ~400 lines per `Read`), the
   `<ROLE>: DONE version=v1.N` line FIRST, assert-before-write. Rule ownership explicitly before any
   successor; a "Prompt is too long" notification is recoverable (SKILL.md §Teammate authors).
3. **Collect on DONE lines + `git show :<path>`** (FACT 6/7); delta self-review the diff (#11) —
   the r17 pattern was ~1/3 of authors' fixes needing a correction, so budget for C-entries.
4. **Freeze the batch commit, then gate** (task #98): design **c98** / plan **c89** / impl-plan
   **c49**, `--vh-tail 3`, codex via `hmad-dispatch exec codex … --sandbox read-only --timeout 1800`
   backgrounded with `--log` (it now HALTs `oversize` and reports `INPUT_TOO_LARGE` distinctly), plus a
   `doc-auditor` teammate per phase told freeze + HEAD. No agy gating leg until #77.
5. **Inbound handover NOT taken over** — `docs/handoffs/2026-09-05-main__hmad-audit-loop-evidence-from-gateway-consolidation.md`
   (`**Handover-From:** HemaSuite · main · session cab14393`; H1–H9 + two tooling defects from a
   99-cycle design audit; landed as `f81f75e`/`55b2371` while this session was mid-work).
   `pending-handovers` reports it; the next resume's Step 3.5 decides. It overlaps
   `hmad-audit-evidence-gate` (#66/#91) — read it before touching that feature.
6. **#65 carry-forward displacement** — this WRITE reproduced the r17 observation only partially:
   `carry-forward-sources --branch main` printed THREE handover briefs and NOT the branch predecessor
   `…round-seventeen.md` (which `latest --branch main` does return). Fix `handoff/scripts/handoff_paths.py`.
7. **#96(g) remaining half** — the impl-plan states why Task 2's first RED is `AttributeError` by
   construction and cites `h-mad/references/codex-implementer-prompt.md` (tooling half landed).

## Open / Blocked Items

**doc-block-exec (this lane) — `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`**

- **5b gate NOT met.** design v1.109 / plan v1.104 / impl-plan v1.53 / spec v1.63 at `cb4fe99`;
  r17 gating `fa64031` FAIL on every phase (union 15) + plan c88 `-b` must 1 (converges). r18 sheet
  written; **r18 revisions NOT started**.
- **Claim on `doc-block-exec`: RELEASED at this handoff** (`h_mad_state_write.py --release`, owner now
  None). Claim before working. `phase=step5`, `codex_status=available`.
- **Claim on `hmad-audit-evidence-gate`: none** (owner None; released by the r17 session).
- **#99 operator decision — DONE ("keep the repair").** Authors act on sheet FACT 3.
- **#87 — DONE at `b39d9dc`.** Owed follow-through: none in tooling; documents re-stamp figures per
  sheet FACT 1.
- **#90 — DONE (codified) at `b39d9dc`.**
- **Probes committed** at `fbc2ea0`; at HEAD the 09-04 probe reads TRACKED `files=30 both=292
  old_only=82 new_only=0`, GLOB `files=35 both=297 new_only=0`, `titleless=0`. markdown-it-py claims
  still measured at 2.2.0; 4.2.0 venv unreconstructable. r18 debt: five grammar-probe cases (r17 C20).
- **Codex quota — OPEN and used** (one live probe this session; three legs in r17).
- **Standing "same model family" limit** — plan settled (c86, c88); design/impl-plan still find
  disjoint populations across families. Unchanged.
- **agy leg — do not dispatch for gating until #77 addressed.** Unchanged.
- **Orchestrator errors this session:** the specimen deletion (sheet FACT 3; lesson above), the
  three-vs-six commit attribution (sheet C1), the `-q -q` summary suppression. Prior session's #88,
  #89, #93 remain open ledger entries (records, not work).
- **#61 `COLLECT: MISSING` marker-name defect** — unchanged.
- **#48 `tools=N` / Effort figures unverifiable from repo** — unchanged; blocks #4/#13.
- **#42 INHERITED-UNVERIFIED register** — plan's register 10 members; r18 routes the status
  contradiction (sheet FACT 5). Carry.
- **#36 `tree delta: N` cannot signal agent writes** — unchanged; 84 untracked `.done` markers.
- **Evidence-gate corpus OUTSIDE the repo, not backed up** (`~/.h-mad-corpora/evidence-gate/`) —
  unchanged.
- **#27 deferred evidence check** — unchanged.
- **#7 `docsections.py` `_fence_aware_end` dedupe** — unchanged; closes with 5e.
- **Marker-aware reaping for `exec`** — unchanged, deliberately not built.
- **#30 awk boundary fix HALF done** — unchanged.
- **#32 re-dispatch two agy legs round five** — stale; likely withdraw; unchanged.
- **#49 AUTOMATION SCOUT — SKIPPED this WRITE (`--skip-scout`, context budget)**; last census 09-05
  morning (194/194 parsed, 15 open `yes` rows). Candidates from THIS session to append: grep the four
  documents for the identity of any line deleted from a measured corpus (specimen lesson); paste
  per-commit lists from `git log`; a size gate reserves transport overhead; `-q -q` drops the summary.
  Plus r17's five carried candidates (spelling-complete value sweep; census-command enumerator;
  author-definition rules — now SHIPPED at `b39d9dc`, reconcile that row; DONE-first contract — SHIPPED;
  stale "—" cell check).
- **#9, #5, #8 P5 backlog** — unchanged. #5 is a foreign lane.
- **HemaSuite skill-candidate row handed over** — brief
  `HemaSuite/docs/handoffs/2026-09-04-main__wrapper-rc-row-is-probably-a-duplicate.md`, not re-checked.
  `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none`. Unchanged.
- **`.claude/agents/` remains CLOSED** — five agents at `h-mad/agents/`, user-scope symlinks verified
  this session to resolve to the edited files (byte-identical). Unchanged.
- **`.done` markers untracked** — deliberate; do not commit.
- **r15 sheet's false scope clause** — C5 in `…delta-decision-sheet.r15.md`; unchanged.

**Inherited — `**Handover-From:** HemaSuite · main · session f0b69d8d` · `**Taken-Over-By:** skills · main · session ca259110 · 2026-09-03`**
(`docs/handoffs/2026-09-03-main__hmad-audit-evidence-gate.md`; `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none`; feature `hmad-audit-evidence-gate`, phase 0, THREE defects, task #66)

- **Both original fixes — not started, unchanged since 09-03**: (1) move rejections out of the gated
  set; (2) evidence check in `h-mad/scripts/h_mad_audit_gate.py`; (3) tighten the contract; (4)
  mutation-test against the sender's corpus; (5) `[suggested]` agy-only `--passes N` gating.
- **Evidence corpus in the sender's scratchpad, not durable** — unchanged.

**Inherited — `**Handover-From:** HemaSuite · main · session 9d8394fb` · `**Taken-Over-By:** skills · main · session ee549bb1 · 2026-09-05`**
(`docs/handoffs/2026-09-05-main__audit-loop-never-runs-repo-suite.md`; folded into `hmad-audit-evidence-gate` as its THIRD defect, task #91; `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none`)

- **Phase 3–4 audit cycle never runs the project test suite** — unchanged since the r17 handoff
  (premises verified at `fbc2ea0`; Next Steps and the concurrent-suite trap as recorded there).

**Inbound, NOT taken over — `**Handover-From:** HemaSuite · main · session cab14393`**
(`docs/handoffs/2026-09-05-main__hmad-audit-loop-evidence-from-gateway-consolidation.md`, commits
`f81f75e`/`55b2371`; `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none`)

- **Pending in `pending-handovers`.** Not read beyond its header and summary this session (budget).
  H1–H9 + two tooling defects from the 99-cycle gateway-consolidation design audit; overlaps #66/#91.
  The next resume's Step 3.5 claims or declines it.

**Related lanes, not owned here**

- **`exec agy` lingers after its `result` event** — `docs/handoffs/2026-09-03-main__exec-agy-hang-after-report.md`,
  taken over by session `cd979362`. Unchanged. `repo: /Users/kimhawk/orca/skills · branch: main`.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/hmad-dispatch.sh` (`_codex_input_too_large`, `INPUT_TOO_LARGE` branch, codex `pre_lines`), `h-mad/scripts/h_mad_assemble_audit.py` (`DISPATCH_OVERHEAD_CHARS`, `prompt_oversize`)
- `h-mad/SKILL.md` (exec-path paragraph, step 5.5, bare `#` removed, §Teammate authors orchestrator rules), `h-mad/references/agent-substrate.md`, `h-mad/references/codex-implementer-prompt.md` (:52)
- `h-mad/agents/{design-author,plan-author,implplan-author,spec-author,doc-auditor}.md`
- `h-mad/tests/test_hmad_dispatch_exec.py` (+4), `h-mad/tests/test_h_mad_assemble_audit.py` (+3), `h-mad/tests/test_h_mad_agent_definitions.py` (new, 15 collected)
- `docs/03-analysis/doc-block-exec.gating-decision-sheet.r18.md` (new; C1 appended)
- `docs/learnings.md` (+4 rows), `docs/.bkit-memory.json` (claim released; gitignored)

**Uncommitted changes:** the r18 sheet's C1 edit and `docs/learnings.md` (+2) are committed alongside
this doc; otherwise none besides the 84 untracked `.done` markers. `origin/main` in sync at `34d00a8`
before this handoff's commit.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
/handoff read
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"; hmad-dispatch env
python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature doc-block-exec --session-id <you>   # then --claim
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/ -q -p no:cacheprovider    # 2574 at b39d9dc; ONE -q; bare python3 is 3.14, no pytest
for f in docs/02-design/features/doc-block-exec.design.md docs/01-plan/features/doc-block-exec.{plan,impl-plan,spec}.md; do tr '\n' ' ' < $f | /usr/bin/grep -oE -- '- v1\.[0-9]+' | tail -1; done   # re-derive, never trust a pin
git log --oneline fa64031..HEAD    # paste, never type, the commit list into any sheet
```

**Related docs:**
- `docs/03-analysis/doc-block-exec.gating-decision-sheet.r18.md` — the r18 contract for the authors
- `docs/03-analysis/doc-block-exec.gating-decision-sheet.r17.md` — C22/C24 (author overflow), C32–C40 (verified findings)
- `h-mad/SKILL.md` §"Teammate authors" (new orchestrator rules), §"Never gate on one audit pass"
- Commits this session: `b39d9dc` (#87), `cac6edc` (learnings), `34d00a8` (r18 sheet)
- Task ledger #95 ✓ #87 ✓ #90 ✓ #99 ✓; #96 #97 #98 next; #65 reproduced again
