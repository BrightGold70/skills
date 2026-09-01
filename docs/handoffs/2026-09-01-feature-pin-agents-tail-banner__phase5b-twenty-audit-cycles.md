# Handoff — pin-agents-tail-banner Phase 5b, twenty audit cycles, still ungated

**Date:** 2026-09-01
**Branch:** `feature/pin-agents-tail-banner`
**Project:** orca/skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** `2026-09-01-feature-pin-agents-tail-banner__phase5-audit-convergence-and-sigpipe-handover.md`, `2026-09-01-fix-wait-frame-gate-sigpipe__frame-satisfies-sigpipe.md`

## Session Summary

Resumed at Phase 5b cycle 16 and ran **twenty impl-plan audit cycles (v16–v35)** on the codex
surface, applying every finding. **5b is still NOT gated** — `must` fell 6 → 3 → 3 → 5 → 3 → 3 →
1 → 1 → 2 → 3 → 1 → 2 → 3 → 4 → 5 → 5 → 5 → 4 → 3 → **2**, never reaching 0. Stopped at cycle 35
on the context ceiling, not on a verdict. Three side items closed on the way: the SIGPIPE sweep
(2 live wrapper defects fixed), `handover_landed.py`'s false NOT_YET, and the "has `wait` ever
mis-fired" question. `main` and this branch are both pushed and in sync as of `a0ae09d`; the 23
commits since are local.

## Key Learnings

- **The prescribed matcher had never executed.** For four cycles I reported a 24/24 corpus result
  measured by *probe scripts* while the document carried a differently-escaped regex that `grep -E`
  rejected outright (rc 2 on every input). Measure the artifact the document prescribes — extract
  the block and run it. AC-2.11 now enforces this.
- **A version-history entry claiming a back-propagation is the single best predictor of the next
  finding.** Four instances (design live check v1.13, plan Convention Prerequisites v1.7, the T2
  move v1.28/v1.29, design Order+API v1.29). Grep the body; never trust the changelog.
- **Editing a code block orphans the JSON anchors pointing at it** — three instances, each after I
  had written the check down. Anchors are now *generated* from the block. Two further anchors
  landed on the *wrong mechanism* (`|| return 1` aborting the caller; agy mutants on a Codex-only
  fixture), which a match-count check cannot catch: read each mutant back as code.
- **Seven equivalent mutants**, one of them created by the very cycle that added it to close a
  coverage gap. Every new mutation needs a controlled pair against the AC's *own* fixture.
- **Three nodes classified `RED: FAIL` that the RED state itself makes pass** (AC-1.5, T4's
  WIRE-PIN, AC-3.17). Ask of every such node: what does it assert when nothing is implemented? A
  negative-only fixture almost never fails; a mixed positive-plus-decoy one does.
- **A negative corpus is only as strong as its shapes.** The prose rule took four revisions
  (0 → 7 → 14 → 19 → 24 of 24), each falling to a shape the previous corpus lacked: mid-sentence,
  line-leading, banner-prefixed, then headings and hyphenated pseudo-versions.
- **`printf … | grep -q` under `pipefail` reports a MATCH as 141** — fixed in two more live sites
  this session (`_recovered_has_verdict`, `_cmd_alive`). For an *external* producer the ~64 KB pipe
  buffer is not the bound at all: an incrementally-writing producer inverts at 110 bytes.
- **Fixing one direction of a guard is half the job.** The prose false-positive took three cycles;
  the mirror — rival rejection using the same prose-unsafe matcher, *suppressing* real panes — was
  found only at cycle 28. Grep every consumer of a matcher you have just proven unsafe.

## Next Steps

1. **Dispatch impl-plan audit cycle 36** — `h_mad_assemble_audit.py --feature pin-agents-tail-banner
   --phase impl-plan --cycle 36 --project-root /Users/kimhawk/orca/skills --report-file …`, then
   `hmad-dispatch exec codex <prompt> --cd /Users/kimhawk/orca/skills --out … --log … --timeout 1500`.
   Gate with `h_mad_audit_gate.py`; read the `GATE:` token, never `$?`.
2. **Gate 5b on `must=0 AND should=0`**, then a confirming **agy** pass. agy passed at cycles 4 and
   6 and codex broke both; a clean verdict on this branch has been falsified four times.
3. **Then 5d/5e** — `h_mad_assemble_tdd.py --phase red` with PER-TASK counts derived from the
   authoritative rows, never carried.
4. **Task 1 is the prerequisite** — the stub `orca` must answer `terminal read` per handle.
5. [suggested] Decide whether the tail-matcher grammar deserves its own design pass rather than
   further audit iteration (see Open Items).

## Open / Blocked Items

- **Phase 5b NOT gated — status: in progress, 20 cycles spent.** Last verdict v35 `must=2 should=2`.
  All v35 findings applied (`2237b8e`); cycle 36 has not been dispatched.
  - `repo: /Users/kimhawk/orca/skills · branch: feature/pin-agents-tail-banner · worktree: none (main checkout)`
  - Artifacts: `docs/01-plan/features/pin-agents-tail-banner.{spec,plan,impl-plan}.md`,
    `docs/02-design/features/pin-agents-tail-banner.design.md`, audit reports
    `*.impl-plan.audit.v1–v35.*` (v16–v35 committed at `0773020`)
- **An honest read of the trend, for whoever picks this up.** Cycles 16–25 found prose and count
  drift. Cycles 26–35 found (a) the tail-matcher grammar's semantics, which is being *designed*
  through audit rather than through design, and (b) my own incomplete edits — (b) dominated
  cycles 30–34. The plan is materially better (two real wrong-pane defects and an unbound
  `$rival` were caught), but the matcher is the part still moving, and twenty cycles without
  reaching 0 is evidence the loop is not the right instrument for it. **Consider a design pass on
  `_agent_tail_re` instead of a 36th audit.** That is a judgement for the operator, not something
  I should decide by continuing to spend cycles.
- **`carry-forward-sources` lists 18 sources; I read 2** — the branch predecessor and the
  `frame-satisfies-sigpipe` brief, both named in `**Supersedes:**`. The other 16 are historical
  handover briefs from the documented cold-start queue. **I did not read them and make no claim
  about their contents.** They stay in the queue.
- **23 local commits, unpushed** — `git push origin HEAD` when ready. `main` is untouched since
  `4d41a7c`.
- **`.done` marker files for audit reports v16–v35 are untracked** and deliberately not committed.
- **The automation-scout phase was NOT run — status: deferred, deliberately.** WRITE's
  `references/automation-scout.md` phase reconciles the open rows in `docs/skill-candidates.md`
  before appending new ones, and it is the only thing that writes that file. This session hit
  `CTXBUDGET: HALT` at 81.6% (ceiling 80) immediately after the doc was pushed, so the phase was
  skipped rather than half-run. **It is owed**, and this session generated at least three
  candidate-shaped findings worth a row: (a) a mutation `find` orphaned by editing its own code
  block — three instances, mechanically detectable by resolving every anchor after any block edit;
  (b) a node classified `RED: FAIL` that the RED state itself makes pass — three instances,
  detectable by asking what a node asserts when nothing is implemented; (c) a version-history entry
  claiming a back-propagation the body never received — four instances, detectable by grepping the
  body for the claimed string. Run the scout next session BEFORE dispatching cycle 36.
- **Auto-memories: DONE.** `project_pin_agents_tail_banner.md` and its `MEMORY.md` index line were
  corrected — the stored premise still said the pass "reuses the EXISTING `_agent_pv_re`", which
  this session falsified 24/24.

## Context for Next Session

**Files touched this session:**
- `docs/01-plan/features/pin-agents-tail-banner.{spec,plan,impl-plan}.md`
- `docs/02-design/features/pin-agents-tail-banner.design.md`
- `docs/01-plan/features/pin-agents-tail-banner.impl-plan.audit.v16–v35.codex.md`
- `h-mad/scripts/hmad-dispatch.sh`, `h-mad/tests/test_hmad_dispatch.py`,
  `h-mad/tests/mutation-specs/{wait_frame_gate_sigpipe,agy_recovery_sigpipe,cmux_alive_sigpipe}.json`
- `handoff/scripts/handover_landed.py`, `handoff/scripts/test_handover_landed.py`,
  `handoff/tests/mutation-specs/handover_landed.json`, `handoff/SKILL.md`
- `docs/skill-candidates.md`, `docs/learnings.md`, `.h-mad/wires.jsonl`

**Uncommitted changes:** none but the untracked `.done` markers.

**Measured constants — re-derive, never carry:**
- authoritative rows: **45 nodes, 32 FAIL, 13 PASS**; T1 2/4 · T2 10/1 · T3 12/6 · T4 4/1 · T5 3/1 · T6 1/0
- green-at-RED split **12 + 1** (the +1 is AC-2.7's node on AC-2.8's procedure)
- spec **16 ACs** (row-anchored derivation); **37 mutations**; wire gate `wiring=2 registered=3`
- prose corpus **24 negatives / 12 positives**, run through the doc's own block: 24/24 decline, 12/12 match
- `test_hmad_dispatch.py` collects **290**; feature selector 0/290; broad `tail` 2/290
- `_cmd_run`: `--timeout 1` → 0.376–1.16 s rc124; `--timeout 2` → 1.936–2.232 s rc124;
  `0|notanumber|""` → rc 2 in ~0.04 s
- real `orca terminal read --json` carries top-level `ok:true`; `tail` is a LIST; capped at 2000 lines

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
git checkout feature/pin-agents-tail-banner
python3 ~/.claude/skills/h-mad/scripts/h_mad_context_budget.py --mode run   # check the ceiling FIRST
/h-mad "pin-agents-tail-banner"        # state: last_completed_phase=5, current_phase=5
```

**Related docs:**
- `docs/01-plan/features/pin-agents-tail-banner.impl-plan.md` — v1.32, the dispatch contract
- `docs/02-design/features/pin-agents-tail-banner.design.md` — v1.31
- `h-mad/SKILL.md` §"Phase 5 (Implementation) sub-steps", §"Run-context ceiling"
