# Handoff — doc-block-exec 5b: rounds fifteen and sixteen, codex returns, the assembler learns `--vh-tail`, and a second defect population opens

**Date:** 2026-09-05
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-05-main__doc-block-exec-rounds-twelve-to-fourteen.md (branch predecessor — every open item walked below), 2026-09-03-main__hmad-audit-evidence-gate.md (taken over by session `ca259110`; its Next Steps and Open Items read this session and re-emitted below under their origin), 2026-09-05-main__audit-loop-never-runs-repo-suite.md (inbound handover, read in full at session start, **NOT taken over** — no `Taken-Over-By:` stamp, re-emitted below and still pending)

## Session Summary

Two complete rounds at nine commits — `59cc2ad` → `6fc71ab`. **Round fifteen**: a four-leg delta pass
(union must **16**, six wrong published figures falsifying round fourteen's "none wrong" headline),
four author revisions, and gating on three phases where **codex returned mid-round** and matched the
teammate leg's four plan musts one-for-one — the arc's first cross-family agreement. Codex refused the
design and impl-plan prompts (`input_too_large`, 1 Mi chars), which was fixed at `af19d53`: the
assembler gained `--vh-tail N` and an oversize `HALT`. **Round sixteen**: revisions, then gating with
**two model families on every phase** for the first time — FAIL, union **21** — and the two surfaces
found **different populations**: the teammate legs' standing prose class (thinning; design fell 4→2),
and eleven codex musts that are **engineering defects in what the documents specify**, three of them
orchestrator-verified by direct run. The gate is not met; r17 owes both kinds of work. **Sixteen
orchestrator errors this session** (#49h–#49r), every one caught by an author or by reading raw output
against a verdict. Loop stopped by the operator's 80% context ceiling.

## Key Learnings

- **A freeze that touches no document is not a freeze that touches no measurement.** The assembler fix
  `af19d53`, chosen as r16's freeze, touched `h-mad/scripts` and `h-mad/tests` and thereby expired a
  blanket interval closure licensing ~70 plan readings, moved the suite floor (7→12 tests in one file),
  and moved an impl-plan AST sweep 22→23 — in a document whose author had already corrected one such
  instance and declared "no reading moved". Before naming a commit as a freeze, run the documents'
  own closure predicates against it, not just "are the four documents byte-identical".

- **Two model families find two populations.** Codex agreed with the teammate on prose defects (plan
  c86, 4/4) AND found a class no same-family auditor filed in sixteen rounds: substitution overlap
  logic that returns `Xc Xc` while reporting both counts 2 (found independently in design and
  impl-plan); `raise … from None` suppressing context rather than selecting the stated fallback; a
  NUL-bearing shell payload raising `ValueError: embedded null byte` with no verdict path; a bare `#`
  at `h-mad/SKILL.md:984` falsifying a guard-narrowing invariant. The standing limit was never only
  "will the same defects be found" — it was "will the same KIND be looked for".

- **Version History is ~36% of every document and was embedded verbatim, for the target AND every
  paired sibling.** That is what pushed prompts past 1,048,576 chars — the limit BOTH codex (server
  error) and agy (arg cap) enforce, while the assembler said "no limit via exec" and printed PASS.
  `--vh-tail 3` brought design 1,128,136→838,042 and impl-plan 1,053,882→765,333 with nothing lost:
  every auditor that needed an older entry read it via `git show`.

- **Every uninformative completion signal in one session.** A version bump is the FIRST thing an
  author writes (#49k — I committed while three authors were still writing). A hook's `Running:` set
  is not a liveness oracle (#49o — two legs declared dead were alive and slow; my re-dispatch's
  "write early" stub overwrote a completed report with a scorable false CLEAN for four minutes).
  `rc`, `EMPTY final message` and `tree delta` say nothing about whether an agent worked (#77 — agy
  ran 86 steps and died on `pytest`; codex's refusal carried an explicit `input_too_large` the
  wrapper flattened into the same shape). A committed blob is not the file you read minutes earlier
  (#49q — I pushed the -b agent's IN-PROGRESS partial under a commit message describing the
  original's report). **Only the author's own DONE, and the index blob read back before the
  message is written, are evidence.**

- **A line count is not a measure of change here.** Version History entries are single
  ~3000-character lines; `--stat` reported "1 insertion, 1 deletion" for a 2,066-character rewrite,
  and I used that to tell three running auditors not to re-read (#49m). Fixed-string presence checks
  on the specific claim, never `--stat`.

- **Three grammar-blind counts in one session.** Line-scoped `grep -c` missed two wrap-split members
  (12 vs 14, #49j); a needle without backtick allowance missed half the sites (2 vs 4, #49r); a
  chained `cd` made two pytest "controls" read one tree (#49h). Collapse newlines, admit inline-code
  delimiters, one control per invocation. And `ugrep` shadows `grep` in this shell — it threw
  `exceeds complexity limits` **four** times on ordinary regexes, each an empty result one step from
  becoming a finding.

- **A shared-facts sheet is a single point of failure for unmeasured claims as much as a single
  source of truth for measured ones.** "`dfae038` touched only `docs/handoffs/`" was never run; it
  propagated from one sheet line into eight surfaces and became a must in three documents (#49n).
  The sheet's own instruction — "your run outranks this sheet" — is what caught it, one surface
  downstream. Every clause of the form "X touched only Y" takes a command.

- **Two same-family legs on one freeze disagree in both directions.** The -b legs I called redundant
  found four musts the originals missed (one was #49n in a third document); the originals found
  things the -b legs did not. A second read has value without a second family.

- **The reopen introduces.** impl-plan reopened twice after DONE in r16 (each announced first, per
  the sheet); its two reopens produced two of r16 gating's four musts (self-reference screen hits in
  the reopen's own text; a freeze-scope clearance false a second time). A post-DONE edit must re-run
  every screen the edit's own new text can move.

## Next Steps

1. **r17 — write the sheet, then split the routing.** `docs/03-analysis/doc-block-exec.gating-decision-sheet.r17.md`.
   Freeze = HEAD after any tooling commit, **checked with the documents' own closure predicates**
   (`git diff --name-only 74e126f <freeze> -- h-mad handoff` and the impl-plan's `_SCANNED`
   corpora), not byte-identity alone. Carry r16's FACT 2 (three-clause freeze rule) and FACT 6, adding:
   a post-DONE reopen re-runs every screen its own text can move.
2. **r17(a) — the teammate class, to three authors** (design 2, plan 4, impl-plan 4 musts; spec none).
   Reports: `docs/02-design/features/doc-block-exec.design.audit.v96.teammate.md`,
   `docs/01-plan/features/doc-block-exec.plan.audit.v87.teammate.md`,
   `docs/01-plan/features/doc-block-exec.impl-plan.audit.v47.teammate.md`. Same protocol as r16.
3. **r17(b) — the codex class, VERIFY each before routing, then treat as DESIGN CHANGES.** Reports
   `…design.audit.v96.codex.md` (3), `…plan.audit.v87.codex.md` (2), `…impl-plan.audit.v47.codex.md` (6).
   Three already verified (`h-mad/SKILL.md:984` bare `#`; `raise … from None` semantics;
   `Popen(["bash","-c","true\x00"])` → `ValueError`). The overlap-span defect is in design AND
   impl-plan and may reach the spec's FR for substitution. Do not hand these to authors as prose
   repairs. A codex must that does not reproduce is a finding about codex.
4. **Assemble with `--vh-tail 3`** — `python3 ~/.claude/skills/h-mad/scripts/h_mad_assemble_audit.py --feature doc-block-exec --phase <p> --project-root /Users/kimhawk/orca/skills --cycle <N> --vh-tail 3`; cycles are **design c97 / plan c88 / impl-plan c48**. Dispatch codex via
   `hmad-dispatch exec codex <prompt> --sandbox read-only --timeout 1800 --out /tmp/codex_<p>_c<N>.md`
   and teammate `doc-auditor` by path, **one report path per agent, never shared**. Persist codex
   `--out` to `…audit.v<N>.codex.md` + `.done` before reading it.
5. **Before every commit of agent-written files**: all authors' DONE received; `git show :<path>`
   read back and its evidence/version line compared to what the message will claim; refuse if a
   path has a live writer. (#49k, #49o, #49q.)
6. **Owed from #71**: `h-mad/SKILL.md` step 5.5 should name `--vh-tail` as the first remedy for an
   oversize prompt; `hmad-dispatch exec` should grep its transcript tail for `turn/start failed` /
   `input_too_large` and emit a distinct token instead of the generic `EMPTY final message`.
7. **Fix the carry-forward displacement** (#65, unchanged from predecessor) — `handoff/scripts/handoff_paths.py`
   `carry-forward-sources` should return the branch's newest non-handover handoff in addition to
   any pending brief, not whichever sorts newest.

## Open / Blocked Items

**doc-block-exec (this lane) — `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`**

- **5b gate NOT met.** design v1.108 / plan v1.103 / impl-plan v1.52 / spec v1.62 at `09e9307`;
  r16 gating at `6fc71ab`: design 2+3, plan 4+2, impl-plan 4+6 (teammate+codex). Union 21. Two
  surfaces on every phase for the first time.
- **Claim on `doc-block-exec` UNCLAIMED** — `enter_autonomous`, owner `None`, verified at session
  start and never claimed. Re-verify with `h_mad_resume_decision.py` before claiming.
- **Codex quota — CLOSED.** Returned 2026-09-05 (early; was forecast 09-07 11:28). `codex_status=available`
  written. The pane pin answered `agent_prompt_blocked` while three `exec` legs ran — headless `exec`
  is unaffected and is the surface to prefer for gating.
- **Standing "same model family" limit — DISCHARGED for the plan, OPENED WIDER for everything.**
  Plan c86: codex 4/4 with teammate. r16: codex found a design-logic class no teammate leg filed.
  agy's four clean rounds were not measurements (#77, #79).
- **agy leg — do not dispatch for gating until #77 is addressed.** It ran 86 steps and died at 285s
  on a `pytest` it chose to run; its clean verdicts are indistinguishable from truncations.
- **SIXTEEN orchestrator errors this session** (#49h–#49r, tasks #69, #72–#75, #78, #80, #81) —
  open as rules to apply, not defects to fix. Species: scope ×4, grammar ×3, freeze ×2,
  completion-signal ×3, verifier ×1, measurement ×1, asserted-scope ×1, commit-blob ×1.
- **#61 `COLLECT: MISSING` marker-name defect** — unchanged since 09-05 predecessor.
- **#48 `tools=N` / Effort-block figures unverifiable from the repo** — unchanged. Blocks #4.
- **#13 evidence floor may be one call too low — MEASURE** — unchanged; blocked on #48.
- **#42 INHERITED-UNVERIFIED register** — unchanged (the `2748`/`2486` pair, CommonMark oracles,
  markdown-it-py corpus, OS carve-out probes, AC-6.4's `2675`). Codex plan c87 filed two musts in
  this territory: probe commands reference files absent from the tracked tree; `49 across 2 files`
  re-derives as `73 / 10`.
- **#36 `tree delta: N` cannot signal agent writes** — unchanged; 61+ untracked `.done` markers.
- **Evidence-gate corpus OUTSIDE the repo, not backed up** (`~/.h-mad-corpora/evidence-gate/`) — unchanged.
- **#27 deferred evidence check** — unchanged (`docs/03-analysis/hmad-audit-evidence-gate.measurement.md`).
- **#7 `docsections.py` `_fence_aware_end` dedupe** — unchanged; closes with 5e.
- **Marker-aware reaping for `exec`** — unchanged, deliberately not built.
- **#30 awk boundary fix HALF done** — unchanged.
- **#32 re-dispatch two agy legs round five did not complete** — stale after rounds 6–16; re-probe
  before acting; likely withdraw.
- **#49 AUTOMATION SCOUT — PARTIALLY RUN this WRITE.** Census 194/194 parsed; **15 open `yes` rows, 0 landed this session** (three gained live evidence: L1368 probe verb — #49l; L1370 carry-forward — #65; L1371 delta verb — four hand-dispatches). Appended 5 rows (one **LANDED** at `af19d53`: the assembler HALT + `--vh-tail`) and one dated reinforcement under L1368. Per-row source verification of the 15 still owed.
- **#9, #5, #8 P5 backlog** — unchanged. #5 (101 HemaSuite rows) is a foreign lane.
- **HemaSuite skill-candidate row handed over** — brief
  `HemaSuite/docs/handoffs/2026-09-04-main__wrapper-rc-row-is-probably-a-duplicate.md`, not re-checked.
  `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none`.
- **`.claude/agents/` remains CLOSED** — five agents at `h-mad/agents/`, user-scope symlink.
- **`.done` markers untracked** — deliberate; do not commit.
- **r15 sheet's false scope clause** — annotated as C5 in
  `docs/03-analysis/doc-block-exec.delta-decision-sheet.r15.md`; line 5 left as written per the
  sheet's own append-never-rewrite rule.

**Inherited — `**Handover-From:** HemaSuite · main · session f0b69d8d` · `**Taken-Over-By:** skills · main · session ca259110 · 2026-09-03`**
(`docs/handoffs/2026-09-03-main__hmad-audit-evidence-gate.md`; `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none`; feature record `hmad-audit-evidence-gate` in `docs/.bkit-memory.json`, phase 0, owner None)

- **Both fixes — not started, unchanged since 09-03.** (1) Move rejections out of the gated set —
  a rejection-only cycle destroys the streak by editing a gated file. (2) Add the evidence check to
  `h-mad/scripts/h_mad_audit_gate.py` — the gate scores bullets without checking a finding's quoted
  evidence exists. (3) Tighten the audit contract to make the check possible. (4) Mutation-test the
  gate change against the sender's corpus before shipping. (5) `[suggested]` whether agy-only
  `--passes N` consistency should be gated at all.
- **Evidence corpus lives in the sender's scratchpad and is not durable** — unchanged; copy before
  starting. Candidate merge target for the pending handover below — all three defects are "the gate
  scores documents and never checks reality".

**Inbound handover — PENDING, NOT TAKEN OVER — `**Handover-From:** HemaSuite · main · session 9d8394fb`**
(`docs/handoffs/2026-09-05-main__audit-loop-never-runs-repo-suite.md`; `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none`)

- **Phase 3–4 audit cycle never runs the project test suite** — premises re-verified this session
  (`h_mad_audit_gate.py` 407 lines, zero `subprocess|pytest|check_call|os.system`; `pytest` in
  `h-mad/SKILL.md` only at 5e/5f). **New evidence from the other side (#77):** an agy Phase-4
  auditor reached for `pytest` unprompted and the 285s dispatch timeout killed it. Any fix must
  budget for a ~2809-test suite. Decision still owed: take over (stamp `Taken-Over-By:` + claim) or
  leave pending. Left pending deliberately by two sessions now.

**Related lanes, not owned here**

- **`exec agy` lingers after its `result` event** — `docs/handoffs/2026-09-03-main__exec-agy-hang-after-report.md`,
  taken over by session `cd979362`. Unchanged. `repo: /Users/kimhawk/orca/skills · branch: main`.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_assemble_audit.py` (`--vh-tail`, oversize HALT, corrected advisory text) + `h-mad/tests/test_h_mad_assemble_audit.py` (+5 tests; suite 2552 passed)
- `docs/02-design/features/doc-block-exec.design.md` (v1.106 → v1.108)
- `docs/01-plan/features/doc-block-exec.plan.md` (v1.101 → v1.103)
- `docs/01-plan/features/doc-block-exec.impl-plan.md` (v1.50 → v1.52)
- `docs/01-plan/features/doc-block-exec.spec.md` (v1.61 → v1.62)
- `docs/03-analysis/doc-block-exec.{design,plan,impl-plan,spec}.delta-review.r15.md`, `…delta-decision-sheet.r15.md` (+C1–C5), `…gating-decision-sheet.r16.md`
- 12 gating reports: `…audit.v95.{teammate,teammate-b}.md`, `…v86.{teammate,codex}.md`, `…v46.{teammate,teammate-b}.md`, `…v96.{teammate,codex}.md`, `…v87.{teammate,codex}.md`, `…v47.{teammate,codex}.md`
- `docs/.bkit-memory.json` (`codex_status=available`, gitignored)

**Uncommitted changes:** none besides the untracked `.done` markers and this doc until committed.
`origin/main` at `6fc71ab`, 0/0.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
/handoff read
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"; hmad-dispatch env
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/ -q -p no:cacheprovider    # 2552 at 6fc71ab; bare python3 is 3.14, no pytest
for f in docs/02-design/features/doc-block-exec.design.md docs/01-plan/features/doc-block-exec.{plan,impl-plan,spec}.md; do grep -oE '^- v1\.[0-9]+' $f | tail -1; done   # re-derive, never trust a pin
```

**Related docs:**
- `h-mad/SKILL.md` §"Delta self-review", §"The four rules that are the ORCHESTRATOR's", §"Precheck before you dispatch"
- Commits this session: `59cc2ad` `7b182b0` `3f70eb3` (r15 revisions), `4c1c3a5` `b442a80` `7b9d174` (r15 gating; `b442a80` corrects `4c1c3a5`), `af19d53` (assembler), `09e9307` (r16 revisions), `6fc71ab` (r16 gating)
- Task ledger #63–#83 carries the round records, the sixteen orchestrator errors, and #82/#83 (the codex population and r17's split routing).
