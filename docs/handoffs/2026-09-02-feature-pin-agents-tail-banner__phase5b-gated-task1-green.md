# Handoff — pin-agents-tail-banner: 5b GATED at cycle 53, Task 1 GREEN, Tasks 2–6 next

**Date:** 2026-09-02
**Branch:** `feature/pin-agents-tail-banner`
**Project:** orca/skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** `2026-09-01-feature-pin-agents-tail-banner__phase5b-twenty-audit-cycles.md`

## Session Summary

Resumed at Phase 5b cycle 36. Ran the owed automation scout, then the operator chose a **scoped
design pass** over a 36th audit; writing the grammar down once found two defects 20 cycles had
missed. Eighteen two-surface cycles (v36–v53) followed, every report persisted before acting and
every finding verified before applying; **5b GATED at v53 — codex and agy both `must=0 should=0
nit=0` on identical bytes (impl-plan v1.58)**. Then Phase 5d/5e **Task 1: RED `8f48047`, GREEN
`e0390cc`**, 296 passed, T1's five mutations `ALL_CAUGHT` against real code. Tasks 2–6 remain.
Everything is pushed; branch in sync with `origin/feature/pin-agents-tail-banner` at `e0390cc`.

## Key Learnings

- **The first RED dispatch found two plan defects that 53 audit cycles could not** — the tests did
  not exist to run against. (a) T1 prescribed `tempfile.mkdtemp(` inside the test module while the
  module's own guard asserts that literal is absent. (b) The 5d assembler cuts §Task N only, and 39
  of 45 AC bodies did not name their test node — names lived solely in the contract table outside
  every task — so Codex invented all six T1 names, which would have orphaned every T1 mutation pin.
  Every AC now carries `**Node:**`. Run the prescribed helper block against the live module's
  guards before trusting a plan; a doc audit cannot.
- **A design pass beat a 36th audit.** Stating the grammar ONCE surfaced (i) the case-fold was
  load-bearing and undocumented — under `grep -E` 9 of 12 real banners decline while the negative
  corpus still passes, and (ii) the flat continuation list was per-arm and wrong on 3/5 rows.
- **codex broke an agy clean nine times; agy's own clean broke on its next cycle three times.**
  Seven reported findings did NOT reproduce (four phantom test bodies in one agy report; a
  landmark the plan never contained; a nit whose line I had already fixed; one "missing
  `; _prev`" that was a legal substring anchor). Verify before applying — every time.
- **Real defects the loop found after the design pass:** a wire that VANISHED from
  `.h-mad/wires.jsonl` under `WIREPIN: PASS` (bare labels collapsed T3's two wires — the numbered-
  labels defect again); a `local` re-declaration that wiped the rival matcher (mine; both surfaces
  caught it independently); `pytest -k orca_find` collecting 0/290; a self-falsifying source
  assertion (mine); the matcher accepting non-dotted versions, unbalanced parens, Markdown
  `>`/`|`/`:` prefixes and an empty cwd (corpus 24→36, five single-field revert-mutants,
  mutations 37→46); an empty rival token rejecting EVERY candidate (unreachable via
  `_resolve_target`, wrong for 19 cycles); the harness invoked by basename (exit 127).
- **Two of my sweeps stopped at one document** (FR-2 mislabel; anchor re-indent prose). The
  paired-surface half is the whole point of the value sweep.
- **Codex "model at capacity" ×3** (v43, v48, v48-retry) — back off ~25 min, never score.

## Next Steps

1. **Task 2 RED** — `python3 h-mad/scripts/h_mad_assemble_tdd.py --feature pin-agents-tail-banner
   --task "Task 2" --phase red --project-root /Users/kimhawk/orca/skills --module h-mad
   --test-path h-mad/tests/test_hmad_dispatch.py --python /opt/anaconda3/bin/python3
   --expect-fail 10 --expect-pass 1 --guard "all 296 current nodes" …` then `hmad-dispatch exec
   codex <prompt> --cd /Users/kimhawk/orca/skills --timeout 1500`. **Re-derive the counts from the
   RED table first** (last derivation: T2 10/1 · T3 12/6 · T4 4/1 · T5 3/1 · T6 1/0; total 45 =
   32/13). Read `STATUS:` via `h_mad_extract_verdict.py`, then re-run pytest yourself.
2. **Task 2 GREEN**, then cut T2's mutations from the plan's embedded JSON into a temp spec under
   `h-mad/tests/mutation-specs/` (so `root: ../..` resolves) and run
   `python3 h-mad/scripts/h_mad_mutation_harness.py <spec>` — expect `ALL_CAUGHT`; delete the spec.
3. Repeat for T3 (WIRE 1/2 — require failure MODE per test, not only the count), T4, T5, T6
   (T6 ships the real spec file).
4. `docs/01-plan/features/pin-agents-tail-banner.impl-plan.md` §Verification — the full list,
   read stdout tokens never `$?`; then Phase 6.

## Open / Blocked Items

- **Tasks 2–6 — status: not started.** T1 landed (`8f48047`, `e0390cc`).
  `repo: /Users/kimhawk/orca/skills · branch: feature/pin-agents-tail-banner · worktree: none
  (main checkout)` · prompts: scratchpad `tdd_t1_{red,green}.{prompt,out,log,report.md}`.
- **5b gate record** — h-mad state `audit_cycles.impl_plan=53`, `phase=step5` (the schema's
  Phase-5 value; `step5b`/`step5b_gated` are refused). Evidence is the two committed v53 reports.
- **`carry-forward-sources` lists 18; I read 1** (the branch predecessor, named in Supersedes).
  The 17 historical `main`/`BrightGold70` briefs remain unread and UNCLAIMED — task #11. One is
  new today: `2026-09-02-main__audit-report-docs-copy.md`, written UNTRACKED by a sibling `main`
  lane into the shared store; not mine, not committed by me.
- **Claim** — `pin-agents-tail-banner` held by session `99361dc9` (this one), heartbeat
  2026-09-02. Stale claims are takeable by plain `--claim`.
- **`.done` marker files for audit reports v16–v53 are untracked** — deliberately (unchanged
  since 2026-09-01).
- **Automation scout — CLOSED** this session (`8d293f9`): 3 open rows re-verified, 3 rows
  appended; re-run at this closeout appends the two learnings above.
- Predecessor items closed: 5b gate (done, v53); "design pass instead of a 36th audit" (done,
  operator chose it); cycle 36 / confirming agy pass (done); Task 1 prerequisite (done).

## Context for Next Session

**Files touched this session:**
- `docs/01-plan/features/pin-agents-tail-banner.{spec,plan,impl-plan}.md` (impl-plan v1.32→v1.59)
- `docs/02-design/features/pin-agents-tail-banner.design.md` (v1.31→v1.42)
- `docs/01-plan/features/pin-agents-tail-banner.impl-plan.audit.v36–v53.{codex,agy}.md`
- `h-mad/tests/test_hmad_dispatch.py` (+6 T1 nodes), `h-mad/tests/stubs/orca` (T1 branch)
- `.h-mad/wires.jsonl`, `docs/skill-candidates.md`, `docs/learnings.md`

**Uncommitted changes:** none but the untracked `.done` markers and the sibling lane's handoff.

**Measured constants — re-derive, never carry:** 45 nodes 32/13 · 46 mutations, 46/46 with
`_mechanism` naming their node, 46/46 anchors resolving against blocks-or-live · corpus 36
negatives / 12 positives, 36/36 + 12/12 under `grep -Ei` · `test_hmad_dispatch.py` collects 296.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
git checkout feature/pin-agents-tail-banner
python3 ~/.claude/skills/h-mad/scripts/h_mad_context_budget.py --mode run   # ceiling FIRST
/h-mad "pin-agents-tail-banner"   # state: last_completed_phase=5, current_phase=5, impl_plan cycles=53
```

**Related docs:**
- `docs/01-plan/features/pin-agents-tail-banner.impl-plan.md` — v1.59, the dispatch contract
- `docs/02-design/features/pin-agents-tail-banner.design.md` — v1.42
- `h-mad/SKILL.md` §"Phase 5 (Implementation) sub-steps", §"Run-context ceiling"
