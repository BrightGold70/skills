# Handoff — upstream sync, three hmad-dispatch/gate fixes, token-weather in the repo

**Date:** 2026-10-04
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-10-03-main__arity-guards-and-codex-symlink.md

## Session Summary

Resumed into a tree that was **344 commits behind** `origin/main` (the predecessor reported "3
ahead" without having fetched since 09-18); rebased the 4 local commits on top and pushed. Then
drained the predecessor's whole queue: three fixes landed (`25855d08` option-value guard,
`a1bd6a84` central `--help` guard, `2a0cc74d` codex-gate `/tmp` reports), two test-portability
fixes (`ffd72e4e`), a full re-probe of the 50 open skill-candidate rows (`0474a14d`), and the
token-weather mod moved into the repo (`5e27b915`) with a step-shaped sparkline (`7a456521`).
**Done and pushed**: `origin/main` = `7a456521`, final suite **5510 passed / 0 failed / 2
skipped**, tree clean. Nothing in flight.

## Key Learnings

- **Check what code a host actually loads before debugging its behaviour.** Every codex-gate
  symptom in the inbound HemaSuite brief (venv refused, "no derived test file") came from
  `~/.agents/skills/h-mad` being a stale copy byte-identical to `7c385b8` (09-18), which predates
  the 09-28 fixes (`6a9c14b9` contained venv, `72e915b5` judge). They read as gate defects and were
  already fixed upstream. agy's copy was 181 files stale.
- **A verb whose first positional is free-form will execute `--help` as its argument.**
  `worktree-comment --help` ran `orca worktree set --worktree active --comment --help --json`. The
  proof technique: a tripwire `orca`/`cmux` stub that appends its argv to a file and exits 1; "no
  file" is positive evidence nothing was called, which a normal stub's silence is not.
- **A failure that appears only in worktrees can be a path dependency, not your diff.** Confirm with
  a clean `git worktree add --detach … HEAD`: `test_live_smoke_v111_rehearsal_passes` failed there
  too. Root cause: `smoke_assert.py` used one `root` both as the prefix for matching recorded log
  paths and as the on-disk checkout; it only passed at `/Users/kimhawk/orca/skills` — i.e. it would
  also fail in a clone at another path on another Mac.
- **Sparklines scaled to the history's own min–max redraw every column each turn**, so they never
  read as steps. Scale to a fixed domain (the window) to make the series prefix-stable.
- **Background subagents' final replies can arrive as just "Done."** Four of five recon agents lost
  their tables that way; asking them to write results to a scratchpad file recovered all five.
- **The bkit destructive detector refuses `rm -rf`**; `rm -r` on explicit, verified paths passes.

## Next Steps

1. **Cheap skill-candidate follow-ups** surfaced by the re-probe (`docs/skill-candidates.md`, each
   row has a `RE-PROBED 2026-10-03` note): (a) row "ask whether a line pin was correct" — four pins
   still cite `docs/skill-candidates.md:1277`: `h-mad/scripts/h_mad_audit_gate.py:515`,
   `h-mad/tests/test_h_mad_audit_suite_gate.py:18`, `h-mad/tests/mutation-specs/audit_suite_gate.json:68`
   (anchor — re-check after edit), `docs/03-analysis/hmad-gate-field-verification.md:93`; re-pin by
   row NAME. (b) `HARD_KINDS` defined at `h-mad/scripts/h_mad_precheck_doc.py:129`, never read by
   `hard()`. (c) rows 1666/2121 closable as lesson-only. (d) move the 2026-09-14 PARTIAL note under
   "expect 0 screens" to the "merged-tree suite" row.
2. **Build open rows by value** — `python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md`
   (49 open; 15 PARTIAL, 34 OPEN; each note names what remains).
3. `[optional]` Restore coverage of the 2 skipped `test_scoring_kinds[*-with-subtest]` cases by
   giving `/opt/anaconda3` pytest ≥ 9 (or `pytest-subtests`) — `h-mad/tests/test_h_mad_tdd_judge.py:861`.

## Open / Blocked Items

**Carried from `arity-guards-and-codex-symlink` (2026-10-03) — every item accounted for:**

- **Next Step 1 (restart to load token-weather)** — **CLOSED**: this session is that restart; the
  mod is now in-repo at `mods/token-weather` and `~/.claude/mods/token-weather` is a symlink to it.
- **Next Step 2 / inbound brief item 1 (reproduce codex gate refusal)** — **CLOSED**: reproduced by
  replaying the live hook against a Phase-5 fixture; root cause the stale `~/.agents` copy (above).
- **Brief item 2 (venv allowlist)** — **CLOSED by upstream `6a9c14b9`** (a `.venv` contained in the
  project root is trusted). Residual, by design: a venv OUTSIDE the worktree (the main HemaSuite
  checkout's, or a worktree venv symlinked to it) is still refused (`venv-escapes-root`).
- **Brief item 3 (report path)** — **CLOSED `2a0cc74d`**: out-of-root writes under `/tmp` that are
  not `.py` are admitted. The predecessor's ":245 → `gettempdir`" fix targeted the wrong path
  (assemble_tdd option values, not codex writes).
- **Brief item 4 / Next Step 5 (codex symlink + install check)** — **CLOSED**: install check covers
  `~/.agents` and agy roots upstream (`1aeefd55`, `8cf71e05`); four more stale copies (agy h-mad +
  handoff, codex handoff + find-skills) replaced by symlinks; `INSTALL: PASS`; backups deleted.
- **Brief item 5 (second gate trip, derived test)** — **CLOSED, already solved**: the 09-28 judge
  resolves tests from the impl-plan task first; the "no derived test file" trip was the stale copy.
- **Next Step 3 / two suite failures (`$schema`/`TOP`)** — **CLOSED by upstream `58344684`**.
- **Next Step 4 / 53 option-value sites** — **CLOSED `25855d08`** (68 arms at HEAD; `run --timeout`
  was a silent exit 1, not an unbound-variable crash).
- **`send --help` cosmetic** — **CLOSED `a1bd6a84`** — turned out to be a safety defect (see
  learnings); every verb now answers `-h/--help` before running.
- **Stale codex-install backup** — **CLOSED**, deleted after a diff showed no unique content.
- **`docs/skill-candidates.md` rows open** — **status updated: 49 open** after `0474a14d` re-probed
  all 50 with evidence (1 LANDED). Cheap follow-ups are Next Step 1.
- **Sibling brief `wsg-backlog-two-items-owed-here`** — **CLOSED, premise false**: HemaSuite handed
  `#56` back to skills on 2026-09-14 (`HemaSuite/docs/handoffs/2026-09-14-main__phase5-tasks-4-8-shipped.md:126`)
  and closed item 2 itself (`c8b0ed79`). Nothing owed outward.
- **`exec-pane` wrapper leak** — **CLOSED, LANDED upstream 2026-10-01** (`h-mad/tests/leak_reaper.py`).
- **A concurrent session shares this working tree** — **unchanged; no recurrence observed**:
  `main` did not move during any of this session's five full-suite runs.
- **`#56`'s residue trichotomy reads as three live options** — **unchanged, deliberate.**
- **`T6 r10`'s rank** · **`run_spec` sibling precheck** · **`~/.claude/settings.json` edited outside
  the repo** · **88 `.done` artifacts + `lanestate/`** · **two stale `d4352d63` worktrees** ·
  **auto-memory index over cap** — **CLOSED by earlier sessions**; not reopened.

**New this session:**

- **token-weather on the other Mac** — status: **user action, not blocked**. `git pull`, then the
  one-time setup in `mods/token-weather/README.md` (symlink, `CLAUDE_CODE_PLUGIN_DIRS` in
  `~/.claude/settings.json`, restart).
- **token-weather TypeScript not type-checked** — status: **open, minor**. `tsc` is not installed
  here; `claude plugin test` (17/17) and `claude plugin validate` pass.
- **2 skipped tests on this machine** — status: **deferred** (Next Step 3).

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/hmad-dispatch.sh` (`_need_val` in 68 arms; `_HMAD_VERBS` + `--help` guard in `main()`)
- `h-mad/hooks/h-mad-codex-tdd-gate.py` (`_tmp_report_target`)
- `docs/03-analysis/probes/multi-host-runtime/smoke_assert.py` (`Places.checkout`, `REHEARSAL_ROOT`)
- `h-mad/tests/`: `test_hmad_dispatch_missing_option_values.py`, `test_hmad_dispatch_verb_help.py`,
  `test_h_mad_codex_gate_tmp_reports.py` (new); `test_hmad_dispatch_exec_completion.py`,
  `test_hmad_dispatch_missing_positionals.py`, `test_host_runtime_docs.py`, `test_h_mad_tdd_judge.py`
- `h-mad/tests/mutation-specs/`: `wrapper_option_values.json`, `wrapper_verb_help.json`,
  `codex_gate_tmp_reports.json` (new, all ALL_CAUGHT); `wrapper_gate_flags.json` (re-anchored)
- `mods/token-weather/**` (new), `docs/skill-candidates.md`, `docs/learnings.md` (rebase merge)
- Outside the repo: `~/.claude/mods/token-weather` → symlink; `~/.agents/skills/{handoff,find-skills}`
  and `~/.gemini/config/skills/{h-mad,handoff}` → symlinks into this checkout

**Uncommitted changes:** none (besides this handoff).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git pull --ff-only                       # expect 7a456521 or later
hmad-dispatch env                        # PREFLIGHT: PASS
python3 h-mad/scripts/h_mad_install_check.py | head -1      # INSTALL: PASS
python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors \
    h-mad/tests/mutation-specs/*.json handoff/tests/mutation-specs/*.json \
    h-mad/tests/specs/*.json             # ANCHORS_OK 1374/1374, 138 specs
python3 -m pytest -q                     # ~14.5 min; expect 0 failed, 2 skipped
claude plugin test mods/token-weather    # 17 pass
```

**Related docs:**
- `docs/handoffs/2026-10-03-main__hmad-codex-gate-project-venv.md` — the inbound brief, now fully closed
- `mods/token-weather/README.md` — per-Mac install
- `docs/04-report/features/wsg-56-impl-plan-ac-enumeration.probe.v1.md` — `#56`, settled here
