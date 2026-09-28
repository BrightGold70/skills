# grok runtime adapter

Use this adapter when grok is the active handoff host. It supplies host mechanics for
`../SKILL.md`; follow that file for the handoff protocol and its stop conditions.

## Version and compatibility

These mappings were checked against grok 1.0.41. Run `grok inspect` and check its
Harness Compatibility section on the active installation. Grok loads the Claude
skill package through `compat.claude.skills`; verify that bridge is enabled before
invoking the skill. Record a changed version or compatibility setting during the
live smoke rather than assuming the mapping still applies.

## Resolve the skill package

Set `HANDOFF_SKILL_ROOT` from the loaded skill path containing this reference. Today
grok loads `~/.claude/skills/handoff` through `compat.claude.skills`; an installed
`~/.agents/skills/handoff` link can point to the same package. Run bundled scripts
from `"$HANDOFF_SKILL_ROOT/scripts/"`. If the package is incomplete, stop and report
the missing path. Do not infer the root from a user-specific checkout.

## grok tool mapping

- Restore READ tasks with the built-in `todo_write` checklist. Its separate pane is
  user-visible and toggled with `Ctrl+T`. Name the task sink in the READ report;
  never silently skip restoration. If that tool is unavailable, use the source
  fallback ladder: `.omc/notepad.md` when writable, then an inline checklist.
- Use `spawn_subagent` only for independent verification or delivery that the mode
  calls for. Give the child a self-contained prompt; it does not inherit the parent
  transcript. Check the resulting worktree changes before accepting its report.
- Resolve `HANDOFF_SKILL_ROOT` from the loaded skill path before calling bundled
  scripts. Invoke another installed skill by its slash command when the source
  protocol calls for it; otherwise perform the bounded step inline.

## Mode routing

- **WRITE** follows the source rules for the canonical main-worktree store,
  branch-qualified filename, `Supersedes` chain, carry-forward, preflight, scoped
  commit, sync, push, and post-push verification. Orca checkpointing is best-effort.
- **READ** requires a fresh session. In a loaded session, stop and instruct the user
  to run grok's `/new` (alias `/clear`) and re-invoke `/handoff` for READ. In that
  fresh session, locate the handoff with `scripts/handoff_paths.py`, reconcile claims
  with git and live state, restore tasks with `todo_write`, report, and stop.
- **LEARN** records or searches one durable lesson with `scripts/learn.py`, then
  reports the written or matched entry and stops.
- **HANDOVER** releases the advisory claim before delivery, writes into the
  receiver's canonical store, verifies receiver identity, delivers through the
  installed Orca capability when present, and stops monitoring after delivery.
- **TAKEOVER** re-checks one inbound brief, claims through the liveness oracle,
  restores only origin-scoped tasks, stamps the takeover, makes the scoped commit,
  acknowledges it, and returns to the current session.

## Construct mapping

| construct | status | mapping | source |
|---|---|---|---|
| `skill-call` | mapped | Invoke the installed `/handoff` skill. | `08-skills.md` |
| `task-tools` | mapped | Restore tasks with built-in `todo_write`; the checklist has a user-visible pane toggled by `Ctrl+T`. | `01-getting-started.md`; `16-subagents.md` |
| `tool-search` | not-applicable | `todo_write` is built in, so there is no deferred task tool to load. | `01-getting-started.md` |
| `skill-root-env` | mapped | Resolve `HANDOFF_SKILL_ROOT` from the loaded handoff skill path. | `08-skills.md` |
| `todo-tools-optin` | not-applicable | Built-in `todo_write` needs no settings opt-in. | `01-getting-started.md` |
| `claude-md` | mapped | Read `Claude.md`, `CLAUDE.md`, or `AGENTS.md` as project rules. | `12-project-rules.md` |
| `claude-skills-dir` | mapped | Load from `~/.claude/skills/handoff` through `compat.claude.skills`. | grok inspect |
| `claude-settings` | not-applicable | Built-in `todo_write` needs no settings opt-in for handoff. | `01-getting-started.md` |
| `claude-handoffs-dir` | mapped | Keep the shared plain-file handoff store that hosts read and write. | observed: shared handoff index file |
| `session-reset-command` | mapped | Use `/new` (alias `/clear`) for a fresh READ session; `/compact` is also a documented session action. | `04-slash-commands.md` |
| `skill-slash-invocation` | mapped | Invoke `/handoff` as an installed skill. | observed: available_commands in sibling probe log |
| `claude-homunculus` | mapped | Keep the optional file read when the source path is present. | observed: optional store path |

## Safety invariants

Keep the source fail-closed rules: never choose a different branch's newest handoff
without user confirmation; never repair ambiguous divergence; never claim or
release anonymously; never stage the whole repository for a scoped handoff commit;
and never report delivery, takeover, push, or restoration without checking the
observable result. Inspect tracked and untracked worktree changes after a delegated
dispatch because a grok subagent has no filesystem jail.
