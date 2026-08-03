# Handoff — TAKEOVER built, and an inbound five-item handover discharged

**Date:** 2026-08-03
**Branch:** main
**Project:** /Users/kimhawk/orca/skills (symlinked as `~/.claude/skills/h-mad` and `~/.claude/skills/handoff`)

## Session Summary

Continues `2026-08-03-main__agy-reviews-mutation-harness.md` (which ended at 7 PRs merged). Ran a third agy review — this time on the **vendor-managed** `orca-cli` skill — whose two Must-fix items landed in *our* HANDOVER mode rather than theirs. Mid-session a five-item handover arrived from the HemaSuite worktree; it was taken over, every premise re-verified, and the whole queue discharged. Five more PRs merged (**#28–#32**), `main` @ `102d2af`, clean, zero open PRs. The session also built **TAKEOVER**, the receiving half of a handover, using the real inbound handover as its test case.

## Key Learnings

- **Reviewing a dependency found bugs in our integration, not theirs.** The `orca-cli` review's two Must-fix items were both `[OURS]`, and both sat in the **new-worktree** handover path — which I had never exercised, because the only real handover I had run targeted an *existing* worktree. Reviewing the thing you depend on is a way to find your own untested seams.
- **Verifying the reviewer mattered as much as the review.** Two upstream findings did not survive checking: M3 claimed the existing-terminal handoff had "no preconditions" (the `tui-idle` wait is in the same section two snippets above, and in Notes), and S6 claimed orca-cli omits `--setup run` entirely (it is documented at lines 141/149-150, with `inherit` a deliberate default). Acting on S6 would have meant filing an upstream bug that isn't one.
- **`orca-cli` is vendor-managed and cannot be patched locally.** `~/.agents/.skill-lock.json` pins it to github `stablyai/orca` with a `skillFolderHash`; the substantive 331-line guide is emitted by the binary. Local edits get clobbered on sync. Classify findings by who can act (`[UPSTREAM]` / `[OURS]` / `[USAGE]`) *before* spending effort on them.
- **A handover brief is named for the SENDER'S target branch, so READ can miss it.** The inbound brief landed as `…-main__…` while I sat on a feature branch: READ's branch-filtered lookup returned nothing, and the repo-wide fallback's own advice is to treat a different-branch match as a suspicious sibling pickup. So a legitimate handover was both invisible and, once found, mistrusted. Fixed in #31 — a brief carrying `**Handover-From:**` is addressed to the *repo*, not the branch.
- **Three distinct mutation outcomes this session, each needing a different response.** (1) *Weak test* — the assertion named a mention, not the actionable thing; tighten it. (2) *Equivalent mutant* — deleting `[ -z "$STATE_FILE" ]` changed nothing because `[ ! -f "" ]` covers it; the **code** was redundant, so delete the line rather than invent a test. (3) *Pre-existing weak test* — `test_no_feature_branch_means_no_claim` sets `branch_exists: False` **and** `impl_commit_count: 0`, so either alone suppresses the finding and the `branch` guard was untested. Conflating these produces meaningless tests.
- **A conclusion can be right while its reasoning is unsound, and the reasoning is what you keep.** `#40` proposed closing `#38` because a full Phase 5 ran with zero pane dispatches. But absence of the string means the path was never *exercised* — the guard's correctness comes from `test_hmad_dispatch.py:1316`, which I confirmed is discriminating by mutation. Closed the instrumentation plan, kept the guard.
- **The TDD gate had been silently off in HemaSuite for an entire Phase 5**, and its own allow-list was over-matching (`*test_*.py` against the whole path, so anything under a `test_`-named directory was exempt). Two silent-stand-down defects in one hook; the second was found by the first's test harness.
- **[self-inflicted] WRITE's stamp rule does not know about `handover:`.** §"WRITE — stamp an Orca checkpoint" treats a comment as human-written unless it starts with `handoff:` or `h-mad`. HANDOVER Step 4 (added this session) also writes `handover:`, and TAKEOVER writes `taken over:` — so WRITE would append to its own skill stamp rather than replacing it. See Next Steps 1.

## Next Steps

1. **Add `handover:` and `taken over:` to WRITE's stamp-preserve list** — `handoff/SKILL.md` §"WRITE — stamp an Orca checkpoint", the bullet beginning "Preserve a foreign note". HANDOVER Step 4 already uses the three-prefix form; WRITE still lists two, so it will treat a handover stamp as a human note and append. One-line fix plus a doc-literal test in `handoff/scripts/test_handover_docs.py`.
2. **[suggested] agy-review the `orchestration` skill.** It is the third leg of the HANDOVER / `orca-cli` / `orchestration` boundary and is the only one never reviewed. The arbitration now spans three skills' descriptions and is the least-tested part of mode routing.
3. **[suggested] Grep the skill family for the "hazard named, command withheld" shape** — six of the ten findings across the handoff and h-mad reviews were that. Start from every place the prose says a command "exits 0 anyway", "stashes nothing", or "reads empty" without an adjacent safe alternative. See `feedback_docs_name_hazard_withhold_command` in the auto-memory store.

## Open / Blocked Items

- **Nothing open in this repo.** All five inbound items are discharged (#67 and #66(2) shipped, #68 and #86 closed as bookkeeping, #40 re-scoped), and the takeover work merged.
- **HemaSuite Task 5 — NOT mine; pointer only.** Handed over earlier today and owned by that worktree. `repo: /Users/kimhawk/orca/HemaSuite · branch: feature/196-grounding-shadow-measurement · worktree: none (main worktree)`. Brief: `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-08-03-feature-196-grounding-shadow-measurement__task5-handover.md`. That lane has since closed out on its own (`b94e0317`, `536f67da`) and corrected its TDD-gate claim, so it is live and not waiting on me. Do not re-adopt it.
- **`#40` / `#38` — closed by decision, not by code.** If the pane path ever becomes primary again, the instrumentation question reopens; the guard itself stays covered by its unit test. Rationale recorded in `docs/skill-monitoring.md`.

## Context for Next Session

**Files touched this session (all merged to `main`):**
- `h-mad/hooks/h-mad-tdd-gate.sh` — state-file resolution + allow-list anchoring (#67)
- `h-mad/scripts/h_mad_state_staleness.py` — mid-phase suppression (#66 item 2)
- `handoff/SKILL.md` — TAKEOVER (Step 3.5), the `Handover-From:` marker, the locate exception, and the three `[OURS]` fixes from the orca-cli review
- `docs/skill-monitoring.md` — the `#68`/`#86` and `#40` adjudications
- New tests: `h-mad/tests/test_h_mad_tdd_gate_state_resolution.py`, plus additions to `test_h_mad_state_staleness.py` and `handoff/scripts/test_handover_docs.py`

**Uncommitted changes:** none. `main` @ `102d2af`, in sync with `origin/main`.

**Other repo touched:** HemaSuite `feature/196-grounding-shadow-measurement` — `ed053f1e` (consumer test follows the new `PRECONDITION:` token contract) is an ancestor of its current HEAD `536f67da`, so it survived that lane's own closeout. Its one pre-existing dirty file (`.bkit/state/pdca-status.json`) was left untouched throughout.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main                                                     # @ 102d2af
/opt/anaconda3/bin/python3 -m pytest h-mad/tests handoff/scripts -q   # 1015 expected

# the coupled consumer suite — the symlink means this repo's HEAD is what it runs
cd /Users/kimhawk/orca/HemaSuite/hematology-paper-writer
/opt/anaconda3/bin/python3 -m pytest tests/test_h_mad_*.py -q         # 48 expected
```
A bare `python3` is homebrew 3.14 with no pytest — use `/opt/anaconda3/bin/python3` for tests. The h-mad/handoff scripts are stdlib-only and run fine under bare `python3` (that constraint is tested).

**Running an agy review (the transport that worked, three times):**
```bash
bash ~/.claude/skills/h-mad/scripts/hmad-dispatch.sh exec agy <prompt-file> \
  --cd <repo> --out <report.md> --log <run.log> --timeout 900
```
Headless `agy --print`, pane-independent. **Read the report yourself and verify every finding against the file before acting** — two findings did not survive that check this session.

**The bundled mutation harness (use it, do not hand-roll one):**
```bash
python3 h-mad/scripts/h_mad_mutation_harness.py <spec.json>
# spec: {root, command:[argv], mutations:[{name,file,find,replace}]}
```

**Related docs:**
- Prior handoff (same day, earlier): `docs/handoffs/2026-08-03-main__agy-reviews-mutation-harness.md`
- Inbound brief: `docs/handoffs/2026-08-03-main__five-hmad-items-handover.md`
- Adjudications: `docs/skill-monitoring.md` (tail — `#68`/`#86`, then `#40`)
- The three agy review reports were scratchpad-only and **not** persisted; their findings live in the PR bodies for #26, #27, and #28–#32.
