# Handoff — Add grok as the h-mad fallback when codex is unavailable

**Date:** 2026-09-28
**Branch:** main
**Project:** skills
**Handover-From:** HemaSuite · feature/28-review-manifest-guideline-evidence · session 738e5628-0d9b-46d3-9184-d056e0704d0b
**Supersedes:** none — first on this branch for this topic

## Session Summary

When codex runs out of quota, h-mad has only two fallbacks today:

- **Phase 5 implementation:** `codex_status=exhausted` lets Claude write the production code itself.
- **Audit gating:** a doc-auditor teammate stands in for codex. It is the same model family as the orchestrator, so its blind spots overlap the orchestrator's.

The operator asked to use **Grok** as the fallback instead. HemaSuite ran a first trial, and it passed on the easiest phase: grok 1.0.41 in headless mode executed an h-mad test-writing (RED) dispatch correctly. This brief hands the feature to the skills repo, where `hmad-dispatch` and the h-mad state schema live. **No work has started and nothing is claimed.** Run it as an H-MAD feature: `/h-mad "grok-codex-fallback"`.

## Key Learnings

- **Headless invocation that worked:**
  `env -u CLAUDE_CODE_SESSION_ID -u CLAUDE_CODE_SESSION_ATTENDED -u CLAUDE_EFFORT HPW_AGENT_BACKEND=claude hmad-dispatch run --timeout 1500 -- grok --cwd <dir> --always-approve --prompt-file <prompt>`.
  - `-p/--single` **cannot** be combined with `--prompt-file`; argparse exits with rc=2.
  - stdout carries the final message, and it ended in a parseable `STATUS: DONE`.
  - grok also wrote the report file the prompt named.
- **Trial result.** This was HemaSuite #28 Task 2's RED prompt (a refactor task), run in a throwaway worktree at `ca56d86b`:
  - rc=0, 543 s.
  - The planned split was 5 failing / 1 passing; re-running it myself gave exactly that.
  - It wrote only the test file, and its failure reasons were correct.
  - Its 4 test functions are the same ones the Claude-authored version has.
- **The environment-marker conflict applies to grok too.** HPW's backend resolver raises `Conflicting agent backend markers` when the child process inherits `CLAUDE_*` variables. Strip them, or set `HPW_AGENT_BACKEND` explicitly.
- **agy is a weak audit leg on evidence so far.** On HemaSuite #28 5b cycle 1 it read the tree (52 tool calls, all ok) and still produced 3 of 3 false findings. That makes an independent model family worth having, but only once it has been measured.

## Next Steps

1. `/h-mad "grok-codex-fallback"` in `/Users/kimhawk/orca/skills`; this is a fresh feature, so claim it with `--create --claim`. Run the brainstorm against the scope below.
2. **Scope:**
   - (a) Add `hmad-dispatch exec grok`, parallel to `exec codex` / `exec agy`, in `h-mad/scripts/hmad-dispatch.sh`. It needs `--out`/`--log`, a timeout, and verdict recovery. It must clear the `CLAUDE_*` environment and pass `--cwd`, `--always-approve` and `--prompt-file`.
   - (b) Add a routing value to `codex_status` (`h-mad/scripts/h_mad_state_schema.json:144`, enum `available|unavailable|exhausted`), such as `grok`, or a separate `fallback_agent` field. With it, the TDD gate (`h-mad/hooks/h-mad-tdd-gate.sh:139-142`) still blocks Claude's own production writes and Phase 5 routes to grok.
   - (c) Extend `h_mad_assemble_tdd.py` so its printed command block can target grok.
   - (d) Document grok as a candidate independent audit leg in SKILL.md §"Never gate on one audit pass" / §"Teammate audit leg".
3. **Measure before trusting**, the same way agy was measured:
   - a GREEN dispatch;
   - mutation-kill quality on a completed task;
   - a `wiring` task, where the test that proves the connection must fail on the caller's behaviour;
   - audit-leg precision: false-finding rate against codex/teammate on an already-audited document.
4. Check `grok --output-format` values for a stream/NDJSON option that `hmad-dispatch progress` and `h_mad_review_evidence.py` could parse. Neither parses grok's transcript today.

## Open / Blocked Items

- **Feature not started.** repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills (main checkout).
- **Trial artifacts** are read-only, in HemaSuite: `/Users/kimhawk/orca/HemaSuite/docs/03-analysis/grok-tracer-2026-09-28/`. The directory holds the prompt, grok's stdout, its report, and the test file it wrote (`grok_test_restoration_title_corroborated.py.txt`). Committed as HemaSuite `3317254c` on `feature/28-review-manifest-guideline-evidence`.
- **Unmeasured:** GREEN, mutation quality, wiring pins, audit leg, and cost/latency. The single trial took 9 min for a small RED.
- **No claim to release.** Nothing in `/Users/kimhawk/orca/skills/docs/.bkit-memory.json` names grok.

## Context for Next Session

**Files to touch (expected):** `h-mad/scripts/hmad-dispatch.sh` (the backend switch near `:282-293`), `h-mad/scripts/h_mad_state_schema.json:144`, `h-mad/hooks/h-mad-tdd-gate.sh:139-142`, `h-mad/scripts/h_mad_assemble_tdd.py`, `h-mad/SKILL.md`, `h-mad/references/agent-substrate.md`.

**Uncommitted changes (skills, pre-existing, not ours):** `.gitignore`, `.ignore`, `.mcp.json`, `AGENTS.md`, `docs/03-analysis/jev-system-one-adaptation.md`.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
grok --version            # expect 1.0.41+
echo "${XAI_API_KEY:+set}"
/h-mad "grok-codex-fallback"
```

**Related docs:**
- HemaSuite handoff that raised this: `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-09-28-feature-28-review-manifest-guideline-evidence__rmge-tasks-0-5.md`
- Memory: `feedback_codex_dispatch_poisons_hpw_backend_markers.md`
