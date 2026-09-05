# Handoff — doc-block-exec 5b: rounds twelve to fourteen, the delta pass, and six orchestrator errors

**Date:** 2026-09-05
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-04-main__doc-block-exec-round-twelve-and-decision-q.md (branch predecessor — every open item carried below), 2026-09-05-main__audit-loop-never-runs-repo-suite.md (inbound handover, read in full, **NOT taken over** — re-emitted below and still unclaimed), 2026-09-03-main__exec-agy-hang-after-report.md, 2026-09-03-main__hmad-audit-evidence-gate.md (both taken over by other sessions; their open items re-emitted below so the chain continues through this doc)

## Session Summary

Ran **three complete gating rounds** (twelve's revisions, thirteen, fourteen) plus **two delta
self-review passes**, on two surfaces, at four freezes — `1cbddb7` → `700c599` → `8c6539a` →
`b3be433` → `00b961f`. Every round FAILED its gate and every revision landed: design v1.101 →
**v1.106**, plan v1.96 → **v1.101**, impl-plan v1.45 → **v1.50**, spec v1.60 → **v1.61** (its first
revision since before round twelve). The exit gate is **not met** and cannot be met before
2026-09-07 11:28, when codex quota returns. The substantive result is that **the defect population
inverted**: rounds 6–13 were dominated by wrong or unexecuted numbers, and by round fourteen *not
one published figure was wrong in any of the four documents* — all nine musts were prose whose
referent had moved, which no screen this feature ships can detect.

## Key Learnings

- **The delta self-review pays for itself and should run every round.** Three delta passes, and in
  each one **every** must was fix-introduced by the previous round's own repairs, sitting in the
  paragraph that round's must rewrote. r13's delta found 2 musts already pushed to `main`; r14's
  found 6. A gating round would have found the same defects at roughly four times the cost.

- **The population inverted, and that is the arc's real signal.** Union must went 5 → 3 → 6 → 6 → 9,
  which reads as no progress — but the composition changed completely. Decision Q plus the delta
  pass drained the unexecuted-number class; what replaced it is *text that was true when written*.
  Both r14 auditors found those by reading, having first re-derived 150+ figures and every screen,
  control and probe byte-for-byte with zero discrepancies.

- **SIX orchestrator verification errors this session, in THREE distinct species.** They are not one
  mistake repeated: (a) **provenance** — a value attributed to a commit that does not touch the file
  (#58, #59); (b) **scope** — a series verified against its published values rather than its stated
  definition, head-vs-whole (#60); (c) **grammar** — a token counted without checking which language
  construct it sits in; two `pgid=<n>` hits were Python kwargs (#62). Each rule fixes only its own
  species. The generalisation that does hold: **a count is evidence only against another count taken
  at the same commit, over the same corpus, in the same grammar.**

- **The authors are a better verification surface than I am.** Three consecutive rounds ended with an
  author refuting a claim in my decision sheet, twice with two authors catching the same one
  independently and neither adopting it. That is the fresh-context design working — but the honest
  reading is that the orchestrator is the least reliable surface in the loop, and the sheets should
  say so rather than only this ledger.

- **`COLLECT: MISSING` is not evidence the auditor failed.** A complete 13.7K gating report was
  invisible to `collect-report` because its marker was written as `<report-basename>.done` instead
  of `<report>.done` — four missing characters. The agy leg on the same cycle got it right, so it
  fires per-instance and unpredictably. This is a **second** independent mechanism producing a false
  absence, alongside the TUI-capture one (#56); round twelve's `plan c83 no_report` is recorded in a
  *committed* Version History entry and may be either of them.

- **agy liveness must be scored on `hmad-dispatch env`'s `last=`, never on `read`.** The pane capture
  sat frozen for 20+ minutes on a spinner while `env` already reported `state=done last="340997"` —
  the correct answer to the computed probe. A watcher grepping the pane would have looped forever.

- **Four consecutive rounds of agy `PASS must=0 should=0` beside 12+ verified teammate musts.** Over
  r13–r14 agy returned clean on five of six legs (one `UNVERIFIED low_evidence`) while gating
  teammates found real, re-derived defects every time. Whatever that leg measures, it is not this
  document's defect population — and only the codex round can distinguish "agy is blind" from "one
  model family is blind".

- **An inbound handover filed under this branch's slug DISPLACES the branch predecessor in
  `carry-forward-sources`.** Measured while writing this doc: `latest --branch main` returned the
  09-05 handover, and my actual predecessor (`2026-09-04-…round-twelve-and-decision-q.md`) was **not
  in the list at all**. I had its items only because this session ran READ at start. A session that
  had not would have dropped the entire branch backlog with no error. New shape of the
  chain-drops-backlogs defect; see Next Step 6.

## Next Steps

1. **Round fifteen: delta self-review of `00b961f`, then gating.** Freeze `00b961f`. Three
   `doc-auditor` agents, ADVISORY, subject `git show 00b961f -- <doc>` plus the c94/c85/c45 reports.
   Report paths go under `docs/03-analysis/…delta-review.r15.md` — **deliberately outside the audit
   filename grammar**, because the codex ledger derives from `doc-block-exec.plan.audit.v<N>.<surface>.md`
   and a delta report named that way silently bumps it.
2. **Gating cycles are design c95 / plan c86 / impl-plan c46.** Assemble with
   `h_mad_assemble_audit.py`, assert `ASSEMBLE: PASS`, dispatch `doc-auditor` **by path** with
   `This pass is GATING`, run the three agy `audit-cycle` legs **sequentially** (one pinned pane —
   parallel cycles collide). Prove agy liveness first with a computed-answer probe scored on
   `hmad-dispatch env`'s `last=`.
3. **When codex returns 2026-09-07 11:28** — flip the status, then run **one real-codex round before
   stamping anything**:
   `python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json --feature doc-block-exec --set codex_status=available`
4. **If a round comes back clean on BOTH surfaces at ONE commit:** `h_mad_audit_gate.py … --gated`
   per phase, then `h_mad_wire_pin_gate.py … --feature doc-block-exec`, then 5c
   `git checkout -b feature/doc-block-exec`. Claim `doc-block-exec` first with plain `--claim` — it
   is still **unclaimed** (`enter_autonomous`, owner `None`).
5. **`df04e8e` is unpushed and is not this session's commit** — another session committed the inbound
   handover locally at 10:09. It goes out with this handoff's push; nothing else is owed on it.
6. **Fix the carry-forward displacement** (Key Learnings, last bullet). `carry-forward-sources`
   should return the branch's newest *non-handover* handoff **in addition to** any pending brief, not
   whichever file sorts newest. File against `handoff/scripts/handoff_paths.py`.

**The impl-plan precheck invocation, needed every round** (the eight PLACEHOLDER hits are output-line
grammar specimens; the `--allow` list is an INPUT, never inferred):

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_precheck_doc.py \
  docs/01-plan/features/doc-block-exec.impl-plan.md --phase impl-plan --root /Users/kimhawk/orca/skills \
  --allow 'stream: "<name>"' --allow 'os_error: "<text>"' --allow 'overlap: "<a>" "<b>"' \
  --allow '<key>=<bare>' --allow '<key>="<json-string>"' --allow 'pgid: "<n>"'
```

## Open / Blocked Items

- **doc-block-exec 5b — gate NOT met.** design v1.106 / plan v1.101 / spec v1.61 / impl-plan v1.50 at
  `00b961f`. Three gating rounds run this session, all FAIL. `repo: /Users/kimhawk/orca/skills ·
  branch: main · worktree: /Users/kimhawk/orca/skills`.
- **The claim on `doc-block-exec` is UNCLAIMED** — verified `enter_autonomous`, owner `None`, at
  session start and never claimed. Re-verify with `h_mad_resume_decision.py` before claiming.
- **Codex quota — blocked until 2026-09-07 11:28**; `codex_status` still `exhausted`. One switch, two
  effects: it also permits Claude to author 5d/5e production code.
- **THE STANDING LIMIT: every surface shares a model family with the authoring surface.** All nine
  gating auditors across three rounds volunteered it unprompted; none has been scored against a
  labelled corpus. Nothing gated by a teammate is settled until a real codex round runs.
- **INBOUND HANDOVER, PENDING AND UNCLAIMED** — `docs/handoffs/2026-09-05-main__audit-loop-never-runs-repo-suite.md`,
  **Handover-From:** HemaSuite · main · session `9d8394fb`. Read in full this session, **deliberately
  not taken over** (no `Taken-Over-By:` stamp), so it still appears in `pending-handovers`. The defect:
  h-mad's Phase 3–4 audit cycle never executes the project's test suite, so
  `tests/test_audit_phase_inline_summary_sync.py::test_real_features_synced` stayed red for 91+ cycles
  while every cycle scored clean — a test enforcing the audit loop's own invariant, which the audit
  loop never ran. `h_mad_audit_gate.py` is 407 lines with **zero** `subprocess`/`pytest`/`os.system`.
  The framing that matters: h-mad *does* run the suite, at 5e and 5f only; Phases 3 and 4 have no run
  in the protocol and no execution in the gate. `repo: /Users/kimhawk/orca/skills · branch: main ·
  worktree: none`. Its Next Step 3 asks whether to fold it into `hmad-audit-evidence-gate` — a
  judgement, not a conclusion.
- **`hmad-audit-evidence-gate` — two defects, not started** — brief
  `docs/handoffs/2026-09-03-main__hmad-audit-evidence-gate.md`, **Handover-From:** HemaSuite · session
  `f0b69d8d`, **Taken-Over-By:** session `ca259110`. The gate scores bullets without checking a
  finding's quoted evidence exists, and a rejection-only cycle destroys the streak by editing a gated
  file. `repo: /Users/kimhawk/orca/skills · branch: main`. Files: `h-mad/scripts/h_mad_audit_gate.py`,
  `h-mad/scripts/h_mad_assemble_audit.py` (output contract `:158`–`:176`). Its evidence corpus lives
  in a sender scratchpad and is **not durable**.
- **`exec agy` lingers after its `result` event — handed over, not started** — brief
  `docs/handoffs/2026-09-03-main__exec-agy-hang-after-report.md`, **Handover-From:** HemaSuite ·
  session `45db0187`, **Taken-Over-By:** session `cd979362`. Intermittent (2 of 29 dispatches);
  `agy exec rc=124` is printed for both a genuine timeout and a delivered-report case, so a
  coordinator gating on rc re-dispatches work already on disk. `repo: /Users/kimhawk/orca/skills ·
  branch: main · worktree: /Users/kimhawk/orca/skills`.
- **SIX orchestrator errors this session, three species** — tasks #51, #53, #58, #59 (closed by the
  forward correction in `b3be433`), #60, #62. #58 and #60 and #62 remain open as *rules to apply*,
  not as defects to fix.
- **`COLLECT: MISSING` marker-name defect** (#61) — a complete report was unreachable because the
  marker dropped `.md`. **Two things owed**: re-check round twelve's `plan c83 no_report` against this
  mechanism *and* against #56's TUI-capture mechanism, because a committed Version History entry
  records that leg as having produced no verdict; and make `collect-report` name the file it actually
  waited for.
- **#48 `tools=N` and every Effort-block figure is UNVERIFIABLE from the repo** — verdict files live
  in `/tmp` and are never committed. Blocks #4 (the thinking-per-call ratio). Unchanged.
- **#13 evidence floor may be one call too low — MEASURE, do not raise it.** Blocked on #48.
- **INHERITED-UNVERIFIED register (#42)** — the `2748`/`2486` pair at `b7d0d77` (needs a checkout);
  the plan's 263/76/0 and 268/76/0 CommonMark oracles; the markdown-it-py 14-case corpus; the five
  OS/runtime carve-out probes; **AC-6.4's `2675` predicate — ten variants tried, none reproduces it**,
  and v1.46 correctly withdrew the word `verified` while keeping the invariance (1450/1450/1450).
- **`tree delta: N` cannot signal agent writes in this repo (#36)** — now **61** untracked `.done`
  markers make its baseline never 0.
- **Evidence-gate corpus lives OUTSIDE the repo and is not backed up** — `~/.h-mad-corpora/evidence-gate/`,
  66 files, re-verified 2026-09-04.
- **#27 deferred evidence check** — measured and refused; no span-occurrence rule discriminates.
  `docs/03-analysis/hmad-audit-evidence-gate.measurement.md`, `109a02a`. Unchanged.
- **#7 `docsections.py` `_fence_aware_end` dedupe** — unchanged, not started. Closes with 5e.
- **Marker-aware reaping for `exec`** — owed, deliberately not built. Unchanged.
- **#30 the awk boundary fix was HALF done** — `\b` closed for `today`, trailing `[,)]` left on
  `measured`. Unchanged, not started.
- **#32 re-dispatch the two agy legs round five did not complete** — likely stale after rounds 6–14;
  re-probe before acting.
- **#49 AUTOMATION SCOUT DEFERRED** — census measured (12 open yes / 12 maybe of 179), reconciliation
  NOT run. Unchanged.
- **#9, #5, #8 P5 backlog** — unchanged, not started. #5 (101 HemaSuite rows) is a foreign lane.
- **A HemaSuite skill-candidate row was HANDED OVER and remains theirs** — brief at
  `HemaSuite/docs/handoffs/2026-09-04-main__wrapper-rc-row-is-probably-a-duplicate.md` (`f5afb219`).
  Not re-checked. `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none`.
- **`.claude/agents/` remains CLOSED** — five agents tracked at `h-mad/agents/`, user-scope symlink.
- **61 untracked `.done` markers** — deliberate, do not commit.

## Context for Next Session

**Files touched this session:**
- `docs/02-design/features/doc-block-exec.design.md` (v1.101 → v1.106)
- `docs/01-plan/features/doc-block-exec.plan.md` (v1.96 → v1.101)
- `docs/01-plan/features/doc-block-exec.impl-plan.md` (v1.45 → v1.50)
- `docs/01-plan/features/doc-block-exec.spec.md` (v1.60 → v1.61)
- 12 audit reports under `docs/01-plan/features/` and `docs/02-design/features/` (cycles 93/94, 84/85, 44/45, both surfaces)
- 6 delta-review reports under `docs/03-analysis/` (r13, r14)

**Uncommitted changes:** none besides the 61 `.done` markers (and this doc until committed).
`df04e8e` (another session's inbound-handover commit) is committed but unpushed.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
/handoff read
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"; hmad-dispatch env   # agy pin; score liveness on last=, never on read
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/ -q                 # bare python3 is 3.14, no pytest
grep -oE '^- v1\.[0-9]+' docs/02-design/features/doc-block-exec.design.md | tail -1   # re-derive, never trust a pin
```

**Related docs:**
- `h-mad/SKILL.md` §"Delta self-review", §"Teammate audit leg", §"Never gate on one audit pass",
  §"Close the class, never the instance"
- Commits this session: `1cbddb7` (r12 revisions), `700c599` (r13 delta), `8c6539a` (r13 gating),
  `b3be433` (r14 delta), `00b961f` (r14 gating), `df04e8e` (inbound handover, not mine)
- Decisions G–Q live in the session task list (#35, #39–#48) and in the commit messages from
  `6f0ee85` onward.
