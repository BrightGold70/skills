# Handoff — J29 `--out` clobber guard shipped; HemaSuite items handed to their own repo

**Date:** 2026-08-09
**Branch:** main
**Project:** /Users/kimhawk/orca/skills

## Session Summary

Resumed from `2026-08-09-main__guard-patches-and-h-mad-install-gate.md`, verified every
claim it made (install gate PASS, both plugin patches PRESENT and behaviourally correct,
suite green at its recorded 1207), then closed its one buildable item: J29's `--out`
clobber guard. Shipped as `d53e385` — TDD, mutation-tested, suite 1207 → 1213. The
durable learning is persisted separately in `503fd84`. Both pushed; tree clean at
`origin/main`. The three HemaSuite-owned items from the prior handoff were **not worked**
— they are handed over in that repo's own
`docs/handoffs/2026-08-09-main__hemasuite-items-handover.md`, and one of them got worse.
Nothing is blocked or in flight here.

## Key Learnings

- **J29's own filed remedy was wrong, and implementing it literally would have broken the
  skill.** The entry says "refuse to overwrite a non-empty `--out` it did not create."
  One grep killed that: `references/failure-recovery.md:45` makes re-dispatch the
  `no_verdict` remedy, and SKILL.md's `--out` paths are templated per feature+module
  (`/tmp/rev_<feature>_<module>.txt`) — deterministic, so a legitimate retry lands on the
  same path the failed attempt already filled with its short narration. A monitoring
  entry's proposed remedy is a hypothesis, not a spec. Persisted as a learning in
  `503fd84`.
- **The guard had to key on CHANGE, not on non-emptiness, and a mutant proves it.**
  Fingerprint `--out` (`cksum`) before dispatch, re-check at each write site. Swapping the
  change check for `[ -s "$out" ]` kills exactly one test —
  `test_exec_still_overwrites_a_stale_out_left_by_a_previous_attempt` — which is the test
  that encodes the design decision. Without that test the naive version ships green.
- **`rc` was deliberately left alone, and that is a design position, not an oversight.**
  `_cmd_exec`'s contract is `$?` == "did the CLI run"; `_exec_stamp` and `_cmd_notify`
  both consume it. What J29 records is the *silence*, so the cure is the preserved file
  plus a `REFUSING to overwrite --out` stderr line, with the verdict still on stdout and
  in `--log`. A new exit code would have been a contract change for every caller.
- **An unwritable `--out` kills the dispatch with rc=1 and swallows stdout — pre-existing,
  and confirmed byte-identical before and after the guard.** Checked deliberately because
  no test covers that path. Not fixed: out of scope for this change, but it is a real
  sharp edge (`--out` into a non-existent directory loses the verdict entirely).
- **The startup `bkit hook reachability check: missing=[skill_post]` warning is NOT a
  plugin update having clobbered the patched cache files.** Both verifiers report the
  patch symbol PRESENT at bkit 2.1.19, so the cache is intact; the warning is the separate
  CC plugin-hook drop (#57317) the hook names itself. Worth knowing because "patch missing
  after update" and "hook not firing" look alike from the session banner.
- **`hematology-paper-writer/` is tracked in THIS repo — 239 files — while the HemaSuite
  consumer items concern the copy at `/Users/kimhawk/Coding/HemaSuite`.** Unexplained. Two
  copies of a consumer is exactly the mechanism that produces the coupled-suite drift the
  prior handoff recorded. Not investigated.
- **A repo-wide TODO/FIXME audit came back essentially empty, which is itself the result.**
  21 hits, 19 of them non-debt (template scaffolding meant to be filled in, prose *about*
  TODO markers, one eval fixture). `h-mad/` has zero. The only two real ones are
  `hematology-paper-writer/cli.py:1172` (a commented-out call) and
  `docs/02-design/features/hpw-csa-macos-app.design.md:260` (a spec gap).

## Next Steps

1. Watch the two upstream issues; if either ships, **drop** the local patch rather than
   re-applying — `verify` exiting 0 with the patch symbol MISSING is exactly that signal.
   [bkit#145](https://github.com/popup-studio-ai/bkit-claude-code/issues/145) ·
   [claude-plugins-official#5085](https://github.com/anthropics/claude-plugins-official/issues/5085)
2. After **any** plugin update, run both verifiers — the patches live in version-pinned
   caches that an update replaces wholesale:
   `node docs/patches/bkit-enh310-quoted-heredoc-body/verify.js` and
   `python3 docs/patches/claude-security-guidance-bare-exec/verify.py`
3. If J28 recurs (a dispatch returning exit 0 having produced nothing), **capture the
   transcript before re-running anything** — re-running is what destroyed the evidence the
   first time. `docs/skill-monitoring.md` J28.
4. [suggested] Resolve the duplicate `hematology-paper-writer/` — `git ls-files
   hematology-paper-writer | wc -l` says 239 here, and there is a second copy at
   `/Users/kimhawk/Coding/HemaSuite/hematology-paper-writer`. Establish which one the
   `~/.claude/skills` symlink chain actually reaches before either is edited; a consumer
   suite drifting from its skill is what two copies produce.
5. [suggested] Consider whether an unwritable `--out` should fail soft — today it takes
   the whole dispatch to rc=1 with empty stdout, so a typo'd directory loses a verdict
   that the agent successfully produced. `h-mad/scripts/hmad-dispatch.sh` write sites.

## Open / Blocked Items

- **J28** — status: MONITORING, unreproduced. Three hypotheses tested and refuted (no-TTY,
  backgrounding, concurrent dispatch). Filed deliberately without a diagnosis. Unchanged
  this session.
- **Known remaining false positive (accepted)** — pipe-to-shell *text* inside a quoted
  heredoc body is still denied by bkit ENH-310; the `pipe-shell` vector scans the full
  string by design. Pinned by `QH-06`. No action intended.
- **Duplicate `hematology-paper-writer/`** — status: not investigated. See Next Step 4.
- **HemaSuite items (3)** — status: handed over, not worked. See
  `/Users/kimhawk/Coding/HemaSuite/docs/handoffs/2026-08-09-main__hemasuite-items-handover.md`.
  One of them was widened this session: its test suite is now known to be *unrunnable*,
  not merely failing.

## Context for Next Session

**Files touched this session:**

*Committed as `d53e385` (the guard):*
- `h-mad/scripts/hmad-dispatch.sh` — `_out_fingerprint` + `_out_clobber_ok`, wired at all
  three `--out` write sites (codex `cp`, agy `printf`, recovery `printf`)
- `h-mad/tests/test_hmad_dispatch_exec.py` — 6 tests
- `h-mad/tests/stubs/codex`, `h-mad/tests/stubs/agy` — `*_RIVAL_OUT`/`*_RIVAL` knobs, which
  simulate a concurrent dispatch landing its verdict mid-run
- `h-mad/SKILL.md` — §"Give every dispatch its own `--out`"
- `docs/skill-monitoring.md` — J29 🟡 → 🟢 `GUARDED`

*Committed as `503fd84`:*
- `docs/learnings.md` — the "monitoring entry's remedy is a hypothesis" kernel

**Uncommitted changes:** none. Clean and level with `origin/main` (0 ahead / 0 behind).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main

# health: all three should be green, as they were at handoff
python3 h-mad/scripts/h_mad_install_check.py                          # INSTALL: PASS
node docs/patches/bkit-enh310-quoted-heredoc-body/verify.js           # exit 0, symbol PRESENT
python3 docs/patches/claude-security-guidance-bare-exec/verify.py     # exit 0, symbol PRESENT

# full suite (1207 at session start, 1213 now)
python3 -m pytest h-mad/tests/ -q --tb=line
```

**Related docs:**
- `docs/handoffs/2026-08-09-main__guard-patches-and-h-mad-install-gate.md` — the session
  this resumed from; its one buildable item is now closed, its watch items carried forward
- `/Users/kimhawk/Coding/HemaSuite/docs/handoffs/2026-08-09-main__hemasuite-items-handover.md`
  — the three items that belong to that repo
- `docs/skill-monitoring.md` J28 (open) / J29 (`GUARDED`, with the reasoning for the
  change-keyed design)
- `h-mad/SKILL.md` §"Give every dispatch its own `--out`" — the operator-facing version
