---
name: skill-creator
description: Guide for creating effective OpenCode skills. Use when users want to create a new skill or update existing skills that extend OpenCode's capabilities with specialized knowledge, workflows, or tool integrations.
---

# OpenCode Skill Creator

This skill provides guidance for creating effective OpenCode skills.

## About Skills

Skills are modular, self-contained packages that extend OpenCode's capabilities by providing specialized knowledge, workflows, and tools.

### Skill Locations

OpenCode searches for skills in:
- Project: `.opencode/skills/` or `.claude/skills/` or `.agents/skills/`
- Global: `~/.config/opencode/skills/` or `~/.claude/skills/` or `~/.agents/skills/`

### Anatomy of a Skill

Each skill needs:
```
skill-name/
└── SKILL.md (required)
    ├── YAML frontmatter (required)
    │   ├── name: (required)
    │   └── description: (required)
    └── Markdown instructions (required)
```

### SKILL.md Format

**Frontmatter** (YAML):
```yaml
---
name: skill-name
description: Brief description of what this skill does. Use third-person.
---
```

**Content**: Detailed instructions, workflows, and guidance.

### Best Practices

1. **Name**: Use kebab-case (e.g., `github-automation`)
2. **Description**: Be specific about when to use this skill
3. **Content**: 
   - Keep SKILL.md focused on procedural knowledge
   - Use references/ for detailed documentation
   - Include practical examples

### Example Skill Structure

```markdown
---
name: example-skill
description: Does something specific. Use when user wants to...
---

# Example Skill

## When This Skill Must Be Used

[Describe when this skill applies]

## Workflow

1. Step one
2. Step two
3. Step three

## Examples

[Provide concrete examples]
```

### Tips

- Skills are loaded on-demand via the native `skill` tool
- OpenCode agents see available skills and can load full content when needed
- Keep skills focused on specific domains for better reusability
