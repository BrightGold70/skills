# Handoff — Seven PRs: mutation harness bundled, HANDOVER mode, two agy reviews applied

**Date:** 2026-08-03
**Branch:** main
**Project:** /Users/kimhawk/orca/skills (symlinked as `~/.claude/skills/h-mad` and `~/.claude/skills/handoff`)

## Session Summary

Resumed from the wire-pin-gate handoff, cleared its blocker, and shipped **seven PRs, all merged** — `main` @ `a6fd01d`, clean, zero open PRs. Three fixes to h-mad gates (#21 `WIREPIN: UNREADABLE`, #22 claim/resume staleness reconciliation, #23 the bundled Phase-5e mutation harness), a new HANDOVER mode for the handoff skill (#24) plus the WRITE step that routes foreign work into it (#25), and two independent **agy reviews** applied in full (#26 handoff, 9 findings; #27 h-mad, 6 findings). HemaSuite Task 5 was **handed over** to its own worktree and is no longer tracked here. One task closed with *no* code: the "`hmad-dispatch launch` is broken" claim was falsified on re-probe.

## Key Learnings

- **A test that passes is not a verified test.** The mutation harness caught **six** tests passing for the wrong reason this session — including twice on tests written *for the harness itself*. Every one looked correct and was green. The recurring shape: asserting a *mention* rather than the *actionable thing* (`"git add -N" in text` passes when the prose mentions it but the copyable command is deleted; `restore_verified is True` stays true when the verification is removed; a filename appearing in a phase list keeps a routing test green while the instruction that uses it breaks). Treat "I wrote a test and it passed" as unverified until something kills it.
- **Both agy reviews found the same authoring defect: the doc names a hazard precisely, then withholds the command needed to avoid it.** Six of the ten findings across the two reviews were that shape — `git stash push` exits 0 on untracked paths (documented for months; `git add -N` appeared *nowhere* in h-mad), "presence is not enforcement" (in `invariants.base.md`, never reaching the spec-reviewer prompt), a preconditions check emitting no token while the caller is told to read one. An agent handed a rule without the means to obey it does not stop — it improvises. Worth grepping for this shape directly in any future review of this family.
- **Findings go stale in both directions — re-probe before acting.** "`hmad-dispatch launch` broken by J1 (no paneKey)" was recorded 08-02 and was **false** on 08-03: Orca 1.4.163's `terminal create --json` does return `paneKey`, and `launch` succeeded end-to-end in both worktrees. The J1 *protection* is still correct (the create-response `handle` genuinely is a pre-adoption placeholder absent from `terminal list`) — it was doing its job, not failing. Memory corrected.
- **`pin-agents` cannot resolve panes Orca does not track in `worktree ps` `agents[]`.** Its Pass-0 paneKey join has nothing to match, and `terminal read` returns 0 rows for *any* full-screen TUI (alt-screen buffer) — including known-good panes — so emptiness proves nothing. The join that works: `terminal switch` → `get-app-state`, where each handle yields a unique **focused element index**, ordered against the tab's pane control strip. Needed macOS Accessibility granted to the *helper* app; `orca computer permissions` self-reports `granted` while the actual call still returns `permission_denied`.
- **`merge-tree` clean does not mean the union is green.** Four PRs each merged cleanly against `main` individually, but #21↔#23 conflicted once one landed (adjacent edits to the same script-inventory block), and none had ever been *tested together*. Building a throwaway integration branch caught both before any merge.
- **The skills↔HemaSuite symlink makes exit-code changes cross-repo contract changes.** #27's M1 fix (preconditions now exits 0 with a token) turned HemaSuite's consumer suite red in four places while the skills suite stayed green at 992. Both suites have to gate a skill-script change; the skills suite alone would have shipped it.

## Next Steps

1. **[optional] Decide whether N1 should be a literal skill split.** #26 extracted auto-memories + automation-scout to `handoff/references/*.md` (progressive disclosure) rather than minting two new skills, as agy's fix text suggested. If separate skills were intended, that is a follow-up — see `handoff/SKILL.md` §"Update persistent auto-memories, then automation scout".
2. **[suggested] Re-run an agy review on `orca-cli` / `orchestration` boundaries.** Both were consulted heavily this session and neither was reviewed. The HANDOVER-vs-orca-cli-vs-orchestration arbitration now spans three skills' descriptions and is the least-tested part of the routing.
3. **[suggested] Grep the skill family for the "hazard named, command withheld" shape.** Six of ten review findings were this; the remaining instances are unlikely to be zero. Start from every place a doc says a command "exits 0" or "stashes nothing" or "reads empty" without an adjacent safe alternative.

## Open / Blocked Items

- **HemaSuite Task 5 — HANDED OVER, no longer tracked here.** This is a pointer, not a parking space (per `handoff/SKILL.md` §"Route foreign-worktree work before closing out"). Brief: `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-08-03-feature-196-grounding-shadow-measurement__task5-handover.md` (committed `5081b5fc`, pushed). `repo: /Users/kimhawk/orca/HemaSuite · branch: feature/196-grounding-shadow-measurement · worktree: none (main worktree)`. Unstarted; `PREFLIGHT: PASS`; the receiver owns it.
  - **One thing in that brief is now out of date in the receiver's favour**: it describes the pre-#22 claim dance (`--release` then `--claim`, with `--force` warnings). #22 is merged, so a stale claim is takeable by plain `--claim`. The dead session's claim (`73aae80d`, heartbeat `2026-08-02T06:08:58Z`) was deliberately **left in place** — taking ownership is the receiver's decision, not the sender's.
- **N1 interpretation — deferred, not blocked.** See Next Step 1.
- Nothing else is open. All five session todos closed; no in-flight work.

## Context for Next Session

**Files touched this session** (all merged to `main`; 21 files across 7 PRs):
- New: `h-mad/scripts/h_mad_mutation_harness.py`, `h-mad/scripts/h_mad_state_ownership.py`, `handoff/references/{auto-memories,automation-scout}.md`
- Changed: `h-mad/SKILL.md`, `handoff/SKILL.md`, `h-mad/scripts/{h_mad_wire_pin_gate,h_mad_state_write,h_mad_resume_decision,h_mad_do_preconditions}.py`, `handoff/scripts/handoff_paths.py`, `h-mad/references/{failure-recovery,codex-verifier-prompt,agy-spec-reviewer-prompt}.md`
- New tests: `h-mad/tests/test_h_mad_{mutation_harness,claim_staleness,agy_review_fixes}.py`, `handoff/scripts/test_handover_docs.py`

**Uncommitted changes:** none. `main` @ `a6fd01d`, in sync with `origin/main`.

**Other repo touched:** HemaSuite `feature/196-grounding-shadow-measurement` — two commits pushed: `5081b5fc` (Task 5 handover brief) and `ed053f1e` (consumer test follows the new `PRECONDITION:` token contract). Its one pre-existing dirty file (`.bkit/state/pdca-status.json`) was left untouched throughout.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main                                        # @ a6fd01d
/opt/anaconda3/bin/python3 -m pytest h-mad/tests handoff/scripts -q   # 992 expected

# the coupled consumer suite — the symlink means this repo's HEAD is what it runs
cd /Users/kimhawk/orca/HemaSuite/hematology-paper-writer
/opt/anaconda3/bin/python3 -m pytest tests/test_h_mad_*.py -q         # 48 expected
```
A bare `python3` is homebrew 3.14 with no pytest — use `/opt/anaconda3/bin/python3` for tests. The h-mad/handoff scripts are stdlib-only and run fine under bare `python3` (that constraint is tested).

**Running an agy review (the transport that worked):**
```bash
bash ~/.claude/skills/h-mad/scripts/hmad-dispatch.sh exec agy <prompt-file> \
  --cd <repo> --out <report.md> --log <run.log> --timeout 900
```
Headless `agy --print`, pane-independent — sidesteps pane identity entirely. **Read the report yourself**; an extract-then-gate pass has previously swallowed real Must-fix items from agy output.

**Related docs:**
- Prior handoff: `docs/handoffs/2026-08-03-fix-wire-pin-gate-qualifier-and-no-tasks__wire-pin-gate-hardened.md`
- The two review reports are session-scratchpad only and were **not** persisted; their findings live in PR #26 and #27 bodies.
- `h-mad/invariants.base.md` §"Audit-gate signal discipline" and §"Connection enforcement" — the two rules most of this session's fixes serve.
