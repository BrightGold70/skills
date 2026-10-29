# Backlog triage — 2026-10-25

**Scope:** every unresolved item carried by this repo's handoff chain. The chain was walked from
`2026-10-25-main__step11-extract-done-blind-labels.md` back through each "Carried from" link to
`2026-10-02-main__v111-review-loop-closed.md`. Also covered: the two sibling 2026-10-25 handoffs,
recent takeovers, and plan docs that never got a report.
**Method:**
- A read-only agent checked every item against the tree, where a check was cheap: `git log -S`,
  grep, `ls`, branches, stashes, worktrees, `ps`.
- The orchestrator spot-checked three of the agent's claims (rows 9, 14, 40) and all three held.
- Takeover and state-file findings were checked directly.
**Machine:** Hawui-Macmini. This Mac is **not** the one that holds the Task 15 run state, and it
has no HemaSuite checkout. Both facts set many rows' class.
**HEAD at triage:** `main` = `8118f6fc`. Branch `feat/wire-pin-runner` is in progress.

Source abbreviations, all under `docs/handoffs/`:
- **S11** = `2026-10-25-main__step11-extract-done-blind-labels.md`
- **R8** = `2026-10-25-main__run8-done-authors-test-merged.md`
- **WR** = `2026-10-25-main__wire-registry-and-bkit-g001.md`
- **T15** = `2026-10-24-main__task15-runs4-7-14h-green.md`
- **R3** = `2026-10-23-main__grok-run3-agy-gate-halt.md`
- **V02** = `2026-10-02-main__v111-review-loop-closed.md`

## Summary

| class | count |
|---|---|
| CLOSED | 5 |
| OPEN-ACTIONABLE-HERE | 18 |
| NEEDS-DECISION | 4 |
| BLOCKED-OTHER-MAC | 6 |
| BLOCKED-HEMASUITE | 5 |
| WATCH-ONLY / NO-ACTION | 18 |
| UNVERIFIABLE | 3 |
| **total (de-duplicated across docs)** | **52** (+1 below, row 53) |

**Pending handovers:** none. `pending-handovers` returned rc=1.

## Findings that change how the backlog is read

### This Mac's h-mad state file is a stale copy

`docs/.bkit-memory.json` is untracked and stays on each machine. Here it was last written
**2026-10-18 22:37** (742 bytes). It shows `grok-audit-surface` at **phase 3**, owned by session
`1f39eb76` with a 10-18 heartbeat. The handoffs record that feature in Phase 5, with its claim
released on 2026-10-25 on the other Mac.

So this Mac's resume checker answers against week-old state. The `resume_manual` reported for
`grok-audit-surface` at the start of this session came from this file.

**Rule until reconciled:**
- Make no claim and no release on this Mac.
- When the Task 15 run state is copied over (`~/.local/state/h-mad/grok-audit-surface/`), copy the
  other Mac's `docs/.bkit-memory.json` with it, or treat that Mac's file as the real one.

### Recent takeovers

| brief | Taken-Over-By | claim here | items |
|---|---|---|---|
| `2026-10-25-main__wire-registry-and-bkit-g001.md` (from HemaSuite `c1e6df26`) | session `40f31cca`, 2026-10-25 (`59d1174c`) | **none.** No record; the checker returns `start_fresh`. Any claim is on the other Mac. | G-001: CLOSED (`c0c73e51`). Playwright pin: CLOSED as a decision (`8118f6fc`), implementation on `feat/wire-pin-runner`. `missing=268`: BLOCKED-HEMASUITE (row 5). |
| `2026-10-24-main__gate-task-authors-test.md` (from HemaSuite `245c1f4a`) | session `40f31cca`, 2026-10-24 | none | CLOSED: merged in `7373cb1b`. Worktree and local branch gone. The remote branch was deleted 2026-10-26 (row 9). |

Both briefs are stamped and committed, so neither will be offered again.

## Actionable here (18)

The quickest are marked ⚡.

| # | item | source | evidence | next action |
|---|---|---|---|---|
| 40 ⚡ | `h_mad_mutation_harness.py:2300` SyntaxWarning, `'return' in a 'finally' block` | T15:110 | Still warns on every harness call (seen this session) | Move the `return 2` out of the `finally` under TDD |
| 14 | 14h residual: `home + "/…"` has no `rstrip` | T15:67-69 | `h-mad/scripts/h_mad_tool_calls.py:168-169`. **Parked fix:** `60635019` on `park/grok-14h-home-rstrip`, RED→GREEN, 399 tests passing. **Operator 2026-10-25:** do not merge outside `grok-audit-surface`'s own flow, because Task 15 calibration is in progress. **The security review widened it:** `needle_dirs` (`needle + "/"`), `root` and `checkout` are not normalized either, and fail open the same way. | After step 11, fold it in as a feature task that normalizes every comparison base in `scan_log`, or refuses non-normalized `--home/--root/--checkout/--needle-dir` in `main()` |
| 15 | 14i residual: canary prompt paths are unquoted | R8:81 | Deliberate per impl-plan `:2787`. Changing it would change the calibration prompt mid-Task-15. **Operator 2026-10-25:** parked for the feature. | Revisit after step 11, inside the feature |
| 29 ⚡ | 14c `status_dir` note missing from the impl-plan and design | T15:90; R3:75-78 | Code at `h_mad_grok_containment.py:135`; no text in either doc | Add the note to the impl-plan |
| 46 ⚡ | V02 task #28: run `test_the_warn_and_target_fractions_still_match` by name | T15:117 | Never run | Run it by name after the current suite |
| 17 | Todo #5: test-boundary and oracle fields with a deterministic check | T15:72 | No commits since 10-23 | Plan as its own feature or worktree |
| 18 | Todo #6: handoff redaction, next-session focus, scout remedies | T15:73 | No commits | Plan as its own feature |
| 27 | Todo #4: skills defects 1-12, judge-mapping defect, agy-1.4.6, dedupe against `f2a37a71` | T15:86-89; R3:55-66; R8:90 | Defect list at R3:55-66; no judge-mapping row in skill-candidates | File the rows in `docs/skill-candidates.md` with the dedupe map |
| 33 | Phase 6 residuals: T19 RMGUARD (D16), T22 grep-whole-source | T15:96-98 | `test_grok_audit_surface_containment.py:507` | Fix during Phase 6 |
| 35 | Owed measurement-class notes (T19, T20, T25, T26, marker 177, D18) | T15:102; R3:105-113 | No commits | Write them into the measurement doc |
| 38 | 7 older `yes` rows (2666, 2667, 2672, 2673, 2677, 2678, 2682), plus the agy install-check gap at `:2673` | T15:105; R3:118-119 | Re-probed in `4e4a3b04`; still open | Work them as features |
| 39 | Mutation-harness interpreter row, `backlog_cycle` LOW residuals, census `--help` | T15:106-109 | Not re-run | Fix after the current suite |
| 44 | Meta: handoff WRITE does not verify the state it claims | T15:115; R8:105 | `docs/skill-candidates.md` row, `yes` | Make WRITE read `owner_session_id` before writing "released". Today's stale-state finding is a fresh instance of this. |
| 9 | Remote branch `origin/fix/gate-task-authors-test` still exists | S11:93; R8:67 | `2d087a39`, already merged into `origin/main` | **CLOSED 2026-10-26:** deleted on origin with the operator's OK, along with 5 other merged remote branches |
| 6 | Playwright WIRE-PIN: implementation | S11:90; WR:50 | Decision `8118f6fc`; branch `feat/wire-pin-runner` | Finish the branch (task #7) |

Rows 6 and 9 are counted as CLOSED in the summary, because their original items are done; the
open work listed here is what follows from them. The 18 OPEN-ACTIONABLE rows are 14, 15, 17, 18,
27, 29, 33, 35, 38, 39, 40, 44, 46, and the plan-backlog items below.

## Needs a decision (4)

| # | item | source | the choice |
|---|---|---|---|
| 16 | Policy B: the agy gate denies `run_command` and writes when there is no git toplevel | T15:70 | In scope or not. No commit since 10-23; runs do not need it. |
| 19 | Todo #7: progressive disclosure (82/192 tests and 7/12 modules read `SKILL.md`) | T15:74 | Schedule it or drop it. Currently deferred. |
| 28 | Task 14d AC.5 load-sensitivity | T15:90; R3:74 | Whether to split the two real-cycle ids into their own module. See `grok-audit-surface.task14d-gate-2026-10-23.md`. |
| 47 | V02 optional agy live smoke | T15:118 | Run it or drop it. |

## Blocked on the other Mac (6)

| # | item | source | next action |
|---|---|---|---|
| 1 | Task 15 step 11: blind labels and score commit | S11:74; R8:62; T15:52 | On the run Mac (or after copying its state), follow S11 Next Steps 1-7. Ask the operator before the push. |
| 2 | Record the labeller-package deviation (design rows 122-123) | S11:77 | Write it into the Task 16 measurement doc |
| 23 | Local-only `.claude/skills/verify-hmad-{gates,claims}/` | T15:77 | Copy or commit them if they are wanted elsewhere |
| 24 | TLA+ findings F1-F4 (only F2 is cross-referenced) | T15:78 | File F1-F4 from the run Mac, with todo #4 |
| 26 | Tasks 16-17, 5f/5g, Phases 6-7 | T15:85; R8:89 | Start after the score sha (row 1) |
| 34 | ~179 leaked `hmad_exec_prompt.*` temp files | T15:101 | Clean up the run Mac's temp dir |

## Blocked on HemaSuite (5)

| # | item | source | next action |
|---|---|---|---|
| 5 | wire-registry `verify` reports `missing=268` (plus the 5f nested `--rootdir` note) | S11:84; R8:63,68; WR:49 | Run the S11:86 repro where the HemaSuite checkout exists, under TDD (task #2) |
| 41 | HemaSuite feature/204 `no-mutation-spec` | T15:113 | HemaSuite's call |
| 49 | HemaSuite WSG pointer `2026-09-14-main__wsg-backlog-two-items-owed-here.md` | T15:121; V02:89 | Open it from the HemaSuite checkout |
| 50 | 2026-10-23 sender-side pointer owed by HemaSuite | T15:123; R8:107 | Owed by HemaSuite's next WRITE |
| 52 | HemaSuite worktree's uncommitted `.gitignore`, `.mcp.json`, `graft/INDEX.md` | R8:63 | Not ours; leave them |

## Closed (5)

| # | item | evidence |
|---|---|---|
| 6 | Playwright WIRE-PIN representation (the decision) | `8118f6fc` |
| 7 | bkit G-001 heredoc false positive | `c0c73e51`. Fixed upstream in 2.1.40; a new bare-tag false negative was patched locally and filed as ww-w-ai/bkit-claude-code#161. |
| 8 | Skill-candidates reconcile (26 `yes` rows; also V02's "reconcile not run") | `4e4a3b04` |
| 9 | Worktree `../skills-gate-authoring` and local branch `fix/gate-task-authors-test` | Both gone. The remote branch was deleted 2026-10-26 (see Actionable). |
| 37 | HemaSuite PID 70888 and escape-diff backup | `ps -p 70888` finds no process |

## Unverifiable (3)

| # | item | source | why |
|---|---|---|---|
| 3 | h-mad claim on `grok-audit-surface` | S11:78; R8:70; T15:60 | This Mac's state file is stale (see above). Check on the run Mac with `h_mad_resume_decision.py`. |
| 4 | Session task list #7, #16-#21 | S11:79 | That task list belonged to another session and is not stored in the repo. This table replaces it. |
| 20 | Untracked mattpocock analysis doc (another session's) | T15:75; R8:84 | Not in this clone or in git history. Its owner should commit it on the other Mac. |

## Watch-only / no action (18)

These are standing rules, evidence-only dirs and never-stage notes. Keep them; there is nothing to
do.

- **Never score:** run 8 attempts 1-2 (11); run dirs 4-7 and their incident docs (13); halted run
  dirs `…T015212Z`, `…T044856Z`, `…T222714Z` (31).
- **Calibration tip:** `8f8deaf1` is the `--parent` for the score commit (12).
- **Keep:** the old S2 positive-control data `run-ab2c85dc2e25/` (36).
- **Codex pin:** `term_134b0865…` is stale; re-pin before any codex dispatch (10; task #6).
- **Never stage:** the foreign untracked files (21) and `.codex/config.toml` (22).
- **pstack rule:** `~/.claude/rules/pstack-models.md`, absent here (25).
- **Defect 11:** the `implementation_authors` misattribution; the field is append-only (30).
- **Run-Mac only:** `.h-mad/phase5-shell-allow` and the root `.venv` (32).
- **Other clone:** the foreign `stash@{0}` (`resolved-model`, `7541628`); do not touch it (42).
- **Standing notes:** the Bash pin blast radius, the `.git/info/exclude` entries, row 1412
  liveness, `review_independence_unrecorded`, and the advisor ceiling (43).
- **Expected:** the plan-audit exit stamp is never written; Phase 5 is the gate (45).
- **Deferred by design:** V-11.1 residuals, round-22 F2 (still without a fresh review), and the
  tdd-gate-fail-opens bookkeeping (48).
- **agy-1.4.6 flake:** passed in both full suites on 10-25; file it only if it fails again (51).

## Row 53 — not carried by any handoff

`docs/03-analysis/grok-audit-surface.plan.delta-review.5b2df07-20261018T130440Z.md.txt` has been
untracked in this working tree since at least the start of this session, and every handoff says
not to stage it. **CLOSED 2026-10-26:** deleted on the operator's instruction. It was a 1 KB
dispatch stub for an advisory delta review (dated 2026-10-18), with no findings in it.

## Plan docs without a report (not deep-checked)

All in `docs/01-plan/features/`:
- **Draft, awaiting approval:** `backlog-row-cycle`, `hpw-duplicate-copy-retirement`.
- **Plan header with no status line:** `claude-context-reduction`, `hpw-csa-unified-ui`,
  `hpw-csa-unified-ui-v2`, `hpw-protocol-extraction`.
- **Other:**
  - `grok-audit-surface`: active; this is the Task 15 feature (row 1).
  - `hemasuite-100-percent`: no status line; reads "Current Match Rate 85%".
  - `hpw-csa-macos-app`: marked SUPERSEDED, so effectively closed.

## Suggested order

1. **Finish task #7** (`feat/wire-pin-runner`): the full suite, then mutation scoring, review and
   merge.
2. **Quick wins on this Mac:** rows 40, 14, 46 and 29. The first two are small fixes under TDD, and
   the last two are a test run and a doc note.
3. **Decisions:** rows 16, 19, 28 and 47, the remote-branch deletion (9) and row 53.
4. **On the run Mac:** copy the state over, including `docs/.bkit-memory.json`. Then do row 1, which
   unblocks 2 and 26.
5. **With a HemaSuite checkout:** row 5 (task #2).

## Outcome — same session, 17:24–21:40 KST (Hawui-Macmini)

Everything below was merged to `main` after a full suite showing 0 new failures against `main`'s
environmental baseline, plus an independent review whose must-fixes were all closed.

| merged | what it closes |
|---|---|
| `94cf6d7b` feat/wire-pin-runner | task #7: `runner` field + `unverifiable` bucket (operator decision `8118f6fc`), 3 review rounds, mutation 13/13 |
| `a9c6c692` fix/independent-bugs | row 40 (harness SyntaxWarning, PEP 765); skill-candidates: bold `STATUS` verdicts, `--suite-cmd` via shlex, harness `--python` |
| `039837bd` fix/batch-2 | skill-candidates: LIVE takeover (operator decision: refuse only on proof the owner itself is live; claim, release and the resume oracle share `owner_proven_live`), Codex prompts name the gate's read verbs, §5e revert never pops a foreign stash |
| `da1584c7` fix/batch-3 | skill-candidates: harness `--only NAME`, assembler `--prompt`/`--out` naming; also a `NameError` on a no-spec harness run |

The census moved from OPEN 32 (yes 26) to **OPEN 24**: 8 rows closed, and 248 are terminal.

**Parked, not merged:** `park/grok-14h-home-rstrip` (`60635019`), row 14. Fold it into
`grok-audit-surface` after step 11, together with the security review's point that every comparison
base should be normalized. Row 15 was skipped for the same reason (calibration prompt).

**Still open:** all BLOCKED-OTHER-MAC rows (1, 2, 23, 24, 26, 34), all BLOCKED-HEMASUITE rows
(5, 41, 49, 50, 52), all NEEDS-DECISION rows (16, 19, 28, 47), and the actionable rows not
reached: 17, 18, 27, 29, 33, 35, 38 (the remaining older `yes`
rows), 39 (except the interpreter row), 44 and 46. Rows 9 and 53 were closed on 2026-10-26.

## Outcome — 2026-10-26/27 (Hawk-MacStudio)

| row | outcome |
|---|---|
| 2 | Closed. Task 16's measurement doc records the labeller-package deviation (merged `2614364b`). |
| 14 | Closed. Folded in as Task 14j, which normalizes every `scan_log` comparison base (merged `c0300c1c`; parked `60635019` superseded, branch deleted). |
| 15 | Left as designed (Task 14i), reviewed inside Task 14j. |
| 16 | **Operator 2026-10-27: dropped.** The audit path never needs Policy B (agy reads and delivers via `out`). Reopen only if agy must write or run commands outside a git tree. |
| 19 | **Operator 2026-10-27: kept deferred.** Do it only as a planned feature with a before-and-after invocation measurement (82+ test modules couple to SKILL.md's text). |
| 28 | **Operator 2026-10-27: split.** Move the two real-cycle test ids out of the path-scope module so the judged module stays well under the 40 s `JUDGE_BUDGET_S`. Open, actionable. |
| 47 | **Operator 2026-10-27: dropped.** Superseded by Task 15's 9 live agy audit passes (delivered=9, CONTAINMENT CLEAN on all 9). |

Task 15 step 11 and Task 16 are done: score sha `05cc3935`, `SEEDSCORE: PASS`. The Mac Studio's
bkit is now 2.1.40 with the G-001 patch applied (`9e5b39d0`).

## Outcome — 2026-10-27, rows 27 and 29 (Hawk-MacStudio, branch `docs/backlog-rows-27-29`)

Every item was re-probed at `190939a8` before it was filed.

| row | outcome |
|---|---|
| 27 | Closed. `docs/skill-candidates.md` §"2026-10-27 — backlog-triage-row-27 (filed)" files 7 new rows: #3, #7, #8, #11, the judge-mapping defect, F1, and F2+F3 as one row. Cross-referenced instead of filed: #1 (= HS2), #2 (= HS7), #4 (agy half fixed by 14e `84d069ed`, codex half on HS1), #5 (= HS6), each with a 2026-10-27 RE-PROBED note on its `f2a37a71` row; #10 is the 2026-10-20 `--check-anchors` row, now with its cause (the gate does not trust the interpreter the assembler writes). Not filed: #6 (already handled by `change-reviewer`), #9 (row 16, dropped), #12 (row 28, split), F4 (bkit's writer targets `.bkit/state/memory.json`, not h-mad's file; the rename that made them share it is guarded by `951c99f2`), and the agy-1.4.6 test (passed again on agy 1.4.7; stays row 51). |
| 29 | Closed. Impl-plan v1.21 (Task 14c `assembler-read`) and design v1.20 (D21) record the operator-accepted `status_dir = here.parent if here.name == "scripts" else here` at `h-mad/scripts/h_mad_grok_containment.py:135` (commit `9f8c96c6`; R3 says `:134`), and the reason: the plan's `git -C <here>/..` contradicts Task 14c's own sha256 fixture. |

## Outcome — 2026-10-29 (Hawk-MacStudio, `main`)

| row | outcome |
|---|---|
| 1, 26 | Closed earlier (`grok-audit-surface` Phase 7 archived in `860f4aa3` on 2026-10-28). |
| 17 | Closed (`f54ba2de`). `hmad-test-boundaries` shipped in full (`h_mad_test_boundaries_check.py`, `test_boundaries_gate.json` `ALL_CAUGHT 18/18`). |
| 18 | Closed (`8597bce9`). Handoff redaction rule, artifact reference guidance, optional `**Next-Session Focus:**` / `**Suggested-Skills:**` headers in `handoff/SKILL.md`, and the 6 scout remedy classes (`navigation-pointer`, `existing-tool-repair`, `deterministic-check`, `review-rule`, `tool-improvement`, `skill-candidate`) in `handoff/references/automation-scout.md`, pinned by `TestWriteVerifiesClaimedStateAndRedactionAndScoutRemedies`. |
| 23 | Verified on Mac Studio: `.claude/skills/verify-hmad-gates/bin/hmad-verify.sh doctor` → `HMAD-VERIFY-DOCTOR: PASS`; `.claude/skills/verify-hmad-claims/run.sh core` → `OK core expected pass got pass 3s 11798 distinct states found`. |
| 24 | Closed (`27a383e4`, row 27). TLA+ findings F1–F4 were re-probed and filed in `docs/skill-candidates.md` (`:2834-2835`). |
| 28 | Closed (`234f9be0`). Split the two real-cycle test IDs (`test_real_audit_cycle_wrapper_passes_path_scope_to_scanner`, `test_real_audit_cycle_wrapper_halts_on_out_of_scope_log_before_scoring`) into `h-mad/tests/test_grok_audit_surface_path_scope_real_cycle.py` and updated `grok_audit_surface.json`; `test_grok_audit_surface_path_scope.py` dropped from `18.60s` to `3.13s`, well below the 40 s `JUDGE_BUDGET_S`. All 578 tests across the 10 `grok_audit_surface` modules pass. |
| 33 | Closed (`290459c0`). T19 `RMGUARD` refusal fixture (`test_exec_grok_rmguard_refuses_to_remove_outside_staging_prefix`) + `grok-tmp-rmguard-always` mutant added and verified killed; T22 `test_quarantine_never_deletes` scoped to AST function spans of `quarantine`, `_names`, and `_matches` (`quarantine-move-copies` mutant verified killed). |
| 34 | Closed (`290459c0`). Verified 0 leaked `hmad_exec_prompt.*` files remain in `/private/tmp` or `$TMPDIR`; recorded closed in `docs/archive/2026-10/grok-audit-surface/grok-audit-surface.phase5-s0c-notes.md`. |
| 35 | Closed (`290459c0`). Recorded the 8 Phase 5 measurement-class notes (T19, T20, T25, T26, marker 177, D18) in `docs/03-analysis/grok-audit-surface.measurement.md` and `docs/archive/2026-10/grok-audit-surface/grok-audit-surface.phase5-s0c-notes.md`. |
| 38 | Closed (`5746b8bb`, plus `patch-verify-on-update.sh` in `d13f5e8f`). `h_mad_install_check.py` reads `.skill-lock.json` and emits non-blocking `AGENTS_SIBLING_COLLISION:<path> kind=<kind>` details (`install_check_roots.json` `ALL_CAUGHT 18/18`); `h-mad/SKILL.md` item 3 documents the same-session `general-purpose` + full role-file fallback; all four author contracts require literal phase-scoped audit filenames in Version History. Census `OPEN` moved `31 → 26`. |
| 39 | Closed (`066c34df`). `skill_candidates_census.py` `--help` / `-h` prints usage and exits 0 (`help-flag-treated-as-store-path` `ALL_CAUGHT 1/1`); all 5 LOW review residuals in `h_mad_backlog_cycle.py` fixed (`backlog_cycle.json` `ALL_CAUGHT 20/20`). |
| 44 | Closed (`8597bce9`). `handoff/SKILL.md` §"Gather context before drafting" item 9 requires WRITE to run `h_mad_resume_decision.py`, read `owner_session_id` via `.get()`, and verify claimed files exist on disk before drafting; both `skill-candidates.md` rows stamped `LANDED`. |
| 46 | Closed. `test_the_warn_and_target_fractions_still_match` in `h-mad/tests/test_h_mad_context_budget_docs.py` executed by name and passed (`1 passed in 2.65s`). |
| 5, 41, 49, 50, 52 | **Handed over to `HemaSuite@main` (2026-10-30).** Ownership transferred to `/Users/kimhawk/orca/HemaSuite` (`main`) via `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-10-30-main__skills-handover-todos-8-9-12.md` (along with `document-intake-source-review::Task 6` `WIRE-RUNNER` and the 5f nested-`--rootdir` note). |

## Outcome — 2026-10-30 (Hawk-MacStudio, HemaSuite takeover & closure of rows 5, 41, 49, 50, 52)

| row | outcome |
|---|---|
| Todo #8 | Closed (`11874bce` on `BrightGold70/hemasuite-document-workbench`). `document-intake-source-review::Task 6` in `docs/archive/2026-10/document-intake-source-review/document-intake-source-review.impl-plan.md` now declares `**WIRE-RUNNER**: \`playwright\`` and `.h-mad/wires.jsonl` carries `"runner": "playwright"` (`WIREPIN: PASS tasks=7 wiring=2 unpinned=0 mislabeled=0`). |
| 5 | Closed. Re-ran the `missing=268` repro in `/Users/kimhawk/orca/workspaces/HemaSuite/hemasuite-document-workbench`: the 268 records partition into **1** Playwright pin (`document-intake-source-review::Task 6`, now `unverifiable=1`), **5** `@pytest.mark.parametrize` pins (`document-intake-source-review::Task 5 (WIRE 1..5)`, Hypothesis (a) — 28 + 7 = 35 parametrized items), **262** foreign sub-project pins outside `--testpath hemasuite/tests` (255 `hematology-paper-writer` + 7 `clinical-statistics-analyzer`, Hypothesis (b)), and **0** collection errors (Hypothesis (c) false; `225 tests collected`, exit 0). Fixed `h_mad_wire_registry.py` (`_base_node_id`, `_resolve_pin`, `_cli_pin`) and `h-mad/SKILL.md:541` under TDD (`wire_registry_runner.json` `ALL_CAUGHT 16/16`); all 5 `document-intake-source-review::Task 5` records now resolve and verify (`verified=5 unverifiable=1`). |
| 41 | Closed. Recorded explicit `--no-mutation` waiver on the 4 one-off analysis probe scripts (`docs/archive/2026-10/synopsis-path-preflight/probes/*.py`) in `docs/archive/2026-10/synopsis-path-preflight/synopsis-path-preflight.report.md` (v1.1); all production modules of `feature/204-synopsis-path-preflight` closed Phase 5 with `ALL_CAUGHT` on their mutation specs. |
| 49 | Closed. Updated `docs/handoffs/2026-09-14-main__wsg-backlog-two-items-owed-here.md` (`202 matching lines / 341 AC-x.y occurrences / 96 distinct AC ids`) and recorded `## Closure`: Item 1 (`#56`) closed via `docs/04-report/features/wsg-56-impl-plan-ac-enumeration.probe.v1.md` (`015d2bd1`), Item 2 (wire registries) closed via `website-source-grounding.wire-registry-decision.md` (`c8b0ed79`). |
| 50 | Closed. Recorded the sender-side pointer (`handed over to skills@main, brief docs/handoffs/2026-10-23-main__hemasuite-hmad-skill-defects.md; filed in orca/skills:docs/skill-candidates.md in commit f2a37a71`) in `docs/handoffs/2026-10-23-BrightGold70-hemasuite-document-workbench__intake-a1-task2-red.md` and committed it to `HemaSuite@main`. |
| 52 | Closed. Verified `.mcp.json` clean and reverted the uncommitted `.gitignore` (`/graft/`) and `graft/` regeneration diffs in `/Users/kimhawk/orca/HemaSuite`. |



