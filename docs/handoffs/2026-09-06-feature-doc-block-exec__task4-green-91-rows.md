# Handoff — doc-block-exec Task 4 RED+GREEN shipped; matrix and spec agree at 91; 5e gates still owed

**Date:** 2026-09-06
**Branch:** `feature/doc-block-exec` — **PUSHED** (`b5f33b5..81c0f36`, `0 behind / 0 ahead`), after
the harness finished and the tree restored. The first attempt was correctly BLOCKED; see Next Step 7
for why, because the reason is a standing hazard rather than a one-off.
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-06-feature-doc-block-exec__merge-settled-task4-next.md (branch predecessor), 2026-09-05-main__audit-loop-never-runs-repo-suite.md and 2026-09-05-main__hmad-audit-loop-evidence-from-gateway-consolidation.md (taken over 09-05; re-emitted below, not re-read this session)

## Session Summary

Executed the operator's §D10 merge, settled the last three r19 OPEN-DECISIONs, and took Task 4
through RED and GREEN. **Eight commits, none pushed.** `doc_block_exec_task3.json` is merged and
deleted; the design's matrix and the spec now hold the same 91 names; Task 4's 62 tests are written
and passing and the CLI, stream artifacts and SKILL.md registry entry are implemented. **5e is NOT
complete** — the revert test and the independent anti-gaming verification have not been run, and a
full 91-row harness pass was still executing when this was written. The claim is HELD, not released,
because a mutation harness is mid-run against the working tree.

## Key Learnings

- **The orchestrator was the least reliable measuring surface in the loop, by a wide margin.** Seven
  measurement errors were mine; every one was caught by an author, an auditor or by a number that
  disagreed, and **none** by re-reading my own work. Each returned a *smaller, cleaner-looking*
  figure: a `sed` truncation that hid the value past the cut; `^- \[ \] AC-` missing a `- [ ] Parser`
  bullet; a count taken on a file another author was actively writing; "42 specs" published from a
  pre-merge `Counter`; "in any argv position" generalised past the five shapes I actually ran;
  "three sites" relayed from an author's owed list as though measured (the real number was 20); and
  a verification instruction requiring `MATRIX-NOT-ON-DISK = 30` that was already stale when I wrote
  it. The pattern is not carelessness — it is that a decision sheet and a dispatch brief are read by
  four authors and gated by nobody.
- **`--expect-fail` inverted twice under three different greps.** A bare sweep of the task section
  gives **64** (it admits Task-3 cross-references named in prose); `^- \[ \] AC-` gives **61**; the
  document's OWN published awk, keyed on `^- \[ \]`, gives **62**. Run the command the document
  defines, never one that reproduces its number — and the classification predicate is membership of
  the shipped FILE, never of an earlier task's checklist: two Task 4 tests appear in earlier
  checklists as forward references, so a checklist-based classification publishes 60.
- **A guard's row is not covered by a neighbouring row whose killer cannot reach it.** §D13's whole
  argument: `rollback-leftover-unreported`'s killer drives the ROLLBACK path and never enters the
  alias branch, so deleting the alias read-back leaves it green and the mutant survives. That is a
  sharper test than "is the guard needed", and it is what made the 91st row non-optional.
- **A numeric value sweep cannot see a spelled-out total.** The design writes "Ninety-one rows,
  ninety-one mutations"; `grep -c '[Nn]inety'` returns 6 and every `\b90\b`/`\b91\b` sweep this
  feature has ever run was blind to it. Add spelled-out forms to any total sweep.
- **A wrong path and a true zero are the same number.** plan-author's `0 5 4 6` control had a `0`
  that came from sweeping `docs/00-spec/…`, a path that does not exist — `git show <sha>:<absent>`
  fails to stderr and `grep -c` scores an empty stream. It shipped both scopes per element in
  v1.111 (`1 5 4 6` whole-file, `0 5 3 4` body) with plan 5/5 as the non-diverging control.
- **A resend is not a tail.** Asking a truncated author to "send only the tail" produced a full
  re-generation that truncated at the identical byte and delivered none of the requested material.
  What works: name everything already received, forbid restating it, and pose numbered questions.
  Putting the owed list FIRST in the dispatch contract worked better still — the last two reports
  cut on trailing detail instead of on the findings.

## Next Steps

1. ~~Read the 91-row harness result.~~ **DONE — `MUTATION: ALL_CAUGHT mutations=91 caught=91
   survived=0 refused=0 unreadable=0`**, the orchestrator's own run, 0 survivor lines, agreeing with
   codex's report. Nothing owed here.
2. ~~Confirm the tree is restored.~~ **DONE.** `git status --short` clean, and restoration was
   verified by EXECUTING the shipped entry point rather than grepping the source: `--help` → exit 0
   (D11's broadened contract, live), `--nope` → `DOCBLOCK: BAD_ARGS message="the following arguments
   are required: doc, --heading"`, and an import with `sys.modules` registered gives `main` callable
   with `VERDICT_TABLE` at 23 entries, matching AC-4.2's 23 heads. **Note the probe that failed
   first**: `module_from_spec` WITHOUT registering in `sys.modules` raises `AttributeError:
   'NoneType' object has no attribute '__dict__'` from inside `@dataclass`, because dataclasses
   resolves `sys.modules.get(cls.__module__)`. That is the probe's bug, not the helper's — do not
   read it as a broken restore.
3. **The 5e revert test for Task 4**, which has NOT been run. **This is now the top open item.** Production is committed now, so the
   `git stash push -u` sequence in h-mad §5e is not the destructive case it warns about — but follow
   it anyway: revert production only, confirm the RED split returns EXACTLY `62 failed, 98 passed`,
   restore, confirm green returns, and assert the revert LANDED with an existence check
   (`git diff --quiet` is trivially clean for an untracked path and cannot see this failure).
4. **The independent anti-gaming verification** (`references/codex-verifier-prompt.md`) — module
   count, test-discrimination audit, quote the source line for each pinned property, full suite vs
   the reference, every reported count cross-checked a second way. Never dispatched this session.
5. **Task 5**, then **5f**: `h_mad_baseline_sha.py --branch feature/doc-block-exec --trunk main`
   reports `UNVERIFIED reason=no_impl_plan candidate=0885152` **by design**; `0885152` IS the 5c sha.
   Then `h_mad_wire_registry.py verify --base 0885152 --rootdir . --testpath h-mad/tests`.
   Note Task 5 writes `doc_block_exec_wire.json`, which does not exist yet — the design's
   verification block labels that absence as schedule, not defect.
6. **5g** — the D3 provenance bump lands here and nowhere earlier; `phase = null` ONLY after 5f.
7. **PUSH — attempted at closeout and correctly BLOCKED. Do it AFTER step 2, not before.**
   `git rev-list --left-right --count @{u}...HEAD` → `0 9`. The pre-push hook returned:

       drifted: drain-unbounded         :: scripts/h_mad_doc_block_exec.py :: hits=0, expected exactly 1
       drifted: drain-oserror-unmapped  :: scripts/h_mad_doc_block_exec.py :: hits=0, expected exactly 1
       ANCHORS: ANCHORS_DRIFTED specs=47 mutations=585 ok=583 drifted=2

   **This is NOT anchor drift. It is the harness holding that file mutated mid-run.** The hook
   sweeps anchors over the WORKING TREE and the harness deliberately mutates the working tree, so
   the two are mutually exclusive and running them concurrently produces a guaranteed false
   `ANCHORS_DRIFTED`. The hook is behaving correctly and the two anchors are fine.
   **Do NOT `--no-verify`.** Wait for the harness (step 1), confirm restoration (step 2), then
   `git push origin HEAD` — the sweep will then read `ANCHORS_OK` and the push will land. If it
   still reports these two after the tree is restored, THAT is real drift and needs re-anchoring.

## Open / Blocked Items

**doc-block-exec — `repo: /Users/kimhawk/orca/skills · branch: feature/doc-block-exec · worktree: /Users/kimhawk/orca/skills`**

- **THE CLAIM IS STILL HELD** by session `49c8fdee-3f5c-4cd3-93c3-c14c4e889554`, deliberately, because
  a harness was mutating the tree at handoff. Release it once step 2 confirms restoration:
  `h_mad_state_write.py docs/.bkit-memory.json --feature doc-block-exec --release --session-id 49c8fdee-3f5c-4cd3-93c3-c14c4e889554`.
  Note the heartbeat is frozen at `2026-09-06T11:23:31Z` — `--claim` is the only heartbeat writer
  (open item #126 below), so the claim reads stale however live the session was.
- **5e INCOMPLETE** — revert test and anti-gaming verify not run (Next Steps 3 and 4). Task 4's code
  and tests are committed and green; the *gates that prove the tests are real* are not.
- **D3 — SETTLED at remedy 3; its obligation is live through 5g.** `assert 19 <= 12`. Full suite at
  the GREEN tree is `1 failed, 2782 passed`, and the 1 is D3. `PRECHECK: FAIL issues=19` on the
  impl-plan (8 PINDRIFT + 11 PLACEHOLDER) is that same red and did NOT rise this session.
- **THREE consecutive handoffs have skipped the automation scout**, this one included (context
  budget). It is the only writer of `docs/skill-candidates.md`; its open rows decay until someone
  runs it, and 4 of 5 open rows were already-shipped work the last time anyone looked. **Run it
  EARLY next session, not at closeout** — that is why it keeps being dropped. Task #49.
- **The `.json.pending` parked specs stay** at `docs/03-analysis/doc-block-exec.pending-mutation-specs/`.
  Nothing detects a parked spec never moved back (D2's residual, task #142).
- **#126 heartbeat that does not beat** — OPEN, diagnosed to the line, NOT implemented. Fix is in
  `h_mad_state_write.py` (`--claim` at `:286` is the only heartbeat writer); `h_mad_state_ownership.py`
  is correct. This session is a live instance: one beat, then nothing for hours.
- **#146 — TWO orchestrator errors in §D11, both bracket-corrected in the sheet**, both mine, both
  found by authors: "30 of the 42 specs" (it is 41 — a post-merge claim on a pre-merge denominator)
  and "in any argv position" (false; the axis is *recognised as an option*, since `-h` short-circuits,
  `d.md --heading --help` is consumed as a VALUE, and `-- --help` is the positional). The SPEC ships
  the correct form at AC-5.6; only the sheet was wrong.
- **#145 AC-1.8 spec debt** — an over-broad universal the design's codex leg filed as false, reported
  and unrouted since spec v1.63. Three rounds have not routed it. Route it into the next spec dispatch.
- **#129 partition-parts species** · **#105 self-counting screens** — NEW/open, both owed to
  `h-mad/references/measurement-discipline.md`. This session produced two more worked examples for
  them: the spelled-out-total trap and the wrong-path zero.
- **#128 fresh-branch predecessor gap** — OPEN, emission-policy call.
- **#100 taken-over H1–H9 brief** — unchanged, not started. `repo: /Users/kimhawk/orca/skills ·
  branch: main · worktree: none`. **Handover-From:** HemaSuite · main · session cab14393.
- **#91 inherited** — "Phase 3–4 audit cycle never runs the project test suite", a skill defect.
  **Handover-From:** HemaSuite · main · session 9d8394fb. Unchanged.
- **#111 tooling worktree** — merge commit `f2b3d74` verified; `../skills-hmad-gate @
  feature/hmad-class-scored-gate` still present (re-verified this session). Removal is the operator's:
  `git worktree remove ../skills-hmad-gate && git branch -d feature/hmad-class-scored-gate`.
- **#112** · **#48** · **#42** · **#77** · **#27** · **#20** · **#9/#5/#8** · **#7 (closes with 5e)** — unchanged.
- **Evidence-gate corpus outside the repo, not backed up** (`~/.h-mad-corpora/evidence-gate/`) — unchanged.
- **HemaSuite skill-candidate row** — ownership already moved; brief
  `HemaSuite/docs/handoffs/2026-09-04-main__wrapper-rc-row-is-probably-a-duplicate.md`. Not re-checked.
- **Codex quota** — did NOT bind this session; four codex dispatches all completed. `codex_status`
  remains `available` and codex-cli is 0.153.2.
- **`hmad-dispatch run --help` exits 2** with `unknown option '--help'`. Unchanged, no ticket (#143).

**Related lanes, not owned here**

- **`exec agy` lingers after its `result` event** — unchanged; agy was not dispatched this session.
- **HemaSuite `#18 gateway-consolidation`** — HALTED by the operator; another repo's lane, not acted on.

## In-Flight Processes

**None — the one process this session handed off has since COMPLETED and is recorded here rather
than deleted, so a reader can tell a finished job from one that was never started.**

| PID | Command | Log | Started | Elapsed | Result |
|---|---|---|---|---|---|
| (bg `b3s2b9jtb`) | `h_mad_mutation_harness.py tests/mutation-specs/doc_block_exec.json` from `h-mad/` | `<scratchpad>/harness91.txt` | ~22:10 | ~20 min | `MUTATION: ALL_CAUGHT mutations=91 caught=91 survived=0 refused=0 unreadable=0`; tree restored, verified by execution |

`<scratchpad>` = `/private/tmp/claude-501/-Users-kimhawk-orca-skills/49c8fdee-3f5c-4cd3-93c3-c14c4e889554/scratchpad`.

## Context for Next Session

**Files touched this session:** `h-mad/scripts/h_mad_doc_block_exec.py` · `h-mad/tests/test_h_mad_doc_block_exec.py` ·
`h-mad/tests/mutation-specs/doc_block_exec.json` (+ `doc_block_exec_task3.json` deleted) · `h-mad/SKILL.md` ·
all four phase documents · `docs/03-analysis/doc-block-exec.5d-decisions.md`

**Uncommitted changes:** the harness's in-flight mutation only, plus the 88 untracked `.done` markers
(do not commit).

**Verified figures — each stamped at its own commit, re-derived by the orchestrator not carried:**

| what | value | at |
|---|---|---|
| merged spec after §D10 | 60 rows, `ALL_CAUGHT 60/60`, closure predicate `0` | `7afc0ef` |
| Task 4 RED | `62 failed, 98 passed in 42.22s`, zero wrong-reason reds | `0251b9e` |
| Task 4 GREEN, module | `160 passed in 56.25s` | `a10eacb` |
| Task 4 GREEN, full h-mad | `1 failed, 2782 passed in 439.12s` (the 1 is D3) | `a10eacb` |
| matrix ↔ spec after the 91st row | both 91; `NOT-IN-MATRIX []`, `MATRIX-NOT-ON-DISK []` | `70efed2` |
| mutation split | 90 helper + 1 `SKILL.md`; `25 + 7 + 28 + 31 = 91` | `70efed2` |
| impl-plan noise floor | `PRECHECK: FAIL issues=19` = 8 PINDRIFT + 11 PLACEHOLDER, unmoved | `70efed2` |

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout feature/doc-block-exec        # 8 commits ahead of origin, 0 behind
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"; hmad-dispatch env
git status --short | grep h_mad_doc_block_exec.py    # MUST be empty — harness restored
grep -E '^MUTATION:' /private/tmp/claude-501/-Users-kimhawk-orca-skills/49c8fdee-3f5c-4cd3-93c3-c14c4e889554/scratchpad/harness91.txt
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json \
  --feature doc-block-exec --release --session-id 49c8fdee-3f5c-4cd3-93c3-c14c4e889554
```

**Related docs:**
- `docs/03-analysis/doc-block-exec.5d-decisions.md` — §D10 (merge, executed), §D11/§D12 (settled, one
  bracket-corrected twice), §D13 (the 91st row, settled by design-author on killer reachability)
- The predecessor handoff, for the full 5e narrative behind the merge decision
