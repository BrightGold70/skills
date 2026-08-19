# Handoff — advisor context budget, the advisor gate hook, and hook-wiring verification

**Date:** 2026-08-20
**Branch:** main
**Project:** /Users/kimhawk/orca/skills (h-mad skill)

## Session Summary

A prior session's context went from ~50% remaining to full in one turn; the investigation
established that `advisor()` forwards the entire transcript to a second model and bills it into
the same turn, so the turn costs ~2× the current context. This session turned that finding into
h-mad machinery in three shipped commits: a documented ceiling plus a measurement script
(`d6f88bd`), a `PreToolUse` hook that makes the ceiling a refusal (`079d8f7`), and a hook-wiring
checker plus a re-routed advisory ladder that makes **agy the default advisory channel** with
`advisor()` reserved for the hardest calls (`2c9ec82`). All three are merged and pushed to
`origin/main`; the h-mad suite ends at **1443 passed / 0 failed**. One verification is owed and
cannot be done from this session — see Open Items.

## Key Learnings

- **`advisor()` takes no parameters, so there is no way to send it less.** The payload *is* the
  transcript. The only levers are transcript size (`/compact`) and not calling it. Any plan that
  starts "make the advisor request smaller" is dead on arrival.
- **The advisor cost is invisible at the call site and scales with session age**, so the identical
  call is free in Phase 1 and fatal in Phase 6 — which is exactly where the tool's own "call
  before declaring done" guidance points. Following the instructions is what triggers the failure.
- **`set -euo pipefail` would have inverted the advisor gate.** The budget script exits 2 on a
  cannot-judge, and `PreToolUse` exit 2 means *block* — a fresh session with no usage record would
  have been denied the early, cheap call the ladder recommends. The hook is `set -uo pipefail` and
  branches on the `CTXBUDGET:` token, never the rc.
- **A safe-but-useless check stops being run.** `h_mad_context_budget.py` shipped with every test
  passing `--cwd <repo root>`; nothing exercised the default, and the *documented* invocation
  returned `UNKNOWN` from the skill's own directory. The cwd slug names the **session's** project
  root, not the process's cwd. It now resolves by `CLAUDE_CODE_SESSION_ID`.
- **Newest-mtime is the wrong way to find "your" transcript.** With two Claude sessions open on
  one repo it scores the other one, and a fresh sibling reads small — a false `OK`.
- **agy consults earn their keep on artifact questions.** Reviewing this very change, agy found
  two real source-resolution defects I did not have (`CLAUDE_CONFIG_DIR`; project settings resolve
  by walking **up** the tree). Its third claim — that `re.search("*", …)` would crash — was wrong
  about the implementation (match-all is handled before regex) and was kept as a test, not applied
  as a fix. Falsify each finding separately; facts, concern and prescription fail independently.
- **What defaulting to agy costs: trajectory awareness.** agy runs fresh and will confidently
  re-propose the fix you rolled back five minutes ago. Consulting it while *stuck* means handing
  it your dead ends explicitly, which is why 5d/5e and 6b are where it is the wrong tool.
- **A slice replacement can silently swallow an intervening subsection.** Rewriting SKILL.md from
  `### Above the ceiling` to `**Never batch…**` deleted the `### Making it mechanical` subsection
  that sat between them. Only its own docs test caught it — the edit reported success.
- **`a and b or c` is `(a and b) or c`.** A doc assertion written that way passes on the fallback
  alone; it looked like three checks and was one.

## Next Steps

1. **Live-fire the advisor gate — this is the top item and only works in a NEW session.** Hooks
   are snapshotted at session start, so nothing in this session proves the matcher fires:
   `HMAD_CONTEXT_WINDOW=1000 claude`, then make one `advisor()` call. It **MUST** be denied with
   `[H-MAD-ADVISOR-GATE] BLOCK`. If it sails through, the matcher never fired and that is the
   finding, not a pass — see `h-mad/SKILL.md` §"Making it mechanical — the advisor gate hook".
2. Sanity-check the wiring checker against a deliberately broken wiring, live rather than in
   pytest: temporarily narrow the TDD gate's matcher to `Write` in `~/.claude/settings.json` and
   confirm `python3 ~/.claude/skills/h-mad/scripts/h_mad_hook_wiring.py` reports
   `HOOK_WIRED_WRONG_MATCHER … uncovered=Edit`, then restore. Backup:
   `~/.claude/settings.json.bak-advisor-gate`.
3. Decide whether `HMAD_CONTEXT_WINDOW` should be derived rather than defaulted. The transcript's
   `message.model` reads `claude-opus-5` with no `[1m]` marker, so the 1M default cannot be
   confirmed from the JSONL — a smaller-window model silently gets a permissive ceiling. Entry
   point: `h-mad/scripts/h_mad_context_budget.py:DEFAULT_WINDOW`.
4. `[suggested]` Reconcile `docs/skill-candidates.md` — the automation scout run for this session
   appends to it, and prior handoffs recorded that open rows decay into already-shipped work.

## Open / Blocked Items

- **Advisor gate live verification — status: blocked on a new session.** Not blocked on any work;
  hooks load at session start and this session predates the wiring. Command in Next Step 1.
  Recorded in auto-memory so it survives a `/clear`.
- **`HMAD_CONTEXT_WINDOW` default is a guess — status: deferred, decision needed.** 1M is right
  for this machine's Opus 5 1M sessions and permissive for anything smaller. The deny message
  prints the assumed window so a wrong assumption is at least visible. See Next Step 3.
- **Duplicate hook wiring is not reported — status: deliberately declined.** The agy consult
  suggested a `HOOK_WIRED_MULTIPLE` warning. Declined because the harness runs each matching entry
  and double-fire is harmless for both gates, and a warn line inside a `FAIL`-shaped token trains
  the operator to ignore the token. Recorded here so the decision is not re-litigated as an
  oversight.
- **Nothing verifies the wiring checker itself is run — status: accepted.** Bootstrap now obliges
  it (`h-mad/SKILL.md` §"First-run auto-bootstrap" item 2), which is the same class of obligation
  every other h-mad gate has. There is no mechanical enforcement below that, by design: a wiring
  failure must never halt bootstrap.

## Context for Next Session

**Files touched this session:**
- `h-mad/SKILL.md` — new §"Orchestrator context hygiene (your own window)" with the channel-routing
  table, the ceiling, the gate hook, and §"Wired, not just installed" in the bootstrap section
- `h-mad/scripts/h_mad_context_budget.py` — new; `CTXBUDGET:` verdict
- `h-mad/scripts/h_mad_hook_wiring.py` — new; `WIRING:` verdict
- `h-mad/hooks/h-mad-advisor-gate.sh` — new; `PreToolUse` deny on `advisor`
- `h-mad/tests/test_h_mad_context_budget.py`, `…_context_budget_docs.py`, `…_advisor_gate.py`,
  `…_hook_wiring.py` — new
- `h-mad/tests/mutation-specs/{context_budget,context_budget_docs,advisor_gate,hook_wiring}.json` —
  new; the mutation specs are now parked in-repo rather than `/tmp`, so the guards are re-runnable
- `~/.claude/settings.json` — wired the advisor gate at `PreToolUse` index 3 (backup:
  `~/.claude/settings.json.bak-advisor-gate`). **Outside this repo; not committed anywhere.**

**Uncommitted changes:** none — `2c9ec82` is pushed and the tree is clean.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills/h-mad
python3.11 -m pytest tests/ -q                      # baseline: 1443 passed
python3 ~/.claude/skills/h-mad/scripts/h_mad_context_budget.py   # CTXBUDGET: OK …
python3 ~/.claude/skills/h-mad/scripts/h_mad_hook_wiring.py      # WIRING: PASS
# re-run any guard:
python3.11 scripts/h_mad_mutation_harness.py tests/mutation-specs/hook_wiring.json
```

Note: `python3` on PATH is 3.14 without pytest; use `python3.11` for the suite. `ls` and `grep`
are aliased to eza/ugrep — `ls -t` errors, use `/bin/ls -t`.

**Related docs:**
- `h-mad/SKILL.md` §"Orchestrator context hygiene (your own window)", §"Wired, not just installed",
  §"First-run auto-bootstrap"
- Auto-memory `feedback_advisor_doubles_context.md` — the measured 2.0× table, the routing policy,
  and the owed live-fire test
- Commits: `d6f88bd` (budget), `079d8f7` (gate hook), `2c9ec82` (wiring check + agy-first routing)
