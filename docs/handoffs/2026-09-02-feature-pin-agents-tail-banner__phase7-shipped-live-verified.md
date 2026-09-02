# Handoff — pin-agents-tail-banner SHIPPED, live-verified; merge to main is the operator's call

**Date:** 2026-09-02
**Branch:** `feature/pin-agents-tail-banner`
**Project:** orca/skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** `2026-09-02-feature-pin-agents-tail-banner__phase5b-gated-task1-green.md`

## Session Summary

Took `pin-agents-tail-banner` from Phase 5b-gated/Task-1-GREEN to **Phase 7 complete**: Tasks 2–6
RED+GREEN, the full verification list, Phase 6a-prime, gap analysis, telemetry, report, archive.
**The live check failed at first and that is the story of this session** — every offline gate was
green (2663 tests, 46/46 mutations, 53 audit cycles, two clean audit surfaces) while the matcher
could not match ANY real agent banner. Fixed, re-verified live, and the feature now resolves a real
Codex pane. The branch is NOT merged to main; that is deliberate and is the top Next Step.

## Key Learnings

- **A feature can pass every offline gate and be inert.** The corpus held only idealised banners,
  so `_agent_tail_re` had never been shown the string it exists to match. Real shapes:
  `│ >_ OpenAI Codex (v0.149.1)   │` (framed + prompt glyph) and agy's block art
  `▄▀▀▄  Antigravity CLI 1.1.22`. Zero of five matched, on both arms.
- **The fix is narrow and the discriminating rule never moved.** Only DECORATION changed: prefix
  `[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?`, line end `[[:space:]]*[│┃╎┆]?[[:space:]]*$`.
  "What FOLLOWS the signature" — the rule that took four revisions — is untouched.
- **`>_` must be a UNIT, not a bare `>` in the class.** Bare `>` matches the negatives
  `> OpenAI Codex` and `> Antigravity CLI 1.1.22`; Markdown blockquotes are `> `, the Codex glyph
  is `>_`. `tail-re-bare-gt-prefix` pins that choice.
- **My own first measurement of the fix was wrong and nearly killed it.** I reported "16 of 36
  negatives break" from a hand-written regex that dropped the line-complete rule. Properly scoped
  it was 2, then 0. **Six hand-rolled checks of mine produced false results this session; the
  prescribed tooling produced none.** Derive candidates by editing the shipped regex, not by
  retyping one.
- **Citing an AC after the id in a table row silently breaks the derivation.**
  `| AC-2.9 (spec AC-4.4) |` made the per-task loop read T2 as 8/1 instead of 10/1 while the
  unanchored aggregate still said 45. Cite in the proof column; re-run BOTH derivations after any
  table edit.
- **Two independent triages of the same 17 briefs produced DIFFERENT still-open sets.** The sibling
  lane's Phase 7 handoff retired all 18 in its `Supersedes` and carried its own list; four of mine
  appear nowhere in theirs. Neither triage is complete alone.
- **Concurrency manufactures phantom regressions.** Two pytest runs over one tree gave 6 failures
  and 3 failures in different sets; the file passed 36/36 alone. Run the repo suite alone.
- **`RUN_RC` is not a work signal when the task edits the wrapper it dispatches through.** T2 gave
  rc=2, T3 gave rc=127 (`line 3597: ame: command not found` — a torn read of a file being
  rewritten). Both were self-edit artefacts; the work was fine. The independent re-run is the gate.

## Next Steps

1. **Merge `feature/pin-agents-tail-banner` into `main`** — operator decision, deliberately not done.
   Probed clean in a throwaway worktree: 129 ahead / 62 behind, **3 conflicts, all append-only
   ledgers** (`.h-mad/wires.jsonl`, `docs/learnings.md`, `docs/skill-candidates.md`). The CODE
   auto-merges — `h-mad/scripts/hmad-dispatch.sh` and `h-mad/SKILL.md` both clean. Union both sides
   for the two docs; for `wires.jsonl` union by `(owning_feature, id)`, NOT by line, or one
   feature's wire evicts another's (J43). This repo IS the installed skill, so until it merges the
   live skill still cannot resolve a real Codex pane.
2. **After merging, re-verify on the MERGE RESULT, not on either parent** — `pytest
   h-mad/tests/test_hmad_dispatch.py -q` (335), full `pytest -q` (2663), then
   `python3 ~/.claude/skills/h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/tail_signature_pass.json`
   (49/49) and `h_mad_wire_registry.py verify --base 03c66d55 --python /opt/anaconda3/bin/python3`.
3. **Re-run the live check on the merged skill** — isolated pin file, seed and prove presence,
   clear, prove absence, then require `bound <handle> by tail evidence` in `hmad-dispatch env`.
   Protocol and evidence: `docs/03-analysis/pin-agents-tail-banner.live-check.md`.

## Open / Blocked Items

- **Merge to main** — status: operator decision. See Next Step 1 for the probe evidence.
- **The 9 still-open items my brief triage found.** The 17 briefs were RETIRED by the sibling lane's
  `2026-09-02-BrightGold70-audit-report-docs-copy__phase7-complete.md` (18 names in its
  `Supersedes`), and its independent triage found a DIFFERENT set. **These four appear in mine and
  not in theirs, so they exist only here:**
  1. `#68` — amend the shipped `tdd-dispatch-verification-discipline` spec with the prompt-size
     ceiling finding, or close it as covered. No decision recorded anywhere. *Operator decision.*
  2. `#86` — close as a duplicate of `#67`/`#66`/`#68`. The `#NN` tracker was a HemaSuite TodoList
     that no longer exists, so this is judgement, not lookup. *Operator decision.*
  3. gate-blindness — never filed as a sanitized GitHub issue; the code fix shipped without it.
     *Operator decision, deferred by the original brief.*
  4. Cross-repo sweep of `~/.claude/handoffs/INDEX.md` for handoff-drop damage outside HemaSuite —
     the probe the restore-chain brief suggested was never run.
  The remaining five overlap the sibling's list (HemaSuite `docs/skill-candidates.md`: I measured
  **125 open of 314** in the main store; the 16 still-open h-mad-domain rows of the 36 handed over).
  `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: /Users/kimhawk/orca/HemaSuite` —
  FOREIGN REPO, a HANDOVER candidate rather than work owed here. Full ledger:
  `docs/carry-forward-triage-2026-09-02.md`.
- **Pre-existing test-isolation defect, NOT this feature's** — status: open.
  `test_send_unresolved_agents_is_not_refused_as_a_conflict` reads the real `.h-mad` preflight
  receipt rather than a per-test one, so it passes or fails on ambient state. Reproduced failing on
  `origin/main` in a clean detached worktree.
- **`docs/skill-candidates.md` — 3 rows still open here** (25 shared mutation anchors across specs;
  pane janitor still hand-closed; no new verdict token this session), plus 3 rows appended today.
- **59 untracked `.done` markers** — deliberate, unchanged since 2026-09-01. Do not commit.
- Predecessor items, all CLOSED this session: Tasks 2–6 (`d8cca19`…`e1f128d`), the verification
  list, Phase 6, Phase 7. The predecessor's "17 unread briefs" item is closed by
  `docs/carry-forward-triage-2026-09-02.md` and the sibling's retirement.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/hmad-dispatch.sh` — the pass, both helpers, both matchers
- `h-mad/tests/test_hmad_dispatch.py` — 45 new nodes, corpus 36 negatives / 15 positives
- `h-mad/tests/mutation-specs/tail_signature_pass.json` — 49 mutations
- `docs/01-plan/features/pin-agents-tail-banner.{spec,plan,impl-plan}.md`, `docs/02-design/…design.md`
- `docs/03-analysis/pin-agents-tail-banner.{analysis,live-check}.md`, `docs/04-report/features/…report.md`
- `docs/carry-forward-triage-2026-09-02.md`, `docs/archive/2026-09/pin-agents-tail-banner/`

**Uncommitted changes:** none but `.h-mad/wires.jsonl` (registration timestamps) and the 59
untracked `.done` markers.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
git checkout feature/pin-agents-tail-banner
python3 ~/.claude/skills/h-mad/scripts/h_mad_context_budget.py --mode run
# feature is Phase 7 COMPLETE — the open work is the merge, Next Step 1
```

**Related docs:**
- `docs/04-report/features/pin-agents-tail-banner.report.md` — what shipped and the evidence
- `docs/03-analysis/pin-agents-tail-banner.live-check.md` — the failure, the fix, the passing re-run
- `docs/carry-forward-triage-2026-09-02.md` — all 17 briefs, per-item evidence
