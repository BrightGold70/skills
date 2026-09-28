# Multi-host runtime analysis

## Baseline at BASE_SHA

`BASE_SHA=3b5c4388b4f11b7011eacf7aae6f95a6445f433f`, derived as the parent of the `BASELINE: OK` commit on `feature/multi-host-runtime`.

### Calibration at BASE_SHA

Command: `bash docs/03-analysis/probes/multi-host-runtime/calibrate.sh "$BASE_SHA"`

```text
== h-mad/SKILL.md
  10 $HOME/.claude
   8 Agent(
   2 CLAUDE
   1 CLAUDE_CODE_SESSION_ID
   2 CLAUDE_CONFIG_DIR
   2 Skill(
   1 `PermissionRequest`
   2 `PostToolUseFailure`
   3 `PostToolUse`
   6 `PreToolUse`
   2 `SendMessage`
   1 `SessionStart`
  82 ~/.claude
TOTAL h-mad/SKILL.md occurrences=122 distinct=13
== handoff/SKILL.md
  19 $HOME/.claude
   1 CLAUDE
   2 CLAUDE_CODE_ENABLE_TODO_TOOLS
  18 CLAUDE_SKILLS_ROOT
   1 Skill(
   7 `TaskCreate`
   1 `TaskGet`
   3 `TaskList`
   2 `TaskUpdate`
   5 `TodoWrite`
   3 `ToolSearch`
   9 ~/.claude
TOTAL handoff/SKILL.md occurrences=71 distinct=12
CALIBRATE: OK sha=3b5c4388b4f11b7011eacf7aae6f95a6445f433f
```

### Seed coverage at BASE_SHA

Command: `/opt/anaconda3/bin/python docs/03-analysis/probes/multi-host-runtime/seed_coverage.py --sha "$BASE_SHA" --registry docs/03-analysis/probes/multi-host-runtime/seed.json`

```text
ENTRY id=subagent-call h-mad=14 handoff=0 declared=h-mad verdict=ok
ENTRY id=skill-call h-mad=2 handoff=1 declared=h-mad,handoff verdict=ok
ENTRY id=advisor h-mad=18 handoff=0 declared=h-mad verdict=ok
ENTRY id=send-message h-mad=2 handoff=0 declared=h-mad verdict=ok
ENTRY id=hook-event h-mad=21 handoff=0 declared=h-mad verdict=ok
ENTRY id=task-tools h-mad=0 handoff=24 declared=handoff verdict=ok
ENTRY id=tool-search h-mad=0 handoff=5 declared=handoff verdict=ok
ENTRY id=session-id-env h-mad=1 handoff=0 declared=h-mad verdict=ok
ENTRY id=claude-config-dir h-mad=2 handoff=0 declared=h-mad verdict=ok
ENTRY id=skill-root-env h-mad=0 handoff=18 declared=handoff verdict=ok
ENTRY id=todo-tools-optin h-mad=0 handoff=2 declared=handoff verdict=ok
ENTRY id=claude-md h-mad=2 handoff=1 declared=h-mad,handoff verdict=ok
ENTRY id=claude-skills-dir h-mad=73 handoff=18 declared=h-mad,handoff verdict=ok
ENTRY id=claude-agents-dir h-mad=6 handoff=0 declared=h-mad verdict=ok
ENTRY id=claude-hooks-dir h-mad=6 handoff=0 declared=h-mad verdict=ok
ENTRY id=claude-settings h-mad=2 handoff=1 declared=h-mad,handoff verdict=ok
ENTRY id=claude-handoffs-dir h-mad=1 handoff=7 declared=h-mad,handoff verdict=ok
ENTRY id=claude-projects-store h-mad=3 handoff=0 declared=h-mad verdict=ok
ENTRY id=claude-homunculus h-mad=0 handoff=2 declared=handoff verdict=ok
ENTRY id=claude-home-bare h-mad=3 handoff=0 declared=h-mad verdict=ok
ENTRY id=session-reset-command h-mad=4 handoff=7 declared=h-mad,handoff verdict=ok
ENTRY id=skill-slash-invocation h-mad=15 handoff=11 declared=h-mad,handoff verdict=ok
SEEDCOV: PASS entries=22 stale=0 undeclared=0
```
