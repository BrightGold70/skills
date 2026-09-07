# Handoff — doc-block-exec: 5e's document debt closed at total 90; four tooling defects fixed; Tasks 4–5 still unstarted

**Date:** 2026-09-06
**Branch:** `feature/doc-block-exec`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-06-feature-doc-block-exec__task3-shipped-5e-gates.md (the branch predecessor), 2026-09-05-main__audit-loop-never-runs-repo-suite.md and 2026-09-05-main__hmad-audit-loop-evidence-from-gateway-consolidation.md (taken over 09-05; re-emitted below, not re-read this session)

> **The predecessor's standing WARNING about `carry-forward-sources` is FALSIFIED — do not carry it.**
> It told every WRITE on this branch to run `--branch main` as well. The doc it said went missing,
> `2026-09-06-main__doc-block-exec-5b-exit-and-hmad-class-gate.md`, IS named in the predecessor's own
> `**Supersedes:**` field, so the chain absorbed it and withholding it is correct. Running the second
> invocation re-offers work the chain already owns. This handoff ran the single documented invocation.
> A REAL and separate gap remains, filed as #128: a branch with NO handoff of its own gets no
> predecessor at all.

## Session Summary

Resumed by `/handoff read` into a claim collision, took the feature over on operator authority, and
took `doc-block-exec` from "5e BLOCKED by D9" to **5e's document debt fully closed**. Six commits,
**all unpushed**. D9 closed and mutation-verified (`98 passed`, `ALL_CAUGHT 28/28`); D3 settled by
the operator at remedy 3; the 5e document round ran four parallel authors and established that the
mutation total is **90** and that the long-published `88` was never a file count. Four h-mad/handoff
tooling defects were fixed with RED-proven tests. **Tasks 4 and 5 are still unstarted** — Task 4 has
zero CLI tests — so Phase 6 and the Phase-7 gate are unchanged and distant.

## Key Learnings

- **`88` was never a file count, and the question that asked "which file?" was malformed.** The
  number's AUTHORITY is the design's mutation table, its VALUE is 90, and the file that REALIZES it
  is `doc_block_exec.json`. Three authors gave three answers because each named a different one of
  those three; none was wrong. A dichotomy offered to parallel authors can be false in a way none of
  them can see alone.
- **`no_report` was the GUARD, not the defect.** On plan c83 the agy leg was handed a 440 kB prompt
  for `plan-v83` and returned a complete, confident, all-clean verdict for `impl-plan-v38` — a
  document it had audited four hours earlier. Nothing in the audit loop caught it. The collector's
  strict banner wait did, by refusing to harvest. Any proposal to loosen `collect-report` must not
  relax the banner match.
- **A partition whose TOTAL is right proves nothing about its PARTS.** plan-author published a
  four-way split of 73 that reconciled exactly while three of four parts were wrong, because the last
  bucket absorbed the remainder. A remainder bucket cannot fail to reconcile, so reconciliation
  carries no information. Filed as #129; not yet in `measurement-discipline.md`.
- **Excluding a whole class is not the same as excluding the noise in it.** The first `tree delta`
  fix dropped ALL untracked entries and was caught by the suite: a brand-new source file IS work, so
  that traded a false positive for a false negative arguing FOR re-running work that already ran —
  the worse direction. Name the class by what it is (h-mad's `.done` markers), never by an accident
  it shares with real work.
- **A cold heartbeat is not death, and the 2h window is a deadline every LIVE session races.** Owner
  22e0a5f1 was open and working with a heartbeat 110 min cold; the oracle then released its claim on
  wall-clock. This session's own claim was 748 s from the same fate while committing. `--claim` is
  the only writer of `owner_heartbeat_ts`; ordinary work goes through `--set`, which never beats it.
- **Two of the four author briefs I wrote carried stale task-list claims** (#30 fixed 14 revisions
  earlier, AC-5.6 discharged at spec v1.65). Both authors verified instead of complying, so neither
  cost anything. The task list is itself a carried-premise store and is not evidence.

## Next Steps

1. **Push the 6 commits** — `git push origin HEAD`. Fast-forward, `0 behind / 6 ahead` at write time.
2. **Decide the per-task merge question** (the one thing 5e left genuinely open). Does
   `h-mad/tests/mutation-specs/doc_block_exec_task3.json` merge into `doc_block_exec.json` before 5f?
   impl-plan v1.58 records it as a checkable 5e obligation (`ls h-mad/tests/mutation-specs/ | grep -cE
   '_task[0-9]+\.json$'` must print `0`, and the staged file's absolute
   `/opt/anaconda3/bin/python3.11` `target_command` reconciled); design v1.114 lists it as an open
   residual; plan v1.108 declines to ratify either intent. **No document, decision sheet or commit
   message states the intent behind the per-task naming** — plan-author looked and found nothing.
   Operator call, not a reading.
3. **Task 4** (CLI + registry) — not started, `grep -c 'def test_cli_'` on
   `h-mad/tests/test_h_mad_doc_block_exec.py` returns **0**. Carries `OPEN-DECISION` `:3503`
   (alias-refusal unlink read-back) and `:3505` (`--help` bypass), plus the D6 row
   `substitution-result-not-passed-to-run_block` and its specified killer
   `test_cli_subst_value_reaches_the_child`.
4. **Task 5**, then **5f**:
   `python3 ~/.claude/skills/h-mad/scripts/h_mad_baseline_sha.py --branch feature/doc-block-exec --trunk main`
   reports `UNVERIFIED reason=no_impl_plan candidate=0885152` **by design**; `0885152` IS the 5c sha.
   Then `h_mad_wire_registry.py verify --base 0885152 --rootdir . --testpath h-mad/tests`.
5. **5g** — the D3 provenance bump lands here and nowhere earlier, then `phase = null` ONLY after 5f.
6. **Re-claim the feature before touching anything** — this session RELEASED its claim at close
   (see Open Items). `h_mad_resume_decision.py --state docs/.bkit-memory.json --feature doc-block-exec
   --session-id <you>` then `--claim`.

## Open / Blocked Items

**doc-block-exec (this lane) — `repo: /Users/kimhawk/orca/skills · branch: feature/doc-block-exec · worktree: /Users/kimhawk/orca/skills`**

- **The per-task merge question — OPEN, and the only thing 5e left undecided.** See Next Step 2.
- **D3 — SETTLED at remedy 3, but its OBLIGATION is live through 5g.** `assert 19 <= 12` at
  `aa89d62`; `PRECHECK: FAIL issues=19` is byte-identical to the freeze blob's 19, so the batch
  introduced none. **5e must not be reported green on a suite carrying this without naming it**, and
  that holds for every claim from here to 5g. A grep tally is NOT the figure — `grep -c PINDRIFT` 10
  + `grep -c PLACEHOLDER` 12 = 22 on the same capture; those are grep OUTPUT LINES.
- **Tasks 4 and 5 not started**, carrying `OPEN-DECISION` `:3503` and `:3505`. `:2735` (Task 2's
  shared key predicate) was IMPLEMENTED at `d6bab5b` — verify the shipped choice rather than
  re-deciding it.
- **The `.json.pending` parked specs stay** at `docs/03-analysis/doc-block-exec.pending-mutation-specs/`
  as provenance — do not delete. Nothing detects a parked spec never moved back (D2's residual).
- **The claim was RELEASED at close.** No session holds `doc-block-exec`. Re-claim before working.
- **All 6 commits are UNPUSHED.** `main` untouched. No PR.

**Carried from the branch predecessor — every item walked**

- **D9** — **CLOSED** at `2b64747`. `98 passed`, `ANCHORS_OK 28/28 drifted=0`,
  `ALL_CAUGHT mutations=28 caught=28 survived=0`. Clause (c), the vacuity repair, is a TEST fix that
  no mutation row can express; it is evidenced separately in `docs/03-analysis/doc-block-exec.d9-proof.md`
  §C and must not be reported as covered by `ALL_CAUGHT`.
- **#122 enumeration resize** — **CLOSED**, and the answer is **EIGHT, not the seven that was
  called "settled routing"**. `kill-skipped-after-collect-failure` also reds
  `test_poll_oserror_is_launch_failed_collect`, a different row's canonical key;
  `stderr-not-closed` reds only its own and is NOT a member. Measured with an unmutated control
  (`1 failed, 97 passed`) isolating a `git status` scratch artifact. The brief's basis
  `test_cli_bad_timeout_values` **does not exist yet** and is written as a Task-4 claim.
- **#65 carry-forward displacement** — **FIXED** at `8f29826`, RED-proven, and the predecessor's
  WARNING falsified (see the box at the top). The real remaining gap is **#128**.
- **#61 `COLLECT: MISSING` marker-name defect** — **FIXED** at `aa89d62`. Both owed items discharged;
  the c83 investigation it asked for produced the agy wrong-document finding above.
- **#36 `tree delta` baseline** — **FIXED** at `f67454e`. Old delta 89 (never 0), new delta 1, 88
  markers excluded, control confirms a new untracked non-`.done` file still counts.
- **#30 awk boundary half-fix** — **CLOSED**, premise stale by 14 revisions; the published screen
  already applies both-sides POSIX boundaries to every alternative (143 / 116 / 49, re-run).
- **#126 heartbeat that does not beat** — OPEN, diagnosed to the line, NOT implemented. Fix is in
  `h_mad_state_write.py` (`--claim` at `:286` is the only heartbeat writer);
  `h_mad_state_ownership.py` is correct and needs no change. Two backward-compatible options and a
  third orthogonal one recorded on the task. Deliberately not started at ~60% context.
- **#129 partition-parts measurement species** — NEW, not yet in `measurement-discipline.md`.
- **#105 self-counting screens** — unchanged, now with a live worked example from spec-author.
- **#100 taken-over H1–H9 brief** — unchanged, not started. `repo: /Users/kimhawk/orca/skills ·
  branch: main · worktree: none`.
- **#111 tooling worktree `skills-hmad-gate`** — re-probed, merge commit `f2b3d74` confirmed, safe to
  remove. Destructive, so operator's call:
  `git worktree remove ../skills-hmad-gate && git branch -d feature/hmad-class-scored-gate`.
- **#112 GATE-CLASS field measurement** · **#48 Effort figures unverifiable** · **#42
  INHERITED-UNVERIFIED register** · **#77 agy died running pytest** · **#27 marker-aware reaping** ·
  **#9/#5/#8 P5 backlog** · **#7 docsections dedupe (closes with 5e)** — all unchanged.
- **Evidence-gate corpus outside the repo, not backed up** (`~/.h-mad-corpora/evidence-gate/`) —
  unchanged.
- **HemaSuite skill-candidate row** — ownership already moved; brief
  `HemaSuite/docs/handoffs/2026-09-04-main__wrapper-rc-row-is-probably-a-duplicate.md`. Not re-checked.
- **Codex quota** — did not bind. `codex_status` remains `available`.

**Taken over 09-05 by `adb05ac8` — `**Handover-From:** HemaSuite · main · session cab14393`** (task **#100**)

- **H1–H9 + tooling defects A/B — owned here, NOT started, unchanged since 09-05.**

**Inherited — `**Handover-From:** HemaSuite · main · session 9d8394fb`** (task **#91**)

- **Phase 3–4 audit cycle never runs the project test suite** — unchanged as a skill defect.

**Related lanes, not owned here**

- **`exec agy` lingers after its `result` event** — unchanged.
- **HemaSuite `#18 gateway-consolidation`** HALTED by the operator until the orca/skills h-mad update
  lands. That update landed. Not acted on: another repo's lane.

**New, small, unowned**

- `hmad-dispatch run --help` exits 2 with `unknown option '--help'`. Unchanged, no ticket.

## Context for Next Session

**Files touched this session:**
- `h-mad/tests/test_h_mad_doc_block_exec.py`, `h-mad/tests/mutation-specs/doc_block_exec_task3.json`
- `h-mad/scripts/h_mad_collect_report.py` + `h-mad/tests/test_h_mad_collect_report.py`
- `h-mad/scripts/hmad-dispatch.sh`
- `handoff/scripts/handoff_paths.py` + `handoff/tests/test_handoff_carry_forward.py`
- `docs/01-plan/features/doc-block-exec.{impl-plan,spec,plan}.md` · `docs/02-design/.../design.md`
- `docs/03-analysis/doc-block-exec.5d-decisions.md` · `.d9-proof.md` (new)

**Uncommitted changes:** none besides the 88 untracked `.done` markers (do not commit).

**Verified figures, each re-derived by the orchestrator at the commit named:**

| what | value | at |
|---|---|---|
| module suite | `98 passed` | `2b64747` |
| mutations, Task 3 | `ALL_CAUGHT mutations=28 caught=28 survived=0` | `2b64747` |
| anchors | `ANCHORS_OK specs=1 mutations=28 ok=28 drifted=0` | `2b64747` |
| full h-mad suite | `1 failed, 2717 passed` (the 1 is D3) | `2b64747` |
| h-mad + handoff suites | `1 failed, 2987 passed` — DIFFERENT CORPUS, not comparable to 2717 | `aa89d62` |
| D3 precheck | `assert 19 <= 12` | `aa89d62` |
| mutation matrix total | **90** = 89 helper + 1 `SKILL.md`; walk `32 + 28 + 30 = 90`, `NOT-IN-MATRIX = []` | `bdc606e` |
| exec suite | `64 passed` | `f67454e` |

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout feature/doc-block-exec        # HEAD f67454e, 6 commits, UNPUSHED
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"; hmad-dispatch env
python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json \
  --feature doc-block-exec --session-id <you>          # then --claim; nobody holds it
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/test_h_mad_doc_block_exec.py -q -p no:cacheprovider   # 98 passed
grep -c 'def test_cli_' h-mad/tests/test_h_mad_doc_block_exec.py    # expect 0 — Task 4 not started
```

**Related docs:**
- `docs/03-analysis/doc-block-exec.5d-decisions.md` — **D1–D10; read §D3 (settled), §D9 (closed) and
  §D10 (settled, with both orchestrator errors recorded) before Task 4**
- `docs/03-analysis/doc-block-exec.d9-proof.md` — the isolated mutation proofs, incl. clause (c)
- Commits: `2b64747` `8f29826` `aa89d62` `6a1693c` `bdc606e` `f67454e`
