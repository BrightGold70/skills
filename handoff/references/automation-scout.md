## Automation scout

Scan this session's work for repeated patterns worth capturing as skills. Runs after learnings are persisted, before committing. Skip entirely if `--skip-scout` was set.

### How to run

Run this analysis inline (no external agent or plugin required). If a read-only subagent is available, spawn one for isolation — but the inline path is the default.

Review `git diff HEAD~10..HEAD` and the conversation. Find: command pipelines the user retyped multiple times, multi-step workflows done manually without a shortcut, patterns that recurred ≥2 times, or any sequence that felt like "there should be a skill for this." For each candidate: pattern name, recurrence count, one-line description. Cap at 5 candidates.

### Where to write

Append to `docs/skill-candidates.md` (create with `# Skill Candidates` header if absent):

```markdown
## YYYY-MM-DD — <session-slug>

- **<pattern>**: <description> — recurrence: N — candidate: yes/maybe/no
```

If zero candidates found, write: `## YYYY-MM-DD — <slug> — no candidates`.

### Evolution bridge (opt-in)

After writing to `docs/skill-candidates.md`, check whether
`~/.claude/homunculus/evolved/skills/` exists. If it does **and** any candidate
has `recurrence: N` where N ≥ 3 **and** `candidate: yes`, write a minimal stub
there so the pattern is visible to continuous-learning-v2 if installed:

For each qualifying candidate, create
`~/.claude/homunculus/evolved/skills/<pattern-slug>.md`:

```markdown
---
name: <pattern-slug>
description: <one-line description from candidate>
source: handoff-scout
recurrence: N
session: YYYY-MM-DD
---

# <Pattern Name>

Candidate graduated from `docs/skill-candidates.md` via handoff automation scout.
Recurrence: N sessions. Promote to a full skill when the pattern stabilises further.
```

Skip silently if `~/.claude/homunculus/evolved/` does not exist — this bridge
is opt-in for users who have continuous-learning-v2 installed. Do not create
the directory; just skip.
