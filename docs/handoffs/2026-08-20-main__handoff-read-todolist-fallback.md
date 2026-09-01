# Handoff — handoff READ Step 4 hard-depends on a todo tool that does not exist

**Date:** 2026-08-20
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Handover-From:** HemaSuite · main · session 603da342-ea2b-40e9-b1a6-9cb1d6d3aae7
**Taken-Over-By:** skills · main · session unknown · backfilled 2026-09-01 — fixed in `2ce26d3` and `b79b036`; READ Step 4's opt-in + three-rung ladder is present in `handoff/SKILL.md` at HEAD

## Session Summary

A `/handoff read` in HemaSuite reconciled cleanly and then **silently failed to restore any todos**:
READ Step 4 instructs "Use the TodoList tool (TaskCreate or equivalent)", and this Claude Code
install has no todo-authoring tool in the main-loop tool set. The step has no fallback, so READ
half-completes — divergences reported, action queue evaporated — and nothing in the report says so.
The absence is environmental and unfixable from config; the skill defect is that Step 4 treats an
optional tool as guaranteed. **WRITE already hedges the same dependency and READ does not** — that
asymmetry is the bug. Scope: three edits in `handoff/SKILL.md`. Nothing is claimed; nothing is
in flight.

## Key Learnings

- **The tool is absent, not denied.** Ruled out one at a time on the reporting machine: project
  `permissions.deny` holds only 8 `Bash(...)` rules; `~/.claude/settings.json` has no
  `disallowedTools`; `outputStyle` is `None` and `~/.claude/output-styles` does not exist; of 26
  enabled plugins only context-mode names `TodoWrite`, and only as a **PostToolUse matcher**
  (`…|TodoWrite|TaskCreate|TaskUpdate|…`), which does not remove a tool. Feature flags say todos are
  ON (`showExpandedTodos: true`, `hasSeenTasksHint: true`).
- **Measured, not inferred: 0 `TodoWrite` tool_use calls in all 60 HemaSuite transcripts and across
  every other project on that machine.** So this is not a today regression and not session-specific.
- **Why the name is everywhere anyway.** All 63 attachment-level mentions of `TodoWrite` are one
  string — the **bkit agent catalog** declaring `(Tools: …, TodoWrite, …)` for its *subagents*. A
  grep for the name finds it in every transcript and proves nothing about the main loop. Distinguish
  `"name":"TodoWrite"` inside a `tool_use` block from a prose/catalog mention before concluding.
- **`ToolSearch` confirms the negative.** `select:TodoWrite,TaskCreate` → no match; `+todo` → no
  match. The deferred catalog carries `TaskOutput`/`TaskStop` (background tasks) but nothing that
  authors a list. Built-ins in that session were `Agent / Artifact / AskUserQuestion / Bash / Edit /
  ListAgents / Read / ReportFindings / ScheduleWakeup / SendUserFile / Skill / ToolSearch / Workflow
  / Write / advisor`.
- **No user config can add a built-in tool.** The only lever available is the skill.

## Next Steps

1. **Rewrite READ Step 4 as a fallback ladder** — `handoff/SKILL.md:246–248` (§"Step 4: Restore the
   TodoList"). Current text: *"Use the TodoList tool (TaskCreate or equivalent) to repopulate todos
   from the doc's **Next Steps** and **Open / Blocked Items**."* Replace the unconditional
   instruction with, in order: (a) a task/TodoList tool if one exists; (b) OMC's
   `mcp__plugin_oh-my-claudecode_t__notepad_write_working` when that MCP is present (project-scoped,
   survives `/clear`, 7-day prune); (c) an inline numbered checklist in the Step 5 report. Keep every
   existing Step 4 rule — the `[<repo>@<branch>]` prefix, the `[verify path — file moved since
   handoff]` inline note, and the dedupe rule — they apply to all three sinks. **The step must never
   be a no-op.**
2. **Name the sink in the Step 5 report** — `handoff/SKILL.md:258` and the fenced report template
   below it. Add a `**Todos restored to:** <task tool | .omc/notepad.md | this report only>` line.
   Without it a reader cannot tell a successful restore from a skipped one; that is what made the
   failure silent.
3. **Fix the `description:` frontmatter** — `handoff/SKILL.md:3` promises READ "restoring the
   TodoList". Soften to "restoring the todo list (task tool where available, durable fallback
   otherwise)" so the description does not advertise a hard dependency.
4. **Sweep for the same asymmetry elsewhere.** `handoff/SKILL.md:582` (WRITE gather step 2) already
   reads *"if you have a TodoList / task tool"* — that is the correct shape and the model for the
   Step 4 rewrite. Grep the rest of the skills tree for other unconditional tool assumptions:
   `grep -rn 'TodoList\|TaskCreate\|TodoWrite' --include='SKILL.md' /Users/kimhawk/orca/skills`

## Open / Blocked Items

- **This item** — status: handed over, unstarted. `repo: /Users/kimhawk/orca/skills · branch: main ·
  worktree: /Users/kimhawk/orca/skills (main worktree, none linked)`. Artifacts: `handoff/SKILL.md`
  (lines 3, 246–248, 258, 582). No plan/spec doc exists; scope is small enough not to need one.
- **h-mad claim** — status: none to release. `h_mad_resume_decision.py --state
  /Users/kimhawk/orca/skills/docs/.bkit-memory.json --feature handoff-read-todolist-fallback`
  returned `start_fresh`, and the state file has **no record** for that feature. Nothing was claimed
  and nothing was force-taken. Claim it normally if you run this through h-mad.
- **Not reproducible from config** — status: won't-fix by design. Do not spend time trying to
  re-enable the tool; verify the fallback path instead. A machine that *does* have a task tool will
  take branch (a) and never exercise (b)/(c), so test the fallback by reasoning about the ladder
  rather than waiting for an environment that lacks it.

## Context for Next Session

**Files touched this session (in this repo):** none — this brief is the only write.

**Uncommitted changes:** this brief, untracked.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
sed -n '240,275p' handoff/SKILL.md   # Step 4 + Step 5 report template
sed -n '578,586p' handoff/SKILL.md   # the WRITE-side hedge to mirror
```

**Reporting-side evidence (HemaSuite, for reference only):**
- Todos from the failed restore were parked in `/Users/kimhawk/orca/HemaSuite/.omc/notepad.md`
  (Working Memory, 10 items) — that is the manual version of the fallback this fix should automate.
- `hmad-dispatch` is not on PATH there; it lives at `~/.claude/skills/h-mad/bin/hmad-dispatch`
  (symlink into this repo).
