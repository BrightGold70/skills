# Handoff — Carries closed; codex dispatch now runs the h-mad gate

**Date:** 2026-11-08
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-08-main__quick-fixes-backlog-zero.md
**Next-Session Focus:** Nothing is in flight. Open items: the Macmini sync (#16, on that machine) and the watch on the heartbeat test. A codex session started by hand, outside `hmad-dispatch`, is still ungated.
**Suggested-Skills:** handoff (resume), verify-hmad-gates (only if a gate is touched)

## Session Summary

Done, all pushed (`origin/main` = `1d92ef9c`).
- **Every predecessor item is closed or re-emitted.** First real agy 5e review and `--full-suite` runs (`27614051`); gate-non-py worktree archived and removed (`a7a5b92e`); 2026-11-04 FR-9 ruling located (`55242281`); scout row superseded (`cb4d7311`); all low-priority carries worked (A–F, `docs/03-analysis/2026-11-08-low-priority-carries.md`); HemaSuite-owned items handed over.
- **Measuring codex's hook timeout found a real defect.** Codex 0.167 skips untrusted hooks, so the h-mad Phase-5 gate never ran under dispatch. Operator chose route B, which is now built (`09c36baf`, `1d92ef9c`).
- Last full suite: 8983 passed, 0 failed, at `1d92ef9c`'s tree. ANCHORS_OK 3235/3235.

## Key Learnings

- **Codex 0.167 runs a hook only with a persisted trust record or `--dangerously-bypass-hook-trust`.** The record is keyed by the `hooks.json` absolute path plus a hash, so every Orca worktree starts untrusted, and the 2026-09-29 trust on HemaSuite was gone by today. The gate's own tests drive the hook script directly, so they could not see this. Proof: a real `codex exec` appended to a listed file; with the flag, the real gate denied it.
- **Codex hook `timeout` is in seconds and is honoured** (10 → killed at ~8–10 s). With no timeout, or with 120, a hook still running at ~38 s is cancelled (`tool call cancelled`).
- **An absence claim nearly dropped four items.** I first wrote off the 2026-10-31 residuals as "no list survives"; the list was in `2026-10-31-main__skill-backlog-clusters-a-d.md:75-79`. Corrected (`0e3beea7`) before it shipped.
- **Re-shaping a guarded line breaks a mutation anchor in a spec you did not touch.** `ec253592` left `install_check_roots.json` `AH2` with hits=0. Run `--check-anchors` over all specs, not only the ones edited.
- **A fix can make an older mutation row equivalent.** `all(())` is True, so the hard-link fix left `CX-DOCDATA-DIRECTORY` surviving. `resolved.names and` restored it.

## Next Steps

1. **Hawui-Macmini sync** (#16), on that machine:
   - `git pull` (brings everything up to `1d92ef9c`);
   - drop the 2026-11-01 `assemble_tdd` stash;
   - compare its 9 Macmini-only env failures with `h_mad_failure_diff.py run --base <ref> -- <tests>`.
   - Codex there also gets the dispatch bypass now. Watch dispatch stderr for `NOT enforced`.
2. **If `test_heartbeat_stamps_across_three_intervals` fails, keep that run's `calls` capture before re-running.** `h-mad/tests/test_hmad_dispatch_exec_stamp.py:426`. It passed in both full suites this session.

## Open / Blocked Items

**From this session:**
- **A codex session started by hand (not `hmad-dispatch`) is still ungated.** It needs `--dangerously-bypass-hook-trust` or a one-time interactive approval per worktree path. Status: accepted, operator-informed.
- **Adding any other hook to a repo's `.codex/hooks.json` makes dispatch withhold the bypass**, with stderr `the h-mad gate is NOT enforced`. Status: by design (`_codex_hook_trust_arg`, `h-mad/scripts/hmad-dispatch.sh`).
- **Two hook-trust lines are unanchored by design** (`local dir=…`, `hooks=…`), plumbing whose mutants only crash; plus the `if python3` and `for` lines, whose behaviour is covered by HT-ONLY-GATE. Status: accepted.
- **Rust default toolchain changed** to `stable-aarch64-apple-darwin` (operator-approved). It was x86_64 only, with no Rosetta, so `cargo` could not run. Status: informational.
- **Hard-link kinds still differ by host** (Claude `no-test-resolved`, codex/agy `test-missing`); all three DENY. Status: accepted, pinned.
- **Leftovers:**
  - this session's scratch dirs (`codexhome.*` — credentials deleted, only codex's MCP cache remains — `cxwork.*`, `cxto.*`, `gateprobe.*`, `sbx.*`, `tcprobe.*`) under `/private/tmp/claude-501/-Users-kimhawk-orca-skills/f7b82980-9b1f-439b-b8a2-d143865d9b9f/scratchpad/`;
  - the 43 `.md` reports in the three old scratchpads (7f75b04a, 651783e3, 85400c95) not found in `docs/`, kept unreviewed.

  Status: harmless.
- **Scout rows filed at closeout** (`docs/skill-candidates.md` §2026-11-08 carries-closed-codex-gate-armed): `hand-inserted-mutation-rows` (maybe; point SKILL.md/phase5-substeps at `--append-row`), `codex-hook-trust-unseen-by-install-check` (maybe). Status: open.
- **Foreign process:** PID 32561 (zsh, ~31 h old, the 2026-11-07 session's scratch). Not mine, left running. Status: informational.

**Carried from 2026-11-08 (quick-fixes-backlog-zero), updated:**
- `review_fence` / `--phase review` never run on real agy: CLOSED `27614051` (VERDICT COMPLIANT).
- `--full-suite` one real run on a doc-only diff: CLOSED `27614051` (8372 passed on a code diff).
- `argument_not_printable` refuses NBSP/U+202F/ZWJ: accepted, unchanged.
- Two `_enc` print sites unpinned: accepted, unchanged.
- Broken `.py` + broken spec reports `unreadable-file` first: accepted, unchanged.
- 651783e3 leftovers (`gitmv.ASBM`, `depth.BjUw`): CLOSED, deleted. Its review drafts were already in `docs/`.
- Foreign PID 25981: exited. PID 32561: see above.
- Scout rows: `full-suite-runs-on-a-moving-tree` CLOSED SUPERSEDED `cb4d7311`; `hand-applied-single-mutants` (no) unchanged.
- Old Tauri `HPW_PATH` default: CLOSED `d04d7fe9`. It also fixed the sidecar's `PROJECTS_DIR`=cwd bug.
- HemaSuite restores static limit; autopilot `b1a99532`; ai-memory pending handoff (re-shown this session, matched nothing); AC-9.3 on v4's census; narrowed `READY_TO_MERGE`; `pkill` disclosure; Run 8 attempts 1–2; watch-only rows 19 and 51: settled, no next action. Recorded in the carries doc §Settled.
- Heartbeat test: watch, unchanged (passed twice). Next Step 2.
- Same-directory hard-link residual: CLOSED `4dbd5055`. The different-directory case was already consistent.
- `crash_visible=0/0` on host specs: narrowed, unread host-spec rows stay unread. Unchanged since 2026-11-06.
- 2026-11-04 FR-9 ruling: CLOSED `55242281`.
- 11 nits in analysis v5: CLOSED `cbef15f3`.
- gate-non-py feature record in worktree state: CLOSED `a7a5b92e`; worktree removed, branch deleted.
- 2026-11-06/07 scratch leftovers: CLOSED, deleted. The 6 `verify-hmad-gates` evidence dirs are kept by design.
- 2026-10-31 and 2026-11-01 residuals: CLOSED, see the carries doc §C/§F.
- HemaSuite-owned items: **handed over** to HemaSuite (`d6a371568`, brief `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-11-08-main__skills-owned-hemasuite-items.md`), taken over by HemaSuite session `0b65b121`. One item is open there: drafting quality without `CLAUDE.md`.
- HemaSuite pull + `chore/rescue-hbv-scaffold`: closed 2026-11-08 (predecessor).
- Pre-existing untracked files in `~/orca/skills`: not carried, by operator choice on 2026-11-06.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/{hmad-dispatch.sh,h_mad_derive_test_path.sh,h_mad_archreview_cycle.py,h_mad_install_check.py}`
- `h-mad/hooks/{h-mad-codex-tdd-gate.py,h-mad-agy-tdd-gate.py,h-mad-tdd-gate.sh}`
- `h-mad/tests/test_{hmad_dispatch_exec,h_mad_tdd_judge,h_mad_archreview_cycle,h_mad_install_check_roots,h_mad_tdd_judge_listing,h_mad_codex_tdd_gate_non_py,h_mad_agy_tdd_gate_non_py,h_mad_tdd_gate_non_py}.py`
- `h-mad/tests/mutation-specs/{codex_hook_trust,codex_gate_listing,agy_gate_listing,listing_matcher,tdd_judge_resolution,archreview_cycle,install_check_roots}.json`
- `h-mad/references/{codex-runtime,inline-protocols,helper-scripts}.md`
- `hemasuite/src-tauri/src/{lib,tests}.rs`, `hemasuite/src-tauri/sidecar/{routers/hpw.py,tests/test_hpw_manuscript.py}`
- `docs/skill-candidates.md`
- `docs/03-analysis/2026-11-08-{first-real-5e-runs/,low-priority-carries.md}`
- `docs/archive/2026-11/gate-non-py-production-files/{state/,…ruling-2026-11-04.md,…report.md}`

**Uncommitted changes:** none but the pre-existing untracked files.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch
python3 handoff/scripts/skill_candidates_census.py docs/skill-candidates.md   # expect OPEN(yes+maybe)=2 (this closeout's two maybe rows)
```

**Related docs:**
- `docs/03-analysis/2026-11-08-low-priority-carries.md` (carries A–F and the codex trust finding)
- `docs/03-analysis/2026-11-08-first-real-5e-runs/`
- `h-mad/references/codex-runtime.md` §hooks (the trust paragraph)
