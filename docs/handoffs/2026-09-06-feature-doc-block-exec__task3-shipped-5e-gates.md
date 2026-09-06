# Handoff — doc-block-exec: Task 3 shipped and mutation-verified; the anti-gaming pass is the one 5e gate left

**Date:** 2026-09-06
**Branch:** `feature/doc-block-exec`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-06-feature-doc-block-exec__task1-task2-shipped.md (the branch predecessor), 2026-09-06-main__doc-block-exec-5b-exit-and-hmad-class-gate.md (returned only by `carry-forward-sources --branch main` — see the WARNING), 2026-09-05-main__audit-loop-never-runs-repo-suite.md and 2026-09-05-main__hmad-audit-loop-evidence-from-gateway-consolidation.md (taken over 09-05; re-emitted below, not re-read this session)

> **WARNING FOR THE NEXT WRITE — #65 STILL FIRES AND I RAN THE WORKAROUND.**
> `carry-forward-sources --branch feature-doc-block-exec` returns this branch's own handoff plus the
> two taken-over briefs, and does NOT return `…-main__doc-block-exec-5b-exit-…`. I ran
> `--branch main` as well and walked what it returned. Until #65 is fixed, every WRITE on this
> branch must run BOTH.

## Session Summary

Resumed at `enter_autonomous`, claimed the feature, and took `doc-block-exec` from "Tasks 1–2
shipped, Tasks 3–5 owed" to **Task 3 implemented, mutation-verified, and green**. Both of Task 3's
`OPEN-DECISION (r19, 5d)` lines were settled on measured evidence (D6, D7) and all four documents
were brought into agreement. Eight commits, **all pushed**. The module suite is `96 passed`, the
full suite `1 failed, 2715 passed` where the one failure is D3, and
`MUTATION: ALL_CAUGHT mutations=26 caught=26 survived=0 refused=0` — every figure re-derived by the
orchestrator rather than taken from a dispatch. **5e is NOT complete**: the anti-gaming verification
pass has not run, and D3 remains an open operator call.

## Key Learnings

- **A zombie's process group answers `killpg` with EPERM on macOS, not ESRCH.** This is the whole
  of the Task 3 GREEN blocker. The injected `wait()` failure left the killed leader unreaped, and
  the fixture's `kill_if_present` catches `ProcessLookupError` only. It also explains why my own
  probe failed to reproduce it and reported ESRCH: the probe called `p.wait()` and reaped. **Reaping
  was the entire difference**, and the falsified hypothesis is what narrowed the search correctly.
- **Every text transform in a counting pipeline fails PERMISSIVELY.** Four instances this session,
  all mine or an author's, all returning a SMALLER number that reads as clean: a `grep -o` truncating
  a line before the phrase; a hard-wrapped sentence returning 0 for a phrase the document states; a
  per-bullet `awk` reading only each bullet's first line; and two spans bounded by guessing an end
  (one returned 106 for 39, one 21 for 26). A pipe that lost data by *erroring* would have been
  caught at once. **The guard: derive every count twice under transforms that fail in opposite
  directions and require agreement.** Corollary — **a vacuous agreement is not a confirmation**: two
  commands sharing a defect will agree, and that means nothing.
- **A filed premise's VALUE is not its BOUNDARY.** D7 was filed naming `1e300`; the real edge is
  `2147483.647` — `(2**31 - 1) / 1000`, CPython's INT_MAX-**milliseconds** limit, ~24.855 days, five
  orders of magnitude lower and reachable by an ordinary "very large timeout". The conclusion was
  right and the surface it described was ~10^294 times too small.
- **Codex's refusal was right for the fifth time on this feature.** `STATUS: BLOCKED` at 94/96 with
  the reason named in the contract line. Its *summary* mislocated the failing line (it implied the
  escapee kill; it is the leader's process group at `:1070`), which is the documented pattern: right
  symptom, wrong mechanism. Verify a refusal by re-deriving it, and give it the benefit of the doubt
  as long as the evidence does.
- **Three claims I handed authors were wrong about the tree, and authors caught all three.** The
  guard predicate had TWO body sites where I named one; the spec sentence I quoted hard-wraps and
  greps to 0; and I told `plan-author` the design was committed at a freeze where it was not,
  because I committed `da03ca5` *during* its round — h-mad ORCHESTRATOR RULE 2 broken by me. None
  was caught by me. This is the case for fresh-context authors, measured.
- **A mutation-row rename is invisible to a count and visible to a name diff.** The matrix moved
  87 → 88 by TWO arrivals and ONE departure, netting +1. Reading two arrivals as two rows
  over-counts; reading the departure as a deleted guard reports a coverage loss that never happened.

## Next Steps

1. **The anti-gaming verification pass** (`references/codex-verifier-prompt.md`) — the one 5e gate
   not yet run for Task 3: module count, test-discrimination audit, quote the source line for each
   pinned property, full suite vs the reference, every count cross-checked a second way.
2. **Settle D3** (#114) before anything calls the suite green — `docs/03-analysis/doc-block-exec.5d-decisions.md` §D3,
   three remedies, none picked, and §D3 says none is the orchestrator's to pick alone. Current
   posture is remedy 3 (carry the red to 5g, one provenance bump) by default because it needs no
   action. Reading is now `PRECHECK: FAIL issues=19` against a floor of 12.
3. **#122 — resize the "reds a second named test" enumeration to seven** in the impl-plan.
   `timeout-validation-removed` reds Task 4's `test_cli_bad_timeout_values` as well as its canonical
   killer, and was already a member before this round. Routing is SETTLED (resize, do NOT add a
   scope sentence — `spawn-valueerror-unmapped` is already cross-task at `impl-plan:119`/`:140`, so a
   scope sentence would silently drop its third red). Verified by me against the tree.
4. **Task 4**, carrying `OPEN-DECISION` `:3503` (alias-refusal unlink read-back) and `:3505`
   (`--help` bypass), plus the D6 row `substitution-result-not-passed-to-run_block` and its new
   killer `test_cli_subst_value_reaches_the_child`, which the impl-plan SPECIFIED because Task 4's
   AC list held no success-path test that could see that mutant.
5. **Task 5**, then **5f**:
   `python3 ~/.claude/skills/h-mad/scripts/h_mad_baseline_sha.py --branch feature/doc-block-exec --trunk main`
   reports `UNVERIFIED reason=no_impl_plan candidate=0885152` **by design** — the impl-plan was
   committed on `main` before this branch existed. `0885152` IS the 5c sha. Then
   `h_mad_wire_registry.py verify --base 0885152 --rootdir . --testpath h-mad/tests`.
6. **5g** — write `phase = null` ONLY after 5f, never before.

## Open / Blocked Items

**doc-block-exec (this lane) — `repo: /Users/kimhawk/orca/skills · branch: feature/doc-block-exec · worktree: /Users/kimhawk/orca/skills`**

- **Anti-gaming verify NOT run for Task 3** — the only 5e gate outstanding. The revert test and the
  mutation harness both passed and are recorded below.
- **D3 — OPEN, and still the sole full-suite failure** (#114). `issues=19` vs a floor of 12, up from
  13 at the last handoff. It rises through Tasks 4–5 by construction: PINDRIFT means "a pin into a
  file changed since the document's provenance `0021c77`", and Phase 5 changes exactly those files.
  **5e must not be reported green on a suite carrying this without naming it.**
- **#122 enumeration resize** — filed by `implplan-r20`, deliberately not absorbed on an author's
  authority; it is a population the document publishes. Routing settled, see Next Step 3.
- **Tasks 4 and 5 not started**, carrying three of the five original `OPEN-DECISION (r19, 5d)` lines
  (`:2735` Task 2's shared key predicate — note it was IMPLEMENTED at `d6bab5b`, so verify the
  shipped choice rather than re-deciding; `:3503` and `:3505` for Tasks 4/5).
- **The `.json.pending` parked specs stay** at `docs/03-analysis/doc-block-exec.pending-mutation-specs/`
  as provenance — do not delete them. D2's convention now reads "write the spec at 5e", and Task 3's
  is committed as `h-mad/tests/mutation-specs/doc_block_exec_task3.json`.
- **All 8 commits are PUSHED** (`0 behind / 0 ahead` at write time). `main` is untouched. No PR.

**Carried from the branch predecessor `2026-09-06-feature-doc-block-exec__task1-task2-shipped.md` — every item walked**

- **Five `OPEN-DECISION (r19, 5d)` lines** — **two CLOSED this session** (D6 `:2871`, D7 `:2873`);
  three remain, re-derived at HEAD: `:2735`, `:3503`, `:3505`.
- **The `implplan-author` revision owed for D1/D2/D5** — **CLOSED** in impl-plan v1.56 (`eaa10ca`).
  D2's own path was wrong and is corrected: `git-hooks/pre-push` does not exist; it is
  `h-mad/git-hooks/pre-push`.
- **Mutation rows written at GREEN not RED** — the pattern held; Task 3's spec was written at 5e.
- **#65 carry-forward displacement** — still open, and it fired again. Workaround run, see WARNING.
- **#100 taken-over H1–H9 brief** — unchanged, not started. `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none`.
- **#105 codify "self-counting screens run last, per instrument"** in `h-mad/agents/*-author.md` — unchanged, not started.
- **Tooling worktree `skills-hmad-gate`** (`feature/hmad-class-scored-gate` @ `2f937a3`) — still present, still the operator's call (#111).
- **#112 reviewer-side `class:` tagging / GATE-CLASS field measurement** — still owed. This session ran no audit cycle, so it could not have discharged it.
- **#61 `COLLECT: MISSING` marker-name defect** · **#48 Effort figures unverifiable** · **#42 INHERITED-UNVERIFIED register** · **#36 `tree delta` baseline never 0** (88 untracked `.done` markers, count unchanged) — all unchanged.
- **Evidence-gate corpus outside the repo, not backed up** (`~/.h-mad-corpora/evidence-gate/`) — unchanged.
- **#77 agy leg not dispatched** · **#27, #7, #30, #32, marker-aware reaping** · **#9, #5, #8 P5 backlog** — unchanged.
- **HemaSuite skill-candidate row** — ownership already moved; brief `HemaSuite/docs/handoffs/2026-09-04-main__wrapper-rc-row-is-probably-a-duplicate.md`. `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none`. Not re-checked.
- **Codex quota** — did not bind: **four** codex dispatches this session (Task 3 RED, GREEN, teardown repair, mutation spec), zero `usage limit` hits. `codex_status` remains `available`.
- **`.claude/agents/` CLOSED** · **r15 sheet's false scope clause** — unchanged.

**Taken over 09-05 by `adb05ac8` — `**Handover-From:** HemaSuite · main · session cab14393`** (task **#100**)

- **H1–H9 + tooling defects A/B — owned here, NOT started, unchanged since 09-05.**

**Inherited — `**Handover-From:** HemaSuite · main · session 9d8394fb`** (folded into `hmad-audit-evidence-gate`, task **#91**)

- **Phase 3–4 audit cycle never runs the project test suite** — unchanged as a skill defect. This
  session ran the full suite by hand twice, which is the workaround, not the fix.

**Related lanes, not owned here**

- **`exec agy` lingers after its `result` event** — `docs/handoffs/2026-09-03-main__exec-agy-hang-after-report.md`. Unchanged.
- **HemaSuite `#18 gateway-consolidation`** is HALTED by the operator until the orca/skills h-mad update lands. That update landed. Not acted on: another repo's lane, operator's call.

**New, small, unowned**

- `hmad-dispatch run --help` exits 2 with `unknown option '--help'`. Surfaced by codex probing the
  time-bounder during the Task 3 RED. A gap in the wrapper's own verb; no ticket filed.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_doc_block_exec.py` (Task 3 production)
- `h-mad/tests/test_h_mad_doc_block_exec.py` (39 Task 3 tests + the teardown fix)
- `h-mad/tests/mutation-specs/doc_block_exec_task3.json` (new, 26 rows)
- `docs/01-plan/features/doc-block-exec.impl-plan.md` v1.56 · `.spec.md` v1.65 · `.plan.md` v1.107
- `docs/02-design/features/doc-block-exec.design.md` v1.113
- `docs/03-analysis/doc-block-exec.5d-decisions.md` (D6, D7, D8) · `.task3-red.report.md` (new)

**Uncommitted changes:** none besides the 88 untracked `.done` markers (do not commit).

**Verified figures, each re-derived by the orchestrator at the commit named:**

| what | value | at |
|---|---|---|
| module suite | `96 passed` | `ebd8e27` |
| full suite | `1 failed, 2715 passed` (the 1 is D3) | `0328fc7` |
| revert test | production reverted → `37 failed, 59 passed`, EXACTLY the RED split | `0328fc7` |
| mutations, Task 3 | `ALL_CAUGHT mutations=26 caught=26 survived=0 refused=0` | `ebd8e27` |
| anchors | `ANCHORS_OK specs=1 mutations=26 ok=26 drifted=0` | `ebd8e27` |
| Task 3 RED | `37 failed, 59 passed` against `--expect-fail 37 --expect-pass 59` stated BEFORE the dispatch | `0bfcaa7` |
| Task 3 AC list | 39 test identifiers, span 2952..2975 | `eaa10ca` |
| mutation matrix total | **88** = 87 helper-source + 1 `SKILL.md`, by FOUR independent derivations | `da03ca5` |
| D3 precheck | `PRECHECK: FAIL issues=19` vs floor 12 | HEAD |

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout feature/doc-block-exec       # HEAD ebd8e27, 8 commits, PUSHED
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"; hmad-dispatch env
python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json \
  --feature doc-block-exec --session-id <you>          # then --claim
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/test_h_mad_doc_block_exec.py -q -p no:cacheprovider   # 96 passed
grep -n '^\*\*OPEN-DECISION (r19, 5d):\*\*' docs/01-plan/features/doc-block-exec.impl-plan.md   # expect 3
```

**Related docs:**
- `docs/03-analysis/doc-block-exec.5d-decisions.md` — **D1–D8; read D6, D7 and D8 before Task 4**
- `docs/03-analysis/doc-block-exec.task3-red.report.md` — the 5d dispatch report, persisted out of /tmp
- Commits: `acb2b56` `eaa10ca` `0bfcaa7` `da03ca5` `ecd7bee` `fd4d1d4` `0328fc7` `ebd8e27`
