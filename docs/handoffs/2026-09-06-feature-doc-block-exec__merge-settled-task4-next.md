# Handoff — doc-block-exec: the merge question is SETTLED (merge, then Task 4); nothing is in flight

**Date:** 2026-09-06
**Branch:** `feature/doc-block-exec`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-06-feature-doc-block-exec__5e-documents-closed-and-tooling-batch.md (the branch predecessor, written earlier today), 2026-09-05-main__audit-loop-never-runs-repo-suite.md and 2026-09-05-main__hmad-audit-loop-evidence-from-gateway-consolidation.md (taken over 09-05; re-emitted below, not re-read this session)

> **Short doc on purpose.** This is a delta closeout: its predecessor was written ~30 min earlier
> and is accurate, and only ONE thing has landed since — `8ef45fc`, the operator decision that
> unblocks the whole critical path. Everything the predecessor holds is re-emitted below in
> compressed form with pointers; read it for the detail behind any line here.

## Session Summary

The predecessor closed 5e's document debt. Since then exactly one commit landed: **`8ef45fc`, the
operator's decision on the per-task merge** — the single question 5e left genuinely open and the one
thing no artifact in the tree stated. Decision: **`doc_block_exec_task3.json` MERGES into
`doc_block_exec.json`; the per-task file was staging, not a convention; merge FIRST, then Task 4.**
Recorded in `§D10` of the decisions sheet with its four parts and its verification commands.
**Nothing is in flight, the claim is released, everything is pushed (`0/0`), and Task 4 is still
unstarted.**

## Key Learnings

- **The merge is not a file move, and the 5e round is what made that true.** `doc_block_exec_task3`
  appeared **0** times in all four documents at `6a1693c` and appears in **all four** at `bdc606e`
  (spec 1, plan 5, impl-plan 6, design 4). Merging the files without reconciling those references
  leaves four *gated* documents pointing at a deleted path — strictly worse than not merging. The
  round that answered D10 created D10's own execution cost.
- **The merge and Task 4 want ONE author round, not two.** Task 4 adds 30 rows to the same file, so
  reconciling the documents once — for the merge and Task 4's rows together — avoids re-opening four
  gated documents twice. This is the main sequencing advice for the next session and it is not in
  `§D10`.
- **A decision that exists nowhere in the tree is the only thing a session cannot reconstruct.**
  Three documents took three positions on the merge and `grep` found the intent in none of them,
  no sheet, and no commit message. Everything else in this feature is re-derivable from commits;
  that one sentence was not, which is why it was recorded before anything was executed.

## Next Steps

1. **Execute the merge** — `§D10` in `docs/03-analysis/doc-block-exec.5d-decisions.md` carries all
   four parts: fold 28 rows into `doc_block_exec.json` (32 → 60, name-disjoint so nothing is lost);
   reconcile the absolute `/opt/anaconda3/bin/python3.11` `target_command`; satisfy
   `ls h-mad/tests/mutation-specs/ | grep -cE '_task[0-9]+\.json$'` → `0`; and reconcile the four
   documents. **Do the document half in the same author round as Task 4's rows.**
2. **Re-derive, do not carry**, at the merge commit: 32 / 28 / 60 / 90 / 30 are stamped at
   `bdc606e` and the merge changes three by construction. Run `--check-anchors` AND a full harness
   pass on the merged file — a merged spec whose anchors resolve but whose rows no longer kill is
   the failure this feature has already met twice.
3. **Task 4** (CLI + registry). `grep -c 'def test_cli_' h-mad/tests/test_h_mad_doc_block_exec.py`
   → **0** today. Carries `OPEN-DECISION` `:3503` (alias-refusal unlink read-back) and `:3505`
   (`--help` bypass), plus the D6 row `substitution-result-not-passed-to-run_block` and its
   specified killer `test_cli_subst_value_reaches_the_child`. Note `test_cli_bad_timeout_values`
   **does not exist yet** — the #122 enumeration records it as a Task-4 claim, not a measurement.
4. **Task 5**, then **5f**: `h_mad_baseline_sha.py --branch feature/doc-block-exec --trunk main`
   reports `UNVERIFIED reason=no_impl_plan candidate=0885152` **by design**; `0885152` IS the 5c sha.
   Then `h_mad_wire_registry.py verify --base 0885152 --rootdir . --testpath h-mad/tests`.
5. **5g** — the D3 provenance bump lands here and nowhere earlier; `phase = null` ONLY after 5f.
6. **Claim before touching anything** — nobody holds `doc-block-exec`.

## Open / Blocked Items

**doc-block-exec — `repo: /Users/kimhawk/orca/skills · branch: feature/doc-block-exec · worktree: /Users/kimhawk/orca/skills`**

- **The per-task merge — DECIDED (`8ef45fc`), NOT EXECUTED.** This is the whole delta over the
  predecessor. Four parts in `§D10`; part 4 (document reconciliation) is the larger half.
- **D3 — SETTLED at remedy 3; its obligation is live through 5g.** `assert 19 <= 12`. Every green
  claim from here to 5g names the red. A grep tally is not that figure.
- **Tasks 4 and 5 not started**, carrying `OPEN-DECISION` `:3503` and `:3505`. `:2735` was
  IMPLEMENTED at `d6bab5b` — verify the shipped choice, do not re-decide it.
- **The `.json.pending` parked specs stay** at `docs/03-analysis/doc-block-exec.pending-mutation-specs/`.
  Nothing detects a parked spec never moved back (D2's residual).
- **Claim RELEASED. Everything PUSHED (`0 behind / 0 ahead` at `8ef45fc`).** `main` untouched. No PR.

**Carried from the predecessor — every item walked, all unchanged since it was written ~30 min ago unless noted**

- **CLOSED there and staying closed:** D9 (`2b64747`, `98 passed`, `ALL_CAUGHT 28/28`; clause (c) is
  a TEST fix no row can express — see `.d9-proof.md` §C, never report it as covered by ALL_CAUGHT) ·
  #122 (resolved to **EIGHT**, not the "settled" seven) · #65 (`8f29826`) · #61 (`aa89d62`) ·
  #36 (`f67454e`) · #30 (premise stale by 14 revisions).
- **#126 heartbeat that does not beat** — OPEN, diagnosed to the line, NOT implemented. Fix is in
  `h_mad_state_write.py` (`--claim` at `:286` is the only heartbeat writer); `h_mad_state_ownership.py`
  is correct. Two backward-compatible options plus a third orthogonal one on the task.
- **#129 partition-parts species** · **#105 self-counting screens** — NEW/open, both owed to
  `h-mad/references/measurement-discipline.md`, both with live worked examples.
- **#128 fresh-branch predecessor gap** — OPEN, emission-policy call.
- **#100 taken-over H1–H9 brief** — unchanged, not started. `repo: /Users/kimhawk/orca/skills ·
  branch: main · worktree: none`.
- **#111 tooling worktree** — merge commit `f2b3d74` verified; removal is the operator's:
  `git worktree remove ../skills-hmad-gate && git branch -d feature/hmad-class-scored-gate`.
- **#112** · **#48** · **#42** · **#77** · **#27** · **#9/#5/#8** · **#7 (closes with 5e)** — unchanged.
- **Evidence-gate corpus outside the repo, not backed up** (`~/.h-mad-corpora/evidence-gate/`) — unchanged.
- **HemaSuite skill-candidate row** — ownership already moved; brief
  `HemaSuite/docs/handoffs/2026-09-04-main__wrapper-rc-row-is-probably-a-duplicate.md`. Not re-checked.
- **Codex quota** — did not bind; `codex_status` remains `available`.
- **The predecessor's `carry-forward-sources` WARNING stays FALSIFIED** — run the single documented
  invocation. It was re-run this session and returned the correct three sources.

**Taken over 09-05 by `adb05ac8` — `**Handover-From:** HemaSuite · main · session cab14393`** (task **#100**)

- **H1–H9 + tooling defects A/B — owned here, NOT started, unchanged since 09-05.**

**Inherited — `**Handover-From:** HemaSuite · main · session 9d8394fb`** (task **#91**)

- **Phase 3–4 audit cycle never runs the project test suite** — unchanged as a skill defect.

**Related lanes, not owned here**

- **`exec agy` lingers after its `result` event** — unchanged.
- **HemaSuite `#18 gateway-consolidation`** — HALTED by the operator; the skills h-mad update it
  waited on has landed. Another repo's lane, not acted on.

**New, small, unowned**

- `hmad-dispatch run --help` exits 2 with `unknown option '--help'`. Unchanged, no ticket.
- **The automation scout has not run for two consecutive handoffs** (skipped on context both times).
  It is the only writer of `docs/skill-candidates.md`, so its open rows decay until someone runs it.
  Run it early next session rather than at closeout.

## Context for Next Session

**Files touched since the predecessor:** `docs/03-analysis/doc-block-exec.5d-decisions.md` only.

**Uncommitted changes:** none besides the 88 untracked `.done` markers (do not commit).

**Verified figures — unchanged from the predecessor, each stamped at its own commit:**

| what | value | at |
|---|---|---|
| module suite | `98 passed` | `2b64747` |
| mutations, Task 3 | `ALL_CAUGHT 28/28 survived=0` | `2b64747` |
| full h-mad suite | `1 failed, 2717 passed` (the 1 is D3) | `2b64747` |
| mutation matrix total | **90** = 89 helper + 1 `SKILL.md`; `32 + 28 + 30 = 90`, `NOT-IN-MATRIX = []` | `bdc606e` |
| exec suite | `64 passed` | `f67454e` |
| `verdict_laundering` re-anchor | `ANCHORS ok=5/5`, `ALL_CAUGHT 5/5` | `eb79500` |

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout feature/doc-block-exec        # HEAD 8ef45fc, pushed, 0/0
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"; hmad-dispatch env
python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json \
  --feature doc-block-exec --session-id <you>          # then --claim; nobody holds it
grep -c 'def test_cli_' h-mad/tests/test_h_mad_doc_block_exec.py    # expect 0 — Task 4 not started
ls h-mad/tests/mutation-specs/ | grep -cE '_task[0-9]+\.json$'      # expect 1 — merge not executed
```

**Related docs:**
- `docs/03-analysis/doc-block-exec.5d-decisions.md` — **read §D10 first**: the merge decision, its
  four parts, and both orchestrator errors from the round that produced it
- The predecessor handoff, for the full 5e narrative and the per-defect detail
