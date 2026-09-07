# Handoff — doc-block-exec COMPLETE through Phase 7; the branch is done, the backlog is not

**Date:** 2026-09-07
**Branch:** `feature/doc-block-exec` — clean, `0/0`, HEAD `c5e5da9`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-07-feature-doc-block-exec__task4-closed-5e-gates-owed.md (branch predecessor, read in full at this session's start and reconciled below)

> **NOT superseded, deliberately:** `2026-09-05-main__audit-loop-never-runs-repo-suite.md` and
> `2026-09-05-main__hmad-audit-loop-evidence-from-gateway-consolidation.md` are still returned by
> `carry-forward-sources`. This session did **not** read them, so naming them would retire them on a
> false claim and hide them from every future WRITE. Their items survive as #91 and #100 below.

## Session Summary

`doc-block-exec` is **complete through Phase 7** and pushed. The session opened with Task 4's two 5e
gates owed and closed with the feature archived: Task 5 shipped (step 0 + RED + GREEN), 5f verified
the wire registry, 5g re-stamped D3 and disarmed the TDD gate, Phase 6a returned 100.00% (49/49),
6a-prime returned `READY_TO_MERGE`, and Phase 7 wrote the report and archive. Ten commits, all
pushed, tree clean, claim released. The feature backlog is done; the **tooling** backlog grew by
four defects this session found in H-MAD itself.

## Key Learnings

- **A gate's zero is only a measurement if the instrument can read that input.** `EVIDENCE: NONE
  tools=0` fired on a codex review that verifiably read the tree — the gate parses agy NDJSON,
  codex logs are `codex-text` (#154). `PHASE7: match_rate_unreadable` fired on an analysis stating
  its rate correctly — the parser takes `match rate:` but not the `match_rate=` its own template
  emits (#155). Both fail closed, both cost a cycle, because the blocker text names a real hazard
  that is not the one present.
- **My own control for that was mis-scoped and nearly hid it.** Running the evidence gate on an
  *agy* log returned `tools=5` and I read it as "the gate works" — it establishes only that the gate
  works on agy logs. A control must vary the thing under suspicion, here the log FORMAT.
- **Briefing a reviewer with the answer removes its reason to read.** Same 740 KB prompt:
  `tools=12` with no appendix, `tools=0` once handed the confirmed conclusion and told not to
  re-litigate — and the blind run still wrote 2154 fluent bytes (#153).
- **One review pass would have shipped a defect.** 6a-prime round 1 found the key-validity policy
  duplicated; round 2, on the fixed tree, found the code right and the *plan* stale; round 3 cleared
  it. Each round found what the previous structurally could not.
- **An unlanded mutation reports as a kill — from my own hand.** Verifying the 6b fix, my first
  API-side mutation did not match its target and the pin "passed" against an unmutated tree. Redone
  with a landing assertion, both call sites red it.
- **Two dispatches that look independent can share a file.** The gap analysis ran concurrently with
  the 6b fix that edits the module it imports, measured a torn tree, read `13 failed`, and marked a
  satisfied AC as failed — which would have published `97.96%` instead of `100.00%`.
- **A wrong-file zero reads exactly like an absence, twice.** I grepped `h-mad/bin/hmad-dispatch.sh`
  (it is under `scripts/`) and got a clean zero; later I grepped `test_docsections.py` for
  `test_docsections_has_no_second_bounder` (it is in `test_h_mad_doc_block_exec.py:387`) and nearly
  filed a fabricated-citation finding against an author for a name already in the document 11 times.

## Next Steps

1. **Merge `feature/doc-block-exec` to `main`.** The feature is closed and pushed; nothing here
   blocks it. `git log --oneline main..feature/doc-block-exec` is 10 commits.
2. **#111 — remove the merged tooling worktree**, still present:
   `git worktree remove ../skills-hmad-gate && git branch -d feature/hmad-class-scored-gate`
3. **Fix the two false-zero gates**, both one-line-ish and both filed with the remedy:
   #154 (`h_mad_review_evidence.py` → `UNREADABLE reason=unsupported_format` on codex-text, never
   `tools=0`) and #155 (`h_mad_phase7_preconditions.py:31` → widen `_RATE` to `match[\s_]*rate`).
4. **#153 — state the verdict line in `references/agy-architectural-reviewer-prompt.md`** as the last
   line, alone, in the shape `h_mad_extract_verdict.py` accepts. Three dispatches, three misses.
5. **#152 — `h_mad_extract_verdict.py` refuses a prose-only `DONE_WITH_CONCERNS`**; either the
   verifier prompt states the required shape or the extractor accepts prose.
6. **#100 and #91 — the two taken-over briefs**, still not started. Read them before the next WRITE
   or they leave the chain unmentioned.

## Open / Blocked Items

**doc-block-exec — `repo: /Users/kimhawk/orca/skills · branch: feature/doc-block-exec · worktree: none (main)`**

- **CLOSED THIS SESSION**, so the next reader does not re-check them: Task 4's 5e revert test and
  anti-gaming verify (#148/#149) · Task 5 entire (#115) · 5f (#119) · 5g (#120) · D3 (#151, `31 → 11`,
  noise floor green) · the OPEN-DECISION at impl-plan:2894 (#117, shared predicate `92ae93a`,
  recorded `fb0dc15`) · #16 docsections dedupe · #49 automation scout (ran, `d61dd93`).
- **#142 — D2 residual**, unchanged: nothing detects a parked `.json.pending` spec never moved back.
  Exercised successfully this session, so the convention works; the detector is still absent.
- **#146 — now THREE orchestrator errors in §D11**, not two. The new one: `d.md --heading --help`
  makes `--help` a VALUE is FALSE — measured, it returns `BAD_ARGS "argument --heading: expected one
  argument"`, byte-identical to the control `d.md --heading` with nothing after it.
- **#145 AC-1.8 spec debt** — over-broad universal, unrouted since spec v1.63, now five rounds.
- **#126 heartbeat that does not beat** — OPEN, diagnosed to `h_mad_state_write.py:286`.
- **#129 partition-parts** · **#105 self-counting screens** — owed to `measurement-discipline.md`.
- **#152 · #153 · #154 · #155 — four tooling defects filed this session**, all one family: an output
  contract a prompt never spells, or a gate reading the wrong instrument.
- **#100 taken-over H1–H9 brief** — unchanged, not started. `repo: /Users/kimhawk/orca/skills ·
  branch: main · worktree: none`. **Handover-From:** HemaSuite · main · session cab14393.
- **#91 inherited** — "Phase 3–4 audit cycle never runs the project test suite", a skill defect.
  **Handover-From:** HemaSuite · main · session 9d8394fb. Unchanged.
- **#111 tooling worktree** — `../skills-hmad-gate @ feature/hmad-class-scored-gate` still present.
- **#112 · #48 · #42 · #77 · #27 · #20 · #9/#5/#8 · #143** — unchanged. (#7 closed with 5e as #16.)
- **Evidence-gate corpus** at `~/.h-mad-corpora/evidence-gate/` — outside the repo, not backed up.
- **Codex quota** — did not bind; ~10 dispatches all completed. `codex_status: available`.

**Related lanes, not owned here:** HemaSuite `#18 gateway-consolidation`, HALTED by the operator.

## In-Flight Processes

**None.** Every dispatch this session completed and was reaped; `pgrep` for
`hmad-dispatch|pytest|codex exec` returns nothing at write time.

## Context for Next Session

**Files touched this session:** `h-mad/scripts/h_mad_doc_block_exec.py` ·
`h-mad/tests/test_h_mad_doc_block_exec.py` · `h-mad/tests/test_h_mad_collect_report_docs.py` ·
`h-mad/tests/mutation-specs/doc_block_exec{,_wire}.json` · `h-mad/SKILL.md` ·
`docs/01-plan/features/doc-block-exec.impl-plan.md` · `docs/03-analysis/doc-block-exec.analysis.md` ·
`docs/04-report/features/doc-block-exec.report.md` · `docs/skill-candidates.md` ·
`docs/archive/2026-09/doc-block-exec/` (6 files)

**Uncommitted changes:** none, besides the 88 untracked `.done` markers (do not commit).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout feature/doc-block-exec          # c5e5da9, clean, 0/0
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"; hmad-dispatch env
# the feature is CLOSED — no claim needed. Next action is the merge, or the tooling backlog.
```

**Verification state at closure, all re-derived at `4ecc4c4`:** full h-mad suite `2792 passed / 0
failed` · gap analysis `100.00% (49/49)` · 6a-prime `READY_TO_MERGE` · `WIREREG: PASS 14/14` ·
mutations `ALL_CAUGHT 91/91` and `8/8` · `ANCHORS_OK specs=42 mutations=526 drifted=0`.
Note the suite figure is **h-mad-scoped**; the repo-root run reads `3057 passed` because it collects
sibling projects. Different corpus, not growth.

**Related docs:**
- `docs/04-report/features/doc-block-exec.report.md` — the Phase 7 report; its "What the 5e gates
  actually established" section is the part worth reading, not the verification table.
- `docs/03-analysis/doc-block-exec.analysis.md` — carries two bracketed corrections recording the
  torn-tree measurement rather than hiding it.
