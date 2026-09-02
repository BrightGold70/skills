# Handoff — pin-agents-tail-banner Phase 5a–5c, 15 audit cycles, and a SIGPIPE defect handed over

**Date:** 2026-09-01
**Branch:** `feature/pin-agents-tail-banner`
**Project:** orca/skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** `2026-09-01-main__backlog-drain-and-tail-banner-design.md`

## Session Summary

Resumed `pin-agents-tail-banner` at the Phase 4/5 boundary and took it through **5a (impl-plan),
5b (15 audit cycles across two surfaces) and 5c (branch + commit)**. The impl-plan is at **v1.12**,
38 test nodes, 19 mutations, `WIREPIN: PASS wiring=1`. **Phase 5b is NOT gated** — the last
recorded verdict is impl-plan audit v15 (codex) `FAIL must=3 should=2`, every finding applied but
not re-audited. Cycle 16 is the resume point.

Three of the phase's corrections were **back-propagated to the spec, plan and design** on the
operator's call, so those documents changed too (spec v1.6, plan v1.9, design v1.13; design
re-gated `AUDITCYCLE: PASS` at cycle 10). Separately, a **live defect in the shipped wrapper** was
found mid-audit, handed over to its own lane, fixed, tested, merged as `282a3a5` and pushed —
`main` is now at `282a3a5` and in sync with origin.

## Key Learnings

- **`printf … | grep -q` under `set -o pipefail` reports a MATCH as a non-match.** `grep -q` exits
  on first match, `printf` takes SIGPIPE, the pipeline yields **141**. Measured: 240 KB tail with
  the signature on line 1 → rc 141; same tail at 16 KB → rc 0, because it fits the ~64 KB pipe
  buffer. Every small fixture passes, so the defect is invisible to an entire test plan. Fix is a
  here-string (no pipeline, status is `grep`'s alone). Found in the impl-plan AND live in the
  shipped `_frame_satisfies`, where it inverted both `wait` gates — `--not-while-regex` failing
  **open**, which is the dangerous direction.
- **Three mutations in this plan were EQUIVALENT when first written**, each scoring `survived`
  against a guard that holds and reading as a coverage gap: `local`-masking (behaviourally
  identical inside the pass — the property is a SOURCE invariant, pinned as one), `return 1 →
  return 0` on the tail helper (same decline by a different route), and `resolve-on-ge-0`, which
  killed by a `set -e` **abort** rather than by the property. A fourth moved two controls at once
  so no kill could be attributed. Mutation authorship is where this feature's real risk lived.
- **A mutation's kill can depend on FIXTURE SHAPE, which no proof-mapping accounted for.**
  `tail-sig-fabricates-banner-on-failure` only bites with exactly one unreadable `codex`
  candidate; two, or an `agy` fixture, and it survives. Fixtures are now pinned where a mutation
  needs them.
- **`h_mad_assemble_tdd.py` consumes PER-TASK counts, not aggregate.** A RED contract stated at
  AC granularity was unusable — two nodes carry two ACs each, so one node landed in both columns
  and another was double-counted. Recast per test NODE (38 nodes, 27 FAIL / 11 PASS), and running
  the prescribed per-task loop then exposed two rows still carrying combined AC labels that made
  it match 35 of 37.
- **`handover_landed.py` reads a COMPLETED handover as `NOT_YET`.** The receiver did the work,
  merged it, released its claim and overwrote the stamp with `Complete: …`. Both signals then read
  negative and the tool prescribed re-delivery of already-merged work. Filed as a candidate row.
- **`worktree-rm` deletes the BRANCH as well as the checkout.** Harmless here (both branches were
  fully merged, all commits reachable from `main`), but it is not what the verb's name implies.
- **The value sweep is still the weak step, on both sides.** Counts and claims went stale on up to
  **six live sites across three documents** in one cycle; and in cycle 15 the audit named three
  stale surfaces where sweeping found four.
- **My own probes produced three false negatives this session**, each from a documented trap: an
  unquoted `$(git ls-files …)` word-split a path containing spaces into five bogus "unparseable"
  specs (falsely predicting a blocked push — the real hook sets `IFS='\n'`); a `| tail` swallowed a
  command's exit code so a missing-argument failure looked like success; and a first `_agent_pv_re`
  probe whose CONTROL failed, which is the only reason it was caught. Controls are not optional.

## Next Steps

1. **Dispatch impl-plan audit cycle 16** — codex surface, the one that has found every substantive
   defect: assemble with `h_mad_assemble_audit.py --feature pin-agents-tail-banner --phase impl-plan
   --cycle 16 --project-root /Users/kimhawk/orca/skills --report-file /tmp/…`, then
   `hmad-dispatch exec codex <prompt> --cd /Users/kimhawk/orca/skills --out … --log … --timeout 1500`.
   Read the `AUDITCYCLE:`/report, never `$?`.
2. **Gate 5b properly before 5d.** Exit requires `must=0 AND should=0`. Do not accept an agy-only
   clean: agy passed at cycles 4 and 6 and codex broke both.
3. **Then 5d/5e** — `h_mad_assemble_tdd.py --phase red`, with **per-task** counts derived by the
   loop in the impl-plan's §Verification (T1 3/3 · T2 6/1 · T3 10/6 · T4 4/0 · T5 3/1 · T6 1/0).
   T3 is a `wiring` task: its `WIRE-PIN` RED must be a caller-observable failure, not a missing
   symbol, which is why T2 must land first.
4. **Task 1 is the prerequisite** — the stub `orca` must answer `terminal read` per handle before
   any later task's tests can exist.
5. [suggested] **Triage the 16-entry cold-start handover queue** (see Open Items) — one pass,
   stamping `**Taken-Over-By:**` on each brief already closed.

## Open / Blocked Items

- **Phase 5b NOT gated — status: in progress.** Last verdict impl-plan audit v15 (codex)
  `FAIL must=3 should=2`; all findings applied, not re-audited. 15 cycles run; findings per cycle
  3→4→5→5→1→3→3→3, and every spike followed a cycle where I introduced a new verification artifact.
  - `repo: /Users/kimhawk/orca/skills · branch: feature/pin-agents-tail-banner · worktree: none (main checkout)`
  - Artifacts: `docs/01-plan/features/pin-agents-tail-banner.{spec,plan,impl-plan}.md`,
    `docs/02-design/features/pin-agents-tail-banner.design.md`, audit reports
    `*.impl-plan.audit.v1–v15.{p1,p2,codex}.md`, `*.design.audit.v10.p{1,2}.md`
- **The 16-entry `carry-forward-sources` / `pending-handovers` cold-start queue — status: NOT
  triaged, deferred deliberately.** This is the documented cold start: `**Taken-Over-By:**` is
  newer than the store, so historical briefs all read as pending. I did **not** bulk-stamp them —
  the skill is explicit that a brief wrongly marked taken-over is invisible again, which is the
  original defect restored by the tool built to fix it. I stamped exactly one, my own outbound
  `frame-satisfies-sigpipe` brief, on direct evidence (`282a3a5` merged, worktree removed).
  Deferred because this session is at 75% of its context ceiling, not because the queue is fine.
- **`main` is 3 commits ahead of where this session found it and PUSHED** — `282a3a5`. Unusual for
  a feature-branch session; it happened because the handover lane merged to `main` and the operator
  asked for the push. `feature/pin-agents-tail-banner` has `main` merged in (`8cb8f88`).
- **`handover_landed.py` false negative — status: filed, not fixed.** Candidate row added to
  `docs/skill-candidates.md` (commit `eb8baf4`). It ranks stamp-prefix matching above visible
  completion; the fix is to treat a feature record that exists at all, or a commit on the target
  branch, as pickup evidence.
- **`MEMORY.md` is 29.6 KB against a 24.4 KB limit — status: over, and this session made it worse.**
  It was already 26.9 KB at session start (the loader warned and truncated). I updated three entries
  and lengthened two. The index is what the next session reads first, so a truncated one silently
  drops guidance. Fix is mechanical: move detail out of the index hooks into the topic files they
  point at — the hooks are meant to be pointers, not summaries.
- **Not verified: whether the shipped `wait` has ever actually mis-fired in the field.** The
  mechanism is proven and fixed; a field occurrence was never sought.

## Context for Next Session

**Files touched this session:**
- `docs/01-plan/features/pin-agents-tail-banner.{spec,plan,impl-plan}.md` + 18 audit reports
- `docs/02-design/features/pin-agents-tail-banner.design.md` + 2 audit reports
- `docs/skill-candidates.md`, `.h-mad/wires.jsonl`
- `docs/handoffs/2026-09-01-fix-wait-frame-gate-sigpipe__frame-satisfies-sigpipe.md` (outbound brief)
- *(the wrapper fix itself was made by the receiving lane, not here)*

**Uncommitted changes:** none.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
git checkout feature/pin-agents-tail-banner
python3 ~/.claude/skills/h-mad/scripts/h_mad_context_budget.py --mode run   # check the ceiling FIRST
/h-mad "pin-agents-tail-banner"        # state: last_completed_phase=5, current_phase=5
```

**Related docs:**
- `docs/01-plan/features/pin-agents-tail-banner.impl-plan.md` — v1.12, the dispatch contract
- `docs/02-design/features/pin-agents-tail-banner.design.md` — v1.13, re-gated at cycle 10
- `h-mad/SKILL.md` §"Phase 5 (Implementation) sub-steps", §"Run-context ceiling"
