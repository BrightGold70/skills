# Handoff — verb arity guards, a stale codex install, and why this session must be restarted

**Date:** 2026-10-03
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-10-03-main__hmad-codex-gate-project-venv.md, 2026-09-15-main__two-false-task-premises.md

## Session Summary

A TAKEOVER of HemaSuite's codex-gate brief, then a drain of the errors in it that did not need the
full seven-phase workflow. **Two fixed and committed** (`41c36fd`): seven `hmad-dispatch` verbs that
died on `$1: unbound variable` when a required argument was omitted, and the codex install at
`~/.agents/skills/h-mad`, which was a *stale copy* rather than the symlink it should be. **Three
recorded rather than fixed** (todos 6/7 plus the four gate items), each with the evidence that makes
the next session's first move obvious. Suite **2 failed / 3905 passed** against a **2 failed / 3854
passed** baseline — exactly the 51 new tests, same two pre-existing failures. Anchors
`ANCHORS_OK 980/980` across all three spec dirs, matching the predecessor's figure exactly.

**Restart this session.** The `token-weather` mod is not loaded here and never can be: this process
started 13:46:07 and the mod was registered in `settings.json` at 15:00:24. See Next Step 1 — that
is the only reason this handoff was written now rather than at the end of the backlog.

## Key Learnings

- **The reported symptom was not the class.** "`send --help` crashes" is true, and `--help` is
  irrelevant: a bare `hmad-dispatch send` fails identically, because `--help` merely lands in `$1`
  and leaves `$2` unset under `set -u`. Fixing the spelling that gets typed most often would have
  left six other verbs crashing — which is exactly what happened to `run --help` (#143), fixed for
  `run` alone.
- **A test whose cases are DERIVED catches what a hand audit misses.** The sweep reads the verb list
  out of the wrapper's own top-level help, and found `read` — which a careful read of all 41 `_cmd_`
  function heads had missed. A hardcoded case list would have shipped the same blind spot as the
  audit that wrote it.
- **"A set containing X exists in the binary" does not mean "X is accepted".** Bumping `TOP` on that
  inference turned 2 failures into 5. The diagnosis was right and the *fix* was not: the module's
  premise is that `$schema` must be REMOVED (`PATCHED = {k: v for ... if k != "$schema"}`), so
  accepting it invalidates the negative controls the module is built on. Re-recording the verbatim
  fixtures to go green would have destroyed the evidence.
- **`claude plugin list` reports a fresh process, not your session.** It said `token-weather … ✔
  loaded` while this session has never had it. `CLAUDE_CODE_PLUGIN_DIRS` also appears in every Bash
  tool shell, because Claude Code applies `settings.env` to children from settings as they are on
  disk *now*, while the plugin table was fixed at launch. Two true readings, one false conclusion.
- **Enumerating verbs by running them has side effects.** A loop that ran every verb with `--help`
  included `launch`, `clear`, `interrupt`, `worktree-rm` and `automation-create`. Nothing broke
  (terminal count was 10+1, pins intact, 4 healthy worktrees) but only because the verbs rejected
  `--help` as an argument before acting. Use static analysis or the isolated stub env.
- **`python3` on this machine now HAS pytest** — 3.11.7, pytest 7.4.0, `/opt/anaconda3/bin/python3`.
  The predecessor's resume block says *"python3 here is 3.14 with NO pytest — use python3.11"*. That
  is false as of today and would send the next session down a dead end.
- **`timeout` does not exist on macOS.** It silently turned two mutation-spec runs into
  `command not found` that read, at a glance, like the harness refusing.

## Next Steps

1. **Restart Claude Code to get the `token-weather` band.** Nothing to fix — `hooks.json` is `CLEAN`
   per Claude Code's own validator, and every surface it hooks (`AbovePrompt`, `ui.render`,
   `session.measure`, `hasSurvey`, `bodyColumns`) is present in 2.1.288. This process simply predates
   the registration. `claude plugin details token-weather` reporting `Hooks (0)` is a reporting gap
   for the `modules` form, not a failure.
2. **Reproduce the codex gate refusal** — todo 1. Both of its blockers are now cleared: `hmad-dispatch`
   is on PATH (`~/.zshrc`) and a codex pane is pinned. Dispatch a prompt running
   `/Users/kimhawk/orca/HemaSuite/hematology-paper-writer/.venv/bin/python -m pytest -q <one file>`
   and expect the PreToolUse gate to refuse it.
3. **Decide the `$schema` question** — todo 7, and it blocks a green suite. Either the module tracks
   the current binary (and the recorded-warning fixtures become version-pinned history with their own
   2.1.270 `TOP`), or it becomes version-aware. Do **not** just bump `TOP`.
4. **Guard the 53 option-value sites** — todo 6. Same `set -u` root cause, second location:
   `--opt) x="$2"; shift 2` crashes when the value is omitted (`hmad-dispatch worktree-ps --limit`).
   24 sites already use `${2:-}`, so the file is inconsistent, not uniformly unguarded.
5. **Finish `h_mad_install_check.py`** — todo 4 part 2. It reported `INSTALL: PASS` throughout, while
   checking only `~/.claude/skills`, which is precisely why the stale codex copy went unnoticed.
6. `[suggested]` **Keep draining `docs/skill-candidates.md`** — carried, see Open Items.

## Open / Blocked Items

**Carried from `two-false-task-premises` (2026-09-15) — every item accounted for:**

- **`docs/skill-candidates.md` rows open** — status: **unchanged, 51**. Not touched this session; the
  automation-scout phase of this closeout was deliberately **skipped**, so the 27 unreconciled `yes`
  rows are still unreconciled and no new rows were filed. Re-run the census before trusting any count:
  `python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md`.
- **Sibling brief `wsg-backlog-two-items-owed-here`** — status: **unchanged since 2026-09-15.** Still
  one-directional information owed outward: its Next Step 1 was answered in this repo by
  `docs/04-report/features/wsg-56-impl-plan-ac-enumeration.probe.v1.md` and its owner has no way to
  know. `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none (removed)` ·
  `brief: docs/handoffs/2026-09-14-main__wsg-backlog-two-items-owed-here.md`. Owned and adopted
  there, so there is nothing to HANDOVER — only a pointer to send.
- **`exec-pane` wrapper leak** — status: **unchanged, not started.** Row at `docs/skill-candidates.md`
  §"reap LEAKED `exec-pane` wrapper processes". Not a `live-e2e-pane-janitor` recurrence.
- **A concurrent session shares this working tree** — status: **recurred, and attribution holds.**
  `0c377ac` landed at 14:55:28, after this process started at 13:46:07. It predates both suite runs,
  and `git log` moved at no point between the baseline and the verify run, so **both counts are
  attributable**. The guard (`MUTATION: TREE_MOVED`, `tree_lock()`) stayed in place.
- **`#56`'s residue trichotomy still reads as three live options** — status: **unchanged, deliberate.**
  A convention to know before re-reading that section, not a defect.
- **`T6 r10`'s rank** — status: **closed by the predecessor as not load-bearing.** Not reopened.
- **`run_spec` sibling precheck** · **`~/.claude/settings.json` edited outside the repo** · **88
  `.done` artifacts + `lanestate/`** · **two stale `d4352d63` worktrees** · **auto-memory index over
  cap** — all **CLOSED by the predecessor**; re-checked here for completeness, nothing reopened.

**Open, new this session:**

- **Two pre-existing suite failures, one root cause** — status: **open, blocks a green suite.**
  `test_h_mad_check_plugin_hooks.py::TestAgainstTheLiveBinary::test_top_level_key_set_still_matches`
  and `::TestThePatchedShapeIsClean::test_the_live_bkit_cache_is_clean_if_it_is_installed`. Claude
  Code 2.1.288 spells the validator's top-level set
  `new Set(["$schema","description","hooks","modules","surface"])` — the old spelling has **zero**
  matches — so `$schema` is now accepted and bkit 2.1.38 shipping it is **correct, not a defect**.
  `TOP` (`h-mad/scripts/h_mad_check_plugin_hooks.py:44`) is transcribed from 2.1.270. Will fail for
  anyone on 2.1.288+. Full evidence and the three options in todo 7 / Next Step 3.
- **53 option-value crash sites** — status: **open, deferred deliberately.** See Next Step 4.
- **`h_mad_install_check.py` still checks only `~/.claude/skills`** — status: **open** (part 2 of the
  codex-install item; part 1 is closed below).
- **`hmad-dispatch send --help` prints usage but `--help` is not a documented verb flag** — status:
  **open, cosmetic.** The arity guard now answers it with `usage:` because `--help` lands in `$1` and
  `$2` is empty. That is the right output by accident, not by design; only `run` has a real
  `-h|--help` arm. Decide whether every verb should document itself.
- **Stale codex-install backup, 5.6M** — status: **awaiting your call.**
  `~/.agents/skills/h-mad.stale-copy-backup-2026-10-03`. Delete once satisfied with the symlink.

**Closed this session:**

- **Codex install was a stale copy** — **CLOSED**, not committed (outside the repo). It had already
  drifted, which the inbound brief did not know: pre-agy `SKILL.md`, `references/agy-runtime.md`
  absent entirely, a superseded assertion in `tests/test_h_mad_codex_runtime.py`. Codex had been
  reading a ~2.5-week-old SKILL.md. Now a symlink mirroring the Claude install; both resolve to
  `/Users/kimhawk/orca/skills/h-mad`.
- **Seven verbs crashed on a missing argument** — **CLOSED, `41c36fd`.**
- **`hmad-dispatch` was not on PATH** — **CLOSED**, outside the repo. `export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"`
  appended to `~/.zshrc` (backup `~/.zshrc.bak-hmad-path`). It had never been installed; the shim
  worked by absolute path all along, and its absence by bare name was misread as "not an Orca substrate".
- **Both agent panes were `UNRESOLVED`** — **CLOSED.** `PREFLIGHT: PASS`. Auto-detect is
  worktree-scoped, which is why it found 0: codex runs in the HemaSuite worktree, invisible from here.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/hmad-dispatch.sh` (`_need_arg` + seven guards)
- `h-mad/tests/test_hmad_dispatch_missing_positionals.py` (new, 124 lines)
- `docs/handoffs/2026-10-03-main__hmad-codex-gate-project-venv.md` (`**Taken-Over-By:**`, `ad55fd0`)
- Outside the repo: `~/.zshrc`, `~/.agents/skills/h-mad` (now a symlink), `.h-mad/orca-pins.env`

**Uncommitted changes:** none at the time of writing, besides this handoff.

**Pinned agent panes** (survive a restart — `.h-mad/orca-pins.env` is on disk and gitignored):
- `codex=term_61254299-5f7f-451b-acb2-e38e432240ea` — HemaSuite worktree, `feature/203-…`
- `agy=term_2de23026-727e-4555-9c7e-4eccab21d75d` — launched here, `~/orca/skills`, **accept-edits
  mode on** (`shift+tab` cycles it; looser than a read-only reviewer needs for Phase 6a-prime)
- Re-verify with `hmad-dispatch env` after the restart; a handle can rotate.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main                        # expect 41c36fd or later; 3 ahead of origin, UNPUSHED
hmad-dispatch env                        # expect PREFLIGHT: PASS (bare name works now)
python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors \
    h-mad/tests/mutation-specs/*.json handoff/tests/mutation-specs/*.json \
    h-mad/tests/specs/*.json             # expect ANCHORS_OK 980/980, 108 specs
python3 -m pytest -q                     # ~8.5 min from the REPO ROOT
# python3 IS 3.11.7 with pytest 7.4.0 (/opt/anaconda3/bin/python3) — the predecessor's
#   "python3 is 3.14 with NO pytest, use python3.11" is STALE as of 2026-10-03.
# Expect exactly 2 failures, both test_h_mad_check_plugin_hooks ($schema / 2.1.288). Do NOT
#   pin a passed count: doc-derived tests move it. Measured 3905 at 41c36fd.
# `timeout` does not exist on macOS — omit it or install coreutils (gtimeout).
# ANOTHER SESSION COMMITS INTO THIS TREE — check `git log` before AND after a suite run.
# Do NOT run the mutation harness concurrently with a suite: it modifies real source files.
```

**Related docs:**
- `docs/handoffs/2026-10-03-main__hmad-codex-gate-project-venv.md` — the inbound brief, with
  `**Taken-Over-By:**` stamped; its Next Step 3 premise is **refuted** (see below)
- `h-mad/tests/test_hmad_dispatch_unknown_flags.py` — the sibling defect and the exit-2 convention
- `h-mad/scripts/h_mad_check_plugin_hooks.py` — docstring explains why its constants are transcribed
  and why the live-binary test is the thing trusted, not the docstring
- `h-mad/references/agent-substrate.md` §"Putting `hmad-dispatch` on PATH", §"The `.result` envelope"

**One premise of the inbound brief was refuted, not inherited.** Its Next Step 3 blamed `/tmp` vs
`/private/tmp` symlink resolution for codex reports landing in `tests/`. `_path_within`
(`h-mad/hooks/h-mad-codex-tdd-gate.py:204-211`) resolves **both** sides, so
`/private/tmp/claude-501/...` already passes. What fails is `$TMPDIR`
(`/var/folders/6q/.../T/`), which is not under `/private/tmp`. Measured: `/tmp/report.md` True ·
`/private/tmp/claude-501/…` **True** · `/var/folders/ab/T/report.md` **False** · `~/report.md` False.
The fix at `:245` is to trust `tempfile.gettempdir()`, not to widen `/tmp`.
