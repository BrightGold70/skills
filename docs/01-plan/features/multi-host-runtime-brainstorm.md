# Brainstorm: multi-host-runtime

## Executive Summary

Make `h-mad` and `handoff` run correctly with **codex, agy or grok as the orchestrator host**. The work has three parts:
- a grok host adapter that documents only where grok diverges from Claude Code (grok already loads Claude skills, agents and hooks);
- a registry-driven **parity gate** that fails when a Claude-specific construct in either `SKILL.md` has no mapping row in each host adapter;
- the missing `~/.agents/skills/{h-mad,handoff}` install for hosts that read that root, with an install check.

## Problem Statement

Both skills are written in Claude Code's vocabulary. On 2026-09-28, `grep -c -E 'Agent\(|subagent_type|TaskCreate|ToolSearch|advisor\(\)|Skill\(|AskUserQuestion|PreToolUse|CLAUDE_CODE'` counted 39 matching lines in `h-mad/SKILL.md` and 8 in `handoff/SKILL.md`.
- **codex and agy** have adapters (`{h-mad,handoff}/references/{codex,agy}-runtime.md`). Nothing checks that they cover each construct, so drift is unmeasured.
- **grok** has no adapter.
- **`~/.agents/skills/h-mad` is absent.** A codex host that follows HemaSuite's `.codex/hooks.json` therefore finds no TDD gate. Codex worked around it with other file tools, so the absence is a bypass, not a block (brief `docs/handoffs/2026-09-28-main__codex-tdd-gate-defects.md`).

## Findings that shape the approach (measured 2026-09-28, grok 1.0.41, no model call)

- `grok inspect` in this repo lists `h-mad` and `handoff` as `user [claude]` skills. It reads them straight from `~/.claude/skills`, which is the same checkout. It also lists 71 agents, among them `spec-author`, `plan-author`, `design-author` and `implplan-author` from `~/.claude/agents`.
- grok's local user guide at `~/.grok/docs/user-guide/`:
  - `10-hooks.md`: `~/.claude/settings.json` hooks are scanned by default (Claude compatibility, configurable), and Claude-style tool names in matchers are mapped to grok's.
  - `08-skills.md`: `~/.claude/skills/` is scanned at the lowest precedence. `.agents/` is also a known skill root.
- `~/.grok/skills/` holds symlinks into `~/.agents/skills/`, the same layout codex uses.
- Unknowns for the adapter:
  - grok's equivalents of `Agent(subagent_type)` (the doc names a `spawn_subagent` tool), `advisor()`, the task sink, and `AskUserQuestion` (tool list names `ask_user_question`);
  - the session-id environment variable, since `h_mad_context_budget.py` keys on `CLAUDE_CODE_SESSION_ID`;
  - the hook payload field differences (`hookEventName` versus `hook_event_name`).

## Proposed Approach

Operator decisions from 2026-09-28 are marked **[D1]**–**[D4]**.

1. **[D1] Delta adapter over Claude compatibility.**
   - Write `h-mad/references/grok-runtime.md` and `handoff/references/grok-runtime.md`. Each documents only where grok diverges: tool names, the subagent call, what stands in for `advisor()`, the task sink, environment variables, hook payload keys, and project trust (`grok inspect` shows `Project trusted: no` here, and project Claude hooks need trust).
   - Each row cites a section of grok's user guide or a `grok inspect` reading.
   - The compatibility toggles the adapter relies on (`[compat.claude]` skills and hooks) are named, along with how to verify them.
2. **[D2] A curated construct registry drives the parity gate.**
   - Add a committed registry, for example `h-mad/references/host-constructs.json`. Each entry holds a construct id, a grep pattern, and the skills it applies to.
   - A test asserts (a) every registry pattern's hits in each `SKILL.md` are known, and (b) every host adapter has a row per construct, marked either `mapped` or `not-applicable` with a reason.
   - A coarse catch-all regex fails the test when a new Claude construct shows up in `SKILL.md` that the registry does not know.
   - Adapter rows are machine-readable, e.g. a fenced table with a construct-id column, so that a mention is not counted as a mapping.
3. **[D3] Scope covers codex, agy and grok.** The existing codex and agy adapters are brought to parity, and their gap is measured first.
4. **Install.** Symlink `~/.agents/skills/{h-mad,handoff}` into this checkout for hosts that read `~/.agents`, and add coverage to `h_mad_install_check.py`. It must follow the existing `SIBLING_*` rules and never copy. This absorbs the install half of the codex-tdd-gate brief.
5. **[D4] One live smoke per host.**
   - Each host loads h-mad headless and runs a read-only verb once, e.g. `/h-mad status grok-codex-fallback`, with the output recorded. The cost is a few cents per host.
   - This proves the host follows the adapter, not just that the adapter was written.
   - A host that cannot run (no auth or quota) halts and asks the operator. It never passes silently.

## Alternatives Considered

- **A full standalone grok adapter**, with its own `~/.grok` hooks and install. Rejected [D1]: it duplicates what grok already loads through Claude compatibility and doubles the surfaces that can drift.
- **A pure regex census with no registry.** Rejected [D2]: a token merely mentioned in an adapter would pass the test, and a mention is not a mapping.
- **grok only.** Rejected [D3]: the codex and agy adapters' drift is exactly the unmeasured risk.
- **Docs and offline tests only.** Rejected [D4]: a textual parity check cannot show that a host follows the adapter.

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| grok's Claude compatibility changes between versions (toggles, tool aliasing) | M | The adapter pins the grok version it was verified against and names the toggles; the live smoke re-verifies |
| The registry itself drifts (a new construct is added to SKILL.md unregistered) | H | The catch-all regex test fails on any unregistered Claude-looking token; calibrate it against today's SKILL.md at 0 false hits |
| Parity rows become boilerplate "not-applicable" | M | `not-applicable` requires a reason; the delta review spot-checks reasons against the host docs |
| Conflicts with grok-codex-fallback, which also edits `SKILL.md` and `agent-substrate.md` | H | Separate worktrees; merge grok-codex-fallback first; rebase this feature on it before its 5c baseline |
| `~/.agents/skills` symlinks couple repos (memory: skills symlink couples code, not stores) | M | The install check reports a split install; no copy mode |
| A session-id variable that differs per host breaks `h_mad_context_budget.py` (it keys on `CLAUDE_CODE_SESSION_ID`) | M | The adapter maps the variable; if a host has none, the budget reports `UNKNOWN` and that is stated |

## Dependencies

- grok 1.0.41 (`grok inspect`, and the user guide at `~/.grok/docs/user-guide/`), the codex CLI, and the agy CLI. They are dispatched agents per `invariants.base.md` §"No new external dependency" (amended in `0b3f969`).
- Sequencing: implementation merges **after** grok-codex-fallback (shared files).

## Open Questions

1. What stands in for `advisor()` on each host? Candidates: nothing (stated as not-applicable), or the host's subagent.
2. Where does the task sink live on grok (`todo_write`?) and on codex/agy? The handoff READ Step 4 ladder must name each host's rung 1.
3. What is the session id per host, as used by the context budget and claims?
4. Does `handoff` need hooks at all, or only `h-mad`?
5. The registry format and location: one shared file, or one per skill?

## Version History
- v1.0: Initial brainstorm draft (operator decisions D1–D4, 2026-09-28).
