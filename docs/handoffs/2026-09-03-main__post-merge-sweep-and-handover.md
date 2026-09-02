# Handoff — post-merge verification, three pre-existing defects, handover delivered

**Date:** 2026-09-03
**Branch:** `main`
**Project:** skills (`github.com/BrightGold70/skills`)
**Supersedes:** `2026-09-02-feature-pin-agents-tail-banner__phase7-shipped-live-verified.md`, `2026-09-02-BrightGold70-audit-report-docs-copy__phase7-complete.md`, `2026-09-02-main__audit-report-docs-copy.md`

## Session Summary

Resumed after `pin-agents-tail-banner` merged, finished its owed verification, then drained the
whole carried backlog: **16 items, all closed**. Verified the merge result end to end (suite
**2743/0**, 40 mutation specs, 0 anchors drifted, live pane resolution re-proved on the *installed*
skill). Fixed three pre-existing defects — none belonging to any shipped feature — each
mutation-pinned. Found and fixed a fourth while probing a premise that turned out not to matter.
Corrected two ledger rows that had been wrong for a month. Delivered the HemaSuite
skill-candidates handover on an operator-set gate; the receiver has stamped `**Taken-Over-By:**`,
so pickup is confirmed. 8 commits pushed, `origin/main` at `fc1128e`, working tree clean.

## Key Learnings

- **Every carried premise this session was wrong in a way that changed the fix.** `#13` was
  recorded as failing on ambient state — it *passed* on it, and the file was
  `$TMPDIR/preflight.receipt`, not the repo's `.h-mad/`. `#24`'s recorded fix ("require a boundary
  when the log had prior content") would have broken two sequential agy dispatches sharing a log;
  the real fix was `pre_lines`. `#18`'s premise ("only the 401 case was observed") was irrelevant —
  the guard keys on position relative to the boundary, not on failure cause. Re-probe before acting,
  including on premises you wrote yourself an hour earlier.
- **Verifying closures cannot find a wrongly-open row.** The 2026-09-02 triage spot-checked five
  CLOSED verdicts and all five held — which is exactly why two false OPENs survived in it for a
  month. `#68` and `#86` were adjudicated 2026-08-03; the ledger's evidence line claimed a grep
  "found no decision" when re-running it returns three hits whose **first** is the adjudication
  headline. Check the OPEN rows, not the closed ones.
- **Isolating the filename isolated the wrong noun.** `_absent_pin_file()` varied the basename per
  invocation, but `_receipt_file()`, the await cache and the pane slot dir are all
  `dirname(_pin_file)/…` — so every unpinned test shared one `$TMPDIR/preflight.receipt`, and a
  `verdict=PASS` from one test satisfied another's dispatch gate.
- **A gate can fire early and look authoritative.** The Phase-7 gate opened on
  `phase7_report=YES`, but the report is produced *partway through* Phase 7 —
  `last_completed_phase` still read 6. Waiting for `last_completed=7` is not the fix either; that
  bump is a known laggard with its own backlog row. Artifacts-present **plus branch-quiet** was the
  evidenced condition.
- **h-mad's heartbeat is not a liveness signal.** The nlm lane shipped Tasks 9–11 and a phase
  transition while `owner_heartbeat_ts` sat 92–153 minutes cold. A staleness check on the heartbeat
  alone would have declared a demonstrably working lane dead. Commits are the signal; a lane is
  quiet only when both clocks are cold.
- **The same monitor bug twice: putting a monotonically-increasing field in a change-detection key.**
  `heartbeat_age_min`, then `commit_age_min`. Each made every poll look like a change, so the
  monitor would have emitted every interval until Monitor auto-stopped it — taking the delivery gate
  with it. Caught the second one in a 5-second dry run before arming.
- **A null from one surface is not absence.** `hmad-dispatch worktree-ps` reported the HemaSuite
  worktree's `id` as `None`, which nearly made me skip the stamp as unaddressable; the real
  `worktreeId` was in `orca terminal list`.
- **Four of my own probes returned false results, all caught by controls.** BSD `head -n -1`
  rejected (read as empty); a truth table run under zsh, which does not word-split, degenerating
  every row to `no`; an ad-hoc store parser reporting 270/101 against the census's 316/125; a
  `grep -Fqx "$l"` whose leading `-` parsed as an option. The tooling produced none.
- **`docs/*bug*.md` is an upstream-only genre.** All three existing reports address projects that
  cannot see this tree. That is what settled gate-blindness: our code, our repo, already fixed and
  mutation-pinned, so an issue would file a closed internal bug against ourselves.

## Next Steps

1. **Delete the merged remote branch** — `git push origin --delete feature/pin-agents-tail-banner`.
   Local copy already deleted; fully merged at `bf1c851`. Held back because a remote delete is a
   push, and the session was not authorised for one at the time.
2. **Drop the redundant handover ref in HemaSuite** — `git -C /Users/kimhawk/orca/HemaSuite update-ref -d refs/handoffs/main__skill-candidates-hmad-domain-rows-handover`.
   The brief now lives on `main` as `a96ef37c`; the ref (`5140e559`) was the earlier ref-mode copy
   and is harmless but stale.
3. **Decide on the four orphan `exec-pane agy` processes** — `kill 82161 85642 90677 91239`.
   PPID 1, 2+ days old, from dead `pytest-9102/9124/9132/9187` runs, each dispatching into the real
   agy pane. They survived two full green suites, so they are not presumed harmful — but nothing is
   reaping them (worker-abandon, stablyai/orca#13005).
4. **Finish compacting the auto-memory index** — `~/.claude/projects/-Users-kimhawk-orca-skills/memory/MEMORY.md`
   is **23.1 KB** against a 24.4 KB load limit; the harness asks for < 17.1 KB. This session trimmed
   the 10 longest hooks (24.5 → 23.1 KB), which removes the immediate risk of the index silently
   failing to load, but ~40 more entries still carry summaries where a pointer would do. Do it as
   its own pass: the file is edited concurrently by other lanes (a HemaSuite line appeared mid-edit),
   so replace **whole lines by exact match** and leave non-matching ones alone rather than
   rewriting the file wholesale.
5. **[suggested]** Consider `h_mad_doc_block_exec.py` — decided YES but scoped, not built; it is
   feature-sized and belongs in `/h-mad`. Rationale and the risk constraints are in the
   `docs/skill-candidates.md` row and in this session's `#15` disposition: run under `mktemp -d`,
   opt-in per block by explicit marker, never a blanket sweep of the 68 blocks in the docs.

## Open / Blocked Items

- **Four orphaned `exec-pane agy` processes** — status: alive, deliberate decision deferred to the
  operator. PIDs `82161`, `85642`, `90677`, `91239`; PPID 1; elapsed 2d 13–15h. One belongs to
  `repo: /Users/kimhawk/orca/workspaces/skills/j1-residual-probes`, the other three to this repo.
  See Next Step 3. Three further short-lived siblings (`29185`, `29189`, `29190`) appeared in one
  `pgrep` and were gone by the next call, so something may still be cycling.
- **`origin/feature/pin-agents-tail-banner` still exists remotely** — status: deferred, Next Step 1.
- **`refs/handoffs/main__skill-candidates-hmad-domain-rows-handover` in HemaSuite** — status:
  redundant, Next Step 2. `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: /Users/kimhawk/orca/HemaSuite`.
- **Auto-memory index over its target size** — status: partially done, Next Step 4. 23.1 KB after
  this session's trim of the 10 longest hooks; load limit 24.4 KB, target < 17.1 KB. Not a repo
  file: `~/.claude/projects/-Users-kimhawk-orca-skills/memory/MEMORY.md`, user-global, nothing to
  commit.
- **55 untracked `.done` markers** — status: deliberate, unchanged since 2026-09-01. Do not commit.
  (Was 59 in the predecessor; the difference is markers that were committed with their features,
  not markers lost.)
- **`docs/skill-candidates.md` — 16 open rows (8 `yes`, 8 `maybe`) of 166** — status: open, nothing
  owed unless one is picked up. Was 12 of 161 before this session's scout appended 5 (4 open, 1
  DECLINED). The 7 pre-existing open `yes` rows were each re-checked against source and none was
  closed by this session's work, so nothing was flipped. The predecessor's "3 rows still open" and
  the sibling's "5" are both superseded. **Do not carry this number either** — re-run the census.
  The one new `yes` worth picking up first is `census-script-needs-a-__main__-guard-and-an-import-API`
  (recurrence 3): the parse friction is what keeps producing the wrong ad-hoc counts.
- **HemaSuite skill-candidates backlog** — status: **HANDED OVER and picked up**, no longer this
  lane's. Brief: `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-09-02-main__skill-candidates-hmad-domain-rows-handover.md`
  (`a96ef37c` on their main), carrying `**Handover-From:** orca/skills · main` and now
  `**Taken-Over-By:** HemaSuite · main · session 6065abc9-6cf0-4121-80fe-0ee0ac467b16 · 2026-09-03`.
  `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: /Users/kimhawk/orca/HemaSuite`.
  Contents: 35 open h-mad-domain rows, re-derived; store totals 444 rows / 190 open across 3 stores.
- **Predecessor items, all CLOSED this session:** merge to main (`bf1c851`); post-merge re-verify
  (suite 2743/0, anchors 39→40 specs clean, wires 11/11); live check on the merged skill (`6bdcf3f`,
  evidence in `docs/03-analysis/pin-agents-tail-banner.live-check.md`); the `_cmd_await` flake
  (`6cccc44`); the `test_send_unresolved_agents…` isolation defect (`6cccc44`); archreview per-cycle
  rules (`6bdcf3f`); `h_mad_doc_block_exec` decision (`#15`, scoped yes, not built); `#68` and `#86`
  (were never open — closed 2026-08-03, ledger corrected in `2920658`); gate-blindness issue
  (`fc1128e`, closed not filed); cross-repo INDEX sweep (no damage outside HemaSuite); the
  exec-verdict-laundering non-auth probe (does not reproduce); the five unverified carry-forward
  items (two were real gaps, both now closed by `e57eda0` and `6232187`); the census re-run.
- **From `2026-09-02-main__audit-report-docs-copy.md` (the taken-over brief), both CLOSED:** the
  recipe half of HemaSuite task #33 shipped as the `audit-report-docs-copy` feature and merged
  (`8340780`, `d74be7f`); "do not touch this repo on `feature/pin-agents-tail-banner`" is void —
  that branch merged at `bf1c851` and the local copy is deleted.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/hmad-dispatch.sh` — `_cmd_await` first-check budget; `_verdict_after_boundary` skip floor
- `h-mad/tests/test_hmad_dispatch.py` — `_absent_pin_file` directory isolation, 2 new tests
- `h-mad/tests/test_hmad_dispatch_exec.py` — 1 new test (agy degraded recovery)
- `h-mad/tests/mutation-specs/verdict_laundering.json` — new, 5 mutations
- `handoff/tests/test_handoff_commit_reachability.py` — new, 4 tests
- `h-mad/references/agy-architectural-reviewer-prompt.md`
- `docs/03-analysis/pin-agents-tail-banner.live-check.md`, `docs/carry-forward-triage-2026-09-02.md`,
  `docs/skill-monitoring.md`
- `docs/handoffs/2026-09-02-BrightGold70-audit-report-docs-copy__phase5-tasks-1-4-green.md` (landed on main)

**Uncommitted changes:** none but the 55 deliberate `.done` markers.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
git status --short --branch          # expect: main...origin/main, clean bar 55 ?? .done
python3.11 -m pytest -q              # expect 2743 passed; run ALONE, concurrency invents failures
```

**Related docs:**
- `docs/03-analysis/pin-agents-tail-banner.live-check.md` — the live protocol, incl. that seeding
  needs `pin --force` (plain `pin` refuses a handle absent from `orca terminal list`)
- `docs/carry-forward-triage-2026-09-02.md` — the 17-brief ledger, with this session's corrections
- `docs/skill-monitoring.md` — the 2026-09-03 gate-blindness adjudication, beside the 2026-08-03 ones
