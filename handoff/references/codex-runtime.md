# Codex runtime adapter

Use this adapter only when the active host is OpenAI Codex. It overrides host-specific mechanics
in `../SKILL.md`; it does not weaken the handoff protocol.

## Resolve the skill package

Set `HANDOFF_SKILL_ROOT` to the installed package containing this reference. Resolve it from the
loaded skill path, never from a user-specific checkout. All bundled commands then live under
`$HANDOFF_SKILL_ROOT/scripts/`. If the package is incomplete, stop and report the missing path.

Do not use a Claude-specific skill-root variable or home-directory path in Codex commands.

## Codex tool mapping

- Persist restored work in the native task tool when one is available. Otherwise update
  `.omc/notepad.md`; if neither is writable, return an inline checklist. READ must name the sink
  and must never silently skip restoration.
- Use `request_user_input` for a short choice only when that tool is available and the choice is
  optional. When explicit input is required and the tool is unavailable, ask one concise prose
  question and stop.
- Use `collaboration.spawn_agent` only for an independent verification or delegated delivery that
  the mode actually calls for. Use `fork_turns: "none"` for a clean reviewer and `fork_turns:
  "all"` only when the worker must inherit the current context. Do not spawn merely to read a file.
- When the source protocol names another skill, invoke the matching installed Codex skill if it is
  available. Otherwise perform the bounded step inline; never invent a skill or silently omit it.
- Use `apply_patch` for handoff or learning file edits. Preserve unrelated worktree changes.

## Mode routing

- **WRITE** closes the current session. Follow the source sections `WRITE mode flags`, `Audience`,
  `Where to save`, `Gather context before drafting`, `Required template`, and `After writing`.
  Preserve the canonical main-worktree store, branch-qualified filename, `Supersedes` chain,
  carry-forward rules, preflight, scoped commit, sync, push, and post-push verification. Orca
  checkpointing remains best-effort.
- **READ** replaces session context and therefore requires a fresh session. Follow `Reading a
  handoff` Steps 0a through 5. Locate with `scripts/handoff_paths.py`, reconcile every claim with
  git and live state, apply only the source allowlist of mechanically unique repairs, restore tasks,
  report, and stop. Do not resume substantive work in the same turn.
- **LEARN** records or searches one durable lesson through `scripts/learn.py`. Keep the kernel
  concise, categorized, tagged, and deduplicated; report the written or matched entry and stop.
- **HANDOVER** transfers owned work to another repo, worktree, or agent. Release the advisory
  claim before delivery, write into the receiver's canonical store, verify the receiver identity,
  deliver through the installed Orca capability when present, and stop monitoring after delivery.
- **TAKEOVER** adopts one inbound brief mid-session. Re-check its premises, claim through the
  liveness oracle, restore only its origin-scoped tasks, stamp the takeover, make the scoped commit,
  acknowledge it, and return to the current session. It does not perform full READ reconciliation.

## Construct mapping

| construct | status | mapping | source |
|---|---|---|---|
| `skill-call` | mapped | Use the installed handoff skill named in Codex's Skills instructions; load its `SKILL.md` when invoked. | observed Codex Skills instructions (DP16) |
| `task-tools` | not-applicable | No current rung 1 task checklist tool is evidenced; `update_plan` remains a lead from older rollouts. Restore to `.omc/notepad.md` when writable, then an inline checklist. | A3; observed Codex 0.142.0 rollouts (DP16) |
| `tool-search` | not-applicable | No rung 1 todo tool is evidenced, so there is no deferred task tool to load. | A3; Codex 0.157.1 feature list |
| `skill-root-env` | mapped | Resolve `HANDOFF_SKILL_ROOT` from the loaded handoff `SKILL.md` path. | existing adapter rule; observed Codex Skills instructions (DP16) |
| `todo-tools-optin` | not-applicable | No rung 1 todo tool is evidenced, so there is no opt-in setting to enable. | A3; Codex 0.157.1 feature list |
| `claude-md` | mapped | Read `AGENTS.md` for project instructions. | observed Codex rollouts (DP16) |
| `claude-skills-dir` | mapped | Load handoff from its installed `~/.agents/skills/handoff` package path. | observed Codex Skills instructions (DP16) |
| `claude-settings` | not-applicable | Codex hooks use a hooks file rather than Claude's settings file. | observed Codex hooks configuration (DP16) |
| `claude-handoffs-dir` | mapped | Keep the existing shared handoff file store; Codex reads and writes it through the shell. | observed shared store index |
| `session-reset-command` | not-applicable | No Codex reset command is evidenced; start a fresh `codex exec` session for READ. | Codex 0.157.1 help; observed prompt history (DP16) |
| `skill-slash-invocation` | mapped | Name the installed skill as `$handoff` or in plain text. | observed Codex Skills instructions (DP16) |
| `claude-homunculus` | mapped | Keep the optional file read when the source path is present. | observed optional store path |

## Safety invariants

Keep the source fail-closed rules: never choose a different branch's newest handoff without user
confirmation; never repair ambiguous divergence; never claim or release anonymously; never stage
the whole repository for a scoped handoff commit; and never report delivery, takeover, push, or
restoration without checking the observable result.
