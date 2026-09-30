# Handoff — h-mad: Codex TDD template recommends `hmad-dispatch run`, the Codex TDD gate blocks it

**Date:** 2026-10-01
**Branch:** main
**Project:** skills
**Handover-From:** HemaSuite · BrightGold70/citation-fidelity-judge · session ee5d7357-00a9-4192-8c8d-375e4ab3c317
**Taken-Over-By:** skills · main · session c7b2354c-1a9e-4733-95f0-a728f60cbbea · 2026-10-01
**Supersedes:** none — first on this topic

## Session Summary

HemaSuite's `citation-fidelity-judge` Phase 5 (Tasks 0–8, 2026-09-30) hit a contradiction inside h-mad itself. The Codex implementer prompt tells Codex to time-bound shell commands with `hmad-dispatch run --timeout <s> -- <cmd>`, and the Codex Phase-5 PreToolUse gate refuses `hmad-dispatch run` because `run` is not in its safe-verb allowlist. So whenever Codex followed the template and bounded its pytest run, the gate BLOCKED it. HemaSuite worked around this by appending "run the scoped pytest unbounded (no `hmad-dispatch run`)" to every dispatch. That workaround lives in one repo's handoff notes and does not fix the skill. Nothing has been fixed yet; this brief moves ownership of the fix to the skills lane.

## Key Learnings

- The conflict is real at `20b470ba` (skills `main`, 2026-10-01), re-verified by reading both files. It is not a stale report:
  - `h-mad/references/codex-implementer-prompt.md:35` reads: "When you need to time-bound a shell command, use `hmad-dispatch run --timeout <s> -- <cmd...>`". The surrounding paragraph also forbids `timeout`/`gtimeout` and says to halt rather than run unbounded.
  - `h-mad/hooks/h-mad-codex-tdd-gate.py:32-37`: `SAFE_DISPATCH_VERBS` = alive, await, clear, collect-report, env, file-diff, gate-create, gate-resolve, gate-wait, interrupt, notify, pin, pin-agents, progress, read, report-wait, resolve, resolved-model, verify, wait, worktree-comment, worktree-current, worktree-list, worktree-ps. **`run` is absent.** `_is_trusted_argv` (≈ line 364) returns True for hmad-dispatch only when `argv[1] in SAFE_DISPATCH_VERBS`.
  - Codex loads the gate through `.codex/hooks.json` in the consuming repo, which calls `$HOME/.agents/skills/h-mad/hooks/h-mad-codex-tdd-gate.py`. That path is symlinked to `/Users/kimhawk/orca/skills/h-mad`.
- The two instructions together leave Codex no legal way to bound a command. The template says "bound it with `run`, else halt"; the gate says "`run` is not allowed". An orchestrator that says "unbounded" contradicts the template's own no-unbounded rule. So the workaround trades one rule for another rather than resolving the conflict.

## Next Steps

1. Decide the direction; this is a design choice, not a typo.
   - **(a) Allow `run` in the gate.** Add `run` to `SAFE_DISPATCH_VERBS`, but only when the wrapped command is itself trusted. `run --timeout N -- <cmd>` executes an arbitrary `<cmd>`, so a bare verb add would let anything through the gate. The gate must recurse `_is_trusted_argv` on the argv after `--`. This is likely the right fix, because it keeps the template's hang-safety rule intact.
   - **(b) Change the template.** Stop recommending `run` under Phase 5 and say pytest runs unbounded under the gate. That weakens the hang-detection rationale the paragraph spells out.
   - Files: `h-mad/hooks/h-mad-codex-tdd-gate.py:32`, `h-mad/references/codex-implementer-prompt.md:35`.
2. Pin it with tests next to the existing gate tests. Both directions are needed:
   - `run --timeout 60 -- python -m pytest …` is ALLOWED.
   - `run --timeout 60 -- rm -rf x`, or any untrusted inner command, is BLOCKED.
   - Mutation-test the recursion guard, per the repo's mutation-test-every-guard practice.
3. Check `h-mad/SKILL.md`, `h-mad/references/agent-substrate.md` and `h-mad/invariants.base.md` for the same `run` recommendation. All three mention `hmad-dispatch run` per `grep -rln`. Keep them consistent with whichever direction is chosen.
4. After the fix lands, tell the HemaSuite lane it can drop the "unbounded pytest" ORCHESTRATOR NOTE. Receiver: `HemaSuite · BrightGold70/citation-fidelity-judge`, handoff chain `…citation-fidelity-judge__phase5-tasks-0-8.md`.

## Open / Blocked Items

- Template/gate `run` conflict — status: not started, owned by the skills lane from this handover.
  - `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills (main checkout)`
  - Evidence origin: `repo: /Users/kimhawk/orca/workspaces/HemaSuite/citation-fidelity-judge · branch: BrightGold70/citation-fidelity-judge`. The handoff there is `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-09-30-BrightGold70-citation-fidelity-judge__phase5-tasks-0-8.md`; see its Key Learnings bullet on `hmad-dispatch run --timeout`.
- No h-mad feature claim existed for this item, so nothing was released. The receiver may `--create --claim` it under this brief's slug (`codex-run-verb-conflict`).

## Context for Next Session

**Files touched this session:** none in skills. This session only wrote this brief.

**Uncommitted changes (skills main at handover):** none beyond this brief.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
sed -n 28,45p h-mad/references/codex-implementer-prompt.md
sed -n 30,40p h-mad/hooks/h-mad-codex-tdd-gate.py
grep -rn "hmad-dispatch run" h-mad/SKILL.md h-mad/references/agent-substrate.md h-mad/invariants.base.md
```

**Related docs:**
- `h-mad/hooks/h-mad-codex-tdd-gate.py` (`_is_trusted_argv`, `SAFE_DISPATCH_VERBS`)
- `h-mad/references/codex-implementer-prompt.md`
