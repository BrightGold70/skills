# Handoff — regression-provenance-ledger SHIPPED; J26 fixed; Orca #13005 filed

**Date:** 2026-08-07
**Branch:** main
**Project:** /Users/kimhawk/orca/skills

## Session Summary

Took `regression-provenance-ledger` from Phase 5 entry through Phase 7 closure and merged it to
`main` (`36181e5`) — 7 tasks, 1250 tests, match rate 100%, `ASSESSMENT: READY_TO_MERGE`. h-mad now
registers each passing `wiring` task to `.h-mad/wires.jsonl` at 5b and re-verifies every registered
wire at 5f, so a proven wire outlives the feature that proved it. Then fixed skill-monitoring J26
(`e3213d6`) and closed the six-session carry on the two Orca bug docs: re-verified both on Orca
1.4.175, filed the worker-abandon one as **stablyai/orca#13005**, and deliberately did *not* file
the terminal-read one. Nothing is blocked; the only open item needs an Orca restart that has not
happened yet.

## Key Learnings

- **Three mutation sweeps came back `SURVIVED` after their implementer reported `STATUS: DONE`** —
  Task 4 (1 of 7), Task 5 (2 of 6, including the direction the report explicitly claimed verified),
  Task 6 (**5 of 6**). In every case the ACs had tests and the tests did not discriminate, which is
  indistinguishable from having no test until something mutates them. The harness running
  independently of the report is what caught all three.
- **Tidy-ASCII fixtures made a defect class unreachable, again.** `_register_wiring_tasks` required
  an ASCII `->` while the impl-plan template (`references/inline-protocols.md:271`) writes **U+2192
  `→`**, so registration silently skipped every real wiring task while printing `WIREPIN: PASS`. It
  survived 96 gate tests, 6/6 mutations and the wire-scoped revert because every fixture wrote the
  arrow as ASCII. Found only by running the gate on a real plan.
- **A `REFUSED` mutation is not a pass, and it happened to me.** One sweep returned `REFUSED` with
  2 anchors matching zero times, because I wrote the anchors from memory instead of reading the
  source. Zero matches leaves the guard intact and the suite green — exactly what an enforced guard
  looks like.
- **Impl-plan audits never inline the paired *plan*.** Eight clean 5b cycles verified impl-plan ↔
  design and were structurally blind to `plan.md` drifting out of sync. No gate could have caught
  it; found by inspection.
- **Audit cycle 7 refused my deferral, correctly.** I twice flagged design gaps "for 6a-prime", but
  6a-prime reviews Phase-5 code *against* the design, so a stale design makes it flag correct code
  as drift. Back-propagated to design v1.9 in the same pass.
- **J26's own filed fix direction was wrong about its justification.** It said to route the marker
  to stderr "as the gate scripts already do". None of the 8 siblings do — they all print to stdout.
  The fix is still right, but because this script's stdout is a *value to capture* rather than a
  *report to read*; the code comment now says so, so nobody "harmonises" it back.
- **`.h-mad/` holds both ignored runtime state and the TRACKED `invariants.md`.** My `rm -rf .h-mad`
  cleanup deleted a load-bearing tracked file. Caught and restored before any commit. Cleanup must
  target `.h-mad/wires.jsonl` specifically.
- **`git stash push` on an untracked path stashes nothing and the revert silently does not happen** —
  confirmed live. `git add -N` first; and on an intent-to-add entry `stash` then fails with "Entry
  not uptodate", so a file swap is the working revert for a brand-new module.
- **Orca's `_meta` no longer exposes `appVersion`** (1.4.175). Get it from
  `/Applications/Orca.app/Contents/Info.plist` → `CFBundleShortVersionString`.

## Next Steps

1. **Nothing is required.** `main` is clean, pushed, in sync with `origin/main` at `c965937`.
2. `[suggested]` **Settle the terminal-read bug doc** — needs an Orca app restart, which is
   destructive to a live session so it was not done opportunistically. The exact two commands and
   the file/WONTFIX decision rule are in
   `docs/orca-bug-terminal-read-empty-after-restart.md` §"Open question". See Open Items.
3. `[suggested]` **Delete the merged feature branch** — `git branch -d feature/215-regression-provenance-ledger`
   (merged at `36181e5`; kept only in case you want the history handy).
4. `[suggested]` **Decide whether to track `.h-mad/wires.jsonl`.** `.h-mad/` is gitignored here, so
   `verify` correctly reports `UNTRACKED` and the ledger does not survive a clone. Making it real is
   one line: add `!.h-mad/wires.jsonl` to `.gitignore`, then `git add` it. That is an operator
   decision (FR-3 refusing to report coverage it cannot persist), not a defect.

## Open / Blocked Items

- **Terminal-read bug doc — status: revised, deliberately NOT filed, blocked on an Orca restart.**
  `docs/orca-bug-terminal-read-empty-after-restart.md`. The `terminal read` payload is unchanged on
  1.4.175 so the fix has not landed, but re-examination found `terminal list` exposes `orphaned` and
  `lastOutputAt`, which the doc never considered and which correlate cleanly with an all-zero read
  (8 panes populated/2–65 lines; 1 pane null/0). A maintainer could close it with "`lastOutputAt` is
  your flag". That may be wrong for the case the report is *about* — a healthy pane with a live
  process, idle since a restart, not the orphaned-worktree pane measured today — but settling it
  needs a restart. Sanitized paste-ready body already prepared at `/tmp/orca-bug-2-terminal-read.md`
  (**regenerate if /tmp was cleared** — the source doc has everything). Todo #43.
- **stablyai/orca#13005 — status: filed, awaiting maintainer.** No action owed. The positive control
  is in the issue, so its one acknowledged gap is closed.
- **9 tracked `hematology-paper-writer/**/__pycache__/*.pyc` perpetually dirty** — status:
  pre-existing, not this session's. Any full pytest run rewrites them. Left unstaged deliberately.
- **FR-5 (AST shape challenge) ships warning-only** — status: deliberate, by design. Static AST name
  index, so dynamic dispatch / `getattr` / config-driven binding are invisible. A floor on detection,
  never a proof of absence; must not gate a verdict until its rates are measured.
- **Stale codex/agy pane pins** — status: deferred, operational. `PREFLIGHT: FAIL stale=codex,agy`
  all session. Irrelevant to `exec`, which is why every dispatch used it.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_wire_registry.py` — new, ~570 lines (registry, verifier, AST challenge, CLI)
- `h-mad/scripts/h_mad_wire_pin_gate.py` — the wire: `main()` → `register()`, `--feature`, arrow allowlist
- `h-mad/scripts/h_mad_extract_verdict.py` — J26, marker to stderr
- `h-mad/tests/{test_h_mad_wire_registry,test_h_mad_wire_pin_gate,test_h_mad_extract_verdict,test_h_mad_archreview_pane_halt}.py`, `h-mad/tests/conftest.py`
- `h-mad/SKILL.md` — 5b registers, 5f re-verifies, five halt reasons
- `docs/skill-monitoring.md` — J26 → FIXED
- `docs/{01-plan,02-design,03-analysis,04-report}/…/regression-provenance-ledger.*` + `docs/archive/2026-08/`
- `docs/orca-bug-{worker-release-dispatch-not-found,terminal-read-empty-after-restart}.md`

**Uncommitted changes:** none except the 9 incidental `.pyc`.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
git pull --ff-only
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
# suite (default python3 has NO pytest) — expect 1255 passed:
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/ handoff/ -q
```

**The ledger, live** (this is the feature dogfooded on itself — note `--rootdir` is the repo root
and `--testpath` scopes collection; the repo root cannot be collected because sibling projects have
23 pre-existing import-mismatch errors):
```bash
python3 h-mad/scripts/h_mad_wire_pin_gate.py \
  docs/01-plan/features/regression-provenance-ledger.impl-plan.md \
  --feature regression-provenance-ledger          # → registered=1 skipped=0
python3 h-mad/scripts/h_mad_wire_registry.py verify \
  --base $(git rev-parse HEAD) --rootdir . --testpath h-mad/tests
rm -f .h-mad/wires.jsonl     # NEVER `rm -rf .h-mad` — invariants.md is tracked
```

**Related docs:**
- `docs/04-report/features/regression-provenance-ledger.report.md` — what shipped and the four
  silent-no-op defects found inside the feature itself
- `docs/03-analysis/regression-provenance-ledger.analysis.md` — 24/24 AC→test map, and §"coverage
  that was claimed before it was real"
- `docs/skill-monitoring.md` — J26 FIXED `e3213d6`
- https://github.com/stablyai/orca/issues/13005
