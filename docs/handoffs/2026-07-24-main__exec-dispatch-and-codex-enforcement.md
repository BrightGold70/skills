# Handoff — Exit-code dispatch verbs (codex+agy) + Codex-authorship enforcement

**Date:** 2026-07-24
**Branch:** main
**Project:** BrightGold70/skills (`/Users/kimhawk/orca/skills`) + coupled BrightGold70/HemaSuite

## Session Summary

Resumed from `2026-07-24-main__skill-candidate-upgrades` and cleared its 4 todos, then
the session turned into a multi-agent-dispatch arc. Shipped: **`hmad-dispatch exec
<codex|agy>`** — an exit-code (headless subprocess) dispatch path alternative to the
pane REPL, for Codex 5d/5e implementation *and* agy audits/reviews — and a **Codex-
authorship enforcement gate** in the Phase-5 TDD hook so Claude can no longer self-
implement while Codex is available. All merged to `main` (skills) with a coupled
HemaSuite test commit; both clean and in sync. Recurring lesson: **twice** the stub
suite certified a real dispatch-arg bug green; only live dogfooding against the real
CLIs caught it.

## Key Learnings

- **The stub suite certified 2 real dispatch-arg bugs green this session; live runs
  caught each.** (1) bash nul's a backgrounded command's stdin → the `--timeout` path
  starved `codex exec -` of its prompt. (2) `agy --print` consumes the NEXT token as
  its prompt, so a non-adjacent `--print` ate the following flag and dropped the real
  prompt (agy just greeted). Same shape as the tracer-bullet discipline: never trust a
  green stub suite for a real-CLI integration.
- **The Codex-authorship enforcement insight:** the `Write|Edit` PreToolUse hook only
  fires on **Claude's** tool calls. Codex writes via its own process (`exec`
  subprocess or pane `send`) — never through Claude's Write/Edit — so a production
  `.py` write *reaching the hook* during step5 is, by construction, Claude self-
  implementing. That is the signal to gate on. Fallback is an auditable state field
  (`codex_status=exhausted`), never silent.
- **Agent identity resolution is robust, not "complete".** Owned path (launch/pin) and
  the new `exec` path (pane-free subprocess) are solved; un-owned auto-detect is
  recovered by J16's paneKey join but degrades to safe-UNRESOLVED where `worktree ps`
  can't disambiguate. Blocked upstream by orca#9870 (`terminal list` has no identity
  field). Antigravity was the weakest case — `exec agy` now gives it a pane-free path.
- **learn cap raised 200→240** (`MAX_KERNEL`), yet this session's kernels *still* hit
  it 3–4× (payoff-at-end fights the cap; `--trim` would cut the punchline). Live
  evidence the cap may want to go higher, or that kernels should lead with the finding.

## Next Steps

1. **Drive the `exec` verbs inside a real full /h-mad Phase-5 cycle** (5d RED + 5e
   GREEN + 5e-review), end to end — so far only the dispatch chain is dogfooded in
   isolation. `h-mad/SKILL.md` §"Exit-code dispatch for 5d/5e"; `hmad-dispatch.sh`
   `_cmd_exec`.
2. **Exercise the Codex-authorship fallback live.** The gate blocks self-implement
   when Codex is available; the `codex_status=exhausted` fallback path is unit- and
   dogfood-verified but never hit in a real quota-exhausted run. `hooks/h-mad-tdd-gate.sh`.
3. `[suggested]` **Auto-detect Codex quota exhaustion** so `codex_status` need not be
   set by hand — e.g. an `exec codex` that returns a quota-error exit code could write
   `codex_status=exhausted` itself. Today it is a manual, deliberate declaration.
4. `[suggested]` **Reconsider the learn cap again** (Next-Step carryover) — 240 still
   forced 3–4 rewrites this session. `handoff/scripts/learn.py:59` (`MAX_KERNEL`).

## Open / Blocked Items

- **exec verbs** — status: unit + live dogfooded in isolation; NOT yet run inside a
  real end-to-end /h-mad Phase-5 cycle.
- **Codex-authorship gate** — status: live via symlink (`~/.claude/hooks/h-mad-tdd-gate.sh`
  → repo). Active now; harmless outside a step5 run. Fallback path not live-exercised.
- **agy `--sandbox`** — status: passthrough boolean only; its restriction semantics not
  explored. `codex_status` has no auto-detect (manual only).
- **learn 200/240 cap** — status: raised to 240, still tight for payoff-at-end kernels.

## Context for Next Session

**Files touched this session (skills):**
- `h-mad/scripts/hmad-dispatch.sh` — `_cmd_exec` (`exec <codex|agy>`), `_run_with_timeout`
- `h-mad/hooks/h-mad-tdd-gate.sh` — Codex-authorship gate
- `h-mad/scripts/h_mad_state_schema.json` — optional `codex_status` enum
- `h-mad/tests/test_hmad_dispatch_exec.py` (24), `test_h_mad_tdd_gate_codex.py` (6) — new
- `h-mad/tests/stubs/codex`, `h-mad/tests/stubs/agy` — new
- `h-mad/references/agent-substrate.md`, `h-mad/SKILL.md` — verbs table + 5d/5e sections
- `handoff/scripts/learn.py` + `test_learn.py`, `handoff/SKILL.md` — `MAX_KERNEL` 240
- `docs/skill-candidates.md` (backlog reconcile), `docs/learnings.md`

**Files touched (HemaSuite):** `hematology-paper-writer/tests/test_h_mad_tdd_gate.py` only.

**Uncommitted changes:** none in skills. HemaSuite has unrelated pre-existing dirty
files (pins/telemetry/pdca-status/trial.md) that are NOT this session's — leave them.

**Deleted:** local branch `BrightGold70/hmad-j15-live` (throwaway; recover via
`git branch <name> 479cfce`).

**Commits this session (skills, all on main):** `ac48740` ask-dogfood learning ·
`554409f` backlog reconcile · `ce45be4` learn cap 240 · `f1ebbac` exec codex ·
`0dea14f` exec agy · `5ad59c5` Codex-authorship gate. **HemaSuite:** `901aaad3`.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git pull --ff-only
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
hmad-dispatch env                                    # PREFLIGHT: PASS
/opt/anaconda3/bin/python3 -m pytest h-mad/tests/ handoff/scripts/ -q   # 708 + handoff
# try the new verbs (real CLIs):
hmad-dispatch exec codex <promptfile> --out /tmp/x.txt --timeout 900
hmad-dispatch exec agy   <promptfile> --out /tmp/r.txt --timeout 600
```

**Related docs:**
- `h-mad/SKILL.md` §"Codex authors Phase 5 — enforced" + §"Exit-code dispatch for 5d/5e"
- `h-mad/references/agent-substrate.md` — `exec` verbs-table row
- `docs/handoffs/2026-07-24-main__skill-candidate-upgrades.md` — the resumed session

## Version History
- v1.0: exec dispatch verbs (codex+agy) + Codex-authorship enforcement.
