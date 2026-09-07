# Handoff — doc-block-exec merged, the H-MAD tooling backlog drained, and two gates that never existed (7f, #91)

**Date:** 2026-09-07
**Branch:** `main` — clean, `0/0`, HEAD `c0ff86a`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-07-feature-doc-block-exec__feature-complete-through-phase7.md (resumed from at session start; every Next Step in it is closed below), 2026-09-06-main__doc-block-exec-5b-exit-and-hmad-class-gate.md (branch predecessor, read in full, every open item walked below), 2026-09-05-main__audit-loop-never-runs-repo-suite.md (the #91 brief — read in full and now IMPLEMENTED), 2026-09-05-main__hmad-audit-loop-evidence-from-gateway-consolidation.md (the #100 brief — read in full; defects A and B fixed, H1–H9 still open)

## Session Summary

Resumed on `feature/doc-block-exec`, merged it (`8487593`, 53 commits), then drained the H-MAD
tooling backlog it had surfaced: **22 commits, all pushed**. Ten defects closed with tests and
mutation rows (#65 #77b #100A #100B #48 #142 #126 #143 #146 #152–#155 #129/#105), two gates written
that had never existed — **Phase 7f**, the merge step, and **#91**, the audit gate's first execution
path — the Phase-7c archive completed for the closed feature, and the #5 census handed over to
HemaSuite. Two fresh-context review rounds returned **12 and 19 findings on batches already verified
green**, three of them CRITICAL and two of those caused by my own earlier fixes. Final gates:
h-mad **2920 passed**, handoff **281 passed**, anchors **622/622**, every mutation spec `ALL_CAUGHT`.

## Key Learnings

- **A green batch is the INPUT to a fresh-context review, never its substitute.** Two rounds, twelve
  then nineteen findings, on trees where the suite, the mutations and the anchors were all clean. The
  reviewer read each file's own doctrine against my change, tried the CLI with hostile keys, and
  asked what the assembler appends — none of which a test I author would ask.
- **A fix for one defect can invert the fix for another.** Gating the handover comment signal to
  catch a sibling's `handoff:` stamp also caught the *receiver's own*, restoring the 2026-09-01 false
  NOT_YET that sends a sender to re-deliver merged work. The repair needed a discriminator
  (`--slug`) and a rule about which side of it may extend: **strict left boundary, loose right** —
  a receiver's follow-on lane extends the brief's slug, a stranger's does not.
- **A survived mutation is often a bad test, not a weak guard.** My empty-selection stub printed only
  `no tests ran`, which never produced a parseable summary, so the branch it was meant to kill was
  never reached. Fixing the fixture also improved the semantics: a run that collected nothing is now
  `UNREADABLE reason=no_tests_ran` — neither PASS nor FAIL.
- **Editing files while a mutation or pytest job runs invalidates that run.** One `REFUSED` anchor
  measured my own torn tree and proved nothing about the code. Wait for the tree to be quiet.
- **Exclusion pathspecs are CWD-relative too.** `git add -A -- . ':!*.done'` from a subdirectory
  staged 1 of 3 changed files and committed a root marker. Both halves must be anchored:
  `':/' ':(top,exclude)*.done'`, plus `git add -u -- ':/'` for a TRACKED marker's real change that
  the exclusion alone suppresses forever.
- **`git branch --merged` marks a branch checked out in another worktree with `+`, not `*`.** My
  parser stripped only `*`, so it silently dropped the entire population the function reports.
- **The identity claim survives at git level and fails at the script level.** `behind == 0` means the
  base is an ancestor, so `--no-ff` writes the branch tip's tree — the reviewer attacked it with
  `merge.renormalize` over CRLF and both trees matched. The real counterexample was what got checked
  out: with a tag as base, the merge detached, the base never moved, and the verdict still said
  `MERGED` at exit 0.
- **Phase 7c archives by copy in practice.** It moved 6 of 641 files for a closed feature, so a
  merged feature's impl-plan stayed in the live population and kept gating live code — which is how
  an unrelated tooling commit turned the suite red.

## Next Steps

1. **#11 — decide the H1–H9 fold** (the last open item from the #100 brief). H1, H6, H8 have landed;
   H2 and H7 partly. Live: **H3** (clean streak counts only over an unchanged leg set), **H4** (delta
   self-review as a script that re-executes every command in the diff), **H5** (shared sentences
   single-sourced and adoption-checked pre-commit). H9 shipped as the Agent-tool size tier. Evidence:
   `/Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/03-analysis/gateway-consolidation.audit-ledger.md`.
2. **Use 7f on the next feature closure** — `python3 ~/.claude/skills/h-mad/scripts/h_mad_phase7_integrate.py --repo-root <repo> --feature <f>`
   plans; add `--apply` to merge. It runs AFTER 7d's commit and before 7e's push.
3. **Pass `--project-tests <scoped-test-root>` on the next Phase 3/4/5b gate call** and read the
   `SUITE:` line; then `--exit-check <stamp>…` before closing an exit gate.
4. **#112 reviewer-side half** — on the FIRST audit dispatch of the next feature, record how many
   musts came back `class:`-tagged, how many untagged (fail-closed to build), and whether any leg
   emitted an unknown word. The mechanism is already field-measured (below); no reviewer has ever
   emitted a `class:` line.
5. `[suggested]` **#61 `COLLECT: MISSING` marker-name defect** — unchanged since 09-05, never
   re-probed. Cheap to falsify or confirm.

## Open / Blocked Items

**This lane — `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none (main is canonical)`**

- **#11 H1–H9 fold — OPEN, the operator's decision.** See Next Step 1. Inherited via
  **Handover-From:** HemaSuite · main · session `cab14393`.
- **#112 GATE-CLASS — MECHANISM field-measured this session, REVIEWER half still owed.** Measured on
  `docs/archive/2026-09/doc-block-exec/doc-block-exec.plan.audit.v91.md` with controls: as shipped
  (fully acknowledged) `PASS must=0 should=0` and all class counts 0 — the zeros are acknowledgement
  working, not a blind gate; ack section stripped → `FAIL must=1 should=3`, `measurement=4`; must
  retagged `class: build` → `build=1 ack_refused=1`; unknown word `class: cosmetic` →
  `build=1 untagged=1 ack_refused=1`. Corpus: of 1001 audit reports, **833 reviewer legs carry ZERO
  `class:` lines**; all 9 tags in the tree sit in 3 orchestrator-written sidecars. No feature is in
  phase 3/4 now, so the reviewer half waits for a live cycle.
- **#66 / the `hmad-audit-evidence-gate` feature** — record present at `current_phase=0`, unclaimed.
  Its three defects: rejections out of the gated set **LANDED** (SKILL §"Record a rejected finding");
  the evidence-existence check **REFUSED by measurement** (#27 — `h_mad_audit_gate.py:178` records
  that no span-occurrence rule discriminates; revisit only once a `quote:`-contract corpus exists);
  the suite run **IMPLEMENTED this session** as #91. Inherited via **Handover-From:** HemaSuite ·
  main · session `f0b69d8d` / `9d8394fb`.
- **#61 `COLLECT: MISSING` marker-name defect** — unchanged since 09-05, not re-probed.
- **#30 · #32 · #36 · #49w** — unchanged. #36's `tree delta` baseline is still **88** untracked
  `.done` markers (measured this session; 55 in `docs/01-plan/features`, 33 moved into the
  doc-block-exec archive with their reports). Do not commit them: `hmad-dispatch` COUNTS them
  (`^?? .*\.done$`) to exclude them from its delta, so gitignoring would blind that measurement.
- **Evidence-gate corpus at `~/.h-mad-corpora/evidence-gate/`** — outside the repo, not backed up.
  Unchanged.
- **`exec agy` lingers after its `result` event** — related lane, not owned here.
  `docs/handoffs/2026-09-03-main__exec-agy-hang-after-report.md`, session `cd979362`.
- **Codex quota** — did not bind; codex was not dispatched this session (both review rounds ran as
  in-process `code-reviewer` agents).

**Closed this session, so the next reader does not re-check them**

- **doc-block-exec MERGED** `8487593` (53 commits, not the "ten" the predecessor said — that was one
  session's count), local branch deleted, `origin/feature/doc-block-exec` kept. Tree-hash identity
  (`381aaba2` both sides) stood in for a second suite run.
- **#111 tooling worktree REMOVED** — `../skills-hmad-gate` and `feature/hmad-class-scored-gate`.
- **#155** `f8cf262` · **#146** `3da3c5d` (the third §D11 error was INSIDE the correction bracket) ·
  **#143** `8dac5ab` · **#152/#153** `322a179` · **#154** `8f05c0d` · **#142** `5f9b05e` · **#126**
  `fc2ae16` · **#129/#105** `505603e` · **#65** `de6548f` (31 → 87 names retired across 35 fields) ·
  **#100 A** `030cc3c` · **#100 B** `cf5a35c` · **#48** `886ad2d` · **#77b** `a8c1409` (#77a was
  already fixed at `hmad-dispatch.sh:2616`) · **7f + `git add -A`** `0fa825c` · **#91** `a90c365`.
- **#20** was already fixed at `b976319` a month ago and had been carried as open since.
- **#145 AC-1.8** — DECLINED (triage: archived). Spec archived with the merged feature; five rounds
  never routed it; the design's codex leg lists AC-1.8 implemented-as-written.
- **#42 INHERITED-UNVERIFIED register** — CLOSED; the archived plan re-ran it at `0021c77` and the
  register is self-maintaining per revision.
- **#27 marker-aware reaping** — DECLINED (useful, not codable now): `exec` knows `--out` but not the
  report path, and the heartbeat already bounds the cost.
- **#8** skill-candidate row "pytest run leaks exec-pane agy panes" — DROPPED: the row exists in
  neither store (grepped 2026-09-07); definition lost in the chain.
- **#9** `docs/skill-candidates.md` census — CLOSED by the scout run `d61dd93`.
- **#5 HemaSuite census — HANDED OVER**, not parked here. Brief:
  `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-09-07-main__skill-candidate-census-handover.md`,
  committed `aa067fdd`, verified discoverable by `pending-handovers` from that repo.
  `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none`. No claim was released
  because none existed; `skill-candidates-hmad-domain-rows` there is unowned and free to take, and
  `gateway-consolidation`'s live claim (session `3e27e450`) was left alone.
- **Phase 7c archive completed** for doc-block-exec — 600 renames plus 6 stale duplicates removed,
  0 leftovers. The precheck calibration corpus follows the documents to their archived paths.

## In-Flight Processes

**None.** Every background job completed and was read; `pgrep` for
`pytest|h_mad_mutation|hmad-dispatch|codex exec` returns nothing at write time.

## Context for Next Session

**Files touched this session:** `h-mad/scripts/h_mad_phase7_integrate.py` (new) ·
`h-mad/scripts/h_mad_audit_gate.py` · `h-mad/scripts/h_mad_audit_cycle.py` ·
`h-mad/scripts/h_mad_review_evidence.py` · `h-mad/scripts/h_mad_archreview_cycle.py` ·
`h-mad/scripts/h_mad_phase7_preconditions.py` · `h-mad/scripts/h_mad_assemble_audit.py` ·
`h-mad/scripts/h_mad_state_write.py` · `h-mad/scripts/h_mad_extract_verdict.py` ·
`h-mad/scripts/hmad-dispatch.sh` · `handoff/scripts/handoff_paths.py` ·
`handoff/scripts/handover_landed.py` · `h-mad/SKILL.md` · `handoff/SKILL.md` ·
`h-mad/references/{phase-table,inline-protocols,failure-recovery,measurement-discipline,agy-architectural-reviewer-prompt,codex-implementer-prompt,codex-verifier-prompt}.md` ·
6 new test files + 6 new mutation specs · `docs/archive/2026-09/doc-block-exec/` (604 files)

**Uncommitted changes:** none, besides the 88 untracked `.done` markers (do not commit).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main                      # c0ff86a, clean, 0/0
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"; hmad-dispatch env
# nothing is claimed and nothing is in flight; start at Next Step 1
```

**Verification state at closure**, all re-derived at `c0ff86a`: h-mad suite `2920 passed / 0 failed`
· handoff suite `281 passed / 0 failed` · anchors `ANCHORS_OK specs=54 mutations=622 drifted=0` ·
every mutation spec `ALL_CAUGHT`. The h-mad figure is **h-mad-scoped**; the repo-root run collects
sibling projects and reads higher. Different corpus, not growth.

**Related docs:**
- `h-mad/scripts/h_mad_phase7_integrate.py` — 7f's docstring carries the whole rationale, including
  why the route is recorded rather than asked.
- `h-mad/scripts/h_mad_audit_gate.py` §"the project suite (#91)" — why a red suite blocks the exit
  and not the cycle, with the flaky-run receipt.
- `docs/learnings.md` — three entries from this session.
