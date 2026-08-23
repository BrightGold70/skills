# Handoff — J30 closed; the advisor gate turns out never to fire

**Date:** 2026-08-24
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)

## Session Summary

Cleared all five todos carried out of the 2026-08-22 handoff. J30 closed (`e2986fd`) — its size
premise was **refuted** on re-probing and only its off-contract half survived, now closed in code by
`h_mad_offcontract_scan.py`. Live-firing the two owed context gates produced the session's real find:
**the `advisor` PreToolUse hook does not fire at all** (J44), so a guard believed mechanical since
2026-08-19 has never protected anything. The run cap is fine and never needed the relaunch it was
blocked on. Eight merged branches deleted; the `test_verb_no_self_invocation` mutation gap closed
after both halves of its "accepted" premise proved false. Everything is committed and pushed
(`452f4c7`); registry stands at 42 entries, **MONITORING 1 = J44** — *as of this commit*: the sibling
session below has 71 uncommitted lines filing **J46** in the same file, so re-run the census rather
than quoting this number.

**A sibling session is live in this same working tree** — see Open Items before touching anything.

## Key Learnings

- **A carried repro can dissolve, and the probe has to match the WORKLOAD, not just the filed
  variable.** J30's 5/5 drop at ~260 KB did not reproduce: 8/8 clean at 266,342 B on agy 1.1.18. But
  the first five reps were a *trivial* task (write one file, echo it) and would only have proven argv
  fits 260 KB. The three **work-shaped** reps — a 260 KB document with five contradictions planted end
  to end, all five found every time — are what proved the prompt is *read*. The variable that had
  actually moved was neither size nor workload: it was the transport (older agy under text mode vs
  `--output-format stream-json`).
- **Refuting the mechanism an entry leads with does not refute the defect it names.** J30's size gate
  died; its "the artifact is unfindable, not absent" half was *confirmed* by a second off-contract
  report found mid-probe, eleven days after the first. Falsify each claim separately.
- **"Hooks are snapshotted at session start" is half true, and the wrong half was load-bearing.** The
  *registration* and the *launch environment* are fixed at start — but the hook **file** is read from
  disk at every invocation, so it can be instrumented mid-session. That is what made the routing test
  possible with no relaunch, after three handoffs deferred it for one.
- **The advisor gate fails OPEN and silent, and only an instrumented real call could show it.** At the
  default window the gate correctly *allows*, which is indistinguishable from never running. Marker
  run 1 sat after the `tool_name` filter and could not separate "never entered" from "exited at the
  override"; run 2 on line 1 settled it. Self-test the detector before believing its zero.
- **`ALL_CAUGHT` is not evidence — read which assertion died.** The mutation harness reported 3/3 on
  `test_verb_no_self_invocation`; two of the three died on `pids[$i]: unbound variable` and tripped
  `assert r.returncode == 0`, never reaching the property. A mutant caught by a return code proves the
  code crashes when broken and nothing else.
- **`all(...)` over a collection the code under test produces is vacuously true when that collection
  is empty.** `test_verb_no_self_invocation` scored "the verb dispatched nothing at all" identically
  to "dispatched correctly and never recursed" — unfalsifiable exactly when most broken. No mutant
  would have found this; reading the assertion did.
- **`advisor()`'s 2x is a per-turn billing spike, not permanent growth.** Measured across one call:
  `used` 265,581 → 550,626 on that turn → back to ~280,000. A reading taken mid-advisor-turn is real
  but transient and must not be recorded as the session's size.
- **A full-suite number measured in a shared tree can be another session's.** My first run showed 10
  failures in a file I never touched. Same file is 22/22 at clean HEAD. Re-measure in a throwaway
  worktree at HEAD with only your own change applied.

## Next Steps

1. **Resolve the two-sessions-one-tree situation before any commit.** `git status --short` in
   `/Users/kimhawk/orca/skills` shows 7 modified files that are a sibling session's in-flight work.
   Confirm with the operator whether that session is still live before staging anything.
2. **Probe J44 — one fresh session, and it subsumes the relaunch test.** Register a temporary
   `*`-matcher `PreToolUse` hook logging `tool_name` to a file in `~/.claude/settings.json`, relaunch,
   make one `advisor()` call. A line under another name → the matcher string is wrong, one-word fix.
   No line at all → `advisor` bypasses hooks and the gate needs a different attachment point. Entry:
   `docs/skill-monitoring.md`, search `**J44`. Do **not** re-probe with more `advisor()` calls.
3. **Until J44 is fixed, treat the advisor gate as absent** — not as a backstop. Live protection is
   the prose rule in `h-mad/SKILL.md` §"Orchestrator context hygiene" plus running
   `python3 h-mad/scripts/h_mad_context_budget.py --window 1000000 --ceiling 45 --mode advisor`
   yourself.
4. **[suggested] Decide the fate of the inbound handover** at
   `docs/handoffs/2026-08-24-main__audit-dispatch-contract-integrity.md` — see Open Items; its stated
   status is stale.

## Open / Blocked Items

- **J44 — the `advisor` PreToolUse hook never fires** — status: open, `MONITORING`. The only open
  registry entry. `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none (main worktree)`.
  Refuted twice with a self-tested detector. The gate's *logic* is fully verified and correct on every
  branch; this is an attachment-point defect. Leading hypothesis: `advisor` does not traverse
  PreToolUse at all.

- **A sibling session is editing this working tree, and its own brief understates that** — status:
  **hazard, not mine to resolve**. `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none
  (main worktree)`. Seven files are modified that I never touched: `h-mad/SKILL.md`,
  `h-mad/audit-prompt.template.md`, `h-mad/references/orchestration-mode.md`,
  `h-mad/scripts/h_mad_assemble_audit.py`, `h-mad/scripts/h_mad_audit_gate.py`,
  `h-mad/tests/test_h_mad_assemble_audit.py`, `h-mad/tests/test_h_mad_audit_gate.py`. Ten tests in
  `test_h_mad_audit_gate.py` fail in that state; the same file is **22/22 at clean HEAD**, so the
  failures are their mid-edit state and not a regression on main.

- **The inbound handover's status line is STALE — do not act on it as written** — status: needs an
  operator call. `docs/handoffs/2026-08-24-main__audit-dispatch-contract-integrity.md` carries
  `**Handover-From:** HemaSuite · feature/201-grounding-evidence-coverage · session a7f5968f-…` and
  says all three defects are "not started, unclaimed". **D-2 is in fact already implemented in the
  working tree** — `_is_none_sentinel` in `h-mad/scripts/h_mad_audit_gate.py`, uncommitted, with its
  tests mid-edit. A resume that trusts "not started" will start over on top of half-finished work.
  The brief itself is untracked (`??`), so it is not on any remote. State file for the claim:
  `/Users/kimhawk/orca/skills/docs/.bkit-memory.json`, feature `audit-dispatch-contract-integrity`.
  **I did not claim it** — the user did not ask me to, and a live session appears to hold the work in
  practice even though the state file does not.

- **Two remote-only branches survive their deleted local counterparts** — status: deferred, cosmetic.
  `origin/feature/audit-cycle-verb` and `origin/fix/j40-review-evidence-gate`. Deleting a local branch
  leaves the remote; `git push origin --delete <b>` if wanted. Five other remote-only branches are
  genuinely unmerged and were left alone.

- **`test_verb_no_self_invocation`'s in-process-`main` re-entry class stays untested** — status:
  accepted, with the reason now established rather than assumed. A mutation re-entering via `main`
  recurses unboundedly because `main` is not stubbed; the dispatch path through `_cmd_exec` **is**
  stubbed and is covered. Recorded in `h-mad/tests/mutation-specs/verb_no_self_invocation.json`.

## Context for Next Session

**Files touched this session (all committed + pushed):**
- `h-mad/scripts/h_mad_offcontract_scan.py` (new — the off-contract artifact locator)
- `h-mad/tests/test_h_mad_offcontract_scan.py` (new, 11 tests),
  `h-mad/tests/mutation-specs/offcontract_scan.json` (new, 10 mutants)
- `h-mad/tests/test_hmad_dispatch_audit_cycle.py` (vacuity guard),
  `h-mad/tests/mutation-specs/verb_no_self_invocation.json` (new, 2 mutants)
- `h-mad/references/failure-recovery.md` (audit no-report row → scan before re-dispatch)
- `h-mad/references/agent-substrate.md`, `h-mad/SKILL.md`, `h-mad/scripts/h_mad_assemble_audit.py`,
  `h-mad/scripts/hmad-dispatch.sh` (exec-size claim → 266,342 B datapoint)
- `docs/skill-monitoring.md` (J30 close, J28 stale-mechanism clause, J44 + J45), `docs/learnings.md`

**Uncommitted changes:** none of mine. Seven files + one untracked handoff belong to a sibling
session — see Open Items. **Do not `git add -A` in this repo right now.**

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
git status --short          # expect the sibling's 7 files; confirm before staging anything
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests -q   # 1612 at clean HEAD; 10 fail on their edits
```

**Interpreter:** bare `python3` is 3.14 with **no pytest** — always `/opt/anaconda3/bin/python3.11`.
Bare `pytest` from the repo root collects the sibling `hematology-paper-writer/` and dies on
pre-existing collection errors; always scope to `h-mad/tests`. To measure your own change cleanly in
this shared tree: `git worktree add --detach /tmp/check HEAD`, copy your files in, run there, then
`git worktree remove /tmp/check --force`.

**Related docs:**
- `docs/skill-monitoring.md` — 42 entries; header documents the lifecycle vocabulary. **Count
  `MONITORING`, never the absence of a word.**
- `docs/handoffs/2026-08-24-main__audit-dispatch-contract-integrity.md` — the inbound handover
  (untracked, and its status line is stale)
- `h-mad/references/failure-recovery.md` — the audit no-report recovery row now names the locator
