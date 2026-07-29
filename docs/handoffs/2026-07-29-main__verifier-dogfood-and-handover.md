# Handoff — 5e verifier dogfood + template fix; false-idle guard handed to HemaSuite

**Date:** 2026-07-29
**Branch:** main
**Project:** orca/skills (h-mad + handoff skills)

## Session Summary

Third continuation of the day's arc (prior: `2026-07-29-main__skill-upgrades-verifier-parked-paths.md`). Live-dogfooded the new Phase-5e verifier template and closed the h-mad SKILL.md pane-read doc note (#3). The dogfood proved both verdict paths — a seeded FALSE property → `BLOCKED`, a scoped TRUE run → `DONE` — and surfaced a real template defect that got fixed: a headless codex verify was re-running the full suite (PTY dot-only output) to a timeout, so step 4 is now orchestrator-owned. The `wait --not-while-regex` false-idle guard (#2) was **handed to a HemaSuite session** to exercise during a real `/h-mad` run. All green: h-mad 744/0. Everything committed + pushed (HEAD `826a99c`).

## Key Learnings

- **The 5e verifier does not rubber-stamp — proven live.** Seeded a FALSE property ("fuzzy path persists"); the verifier read the source, quoted the contradicting line (`persist=False`, L150), ran no suite, modified nothing, returned `STATUS: BLOCKED`. A gamed verifier would have said DONE.
- **A codex-exec verify must NOT run the full suite.** The PTY exposes only pytest progress dots (no summary line), so codex re-runs the whole suite to reconcile, doubling wall-time until the watchdog (even 1200s) kills it. Fix: the orchestrator runs 5f's full suite and passes the number; the verifier confirms it. (`codex-verifier-prompt.md` step 4, `826a99c`.)
- **Worktree-isolation to dodge concurrency backfires.** Running the suite from a `/tmp` detached worktree fails path-coupled HemaSuite tests — the isolation that removes concurrent-mutation noise introduces path-resolution failures instead. Neither is a real regression.
- **A wrapped literal defeats a single-line mutation test.** "The\norchestrator…" wraps line 44→45; a single-line `perl s///` matched nothing and the mutation *passed* (false enforcement — [[feedback_mutation_test_every_guard]]). Use slurp mode + `\s+` (`perl -0777 -pe 's/The\s+orchestrator.../.../s'`) so the mutation actually breaks the phrase.
- **`--sandbox read-only` breaks pytest** (no writable temp/cache → `FileNotFoundError`); a verify that must run tests needs `workspace-write`. The property-quote step works fine read-only.

## Next Steps

1. **Await the HemaSuite session's result on #2** — the `wait --not-while-regex 'Waiting for background terminal'` false-idle guard is being exercised there during a real 5d/5e where a background-terminal delegation occurs naturally. When it reports, fold the outcome back here (confirm the guard keeps polling through the background-terminal frame instead of false-idling). — `h-mad/SKILL.md` §"Reading a dispatch verdict".
2. **Capture a clean full-suite DONE inside a real `/h-mad` 5e** — the scoped dogfood proved the DONE verdict on module+properties; the orchestrator-owned full-suite confirmation (new step 4) is exercised only in a real run. — `h-mad/references/codex-verifier-prompt.md` step 4.

## Open / Blocked Items

- **#2 false-idle guard live validation — handed off to a HemaSuite session.** status: delegated, awaiting result.
  - repo: `/Users/kimhawk/orca/HemaSuite/hematology-paper-writer` · branch: `main` · worktree: main (Orca-managed) · artifact: exercised via a live `/h-mad` 5d/5e pane dispatch; the guard lives in `h-mad/scripts/hmad-dispatch.sh` (`_cmd_wait` `_frame_satisfies` + `--not-while-regex`), unit-tested in `h-mad/tests/test_hmad_dispatch.py`.
- Orchestrator-owned full-suite DONE (new step 4) — status: deferred to a real 5e run (Next Step 2). Not blocking; module+property DONE path already proven.

## In-Flight Processes

None — the dogfood dispatches (codex exec) all completed or were reaped; no live background work at handoff.

## Context for Next Session

**Files touched this session (all committed + pushed):**
- `h-mad/references/codex-verifier-prompt.md` — step 4 orchestrator-owned (`826a99c`)
- `h-mad/tests/test_h_mad_verifier_prompt.py` — literal updated, mutation-verified (`826a99c`)
- `h-mad/SKILL.md` — `orca terminal read` JSON-shape note (`a9afc69`)
- `docs/learnings.md` — +3 dogfood/verifier entries (`a9afc69`, `826a99c`)
- `~/.claude/projects/-Users-kimhawk-orca-skills/memory/feedback_codex_tdd_verify.md` — dogfood outcome + step-4 fix (user-global, not in repo)

**Uncommitted changes:** none (local `main` = `origin/main` `826a99c`).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
/opt/anaconda3/bin/python3 -m pytest h-mad/tests/ -q   # 744/0
```

**Related docs:**
- `h-mad/references/codex-verifier-prompt.md` + `h-mad/SKILL.md` §Phase 5e
- Prior handoffs (same day): `2026-07-29-main__skill-upgrades-verifier-parked-paths.md`, `2026-07-29-main__dispatch-transport-validation.md`
