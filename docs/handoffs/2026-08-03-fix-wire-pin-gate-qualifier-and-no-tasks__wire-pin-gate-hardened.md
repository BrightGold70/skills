# Handoff — Wire-pin gate hardened: shape allowlist + tasks=0 remedy split

**Date:** 2026-08-03
**Branch:** fix/wire-pin-gate-qualifier-and-no-tasks (skills; NOT yet committed/pushed)
**Project:** /Users/kimhawk/orca/skills (symlinked as `~/.claude/skills/h-mad`)

## Session Summary

Picked Task #17 off the prior handoff ("strip a trailing parenthetical from the shape value") and, after an adversarial code review, escalated it into a real fix of a silent-PASS class in the Phase-5b wire-pin gate. Two defects closed: (1) `_declared_shape` now matches the shape against a **closed allowlist** (`new-behaviour|new-behavior|refactor|wiring`, +qualifier cut) so any unrecognised word (`wire`, `connection`, `wiring — <house-style prose>`, `not-wiring (wiring)`) fails **closed** as `unshaped` instead of sailing through as "declared something, not wiring"; (2) `_TASK_RE` now requires a **digit-led id**, so `## Task decomposition` / `## Task outline` stop inflating a true `tasks=0` to `tasks=1` and misrouting the operator's remedy. Plus the originally-scoped `tasks=0` message split and the parenthetical strip. **Green, mutation-tested (7 mutations, all caught), reviewed by opus code-reviewer whose 3 HIGH findings were all reproduced live and fixed.** Diff is **uncommitted** on a feature branch — owes a commit + PR (mirrors #18/#19). HemaSuite Task 5 remains parked and untouched this session.

## Key Learnings

- **The gate's real hole was never the parenthetical — it was fail-*open* on unknown shapes.** Trimming the qualifier (the Task #17 ask) fixes one surface; the load-bearing fix is the allowlist. Before it, `_declared_shape` returned any lowercased word, and only `== "wiring"` triggered the obligation — so every non-`wiring` word (typo, synonym, invented shape) was a silent PASS on exactly the task the gate exists to catch. Fail-closed (unrecognised → `unshaped` → FAIL) subsumes the parenthetical, the em-dash-prose, AND the synonym cases in one rule.
- **The corpus decided both designs, not intuition.** Swept all 283 shipped `*.plan.md`/`*.impl-plan.md` in HemaSuite: real shape values are only `wiring` and `new-behaviour — <prose>` (em-dash prose is the **house style**, so `wiring — connects X` would have skipped the obligation); real task ids are all digit-led (`0`, `4.a`, `6.1.5`, `7b`, `13.6`), and the ONLY non-numeric `## Task <word>` headers in the entire corpus are the two phantoms (`decomposition`, `outline`). Tightening the id regex dropped exactly those two and zero real tasks — verified by diffing old-vs-new parse across the corpus.
- **`tasks=` became load-bearing this session.** SKILL.md now instructs the operator to *read the `tasks=` count to choose the halt token* (`impl_plan_unshaped` vs `impl_plan_no_tasks`), so the parser's prose-heading looseness — previously cosmetic — now mis-routes. The two fixes are coupled: the message split is only correct once the count is trustworthy.
- **The qualifier cut earns its place for ONE narrow job, not the whole fix.** Mutation G (disable the cut) failed only 1 test: `_SHAPE_RE`'s word boundary already tolerates a trailing qualifier. The cut exists solely so the `|`-alternation check sees the shape *without* a qualifier that might contain a `|` (`wiring (engine | tools seam)`). That's why it must run *before* the `|` test. The comment was corrected to stop overclaiming.
- **A reviewer finding reproduced against the change's own worked example.** The nested-paren case `wiring (connects finalize() to measure())` — the most natural way to name a connection — was NOT stripped by the reviewer-flagged `\([^()]*\)$` regex and routed a real wiring task to `mislabeled`, whose documented remedy is "clear the WIRE lines" → a PASS. The allowlist + `[(,;–—].*$` qualifier cut closes it.
- **One new test was dead weight, caught by mutation.** `test_a_qualified_non_wiring_shape_still_catches_a_mislabel` passed both pre- and post-fix because it asserted on the incidental substring `"refactor"`. Rewritten to assert the operator-visible routing message `declares \`refactor\` but carries` — which fails on the revert mutant.

## Next Steps

1. **Commit the gate fix + open a PR** (mirrors #18/#19). `cd /Users/kimhawk/orca/skills`, on branch `fix/wire-pin-gate-qualifier-and-no-tasks`. Suggested title: `fix(h-mad): wire-pin gate fails closed on unknown shapes + honest tasks=0 remedy`. 5 files, +243/-15. Body should note the allowlist is the load-bearing change and the corpus sweep that justified the digit-led id tightening.
2. **Re-pin + re-assert preflight before ANY HemaSuite dispatch** — `cd /Users/kimhawk/orca/HemaSuite`, `bash ~/.claude/skills/h-mad/scripts/hmad-dispatch.sh env` currently reads `PREFLIGHT: FAIL stale=codex,agy` (both pinned terminals dead). Use `pin-agents` (Pass-0 join) — `launch codex` is broken by J1. This is Task #19, blocks Task 5 (#16).
3. **Dispatch HemaSuite Task 5 RED+GREEN** (#16) once preflight is green — `tests/test_grounding_shadow_isolation.py` (confirmed still absent). See Open Items for full location block.
4. **[suggested] Emit a `WIREPIN: UNREADABLE` token on OSError** — `h-mad/scripts/h_mad_wire_pin_gate.py:~230`. Reviewer MED finding: a missing/unreadable plan prints only `ERROR:` to stderr + exit 2, but SKILL.md says "read the token, never `$?`" — a caller obeying the contract can't tell "gate errored" from "gate never ran", and the new tasks=0 story is *about* being pointed at the wrong file. Deferred, not blocking.

## Open / Blocked Items

- **skills gate fix — status: complete, GREEN, reviewed; uncommitted on a feature branch.** 872 skills-suite + 48 HemaSuite consumer-suite pass. Not committed because we're on `fix/wire-pin-gate-qualifier-and-no-tasks` pre-PR; the handoff doc was deliberately NOT auto-committed onto it (would pollute the eventual PR). `repo: /Users/kimhawk/orca/skills · branch: fix/wire-pin-gate-qualifier-and-no-tasks · worktree: none (main worktree)`.
- **HemaSuite Task 5 — status: parked, undispatched, UNCHANGED this session.** `repo: /Users/kimhawk/orca/HemaSuite/hematology-paper-writer · branch: feature/196-grounding-shadow-measurement · worktree: none` @ `8ed16260`. Confirmed NOT merged into main (only `feature/193` shows in `git branch --merged main`). Target `tests/test_grounding_shadow_isolation.py` confirmed still absent. Plan §Task 5 at `docs/01-plan/features/grounding-shadow-measurement.impl-plan.md:337-341` (v1.5). `new-behaviour` shape, Production file: none (test-only). The plan's synthetic in-test section supersedes the dead `sapphire_sa2` premise. Blocked on Next Step 2 (preflight). Feature was force-claimed by session `73aae80d-...` per prior handoff — release/re-claim before touching.
- **`hmad-dispatch launch` broken by J1 — status: open, worked around.** Task #21. No paneKey in the create response; `pin-agents` is the working path. SKILL.md still recommends `launch`. Not investigated.
- **claim/resume staleness-window inconsistency — status: filed, not fixed.** Task #20. `h_mad_state_write.py --claim` has no staleness allowance while `h_mad_resume_decision.py` has a 2h one; a dead session blocks a claim the router says to proceed on. `--force` is the only way through.
- **Full-demotion residual — status: accepted, documented not mechanical.** Task #18. Unchanged.

## Context for Next Session

**Files touched this session (all in /Users/kimhawk/orca/skills, all uncommitted):**
- `h-mad/scripts/h_mad_wire_pin_gate.py` — `_SHAPE_RE` allowlist, `_SHAPE_QUALIFIER_RE` cut, digit-led `_TASK_RE`, `shape_raw` capture, `_unshaped_entry()` helper, tasks=0 message split
- `h-mad/tests/test_h_mad_wire_pin_gate.py` — +166 lines: qualifier parametrize, unrecognised-shape fail-closed pair, real-shipped-shape counter-direction, digit-led id + phantom-heading cases
- `h-mad/tests/test_h_mad_wiring_task_shape_docs.py` — added `step5b:impl_plan_no_tasks` to `HALT_TOKENS`
- `h-mad/SKILL.md:259` — read `tasks=` count to choose the halt token
- `h-mad/references/failure-recovery.md` — split the UNSHAPED row into non-zero vs `tasks=0` (`step5b:impl_plan_no_tasks`)

**Uncommitted changes:** 5 files, +243/-15, all the above. Tree otherwise clean.

**Verification already done (do not repeat):** full skills suite 872 passed; HemaSuite consumer suite (6 test_h_mad_*.py) 48 passed; real plan `grounding-shadow-measurement.impl-plan.md` still `PASS tasks=5 wiring=2`; 7 mutations (allowlist off, qualifier-cut off, tasks=0 branch off/forced, strip/alternation order reversed, docs-token removed, parser-tighten regression via corpus diff) all caught; opus code-reviewer's 3 HIGH findings all reproduced live and fixed.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout fix/wire-pin-gate-qualifier-and-no-tasks
/opt/anaconda3/bin/python3 -m pytest h-mad/tests -q     # 872 expected
# then: commit + gh pr create   (Next Step 1)

# HemaSuite side (Next Steps 2-3):
cd /Users/kimhawk/orca/HemaSuite
bash ~/.claude/skills/h-mad/scripts/hmad-dispatch.sh env   # currently PREFLIGHT: FAIL — re-pin first
```
A bare `python3` resolves to homebrew 3.14 with no pytest — use `/opt/anaconda3/bin/python3`. `hmad-dispatch` is NOT on PATH this session; invoke by full script path.

**Related docs:**
- Prior handoff: `docs/handoffs/2026-08-02-main__wire-retro-verify-task5-parked.md`
- `h-mad/references/inline-protocols.md` §Phase 5a (the shape allowlist's source of truth)
- Memory: `feedback_wiring_tasks_need_a_wire_scoped_revert.md`, `feedback_mutation_test_every_guard.md`, `feedback_impl_plan_pins_the_blind_spot.md`, `project_grounding_shadow_measurement.md`
