# Handoff — H-MAD candidate rows landed; stale HPW copy retired

**Date:** 2026-11-07
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-06-main__gate-non-py-landed.md
**Next-Session Focus:** No feature is in flight. Choose from three small tool rows in `docs/skill-candidates.md`, or HemaSuite if its bug queue comes first.
**Suggested-Skills:** handoff (resume), verify-hmad-gates (only if a gate row is picked up)

## Session Summary

Done. All 10 H-MAD candidate rows filed 2026-11-05 and 2026-11-06 are on `origin/main`: code at `aed1cae4`, stamps at `6eee7a11`. They add `h_mad_guard_census.py`, `h_mad_assemble_tdd.py --phase review` and `h_mad_branch_evidence.py --full-suite`, and fix prompt text and the harness's `--python` handling. Final reading at `aed1cae4`: 8892 passed, 0 skipped, `ANCHORS_OK` 3208/3208, 29 of 29 affected specs `ALL_CAUGHT`.

Also done: the stale `hematology-paper-writer/` copy is retired from this repo (`ff8234bb`), with its HBV scaffold rescued to HemaSuite `main` (`6ab1ed2df`).

## Key Learnings

- **Reviewing the fixes paid off again.** Round 1 found 2 must-fix. The fixes then introduced 2 new must-fix regressions, one a prompt injection through a `--base-ref` file name, which only round 2 caught. Rounds 3 and 4 found no must-fix. `mutation` scored all of it `ALL_CAUGHT` meanwhile, so the harness would not have caught these.
- **`skill_candidates_census.py --apply` eats the first table line as a header, silently.** Without a header row it read `inserted=9` of 10 and left the first row open. Only reading the count caught it. Filed as a row.
- **A chain of outward steps must gate on each.** `git push origin $RS:refs/heads/main` hit zsh's `:r` modifier, the push failed, and the script still pushed the retirement and deleted the remote rescue branch. The commit survived locally and was restored. Spell `"${RS}:refs/..."`, and test each outward step with `if`.
- **Prepending `/opt/anaconda3/bin` to `PATH` for a measurement disables the new live-interpreter tests.** `python3` becomes the suite interpreter, they skip by design, and `hook_live_interpreter.json` reads `REFUSED`. Measure under the default `PATH`, and read the skip count: 8 skipped was the signal.
- **The HPW plan had two false premises.** "Nothing consumes this copy" missed `hemasuite/src-tauri/src/lib.rs:68`; "HemaSuite's topic is different" was wrong, since it was already HBV, spelled `disease`. I passed the second to the operator as a question before checking it. Both are corrected in the plan's status line.
- **File times sorted by time of day alone mislead.** I read a lane's last write as yesterday's because the sort key had no date. Include the date.
- **A teammate can show `running` while doing nothing.** Lane A wrote nothing for 5.5 hours, with no process, and never answered a stop request. It had finished its edits but not its report. Check file times, not the status.

## Next Steps

1. **Fix the `--apply` header drop** — `handoff/scripts/skill_candidates_census.py:176-184`, row `census-apply-eats-the-first-row-as-a-header`. Either refuse a table with no header separator or treat a row with no `|---|` line as data. Open set: `python3 handoff/scripts/skill_candidates_census.py docs/skill-candidates.md`.
2. **Make the harness tests hermetic under the override** — `h-mad/tests/test_h_mad_mutation_harness.py`, row `mutation-harness-tests-not-hermetic-under-the-override`; lists the 5 failing cases.
3. **Decide on fencing the review prompt** — `h-mad/references/agy-spec-reviewer-prompt.md`, row `review-prompt-inserts-report-unfenced` (`maybe`).
4. **Hawui-Macmini sync** — on that machine: `git pull`; drop the 2026-11-01 `assemble_tdd` stash; compare its 9 Macmini-only env failures with `h_mad_failure_diff.py`. This machine has no route to it (no SSH alias, no Tailscale). The pull now also deletes `hematology-paper-writer/` and brings the new gates and tools.
5. **On HemaSuite's next pull in its main checkout** — it was 1 behind `origin/main` with 363 dirty paths when last read. Afterwards `git -C /Users/kimhawk/orca/HemaSuite branch -d chore/rescue-hbv-scaffold`, which `-d` refuses until then.
6. **Remove the gate-non-py worktree when no longer wanted, copying its state record first if you want it** — `git worktree remove /Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files`.
7. **If `test_heartbeat_stamps_across_three_intervals` fails again, keep the run's `calls` capture before re-running** — `h-mad/tests/test_hmad_dispatch_exec_stamp.py:426`.

## Open / Blocked Items

**From this session:**
- **`--phase review` has never run against real agy.** The printed block ran against `h-mad/tests/stubs`. Its first version also preceded its tests; the operator should know that row was not test-first. Status: open, first real 5e dispatch settles it.
- **`--full-suite` has one real run, on a clone with a doc-only diff** (`FULL-SUITE: PASS passed=8752`). Not yet run after a code diff. Status: open.
- **Census residuals, accepted, no such file at HEAD:** a foreign-interpreter shebang such as `#!/usr/bin/perl` under an allow-listed name reads as a document; a sh or python shebang under an allow-listed name whose HEAD side won't decode or parse makes the census `UNREADABLE`; `--path . --path nope` reads `DONE`, against `helper-scripts.md:25`. Precision was 16% at calibration, so it is a reviewer aid. Status: deferred.
- **Three nits from review 4 and review 3, not fixed:** `--path ../x` prints `reason=git`; `--diff-path -dash.py` is an argparse usage error with no token; the way-out message offers "gitignore" for a tracked name too. Status: deferred, see `docs/03-analysis/2026-11-07-rows-1106/`.
- **Old `hemasuite/` Tauri app in this repo.** `src-tauri/src/lib.rs:68` still defaults `HPW_PATH` to the deleted directory, so its HPW routes return 503 unless `HEMASUITE_SKILLS_ROOT` names a tree holding it. The operator accepted this when choosing to merge. Its sidecar tests (`src-tauri/sidecar/tests/test_hpw*.py`) are outside `testpaths` and were not run. Status: accepted.
- **Static limit on the HemaSuite restores search:** 2525 write sites with fixture-supplied targets were not individually checked. See below. Status: informational.
- **Leftovers:** `/private/tmp/claude-501/-Users-kimhawk-orca-skills/7f75b04a-e075-44c7-be12-2a5bf6994b5b/scratchpad/fs-clone` and its siblings (scratch); 6 `hmad-verify.sh` evidence dirs under `~/.local/state/h-mad/verify-hmad-gates/` (kept by design). A reviewer's parallel driver briefly wrote stray files in parent temp directories including `/private/tmp/tool`; it reports them new and removed, and I confirmed that path is gone. Another reviewer re-ran an `rm -rf` of its own scratch directory by literal path after a bkit hook blocked the first form. Status: harmless.
- **Unattended autopilot session `b1a99532` ended 2026-11-02 without a notepad closeout;** a startup notice raised it. Nothing known to record. **The ai-memory pending handoff** ("write analysis.v2") matched nothing here and was ignored. Status: informational.

**Carried, updated:**
- **Intermittent suite failure, cause unestablished.** `test_heartbeat_stamps_across_three_intervals`; did not fail in this session's three full runs. Status: open, watch.
- **AC-9.3 rests on v4's census.** Unchanged since 2026-11-06, accepted. The new census's calibration listed every hand line but was not used to reopen it.
- **The recorded `READY_TO_MERGE` was earned under a narrowed rubric.** Unchanged since 2026-11-06, accepted.
- **Named hard-link residuals** (same-directory `test_*.py` hard link DENY on Claude, ALLOW on codex and agy; different directory ALLOW on all three). Unchanged since 2026-11-06, deferred.
- **`crash_visible=0/0` on the host specs.** The misleading annotation is fixed (row landed), so 0/0 now reads `crash reading unavailable`. Host-spec rows not read last session stay unread. Status: narrowed, open.
- **Primary record of the 2026-11-04 operator ruling behind the ninth FR-9 refusal: not found.** Unchanged. Needs the operator's memory if it matters.
- **11 nits in `docs/archive/2026-11/gate-non-py-production-files/gate-non-py-production-files.analysis.v5.md`.** Unchanged, deferred.
- **Machine-wide `pkill` disclosure of 2026-11-06.** Unchanged, informational.
- **Feature record exists only in the worktree's gitignored state.** `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files`. Unchanged, informational; see Next Step 6.
- **Leftovers of 2026-11-06** (`.../85400c95-33ed-40d1-b2e9-1d8141402dc6/scratchpad/specv115.ZiEcdd`, `/var/folders/7s/9n332lmj54511rf57fgf8pz40000gn/T/tmp.XQvHmCxplQ`). The delete hook blocked both; not retried. Harmless.
- **Watch-only triage rows; residuals of the 2026-10-31 stamps and 2026-11-01 landings; Run 8 attempts 1–2.** Unchanged since their dates.
- **HemaSuite-owned, not owned here:** drafting quality without CLAUDE.md (next manuscript run); the judge-sdk branch `feat/judge-provenance-non-agent`, another session's. Unchanged. `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none`.

**Closed:**
- **All 10 rows** — LANDED, `aed1cae4`, stamped; the row `crash-visible-empty-denominator` narrows the carried item above.
- **Draft plans** — `backlog-row-cycle` had shipped on 2026-10-18 (status corrected); `hpw-duplicate-copy-retirement` done.
- **BUG-4 record in the CSA worktree** — read-only: owner `094da1cc` is dead (transcript ended 2026-11-04, oracle `enter_autonomous`); current owner `b272bd37` in `bug4-design-audit`. The file looks like a full snapshot of the main store from about 05:30Z on 2026-11-04; the write itself was not observed. Nothing edited.
- **HemaSuite unconditional-restores search** — 0 unconditional restores, 2 conditional (the existing fix), 3 manual generators writing tracked fixtures, 7 not tracked, 1 traced to `tmp_path` by read except `cfg.cache_dir`'s root. No change made. Not handed over: nothing there needs action. Table in `docs/03-analysis/2026-11-07-rows-1106/hemasuite-unconditional-restores.md`.
- **Pre-existing untracked files in `~/orca/skills`** — the operator chose on 2026-11-06 to leave them and stop carrying them. Still there: `.codex/config.toml`, three `docs/03-analysis/2026-10-2*.analysis.md`, `hemasuite/docs/research/`.

## Context for Next Session

**Files touched this session:** `h-mad/scripts/{h_mad_assemble_tdd,h_mad_mutation_harness,h_mad_branch_evidence,h_mad_guard_census}.py`; `h-mad/references/{codex-implementer-prompt,phase5-substeps,failure-recovery,helper-scripts,agy-spec-reviewer-prompt,agy-runtime}.md`; `h-mad/SKILL.md`; tests `test_h_mad_{assemble_tdd,assemble_tdd_agent,mutation_harness,branch_evidence,new_caller_carveout_copies,guard_census,hook_live_interpreter}.py`; specs `assemble_tdd_{agent,prompt_rows,review}`, `mutation_harness`, `branch_evidence`, `guard_census`, `hook_live_interpreter`, `new_caller_carveout_copies`; `docs/skill-candidates.md`; both plan status lines; `hematology-paper-writer/` removed. In HemaSuite: 3 files under `hematology-paper-writer/project_notebooks/`.

**Uncommitted changes:** none but the pre-existing untracked files above.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch
python3 handoff/scripts/skill_candidates_census.py docs/skill-candidates.md
```
Full suite: bare `pytest` under an absolute interpreter and the default `PATH`, about 45 minutes. Naming `h-mad/tests handoff/tests` silently skips 145 tests in `handoff/scripts`.

**Related docs:**
- `docs/03-analysis/2026-11-07-rows-1106/` — the four reviews, the final measurement, the census calibration
- `docs/01-plan/features/hpw-duplicate-copy-retirement.plan.md` — status line carries the corrections
